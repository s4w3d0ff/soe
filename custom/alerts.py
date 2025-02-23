import aiofiles
import keyboard
from pydub import AudioSegment, playback
from poolguy.utils import ColorLogger, loadJSON, aioUpdateFile
from poolguy.utils import time, threading, json, random, asyncio, re
from poolguy.twitchws import Alert
from .plugins.spotifyapi import duck_volume
from .plugins.tts import generate_speech, VOICES

logger = ColorLogger(__name__)


###################=========---------
### channel.ban ###=============---------
###################=================---------
class ChannelBanAlert(Alert):
    """channel.ban"""
    queue_skip = False
    priority = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.banPages = ['templates/ban-pacific.html', 'templates/ban-tucker.html']
        self.ignorelist = ["streamelements", "nightbot"]
        self.defaultpic = "default_pic.jpg"
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
        self.ai_thread = self.bot.ai.threaded_ask(q)
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

class ChannelChannelPointsCustomRewardRedemptionAddAlert(Alert):
    queue_skip = False
    priority = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.avatar_scene = "[S] Avatar"
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
        self.cabbage_emotes = [
            's4w3d0FfPurp', 
            's4w3d0FfGoldCabbage', 
            's4w3d0FfCabbage', 
            's4w3d0FfCabbageJAM'
        ]

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

    async def process(self):
        rewardId = self.data["reward"]["id"]
        if rewardId not in points_cfg:
            logger.error(f"ChannelPointRedeem: {rewardId} \n{json.dumps(self.data, indent=2)}")
            return
        rewardConf = points_cfg[rewardId]
        old_volume = None
        if "lower_volume" in rewardConf:
            old_volume = await self.bot.spotify.get_current_volume()
            await self.bot.spotify.set_volume(volume=rewardConf['lower_volume'])
        if "source" in rewardConf: # Source to hide?
            if "delay" in rewardConf:
                await self.bot.obsws.show_source(rewardConf['source'], rewardConf['scene'])
                await asyncio.sleep(rewardConf['delay'])
                await self.bot.obsws.hide_source(rewardConf['source'], rewardConf['scene'])
            else:
                await self.bot.obsws.show_and_wait(rewardConf['source'], rewardConf['scene'])
        #===============================================================#
        if 'name' in rewardConf:
            match rewardConf['name']:
                # Ban_______________
                case "bansmall":
                    await self.timeout(60)
                case "banbig":
                    await self.timeout(3600)
                # Cabbage____________
                case "cabbage":
                    for i in range(3):
                        await asyncio.sleep(0.3)
                        await self.bot.http.sendChatMessage(f'{random.choice(self.cabbage_emotes)} {random.choice(self.cabbage_emotes)} {random.choice(self.cabbage_emotes)}')
                # Sound on Key____________
                case "mario.mp3":
                    self.addSoundOnKeyTask("db/sounds/mario-jump.mp3", 300, -15)
                case "ctrl_fart":
                    self.addSoundOnKeyTask("db/sounds/farts/fart1.wav", 300, -15)
                # Avatars____________
                case "monke":
                    await self.bot.obsws.hide_all_sources(self.avatar_scene)
                    await self.bot.obsws.show_source("[Av] Monke", self.avatar_scene)
                case "scav":
                    await self.bot.obsws.hide_all_sources(self.avatar_scene)
                    await self.bot.obsws.show_source("[Av] Scav", self.avatar_scene)
                case "kek":
                    await self.bot.obsws.hide_all_sources(self.avatar_scene)
                    await self.bot.obsws.show_source("[Av] Kek", self.avatar_scene)
                 # Clowncore____________
                case "clowncore":
                    await self.bot.obsws.show_and_wait(random.choice(self.clown_sources), self.vidscene)
                 # TWSS____________
                case "TWSS":
                    await self.bot.obsws.show_and_wait(f'TWSS{random.randint(1, 21)}', '[S] TWSS')
                case _:
                    pass
        if old_volume:
            await self.bot.spotify.set_volume(volume=old_volume)


############################=========---------
### channel.chat.message ###=============---------
############################=================---------
class ChannelChatMessageAlert(Alert):
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
        logger.info(f'[Chat] {self.data["chatter_user_name"]}: {self.data["message"]["text"]}', 'purple')
        await self.bot.command_check(self.data)
        out = {
            'id': self.data['message_id'], 
            'user': self.data['chatter_user_name'], 
            'color': self.data['color'], 
            'badges': await self.parseBadges(), 
            'text': await self.parseEmotesText(),
            'timestamp': self.timestamp
            }
        #await self.bot.chat_queue.put(out)
        logger.debug(f'[Chat] {json.dumps(out, indent=2)}', 'purple')


#################################=========---------
### channel.chat.notification ###=============---------
#################################=================---------
class ChannelChatNotificationAlert(Alert):
    queue_skip = True

    async def process(self):
        logger.debug(f'[ChannelChatNotificationAlert] {json.dumps(self.data, indent=2)}', 'purple')
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


#####################=========---------
### channel.cheer ###=============---------
#####################=================---------
cheer_cfg = loadJSON("db/cheers_cfg.json")
bit_scene = "[S] Bit Alerts"
bit_altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
bit_text = "CheerText"

