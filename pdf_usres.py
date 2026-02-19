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
    cols = [40, 80, 180, 450, 550] 
    
    def draw_headers(canvas_obj, current_y):
        canvas_obj.setFont("Helvetica-Bold", 10)
        headers = ["ID", "Telegram ID", "To'liq Ism", "Holati"]
        for i, text in enumerate(headers):
            canvas_obj.drawString(cols[i] + 5, current_y + 5, text)
        
        canvas_obj.rect(cols[0], current_y, cols[-1] - cols[0], 20)
        return current_y - 20

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "Foydalanuvchilar Ro'yxati")
    
    y = height - 100
    y = draw_headers(c, y)

    c.setFont("Helvetica", 9)
    for row in rows:
        u_id, tg_id, f_name, is_bann = row
        
        clean_name = str(f_name)[:45] if f_name else "Ism yo'q"
        
        c.drawString(cols[0] + 5, y + 5, str(u_id))
        c.drawString(cols[1] + 5, y + 5, str(tg_id))
        c.drawString(cols[2] + 5, y + 5, clean_name)
        
        if is_bann in [1, True, "1", "True", "true"]:
            status, color = "BANNED", (0.8, 0, 0)
        else:
            status, color = "ACTIVE", (0, 0.5, 0)
            
        c.setFillColorRGB(*color)
        c.drawString(cols[3] + 5, y + 5, status)
        c.setFillColorRGB(0, 0, 0) 

        c.rect(cols[0], y, cols[-1] - cols[0], 20)
        
        y -= 20
        
        if y < 50:
            c.showPage()
            y = height - 50
            y = draw_headers(c, y) 
            c.setFont("Helvetica", 9)

    c.save()
    return output_pdf