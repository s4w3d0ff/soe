import time
import logging
import asyncio
from typing import Callable, Dict, Optional
from poolguy import TwitchBot, route, command, rate_limit, websocket

logger = logging.getLogger(__name__)

class CountdownTimer:
    """
    Asyncio based countdown timer that can be paused/resumed and time can be added/subtracted.
    A callback function can be set to call when the countdown ends.

    :param seconds: Initial countdown time in seconds (float).
    :param on_end_callback: Optional async callback function to call when timer ends (Callable[[], None]).
    """
    
    def __init__(self, seconds: float, on_end_callback: Optional[Callable[[], None]] = None):
        self.remaining_time: float = seconds
        self.on_end_callback: Callable[[], None] = on_end_callback or self._on_end_callback
        self._paused: bool = False
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None

    async def _on_end_callback(self):
        """Default on end callback, does nothing."""
        pass

    async def _run(self):
        """Core logic loop of the countdown timer. Ran in a task."""
        logger.debug(f"Starting countdown with {self.remaining_time/60:.2f} seconds.")
        # Use a high-resolution timer for accuracy.
        last_time = time.perf_counter()
        while self.remaining_time > 0 and self._running:
            if self._paused:
                # If paused, update the last_time so paused duration is not counted.
                last_time = time.perf_counter()
            else:
                now = time.perf_counter()
                elapsed = now - last_time
                self.remaining_time -= elapsed
                last_time = now
            # Sleep a short amount to keep the loop responsive.
            await asyncio.sleep(0.05)
        # Countdown finished.
        self.remaining_time = 0
        logger.info("Countdown finished.")
        self._running = False
        await self.on_end_callback()

    def start(self):
        """Start the countdown timer."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run())
        else:
           logger.warning("Countdown is already running.")

    def shutdown(self):
       """Shutdown the timer."""
       logger.info("Shutting down timer.")
       if self._running:
           self._task.cancel()
           self._running = False

    def pause(self):
        """Pause the timer."""
        self._paused = True
        logger.info("Timer paused.")

    def unpause(self):
        """Unpause the timer."""
        self._paused = False
        logger.info("Timer unpaused.")

    def add_time(self, seconds: float):
        """Add time (in seconds) to the remaining countdown."""
        self.remaining_time += seconds
        logger.info(f"Added {seconds} seconds to the countdown.")

    def remove_time(self, seconds: float):
        """Remove time (in seconds) from the remaining countdown."""
        self.remaining_time = max(0, self.remaining_time - seconds)
        logger.info(f"Removed {seconds} seconds from the countdown.")


class Subathon:
    """Class to manage a Subathon event."""
    def __init__(
            self,
            init_time=None,
            time_multiplier=1.0,
            value_multipliers=None,
            on_end_callback=None
            ):
        self.storage = None
        self._last_stat_check: float = 0.0
        self.time_multiplier: float = time_multiplier
        self.value_multipliers: Dict[str, float] = value_multipliers or {"bits": 1, "t1": 250, "t2": 400, "t3": 1200, "raids": 100}
        self.timer = None
        self.on_end_callback = on_end_callback or self.on_timer_end
        # Initialization deferred, because we need async for loading
        self._init_time = init_time

    async def init(self):
        """Async initialization to load from the database if needed."""
        if self._init_time:
            init_time = self._init_time
        if not self._init_time:
            old = await self.storage.load_token("subathon")
            init_time = old["remaining"] if old and "remaining" in old else 3600
        self.timer = CountdownTimer(seconds=init_time, on_end_callback=self.on_end_callback)

    async def on_timer_end(self):
        logger.info("The subathon has ended.")

    async def get_stats(self):
        stats = {
            "remaining": self.timer.remaining_time,
            "bits": self.value_multipliers["bits"] * self.time_multiplier,
            "t1": self.value_multipliers["t1"] * self.time_multiplier,
            "t2": self.value_multipliers["t2"] * self.time_multiplier,
            "t3": self.value_multipliers["t3"] * self.time_multiplier,
            "raids": self.value_multipliers["raids"] * self.time_multiplier
        }
        # Save stats to SQLite every 15 seconds
        if time.time() - self._last_stat_check > 15:
            self._last_stat_check = time.time()
            await self.storage.save_token("subathon", stats)
        return stats

    def get_time_left(self):
        return self.timer.remaining_time

    def add_time(self, amount, multiplier=None):
        seconds = amount * self.value_multipliers[multiplier] * self.time_multiplier if multiplier else amount
        self.timer.add_time(seconds)

    def remove_time(self, amount, multiplier=None):
        seconds = amount * self.value_multipliers[multiplier] * self.time_multiplier if multiplier else amount
        self.timer.remove_time(seconds)

    def start(self):
        self.timer.start()

    def shutdown(self):
        self.timer.shutdown()

    def pause(self):
        self.timer.pause()

    def resume(self):
        self.timer.unpause()

    def is_running(self):
        return self.timer._running


#==========================================================================================
# SubathonBot =============================================================================
#==========================================================================================
class SubathonBot(TwitchBot):
    def __init__(self, subathon_cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subathon = Subathon(**subathon_cfg)

    async def after_login(self):
        self.subathon.storage = self.http.storage
        await self.subathon.init()
        self.subathon.start()
        self.subathon.pause()


    @websocket('/subathonws')
    async def subathonws(self, ws, request):
        async def loop(ws, request):
            await ws.send_json({"status": True, "data": await self.subathon.get_stats()})
            await asyncio.sleep(0.5)
        await self.ws_hold_connection(ws, request, loop_func=loop, wait_for_twitch=True)

    @route('/subathon/ui', method='GET')
    async def subathon_ui(self, request):
        return await self.app.response_html('templates/subathon_ui.html')
        
    @route('/subathon/timer', method='GET')
    async def subathon_timer(self, request):
        return await self.app.response_html('templates/subathontimer.html')

    @route('/subathon/pause', method='GET')
    async def subathon_pause(self, request):
        self.subathon.pause()
        return self.app.response_json({"status": True, "data": await self.subathon.get_stats()})
    
    @route('/subathon/resume', method='GET')
    async def subathon_resume(self, request):
        self.subathon.resume()
        return self.app.response_json({"status": True, "data": await self.subathon.get_stats()})
    
    @route('/subathon/stats', method='GET')
    async def subathon_stats(self, request):
        return self.app.response_json({"status": True, "data": await self.subathon.get_stats()})

    @route('/subathon/addtime', method='POST')
    async def subathon_addtime(self, request):
        data = await request.json()
        if "amount" not in data:
            return self.app.response_json({"status": False, "data": data})
        self.subathon.add_time(amount=data["amount"], multiplier=data.get("multiplier", None))
        return self.app.response_json({"status": True, "data": await self.subathon.get_stats()})

    @route('/subathon/removetime', method='POST')
    async def subathon_removetime(self, request):
        data = await request.json()
        if "amount" not in data:
            return self.app.response_json({"status": False, "data": data})
        self.subathon.remove_time(amount=data["amount"], multiplier=data.get("multiplier", None))
        return self.app.response_json({"status": True, "data": await self.subathon.get_stats()})

    @route('/subathon/new/{init_time}', method='POST')
    async def subathon_new(self, request):
        cfg = {
            "init_time": float(request.match_info.get('init_time', 0)),
            "time_multiplier": self.subathon.time_multiplier,
            "value_multipliers": self.subathon.value_multipliers,
            "on_end_callback": self.subathon.timer.on_end_callback
        }
        logger.info(f"Starting new subathon with {cfg}")
        self.subathon.shutdown()
        self.subathon = Subathon(**cfg)
        self.subathon.storage = self.http.storage
        await self.subathon.init()
        self.subathon.start()
        return self.app.response_json({"status": True, "data": await self.subathon.get_stats()})

    @command(name="subathon", aliases=["streamathon, eggathon"])
    @rate_limit(calls=1, period=60, warn_cooldown=30)
    async def subathon_cmd(self, user, channel, args):
        """Shows Subathon stats """
        remaining_time = self.subathon.get_time_left()
        if remaining_time >= 60:
            remaining_time = f"{int(remaining_time / 60)} minutes and {int(remaining_time % 60)} seconds"
        else:
            remaining_time = f"{int(remaining_time)} seconds"
        if self.subathon.timer._paused:
            await self.send_chat(f"Subathon is paused with {remaining_time} remaining.", broadcaster_id=channel["broadcaster_id"])
            return
        if self.subathon.is_running():
            await self.send_chat(f"Subathon is currently running with {remaining_time} left!", broadcaster_id=channel["broadcaster_id"])
            txt = "".join(
                [f"[ {k} = {v} second(s) ]" if v < 60 else f"[ {k} = {int(v / 60)} minute(s) and {int(v % 60)} second(s) ]" for k, v in self.subathon.value_multipliers.items()]
                )
            await self.send_chat(txt, broadcaster_id=channel["broadcaster_id"])