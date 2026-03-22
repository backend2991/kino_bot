import aiosqlite
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
    
    await curr.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                username TEXT,
                phone_number TEXT,
                sub_type TEXT,
                status TEXT,
                reason TEXT,
                date TEXT
            )
        """)
    await conn.commit()
    await conn.close()

async def insert_movie(title, janr, country, language, about, adjactive, code, file_id):
    async with aiosqlite.connect('movies.db') as conn:
        await conn.execute("""
INSERT OR IGNORE INTO movies(title, janr, country, language, about, adjactive, code, file_id)
VALUES(?, ?, ?, ?, ?, ?, ?, ?)
""", (title, janr, country, language, about, adjactive, code, file_id))
        await conn.commit()

async def insert_users(user_id, full_name, is_bann):
    async with aiosqlite.connect('movies.db') as conn:
        await conn.execute("""
                INSERT OR IGNORE INTO users(user_id, full_name, is_bann)
                VALUES(?, ?, ?)
            """, (user_id, full_name, is_bann))
        await conn.commit()

async def get_movie_by_code(code):
    async with aiosqlite.connect('movies.db') as conn:
        conn.row_factory = aiosqlite.Row  
        async with conn.execute("SELECT * FROM movies WHERE code = ?", (code,)) as cursor:
            movie = await cursor.fetchone()
            return movie

async def is_ban(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        await conn.execute("UPDATE users SET is_bann='true' WHERE user_id=?", (user_id,))
        await conn.commit()
       
async def is_not_ban(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        await conn.execute("UPDATE users SET is_bann='false' WHERE user_id=?", (user_id,))
        await conn.commit()

async def insert_payment(user_id, full_name, username, phone, sub_type, status, reason="-"):
    async with aiosqlite.connect('movies.db') as db:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await db.execute("""
            INSERT INTO payments (user_id, full_name, username, phone_number, sub_type, status, reason, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, username, phone, sub_type, status, reason, date))
        await db.commit()

async def check_user_ban(user_id):
    async with aiosqlite.connect('movies.db') as db:
        async with db.execute("SELECT is_bann FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0] == 'false' 
            return True
        
async def delete_movie_by_code(code: str):
    async with aiosqlite.connect("movies.db") as db: 
        cursor = await db.execute("SELECT * FROM movies WHERE code = ?", (code,))
        movie = await cursor.fetchone()
        if movie:
            await db.execute("DELETE FROM movies WHERE code = ?", (code,))
            await db.commit()
            return True  
        return False

async def update_user_subscription(user_id, sub_type):
    async with aiosqlite.connect("movies.db") as db:
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        
        await db.execute("""
            UPDATE users 
            SET sub_type=?, sub_start_date=?, sub_end_date=? 
            WHERE user_id=?
        """, (sub_type, start_date, end_date, user_id))
        await db.commit()

async def check_subscription_expiry(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT sub_end_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row['sub_end_date']:
                expiry_date = datetime.strptime(row['sub_end_date'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() > expiry_date:
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