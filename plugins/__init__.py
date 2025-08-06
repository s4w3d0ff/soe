# bots -----------------------------------
from .bits import TotemBot
from .chat import ChatBot, BlackHoleBot, DumpCupBot
from .goals import GoalBot
from .predictions import PredictionBot
from .subathon import SubathonBot
from .tester import TesterBot
from .obsapi import OBSBot
from .spotifyapi import SpotifyBot
from .tarkov import TarkovBot
from .skynet import AIBot
from .dcord import DiscordBot
# alerts -----------------------------------
from .ban import ChannelBan, ChannelSuspiciousUserMessage
from .bits import ChannelBitsUse
from .channelpoints import ChannelChannelPointsCustomRewardRedemptionAdd
from .chat import ChannelChatMessage, ChannelChatMessageDelete, ChannelChatClearUserMessages
from .chatnotos import ChannelChatNotification
from .follow import ChannelFollow
from .goals import ChannelGoalProgress
from .hypetrain import ChannelHypeTrainProgress, ChannelHypeTrainEnd
from .predictions import ChannelPredictionBegin, ChannelPredictionProgress, ChannelPredictionLock, ChannelPredictionEnd
from .dcord import StreamOnline
# others  -----------------------------------
from .tts import generate_speech

alert_objs = {
    'channel.ban': ChannelBan,
    'channel.suspicious_user.message': ChannelSuspiciousUserMessage,
    'channel.bits.use': ChannelBitsUse,
    'channel.channel_points_custom_reward_redemption.add': ChannelChannelPointsCustomRewardRedemptionAdd,
    'channel.chat.message': ChannelChatMessage,
    'channel.chat.message_delete': ChannelChatMessageDelete,
    'channel.chat.clear_user_messages': ChannelChatClearUserMessages,
    'channel.chat.notification': ChannelChatNotification,
    'channel.follow': ChannelFollow,
    'channel.goal.progress': ChannelGoalProgress,
    'channel.hype_train.progress': ChannelHypeTrainProgress,
    'channel.hype_train.end': ChannelHypeTrainEnd,
    'channel.prediction.begin': ChannelPredictionBegin,
    'channel.prediction.progress': ChannelPredictionProgress,
    'channel.prediction.lock': ChannelPredictionLock,
    'channel.prediction.end': ChannelPredictionEnd,
    'stream.online': StreamOnline
}
