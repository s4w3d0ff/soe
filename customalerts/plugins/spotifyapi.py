from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from functools import wraps
from poolguy.utils import ColorLogger, re, loadJSON, asyncio

logger = ColorLogger(__name__)
spoty = Spotify(auth_manager=SpotifyOAuth(
        **loadJSON("plugins/auth.json")['SPOTIFY'], 
        open_browser=True
    ))

async def get_current_volume():
    """ Get the current volume level of the Spotify player.
    while True:
        try:
            playback_info = spoty.current_playback()
            if playback_info and 'device' in playback_info:
                volume = playback_info['device']['volume_percent']
                return volume
            else:
                logger.warning("No playback information available.")
        except Exception as e:
            logger.error(f"Failed to get current volume: {e}")
        await asyncio.sleep(0.5)"""
    return None

async def set_volume(level):
    """ Set the Spotify player volume to a specific level. 
    while True:
        try:
            if 0 <= level <= 100:
                spoty.volume(level)
                logger.warning(f"Volume set to {level}%.")
                return
            else:
                logger.error("Volume level must be between 0 and 100.")
                return
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
        await asyncio.sleep(0.5)"""
    pass


def get_now_playing():
    i = spoty.current_user_playing_track()['item']
    out = {
        "name": i['name'],
        "artists": ', '.join([a['name'] for a in i['artists']]),
        "url": i['external_urls']['spotify'],
        "uri": i['uri'],
        "art": i['album']['images'][0]['url'],
        }
    return out
    
def get_current_queue(max=3):
    r = spoty.queue()
    qu = r['queue']
    cur = r['currently_playing']
    current = {
        "name": cur['name'],
        "artists": ', '.join([a['name'] for a in cur['artists']]),
        "url": cur['external_urls']['spotify'],
        "uri": cur['uri'],
        "art": cur['album']['images'][0]['url'],
        }
    queued = []
    for i in qu:
        queued.append({
        "name": i['name'],
        "artists": ', '.join([a['name'] for a in i['artists']]),
        "url": i['external_urls']['spotify'],
        "uri": i['uri'],
        "art": i['album']['images'][0]['url'],
        })
    return current, queued[:max]

def search_for_song(query, max=1):
    re = spoty.search(q=query, type='track', limit=max)
    tracks = []
    if re['tracks']['items']:
        for i in re['tracks']['items']:
            tracks.append({
            "name": i['name'],
            "artists": ', '.join([a['name'] for a in i['artists']]),
            "url": i['external_urls']['spotify'],
            "uri": i['uri'],
            "art": i['album']['images'][0]['url'],
        })
        return tracks
    else:
        return None


def skip_current_song():
    spoty.next_track()

def get_all_playlists():
    r = spoty.current_user_playlists()
    return {p['name']: p['uri'] for p in r['items']}
    
def get_user_playlist(playlist_id):
    playlist_tracks = spoty.playlist_tracks(playlist_id.strip("spotify:playlist:"))
    return [track['track']['uri'] for track in playlist_tracks['items']]

def get_user_playlist_uri(name):
    pl = get_all_playlists()
    if name not in pl:
        return create_playlist(name)
    return pl[name]

def create_playlist(name, public=True, collaborative=False, description=None):
    user_id = spoty.me()['id']
    playlist = spoty.user_playlist_create(user=user_id, name=name, public=public, collaborative=collaborative, description=description)
    return playlist['uri']


def add_track_to_playlist(playlist_id, track_uri):
    if not track_uri.startswith("spotify:track:"):
        track_uri = "spotify:track:"+track_uri
    spoty.playlist_add_items(playlist_id.strip("spotify:playlist:"), items=[track_uri])


def add_playlist_to_playlist(destination_playlist_id, source_playlist_id):
    tracks = spoty.playlist_tracks(source_playlist_id.strip("spotify:playlist:"))
    track_uris = [track['track']['uri'] for track in tracks['items']]
    spoty.playlist_add_items(destination_playlist_id.strip("spotify:playlist:"), items=track_uris)

def remove_track_from_playlist(playlist_id, track_uri):
    if not track_uri.startswith("spotify:track:"):
        track_uri = "spotify:track:" + track_uri
    spoty.playlist_remove_all_occurrences_of_items(playlist_id.strip("spotify:playlist:"), items=[track_uri])

def remove_all_tracks_from_playlist(playlist_id):
    playlist_tracks = spoty.playlist_tracks(playlist_id.strip("spotify:playlist:"))
    track_uris = [track['track']['uri'] for track in playlist_tracks['items']]
    if track_uris:
        spoty.playlist_remove_all_occurrences_of_items(playlist_id.strip("spotify:playlist:"), items=track_uris)

def play_playlist_on_shuffle(uri):
    if not uri.startswith("spotify:playlist:"):
        uri = "spotify:playlist:"+uri
    spoty.start_playback(context_uri=uri, shuffle_mode=True)
    
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


def set_spotify_volume(volume=2):
    """
    A decorator that temporarily changes Spotify volume during function execution.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Store original volume
            old_vol = await get_current_volume()
            # Set temporary volume
            await set_volume(volume)
            try:
                # Execute the wrapped function
                result = await func(*args, **kwargs)
                return result
            finally:
                # Restore original volume, even if an error occurs
                await set_volume(old_vol)
        return wrapper
    return decorator