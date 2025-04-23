import logging
import aiohttp
import asyncio
import re
from poolguy import TwitchBot, Alert, route, websocket
from poolguy.twitchws import MaxSizeDict

logger = logging.getLogger(__name__)

emoteEndpoint = "https://static-cdn.jtvnw.net/emoticons/v2/"

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
        cdnurl = "https://cdn.7tv.app/emote/"
        if user_id == "global":
            url = "https://7tv.io/v3/emote-sets/global"
        else:
            url = f"https://7tv.io/v3/users/twitch/{user_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                rmotes = await response.json()
                if 'emotes' in rmotes:
                    emotes = rmotes['emotes']
                else:
                    emotes = rmotes['emote_set']['emotes']
                return {e['name']: f"{cdnurl}{e['id']}/4x.webp" for e in emotes}

    @websocket('/chatws')
    async def chat_ws(self, ws, request):
        logger.warning(f"Websocket connected: chatws")
        while not self.http.user_id:
            logger.error(f"chatws error: not logged in yet")
            await ws.ping()
            await asyncio.sleep(10)
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


############################=========---------
### channel.chat.message ###=============---------
############################=================---------
class ChannelChatMessage(Alert):
    queue_skip = True
    store = False

    async def parseTTVEmote(self, id, format, theme_mode="dark", scale="3.0"):
        """Parse a TTV emote and return the HTML tag for it."""
        return f'<img class="emote" src="{emoteEndpoint}{id}/{format}/{theme_mode}/{scale}">'

    async def parse7TVEmotes(self, text):
        """Parse 7TV emotes from text and replace them with HTML tags."""
        bid = self.data['source_broadcaster_user_id'] or self.data['broadcaster_user_id']
        for name, url in self.bot.emotes[f'7tv_global'].items():
            text = re.sub(r'\b' + re.escape(name) + r'\b', f'<img class="emote" src="{url}">', text)
        if f'7tv_{bid}' not in self.bot.emotes:
            self.bot.emotes[f'7tv_{bid}'] = await self.bot.get7tvEmotes(bid)
        for name, url in self.bot.emotes[f'7tv_{bid}'].items():
            text = re.sub(r'\b' + re.escape(name) + r'\b', f'<img class="emote" src="{url}">', text)
        return text

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

    async def parseEmotesText(self):
        text = self.data['message']['text']
        for f in self.data['message']['fragments']:
            if f['type'] == 'emote':
                text = re.sub(
                    r'\b'+re.escape(f['text'])+r'\b', 
                    await self.parseTTVEmote(f['emote']['id'], 'animated' if 'animated' in f['emote']['format'] else 'static'), 
                    text)
        text = await self.parse7TVEmotes(text)
        return text

    async def process(self):
        logger.info(f'[Chat] {self.data["chatter_user_name"]}: {self.data["message"]["text"]}')
        await self.bot.command_check(self.data)
        if hasattr(self.bot, 'chat_history'):
            out = {
                'user': self.data['chatter_user_name'],
                'color': self.data['color'] or "#32b5c5c",
                'badges': await self.parseBadges(),
                'text': await self.parseEmotesText(),
                'timestamp': self.timestamp
                }
            self.bot.chat_history[self.data['message_id']] = out

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
            for id, msg in self.bot.chat_history.items():
                if msg['user_id'] == self.data['target_user_id']:
                    out = self.bot.chat_history.pop(id)
