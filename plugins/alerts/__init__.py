from .channelpoints import ChannelChannelPointsCustomRewardRedemptionAdd
from .chatnotos import ChannelChatNotification
from .ban import ChannelBan
from .others import (
    ChannelHypeTrainEnd, 
    ChannelHypeTrainProgress, 
    ChannelGoalProgress, 
    ChannelChatMessage, 
    ChannelFollow
    )
from .bits import ChannelBitsUse

alert_objs = {
    'channel.chat.notification': ChannelChatNotification,
    'channel.chat.message': ChannelChatMessage,
    'channel.ban': ChannelBan,
    'channel.channel_points_custom_reward_redemption.add': ChannelChannelPointsCustomRewardRedemptionAdd,
    'channel.hype_train.progress': ChannelHypeTrainProgress,
    'channel.hype_train.end': ChannelHypeTrainEnd,
    'channel.goal.progress': ChannelGoalProgress,
    'channel.bits.use': ChannelBitsUse,
    'channel.follow': ChannelFollow
}
