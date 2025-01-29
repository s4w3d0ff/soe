from poolguy.utils import ColorLogger, json, random
from poolguy.twitchws import Alert
from .plugins.tts import generate_speech, VOICES

logger = ColorLogger(__name__)

scene = "[S] Bit Alerts"
altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
textscene = "CheerText"

class ChannelSubscribeAlert(Alert):
    """channel.subscribe"""
    async def process(self):
        logger.error(f"{self.alert_type}:\n{json.dumps(self.data, indent=2)}")
        """
        {
            "user_id": "1234",
            "user_login": "cool_user",
            "user_name": "Cool_User",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "tier": "1000",
            "is_gift": false
        }
        """
        name = self.data['user_name']
        tier = int(self.data['tier'][0])
        if self.data['is_gift']:
            return
        await self.bot.obsws.set_source_text(textscene, f" {name} subscribed! \n-tier {tier}-")
        for a in altscenes:
            await self.bot.obsws.show_source(a, scene)
        await self.bot.obsws.show_and_wait('yaaay', scene)
        await self.bot.obsws.set_source_text(textscene, "")
        for a in altscenes:
            await self.bot.obsws.hide_source(a, scene)


class ChannelSubscriptionGiftAlert(Alert):
    """channel.subscription.gift"""
    async def process(self):
        logger.error(f"{self.alert_type}:\n{json.dumps(self.data, indent=2)}")
        """
        {
            "user_id": "1234",
            "user_login": "cool_user",
            "user_name": "Cool_User",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "total": 2,
            "tier": "1000",
            "cumulative_total": 284, //null if anonymous or not shared by the user
            "is_anonymous": false
        }
        """
        name = "Anonymous" if self.data['is_anonymous'] else self.data['user_name']
        total = self.data['total']
        tier = self.data['tier'][0]
        await self.bot.obsws.set_source_text(textscene, f" {name} gifted {total} subs! \n-tier {tier}-")
        for a in altscenes:
            await self.bot.obsws.show_source(a, scene)
        await self.bot.obsws.show_and_wait('reallynice', scene)
        await self.bot.obsws.set_source_text(textscene, "")
        for a in altscenes:
            await self.bot.obsws.hide_source(a, scene)
        

class ChannelSubscriptionMessageAlert(Alert):
    """channel.subscription.message"""
    async def process(self):
        logger.error(f"{self.alert_type}:\n{json.dumps(self.data, indent=2)}")
        """
        {
        "user_id": "1234",
        "user_login": "cool_user",
        "user_name": "Cool_User",
        "broadcaster_user_id": "1337",
        "broadcaster_user_login": "cooler_user",
        "broadcaster_user_name": "Cooler_User",
        "tier": "1000",
        "message": {
            "text": "Love the stream! FevziGG",
            "emotes": [
                {
                    "begin": 23,
                    "end": 30,
                    "id": "302976485"
                }
            ]
        },
        "cumulative_months": 15,
        "streak_months": 1, // null if not shared
        "duration_months": 6
        }
        """
        name = self.data['user_name']
        tier = int(self.data['tier'][0])
        total_months = self.data['cumulative_months']
        tts_fp = None
        if self.data["message"]:
            voice = random.choice(list(VOICES.keys()))
            tts_fp = await generate_speech(self.data['message']['text'], "db/sub_tts.mp3", voice)
        await self.bot.obsws.set_source_text(textscene, f" {name} has been subscribed for {int(total_months)} months!")
        for a in altscenes:
            await self.bot.obsws.show_source(a, scene)
        await self.bot.obsws.show_and_wait('goingupthere', scene)
        await self.bot.obsws.set_source_text(textscene, "")
        for a in altscenes:
            await self.bot.obsws.hide_source(a, scene)
        if tts_fp:
            await self.bot.obsws.show_and_wait('sub_tts', scene)