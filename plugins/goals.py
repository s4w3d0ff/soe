import asyncio
import json
import time
import logging
from poolguy import TwitchBot, Alert, route, websocket

logger = logging.getLogger(__name__)

class GoalBot(TwitchBot):
    def __init__(self, goals_cfg={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.goal_queue = asyncio.Queue()
        self.multi = goals_cfg.get("value_multipliers", {"t1": 250, "t2": 420, "t3": 2400, "bits": 1})
        self.goals = goals_cfg.get("goals", {"monthly": 6942069})
        self.bits_total = 0
        self.subs_total = {}
        self.last_sub_update = 0

    async def get_total_cheers(self, days_back=30):
        t = time.time()
        limit = 86400*days_back
        alerts = await self.storage.query('channel_bits_use', 'WHERE CAST(timestamp AS REAL) >= ?', (t-limit,))
        total_bits = 0
        for alert in alerts:
            total_bits += int(alert['bits'])
        return total_bits * self.multi["bits"]

    async def get_total_subs(self):
        data = await self.http.getBroadcasterSubscriptions()
        self.last_sub_update = time.time()
        s = {'t1': 0, 't2': 0, 't3': 0}
        for i in data:
            if i['user_id'] == self.http.user_id:
                # skip own subscription
                continue
            s[f"t{i['tier'][0]}"] += 1
        out = {}
        for teir, value in s.items():
            out[teir] = {"value": value * self.multi[teir], "amount": value}
        return out

    def calculate_goals(self, current_total, bits_total, subs_total):
        out = {
            "bits_total": bits_total,
            "subs_total": subs_total,
            "current_total": current_total,
            "goals": []
        }
        for goal_name, goal_total in self.goals.items():
            t = {
                "goal_name": goal_name,
                "goal_total": goal_total,
                "percent_complete": (current_total / goal_total) * 100,
                "total_needed": goal_total - current_total,
                "bits_total_needed": goal_total - current_total
            }
            for tier, amount in subs_total.items():
                t[f"{tier}_total_needed"] = int(t["total_needed"] / self.multi[tier])
            out["goals"].append(t)
        return out

    async def send_update(self, ws, update_type):
        if update_type == "subscription_count":
            if time.time()-self.last_sub_update >= 30:
                self.subs_total = await self.get_total_subs()
        else:
            self.bits_total = await self.get_total_cheers()
        out = self.calculate_goals(
            self.bits_total + sum([v["value"] for v in self.subs_total.values()]), 
            self.bits_total, 
            self.subs_total
        )
        await ws.send_json(out)

    @websocket('/goalsws')
    async def goalsws(self, ws, request):
        logger.warning(f"Websocket connected: goalsws")
        await self.ws_wait_for_twitch_login(ws)
        await self.send_update(ws, "subscription_count")
        await asyncio.sleep(2.5)
        await self.send_update(ws, "bits")
        await asyncio.sleep(5.5)
        """
        {
            "bits_total": int,
            "subs_total": {
                "t1": int,
                "t2": int,
                "t3": int
            },
            "current_total": int,
            "goals": [{
                "goal_name": str,
                "goal_total": int,
                "percent_complete": int,
                "total_needed": int,
                "bits_total_needed": int,
                "t1_total_needed": int,
                "t2_total_needed": int,
                "t3_total_needed": int
                }]
        }
        """
        while not ws.closed:
            try:
                update = await asyncio.wait_for(self.goal_queue.get(), timeout=15)
                await self.send_update(ws, update['gtype'])
                self.goal_queue.task_done()
            except ConnectionResetError:
                logger.warning("WebSocket client forcibly disconnected during send")
                break
            except asyncio.TimeoutError:
                try:
                    await ws.ping()
                except Exception as e:
                    logger.warning(f"Ping failed: {e}")
                    break
            except Exception as e:
                logger.error(f"Unexpected error in goalsws loop: {e}")
                break
        ws.exception()
        logger.warning("goalsws connection closed")

    @route('/goals')
    async def goalsroute(self, request):
        return await self.app.response_html('templates/goals.html')


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