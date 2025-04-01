import aiofiles
import time
import logging
import asyncio
import os
from aiohttp import web
from typing import Callable, Dict, Optional
from poolguy import TwitchBot, route
from poolguy.storage import loadJSON, saveJSON

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
            init_time = None, 
            time_multiplier = 1.0, 
            value_multipliers = None, 
            on_end_callback = None
            ):
        self._json_file = os.path.join("db", f"subathon.json")
        if not init_time:
            try:
                old = loadJSON(self._json_file)
            except:
                old = {"remaining": 3600} # default to 1 hour if no init time is provided
            init_time = old["remaining"]
        self.timer = CountdownTimer(seconds=init_time, on_end_callback=on_end_callback or self.on_timer_end)
        self.time_multiplier: float = time_multiplier
        self.value_multipliers: Dict[str, float] = value_multipliers or {"bits": 1, "t1": 250, "t2": 400, "t3": 1200}
        self._last_stat_check: float = 0.0
        

    async def on_timer_end(self):
        """
        Default callback for when the timer ends.
        You can overwrite this method in a subclass or 'on_end_callback' parameter will overwrite this method.
        """
        logger.info("The subathon has ended.")
        # Add any additional logic you want to execute when the subathon ends here.

    def get_stats(self):
        """Get the current stats of the subathon."""
        stats = {
            "remaining": self.timer.remaining_time,
            "bits": self.value_multipliers["bits"] * self.time_multiplier,
            "t1": self.value_multipliers["t1"] * self.time_multiplier,
            "t2": self.value_multipliers["t2"] * self.time_multiplier,
            "t3": self.value_multipliers["t3"] * self.time_multiplier,
        }
        # Save stats to JSON file every 15 seconds
        if self._json_file and time.time() - self._last_stat_check > 5:
            self._last_stat_check = time.time()
            saveJSON(stats, self._json_file)
        return stats

    def get_time_left(self):
        """Get the time left in the countdown."""
        return self.timer.remaining_time

    def add_time(self, amount, multiplier=None):
        """Add time to the countdown based on the given multiplier."""
        if multiplier:
            seconds = amount * self.value_multipliers[multiplier] * self.time_multiplier
            logger.info(f"Adding {amount} {multiplier}(s), which is {seconds/60:.2f} minutes.")
        else:
            seconds = amount
            logger.info(f"Adding {amount} seconds.")
        self.timer.add_time(seconds)

    def remove_time(self, amount, multiplier=None):
        """Remove time from the countdown based on the given multiplier."""
        if multiplier:
            seconds = amount * self.value_multipliers[multiplier] * self.time_multiplier
            logger.info(f"Removing {amount} {multiplier}(s), which is {seconds/60:.2f} minutes.")
        else:
            seconds = amount
            logger.info(f"Removing {amount} seconds.")
        self.timer.remove_time(seconds)

    def start(self):
        """Start the countdown timer."""
        self.timer.start()

    def shutdown(self):
        """Shutdown the countdown timer."""
        self.timer.shutdown()

    def pause(self):
        """Pause the countdown timer."""
        self.timer.pause()

    def resume(self):
        """Resume the paused countdown timer."""
        self.timer.unpause()
    
    def is_running(self):
        """Check if the subathon timer is running."""
        return self.timer._running



#==========================================================================================
# SubathonBot =============================================================================
#==========================================================================================
class SubathonBot(TwitchBot):
    def __init__(self, subathon_cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subathon = Subathon(**subathon_cfg)

    async def after_login(self):
        self.subathon.start()
        self.subathon.pause()

    @route('/subathon/ui', method='GET')
    async def subathon_ui(self, request):
        async with aiofiles.open('templates/subathonui.html', 'r', encoding='utf-8') as f:
            template = await f.read()
            return web.Response(text=template, content_type='text/html', charset='utf-8')
        
    @route('/subathon/timer', method='GET')
    async def subathon_timer(self, request):
        async with aiofiles.open('templates/subathontimer.html', 'r', encoding='utf-8') as f:
            template = await f.read()
            return web.Response(text=template, content_type='text/html', charset='utf-8')

    @route('/subathon/pause', method='GET')
    async def subathon_pause(self, request):
        self.subathon.pause()
        return web.json_response({"status": True, "data": self.subathon.get_stats()})
    
    @route('/subathon/resume', method='GET')
    async def subathon_resume(self, request):
        self.subathon.resume()
        return web.json_response({"status": True, "data": self.subathon.get_stats()})
    
    @route('/subathon/stats', method='GET')
    async def subathon_stats(self, request):
        return web.json_response({"status": True, "data": self.subathon.get_stats()})

    @route('/subathon/addtime', method='POST')
    async def subathon_addtime(self, request):
        data = await request.json()
        if "amount" not in data:
            return web.json_response({"status": False, "data": data})
        self.subathon.add_time(amount=data["amount"], multiplier=data.get("multiplier", None))
        return web.json_response({"status": True, "data": self.subathon.get_stats()})

    @route('/subathon/removetime', method='POST')
    async def subathon_removetime(self, request):
        data = await request.json()
        if "amount" not in data:
            return web.json_response({"status": False, "data": data})
        self.subathon.remove_time(amount=data["amount"], multiplier=data.get("multiplier", None))
        return web.json_response({"status": True, "data": self.subathon.get_stats()})

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
        self.subathon.start()
        return web.json_response({"status": True, "data": self.subathon.get_stats()})