import logging
import re
from functools import wraps
from spotifio import Client
from poolguy import TwitchBot, command, route, rate_limit

logger = logging.getLogger(__name__)

def extract_spotify_id(uri_or_url):
    track_pattern = re.compile(r'(?:(?:https?:\/\/)?(?:open\.spotify\.com\/track\/|spotify:track:)([a-zA-Z0-9]+))')
    playlist_pattern = re.compile(r'(?:(?:https?:\/\/)?(?:open\.spotify\.com\/playlist\/|spotify:playlist:)([a-zA-Z0-9]+))')
    track_match = track_pattern.match(uri_or_url)
    playlist_match = playlist_pattern.match(uri_or_url)
    if track_match:
        return track_match.group(1)
    elif playlist_match:
        return playlist_match.group(1)
    else:
        return None

def convert_uri_to_url(uri):
    url = "open.spotify.com/"
    id = extract_spotify_id(uri)
    if not id:
        return
    if "track" in uri:
        url += f"track/{id}"
    if "playlist" in uri:
        url += f"playlist/{id}"
    return url

def duck_volume(volume=20):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get spotify instance from the Alert's bot
            spotify = self.bot.spotify
            old_vol = None
            r = False
            try:
                # Store original volume
                old_vol = await spotify.get_current_volume()
                # Set temporary volume
                await spotify.set_volume(volume)
            finally:
                # Execute the wrapped function
                result = await func(self, *args, **kwargs)
            try:
                # Restore original volume, even if an error occurs
                if old_vol is not None:
                    await spotify.set_volume(old_vol)
            finally:
                return result
        return wrapper
    return decorator


class Spotify(Client):
    async def get_current_volume(self):
        try:
            state = await self.get_playback_state()
        except:
            return None
        if state and 'device' in state:
            return state['device'].get('volume_percent')
        return None

    async def set_volume(self, volume):
        volume = max(0, min(100, volume))
        try:
            await self.set_playback_volume(volume)
            return True
        except:
            return False

    async def get_now_playing(self):
        current = await self.get_currently_playing()
        if not current or 'item' not in current:
            return None
        track = current['item']
        return {
            'name': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'url': track['external_urls']['spotify'],
            'uri': track['uri'],
            'album_art_url': track['album']['images'][0]['url'] if track['album']['images'] else None
        }

    async def skip_track(self):
        await self.skip_to_next()

    async def get_current_queue(self):
        queue = await self.get_queue()
        if not queue or 'queue' not in queue:
            return []
        tracks = []
        for track in queue['queue']:
            tracks.append({
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'url': track['external_urls']['spotify'],
                'uri': track['uri'],
                'album_art_url': track['album']['images'][0]['url'] if track['album']['images'] else None
            })
        return tracks

#==========================================================================================
# SpotifyBot ==============================================================================
#==========================================================================================
class SpotifyBot(TwitchBot):
    def __init__(self, spotify_cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spotify = Spotify(**spotify_cfg)

    async def after_login(self):
        self.spotify.token_handler.storage = self.http.storage
        await self.spotify.login()

    @command(name="nowplaying", aliases=["spotify", "song"])
    @rate_limit(calls=1, period=60, warn_cooldown=30)
    async def now_playing(self, user, channel, args):
        now = await self.spotify.get_now_playing()
        await self.send_chat(f"{now['name']} by {', '.join(now['artists'])} {now['url']}", channel["broadcaster_id"])
    
    @route('/spotify/skip')
    async def spotify_skip(self, request):
        await self.spotify.skip_track()
