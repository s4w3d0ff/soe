import youtube_dl
from googleapiclient.discovery import build
from .utils import cfg, re, os, asyncio, delete_file_if_exists

youtube = build('youtube', 'v3', developerKey=cfg['YOUTUBE']['key'])

def get_video_url(video_id):
    ydl_opts = {
        'quiet': True,
        'format': 'best[height<=720]'
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_id, download=False)
        return info_dict['url']


def search_youtube(query, max=5):
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=max
    ).execute()
    videos = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append({
                'title': search_result['snippet']['title'],
                'id': search_result['id']['videoId'],
                'channel': search_result['snippet']['channelTitle']
            })
    return videos

def extract_video_id(url):
    regex = (
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/[^/]+/|youtu\.be/|youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})'
    )
    match = re.search(regex, url)
    if match:
        return match.group(1)
    else:
        return None

async def get_video(id, path):
    output_path = path+f"/{id}.mp4"
    delete_file_if_exists(output_path)
    ydl_opts = {'outtmpl': output_path, 'quiet': True, 'format': 'best[height<=720]'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([id])
    while not os.path.exists(output_path):
        await asyncio.sleep(0.5)
    return output_path
