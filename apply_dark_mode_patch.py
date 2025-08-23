#!/usr/bin/env python3
"""
STREAMLIT DARK MODE PATCH
========================
Ez a script automatikusan javítja a streamlit_app.py template fájlban a dark mode problémát.
"""

import re

def apply_dark_mode_patch():
    """Dark mode javítások alkalmazása a streamlit_app.py fájlban"""
    
    # Fájl beolvasása
    with open('streamlit_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Háttérszín javítása
    content = content.replace(
        "background-color: white; border:2px solid grey; z-index:9999;",
        "background-color: rgba(40, 40, 40, 0.9); border:2px solid #666; z-index:9999;"
    )
    
    # 2. Szövegszín hozzáadása a div-hez
    content = content.replace(
        "font-size:12px; padding: 10px'>",
        "font-size:12px; padding: 10px; color: white;'>"
    )
    
    # 3. H4 címsor fehér színűre
    content = re.sub(
        r"<h4 style='margin-top:0;'>(.*?)</h4>",
        r"<h4 style='margin-top:0; color: white;'>\1</h4>",
        content
    )
    
    # 4. Komment frissítése
    content = content.replace(
        "# Legenda hozzáadása - ár alapú színkódolás",
        "# Legenda hozzáadása - ár alapú színkódolás (DARK MODE kompatibilis)"
    )
    
    # Fájl visszaírása
    with open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Dark mode patch alkalmazva a streamlit_app.py fájlban!")
    print("🌙 A térkép legenda most már dark mode-ban is jól látható")

if __name__ == "__main__":
    apply_dark_mode_patch()
