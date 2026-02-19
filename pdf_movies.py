import aiosqlite
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

async def generate_movies_pdf(db_path="movies.db", output_pdf="movies_list.pdf"):
    if not os.path.exists(db_path):
        return None  

    async with aiosqlite.connect(db_path) as db:
        query = "SELECT id, code, title, janr, country FROM movies"
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()

    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    
    
    cols = [30, 60, 110, 300, 450, 560] 
    
    def draw_headers(canvas_obj, current_y):
        canvas_obj.setFont("Helvetica-Bold", 10)
        headers = ["ID", "Kod", "Kino Nomi", "Janr", "Davlat"]
        for i, text in enumerate(headers):
            canvas_obj.drawString(cols[i] + 5, current_y + 5, text)
        
        canvas_obj.rect(cols[0], current_y, cols[-1] - cols[0], 20)
        return current_y - 20

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "Kinolar Ro'yxati (Bazadagi ma'lumotlar)")
    
    y = height - 100
    y = draw_headers(c, y)

    c.setFont("Helvetica", 9)
    for row in rows:
        m_id, m_code, m_title, m_janr, m_country = row
        
        clean_title = str(m_title)[:35] if m_title else "-"
        clean_janr = str(m_janr)[:25] if m_janr else "-"
        clean_country = str(m_country)[:20] if m_country else "-"
        
        c.drawString(cols[0] + 5, y + 5, str(m_id))
        c.drawString(cols[1] + 5, y + 5, str(m_code))
        c.drawString(cols[2] + 5, y + 5, clean_title)
        c.drawString(cols[3] + 5, y + 5, clean_janr)
        c.drawString(cols[4] + 5, y + 5, clean_country)

        c.rect(cols[0], y, cols[-1] - cols[0], 20)
        
        y -= 20
        
        if y < 50:
            c.showPage()
            y = height - 50
            y = draw_headers(c, y) 
            c.setFont("Helvetica", 9)

    c.save()
    return output_pdf