import logging
from poolguy import Alert

logger = logging.getLogger(__name__)

hype_scene = "[S] Dumpster Chat"
hype_cfg = {
    "1": "fire1",
    "5": "fire2",
    "10": "fire3",
    "15": "fire4"
    }

###################################=========---------
### channel.hype_train.progress ###=============---------
###################################=================---------
class ChannelHypeTrainProgress(Alert):
    queue_skip = True
    store = False
    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in hype_cfg:
                if int(k) <= self.data['level']:
                    await self.bot.obsws.show_source(hype_cfg[k], hype_scene)


##############################=========---------
### channel.hype_train.end ###=============---------
##############################=================---------
class ChannelHypeTrainEnd(Alert):
    queue_skip = True
    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in hype_cfg:
                await self.bot.obsws.hide_source(hype_cfg[k], hype_scene)