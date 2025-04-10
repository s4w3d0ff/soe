import logging
import random
import string
from datetime import datetime, timedelta, timezone
from poolguy import TwitchBot, route

logger = logging.getLogger(__name__)

def randString(length=12):
    chars = string.ascii_letters + string.digits
    ranstr = ''.join(random.choice(chars) for _ in range(length))
    return ranstr

test_payloads = {
    "channel.follow": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.follow"
        },
        "event": {
            "user_id": "1234",
            "user_login": "deez_nutz_test",
            "user_name": "Deez_Nutz_Test",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "followed_at": datetime.now(timezone.utc).isoformat()
        }
    },
    "channel.cheer": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.cheer",
        },
        "event": {
            "is_anonymous": False,
            "user_id": "1234",
            "user_login": "cool_user",
            "user_name": "Cool_User",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "message": "pogchamp woot woot awooga",
            "bits": 1000
        }
    },
    "channel.bits.use": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.bits.use",
        },
        "event": {
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "user_id": "1234",
            "user_login": "cool_user",
            "user_name": "Cool_User",
            "bits": 275,
            "type": "cheer",
            "power_up": None,
            "message": {
                "text": "Cheer275",
                "fragments": [
                    {
                        "type": "cheermote",
                        "text": "Cheer275",
                        "cheermote": {
                            "prefix": "cheer",
                            "bits": 275,
                            "tier": 100
                        },
                        "emote": None
                    }
                ]
            }
        }
    },
    "channel.subscribe": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.subscribe"
        },
        "event": {
            "user_id": "1234",
            "user_login": "cool_user",
            "user_name": "Cool_User",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "tier": "1000",
            "is_gift": False
        }
    },
    "channel.subscription.gift": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.subscription.gift"
        },
        "event": {
            "user_id": "1234",
            "user_login": "cool_user",
            "user_name": "Cool_User",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "total": 1000,
            "tier": "1000",
            "cumulative_total": None,
            "is_anonymous": False
        }
    },
    "channel.subscription.message": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.subscription.message"
        },
        "event": {
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
            "cumulative_months": 5,
            "streak_months": 3, # null if not shared
            "duration_months": 6
        }
    },
    "channel.goal.progress": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.goal.progress"
        },
        "event": {
            "id": "1234",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "type": "follower",
            "description": "Follow Goal",
            "current_amount": 7,
            "target_amount": 10,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": None
        }
    },
    "channel.hype_train.progress": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.hype_train.progress"
        },
        "event": {
            "id": "1234",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "level": 2,
            "total": 137,
            "progress": 37,
            "goal": 100,
            "top_contributions": [
                {
                    "user_id": "123",
                    "user_login": "cool_user",
                    "user_name": "Cool_User",
                    "type": "bits",
                    "total": 50
                },
                {
                    "user_id": "456",
                    "user_login": "cooler_user2",
                    "user_name": "Cooler_User2",
                    "type": "subscription",
                    "total": 30
                }
            ],
            "last_contribution": {
                "user_id": "123",
                "user_login": "cool_user",
                "user_name": "Cool_User",
                "type": "bits",
                "total": 50
            },
            "started_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        }
    },
    "channel.hype_train.end": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.hype_train.end"
        },
        "event": {
            "id": "1234",
            "broadcaster_user_id": "1337",
            "broadcaster_user_login": "cooler_user",
            "broadcaster_user_name": "Cooler_User",
            "level": 3,
            "total": 437,
            "top_contributions": [
                {
                    "user_id": "123",
                    "user_login": "cool_user",
                    "user_name": "Cool_User",
                    "type": "bits",
                    "total": 200
                },
                {
                    "user_id": "456",
                    "user_login": "cooler_user2",
                    "user_name": "Cooler_User2",
                    "type": "subscription",
                    "total": 100
                }
            ],
            "started_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "cooldown_ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
    },
    "channel.chat.notification": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.chat.notification"
        },
        "event": {
            "broadcaster_user_id": "1971641",
            "broadcaster_user_login": "streamer",
            "broadcaster_user_name": "streamer",
            "chatter_user_id": "49912639",
            "chatter_user_login": "viewer23",
            "chatter_user_name": "viewer23",
            "chatter_is_anonymous": False,
            "color": "",
            "badges": [],
            "system_message": "sys_msg",
            "message_id": "test_"+randString(),
            "message": {
                "text": "",
                "fragments": []
            },
            "notice_type": "<string>",
            "sub": {
                "sub_tier": "1000",
                "is_prime": False,
                "duration_months": 1
            },
            "resub": {
                "cumulative_months": 10,
                "duration_months": 1,
                "streak_months": None,
                "sub_tier": "1000",
                "is_prime": False,
                "is_gift": False,
                "gifter_is_anonymous": None,
                "gifter_user_name": None
            },
            "sub_gift": {
                "duration_months": 1,
                "cumulative_months": 10,
                "sub_tier": "1000",
                "recipient_user_name": "<string>"
            },
            "community_sub_gift": {
                "sub_tier": "1000",
                "total": 5
            },
            "gift_paid_upgrade": {
                "gifter_is_anonymous": None,
                "gifter_user_name": "<string>"
            },
            "prime_paid_upgrade": {
                "sub_tier": "1000"
            },
            "pay_it_forward": {
                "gifter_is_anonymous": None,
                "gifter_user_name": "<string>"
            },
            "raid": {
                "viewer_count": 100,
                "user_name": "<string>"
            },
            "unraid": {},
            "announcement": {
                "color": "#0000FF"
            },
            "bits_badge_tier": {
                "tier": 1000
            },
            "charity_donation": {
                "charity_name": "Charity Name",
                "amount": 10.0
            },
            "shared_chat_sub": None,
            "shared_chat_resub": None,
            "shared_chat_sub_gift": None,
            "shared_chat_community_sub_gift": None,
            "shared_chat_gift_paid_upgrade": None,
            "shared_chat_prime_paid_upgrade": None,
            "shared_chat_pay_it_forward": None,
            "shared_chat_raid": None,
            "shared_chat_announcement": None,
            "source_broadcaster_user_id": None,
            "source_broadcaster_user_login": None,
            "source_broadcaster_user_name": None,
            "source_message_id": None,
            "source_badges": None
        }
    },
    "channel.raid": {
        "subscription": {
            "id": "test_"+randString(),
            "type": "channel.raid"
        },
        "event": {
            "from_broadcaster_user_id": "1234",
            "from_broadcaster_user_login": "cool_user",
            "from_broadcaster_user_name": "Cool_User",
            "to_broadcaster_user_id": "1337",
            "to_broadcaster_user_login": "cooler_user",
            "to_broadcaster_user_name": "Cooler_User",
            "viewers": 9001
        }
    }
}

