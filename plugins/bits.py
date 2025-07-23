import json
import random
import logging
import asyncio
from poolguy.storage import loadJSON
from poolguy import TwitchBot, Alert, websocket, route
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
                await self._process_alert(amount, alertK, text)
        if self.data["type"] == "power_up":
            logger.warning(self.data["power_up"])
            if self.data["power_up"]["type"] == "gigantify_an_emote":
                formats = self.data["message"]["fragments"][0]["emote"]["format"]
                fmat = 'animated' if 'animated' in formats else 'static'
                url = f'https://static-cdn.jtvnw.net/emoticons/v2/{self.data["power_up"]["emote"]["id"]}/{fmat}/dark/3.0'
                if hasattr(self.bot, 'totem_queue'):
                    await self.bot.totem_queue.put(url)
                    self.bot.current_totem.append(url)
                    self.bot.current_totem = self.bot.current_totem[-5:]


    async def _whatever(self):
       source = f'whatever{random.randint(1,4)}'
       await self.bot.obsws.show_source(source, bit_scene)
       await asyncio.sleep(2)
       await self.bot.obsws.hide_source(source, bit_scene)

    @duck_volume(volume=40)
    async def _process_alert(self, amount, alertK, text):
        usr = str(self.data['user_name'])
        txt = cheer_cfg[alertK]['text'].replace("{user}", usr).replace("{amount}", str(amount))
        await self.bot.obsws.set_source_text(bit_text, ' '+txt)
        for a in bit_altsources:
            await self.bot.obsws.show_source(a, bit_scene)
        await self.bot.obsws.show_and_wait(cheer_cfg[alertK]['source'], bit_scene)
        await self.bot.obsws.set_source_text(bit_text, "")
        for a in bit_altsources:
            await self.bot.obsws.hide_source(a, bit_scene)
        if text and amount >= tts_limit:
            voice = random.choice(list(VOICES.keys()))
            await generate_speech(text, tts_path, voice)
            await self.bot.obsws.show_and_wait(tts_source, bit_scene)

class TotemBot(TwitchBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.totem_queue = asyncio.Queue()
        self.current_totem = []

    @websocket('/totempolews')
    async def totempolews(self, ws, request):
        logger.warning(f"Websocket connected: totempolews")
        await self.ws_wait_for_twitch_login(ws)
        self.current_totem = await self.storage.load_token("totempole") or []
        for item in self.current_totem:
            await asyncio.sleep(1)
            await ws.send_json({"imageUrl": item})
        while not ws.closed:
            try:
                update = await asyncio.wait_for(self.totem_queue.get(), timeout=15)
                await ws.send_json({"imageUrl": update})
                await self.storage.save_token(self.current_totem, "totempole")
                await asyncio.sleep(1)
            except asyncio.TimeoutError:
                await ws.ping()
                continue
            except Exception as e:
                logger.error(f"Unexpected error in totempolews loop: {e}")
                break
        logger.warning("totempolews connection closed")

    @route('/totempole')
    async def totempole(self, request):
        return await self.app.response_html('templates/totem.html')