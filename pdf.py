import aiosqlite
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# PythonAnywhere uchun to'liq manzilni aniqlaymiz
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "movies.db")

async def generate_users_pdf(db_path=DB_PATH, output_pdf="foydalanuvchilar.pdf"):
    if not os.path.exists(db_path):
        print(f"Baza topilmadi: {db_path}") # Logda ko'rish uchun
        return None  

    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT id, user_id, full_name, is_bann FROM users") as cursor:
            rows = await cursor.fetchall()

    # Faylni saqlash joyi ham to'liq manzil bo'lgani yaxshi
    output_path = os.path.join(BASE_DIR, output_pdf)
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Kino Bot Foydalanuvchilari")
    
    c.setFont("Helvetica-Bold", 10)
    y = height - 80
    c.drawString(40, y, "ID")
    c.drawString(70, y, "Telegram ID")
    c.drawString(170, y, "To'liq Ism (Full Name)")
    c.drawString(450, y, "Holati")
    c.line(40, y - 5, 550, y - 5)

    c.setFont("Helvetica", 9)
    y -= 20
    
    for row in rows:
        u_id, tg_id, f_name, is_bann = row
        
        c.drawString(40, y, str(u_id))
        c.drawString(70, y, str(tg_id))
        
        name_text = str(f_name)[:45] if f_name else "Ism kiritilmagan"
        c.drawString(170, y, name_text)
        
        # is_bann ni tekshirish (ba'zan bazada 0/1 yoki True/False bo'ladi)
        status = "Banned" if is_bann else "Active"
        
        if status == "Banned":
            c.setFillColorRGB(0.8, 0, 0) 
        else:
            c.setFillColorRGB(0, 0.5, 0) 
            
        c.drawString(450, y, status)
        c.setFillColorRGB(0, 0, 0) 
        
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)

    c.save()
    return output_path