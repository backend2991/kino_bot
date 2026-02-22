import aiosqlite
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

async def generate_payments_pdf(db_path="movies.db", output_pdf="payments_history.pdf"):
    async with aiosqlite.connect(db_path) as db:
        # SELECT ga yangi ustunlarni qo'shdik
        async with db.execute("SELECT id, user_id, full_name, username, phone_number, sub_type, status, reason, date FROM payments ORDER BY id DESC") as cursor:
            rows = await cursor.fetchall()

    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    # 8 ta ustun uchun koordinatalar (X o'qi)
    cols = [15, 35, 95, 175, 245, 315, 365, 465, 580] 
    
    def draw_headers(canvas_obj, current_y):
        canvas_obj.setFont("Helvetica-Bold", 7)
        headers = ["ID", "User ID", "Ism", "Username", "Telefon", "Tarif", "Holat", "Sabab", "Sana"]
        for i, text in enumerate(headers):
            canvas_obj.drawString(cols[i] + 2, current_y + 5, text)
        canvas_obj.rect(cols[0], current_y, cols[-1] - cols[0], 20)
        return current_y - 20

    y = height - 80
    y = draw_headers(c, y)
    c.setFont("Helvetica", 7)

    for row in rows:
        p_id, u_id, name, uname, phone, sub, status, reason, date = row
        
        c.drawString(cols[0] + 2, y + 5, str(p_id))
        c.drawString(cols[1] + 2, y + 5, str(u_id))
        c.drawString(cols[2] + 2, y + 5, str(name)[:18])
        c.drawString(cols[3] + 2, y + 5, f"@{uname}" if uname != "yo'q" else "-")
        c.drawString(cols[4] + 2, y + 5, str(phone))
        c.drawString(cols[5] + 2, y + 5, str(sub))
        
        # Holat rangi
        color = (0, 0.5, 0) if status == "tasdiqlandi" else (0.8, 0, 0)
        c.setFillColorRGB(*color)
        c.drawString(cols[6] + 2, y + 5, "OK" if status == "tasdiqlandi" else "RAD")
        c.setFillColorRGB(0, 0, 0)
        
        c.drawString(cols[7] + 2, y + 5, str(reason)[:20])
        c.drawString(cols[8] + 2, y + 5, str(date)[5:16]) # Oyni va minutni ko'rsatadi

        c.rect(cols[0], y, cols[-1] - cols[0], 20)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            y = draw_headers(c, y)
            c.setFont("Helvetica", 7)

    c.save()
    return output_pdf