from poolguy.utils import ColorLogger, json
from poolguy.twitchws import Alert

logger = ColorLogger("GoalProgressAlert")

class ChannelGoalProgressAlert(Alert):
    """channel.goal.progress"""
    async def process(self):
        logger.debug(f"{json.dumps(self.data, indent=2)}")
        g_type = self.data['type']
        if g_type in ["", "new_bits", "subscription_count"]:
            await self.bot.goal_queue.put({
                "gtype": g_type,
                "amount": int(self.data['current_amount'])
            })
        logger.warning(f"{g_type} goal updated to {self.data['current_amount']}")
