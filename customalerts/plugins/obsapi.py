import simpleobsws
from poolguy.utils import ColorLogger, asyncio

logger = ColorLogger(__name__)

class OBSController:
    def __init__(self, host, port, password, ignore_media=[], media_scenes=[]):
        self.ws = simpleobsws.WebSocketClient(url=f'ws://{host}:{port}', password=password)
        self.ignore_media = ignore_media
        self.media_scenes = media_scenes
        self._connected = False
        self.wait_for_event = None
        self.wait_for = None
        
    async def _setup(self):
        """ Create connection and do setup """
        while not self._connected:
            try:
                await self.ws.connect()
                await self.ws.wait_until_identified()
                self._connected = True
                break
            except Exception as e:
                logger.error(f"Failed to connect to OBS: {e}")
                await asyncio.sleep(15)
        out = {}
        for scene in self.media_scenes:
            # Get list of items in scene using GetSceneItemList
            items = await self._get_scene_item_list(scene)
            out[scene] = [item['sourceName'] for item in items]
        self.media_scenes = out
        # Register callback for media end events
        self.ws.register_event_callback(self._handle_media_end, 'MediaInputPlaybackEnded')

    async def cleanup(self):
        """ Clean up resources and close connection """
        self._connected = False
        if hasattr(self, 'ws'):
            await self.ws.disconnect()

    async def _get_scene_item_list(self, scene_name):
        """ Get list of items in a scene """
        request = simpleobsws.Request('GetSceneItemList', {'sceneName': scene_name})
        response = await self.ws.call(request)
        if response.ok():
            return response.responseData.get('sceneItems', [])
        logger.error(f"Failed to get scene item list for scene {scene_name}")
        return []

    async def _get_scene_item_id(self, scene_name, source_name):
        """ Get the id of a source in a scene """
        request = simpleobsws.Request('GetSceneItemId', {
            'sceneName': scene_name,
            'sourceName': source_name
        })
        response = await self.ws.call(request)
        if response.ok():
            return response.responseData['sceneItemId']
        logger.error(f"Failed to get scene item ID for source {source_name} in scene {scene_name}")
        return None

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