import asyncio
import os
import json
import time
import aiofiles
import logging
from aiohttp import web
from datetime import datetime, timedelta
from poolguy.storage import aioLoadJSON
from poolguy import TwitchBot, route, websocket

logger = logging.getLogger(__name__)

#==========================================================================================
# GoalBot =================================================================================
#==========================================================================================
class GoalBot(TwitchBot):
    def __init__(self, goals_cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.goals_cfg = goals_cfg
        self.goal_queue = asyncio.Queue()
        self.alertws_queue = asyncio.Queue()

    @route('/goals')
    async def goals(self, request):
        async with aiofiles.open('templates/goals.html', 'r', encoding='utf-8') as f:
            template = await f.read()
            return web.Response(text=template, content_type='text/html', charset='utf-8')
    
    async def get_total_cheers(self, days_back=30, base_dir='db/alerts/channel.cheer'):
        current_date = datetime.now()
        earliest_date = current_date - timedelta(days=days_back)
        total_bits = 0
        current = current_date
        while current >= earliest_date:
            date_str = current.strftime('%Y-%m-%d')
            file_path = os.path.join(base_dir, f'{date_str}.json')
            if os.path.exists(file_path):
                try:
                    data = await aioLoadJSON(file_path)
                    for cheer in data.values():
                        if isinstance(cheer, dict) and 'bits' in cheer:
                            total_bits += cheer['bits']
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading {file_path}: {e}")
            current = current - timedelta(days=1)
        return total_bits
        
    async def send_current_bits_amount(self, ws):
        cheers = await self.get_total_cheers(base_dir='db/alerts/channel.cheer') # going to be deprecated
        bits = await self.get_total_cheers(base_dir='db/alerts/channel.bits.use')
        out = {
            "progress_type": "bits",
            "amount": cheers + bits
        }
        logger.debug(f"send_current_bits_amount: {out}")
        await ws.send_json(out)

    async def send_subgoal_update(self, ws):
        data = await self.http.getBroadcasterSubscriptions()
        out = {'t1': 0, 't2': 0, 't3': 0}
        for i in data:
            if i['user_id'] == self.http.user_id:
                continue
            out[f"t{i['tier'][0]}"] += 1

        for tier, value in out.items():
            await asyncio.sleep(0.5)
            o = {
                "progress_type": tier,
                "amount": value
            }
            logger.debug(f"send_subgoal_update: {o}")
            await ws.send_json(o)
            
    @websocket('/goalsws')
    async def goals2ws(self, ws, request):
        logger.warning(f"Websocket connected: goalsws")
        while not self.http.user_id:
            logger.error(f"goalsws error: not logged in yet")
            await ws.ping()
            await asyncio.sleep(10)
            
        await ws.send_json({
            "progress_type": "total",
            "amount": self.goals_cfg['total']
        })
        await self.send_subgoal_update(ws)
        await self.send_current_bits_amount(ws)
        
        last_sub_update = time.time()
        while not ws.closed:
            try:
                update = await asyncio.wait_for(self.goal_queue.get(), timeout=15)
                if update['gtype'] in ["", "new_bit", "new_bits"]:
                    await asyncio.sleep(5)
                    await self.send_current_bits_amount(ws)
                if update['gtype'] == "subscription_count":
                    if time.time()-last_sub_update >= 120:
                        await asyncio.sleep(5)
                        await self.send_subgoal_update(ws)
                        last_sub_update = time.time()
                self.goal_queue.task_done()
            except asyncio.TimeoutError:
                await ws.ping()
                continue
            except Exception as e:
                logger.error(f"Unexpected error in goalsws loop: {e}")
                break
        logger.warning("goalsws connection closed")

    #=====================================================================
    @route('/alerts')
    async def alerts(self, request):
        async with aiofiles.open('templates/alerts.html', 'r', encoding='utf-8') as f:
            template = await f.read()
            return web.Response(text=template, content_type='text/html', charset='utf-8')

    @websocket('/alertsws')
    async def alertsws(self, ws, request):
        while not self.http.user_id:
            logger.error(f"alertsws error: not logged in yet")
            await asyncio.sleep(10)
        # Keep connection alive and wait for updates
        logger.warning(f"Websocket connected: alertsws")
        while not ws.closed:
            try:
                update = await asyncio.wait_for(self.alertws_queue.get(), timeout=15)
                await ws.send_json(update)
                self.alertws_queue.task_done()
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                await ws.ping()
                continue
            except Exception as e:
                logger.error(f"Unexpected error in alertsws loop: {e}")
                break
        # Clean up
        if not ws.closed:
            await ws.close()
        logger.warning("alertsws connection closed")