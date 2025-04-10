import json
import logging
from poolguy import Alert

logger = logging.getLogger(__name__)

#############################=========---------
### channel.goal.progress ###=============---------
#############################=================---------
class ChannelGoalProgress(Alert):
    queue_skip = True

    async def process(self):
        logger.debug(f"{json.dumps(self.data, indent=2)}")
        g_type = self.data['type']
        if hasattr(self.bot, 'goal_queue'):
            await self.bot.goal_queue.put({
                    "gtype": g_type,
                    "amount": int(self.data['current_amount'])
                })
            logger.warning(f"{g_type} goal updated to {self.data['current_amount']}")


###################################=========---------
### channel.hype_train.progress ###=============---------
###################################=================---------
class ChannelHypeTrainProgress(Alert):
    queue_skip = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hype_scene = "[S] Dumpster Chat"
        self.hype_cfg = {
            "1": "fire1",
            "2": "fire2",
            "3": "fire3",
            "4": "fire4"
        }
    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in self.hype_cfg:
                if int(k) <= self.data['level']:
                    await self.bot.obsws.show_source(self.hype_cfg[k], self.hype_scene)


##############################=========---------
### channel.hype_train.end ###=============---------
##############################=================---------
class ChannelHypeTrainEnd(Alert):
    queue_skip = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hype_scene = "[S] Dumpster Chat"
        self.hype_cfg = {
            "1": "fire1",
            "2": "fire2",
            "3": "fire3",
            "4": "fire4"
        }

    async def process(self):
        if hasattr(self.bot, 'obsws'):
            for k in self.hype_cfg:
                await self.bot.obsws.hide_source(self.hype_cfg[k], self.hype_scene)