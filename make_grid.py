import fitz  # PyMuPDF

def create_grid_pdf():
    try:
        doc = fitz.open("Declaration Form.pdf")
        page = doc[0]
        
        # Get page dimensions
        width = int(page.rect.width)
        height = int(page.rect.height)

        # Draw Vertical Lines (X axis)
        for x in range(0, width, 50):
            page.draw_line((x, 0), (x, height), color=(1, 0, 0), width=0.5, overlay=True)
            page.insert_text((x + 2, 20), f"{x}", color=(1, 0, 0), fontsize=8)

        # Draw Horizontal Lines (Y axis)
        for y in range(0, height, 50):
            page.draw_line((0, y), (width, y), color=(0, 0, 1), width=0.5, overlay=True)
            page.insert_text((2, y - 2), f"{y}", color=(0, 0, 1), fontsize=8)

        output_file = "grid_reference.pdf"
        doc.save(output_file)
        print(f"SUCCESS! Open '{output_file}' to see the coordinates.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_grid_pdf()