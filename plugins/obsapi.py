import logging
import asyncio
import simpleobsws
from poolguy import TwitchBot, route
import subprocess

logger = logging.getLogger(__name__)

def get_media_duration(file_path):
    """
    Returns the duration (in seconds as a string) of the media file using ffprobe.
    If ffprobe fails, returns None.

    Args:
        file_path (str): Path to the media file.

    Returns:
        str or None: Duration in seconds, or None if ffprobe fails.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-i", file_path,
                "-show_entries", "format=duration",
                "-v", "quiet",
                '-of', 'csv=p=0'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        duration = result.stdout.strip()
        return duration if duration else None
    except Exception:
        return None

class OBSController:
    def __init__(self, host, port, password, ignore_media=None, media_scenes=None, status_config=None):
        self.host = host
        self.port = port
        self.password = password
        self.ignore_media = ignore_media or []
        self.media_scenes = media_scenes or []
        self._connected = False
        self.wait_for_event = None
        self.wait_for = None
        self.status_config = status_config
        
    async def _setup(self):
        """ Create connection and do setup """
        self.ws = simpleobsws.WebSocketClient(url=f'ws://{self.host}:{self.port}', password=self.password)
        while not self._connected:
            try:
                await self.ws.connect()
                self._connected = await self.ws.wait_until_identified()
            except Exception as e:
                logger.debug(f'{e}')
                logger.error(f"Failed to connect to OBS on {self.host}:{self.port}! Is OBS running?")
                await asyncio.sleep(15)
        logger.warning(f"Connected to obs!")
        await asyncio.sleep(2)
        self.media_scenes = {scene : [item['sourceName'] for item in await self._get_scene_item_list(scene)] for scene in self.media_scenes}
        self.ws.register_event_callback(self._handle_media_end, 'MediaInputPlaybackEnded')

    async def call(self, req, **kwargs):
        """ Make a call to OBS websocket API """
        response = await self.ws.call(simpleobsws.Request(req, kwargs))
        if response.ok():
            return response.responseData
        logger.error(f"{response.requestStatus.comment}")
        return False

    async def cleanup(self):
        self._connected = False
        await self.ws.disconnect()

    async def _get_scene_item_list(self, scene_name):
        """ Get list of items in a scene """
        response = await self.call('GetSceneItemList', **{'sceneName': scene_name})
        if response:
            return response.get('sceneItems', [])

    async def _get_stream_status(self):
        """ Get stream status """
        return await self.call('GetStreamStatus')

    async def _get_scene_item_id(self, scene_name, source_name):
        """ Get the id of a source in a scene """
        response = await self.call(
            'GetSceneItemId', **{
                'sceneName': scene_name,
                'sourceName': source_name
            })
        if response:
            return response['sceneItemId']

    async def start_recording(self):
        """ Starts the recorder """
        logger.warning(f"OBS starting recording!")
        return await self.call('StartRecord')

    async def stop_recording(self):
        """ Stops the recorder """
        response = await self.call('StopRecord')
        logger.warning(f"OBS stopped recording!")
        if response:
            return response["outputPath"]

    async def show_source(self, source_name, scene_name=None):
        """ Show a source in a scene """
        logger.info(f"Showing source {source_name} in scene {scene_name}")
        if not scene_name:
            # If no scene specified, try to find the source in known scenes
            for scene in self.media_scenes:
                if source_name in self.media_scenes[scene]:
                    scene_name = scene
                    break
        scene_item_id = await self._get_scene_item_id(scene_name, source_name)
        # Set the enabled state to true
        return await self.call('SetSceneItemEnabled', **{
            'sceneName': scene_name,
            'sceneItemId': scene_item_id,
            'sceneItemEnabled': True
        })

    async def hide_source(self, source_name, scene_name=None):
        """ Hide a source in a scene """
        logger.info(f"Hiding source {source_name} in scene {scene_name}")
        if not scene_name:
            # If no scene specified, try to find the source in known scenes
            for scene in self.media_scenes:
                if source_name in self.media_scenes[scene]:
                    scene_name = scene
                    break
        scene_item_id = await self._get_scene_item_id(scene_name, source_name)
        # Set the enabled state to false
        return await self.call('SetSceneItemEnabled', **{
            'sceneName': scene_name,
            'sceneItemId': scene_item_id,
            'sceneItemEnabled': False
        })

    async def hide_all_sources(self, scene_name):
        """ Hide all sources in a scene"""
        if scene_name in self.media_scenes:
            for item in self.media_scenes:
                await self.hide_source(item, scene_name)
        else:
            items = await self._get_scene_item_list(scene_name)
            for item in items:
                await self.hide_source(item['sourceName'], scene_name)

    async def get_input_settings(self, input_name):
        return await self.call('GetInputSettings', **{"inputName": input_name})

    async def set_source_text(self, source_name, text_content):
        """ Edit the text content of a text source """
        await self.set_source_settings(source_name, {'text': text_content})

    async def set_source_media(self, source_name, media_path):
        """ Set the media source to a specific path """
        await self.set_source_settings(source_name, {'local_file': media_path})

    async def set_source_settings(self, source_name, settings):
        await self.call('SetInputSettings', **{
            'inputName': source_name,
            'inputSettings': settings
        })

    async def _handle_media_end(self, data):
        """ Logic to execute whenever some media ends """
        input_name = data.get('inputName')
        # ignore if in ignore list
        if not input_name or input_name in self.ignore_media:
            return
        logger.info(f"Media ended -> {input_name}")
        # find and hide the source
        for scene in self.media_scenes:
            if input_name in self.media_scenes[scene]:
                await self.hide_source(input_name, scene)
                break

    async def show_and_wait(self, source_name, scene_name):
        source = await self.get_input_settings(source_name)
        dur = float(get_media_duration(source['inputSettings']['local_file']))
        await self.show_source(source_name, scene_name)
        await asyncio.sleep(dur + 0.2)
        await self.hide_source(source_name, scene_name)
    
    async def clear_wait(self):
        pass
#==========================================================================================
# OBSBot =================================================================================
#==========================================================================================
class OBSBot(TwitchBot):
    def __init__(self, obs_cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obsws = OBSController(**obs_cfg)

    async def after_login(self):
        await self.obsws._setup()

    @route("/obs/clearwait", method="GET")
    async def obs_clear_wait(self, request):
        asyncio.create_task(self.obsws.clear_wait())
        return self.app.response_json({"status": True})
