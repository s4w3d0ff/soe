import copy
import json
import random
import logging
from poolguy import Alert
from .spotifyapi import duck_volume
from .tts import generate_speech, VOICES

logger = logging.getLogger(__name__)


#################################=========---------
### channel.chat.notification ###=============---------
#################################=================---------
class SubNoto(Alert):
    queue_skip = False
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "yaaay"

    @duck_volume(volume=30)
    async def process(self):
        notice_type = self.data['notice_type']
        name = "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name']
        #sys_message = self.data['system_message']
        event = self.data[notice_type]
        tier = int(event['sub_tier'][0])
        #is_prime = event['is_prime']
        #duration = event['duration_months']
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(self._text, f" {name} subscribed! \n-tier {tier}-")
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)

class ResubNoto(Alert):
    queue_skip = False
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "goingupthere"
        self._sub_tts_path = "db/sub_tts.mp3"
        self._sub_tts_source = "sub_tts"

    @duck_volume(volume=30)
    async def process(self):
        notice_type = self.data['notice_type']
        name = "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name']
        #sys_message = self.data['system_message']
        event = self.data[notice_type]
        #cumulative_months = event['cumulative_months']
        #duration_months = event['duration_months']
        #streak_months = event['streak_months']
        tier = int(event['sub_tier'][0])
        total = event['cumulative_months']
        #is_prime = event['is_prime']
        #is_gift = event['is_gift']
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            tts_fp = None
            txt = self.data["message"].get("text", "")
            if txt:
                voice = random.choice(list(VOICES.keys()))
                tts_fp = await generate_speech(txt, self._sub_tts_path, voice)
            await self.bot.obsws.set_source_text(self._text, f" {name} has been subscribed for {int(total)} months!")
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)
            if tts_fp:
                await self.bot.obsws.show_and_wait(self._sub_tts_source, self._scene)

class GiftsubNoto(Alert):
    queue_skip = False
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "reallynice"

    @duck_volume(volume=30)
    async def _process(self, event):
        name = "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name']
        tier = event['sub_tier'][0]
        duration = event['duration_months']
        #cumulative_total = event['cumulative_total']
        recipient_user_name = event['recipient_user_name']
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(
                    self._text, 
                    f" {name} gifted {recipient_user_name} a tier {tier} sub{' for '+str(duration)+' months in advance' if duration > 1 else '' }!"
                )
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)
    
    async def process(self):
        event = self.data[self.data['notice_type']]
        if event["community_gift_id"]:
            return
        await self._process(event)

class CommunitygiftsubNoto(Alert):
    queue_skip = False
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "reallynice"

    @duck_volume(volume=30)
    async def process(self):
        notice_type = self.data['notice_type']
        name = "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name']
        #sys_message = self.data['system_message']
        event = self.data[notice_type]
        tier = event['sub_tier'][0]
        total = event['total']
        #cumulative_total = event['cumulative_total']
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(total, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(
                    self._text, 
                    f" {name} gifted {total} a subs! \n-tier {tier}-"
                )
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)

class GiftpaidupgradeNoto(Alert):
    queue_skip = False
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "yaaay"

    @duck_volume(volume=30)
    async def process(self):
        notice_type = self.data['notice_type']
        name = "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name']
        sys_message = self.data['system_message']
        event = self.data[notice_type]
        tier = event['sub_tier'][0]
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(
                    self._text, 
                    f" {name} upgraded from a gift sub to a paid tier {tier} sub!"
                )
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)

class PrimepaidupgradeNoto(Alert):
    queue_skip = False
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "yaaay"

    @duck_volume(volume=30)
    async def process(self):
        notice_type = self.data['notice_type']
        name = "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name']
        sys_message = self.data['system_message']
        event = self.data[notice_type]
        tier = event['sub_tier'][0]
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't{tier}')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(
                    self._text, 
                    f" {name} upgraded from a prime to a paid tier {tier} sub!"
                )
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)

