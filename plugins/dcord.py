import logging
import re
import asyncio
from poolguy import TwitchBot, Alert, route
from discord.ext import commands
from discord import AllowedMentions, Embed, Color, Intents

logger = logging.getLogger(__name__)

intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    allowed_mentions=AllowedMentions(everyone=True, roles=True)
)

YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=[\w-]{11}|[\w-]{11})"
)

@bot.event
async def on_ready():
    logger.info(f'Discord bot "{bot.user}" is ready!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


class DiscordBot(TwitchBot):
    def __init__(self, discord_cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discord_bot = bot
        self.discord_task = None
        self.discord_cfg = discord_cfg

    def start_discord_bot(self):
        self.discord_task = asyncio.create_task(self.discord_bot.start(self.discord_cfg["token"]))

    async def send_live_notification(self):
        r = await self.http.getUsers()
        user = r[0]
        r2 = await self.http.getChannelInfo()
        chan = r2[0]
        
        channel = self.discord_bot.get_channel(self.discord_cfg['live_noto_channel'])
        embed = Embed(
            title=chan["title"],
            description=f"Now streaming {chan['game_name']}!",
            color=Color.blue(),
            url=f"https://twitch.tv/{user['login']}"
        )
        embed.set_thumbnail(url=f"https://static-cdn.jtvnw.net/ttv-boxart/{chan['game_id']}-150x200.jpg")
        embed.set_image(url=user['profile_image_url'])
        # Mention everyone in a non-embed message since @everyone doesn't ping from embed descriptions
        await channel.send(
            f"@everyone {user['display_name']} just went live! https://twitch.tv/{user['login']}", 
            embed=embed
        )

    @route('/discordnoto')
    async def dicord_noto(self, request):
        await self.send_live_notification()
        return self.app.response_json({"status": True})

#####################=========---------
### stream.online ###=============---------
#####################=================---------
class StreamOnline(Alert):
    queue_skip = True

    async def store(self):
        await self.bot.storage.insert(
            "stream_online", 
            {
                "timestamp": self.timestamp,
                "message_id": self.message_id,
                "type": self.data["type"],
                "id": self.data["id"]
            }
        )

    async def process(self):
        if hasattr(self.bot, 'discord_bot'):
            if self.bot.discord_bot.is_ready():
                await self.bot.send_live_notification()
            else:
                logger.warning("Discord bot is not running.")
        else:
            logger.warning("Discord bot is not attached.")