import asyncio
import os
import aiofiles
import logging
from aiohttp import web
from poolguy.storage import loadJSON
from poolguy import command, rate_limit, route, CommandBot
from poolguy.twitch import UIBot
from plugins import (
    TesterBot, SpotifyBot, TarkovBot, ChatBot,
    SubathonBot, AIBot, GoalBot, BannedBot, OBSBot
)

logger = logging.getLogger(__name__)

#==========================================================================================
# MainBot =================================================================================
#==========================================================================================
class MyBot(
        OBSBot, SubathonBot, GoalBot, BannedBot, 
        SpotifyBot, TarkovBot, CommandBot, 
        ChatBot, TesterBot, UIBot
        ):
    def __init__(self, *args, **kwargs):
        # Fetch sensitive data from environment variables
        client_id = os.getenv("SOE_CLIENT_ID")
        client_secret = os.getenv("SOE_CLIENT_SECRET")
        spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        obsws_password = os.getenv("OBSWS_PASSWORD")
        if not client_id or not client_secret or not spotify_client_id or not spotify_client_secret:
            raise ValueError(f"Environment variables are required: {[
                'SOE_CLIENT_ID', 'SOE_CLIENT_SECRET', 
                'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'OBSWS_PASSWORD'
                ]}")
        kwargs['twitch_config']['client_id'] = client_id
        kwargs['twitch_config']['client_secret'] = client_secret
        kwargs['spotify_cfg']['client_id'] = spotify_client_id
        kwargs['spotify_cfg']['client_secret'] = spotify_client_secret
        kwargs['obs_cfg']['password'] = obsws_password
        super().__init__(*args, **kwargs)

    async def after_login(self):
        await self.setup_chat()
        self.spotify.token_handler.storage = self.http.storage
        await self.spotify.login()
        if not self.http.server.is_running() and self.http.server.route_len() > 2:
            await self.http.server.start()
        await self.eft.start()
        self.subathon.start()
        self.subathon.pause()
        await self.obsws._setup()
        await self.refresh_obs_scenes()
        

    async def refresh_obs_scenes(self):
        await self.obsws.hide_source(source_name="Goals", scene_name="[S] Goals")
        await asyncio.sleep(2)
        await self.obsws.show_source(source_name="Goals", scene_name="[S] Goals")

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

    @route('/endcredits')
    async def endcredits_route(self, request):
        credits = "<br><h2>Director</h2>s4w3d0ff"
        subs = self._cleanSubs(await self.http.getBroadcasterSubscriptions())
        if len(subs['t3']) > 0:
            credits += "<br><h2>Producers</h2>" + '<br> '.join(subs['t3'])
        if len(subs['t2']) > 0:
            credits += "<br><h2>Executive Producers</h2>" + '<br> '.join(subs['t2'])
        credits += "<br><h2>Writers</h2>" + "<br> ".join([i["user_name"] for i in await self.http.getModerators()])
        credits += "<br><h2>Editors</h2>" + "<br> ".join([i["user_name"] for i in await self.http.getVIPs()])
        if len(subs['t1']) > 0:
            credits += "<br><h2>Lead Cast</h2>" + '<br> '.join(subs['t1'])
        # add followers
        credits += "<br><h2>Supporting Cast</h2>"
        followers = await self.http.getChannelFollowers()
        credits += '<br> '.join([f["user_name"] for f in followers])
        async with aiofiles.open("templates/credits.html", 'r', encoding='utf-8') as f:
            template = await f.read()
            rendered = template.replace("{{ credits }}", credits)
            return web.Response(text=rendered, content_type='text/html', charset='utf-8')

    @route('/queue/ui')
    async def queue_ui_route(self, request):
        return await self.app.response_html('templates/queue_ui.html')

    @route('/ads')
    async def ads_route(self, request):
        return await self.app.response_html('templates/ads.html')

    @command(name="cheers", aliases=["bits"])
    @rate_limit(calls=1, period=60, warn_cooldown=30)
    async def cheers_cmd(self, user, channel, args):
        cfg = loadJSON("db/cheers_cfg.json")
        each = [f"[{key} - {cfg[key]['name']}] " for key, value in cfg.items()]
        out = ""
        for i in each:
            if len(out)+len(i) > 400:
                await self.send_chat(out, channel["broadcaster_id"])
                out = f"{i}"
            else:
                out += f"{i}"
        if len(out) > 0:
            await self.send_chat(out, channel["broadcaster_id"])


if __name__ == '__main__':
    from plugins import alert_objs
    from rich.logging import RichHandler
    logging.basicConfig(
        format='%(message)s',
        datefmt="%X",
        level=logging.INFO,
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
    logging.getLogger('simpleobsws').setLevel(logging.INFO)
    cfg = loadJSON("config.json")
    cfg['alert_objs'] = alert_objs
    cfg['twitch_config']['base_dir'] = os.path.dirname(os.path.abspath(__file__))
    bot = MyBot(**cfg)
    asyncio.run(bot.start(paused=True))