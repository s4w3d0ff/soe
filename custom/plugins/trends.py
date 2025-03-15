from trendspy import Trends
import asyncio
import logging

logger = logging.getLogger(__name__)

tr = Trends(hl='en-US', request_delay=1., max_retries=7)

def to_pascal_case(s):
    words = s.replace("-", " ").replace("_", " ").replace(".", " ").replace(",", " ").replace("'", "").split()
    return "".join(word.capitalize() for word in words)

def get_trending_now(geo='US', language='en-US', hours=24, topic='Games'):
    r = tr.trending_now(geo, language, hours)
    o = r.filter_by_topic(topic)
    return [trend.keyword for trend in o][:10]

async def main():
    from pprint import pprint
    trends = get_trending_now()
    pprint(trends)
    
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s-%(levelname)s-[%(name)s] %(message)s', datefmt="%I:%M:%S%p", level=logging.INFO)
    asyncio.run(main())