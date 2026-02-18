import aiosqlite
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

async def generate_users_pdf(db_path="movies.db", output_pdf="users_list.pdf"):
    if not os.path.exists(db_path):
        return None  

    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT id, user_id, full_name, is_bann FROM users") as cursor:
            rows = await cursor.fetchall()

    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "Foydalanuvchilar Ro'yxati")
    
    cols = [40, 70, 180, 450, 550]
    y = height - 80

    c.setFont("Helvetica-Bold", 10)
    c.drawString(cols[0] + 5, y + 5, "ID")
    c.drawString(cols[1] + 5, y + 5, "Telegram ID")
    c.drawString(cols[2] + 5, y + 5, "To'liq Ism")
    c.drawString(cols[3] + 5, y + 5, "Holati")

    c.rect(cols[0], y, cols[4]-cols[0], 20)
    for x in cols:
        c.line(x, y, x, y + 20)

    y -= 20
    c.setFont("Helvetica", 9)
    
    for row in rows:
        u_id, tg_id, f_name, is_bann = row
        
        c.drawString(cols[0] + 5, y + 5, str(u_id))
        c.drawString(cols[1] + 5, y + 5, str(tg_id))
        c.drawString(cols[2] + 5, y + 5, str(f_name)[:50] if f_name else "Ism yo'q")
        
        # Mantiqni barcha holatlar uchun tekshiramiz
        # is_bann 1, True, "1" yoki "True" bo'lsa Banned chiqadi
        if is_bann in [1, True, "1", "True", "true"]:
            status = "BANNED"
            c.setFillColorRGB(0.8, 0, 0)
        else:
            status = "ACTIVE"
            c.setFillColorRGB(0, 0.5, 0)
            
        c.drawString(cols[3] + 5, y + 5, status)
        c.setFillColorRGB(0, 0, 0)

        c.rect(cols[0], y, cols[4]-cols[0], 20)
        for x in cols:
            c.line(x, y, x, y + 20)

        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)

    c.save()
    return output_pdf