import logging
import json
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

    async def store(self):
        await self.bot.storage.insert(
            "channel_hype_train_end", 
            {
                "timestamp": self.timestamp,
                "message_id": self.message_id,
                "total": self.data["total"],
                "level": self.data["level"],
                "cooldown_ends_at": self.data["cooldown_ends_at"],
                "top_contributions": json.dumps(self.data["top_contributions"])
            }
        )
    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in hype_cfg:
                await self.bot.obsws.hide_source(hype_cfg[k], hype_scene)