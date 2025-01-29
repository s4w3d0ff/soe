from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from poolguy.utils import logging, os, ColorLogger, asyncio, ThreadWithReturn, ctxt

logger = ColorLogger(__name__)

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

##### MODELS ################--------------------------
class Llama323BF16:
    model_id = "unsloth/Llama-3.2-3B-Instruct-GGUF"
    filename = "Llama-3.2-3B-Instruct-F16.gguf"
    generation_args = {
        "max_new_tokens": 420,
        "return_full_text": False,
        "do_sample": True,
        "temperature": 0.5,          # lower = more focused
        "num_return_sequences": 3    # Number of alternative generations it can choose from
    }

class Llama323BF16_UNCENSORED:
    model_id = "bartowski/Llama-3.2-3B-Instruct-uncensored-GGUF"
    filename = "Llama-3.2-3B-Instruct-uncensored-f16.gguf"
    generation_args = {
        "max_new_tokens": 420,
        "return_full_text": False,
        "do_sample": True,
        "temperature": 0.5,          # lower = more focused
        "num_return_sequences": 3    # Number of alternative generations it can choose from
    }
    
class Qwen25Coder32BQ8:
    model_id = "unsloth/Qwen2.5-Coder-32B-Instruct-128K-GGUF"
    filename = "Qwen2.5-Coder-32B-Instruct-Q8_0.gguf"
    generation_args = {
        "max_new_tokens": 420,
        "return_full_text": False,
        "do_sample": True,
        "temperature": 0.5,          # lower = more focused
        "num_return_sequences": 1    # Number of alternative generations it can choose from
    }

class DeepSeekQwen14BQ3:
    model_id = "unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF"
    filename = "DeepSeek-R1-Distill-Qwen-14B-Q3_K_M.gguf"
    generation_args = {
        "max_new_tokens": 420,
        "return_full_text": False,
        "do_sample": True,
        "temperature": 0.5,          # lower = more focused
        "num_return_sequences": 1    # Number of alternative generations it can choose from
    }

class DeepSeekLlama8BF16:
    model_id = "unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF"
    filename = "DeepSeek-R1-Distill-Llama-8B-F16.gguf"
    generation_args = {
        "max_new_tokens": 420,
        "return_full_text": False,
        "do_sample": True,
        "temperature": 0.5,          # lower = more focused
        "num_return_sequences": 3    # Number of alternative generations it can choose from
    }
   
class Phi4Q8:
    model_id = "unsloth/phi-4-GGUF"
    filename = "phi-4-Q8_0.gguf"
    generation_args = {
        "max_new_tokens": 420,
        "return_full_text": False,
        "do_sample": True,
        "temperature": 0.5,          # lower = more focused
        "num_return_sequences": 1    # Number of alternative generations it can choose from
    }
    
    
##### PERSONAS ################--------------------------
class TwitchBot:
    name = "s4w3d0ff_bot"
    description = """a Twitch chat bot that is programmed to deliver sassy and witty banter, responding with factual information while maintaining a humorous and cheeky tone throughout the interactions. \nIMPORTANT: Twitch chat has a character limit of 400, so KEEP YOUR RESPONSES SHORT AND TO THE POINT. You don't need to remind anyone that you are an AI, if you are limited by something, just say so and move on. You must NEVER use slurs or curse words."""
    init_history = [
    {
        "role": "assistant", 
        "content": "Got it! Ready to serve and sass like the queen of Twitch chats I was born to be. Hit me with your questions or challenges, and let’s get this show rolling!"
    }]

class GenZbot:
    name = "litAF_bot"
    description = """a Twitch chatbot that serves facts with a side of Gen Z energy: vibin', slangin', and keepin' it skibidi. Responses are short, snappy, and full of trendy lingo. Always stays within a 400-character yap limit, like a true max rizz sigma. No slurs, no cursing—just straight-up lit banter.\nIMPORTANT: Twitch chat has a character limit of 400, so KEEP YOUR RESPONSES SHORT AND TO THE POINT. You don't need to remind anyone that you are an AI, if you are limited by something, just say so and move on. You must NEVER use slurs or curse words."""
    init_history = [
    {
        "role": "assistant", 
        "content": "Sheeesh! No cap, I'm online and ready to flex my big brain. ON GOD. Drop your Qs, and let's pop off!"
    }]


