import json
import logging
import re
from poolguy import Alert
from plugins.spotifyapi import duck_volume

logger = logging.getLogger(__name__)

############################=========---------
### channel.chat.message ###=============---------
############################=================---------
class ChannelChatMessage(Alert):
    queue_skip = True
    store = False

    async def parseBadges(self):
        bid = self.data['source_broadcaster_user_id'] or self.data['broadcaster_user_id']
        message_badges = self.data['source_badges'] or self.data['badges']
        chatter_id =  self.data['chatter_user_id']
        if bid not in self.bot.channelBadges:
            self.bot.channelBadges[str(bid)] = await self.bot.getChanBadges(bid)
        return [self.bot.channelBadges[bid][i['set_id']][i['id']] for i in message_badges]

    async def parseEmotesText(self):
        text = self.data['message']['text']
        for f in self.data['message']['fragments']:
            if f['type'] == 'emote':
                text = re.sub(
                    r'\b'+re.escape(f['text'])+r'\b', 
                    await self.bot.http.parseTTVEmote(f['emote']['id'], 'animated' if 'animated' in f['emote']['format'] else 'static'), 
                    text)
        return text

    async def process(self):
        logger.info(f'[Chat] {self.data["chatter_user_name"]}: {self.data["message"]["text"]}')
        await self.bot.command_check(self.data)
        out = {
            'id': self.data['message_id'], 
            'user': self.data['chatter_user_name'], 
            'color': self.data['color'], 
            #'badges': await self.parseBadges(), 
            'text': self.data['message']['text'], #await self.parseEmotesText(),
            'timestamp': self.timestamp
            }
        #await self.bot.chat_queue.put(out)
        logger.debug(f'[Chat] {json.dumps(out, indent=2)}')

######################=========---------
### channel.follow ###=============---------
######################=================---------
class ChannelFollow(Alert):
    queue_skip = False
    priority = 3
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bit_scene = "[S] Bit Alerts"
        self.bit_altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self.bit_text = "CheerText"
        
    @duck_volume(volume=50)
    async def process(self):
        uname = self.data['user_name']
        logger.info(f"[Bot] {uname} followed!")
        await self.bot.http.sendChatMessage(f"Thank you for the follow! @{uname} s4w3d0FfLuv")
        await self.bot.obsws.set_source_text(self.bit_text, f" {uname} joined the cabbage patch!")
        for a in self.bit_altscenes:
            await self.bot.obsws.show_source(a, self.bit_scene)
        await self.bot.obsws.show_and_wait('greasy', self.bit_scene)
        await self.bot.obsws.set_source_text(self.bit_text, "")
        for a in self.bit_altscenes:
            await self.bot.obsws.hide_source(a, self.bit_scene)

#############################=========---------
### channel.goal.progress ###=============---------
#############################=================---------
class ChannelGoalProgress(Alert):
    queue_skip = True

    async def process(self):
        logger.debug(f"{json.dumps(self.data, indent=2)}")
        g_type = self.data['type']
        if hasattr(self.bot, 'goal_queue'):
            await self.bot.goal_queue.put({
                    "gtype": g_type,
                    "amount": int(self.data['current_amount'])
                })
            logger.warning(f"{g_type} goal updated to {self.data['current_amount']}")


###################################=========---------
### channel.hype_train.progress ###=============---------
###################################=================---------
class ChannelHypeTrainProgress(Alert):
    queue_skip = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hype_scene = "[S] Dumpster Chat"
        self.hype_cfg = {
            "1": "fire1",
            "2": "fire2",
            "3": "fire3",
            "4": "fire4"
        }
    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in self.hype_cfg:
                if int(k) <= self.data['level']:
                    await self.bot.obsws.show_source(self.hype_cfg[k], self.hype_scene)


##############################=========---------
### channel.hype_train.end ###=============---------
##############################=================---------
class ChannelHypeTrainEnd(Alert):
    queue_skip = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hype_scene = "[S] Dumpster Chat"
        self.hype_cfg = {
            "1": "fire1",
            "2": "fire2",
            "3": "fire3",
            "4": "fire4"
        }

    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in self.hype_cfg:
                await self.bot.obsws.hide_source(self.hype_cfg[k], self.hype_scene)