def test_meta_data():
    return {
            "message_id": 'test_'+randString(),
            "message_type": "notification",
            "message_timestamp": datetime.now(timezone.utc).isoformat()
    }

class TesterBot(TwitchBot):
    @route('/test/ui')
    async def test_ui(self, request):
        return await self.app.response_html('templates/test_ui.html')

    @route('/test/{cmd}/', method='POST')
    async def test(self, request):
        cmd = request.match_info['cmd']
        args = await request.json()
        logger.info(f"/test/{cmd}, {args = }")
        payload = {}
        match cmd:
            case "channel.raid":
                payload = test_payloads["channel.raid"]
                payload["event"]["viewer_count"] = int(args.get("viewer_count", 1))
                payload["event"]["from_broadcaster_user_name"] = args.get("from", "Cool_User")
            case "channel.cheer":
                payload = test_payloads["channel.cheer"]
                payload["event"]["bits"] = int(args.get("bits", 1))
                payload["event"]["is_anonymous"] = args.get("anon", False)
            case "channel.bits.use":
                payload = test_payloads["channel.bits.use"]
                payload["event"]["bits"] = int(args.get("bits", 1))
            case "channel.subscribe":
                payload = test_payloads["channel.subscribe"]
                payload["event"]["tier"] = args.get("tier", 1)
                payload["event"]["is_gift"] = args.get("gifted", False)
            case "channel.subscription.gift":
                payload = test_payloads["channel.subscription.gift"]
                payload["event"]["total"] = int(args.get("total", 1))
                payload["event"]["tier"] = args.get("tier", 1)
                payload["event"]["is_anonymous"] = args.get("anon", False)
            case "channel.subscription.message":
                payload = test_payloads["channel.subscription.message"]
                payload["event"]["tier"] = args.get("tier", 1)
                payload["event"]["cumulative_months"] = int(args.get("months", 1))
                payload["event"]["streak_months"] = int(args.get("streak", 1))
                payload["event"]["message"] = args.get("msg", "Yaba daba DO!")
            case "channel.goal.progress":
                payload = test_payloads["channel.goal.progress"]
                payload["event"]["type"] = args.get("type", "bits")
                payload["event"]["current_amount"] = int(args.get("current", 0))
                payload["event"]["target_amount"] = int(args.get("target", 100))
            case "channel.hype_train.progress":
                payload = test_payloads["channel.hype_train.progress"]
                payload["event"]["level"] = int(args.get("level", 1))
                payload["event"]["total_contributions"] = int(args.get("total", 100))
                payload["event"]["progress"] = int(args.get("progress", 50))
            case "channel.hype_train.end":
                payload = test_payloads["channel.hype_train.end"]
                payload["event"]["level"] = int(args.get("level", 1))
                payload["event"]["total"] = int(args.get("total", 100))
            case "channel.follow":
                payload = test_payloads["channel.follow"]
                payload["event"]["user_name"] = args.get("user_name", "cool_user")
            case "channel.chat.notification":
                payload = test_payloads["channel.chat.notification"]
                notice_type = args.get("notice_type", "")
                payload["event"]["notice_type"] = notice_type
                payload["event"]["system_message"] = args.get("system_message", "system_message")
                payload["event"]["message"]["text"] = args.get("message", "")
                payload["event"]["user_name"] = args.get("user_name", "cool_user")
                payload["event"]["color"] = args.get("color", "#555555")
                match notice_type:
                    case "sub":
                        payload["event"]["sub"] = {
                            "sub_tier": args.get("sub_tier", "1000"),
                            "is_prime": args.get("is_prime", False),
                            "duration_months": int(args.get("duration_months", 1))
                        }
                    case "resub":
                        payload["event"]["resub"] = {
                            "cumulative_months": int(args.get("cumulative_months", 10)),
                            "duration_months": int(args.get("duration_months", 1)),
                            "streak_months": args.get("streak_months", None),
                            "sub_tier": args.get("sub_tier", "1000"),
                            "is_prime": args.get("is_prime", False),
                            "is_gift": args.get("is_gift", False),
                            "gifter_is_anonymous": args.get("gifter_is_anonymous", None),
                            "gifter_user_name": args.get("gifter_user_name", None)
                        }
                    case "sub_gift":
                        payload["event"]["sub_gift"] = {
                            "duration_months": int(args.get("duration_months", 1)),
                            "cumulative_months": int(args.get("cumulative_months", 10)),
                            "sub_tier": args.get("sub_tier", "1000"),
                            "recipient_user_name": args.get("recipient_user_name", "<string>")
                        }
                    case "community_sub_gift":
                        payload["event"]["community_sub_gift"] = {
                            "sub_tier": args.get("sub_tier", "1000"),
                            "total": int(args.get("total", 5))
                        }
                    case "gift_paid_upgrade":
                        payload["event"]["gift_paid_upgrade"] = {
                            "gifter_is_anonymous": args.get("gifter_is_anonymous", None),
                            "gifter_user_name": args.get("gifter_user_name", "<string>")
                        }
                    case "prime_paid_upgrade":
                        payload["event"]["prime_paid_upgrade"] = {
                            "sub_tier": args.get("sub_tier", "1000")
                        }
                    case "raid":
                        payload["event"]["raid"] = {
                            "viewer_count": int(args.get("viewer_count", 100)),
                            "profile_image_url": args.get("profile_image_url", "<string>"),
                            "user_name": args.get("user_name", "<string>")
                        }
                    case "unraid":
                        payload["event"]["unraid"] = {}
                    case "pay_it_forward":
                        payload["event"]["pay_it_forward"] = {
                            "gifter_is_anonymous": args.get("gifter_is_anonymous", None),
                            "gifter_user_name": args.get("gifter_user_name", "<string>")
                        }
                    case "announcement":
                        payload["event"]["announcement"] = {
                            "color": args.get("color", "#0000FF")
                        }
                    case "bits_badge_tier":
                        payload["event"]["bits_badge_tier"] = {
                            "tier": int(args.get("tier", 1000))
                        }
                    case "charity_donation":
                        payload["event"]["charity_donation"] = {
                            "charity_name": args.get("charity_name", "Charity Name"),
                            "amount": float(args.get("amount", 10.0))
                        }
            case _:
                raise ValueError(f"Unknown event type: {cmd}")
        await self.ws.handle_message(
            {"metadata": test_meta_data(), "payload": payload}
        )
        return self.app.response_json({"status": True})