class ChannelCheerAlert(Alert):
    queue_skip = False
    priority = 1

    @duck_volume(volume=50)
    async def _process(self, amount, alertK):
        usr = "Anonymous" if self.data['is_anonymous'] else self.data['user_name']
        if self.data["message"] and amount >= 200:
            voice = random.choice(list(VOICES.keys()))
            await generate_speech(self.data['message'], "db/bit_tts.mp3", voice)
        txt = cheer_cfg[alertK]['text'].replace("{user}", usr).replace("{amount}", str(amount))
        await self.bot.obsws.set_source_text(bit_text, ' '+txt)
        for a in bit_altscenes:
            await self.bot.obsws.show_source(a, bit_scene)
        await self.bot.obsws.show_and_wait(cheer_cfg[alertK]['source'], bit_scene)
        await self.bot.obsws.set_source_text(bit_text, "")
        for a in bit_altscenes:
            await self.bot.obsws.hide_source(a, bit_scene)
        if self.data["message"] and amount >= 200:
            await self.bot.obsws.show_and_wait("bit_tts", bit_scene)

    async def process(self):
        logger.debug(f"[Bot] Cheer: \n{json.dumps(self.data, indent=2)}")
        amount = int(self.data['bits'])
        alertK = None
        for k in [*cheer_cfg]:
            if amount < int(k):
                break
            else:
                alertK = k
        if alertK:
            await self._process(amount, alertK)

####################=========---------
### channel.raid ###=============---------
####################=================---------
class ChannelRaidAlert(Alert):
    queue_skip = False
    priority = 2

    @duck_volume(volume=50)
    async def process(self):
        raidFrom = self.data['from_broadcaster_user_name']
        raidTo = self.data['to_broadcaster_user_name']
        views = self.data['viewers']
        r = self.bot.ai.ask(f'{raidFrom} is raiding {raidTo} with {views} viewers!, please inform chat.')
        await self.bot.http.sendChatMessage(f'{r}')
        await self.bot.obsws.set_source_text(bit_text, f" {raidFrom} is raiding with {views} viewers!")
        for a in bit_altscenes:
            await self.bot.obsws.show_source(a, bit_scene)
        await self.bot.obsws.show_and_wait('hotfeet', bit_scene)
        await self.bot.obsws.set_source_text(bit_text, "")
        for a in bit_altscenes:
            await self.bot.obsws.hide_source(a, bit_scene)


######################=========---------
### channel.follow ###=============---------
######################=================---------
class ChannelFollowAlert(Alert):
    queue_skip = False
    priority = 3

    @duck_volume(volume=50)
    async def process(self):
        uname = self.data['user_name']
        logger.info(f"[Bot] {uname} followed!")
        await self.bot.http.sendChatMessage(f"Thank you for the follow! @{uname} s4w3d0FfLuv")
        await self.bot.obsws.set_source_text(bit_text, f" {uname} joined the cabbage patch!")
        for a in bit_altscenes:
            await self.bot.obsws.show_source(a, bit_scene)
        await self.bot.obsws.show_and_wait('greasy', bit_scene)
        await self.bot.obsws.set_source_text(bit_text, "")
        for a in bit_altscenes:
            await self.bot.obsws.hide_source(a, bit_scene)


#############################=========---------
### channel.goal.progress ###=============---------
#############################=================---------
class ChannelGoalProgressAlert(Alert):
    queue_skip = True

    async def process(self):
        logger.debug(f"{json.dumps(self.data, indent=2)}")
        g_type = self.data['type']
        if g_type in ["", "new_bits", "subscription_count"]:
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

class ChannelHypeTrainProgressAlert(Alert):
    queue_skip = True

    async def process(self):
        for k in hype_cfg:
            if int(k) <= self.data['level']:
                await self.bot.obsws.show_source(hype_cfg[k], hype_scene)


##############################=========---------
### channel.hype_train.end ###=============---------
##############################=================---------
class ChannelHypeTrainEndAlert(Alert):
    queue_skip = True

    async def process(self):
        for k in hype_cfg:
            await self.bot.obsws.hide_source(hype_cfg[k], hype_scene)


#########################=========---------
### channel.subscribe ###=============---------
#########################=================---------
sub_scene = "[S] Bit Alerts"
sub_altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
sub_text = "CheerText"

class ChannelSubscribeAlert(Alert):
    queue_skip = False
    priority = 1

    @duck_volume(volume=50)
    async def _process(self):
        name = self.data['user_name']
        tier = int(self.data['tier'][0])
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
class ChannelSubscriptionGiftAlert(Alert):
    queue_skip = False
    priority = 1

    @duck_volume(volume=50)
    async def process(self):
        logger.error(f"{self.channel}:\n{json.dumps(self.data, indent=2)}")
        name = "Anonymous" if self.data['is_anonymous'] else self.data['user_name']
        total = self.data['total']
        tier = self.data['tier'][0]
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
class ChannelSubscriptionMessageAlert(Alert):
    queue_skip = False
    priority = 2
    
    @duck_volume(volume=50)
    async def process(self):
        logger.error(f"{self.channel}:\n{json.dumps(self.data, indent=2)}")
        name = self.data['user_name']
        tier = int(self.data['tier'][0])
        total_months = self.data['cumulative_months']
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