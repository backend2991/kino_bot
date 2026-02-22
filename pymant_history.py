import aiosqlite
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

async def generate_payments_pdf(db_path="movies.db", output_pdf="payments_history.pdf"):
    if not os.path.exists(db_path): return None  

    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT id, user_id, full_name, sub_type, status, reason, date FROM payments ORDER BY id DESC") as cursor:
            rows = await cursor.fetchall()

    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    cols = [20, 45, 110, 210, 270, 330, 450, 575] 
    
    def draw_headers(canvas_obj, current_y):
        canvas_obj.setFont("Helvetica-Bold", 8)
        headers = ["ID", "User ID", "Ism", "Tarif", "Holat", "Sabab", "Sana"]
        for i, text in enumerate(headers):
            canvas_obj.drawString(cols[i] + 3, current_y + 5, text)
        canvas_obj.rect(cols[0], current_y, cols[-1] - cols[0], 20)
        return current_y - 20

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 40, "To'lovlar Tarixi Hisoboti")
    y = height - 80
    y = draw_headers(c, y)

    c.setFont("Helvetica", 8)
    for row in rows:
        p_id, u_id, f_name, sub, status, reason, date = row
        c.drawString(cols[0] + 3, y + 5, str(p_id))
        c.drawString(cols[1] + 3, y + 5, str(u_id))
        c.drawString(cols[2] + 3, y + 5, str(f_name)[:18])
        c.drawString(cols[3] + 3, y + 5, str(sub).capitalize())
        
        color = (0, 0.5, 0) if status == "tasdiqlandi" else (0.8, 0, 0)
        c.setFillColorRGB(*color)
        c.drawString(cols[4] + 3, y + 5, "TASDIQ" if status == "tasdiqlandi" else "RAD")
        c.setFillColorRGB(0, 0, 0)
        
        c.drawString(cols[5] + 3, y + 5, str(reason)[:25])
        c.drawString(cols[6] + 3, y + 5, str(date)[:16])
        c.rect(cols[0], y, cols[-1] - cols[0], 20)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            y = draw_headers(c, y)
    c.save()
    return output_pdf