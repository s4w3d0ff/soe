import keyboard
from pydub import AudioSegment, playback
from poolguy.utils import asyncio, json, time, random, threading
from poolguy.utils import ColorLogger, loadJSON
from poolguy.twitchws import Alert

logger = ColorLogger("ChannelPointsAlert")

cfg = loadJSON("db/chan_points_cfg.json")

class ChannelChannelPointsCustomRewardRedemptionAddAlert(Alert):
    """channel.channel_points_custom_reward_redemption.add"""
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
        if rewardId not in cfg:
            logger.error(f"ChannelPointRedeem: {rewardId} \n{json.dumps(self.data, indent=2)}")
            return
        rewardConf = cfg[rewardId]
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
