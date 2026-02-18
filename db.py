import aiosqlite

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
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    full_name VARCHAR(150),
    is_bann VARCHAR(10) DEFAULT 'false'
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


async def find_user(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        curr = await conn.cursor()
        await curr.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = await curr.fetchone()
        return user 

async def is_ban(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        curr = await conn.cursor() 
        query = "UPDATE users SET is_bann='true' WHERE user_id=?"
        await curr.execute(query, (user_id,))
        await conn.commit()
       
async def is_unlock_ban(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        curr = await conn.cursor() 
        query = "UPDATE users SET is_bann='false' WHERE user_id=?"
        await curr.execute(query, (user_id,))
        await conn.commit()


        
        
async def check_user_ban(user_id):
    async with aiosqlite.connect('movies.db') as conn:
        curr = await conn.cursor() 
        query = "SELECT is_bann FROM users WHERE user_id = ?"
        data = await curr.execute(query, (user_id,))
        return data.fetchone()



async def check_user_ban(user_id):
    async with aiosqlite.connect('movies.db') as db:
        async with db.execute("SELECT is_bann FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0] == 0 
            return True 