class PayitforwardNoto(Alert):
    queue_skip = False
    priority = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "yaaay"

    @duck_volume(volume=30)
    async def process(self):
        notice_type = self.data['notice_type']
        name = "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name']
        sys_message = self.data['system_message']
        event = self.data[notice_type]
        gifter = "Anonymous" if event['gifter_is_anonymous'] else event['gifter_user_name'] 
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(1, f't1')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(
                    self._text, 
                    f" {name} is paying forward the sub gifted to them by {gifter}!"
                )
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)

class RaidNoto(Alert):
    queue_skip = False
    priority = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scene = "[S] Bit Alerts"
        self._altscenes = ["CheerText", "alertbg", "AlerttxtBG"]
        self._text = "CheerText"
        self._source = "hotfeet"

    @duck_volume(volume=30)
    async def process(self):
        notice_type = self.data['notice_type']
        event = self.data[notice_type]
        raidFrom = event['user_login']
        img_url = event['profile_image_url']
        views = event['viewer_count']
        await self.bot.http.sendChatMessage(f"{raidFrom} thank you for the {views} viewer raid!")
        #await self.bot.http.sendShoutout(to_broadcaster_id=event['user_id'])
        if hasattr(self.bot, 'subathon'):
            if self.bot.subathon.is_running():
               self.bot.subathon.add_time(int(views), 'raids')
        if hasattr(self.bot, 'obsws'):
            await self.bot.obsws.set_source_text(self._text, f" {raidFrom} is raiding with {views} viewers!")
            for a in self._altscenes:
                await self.bot.obsws.show_source(a, self._scene)
            await self.bot.obsws.show_and_wait(self._source, self._scene)
            await self.bot.obsws.set_source_text(self._text, "")
            for a in self._altscenes:
                await self.bot.obsws.hide_source(a, self._scene)
        


class ChannelChatNotification(Alert):
    priority = 1
    queue_skip = True

    async def _store(self):
        out = {}
        for key, value in copy.deepcopy(self.data).items():
            # skip shared chat notos
            if key.startswith('shared_') or key.startswith('source_') or key.startswith('broadcaster_'):
                continue
            # skip empty values and keys that are not needed
            if not value or key in ["notice_type", "chatter_user_name"]:
                continue
            # convert lists to json strings
            if isinstance(value, list):
                out[key] = json.dumps(value)
            # walk first level of dict and convert lists and dicts to json strings
            elif isinstance(value, dict):
                for k, v in copy.deepcopy(self.data[key]).items():
                    if isinstance(v, list) or isinstance(v, dict):
                        out[f'{key}_{k}'] = json.dumps(v)
                    else:
                        out[f'{key}_{k}'] = v
            else:
                # pass through other types
                out[key] = value
        out["timestamp"] = self.timestamp
        out["message_id"] = self.message_id
        await self.bot.storage.insert(
            f"channel_chat_notification_{self.data["notice_type"]}", 
            out
        )

    async def process(self):
        notice_type = self.data['notice_type']
        if notice_type.startswith('shared'):
            return
        logger.debug(f"eventsub.{self.channel}.{notice_type}.data:\n{json.dumps(self.data, indent=4)}")
        alert = None
        args = [self.bot, self.message_id, self.channel, self.data.copy(), self.timestamp]
        match notice_type:
            case "sub":
                alert = SubNoto(*args)
            case "resub":
                alert = ResubNoto(*args)
            case "sub_gift":
                alert = GiftsubNoto(*args)
            case "community_sub_gift":
                alert = CommunitygiftsubNoto(*args)
            case "gift_paid_upgrade":
                alert = GiftpaidupgradeNoto(*args)
            case "prime_paid_upgrade":
                alert = PrimepaidupgradeNoto(*args)
            case "pay_it_forward":
                alert = PayitforwardNoto(*args)
            case "raid":
                alert = RaidNoto(*args)
            case "unraid":
                pass
            case "announcement":
                pass
            case "bits_badge_tier":
                pass
            case "charity_donation":
                pass
            case _:
                pass
        if alert:
            if alert.store:
                await alert.store()
            await self.bot.ws.notification_handler._queue.put(alert)
        else:
            await self._store()
