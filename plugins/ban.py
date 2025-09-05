import logging
import json
import time
import asyncio
from poolguy import Alert
from .spotifyapi import duck_volume

logger = logging.getLogger(__name__)

ignorelist = ["streamelements", "nightbot"]
defaultpic = 'D:/Stream Stuff/OBS/Assets/Images/default_pic.jpg'
scene = "[S] Banned"

###################=========---------
### channel.ban ###=============---------
###################=================---------
class ChannelBan(Alert):
    """channel.ban"""
    queue_skip = False
    priority = 4

    async def getUserPic(self, uid):
        logger.debug(f"[Alert] Ban: getting user pic")
        try:
            r = await self.bot.http.getUsers(ids=uid)
            return r[0]['profile_image_url']
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return defaultpic
    
    async def store(self):
        await self.bot.storage.insert(
            "channel_ban",
            {
                "timestamp": self.timestamp,
                "message_id": self.message_id,
                "user_id": self.data["user_id"],
                "user_login": self.data["user_login"],
                "moderator_user_id": self.data["moderator_user_id"],
                "moderator_user_login": self.data["moderator_user_login"],
                "reason": self.data["reason"],
                "ends_at": self.data["ends_at"]
            }
        )

    @duck_volume(volume=40)
    async def process(self):
        logger.debug(f"[Alert] Ban: \n{json.dumps(self.data, indent=2)}")
        if self.data["moderator_user_login"] in ignorelist:
            return
        #scene = random.choice(["[S] TuckerBan", "[S] PacificBan"])
        source = "[S] TuckerBan"
        name = self.data['user_name']
        await self.bot.obsws.set_source_settings("banpic", {"file": await self.getUserPic(self.data["user_id"])})
        await self.bot.obsws.set_source_text("banname", self.data['user_name'])
        #dur = "permanently banned" if self.data['is_permanent'] else "timed out"
        #reason = self.data['reason']
        await self.bot.send_chat(f'Get rekt {name} Modding')
        await self.bot.obsws.show_and_wait(source, scene)
        await asyncio.sleep(2)
        await self.bot.obsws.set_source_settings("banpic", {"file": defaultpic})
        await self.bot.obsws.set_source_text("banname", "some child")
        await asyncio.sleep(2)

#######################################=========---------
### channel.suspicious_user.message ###=============---------
#######################################=================---------
class ChannelSuspiciousUserMessage(Alert):
    queue_skip = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cooldown = 15
        self.last = 0

    async def store(self):
        await self.bot.storage.insert(
            "channel_suspicious_user_message", 
            {
                "timestamp": self.timestamp,
                "message_id": self.message_id,
                "user_id": self.data["user_id"],
                "user_login": self.data["user_login"],
                "low_trust_status": self.data["low_trust_status"],
                "shared_ban_channel_ids": self.data["shared_ban_channel_ids"],
                "types": self.data["types"],
                "ban_evasion_evaluation": self.data["ban_evasion_evaluation"],
                "message": json.dumps(self.data["message"])
            }
        )

    async def process(self):
        if not time.time() - self.last > self.cooldown:
            return
        await self.bot.obsws.show_and_wait("amongsus", "[S] Videos")