from poolguy.utils import asyncio, os, json, webbrowser, time
from poolguy.utils import ColorLogger, loadJSON, MaxSizeDict, cmd_rate_limit, randString, ctxt
from poolguy.twitch import CommandBot
from poolguy.tester import Tester
from poolguy.twitchws import Alert
from customalerts.plugins.obsapi import OBSController
from customalerts.plugins.skynet import AI
from customalerts.plugins.spotifyapi import Spotify
import aiofiles
from aiohttp import web

logger = ColorLogger(__name__)

class MyBot(Tester):
    def __init__(self, goals_cfg, obs_cfg, ai_cfg, spotify_cfg, *args, **kwargs):
        # Fetch sensitive data from environment variables
        client_id = os.getenv("SOE_CLIENT_ID")
        client_secret = os.getenv("SOE_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("Environment variables SOE_CLIENT_ID and SOE_CLIENT_SECRET are required")
        kwargs['http_config']['client_id'] = client_id
        kwargs['http_config']['client_secret'] = client_secret
        #===============================================
        super().__init__(*args, **kwargs)
        self.obsws = OBSController(**obs_cfg)
        self.spotify = Spotify(**spotify_cfg)
        self.ai = AI(**ai_cfg)
        self.goals_cfg = goals_cfg
        self.goal_queue = asyncio.Queue()
        self.chat_queue = asyncio.Queue()
        self.alertws_queue = asyncio.Queue()
        self.banHTML = ""
        self.channelBadges = {}
        self.alertDone = True

    async def after_login(self):
        self.channelBadges[str(self.http.user_id)] = await self.getChanBadges(self.http.user_id)
        await self.obsws._setup()
        await self.spotify.login()
        await self.ai.wait_for_setup()
    
    def _cleanSubs(self, data):
        out = {'t1': [], 't2': [], 't3': []}
        for i in data:
            if i['user_id'] == self.http.user_id:
                continue
            out['t' + i['tier'][0]].append(i["user_name"])
        return out

    async def getChanBadges(self, bid=None, size='image_url_4x'):
        r = await self.http.getGlobalChatBadges()
        r += await self.http.getChannelChatBadges(bid)
        badges = {}
        for i in r:
            badges[i['set_id']] = {b['id']: b[size] for b in i['versions']}
        return badges

    def register_routes(self):
        @self.app.route("/alertended")
        def alertended(request):
            self.alertDone = True
            return web.json_response({"status": True})

        @self.app.route('/banned')
        async def banned(request):
            return web.Response(text=self.banHTML, content_type='text/html', charset='utf-8')

        @self.app.route('/endcredits')
        async def endcredits(request):
            credits = "<br>"
            subs = self._cleanSubs(await self.http.getBroadcasterSubscriptions())
            if len(subs['t3']) > 0:
                credits += "<br><h2>Tier 3 Subs</h2>" + '<br> '.join(subs['t3'])
            if len(subs['t2']) > 0:
                credits += "<br><h2>Tier 2 Subs</h2>" + '<br> '.join(subs['t2'])
            if len(subs['t1']) > 0:
                credits += "<br><h2>Tier 1 Subs</h2>" + '<br> '.join(subs['t1'])
            # add followers
            credits += "<br><h2>Followers</h2>"
            followers = await self.http.getChannelFollowers()
            credits += '<br> '.join([f["user_name"] for f in followers])
            async with aiofiles.open("templates/credits.html", 'r', encoding='utf-8') as f:
                template = await f.read()
                rendered = template.replace("{{ credits }}", credits)
                return web.Response(text=rendered, content_type='text/html', charset='utf-8')
        
        @self.app.route('/matrix')
        async def matrix(request):
            async with aiofiles.open('templates/matrix.html', 'r', encoding='utf-8') as f:
                template = await f.read()
                return web.Response(text=template, content_type='text/html', charset='utf-8')
        #=====================================================================
        #=====================================================================
        @self.app.route('/goals')
        async def goals(request):
            async with aiofiles.open('templates/goals.html', 'r', encoding='utf-8') as f:
                template = await f.read()
                return web.Response(text=template, content_type='text/html', charset='utf-8')
        
        @self.app.websocket('/goalsws')
        async def goals2ws(ws, request):
            async def send_init_bit_goal(ws):
                data = await self.http.getCreatorGoals()
                for g in data:
                    if g['type'] in [""]:
                        out = {
                            "bar": self.goals_cfg['name'],
                            "progress_type": "bits",
                            "amount": int(g['current_amount'])
                        }
                        logger.debug(f"send_init_bit_goal: {out}")
                        await ws.send_json(out)
                        break

            async def send_subgoal_update(ws):
                value = {"t1": 250, "t2": 400, "t3": 1200}
                data = await self.http.getBroadcasterSubscriptions()
                out = {'t1': 0, 't2': 0, 't3': 0}
                for i in data:
                    if i['user_id'] == self.http.user_id:
                        continue
                    tier = f"t{i['tier'][0]}"
                    out[tier] += value[tier]

                for tier, value in out.items():
                    await asyncio.sleep(0.5)
                    o = {
                        "bar": self.goals_cfg['name'],
                        "progress_type": f"{tier}_subs",
                        "amount": value
                    }
                    logger.debug(f"send_subgoal_update: {o}")
                    await ws.send_json(o)
            
            while not self.http.user_id:
                logger.error(f"goalsws error: not logged in yet")
                await ws.ping()
                await asyncio.sleep(10)
            
            await ws.send_json({
                "bar": self.goals_cfg['name'],
                "progress_type": "total",
                "amount": self.goals_cfg['total']
            })
            await send_subgoal_update(ws)                
            await send_init_bit_goal(ws)
           
            last_sub_update = time.time()
            while not ws.closed:
                try:
                    update = await asyncio.wait_for(self.goal_queue.get(), timeout=15)
                    if update['gtype'] in ["", "new_bits"]:
                        await ws.send_json({
                            "bar": self.goals_cfg['name'],
                            "progress_type": "bits",
                            "amount": update["amount"] 
                        })
                    if update['gtype'] == "subscription_count":
                        if time.time()-last_sub_update >= 30:
                            await send_subgoal_update(ws)
                            last_sub_update = time.time()
                    self.goal_queue.task_done()
                except asyncio.TimeoutError:
                    await ws.ping()
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error in goalsws loop: {e}")
                    break
            # Clean up
            if not ws.closed:
                await ws.close()
            logger.warning("goalsws connection closed")
        #=====================================================================
        #=====================================================================
        @self.app.route('/chat')
        async def chat(request):
            async with aiofiles.open('templates/chat.html', 'r', encoding='utf-8') as f:
                template = await f.read()
                return web.Response(text=template, content_type='text/html', charset='utf-8')

        @self.app.websocket('/chatws')
        async def chatws(ws, request):
            while not self.http.user_id:
                logger.error(f"chatws error: not logged in yet")
                await asyncio.sleep(10)
            # Keep connection alive and wait for updates
            while not ws.closed:
                try:
                    update = await asyncio.wait_for(self.chat_queue.get(), timeout=15)
                    await ws.send_json(update)
                    self.chat_queue.task_done()
                except asyncio.TimeoutError:
                    # Send a ping to keep connection alive
                    await ws.ping()
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error in chatws loop: {e}")
                    break
            # Clean up
            if not ws.closed:
                await ws.close()
            logger.warning("chatws connection closed")
        #=====================================================================
        #=====================================================================
        @self.app.route('/alerts')
        async def alerts(request):
            async with aiofiles.open('templates/alerts.html', 'r', encoding='utf-8') as f:
                template = await f.read()
                return web.Response(text=template, content_type='text/html', charset='utf-8')

        @self.app.websocket('/alertsws')
        async def alertsws(ws, request):
            while not self.http.user_id:
                logger.error(f"alertsws error: not logged in yet")
                await asyncio.sleep(10)
            # Keep connection alive and wait for updates
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

        @self.app.route('/')
        async def index():
            out = await self.http.login()
            return web.json_response({"login": out})
        
        logger.info(f"[register_routes] Done")


if __name__ == '__main__':
    import logging
    from customalerts import alert_objs
    fmat = ctxt('%(asctime)s', 'yellow', style='d') + '-%(levelname)s-' + ctxt('[%(name)s]', 'purple', style='d') + ctxt(' %(message)s', 'green', style='d')
    logging.basicConfig(format=fmat, datefmt="%I:%M:%S%p", level=logging.INFO)
    cfg = loadJSON("config.json")
    cfg['alert_objs'] = alert_objs
    bot = MyBot(**cfg)
    asyncio.run(bot.start())