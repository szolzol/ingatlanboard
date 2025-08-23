"""
SCRAPER VÁRAKOZÁSI IDŐK VISSZAÁLLÍTÁSA
=====================================
Dátum: 2025-08-23
Indok: Captcha védelem aktiválódott a gyorsított verzióban

VISSZAÁLLÍTOTT VÁRAKOZÁSI IDŐK:
==============================

1. Lista scraping:
   - Oldal betöltés után: 2s → 5s (visszaállítva)
   - Hiba esetén retry: 1.5s → 3s (visszaállítva)

2. Részletes scraping warmup:
   - Session warmup: 2s → 5s (visszaállítva)

3. Részletes scraping főciklus:
   - Alap várakozás (1-5. kérés): 1.0-2.0s → 2.5-4.5s
   - Közepes várakozás (6-10. kérés): 1.5-2.5s → 4.0-6.5s
   - Lassú várakozás (11+ kérés): 2.0-3.0s → 5.5-8.0s
   - Extra szünet (minden 5. kérés): +1.0-2.0s → +2.0-4.0s

4. Egyszeri kérések:
   - Részletes oldal betöltés: 1.0-1.5s → 2.5-4.0s

CAPTCHA VÉDELEM:
===============
- Alap várakozás: 2.5-4.5 másodperc kérések között
- Fokozott védelem 5 kérés után: 4.0-6.5 másodperc
- Maximális védelem 10 kérés után: 5.5-8.0 másodperc
- Extra szünetek minden 5. kérésnél: +2.0-4.0 másodperc

TELJESÍTMÉNY HATÁS:
==================
- Várható lassulás: ~60-70% (100 ingatlan ~25 perc helyett ~45 perc)
- Captcha kockázat: Minimális
- Bot detektálás esélye: Alacsony

EREDMÉNY:
========
A scraper most ismét a biztonságos, captcha-ellenálló verzióban működik.
A korábbi optimalizációk (DOM szelektorok, URL tisztítás, logging) megmaradtak,
csak a várakozási idők lettek visszaállítva a biztonságos szintre.
"""

print("✅ Scraper várakozási idők visszaállítva biztonságos szintre")
print("📊 Várható teljesítmény: ~60-70% lassabb, de captcha-mentes")
print("🔒 Bot védelem: Alacsony kockázat")
