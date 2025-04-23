import json
import random
import logging
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
bit_altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
bit_text = "CheerText"
tts_limit = 123
tts_source = "bit_tts"
tts_path = "db/bit_tts.mp3"

class ChannelBitsUse(Alert):
    queue_skip = False
    priority = 1

    def remove_cheermotes(self, message):
        # this needs to be fixed so that it doesnt remove reqular emotes
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
        if self.data["message"] and amount >= tts_limit:
            text = self.remove_cheermotes(self.data["message"])
        if text:
            voice = random.choice(list(VOICES.keys()))
            await generate_speech(text, tts_path, voice)
        txt = cheer_cfg[alertK]['text'].replace("{user}", usr).replace("{amount}", str(amount))
        await self.bot.obsws.set_source_text(bit_text, ' '+txt)
        for a in bit_altscenes:
            await self.bot.obsws.show_source(a, bit_scene)
        await self.bot.obsws.show_and_wait(cheer_cfg[alertK]['source'], bit_scene)
        await self.bot.obsws.set_source_text(bit_text, "")
        for a in bit_altscenes:
            await self.bot.obsws.hide_source(a, bit_scene)
        if text:
            await self.bot.obsws.show_and_wait(tts_source, bit_scene)