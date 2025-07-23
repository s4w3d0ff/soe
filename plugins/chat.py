import logging
import aiohttp
import asyncio
import re
from poolguy import TwitchBot, Alert, route, websocket
from poolguy.twitchws import MaxSizeDict

logger = logging.getLogger(__name__)

emoteEndpoint = "https://static-cdn.jtvnw.net/emoticons/v2/"
sevenTVcdnurl = "https://cdn.7tv.app/emote/"
sevenTVurl = "https://7tv.io/v3/"

ball_mass = 10

#==========================================================================================
# ChatBot ===============================================================================
#==========================================================================================
class ChatBot(TwitchBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # stores 3rd party emotes
        self.emotes = {}
        # stores channel badges
        self.badges = {}
        self.chat_history = MaxSizeDict(7)

    async def setup_chat(self):
        """ init the emotes from 7TV and other sources, and get channel badges """
        self.badges = await self.getBadges()
        self.emotes['7tv_global'] = await self.get7tvEmotes()
        self.emotes[f'7tv_{self.http.user_id}'] = await self.get7tvEmotes(self.http.user_id)
    
    async def getBadges(self):
        """ Get channel and global badges from Twitch API """
        global_badges = await self.http.getGlobalChatBadges()
        chan_badges = await self.http.getChannelChatBadges()
        return {i['set_id']: {v['id']: v['image_url_4x'] for v in i['versions']} for i in global_badges + chan_badges}

    async def get7tvEmotes(self, user_id="global"):
        """ Get channel and global emotes from 7TV """
        if user_id == "global":
            url = sevenTVurl+"emote-sets/global"
        else:
            url = sevenTVurl+f"users/twitch/{user_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                rmotes = await response.json()
                if 'emotes' in rmotes:
                    emotes = rmotes['emotes']
                else:
                    emotes = rmotes['emote_set']['emotes']
                return {e['name']: f"{sevenTVcdnurl}{e['id']}/4x.webp" for e in emotes}

    @websocket('/chatws')
    async def chat_ws(self, ws, request):
        logger.warning(f"Websocket connected: chatws")
        await self.ws_wait_for_twitch_login(ws)
        while not ws.closed:
            try:
                await ws.send_json(self.chat_history)
            except Exception as e:
                logger.error(f"Unexpected error in chatws loop: {e}")
                break
            await asyncio.sleep(1)
        logger.warning("chatws connection closed")

    @route('/chat')
    async def chat_route(self, request):
        return await self.app.response_html('templates/chat.html')


class BlackHoleBot(TwitchBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blackhole_queue = asyncio.Queue()

    @websocket('/blackholews')
    async def blackhole_ws(self, ws, request):
        logger.warning("Blackhole websocket connected")
        await self.ws_wait_for_twitch_login(ws)
        while not ws.closed:
            try:
                update = await asyncio.wait_for(self.blackhole_queue.get(), timeout=15)
                await ws.send_json(update)
                self.blackhole_queue.task_done()
            except asyncio.TimeoutError:
               await ws.ping()
               continue
            except Exception as e:
                logger.error(f"Unexpected error in blackholews loop: {e}")
                break
        logger.warning("Blackhole websocket connection closed")
    
    @route('/blackhole')
    async def blackhole(self, request):
        return await self.app.response_html('templates/blackhole.html')

############################=========---------
### channel.chat.message ###=============---------
############################=================---------
class ChannelChatMessage(Alert):
    queue_skip = True
    store = False

    async def parseBadges(self):
        bid = self.data['source_broadcaster_user_id'] or self.data['broadcaster_user_id']
        message_badges = self.data['source_badges'] or self.data['badges']
        badges = []
        for badge in message_badges:
            if badge['set_id'] not in self.bot.badges:
                for s_badge in await self.bot.http.getChannelChatBadges(bid):
                    self.bot.badges[s_badge['set_id']] = {v['id']: v['image_url_4x'] for v in s_badge['versions']}
            badges.append(f'<img class="badge" src="{self.bot.badges[badge['set_id']][badge['id']]}">')
        return badges

    async def parseTTVUrl(self, id, format, theme_mode="dark", scale="3.0"):
        return f'{emoteEndpoint}{id}/{format}/{theme_mode}/{scale}'
    
    async def split_text_with_7TVemotes(self, text, bid):
        if f'7tv_{bid}' not in self.bot.emotes:
            self.bot.emotes[f'7tv_{bid}'] = await self.bot.get7tvEmotes(bid)
        emotes = {**self.bot.emotes[f'7tv_{bid}'], **self.bot.emotes['7tv_global']}
        pattern = r'\b(' + '|'.join(map(re.escape, emotes.keys())) + r')\b'
        result = []
        last_end = 0
        # Iterate over all matches
        for match in re.finditer(pattern, text):
            start, end = match.span()
            emote_name = match.group(1)
            # Add text before the emote (if any)
            if start > last_end:
                result.append({"text": text[last_end:start], "type": "text"})
            # Add the emote URL
            result.append({"url": emotes[emote_name], "type": "emote"})
            last_end = end

        # Add any remaining text after the last emote
        if last_end < len(text):
            result.append({"text": text[last_end:], "type": "text"})

        return result
    
    async def process(self):
        logger.info(f'[Chat] {self.data["chatter_user_name"]}: {self.data["message"]["text"]}')
        await self.bot.command_check(self.data)

        message = {
            "fragments": [],
            'user': self.data['chatter_user_name'],
            'user_id': self.data['chatter_user_id'],
            'color': self.data['color'] or "#32b5c5c",
            'badges': await self.parseBadges(),
            'text': self.data["message"]["text"],
            'timestamp': self.timestamp
        }

        for frag in self.data['message']['fragments']:
            # Check if the fragment is a twitch emote
            if frag['type'] == 'emote':
                message["fragments"].append({
                    "url": await self.parseTTVUrl(
                        frag['emote']['id'], 
                        'animated' if 'animated' in frag['emote']['format'] else 'static'),
                    "type": 'emote',
                })
            # Check other fragments for 7TV emotes
            else:
                bid = self.data['source_broadcaster_user_id'] or self.data['broadcaster_user_id']
                text = frag["text"]
                subfrag = await self.split_text_with_7TVemotes(text, bid)
                for sf in subfrag:
                    message["fragments"].append(sf)


        if hasattr(self.bot, "blackhole_queue"):
            for frag in message["fragments"]:
                if frag['type'] == 'emote':
                    await self.bot.blackhole_queue.put({
                        "image": frag["url"],
                        "mass": ball_mass
                    })
        if hasattr(self.bot, 'chat_history'):
            self.bot.chat_history[self.data['message_id']] = message


###################################=========---------
### channel.chat.message_delete ###=============---------
###################################=================---------
class ChannelChatMessageDelete(Alert):
    queue_skip = True
    store = False

    async def process(self):
        if hasattr(self.bot, 'chat_history'):
            del self.bot.chat_history[self.data["message_id"]]

###################################=========---------
### channel.chat.clear_user_messages ###=============---------
###################################=================---------
class ChannelChatClearUserMessages(Alert):
    queue_skip = True
    store = False

    async def process(self):
        if hasattr(self.bot, 'chat_history'):
            history = self.bot.chat_history.items()
            # Collect keys to be removed in a separate list
            keys_to_remove = [id for id, msg in history if msg['user_id'] == self.data['target_user_id']]
            # Remove the keys from the dictionary
            for id in keys_to_remove:
                self.bot.chat_history.pop(id)
