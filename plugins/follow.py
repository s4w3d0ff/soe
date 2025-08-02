import logging
from poolguy import Alert
from .spotifyapi import duck_volume

logger = logging.getLogger(__name__)

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

    async def store(self):
        await self.bot.storage.insert(
            "channel_follow", 
            {
                "timestamp": self.timestamp,
                "message_id": self.message_id,
                "user_id": self.data["user_id"],
                "user_login": self.data["user_login"]
            }
        )

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