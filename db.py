import aiosqlite
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime, timedelta
async def creat_table():
    conn = await aiosqlite.connect('movies.db')
    curr = await conn.cursor()
    await curr.execute("""
CREATE TABLE IF NOT EXISTS movies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200),
    janr VARCHAR(50),
    country VARCHAR(50),
    language VARCHAR(50),
    about VARCHAR(500),
    adjactive VARCHAR(50),
    code INTEGER UNIQUE,
    file_id VARCHAR(300)
)
""")
    
    await curr.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            full_name TEXT,
            is_bann TEXT DEFAULT 'false',
            sub_type TEXT DEFAULT 'none',
            sub_start_date TEXT,
            sub_end_date TEXT
        )
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            sub_type TEXT,
            price TEXT,
            screenshot_id TEXT,
            status TEXT, -- 'tasdiqlandi' yoki 'rad_etildi'
            reason TEXT, -- rad etish sababi
            date TEXT
        )
    """)
    await conn.commit()
    await conn.close()

async def insert_movie(title, janr, country, language, about, adjactive, code, file_id):
    conn = await aiosqlite.connect('movies.db')
    curr = await conn.cursor()
    await curr.execute("""
INSERT OR IGNORE INTO movies(title, janr, country, language, about, adjactive, code, file_id)
VALUES(?, ?, ?, ?, ?, ?, ?, ?)
""", (title, janr, country, language, about, adjactive, code, file_id))
    await conn.commit()
    await conn.close()
    

async def insert_users(user_id, full_name, is_bann):
    conn = await aiosqlite.connect('movies.db')
    curr = await conn.cursor()
    await curr.execute("""
                INSERT OR IGNORE INTO users(user_id, full_name, is_bann)
                VALUES(?, ?, ?)
            """, (user_id, full_name, is_bann))
    await conn.commit()
    await conn.close()

async def get_movie_by_code(code):
        conn = await aiosqlite.connect('movies.db')
        curr = await conn.cursor() 
        curr.row_factory = aiosqlite.Row  
        cursor = await curr.execute("SELECT * FROM movies WHERE code = ?", (code,))
        movie = await cursor.fetchone()
        await conn.close()
        return movie


 

async def is_ban(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        curr = await conn.cursor() 
        query = "UPDATE users SET is_bann='true' WHERE user_id=?"
        await curr.execute(query, (user_id,))
        await conn.commit()
       
async def is_not_ban(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        await conn.execute("UPDATE users SET is_bann=false WHERE user_id=?", (user_id,))
        await conn.commit()



        
        
async def insert_payment(user_id, full_name, sub_type, price, screenshot_id, status, reason=""):
    async with aiosqlite.connect('movies.db') as conn:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await conn.execute("""
            INSERT INTO payments (user_id, full_name, sub_type, price, screenshot_id, status, reason, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, sub_type, price, screenshot_id, status, reason, date))
        await conn.commit()



async def check_user_ban(user_id):
    async with aiosqlite.connect('movies.db') as db:
        async with db.execute("SELECT is_bann FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0] == 'false' 
            return True
        
async def delete_movie_by_code(code: str):
    """Kino kodiga qarab bazadan o'chirish"""
    async with aiosqlite.connect("movies.db") as db: 
        cursor = await db.execute("SELECT * FROM movies WHERE code = ?", (code,))
        movie = await cursor.fetchone()
        
        if movie:
            await db.execute("DELETE FROM movies WHERE code = ?", (code,))
            await db.commit()
            return True  
        return False
    





async def update_user_subscription(user_id, sub_type, days):
    async with aiosqlite.connect('movies.db') as conn:
        start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        await conn.execute("""
            UPDATE users 
            SET sub_type = ?, sub_start_date = ?, sub_end_date = ? 
            WHERE user_id = ?
        """, (sub_type, start_date, end_date, user_id))
        
        await conn.commit()

async def check_subscription_expiry(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT sub_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row['sub_date']:
                expiry_date = datetime.datetime.strptime(row['sub_date'], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() > expiry_date:
                    await conn.execute("UPDATE users SET sub_type = 'none' WHERE user_id = ?", (user_id,))
                    await conn.commit()
                    return False
                return True
            return False

async def find_user(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        async with conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as curr:
            user = await curr.fetchone()
            return user

