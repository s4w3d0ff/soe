import json
import asyncio
import logging
from poolguy import Alert, TwitchBot, route, websocket

logger = logging.getLogger(__name__)

predict_source = ["Prediction [SOE]", "[S] Prediction"]

#==========================================================================================
# PredictionBot ===========================================================================
#==========================================================================================
class PredictionBot(TwitchBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_prediction = None

    @websocket('/predictionws')
    async def prediction_ws(self, ws, request):
        async def loop(ws, request):
            if self.current_prediction:
                await ws.send_json(self.current_prediction)
            else:
                await ws.ping()
            await asyncio.sleep(0.5)
        await self.ws_hold_connection(ws, request, loop_func=loop, wait_for_twitch=True)

    @route('/prediction')
    async def prediction_route(self, request):
        return await self.app.response_html('templates/prediction.html')


################################=========---------
### channel.prediction.begin ###=============---------
################################=================---------
class ChannelPredictionBegin(Alert):
    """
    {
        "id": "1243456",
        "broadcaster_user_id": "1337",
        "broadcaster_user_login": "cool_user",
        "broadcaster_user_name": "Cool_User",
        "title": "Aren’t shoes just really hard socks?",
        "outcomes": [
            {"id": "1243456", "title": "Yeah!", "color": "blue"},
            {"id": "2243456", "title": "No!", "color": "pink"},
        ],
        "started_at": "2020-07-15T17:16:03.17106713Z",
        "locks_at": "2020-07-15T17:21:03.17106713Z"
    }
    """
    queue_skip = True

    async def process(self):
        logger.warning(f'{json.dumps(self.data, indent=4)}')
        if hasattr(self.bot, 'current_prediction'):
            self.bot.current_prediction = self.data.copy()
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.show_source(*predict_source)



###################################=========---------
### channel.prediction.progress ###=============---------
###################################=================---------
class ChannelPredictionProgress(Alert):
    """
    {
        "id": "1243456",
        "broadcaster_user_id": "1337",
        "broadcaster_user_login": "cool_user",
        "broadcaster_user_name": "Cool_User",
        "title": "Aren’t shoes just really hard socks?",
        "outcomes": [
            {
                "id": "1243456",
                "title": "Yeah!",
                "color": "blue",
                "users": 10,
                "channel_points": 15000,
                "top_predictors": [ // contains up to 10 users
                    {
                        "user_name": "Cool_User",
                        "user_login": "cool_user",
                        "user_id": "1234",
                        "channel_points_won": null,
                        "channel_points_used": 500
                    },
                    {
                        "user_name": "Coolest_User",
                        "user_login": "coolest_user",
                        "user_id": "1236",
                        "channel_points_won": null,
                        "channel_points_used": 200
                    }
                ]
            },
            {
                "id": "2243456",
                "title": "No!",
                "color": "pink",
                "top_predictors": [ // contains up to 10 users
                    {
                        "user_name": "Cooler_User",
                        "user_login": "cooler_user",
                        "user_id": 12345,
                        "channel_points_won": null,
                        "channel_points_used": 5000
                    }
                ]
            },
        ],
        "started_at": "2020-07-15T17:16:03.17106713Z",
        "locks_at": "2020-07-15T17:21:03.17106713Z"
    }
    """
    queue_skip = True

    async def process(self):
        logger.warning(f'{json.dumps(self.data, indent=4)}')
        if hasattr(self.bot, 'current_prediction'):
            self.bot.current_prediction = self.data.copy()
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.show_source(*predict_source)


###################################=========---------
### channel.prediction.lock ###=============---------
###################################=================---------
class ChannelPredictionLock(Alert):
    """
    {
        "id": "1243456",
        "broadcaster_user_id": "1337",
        "broadcaster_user_login": "cool_user",
        "broadcaster_user_name": "Cool_User",
        "title": "Aren’t shoes just really hard socks?",
        "outcomes": [
            {
                "id": "1243456",
                "title": "Yeah!",
                "color": "blue",
                "users": 10,
                "channel_points": 15000,
                "top_predictors": [ // contains up to 10 users
                    {
                        "user_name": "Cool_User",
                        "user_login": "cool_user",
                        "user_id": "1234",
                        "channel_points_won": null,
                        "channel_points_used": 500
                    },
                    {
                        "user_name": "Coolest_User",
                        "user_login": "coolest_user",
                        "user_id": "1236",
                        "channel_points_won": null,
                        "channel_points_used": 200
                    }
                ]
            },
            {
                "id": "2243456",
                "title": "No!",
                "color": "pink",
                "top_predictors": [ // contains up to 10 users
                    {
                        "user_name": "Cooler_User",
                        "user_login": "cooler_user",
                        "user_id": 12345,
                        "channel_points_won": null,
                        "channel_points_used": 5000
                    }
                ]
            },
        ],
        "started_at": "2020-07-15T17:16:03.17106713Z",
        "locked_at": "2020-07-15T17:21:03.17106713Z"
    }
    """
    queue_skip = True

    async def process(self):
        logger.warning(f'{json.dumps(self.data, indent=4)}')
        if hasattr(self.bot, 'current_prediction'):
            self.bot.current_prediction = self.data.copy()
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.show_source(*predict_source)


###################################=========---------
### channel.prediction.end ###=============---------
###################################=================---------
class ChannelPredictionEnd(Alert):
    """
    {
        "id": "1243456",
        "broadcaster_user_id": "1337",
        "broadcaster_user_login": "cool_user",
        "broadcaster_user_name": "Cool_User",
        "title": "Aren’t shoes just really hard socks?",
        "winning_outcome_id": "12345",
        "outcomes": [
            {
                "id": "12345",
                "title": "Yeah!",
                "color": "blue", // can be blue or pink
                "users": 2,
                "channel_points": 15000,
                "top_predictors": [ // contains up to 10 users
                    {
                        "user_name": "Cool_User",
                        "user_login": "cool_user",
                        "user_id": "1234",
                        "channel_points_won": 10000,
                        "channel_points_used": 500
                    },
                    {
                        "user_name": "Coolest_User",
                        "user_login": "coolest_user",
                        "user_id": "1236",
                        "channel_points_won": 5000,
                        "channel_points_used": 100
                    },
                ]
            },
            {
                "id": "22435",
                "title": "No!",
                "users": 2,
                "channel_points": 200,
                "color": "pink",
                "top_predictors": [
                    {
                        "user_name": "Cooler_User",
                        "user_login": "cooler_user",
                        "user_id": 12345,
                        "channel_points_won": null, // null if result is refund or loss
                        "channel_points_used": 100
                    },
                    {
                        "user_name": "Elite_User",
                        "user_login": "elite_user",
                        "user_id": 1337,
                        "channel_points_won": null, // null if result is refund or loss
                        "channel_points_used": 100
                    }
                ]
            }
        ],
        "status": "resolved", // valid values: resolved, canceled
        "started_at": "2020-07-15T17:16:03.17106713Z",
        "ended_at": "2020-07-15T17:16:11.17106713Z"
    }
    """
    queue_skip = True
    
    async def store(self):
        await self.bot.storage.insert(
            "channel_prediction_end", 
            {
                "timestamp": self.timestamp,
                "message_id": self.message_id,
                "title": self.data["title"],
                "outcomes": json.dumps(self.data["outcomes"]),
                "winning_outcome_id": self.data["winning_outcome_id"],
                "status": self.data["status"]
            }
        )

    async def process(self):
        logger.warning(f'{json.dumps(self.data, indent=4)}')
        if hasattr(self.bot, 'current_prediction'):
            self.bot.current_prediction = self.data.copy()
        await asyncio.sleep(30)
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.hide_source(*predict_source)


