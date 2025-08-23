#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

# Tesztelj a budaörsi 10 szobás ingatlant
test_url = "https://ingatlan.com/34931913"

print(f"🧪 Szobaszám kinyerés tesztelése...")
print(f"Teszt URL: {test_url}")

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(test_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print(f"Status code: {response.status_code}")
    
    # Keressük a listing-property diveket
    property_divs = soup.find_all('div', class_='listing-property')
    print(f"Találtunk {len(property_divs)} db listing-property divet")
    
    szobaszam = None
    for i, div in enumerate(property_divs):
        spans = div.find_all('span')
        print(f"  Div {i+1}: {len(spans)} span")
        
        if len(spans) >= 2:
            label_text = spans[0].get_text(strip=True)
            value_text = spans[1].get_text(strip=True)
            print(f"    Label: '{label_text}' -> Value: '{value_text}'")
            
            if 'Szobák' in label_text:
                szobaszam = value_text
                print(f"    ✅ SZOBASZÁM TALÁLAT: {szobaszam}")
                break
    
    if szobaszam:
        print(f"\n🎯 Végeredmény: {szobaszam} szoba")
    else:
        print(f"\n❌ Szobaszám nem található")
        
        # Alternatív keresés - minden span-t megvizsgálunk
        print("\n🔍 Alternatív keresés - összes span:")
        all_spans = soup.find_all('span')
        for i, span in enumerate(all_spans):
            text = span.get_text(strip=True)
            if 'Szobák' in text:
                print(f"  Span {i}: '{text}'")
                # Következő span keresése
                if i + 1 < len(all_spans):
                    next_span = all_spans[i + 1]
                    next_text = next_span.get_text(strip=True)
                    print(f"    Következő span: '{next_text}'")
                    if next_text.strip().isdigit() or '+' in next_text or 'fél' in next_text.lower():
                        print(f"    ✅ SZOBASZÁM ALTERNATÍV: {next_text}")
                        szobaszam = next_text
                        break

    print(f"\n📊 HTML struktúra minta:")
    # Keressük a konkrét struktúrát
    for div in property_divs[:3]:  # Első 3 div
        print(f"  <div class='{' '.join(div.get('class', []))}''>")
        for span in div.find_all('span')[:2]:  # Első 2 span
            print(f"    <span class='{' '.join(span.get('class', []))}''>{span.get_text(strip=True)}</span>")
        print(f"  </div>")

except Exception as e:
    print(f"❌ Hiba: {e}")
