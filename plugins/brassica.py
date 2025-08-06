import aiosqlite, sqlite3
import re
import os
import time
import logging
from poolguy import TwitchBot, Alert
from poolguy import route, websocket, command, rate_limit

logger = logging.getLogger(__name__)

LEVELs = {
    "compost": 0,
    "fertile_soil": 1,
    "seed": 2,
    "cotyledon": 3,
    "kohlrabi": 4,
    "kale": 5,
    "collard": 6,
    "brussls_sprout": 7,
    "broccoli": 8,
    "wild_cabbage": 9,
    "savory_cabbage": 10,
    "red_cabbage": 11,
    "award_winning_cabbage": 12
}

"""
lurk_age = time visable in chat between 'ticks'
chat_messages = number of messages in chat since last stream (max 20 counts)
attention = (lurk_age * 1) + (chat_messages * 10)
age = (current_time - created_time)
health = age - attention
"""


class BrassiBot(TwitchBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _create_brassi_table(self):
        """ Create the brassi table if it doesn't exist """
        async with aiosqlite.connect(self.storage.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS brassi (
                    user_id INTEGER,
                    created_time REAL,
                    lurk_ticks INTEGER,
                    chat_points INTEGER,
                    record INTEGER
                )
                """)
            await db.commit()
    
    async def _tick_lurkers(self):
        """ Add to each lurkers lurk_tick in the database """
        async with aiosqlite.connect(self.storage.db_path) as db:
            lurkers = await self.http.getChatters()
            for l in lurkers:
                await db.execute('''
                    UPDATE brassi
                    SET lurk_ticks = lurk_ticks + 1
                    WHERE user_id = ?
                ''', (l["user_id"],))
                await db.commit()
            

    async def _get_brassi_bits(self, user_id):
        week = 86400*7
        q = await self.storage.query(
                'channel_bits_use', 
                'WHERE CAST(timestamp AS REAL) >= ? AND user_id = ?', 
                (time.time()-week, user_id)
            )
        total = 0
        for row in q:
            total += row["bits"]
        return total

    async def get_brassi_health(self, user_id):
        q = await self.storage.query('SELECT * FROM brassi WHERE user_id = ?', (user_id,))
        brass = q[0]
        lurk_score = brass["lurk_ticks"] * 10
        bits = await self._get_brassi_bits(user_id)
        bits_score = bits * 100
        total_score = lurk_score + bits_score
        age_score = max(time.time() - brass["created_time"], 86400*7)
        