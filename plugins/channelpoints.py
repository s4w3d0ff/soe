import json
import random
import asyncio
import logging
from poolguy.storage import loadJSON
from poolguy import Alert
from .spotifyapi import duck_volume

logger = logging.getLogger(__name__)

###########################################################=========---------
### channel.channel_points_custom_reward_redemption.add ###=============---------
###########################################################=================---------
points_cfg = loadJSON("db/chan_points_cfg.json")

class VideoRedeem(Alert):
    queue_skip = False
    priority = 3
    store = False

    @duck_volume(volume=40)
    async def process(self):
        rewardConf = points_cfg[self.data["reward"]["id"]]
        await self.bot.obsws.show_and_wait(rewardConf['source'], rewardConf['scene'])

class ClownCoreRedeem(Alert):
    queue_skip = False
    priority = 3
    store = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vidscene = "[S] Videos"
        self.clown_sources = [
            "clown-foldpizza",
            "clown-pain",
            "clown-3g",
            "clown-tech",
            "clown-drivethru",
            "clown-sub",
            "clown-hell"
        ]
    
    @duck_volume(volume=40)
    async def process(self):
        await self.bot.obsws.show_and_wait(random.choice(self.clown_sources), self.vidscene)

class ChannelChannelPointsCustomRewardRedemptionAdd(Alert):
    queue_skip = True

    async def timeout(self, size=60):
        viewer2ban = self.data["user_input"].replace("@", "").replace(" ", "")
        logger.warning(f"Banning {viewer2ban}")
        r = await self.bot.http.getUsers(logins=viewer2ban)
        try:
            banId = r[0]['id']
            await self.bot.http.banUser(
                user_id=banId, 
                duration=size, 
                reason=f"{self.data['user_login']} used channel points to timeout {viewer2ban} for {size} secs"
            )
        except Exception as e:
            logger.error("[Bot] "+ e)

    async def process(self):
        rewardId = self.data["reward"]["id"]
        if rewardId not in points_cfg:
            logger.error(f"ChannelPointRedeem: {rewardId} \n{json.dumps(self.data, indent=2)}")
            return
        rewardConf = points_cfg[rewardId]
        if 'name' not in rewardConf:
            alert = VideoRedeem(self.bot, self.message_id, self.channel, self.data, self.timestamp)
            await self.bot.ws.notification_handler._queue.put(alert)
            return
        match rewardConf['name']:
            # Ban_______________
            case "bansmall":
                await self.timeout(60)
            case "banbig":
                await self.timeout(3600)
            # Cabbage____________
            case "cabbage":
                emotes = rewardConf['emotes']
                for i in range(3):
                    await asyncio.sleep(0.3)
                    await self.bot.http.sendChatMessage(f'{random.choice(emotes)} {random.choice(emotes)} {random.choice(emotes)}')
            # Avatars____________
            case "monke" | "scav" | "kek":
                await self.bot.obsws.hide_all_sources(rewardConf['scene'])
                await self.bot.obsws.show_source(rewardConf['source'], rewardConf['scene'])
             # Clowncore____________
            case "clowncore":
                alert = ClownCoreRedeem(self.bot, self.message_id, self.channel, self.data, self.timestamp)
                await self.bot.ws.notification_handler._queue.put(alert)
             # TWSS____________
            case "TWSS":
                await self.bot.obsws.show_source(f'TWSS{random.randint(1, 21)}', '[S] TWSS')
            case "flashbang":
                await self.bot.obsws.show_source(rewardConf['source'], rewardConf['scene'])
                await asyncio.sleep(rewardConf['delay'])
                await self.bot.obsws.hide_source(rewardConf['source'], rewardConf['scene'])
            case _:
                pass