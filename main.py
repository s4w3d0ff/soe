from poolguy.utils import asyncio, os, json, webbrowser, time, aiofiles, logging
from poolguy.utils import loadJSON, MaxSizeDict, randString, web, aioLoadJSON, datetime, timedelta
from poolguy.twitch import CommandBot, command, rate_limit
from poolguy.tester import Tester
from poolguy.twitchws import Alert
from poolguy.webserver import route, websocket
from custom.plugins.obsapi import OBSController
from custom.plugins.skynet import AI
from custom.plugins.spotifyapi import Spotify
from custom.plugins.trends import get_trending_now, to_pascal_case
from custom.plugins.tarkov import TarkovLogMonitor

logger = logging.getLogger(__name__)




class MyBot(Tester):
    def __init__(self, goals_cfg, obs_cfg, ai_cfg, spotify_cfg, eft_config, tags=None, *args, **kwargs):
        # Fetch sensitive data from environment variables
        client_id = os.getenv("SOE_CLIENT_ID")
        client_secret = os.getenv("SOE_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("Environment variables SOE_CLIENT_ID and SOE_CLIENT_SECRET are required")
        kwargs['twitch_config']['client_id'] = client_id
        kwargs['twitch_config']['client_secret'] = client_secret
        #===============================================
        super().__init__(*args, **kwargs)
        self.obsws = OBSController(**obs_cfg)
        self.spotify = Spotify(**spotify_cfg)
        self.ai = None #AI(**ai_cfg)
        self.eft = TarkovLogMonitor(**eft_config)
        self.eft.register_callback('game_prepared', self._eft_game_prepared)
        self.eft.register_callback('initialized', self._eft_initialized)
        self.goals_cfg = goals_cfg
        self.goal_queue = asyncio.Queue()
        self.chat_queue = asyncio.Queue()
        self.alertws_queue = asyncio.Queue()
        self.banHTML = ""
        self.channelBadges = {}
        self.alertDone = True
        self.base_tags = tags or []


    async def _eft_initialized(self, data):
        logger.warning(f"[Tarkov] Game initialized with version {data['version']}")
        try:
            r = await self.obsws.stop_recording()
            logger.warning(f"[Tarkov] Recording saved: {r}")
        except:
            pass
            
    async def _eft_game_prepared(self, data):
        logger.warning(f"[Tarkov] Game prepared: time={data['time_value']}, real={data['real_value']}, diff={data['diff_value']}")
        await self.obsws.start_recording()

    async def after_login(self):
        self.channelBadges[str(self.http.user_id)] = await self.getChanBadges(self.http.user_id)
        await self.obsws._setup()
        self.spotify.token_handler.storage = self.http.storage
        await self.spotify.login()
        if not self.http.server.is_running() and self.http.server.route_len() > 2:
            await self.http.server.start()
        await self.eft.start()
        #await self.ai.wait_for_setup()

    async def shutdown(self, reset=True):
        """Gracefully shutdown the bot"""
        logger.warning("Shutting down TwitchBot...")
        if not reset:
            self.is_running = False
        await self.eft.stop()
        logger.warning("Closing TwitchWS...")
        await self.ws.close()
        # Clear all tasks
        logger.warning("Clearing tasks...")
        for task in self._tasks:
            if task and not task.done():
                task.cancel()
        self._tasks.clear()
        await self.obsws.cleanup()
        await self.spotify.token_handler.stop()
        logger.warning("TwitchBot shutdown complete")

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
        return {i['set_id']: {b['id']: b[size] for b in i['versions']} for i in r}
    
    @command
    @rate_limit(calls=1, period=60, warn_cooldown=30)
    async def cheers(self, user, channel, args):
        """Shows cheer list """
        cfg = await aioLoadJSON("db/cheers_cfg.json")
        each = [f"[{key} {cfg[key]['name']}]" for key, value in cfg.items()]
        out = ""
        for i in each:
            if len(out)+len(i) > 400:
                await self.http.sendChatMessage(out, broadcaster_id=channel["broadcaster_id"])
                out = f"{i}"
            else:
                out += f"{i}"
        if len(out) > 0:
            await self.http.sendChatMessage(out, broadcaster_id=channel["broadcaster_id"])  

    @route("/alertended")
    def alertended(self, request):
        self.alertDone = True
        return web.json_response({"status": True})

    @route('/banned')
    async def banned(self, request):
        return web.Response(text=self.banHTML, content_type='text/html', charset='utf-8')

    @route('/endcredits')
    async def endcredits(self, request):
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
    
    @route('/matrix')
    async def matrix(self, request):
        async with aiofiles.open('templates/matrix.html', 'r', encoding='utf-8') as f:
            template = await f.read()
            return web.Response(text=template, content_type='text/html', charset='utf-8')

    #=====================================================================
    #=====================================================================

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
        current_amount = await self.get_total_cheers()
        out = {
            "progress_type": "bits",
            "amount": current_amount
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
    #=====================================================================

    @route('/chat')
    async def chat(self, request):
        async with aiofiles.open('templates/chat.html', 'r', encoding='utf-8') as f:
            template = await f.read()
            return web.Response(text=template, content_type='text/html', charset='utf-8')

    @websocket('/chatws')
    async def chatws(self, ws, request):
        while not self.http.user_id:
            logger.error(f"chatws error: not logged in yet")
            await asyncio.sleep(10)
        # Keep connection alive and wait for updates
        logger.warning(f"Websocket connected: chatsws")
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

if __name__ == '__main__':
    from custom import alert_objs
    from rich.logging import RichHandler
    logging.basicConfig(
        format='%(message)s',
        datefmt="%X",#"%I:%M:%S%p",
        level=logging.INFO,
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    logging.getLogger('aiohttp.access').setLevel(logging.INFO)
    logging.getLogger('simpleobsws').setLevel(logging.INFO)
    cfg = loadJSON("config.json")
    cfg['alert_objs'] = alert_objs
    cfg['twitch_config']['base_dir'] = os.path.dirname(os.path.abspath(__file__))
    bot = MyBot(**cfg)
    asyncio.run(bot.start())