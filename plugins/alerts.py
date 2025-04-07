import aiofiles
import keyboard
import time
import threading
import json
import random
import asyncio
import re
import logging
from pydub import AudioSegment, playback
from poolguy.storage import loadJSON
from poolguy import Alert
from plugins.spotifyapi import duck_volume
from plugins.tts import generate_speech, VOICES

logger = logging.getLogger(__name__)

###################=========---------
### channel.ban ###=============---------
###################=================---------
class ChannelBan(Alert):
    """channel.ban"""
    queue_skip = False
    priority = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.banPages = ['templates/ban-pacific.html', 'templates/ban-tucker.html']
        self.ignorelist = ["streamelements", "nightbot"]
        self.defaultpic = "images/default_pic.jpg"
        self.scene = "[M] Main"
        self.source = "[S] Banned"
        self.ai_thread = None

    async def wait_till_done(self):
        logger.debug(f"[Alert] Ban: waiting for AI")
        while self.ai_thread:
            if not self.ai_thread.is_alive():
                r = self.ai_thread.join()
                await self.bot.http.sendChatMessage(f'{r}')
                self.ai_thread = None
            await asyncio.sleep(0.1)
        logger.debug(f"[Alert] Ban: waiting for alert")
        while not self.bot.alertDone:
            await asyncio.sleep(0.1)

    async def getUserPic(self, uid):
        logger.debug(f"[Alert] Ban: getting user pic")
        try:
            r = await self.bot.http.getUsers(ids=uid)
            return r[0]['profile_image_url']
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return self.defaultpic
    
    async def render_page(self, page, name, pic):
        try:
            async with aiofiles.open(page, 'r', encoding='utf-8') as f:
                template = await f.read()
            rendered = template.replace("{{ name }}", name).replace("{{ pic_url }}", pic)
            logger.debug(f"[Alert] Ban: rendered template for {name}")
            return rendered
        except Exception as e:
            logger.error(f"[Alert] Ban: Error rendering template: {e}")
            return ""
    
    @duck_volume(volume=50)
    async def process(self):
        self.bot.alertDone = False
        logger.debug(f"[Alert] Ban: \n{json.dumps(self.data, indent=2)}")
        if self.data["moderator_user_login"] in self.ignorelist:
            return
        dur = "permanently banned" if self.data['is_permanent'] else "timed out"
        reason = self.data['reason']
        name = self.data['user_name']
        logger.debug(f"[Alert] Ban: starting ai thread")
        q = f'Please inform everyone that "{name}" was just {dur} from the chat for the reason: "{reason if reason else "Acting like a bot"}".'
        if hasattr(self.bot, 'ai'):
            self.ai_thread = self.bot.ai.threaded_ask(q)
        else:
            await self.bot.http.sendChatMessage(f'Get rekt {name} Modding')
        picurl = await self.getUserPic(self.data["user_id"])
        banPage = random.choice(self.banPages)
        self.bot.banHTML = await self.render_page(banPage, name, picurl)
        await self.bot.obsws.show_source(self.source, self.scene)
        await self.wait_till_done()
        await self.bot.obsws.hide_source(self.source, self.scene)


###########################################################=========---------
### channel.channel_points_custom_reward_redemption.add ###=============---------
###########################################################=================---------
points_cfg = loadJSON("db/chan_points_cfg.json")

class VideoRedeem(Alert):
    queue_skip = False
    priority = 3
    store = False

    @duck_volume(volume=69)
    async def process(self):
        rewardConf = points_cfg[self.data["reward"]["id"]]
        await self.bot.obsws.show_and_wait(rewardConf['source'], rewardConf['scene'])

class ClownCoreRedeem(Alert):
    queue_skip = False
    priority = 3
    store = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vidscene = "[S] Videos"
        self.clown_sources = [
            "clown-foldpizza",
            "clown-pain",
            "clown-3g",
            "clown-tech",
            "clown-drivethru",
            "clown-sub",
            "clown-hell"
        ]
    
    @duck_volume(volume=69)
    async def process(self):
        await self.bot.obsws.show_and_wait(random.choice(self.clown_sources), self.vidscene)
        
