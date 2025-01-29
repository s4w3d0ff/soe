from poolguy.utils import json, random
from poolguy.utils import ColorLogger, loadJSON, aioUpdateFile
from poolguy.twitchws import Alert
from .plugins.tts import generate_speech, VOICES

logger = ColorLogger(__name__)

cfg = loadJSON("db/cheers_cfg.json")
scene = "[S] Bit Alerts"
altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
textscene = "CheerText"

class ChannelCheerAlert(Alert):
    """channel.cheer"""
    async def process(self):
        logger.debug(f"[Bot] Cheer: \n{json.dumps(self.data, indent=2)}")
        usr = "Anonymous" if self.data['is_anonymous'] else self.data['user_name']
        amount = int(self.data['bits'])
        alertK = None
        for k in [*cfg]:
            if amount < int(k):
                break
            else:
                alertK = k
        if alertK:
            if self.data["message"] and amount >= 200:
                voice = random.choice(list(VOICES.keys()))
                await generate_speech(self.data['message'], "db/bit_tts.mp3", voice)
            txt = cfg[alertK]['text'].replace("{user}", usr).replace("{amount}", str(amount))
            await self.bot.obsws.set_source_text(textscene, ' '+txt)
            for a in altscenes:
                await self.bot.obsws.show_source(a, scene)
            await self.bot.obsws.show_and_wait(cfg[alertK]['source'], scene)
            await self.bot.obsws.set_source_text(textscene, "")
            for a in altscenes:
                await self.bot.obsws.hide_source(a, scene)
            if self.data["message"] and amount >= 200:
                await self.bot.obsws.show_and_wait("bit_tts", scene)



class ChannelRaidAlert(Alert):
    """channel.raid"""
    async def process(self):
        raidFrom = self.data['from_broadcaster_user_name']
        raidTo = self.data['to_broadcaster_user_name']
        views = self.data['viewers']
        r = self.bot.ai.ask(f'{raidFrom} is raiding {raidTo} with {views} viewers!, please inform chat.')
        await self.bot.http.sendChatMessage(f'{r}')
        await self.bot.obsws.set_source_text(textscene, f" {raidFrom} is raiding with {views} viewers!")
        for a in altscenes:
            await self.bot.obsws.show_source(a, scene)
        await self.bot.obsws.show_and_wait('hotfeet', scene)
        await self.bot.obsws.set_source_text(textscene, "")
        for a in altscenes:
            await self.bot.obsws.hide_source(a, scene)



class ChannelFollowAlert(Alert):
    """channel.follow"""
    async def process(self):
        uname = self.data['user_name']
        logger.info(f"[Bot] {uname} followed!")
        await self.bot.http.sendChatMessage(f"Thank you for the follow! @{uname} s4w3d0FfLuv")
        await self.bot.obsws.set_source_text(textscene, f" {uname} joined the cabbage patch!")
        for a in altscenes:
            await self.bot.obsws.show_source(a, scene)
        await self.bot.obsws.show_and_wait('greasy', scene)
        await self.bot.obsws.set_source_text(textscene, "")
        for a in altscenes:
            await self.bot.obsws.hide_source(a, scene)