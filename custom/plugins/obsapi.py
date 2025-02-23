import simpleobsws
from poolguy.utils import ColorLogger, asyncio

logger = ColorLogger(__name__)

class OBSController:
    def __init__(self, host, port, password, ignore_media=None, media_scenes=None, status_config=None):
        self.ws = simpleobsws.WebSocketClient(url=f'ws://{host}:{port}', password=password)
        self.ignore_media = ignore_media or []
        self.media_scenes = media_scenes or []
        self._connected = False
        self.wait_for_event = None
        self.wait_for = None
        self.status_config = status_config
        
    async def _setup(self):
        """ Create connection and do setup """
        while not self._connected:
            try:
                await self.ws.connect()
                await self.ws.wait_until_identified()
                self._connected = True
            except Exception as e:
                logger.error(f"Failed to connect to OBS: {e}")
                await asyncio.sleep(15)
        out = {}
        for scene in self.media_scenes:
            items = await self._get_scene_item_list(scene)
            out[scene] = [item['sourceName'] for item in items]
        self.media_scenes = out
        # Register callbacks
        self.ws.register_event_callback(self._handle_media_end, 'MediaInputPlaybackEnded')

    async def call(self, req, **kwargs):
        response = await self.ws.call(simpleobsws.Request(req, kwargs))
        if response.ok():
            return response.responseData
        logger.error(f"{response.requestStatus.comment}")
        return None

    async def cleanup(self):
        self._connected = False
        await self.ws.disconnect()

    async def _get_scene_item_list(self, scene_name):
        """ Get list of items in a scene """
        response = await self.call('GetSceneItemList', **{'sceneName': scene_name})
        return response.get('sceneItems', [])

    async def _get_stream_status(self):
        """ Get list of items in a scene """
        return await self.call('GetStreamStatus')

    async def _get_scene_item_id(self, scene_name, source_name):
        """ Get the id of a source in a scene """
        response = await self.call(
            'GetSceneItemId', **{
                'sceneName': scene_name,
                'sourceName': source_name
            })
        return response['sceneItemId']

    async def hide_all_sources(self, scene_name):
        """ Hide all sources in a scene"""
        if scene_name in self.media_scenes:
            for item in self.media_scenes:
                await self.hide_source(item, scene_name)
        else:
            items = await self._get_scene_item_list(scene_name)
            for item in items:
                await self.hide_source(item['sourceName'], scene_name)

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
        if scene_item_id is None:
            return
        # Set the enabled state to true
        request = simpleobsws.Request('SetSceneItemEnabled', {
            'sceneName': scene_name,
            'sceneItemId': scene_item_id,
            'sceneItemEnabled': True
        })
        response = await self.ws.call(request)
        if not response.ok():
            logger.error(f"Failed to show source {source_name} in scene {scene_name}")


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
        if scene_item_id is None:
            return
        # Set the enabled state to false
        request = simpleobsws.Request('SetSceneItemEnabled', {
            'sceneName': scene_name,
            'sceneItemId': scene_item_id,
            'sceneItemEnabled': False
        })
        response = await self.ws.call(request)
        if not response.ok():
            logger.error(f"Failed to hide source {source_name} in scene {scene_name}")

    async def set_source_text(self, source_name, text_content):
        """ Edit the text content of a text source """
        logger.info(f"Setting text content for source {source_name}")
        request = simpleobsws.Request('SetInputSettings', {
            'inputName': source_name,
            'inputSettings': {'text': text_content}
        })
        response = await self.ws.call(request)
        if not response.ok():
            logger.error(f"Failed to set text content for source {source_name}")

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
        if self.wait_for and self.wait_for == input_name:
            self.wait_for_event.set()

    async def show_and_wait(self, source_name, scene_name, wait_for=None):
        """ Show a source, then hold and wait for 'wait_for' media to end """
        self.wait_for = wait_for or source_name
        self.wait_for_event = asyncio.Event()
        await self.show_source(source_name, scene_name)
        logger.warning(f"Waiting on: {self.wait_for}")
        await self.wait_for_event.wait()
        self.wait_for = None
        await asyncio.sleep(0.5)
    
    async def clear_wait(self):
        self.wait_for_event.set()
        if self.wait_for:
            for scene in self.media_scenes:
                if self.wait_for in self.media_scenes[scene]:
                    await self.hide_source(self.wait_for, scene)
                    break
            self.wait_for = None
        self.wait_for_event = asyncio.Event()


"""
{
    'outputs': [
        {
            'outputActive': True, 
            'outputFlags': {
                'OBS_OUTPUT_AUDIO': True, 
                'OBS_OUTPUT_ENCODED': True, 
                'OBS_OUTPUT_MULTI_TRACK': True, 
                'OBS_OUTPUT_SERVICE': True, 
                'OBS_OUTPUT_VIDEO': True
            }, 
            'outputHeight': 1080, 
            'outputKind': 'rtmp_output', 
            'outputName': 'adv_stream', 
            'outputWidth': 1920
        }, 
        {
            'outputActive': False, 
            'outputFlags': {
                'OBS_OUTPUT_AUDIO': True, 
                'OBS_OUTPUT_ENCODED': True, 
                'OBS_OUTPUT_MULTI_TRACK': True, 
                'OBS_OUTPUT_SERVICE': False, 
                'OBS_OUTPUT_VIDEO': True
            }, 
            'outputHeight': 1080, 
            'outputKind': 'ffmpeg_muxer', 
            'outputName': 'adv_file_output', 
            'outputWidth': 1920
        }, 
        {
            'outputActive': False, 
            'outputFlags': {
                'OBS_OUTPUT_AUDIO': False, 
                'OBS_OUTPUT_ENCODED': False, 
                'OBS_OUTPUT_MULTI_TRACK': False, 
                'OBS_OUTPUT_SERVICE': False, 
                'OBS_OUTPUT_VIDEO': True
             }, 
            'outputHeight': 1080, 
            'outputKind': 'virtualcam_output', 
            'outputName': 'virtualcam_output', 
            'outputWidth': 1920
        }
    ]
}
"""