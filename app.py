import os
from datetime import datetime
from PIL import Image, ImageEnhance
from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURATION: EDIT THIS SECTION ---
# Look at your 'grid_reference.pdf' and put the X, Y numbers here.
# x = horizontal position, y = vertical position
POSITIONS = {
    "name":            {"x": 80, "y": 172},  # Example: Change these numbers!
    "father_name":     {"x": 280, "y": 172},
    "current_address": {"x": 80, "y": 195},
    "app_date":        {"x": 450, "y": 260},
    "perm_address":    {"x": 75, "y": 328},
    "city":            {"x": 386, "y": 463},
    "install_address": {"x": 75, "y": 506},
    "place":           {"x": 100, "y": 733},
    "sign_date":       {"x": 100, "y": 769},
    
    # SIGNATURE AREA (Top-Left corner of where the image should go)
    "signature":       {"x": 375, "y": 650, "width": 200, "height": 200}
}
# ----------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    try:
        pdf_path = "Declaration Form.pdf"
        doc = fitz.open(pdf_path)
        page = doc[0]

        # 1. Loop through text fields (Your existing logic)
        for field_name, coords in POSITIONS.items():
            if field_name == "signature": continue 
            
            user_input = request.form.get(field_name, "")
            
            # Date Fix
            if user_input and (field_name == "sign_date" or field_name == "app_date"):
                try:
                    date_obj = datetime.strptime(user_input, "%Y-%m-%d")
                    user_input = date_obj.strftime("%d-%m-%Y")
                except ValueError:
                    pass 

            if user_input:
                page.insert_text(
                    (coords['x'], coords['y']), 
                    user_input, 
                    fontsize=12, 
                    fontname="tiro", 
                    color=(0, 0, 0)
                )

        # 2. Handle Signature (Your existing Enhanced logic)
        sig_file = request.files.get('signature')
        if sig_file:
            sig_path = os.path.join(UPLOAD_FOLDER, "temp_sig.png")
            
            # Image Enhancement
            img = Image.open(sig_file)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.1) 
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(5.0) 
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            img.save(sig_path, "PNG", quality=100)

            sig_conf = POSITIONS["signature"]
            img_rect = fitz.Rect(
                sig_conf['x'], 
                sig_conf['y'], 
                sig_conf['x'] + sig_conf['width'], 
                sig_conf['y'] + sig_conf['height']
            )
            page.insert_image(img_rect, filename=sig_path)

        # 3. DECIDE OUTPUT FORMAT (PDF vs JPEG)
        output_format = request.form.get('output_format', 'pdf')
        
        if output_format == 'jpeg':
            # --- CONVERT TO JPEG ---
            # Matrix(2, 2) = Zoom in 2x (High Quality / 150-300 DPI)
            # If you want it even clearer, change to Matrix(3, 3)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
            
            output_path = os.path.join(UPLOAD_FOLDER, "Filled_Declaration.jpg")
            pix.save(output_path)
            mime_type = 'image/jpeg'
        else:
            # --- SAVE AS PDF ---
            output_path = os.path.join(UPLOAD_FOLDER, "Filled_Declaration.pdf")
            doc.save(output_path)
            mime_type = 'application/pdf'

        return send_file(output_path, mimetype=mime_type, as_attachment=True)

    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)