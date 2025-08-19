# 🚀 HIBRID SCRAPING ÚTMUTATÓ

## PROBLÉMA

A Cloudflare folyamatosan újratölti a security challenge-et, még a kézi megoldás után is.

## MEGOLDÁS: HIBRID MEGKÖZELÍTÉS

Normál Chrome böngészőt használunk, amit a Python script átvesz.

## 📋 LÉPÉSRŐL LÉPÉSRE ÚTMUTATÓ

### 1. CHROME BEZÁRÁSA

```
- Zárd be az összes Chrome ablakot
- Ellenőrizd a Task Manager-ben, hogy nincs chrome.exe folyamat
```

### 2. DEBUG CHROME INDÍTÁSA

```
- Futtasd: start_chrome_debug.bat
- VAGY kézzel:
  chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/temp/chrome-debug
```

### 3. MANUÁLIS NAVIGÁCIÓ

```
- Navigálj el: https://ingatlan.com/lista/elado+haz+xi-ker
- Old meg a Cloudflare challenge-et normál módon
- Várj, amíg megjelennek a hirdetések
- NE ZÁRD BE A CHROME-OT!
```

### 4. PYTHON SCRIPT FUTTATÁSA

```
cd f:\CODE\real_agent_2
.\ingatlan_agent_env\Scripts\activate
python scrape_ads_hybrid.py
```

## 🎯 ELŐNYÖK

✅ **Nincs bot detektálás** - Normál Chrome böngészőt használ
✅ **Cloudflare elkerülése** - Te oldod meg kézzel egyszer
✅ **Stabil kapcsolat** - Már futó böngészőt vesz át
✅ **Gyors működés** - Nincs új session indítási idő

## ⚠️ FIGYELEM

- A Chrome-ot debug módban kell indítani
- Ne zárd be a böngészőt a scraping alatt
- Az első Cloudflare challenge-et kézzel kell megoldani
- Utána a script automatikusan dolgozik

## 🔧 HIBAELHÁRÍTÁS

### "Nem sikerült kapcsolódni a Chrome böngészőhöz"

```
1. Ellenőrizd, hogy a Chrome debug módban fut
2. Nyisd meg: http://localhost:9222
3. Ha nem töltődik be, indítsd újra a start_chrome_debug.bat-ot
```

### "Nincs aktív Chrome context"

```
1. Nyiss legalább egy tab-ot a Chrome-ban
2. Navigálj el az ingatlan.com-ra
3. Futtasd újra a scriptet
```

### "Cloudflare challenge még mindig aktív"

```
1. Oldd meg kézzel a challenge-et a Chrome-ban
2. Várj, amíg teljesen betöltődnek a hirdetések
3. Csak utána nyomj ENTER-t a scriptben
```

## 📊 VÁRHATÓ EREDMÉNY

- 1-2 oldal sikeres feldolgozása
- 20-40 hirdetés kinyerése
- CSV fájl generálása
- Stabil működés Cloudflare ellenére
