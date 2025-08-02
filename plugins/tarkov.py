import re
import logging
import asyncio
from pathlib import Path
from collections import defaultdict
from poolguy import TwitchBot

logger = logging.getLogger(__name__)

class TarkovLogMonitor:
    def __init__(self, base_log_path, log_names=None):
        self.base_path = Path(base_log_path)
        self.log_names = log_names or ["application", "network-connection"]
        self.callbacks = defaultdict(list)
        self.file_positions = {}
        self.running = False
        
        self.patterns = {
            'game_prepared': (
                r'GamePrepared:(?P<time_value>[\d.]+)\s+real:(?P<real_value>[\d.]+)\s+diff:(?P<diff_value>[\d.]+)',
                self._parse_game_prepared
            ),
            'select_profile': (
                r'SelectProfile ProfileId:(?P<profile_id>[a-f0-9]+)\s+AccountId:(?P<account_id>\d+)',
                self._parse_select_profile
            ),
            'connect': (
                r'Connect \(address:\s*(?P<address>[\d.]+):(?P<port>\d+)',
                self._parse_connect
            ),
            'disconnect': (
                r'Disconnect \(address:\s*(?P<address>[\d.]+):(?P<port>\d+)',
                self._parse_disconnect
            ),
            'statistics': (
                r'Statistics \(address:\s*(?P<address>[\d.]+):(?P<port>\d+),\s*rtt:\s*(?P<rtt>[\d.]+),\s*lose:\s*(?P<lose>[-\dE.]+),\s*sent:\s*(?P<sent>\d+),\s*received:\s*(?P<received>\d+)',
                self._parse_statistics
            ),
            'initialized': (
                r'Initialized\s*\(v(?P<version>[\d.]+)\)',
                self._parse_initialized
            )
        }

    def _parse_game_prepared(self, match, line):
        return {
            'time_value': float(match.group('time_value')),
            'real_value': float(match.group('real_value')),
            'diff_value': float(match.group('diff_value')),
            'raw': line
        }

    def _parse_select_profile(self, match, line):
        return {
            'profile_id': match.group('profile_id'),
            'account_id': match.group('account_id'),
            'raw': line
        }

    def _parse_connect(self, match, line):
        return {
            'address': match.group('address'),
            'port': int(match.group('port')),
            'raw': line
        }

    def _parse_disconnect(self, match, line):
        return {
            'address': match.group('address'),
            'port': int(match.group('port')),
            'raw': line
        }

    def _parse_statistics(self, match, line):
        return {
            'address': match.group('address'),
            'port': int(match.group('port')),
            'rtt': float(match.group('rtt')),
            'lose': float(match.group('lose')),
            'sent': int(match.group('sent')),
            'received': int(match.group('received')),
            'raw': line
        }
        
    def _parse_initialized(self, match, line):
        return {
            'version': match.group('version'),
            'raw': line
        }
        
    def register_callback(self, event_name, callback):
        if event_name not in self.patterns:
            raise ValueError(f"Unknown event: {event_name}")
        self.callbacks[event_name].append(callback)
        
    def _get_latest_log_folder(self):
        folders = [f for f in self.base_path.glob("log_*")]
        return max(folders, key=lambda x: x.stat().st_mtime) if folders else None

    def _process_line(self, line):
        for event_name, (pattern, parser) in self.patterns.items():
            match = re.search(pattern, line)
            if match:
                parsed_data = parser(match, line)
                parsed_data['timestamp'] = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)', line).group(1)
                for callback in self.callbacks[event_name]:
                    asyncio.create_task(callback(parsed_data))
                    
    async def _monitor_file(self, file_name, folder):
        base_name = folder.name.replace('log_', '')
        possible_paths = [
            folder / f"{base_name} {file_name}.log",   # Pattern with space
            folder / f"{base_name}-{file_name}.log",   # Pattern with hyphen
            folder / f"{base_name}_{file_name}.log",   # Pattern with underscore
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            logger.debug(f"Waiting for log file, checking patterns: {[str(p) for p in possible_paths]}")
            while not file_path and self.running:
                await asyncio.sleep(15)
                for path in possible_paths:
                    if path.exists():
                        file_path = path
                        break
        
        if not self.running:
            return
            
        logger.warning(f"Monitoring log file: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Seek to end of file for initial opening
                if file_path not in self.file_positions:
                    f.seek(0, 2)  # Seek to end of file
                    self.file_positions[file_path] = f.tell()
                else:
                    f.seek(self.file_positions[file_path])
                
                while self.running:
                    where = f.tell()
                    line = f.readline()
                    if line:
                        logger.debug(f"[{file_name}]: {line.strip()}")
                        self._process_line(line.strip())
                        self.file_positions[file_path] = f.tell()
                    else:
                        await asyncio.sleep(1)
                        f.seek(where)
        except Exception:
            logger.exception(f"Error monitoring {file_path}:")
            
        logger.warning(f"Monitoring ended for: {file_path}")

    async def _monitor_logs(self):
        current_folder = None
        current_tasks = []
        
        while self.running:
            latest_folder = self._get_latest_log_folder()
            
            if latest_folder != current_folder:
                logger.info(f"New log folder detected: {latest_folder}")
                
                # Cancel existing monitoring tasks
                for task in current_tasks:
                    task.cancel()
                current_tasks.clear()
                self.file_positions.clear()
                
                # Start new monitoring tasks
                current_folder = latest_folder
                if current_folder:
                    for name in self.log_names:
                        task = asyncio.create_task(self._monitor_file(name, current_folder))
                        current_tasks.append(task)
            
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            
        # Cleanup on exit
        for task in current_tasks:
            task.cancel()
        
        try:
            if current_tasks:
                await asyncio.gather(*current_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    async def start(self, hold=False):
        self.running = True
        asyncio.create_task(self._monitor_logs())
        if hold:
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await self.stop()

    async def stop(self):
        self.running = False
        await asyncio.sleep(3)

#==========================================================================================
# TarkovBot ===============================================================================
#==========================================================================================
class TarkovBot(TwitchBot):
    def __init__(self, eft_config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eft = TarkovLogMonitor(**eft_config)
        self.eft.register_callback('game_prepared', self._eft_game_prepared)
        self.eft.register_callback('initialized', self._eft_initialized)

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
        await self.eft.start()

#====================================================================================
#====================================================================================
async def main():
    async def initialized_callback(data):
        logger.warning(f"Game initialized with version {data['version']}")
        
    async def game_prepared_callback(data):
        logger.warning(f"Game prepared: time={data['time_value']}, real={data['real_value']}, diff={data['diff_value']}")

    async def connect_callback(data):
        logger.warning(f"Connected to server {data['address']}:{data['port']}")

    async def disconnect_callback(data):
        logger.warning(f"Disconnected from server {data['address']}:{data['port']}")

    async def select_profile_callback(data):
        logger.warning(f"Logged in as: {data['account_id']} ({data['profile_id']})")

    monitor = TarkovLogMonitor(r"C:\Battlestate Games\Escape from Tarkov\Logs")
    monitor.register_callback('game_prepared', game_prepared_callback)
    monitor.register_callback('connect', connect_callback)
    monitor.register_callback('select_profile', select_profile_callback)
    monitor.register_callback('initialized', initialized_callback)
    monitor.register_callback('disconnect', disconnect_callback)
    await monitor.start(hold=True)
    
if __name__ == "__main__":
    from rich.logging import RichHandler
    logging.basicConfig(
        format='%(message)s',
        datefmt="%X",#"%I:%M:%S%p",
        level=logging.INFO,
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    asyncio.run(main())