from poolguy.utils import ColorLogger, re, json
from poolguy.twitchws import Alert

logger = ColorLogger(__name__)

class ChannelChatMessageAlert(Alert):
    """channel.chat.message
    {
      "broadcaster_user_id": "108284496",
      "broadcaster_user_login": "s4w3d0ff",
      "broadcaster_user_name": "s4w3d0ff",
      "source_broadcaster_user_id": null,
      "source_broadcaster_user_login": null,
      "source_broadcaster_user_name": null,
      "chatter_user_id": "108284496",
      "chatter_user_login": "s4w3d0ff",
      "chatter_user_name": "s4w3d0ff",
      "message_id": "de0d647b-6326-430c-9050-ded5c52bb860",
      "source_message_id": null,
      "message": {
        "text": "sgdsfgh",
        "fragments": [
          {
            "type": "text",
            "text": "sgdsfgh",
            "cheermote": null,
            "emote": null,
            "mention": null
          }
        ]
      },
      "color": "#337272",
      "badges": [
        {
          "set_id": "broadcaster",
          "id": "1",
          "info": ""
        },
        {
          "set_id": "subscriber",
          "id": "18",
          "info": "31"
        },
        {
          "set_id": "glitchcon2020",
          "id": "1",
          "info": ""
        }
      ],
      "source_badges": null,
      "message_type": "text",
      "cheer": null,
      "reply": null,
      "channel_points_custom_reward_id": null,
      "channel_points_animation_id": null
    }
    """
    async def parseBadges(self):
        bid = self.data['source_broadcaster_user_id'] or self.data['broadcaster_user_id']
        message_badges = self.data['source_badges'] or self.data['badges']
        chatter_id =  self.data['chatter_user_id']
        if bid not in self.bot.channelBadges:
            self.bot.channelBadges[str(bid)] = await self.bot.getChanBadges(bid)
        return [self.bot.channelBadges[bid][i['set_id']][i['id']] for i in message_badges]

    async def parseEmotesText(self):
        etext = self.data['message']['text']
        for f in self.data['message']['fragments']:
            if f['type'] == 'emote':
                etext = re.sub(
                    r'\b'+re.escape(f['text'])+r'\b', 
                    await self.bot.http.parseTTVEmote(f['emote']['id'], 'animated' if 'animated' in f['emote']['format'] else 'static'), 
                    etext)
        return etext

    async def process(self):
        #logger.debug(f'[Chat] {json.dumps(self.data, indent=2)}', 'purple')
        id = self.data['message_id']
        message = self.data['message']
        badge_urls = await self.parseBadges()
        text = await self.parseEmotesText()
        out = {
            'id': id, 
            'user': self.data['chatter_user_name'], 
            'color': self.data['color'], 
            'badges': badge_urls, 
            'text': text,
            'timestamp': self.timestamp
            }
        await self.bot.chat_queue.put(out)
        logger.debug(f'[Chat] {json.dumps(out, indent=2)}', 'purple')


class ChannelChatNotificationAlert(Alert):
    """ channel.chat.notification """
    async def process(self):
        logger.debug(f'[ChannelChatNotificationAlert] {json.dumps(self.data, indent=2)}', 'purple')
        notice_type = self.data['notice_type']
        if notice_type.startswith('shared'):
            return
        out = {
            "notice_type": notice_type,
            "name": "Anonymous" if self.data['chatter_is_anonymous'] else self.data['chatter_user_name'],
            "message": self.data['message'],
            "sys_message": self.data['system_message'],
            "event": self.data[notice_type]
        }
        await self.bot.alertws_queue.put(out)
        logger.error(f'[ChannelChatNotificationAlert] \n{json.dumps(out, indent=2)}')