class TWSSRedeem(Alert):
    queue_skip = False
    priority = 1
    store = False

    @duck_volume(volume=69)
    async def process(self):
        await self.bot.obsws.show_and_wait(f'TWSS{random.randint(1, 21)}', '[S] TWSS')

class ChannelChannelPointsCustomRewardRedemptionAdd(Alert):
    queue_skip = False
    priority = 3
        
    async def process(self):
        rewardId = self.data["reward"]["id"]
        if rewardId not in points_cfg:
            logger.error(f"ChannelPointRedeem: {rewardId} \n{json.dumps(self.data, indent=2)}")
            return
        rewardConf = points_cfg[rewardId]
        if 'name' not in rewardConf:
            alert = VideoRedeem(self.bot, self.message_id, self.channel, self.data, self.timestamp)
            await self.bot.ws.notification_handler._queue.put((alert.priority, alert))
            return
        match rewardConf['name']:
            # Ban_______________
            case "bansmall":
                await self.timeout(60)
            case "banbig":
                await self.timeout(3600)
            # Cabbage____________
            case "cabbage":
                emotes = rewardConf['emotes']
                for i in range(3):
                    await asyncio.sleep(0.3)
                    await self.bot.http.sendChatMessage(f'{random.choice(emotes)} {random.choice(emotes)} {random.choice(emotes)}')
            # Sound on Key____________
            case "mario.mp3":
                self.addSoundOnKeyTask("db/sounds/mario-jump.mp3", 300, -15)
            case "ctrl_fart":
                self.addSoundOnKeyTask("db/sounds/farts/fart1.wav", 300, -15)
            # Avatars____________
            case "monke" | "scav" | "kek":
                await self.bot.obsws.hide_all_sources(rewardConf['scene'])
                await self.bot.obsws.show_source(rewardConf['source'], rewardConf['scene'])
             # Clowncore____________
            case "clowncore":
                alert = ClownCoreRedeem(self.bot, self.message_id, self.channel, self.data, self.timestamp)
                await self.bot.ws.notification_handler._queue.put((alert.priority, alert))
             # TWSS____________
            case "TWSS":
                await self.bot.obsws.show_source(f'TWSS{random.randint(1, 21)}', '[S] TWSS')
                #alert = TWSSRedeem(self.bot, self.message_id, self.channel, self.data, self.timestamp)
                #await self.bot.ws.notification_handler._queue.put((alert.priority, alert))
            case "flashbang":
                await self.bot.obsws.show_source(rewardConf['source'], rewardConf['scene'])
                await asyncio.sleep(rewardConf['delay'])
                await self.bot.obsws.hide_source(rewardConf['source'], rewardConf['scene'])
            case _:
                pass

    async def timeout(self, size=60):
        viewer2ban = self.data["user_input"].replace("@", "").replace(" ", "")
        logger.warning(f"Banning {viewer2ban}")
        r = await self.bot.http.getUsers(logins=viewer2ban)
        try:
            banId = r[0]['id']
            await self.bot.http.banUser(
                user_id=banId, 
                duration=size, 
                reason=f"{self.data['user_login']} used channel points to timeout {viewer2ban} for {size} secs"
            )
        except Exception as e:
            logger.error("[Bot] "+ e)
    
    def addSoundOnKeyTask(self, sound, duration, gain):
        key = self.data["user_input"].replace(" ", "").lower()
        asyncio.create_task(self.soundOnKey(key=key, sound=sound, duration=duration, gain=gain))

    def play_sound(self, sound, gain=0):
        logger.debug(f"[play_sound] -> {sound}")
        seg = AudioSegment.from_file(sound)
        s = seg.apply_gain(gain)
        threading.Thread(target=playback.play, args=(s,)).start()

    async def soundOnKey(self, key="space", sound="fart1.wav", duration=30, gain=0):
        start = time.time()
        logger.debug(f"[soundOnKey] -> ({key}):{sound} -{duration}sec-")
        played = False
        while time.time()-start < duration:
            if keyboard.is_pressed(key):
                if not played:
                    played = True
                    self.play_sound(sound, gain)
            else:
                played = False
            await asyncio.sleep(0.05)
        logger.debug(f"[soundOnKey] -> ({key}):{sound} -complete-")


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


