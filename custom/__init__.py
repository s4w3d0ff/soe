from .alerts import (
    ChannelBanAlert, 
    ChannelGoalProgressAlert, 
    ChannelCheerAlert, 
    ChannelRaidAlert, 
    ChannelFollowAlert,
    ChannelChatMessageAlert, 
    ChannelChatNotificationAlert,
    ChannelChannelPointsCustomRewardRedemptionAddAlert,
    ChannelHypeTrainProgressAlert, 
    ChannelHypeTrainEndAlert,
    ChannelSubscribeAlert, 
    ChannelSubscriptionGiftAlert, 
    ChannelSubscriptionMessageAlert
    )

alert_objs = {
    'channel.chat.notification': ChannelChatNotificationAlert,
    'channel.chat.message': ChannelChatMessageAlert,
    'channel.ban': ChannelBanAlert,
    'channel.channel_points_custom_reward_redemption.add': ChannelChannelPointsCustomRewardRedemptionAddAlert,
    'channel.hype_train.progress': ChannelHypeTrainProgressAlert,
    'channel.hype_train.end': ChannelHypeTrainEndAlert,
    'channel.subscribe': ChannelSubscribeAlert,
    'channel.subscription.message': ChannelSubscriptionMessageAlert,
    'channel.subscription.gift': ChannelSubscriptionGiftAlert,
    'channel.goal.progress': ChannelGoalProgressAlert,
    'channel.cheer': ChannelCheerAlert,
    'channel.follow': ChannelFollowAlert,
    'channel.raid': ChannelRaidAlert
}
