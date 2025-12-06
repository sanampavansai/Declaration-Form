import os
from datetime import datetime
from PIL import Image, ImageEnhance
from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
from rembg import remove, new_session

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURATION: EDIT THIS SECTION ---
POSITIONS = {
    "name":            {"x": 80, "y": 172},
    "father_name":     {"x": 280, "y": 172},
    
    # LONG ADDRESS 1
    "current_address": {
        "x": 80, "y": 195,
        "width_limit": 500,
        "x2": 80, "y2": 218
    },
    
    "app_date":        {"x": 450, "y": 260},
    
    # LONG ADDRESS 2
    "perm_address":    {
        "x": 75, "y": 328,
        "width_limit": 500,
        "x2": 75, "y2": 351
    },
    
    "city":            {"x": 386, "y": 463},
    
    # LONG ADDRESS 3
    "install_address": {
        "x": 75, "y": 506,
        "width_limit": 500,
        "x2": 75, "y2": 528
    },
    
    "place":           {"x": 100, "y": 733},
    "sign_date":       {"x": 100, "y": 769},
    
    # SIGNATURE AREA (Fixed Box)
    "signature":       {"x": 375, "y": 640, "width": 200, "height": 150}
}

# --- HELPER FUNCTION: SPLIT TEXT IF TOO LONG ---
def fit_text_in_lines(page, text, fontname, fontsize, max_width):
    """
    Checks if text fits in width. If not, splits it into two lines.
    Returns: (Line1_Text, Line2_Text)
    """
    # 1. Check if the whole text fits in one line
    length = fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
    if length <= max_width:
        return text, ""  # Fits perfectly
    
    # 2. If too long, find the split point
    words = text.split(' ')
    current_line = ""
    
    for i, word in enumerate(words):
        # Test adding the next word
        test_line = current_line + word + " "
        
        if fitz.get_text_length(test_line, fontname=fontname, fontsize=fontsize) < max_width:
            current_line += word + " "
        else:
            # We hit the limit! 
            # line1 is what we built so far
            line1 = current_line.strip()
            # line2 is the rest of the words
            line2 = " ".join(words[i:])
            return line1, line2
            
    return text, ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    try:
        pdf_path = "Declaration Form.pdf"
        doc = fitz.open(pdf_path)
        page = doc[0]

        # --- 1. AUTO-COPY LOGIC (Before the loop) ---
        install_mode = request.form.get('install_mode', 'same')
        form_overrides = {}
        if install_mode == 'same':
            # This copies the text!
            form_overrides['install_address'] = request.form.get('current_address', '')
        # --------------------------------------------

        # --- 2. LOOP THROUGH FIELDS (Only Once!) ---
        for field_name, coords in POSITIONS.items():
            if field_name == "signature": continue 
            
            # Check Override First
            if field_name in form_overrides:
                user_input = form_overrides[field_name]
            else:
                user_input = request.form.get(field_name, "")
            
            # Date Fix
            if user_input and (field_name == "sign_date" or field_name == "app_date"):
                try:
                    date_obj = datetime.strptime(user_input, "%Y-%m-%d")
                    user_input = date_obj.strftime("%d-%m-%Y")
                except ValueError:
                    pass 

            if user_input:
                # Text Wrapping Logic
                if "width_limit" in coords:
                    line1, line2 = fit_text_in_lines(page, user_input, "tiro", 12, coords["width_limit"])
                    page.insert_text((coords['x'], coords['y']), line1, fontsize=12, fontname="tiro", color=(0, 0, 0))
                    if line2:
                        page.insert_text((coords['x2'], coords['y2']), line2, fontsize=12, fontname="tiro", color=(0, 0, 0))
                else:
                    # Normal Text
                    page.insert_text((coords['x'], coords['y']), user_input, fontsize=12, fontname="tiro", color=(0, 0, 0))

        # 2. SMART SIGNATURE (MEMORY SAFE VERSION)
        sig_file = request.files.get('signature')
        if sig_file:
            sig_path = os.path.join(UPLOAD_FOLDER, "temp_sig.png")
            
            img = Image.open(sig_file)
            
            # --- MEMORY FIX: USE LITE MODEL (u2netp) ---
            # This model is ~5MB instead of ~170MB. It runs easily on free servers.
            my_session = new_session("u2netp")
            img = remove(img, session=my_session)
            # -------------------------------------------
            
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Enhance Ink (Your existing settings)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.1) 
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(5.0) 
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            
            img.save(sig_path, "PNG", quality=100)
            
            # Scaling & Centering (Your existing settings)
            img_w, img_h = img.size
            box_x = POSITIONS["signature"]["x"]
            box_y = POSITIONS["signature"]["y"]
            box_w = POSITIONS["signature"]["width"]
            box_h = POSITIONS["signature"]["height"]

            scale = min(box_w / img_w, box_h / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)

            offset_x = (box_w - new_w) / 2
            offset_y = (box_h - new_h) / 2
            
            final_x = box_x + offset_x
            final_y = box_y + offset_y

            img_rect = fitz.Rect(final_x, final_y, final_x + new_w, final_y + new_h)
            page.insert_image(img_rect, filename=sig_path)

        # --- 4. OUTPUT ---
        output_format = request.form.get('output_format', 'pdf')
        if output_format == 'jpeg':
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
            output_path = os.path.join(UPLOAD_FOLDER, "Filled_Declaration.jpg")
            pix.save(output_path)
            mime_type = 'image/jpeg'
        else:
            output_path = os.path.join(UPLOAD_FOLDER, "Filled_Declaration.pdf")
            doc.save(output_path)
            mime_type = 'application/pdf'

        return send_file(output_path, mimetype=mime_type, as_attachment=True)

    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)