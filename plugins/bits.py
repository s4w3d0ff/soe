import json
import random
import logging
import asyncio
from poolguy.storage import loadJSON
from poolguy import Alert
from .spotifyapi import duck_volume
from .tts import generate_speech, VOICES

logger = logging.getLogger(__name__)

########################=========---------
### channel.bits.use ###=============---------
########################=================---------
cheer_cfg = loadJSON("db/cheers_cfg.json")

bit_scene = "[S] Bit Alerts"
bit_altsources = ["CheerText", "AlerttxtBG"]
bit_text = "CheerText"
tts_limit = 123
tts_source = "bit_tts"
tts_path = "db/bit_tts.mp3"
song_skip_amount = 213

class ChannelBitsUse(Alert):
    queue_skip = False
    priority = 1

    def remove_cheermotes(self, message):
        result = ""
        cheermotes = []
        for fragment in message.get('fragments', []):
            if fragment['type'] != 'cheermote':
                result += fragment.get('text', '')
            else:
               cheermotes.append(fragment)
        return result.strip(), cheermotes

    async def process(self):
        logger.info(f"[Bot] Bits: \n{json.dumps(self.data, indent=2)}")
        amount = int(self.data['bits'])
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(amount, 'bits')
        if self.data["type"] == "cheer":
            text, cheermotes = self.remove_cheermotes(self.data["message"])
            if text and amount >= tts_limit:
                voice = random.choice(list(VOICES.keys()))
                await generate_speech(text, tts_path, voice)
            if len(cheermotes) > 1:
                cheers = [frag["cheermote"]["bits"] for frag in cheermotes]
                # handle specific cheermote handling here if we want to 
                # this way we can handle split cheers
            alertK = None
            for k in [*cheer_cfg]:
                if amount < int(k):
                    break
                else:
                    alertK = k
            if alertK:
                if int(alertK) == 25:
                    await self._whatever()
                    return
                if int(alertK) == song_skip_amount:
                    if hasattr(self.bot, 'spotify'):
                        await self.bot.spotify.skip_track()
                await self._process(amount, alertK, text)
    
    async def _whatever(self):
       source = f'whatever{random.randint(1,4)}'
       await self.bot.obsws.show_source(source, bit_scene)
       await asyncio.sleep(2)
       await self.bot.obsws.hide_source(source, bit_scene)

    @duck_volume(volume=40)
    async def _process(self, amount, alertK, text):
        usr = str(self.data['user_name'])
        txt = cheer_cfg[alertK]['text'].replace("{user}", usr).replace("{amount}", str(amount))
        await self.bot.obsws.set_source_text(bit_text, ' '+txt)
        for a in bit_altsources:
            await self.bot.obsws.show_source(a, bit_scene)
        await self.bot.obsws.show_and_wait(cheer_cfg[alertK]['source'], bit_scene)
        await self.bot.obsws.set_source_text(bit_text, "")
        for a in bit_altsources:
            await self.bot.obsws.hide_source(a, bit_scene)
        if text:
            await self.bot.obsws.show_and_wait(tts_source, bit_scene)