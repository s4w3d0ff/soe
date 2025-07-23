import logging
import aiofiles
import json
import random
import asyncio
from aiohttp import web
from poolguy import TwitchBot, Alert, route
from .spotifyapi import duck_volume

logger = logging.getLogger(__name__)

banPages = ['templates/ban-pacific.html', 'templates/ban-tucker.html']
ignorelist = ["streamelements", "nightbot"]
defaultpic = "images/default_pic.jpg"
scene = "[M] Main"
source = "[S] Banned"

#==========================================================================================
# BannedBot ===============================================================================
#==========================================================================================
class BannedBot(TwitchBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.banHTML = ""
        self.alertDone = True

    @route("/alertended")
    def alertended(self, request):
        self.alertDone = True
        return self.app.response_json({"status": True})

    @route('/banned')
    async def banned(self, request):
        return web.Response(text=self.banHTML, content_type='text/html', charset='utf-8')

###################=========---------
### channel.ban ###=============---------
###################=================---------
class ChannelBan(Alert):
    """channel.ban"""
    queue_skip = False
    priority = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            return defaultpic
    
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

    async def store(self):
        self.bot.storage.channel_ban(**{
                "timestamp": self.timestamp,
                "user_id": self.data["user_id"],
                "user_login": self.data["user_login"],
                "moderator_user_id": self.data["moderator_user_id"],
                "moderator_user_login": self.data["moderator_user_login"],
                "reason": self.data["reason"],
                "ends_at": self.data["ends_at"]
            })

    @duck_volume(volume=40)
    async def process(self):
        self.bot.alertDone = False
        logger.debug(f"[Alert] Ban: \n{json.dumps(self.data, indent=2)}")
        if self.data["moderator_user_login"] in ignorelist:
            return
        dur = "permanently banned" if self.data['is_permanent'] else "timed out"
        reason = self.data['reason']
        name = self.data['user_name']
        await self.bot.http.sendChatMessage(f'Get rekt {name} Modding')
        picurl = await self.getUserPic(self.data["user_id"])
        banPage = random.choice(banPages)
        self.bot.banHTML = await self.render_page(banPage, name, picurl)
        await self.bot.obsws.show_source(source, scene)
        await self.wait_till_done()
        await self.bot.obsws.hide_source(source, scene)


#######################################=========---------
### channel.suspicious_user.message ###=============---------
#######################################=================---------
class ChannelSuspiciousUserMessage(Alert):
    queue_skip = True

    async def store(self):
        self.bot.storage.channel_suspicious_user_message(**{
            "timestamp": self.timestamp,
            "user_id": self.data["user_id"],
            "user_login": self.data["user_login"],
            "low_trust_status": self.data["low_trust_status"],
            "shared_ban_channel_ids": self.data["shared_ban_channel_ids"],
            "types": self.data["types"],
            "ban_evasion_evaluation": self.data["ban_evasion_evaluation"],
            "message": self.data["message"]["text"]
        })

    async def process(self):
        logger.warning(f"{json.dumps(self.data, indent=4)}")