#################################=========---------
### channel.chat.notification ###=============---------
#################################=================---------
class ChannelChatNotification(Alert):
    queue_skip = True

    async def process(self):
        notice_type = self.data['notice_type']
        if notice_type.startswith('shared'):
            return
        out = {
            "notice_type": notice_type,
            "name": "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name'],
            "message": self.data['message'],
            "sys_message": self.data['system_message'],
            "event": self.data[notice_type]
        }
        await self.bot.alertws_queue.put(out)
        logger.error(f'[ChannelChatNotificationAlert] \n{json.dumps(out, indent=2)}')

########################=========---------
### channel.bits.use ###=============---------
########################=================---------
cheer_cfg = loadJSON("db/cheers_cfg.json")

class ChannelBitsUse(Alert):
    queue_skip = False
    priority = 1
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bit_scene = "[S] Bit Alerts"
        self.bit_altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self.bit_text = "CheerText"
        self.tts_limit = 123
        self.tts_source = "bit_tts"

    def remove_cheermotes(self, message):
        result = ""
        for fragment in message.get('fragments', []):
            # Only add fragments of type 'text'
            if fragment.get('type') == 'text':
                result += fragment.get('text', '')
        return result.strip()


    async def process(self):
        logger.info(f"[Bot] Bits: \n{json.dumps(self.data, indent=2)}")
        amount = int(self.data['bits'])
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(amount, 'bits')
        if self.data["type"] == "cheer":
            alertK = None
            for k in [*cheer_cfg]:
                if amount < int(k):
                    break
                else:
                    alertK = k
            if alertK:
                await self._process(amount, alertK)

    @duck_volume(volume=50)
    async def _process(self, amount, alertK):
        usr = str(self.data['user_name'])
        text = None
        if self.data["message"] and amount >= self.tts_limit:
            text = self.remove_cheermotes(self.data["message"])
        if text:
            voice = random.choice(list(VOICES.keys()))
            await generate_speech(text, "db/bit_tts.mp3", voice)
        txt = cheer_cfg[alertK]['text'].replace("{user}", usr).replace("{amount}", str(amount))
        await self.bot.obsws.set_source_text(self.bit_text, ' '+txt)
        for a in self.bit_altscenes:
            await self.bot.obsws.show_source(a, self.bit_scene)
        await self.bot.obsws.show_and_wait(cheer_cfg[alertK]['source'], self.bit_scene)
        await self.bot.obsws.set_source_text(self.bit_text, "")
        for a in self.bit_altscenes:
            await self.bot.obsws.hide_source(a, self.bit_scene)
        if text:
            await self.bot.obsws.show_and_wait(self.tts_source, self.bit_scene)


####################=========---------
### channel.raid ###=============---------
####################=================---------
class ChannelRaid(Alert):
    queue_skip = False
    priority = 2
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bit_scene = "[S] Bit Alerts"
        self.bit_altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self.bit_text = "CheerText"
        
    @duck_volume(volume=50)
    async def process(self):
        raidFrom = self.data['from_broadcaster_user_name']
        raidTo = self.data['to_broadcaster_user_name']
        views = self.data['viewers']
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(int(views), 'raids')
        if hasattr(self.bot, 'ai'):
            r = self.bot.ai.ask(f'{raidFrom} is raiding {raidTo} with {views} viewers!, please inform chat.')
        else:
            r = f"{raidFrom} thank you for the {views} viewer raid!"
        await self.bot.http.sendChatMessage(f'{r}')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(self.bit_text, f" {raidFrom} is raiding with {views} viewers!")
            for a in self.bit_altscenes:
                await self.bot.obsws.show_source(a, self.bit_scene)
            await self.bot.obsws.show_and_wait('hotfeet', self.bit_scene)
            await self.bot.obsws.set_source_text(self.bit_text, "")
            for a in self.bit_altscenes:
                await self.bot.obsws.hide_source(a, self.bit_scene)


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
hype_scene = "[S] Dumpster Chat"

hype_cfg = {
    "1": "fire1",
    "2": "fire2",
    "3": "fire3",
    "4": "fire4"
}

class ChannelHypeTrainProgress(Alert):
    queue_skip = True

    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in hype_cfg:
                if int(k) <= self.data['level']:
                    await self.bot.obsws.show_source(hype_cfg[k], hype_scene)


