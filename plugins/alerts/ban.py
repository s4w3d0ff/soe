import aiofiles
import json
import random
import asyncio
import logging
from poolguy import Alert
from plugins.spotifyapi import duck_volume

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
    
    @duck_volume(volume=40)
    async def process(self):
        self.bot.alertDone = False
        logger.debug(f"[Alert] Ban: \n{json.dumps(self.data, indent=2)}")
        if self.data["moderator_user_login"] in self.ignorelist:
            return
        dur = "permanently banned" if self.data['is_permanent'] else "timed out"
        reason = self.data['reason']
        name = self.data['user_name']
        if hasattr(self.bot, 'ai'):
            logger.debug(f"[Alert] Ban: starting ai thread")
            q = f'Please inform everyone that "{name}" was just {dur} from the chat for the reason: "{reason if reason else "Acting like a bot"}".'
            self.ai_thread = self.bot.ai.threaded_ask(q)
            await self.bot.http.sendChatMessage(f'{q}')
        else:
            await self.bot.http.sendChatMessage(f'Get rekt {name} Modding')
        picurl = await self.getUserPic(self.data["user_id"])
        banPage = random.choice(self.banPages)
        self.bot.banHTML = await self.render_page(banPage, name, picurl)
        await self.bot.obsws.show_source(self.source, self.scene)
        await self.wait_till_done()
        await self.bot.obsws.hide_source(self.source, self.scene)
