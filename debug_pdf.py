import fitz  # PyMuPDF

try:
    doc = fitz.open("Declaration Form.pdf")
    page = doc[0]
    
    # 1. Check for text
    text = page.get_text("text")
    words = page.get_text("words")
    
    print("\n--- DIAGNOSTIC REPORT ---")
    if not words:
        print("[RESULT] NO TEXT FOUND.")
        print("Reason: This PDF is likely a scanned image.")
        print("Solution: You must use 'Fixed Coordinates' mode (Method B).")
    else:
        print(f"[RESULT] Text Found! ({len(words)} words detected)")
        print("Here is the exact text Python sees (Copy this carefully if needed):")
        print("-" * 30)
        print(text[:500])  # Prints first 500 characters
        print("-" * 30)
        
        # 2. visual Debugging: Draw red boxes around text
        # This helps you see WHERE Python thinks the text is.
        for w in words:
            # Draw a red box around every word
            rect = fitz.Rect(w[0], w[1], w[2], w[3])
            page.draw_rect(rect, color=(1, 0, 0), width=0.5)
            
        # 3. Save a debug PDF
        doc.save("debug_view.pdf")
        print("\n[ACTION] Open 'debug_view.pdf'.")
        print("If you see RED BOXES around words, the text is readable.")
        print("If you see NO RED BOXES, it is an image.")

except Exception as e:
    print(f"Error: {e}")