##############################=========---------
### channel.hype_train.end ###=============---------
##############################=================---------
class ChannelHypeTrainEnd(Alert):
    queue_skip = True

    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in hype_cfg:
                await self.bot.obsws.hide_source(hype_cfg[k], hype_scene)


#########################=========---------
### channel.subscribe ###=============---------
#########################=================---------
sub_scene = "[S] Bit Alerts"
sub_altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
sub_text = "CheerText"

class ChannelSubscribe(Alert):
    queue_skip = False
    priority = 1

    @duck_volume(volume=50)
    async def _process(self):
        name = self.data['user_name']
        tier = int(self.data['tier'][0])
        # add time to the subathon
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(sub_text, f" {name} subscribed! \n-tier {tier}-")
            for a in sub_altscenes:
                await self.bot.obsws.show_source(a, sub_scene)
            await self.bot.obsws.show_and_wait('yaaay', sub_scene)
            await self.bot.obsws.set_source_text(sub_text, "")
            for a in sub_altscenes:
                await self.bot.obsws.hide_source(a, sub_scene)
        
    async def process(self):
        logger.error(f"{self.channel}:\n{json.dumps(self.data, indent=2)}")
        if self.data['is_gift']:
            return
        await self._process()


#################################=========---------
### channel.subscription.gift ###=============---------
#################################=================---------
class ChannelSubscriptionGift(Alert):
    queue_skip = False
    priority = 1

    @duck_volume(volume=50)
    async def process(self):
        logger.error(f"{self.channel}:\n{json.dumps(self.data, indent=2)}")
        name = "Anonymous" if self.data['is_anonymous'] else self.data['user_name']
        total = self.data['total']
        tier = self.data['tier'][0]
        # add time to the subathon
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(total, f't{tier}')

        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(sub_text, f" {name} gifted {total} subs! \n-tier {tier}-")
            for a in sub_altscenes:
                await self.bot.obsws.show_source(a, sub_scene)
            await self.bot.obsws.show_and_wait('reallynice', sub_scene)
            await self.bot.obsws.set_source_text(sub_text, "")
            for a in sub_altscenes:
                await self.bot.obsws.hide_source(a, sub_scene)


#################################=========---------
### channel.subscription.message ###=============---------
#################################=================---------
class ChannelSubscriptionMessage(Alert):
    queue_skip = False
    priority = 2
    
    @duck_volume(volume=50)
    async def process(self):
        logger.error(f"{self.channel}:\n{json.dumps(self.data, indent=2)}")
        name = self.data['user_name']
        tier = int(self.data['tier'][0])
        total_months = self.data['cumulative_months']
        # add time to the subathon
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            tts_fp = None
            if self.data["message"]:
                voice = random.choice(list(VOICES.keys()))
                tts_fp = await generate_speech(self.data['message']['text'], "db/sub_tts.mp3", voice)
            await self.bot.obsws.set_source_text(sub_text, f" {name} has been subscribed for {int(total_months)} months!")
            for a in sub_altscenes:
                await self.bot.obsws.show_source(a, sub_scene)
            await self.bot.obsws.show_and_wait('goingupthere', sub_scene)
            await self.bot.obsws.set_source_text(sub_text, "")
            for a in sub_altscenes:
                await self.bot.obsws.hide_source(a, sub_scene)
            if tts_fp:
                await self.bot.obsws.show_and_wait('sub_tts', sub_scene)



alert_objs = {
    'channel.chat.notification': ChannelChatNotification,
    'channel.chat.message': ChannelChatMessage,
    'channel.ban': ChannelBan,
    'channel.channel_points_custom_reward_redemption.add': ChannelChannelPointsCustomRewardRedemptionAdd,
    'channel.hype_train.progress': ChannelHypeTrainProgress,
    'channel.hype_train.end': ChannelHypeTrainEnd,
    'channel.subscribe': ChannelSubscribe,
    'channel.subscription.message': ChannelSubscriptionMessage,
    'channel.subscription.gift': ChannelSubscriptionGift,
    'channel.goal.progress': ChannelGoalProgress,
    'channel.bits.use': ChannelBitsUse,
    'channel.follow': ChannelFollow,
    'channel.raid': ChannelRaid
}
