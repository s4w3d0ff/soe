import logging
from aiohttp import web
from poolguy import TwitchBot, route

logger = logging.getLogger(__name__)

#==========================================================================================
# BannedBot ===============================================================================
#==========================================================================================
class BannedBot(TwitchBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.banHTML = ""
        self.alertDone = True

    @route("/alertended")
    def alertended(self, request):
        self.alertDone = True
        return web.json_response({"status": True})

    @route('/banned')
    async def banned(self, request):
        return web.Response(text=self.banHTML, content_type='text/html', charset='utf-8')