class AI():
    def __init__(self, model=None, persona=None, device='cuda', offline_mode=False):
        self.persona = globals()[persona] if isinstance(persona, str) else persona
        self.model_cfg = globals()[model] if isinstance(model, str) else model
        self.system_p = f"You are '{self.persona.name}', {self.persona.description}"
        self.device = device
        self.tokenizer = None
        self.model = None
        self.brain = None
        self.offline_mode = offline_mode
        # Set offline mode environment variables if specified
        if offline_mode:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
        self._setup = self.setup()

    def setup(self):
        def _setup():
            logger.warning(f"Setting up AI: {self.persona.name}")
            try:
                # First try to load from local cache only
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_cfg.model_id,
                    local_files_only=True,
                    gguf_file=self.model_cfg.filename
                )
                logger.info(f"Loaded {self.model_cfg.model_id} Tokenizer from cache")
            except Exception as e:
                if self.offline_mode:
                    raise RuntimeError(f"Cannot load {self.model_cfg.model_id} tokenizer in offline mode: {e}")
                logger.warning(f"Cache miss for {self.model_cfg.model_id} tokenizer, downloading from hub...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_cfg.model_id,
                    gguf_file=self.model_cfg.filename
                )
            try:
                # First try to load model from local cache
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_cfg.model_id,
                    device_map=self.device,
                    torch_dtype="auto",
                    local_files_only=True,
                    gguf_file=self.model_cfg.filename
                )
                logger.info(f"Loaded {self.model_cfg.model_id} Model from cache")
            except Exception as e:
                if self.offline_mode:
                    raise RuntimeError(f"Cannot load model in offline mode: {e}")
                logger.warning("Cache miss for model, downloading from hub...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_cfg.model_id,
                    device_map=self.device,
                    torch_dtype="auto",
                    gguf_file=self.model_cfg.filename
                )

            self.brain = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer
            )
            logger.info(f"{self.model_cfg.model_id} Pipeline Complete")
            
        t = ThreadWithReturn(target=_setup, daemon=True)
        t.start()
        return t

    async def wait_for_setup(self):
        while self._setup.is_alive():
            await asyncio.sleep(15)
            logger.debug(f"{self.model_cfg.model_id} Loading...")
        self._setup.join()
        logger.info(f"LMM {self.model_cfg.model_id} finished loading")

    def ask(self, query, history=[]):
        messages = [{"role": "system", "content": self.system_p}]
        messages += self.persona.init_history
        messages += history
        messages += [{"role": "user", "content": query}]
        output = self.brain(messages, **self.model_cfg.generation_args)
        r = output[0]['generated_text']
        return r

    def threaded_ask(self, query, history=[]):
        ai_thread = ThreadWithReturn(target=self.ask, args=(query, history), daemon=True)
        ai_thread.start()
        return ai_thread


if __name__ == '__main__':
    import logging
    fmat = ctxt('%(asctime)s', 'yellow', style='d') + '-%(levelname)s-' + ctxt('[%(name)s]', 'purple', style='d') + ctxt(' %(message)s', 'green', style='d')
    logging.basicConfig(format=fmat, datefmt="%I:%M:%S%p", level=logging.INFO)
    cfg = {
		"persona": "GenZbot",
		"model": "DeepSeekLlama8BF16", 
		"device": "cuda"
	}
    ai = AI(**cfg)
    asyncio.run(ai.wait_for_setup())
    history = []
    while True:
        inp = input("Prompt: ")
        r = ai.ask(inp, history[-14:])
        logger.warning(f"Answer: {r}")
        history += [{"role": "user", "content": inp}, {"role": "assistant", "content": r}]