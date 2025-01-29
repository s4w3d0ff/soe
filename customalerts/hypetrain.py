from poolguy.utils import ColorLogger
from poolguy.twitchws import Alert

logger = ColorLogger("HypeTrainProgressAlert")

scene = "[S] Dumpster Chat"

cfg = {
    "1": "fire1",
    "2": "fire2",
    "3": "fire3",
    "4": "fire4"
}

class ChannelHypeTrainProgressAlert(Alert):
    """channel.hype_train.progress"""
    async def process(self):
        for k in cfg:
            if int(k) <= self.data['level']:
                await self.bot.obsws.show_source(cfg[k], scene)

class ChannelHypeTrainEndAlert(Alert):
    """channel.hype_train.end"""
    async def process(self):
        for k in cfg:
            await self.bot.obsws.hide_source(cfg[k], scene)
