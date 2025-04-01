import logging
from poolguy import TwitchBot

logger = logging.getLogger(__name__)

# Going to shift to ollama since i use it already for other stuff

#==========================================================================================
# AIBot ===================================================================================
#==========================================================================================
class AIBot(TwitchBot):
    def __init__(self, ai_cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = None #AI(**ai_cfg)