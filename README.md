# 🏠 Real Estate Analyzer - Ingatlan Dashboard Projekt

## ⚠️ Jogi Nyilatkozat

\*\*Ez egy személyes, hobbi projekt, amely kizárólag saját ingatlankeresési célokat szolgál. A projekt nem kereskedelmi célú, nem szolgál semmilyen üzleti vagy kereskedelmi tevékenységet.

## 📊 Projekt Áttekintés

Ez egy átfogó ingatlanpiaci elemző projekt, amely web scraping, adatelemzés és interaktív vizualizáció kombinációjával mélyreható betekintést nyújt a magyar ingatlanpiacba. A projekt különböző Budapest környéki területekre fókuszál, mint Budaörs, Kőbánya-Újhegy, XI-XII kerület, stb.

### 📈 Fejlett Analitikus Dashboard

- **Interaktív Streamlit dashboard** professzionális vizualizációkkal
- **Semantikus szövegelemzés** ingatlanleírásokból
- **Ár-szöveg korreláció** elemzés
- **Átfogó statisztikai metrikák** (átlag, medián, szórás)
- **Befektetési elemzés** pontozási algoritmusokkal
- **Piaci szegmentáció** állapot, emelet, hirdető típus szerint

### 🤖 AI-Támogatott Funkciók

- **Automatikus GPS koordináta** hozzáadás Google Maps API-val
- **Intelligens szűrés** többféle kategória szerint
- **Családbarát pontszám** számítás
- **Modern funkciók** értékelése (smart tech, wellness, zöld energia)

## 🛠 Technikai Stack

- **Python 3.11+**
- **Web Scraping**: Chrome DevTools Protocol, Playwright
- **Adatelemzés**: Pandas, NumPy
- **Vizualizáció**: Streamlit, Plotly, Folium
- **GPS/Maps**: Google Maps Geocoding API
- **Szövegelemzés**: RegEx, szemantikus elemzés

## � Projekt Struktúra

```
real_agent_2/
├── 🕷️ Web Scraping & Adatgyűjtés
│   ├── ingatlan_list_details_scraper.py    # Fő scraper motor
│   └── scraper_timing_reset.py             # Timing reset utility
├── 🗺️ GPS & Koordináták
│   └── add_coordinates.py                  # GPS koordináta hozzáadó
├── 📊 Dashboard Generálás
│   ├── generate_dashboard.py               # Automata dashboard generátor
│   ├── streamlit_app.py                    # Fő dashboard template
│   └── dashboard_*.py                      # Lokáció-specifikus dashboardok
├── 📁 Adatfájlok
│   ├── ingatlan_lista_*.csv                # Lista scraping eredmények
│   ├── ingatlan_reszletes_*.csv             # Részletes adatok
│   └── *_koordinatak_*.csv                 # GPS koordinátákkal bővített
└── 📄 Konfigurációs Fájlok
    ├── .env                                # API kulcsok
    └── requirements.txt                    # Python függőségek
```

## 🔄 Teljes Workflow - Lépésről Lépésre

### 1️⃣ Adatgyűjtés (Web Scraping)

```bash
# Teljes pipeline egy lokációhoz (pl. Budaörs)
python ingatlan_list_details_scraper.py --location "URL" --max_listings 50 --generate_dashboard

# Paraméterek:
# --location: keresési lokáció (pl. "xi-kerulet", "budaors", "kobanyo-ujhegy")
# --max_listings: maximális hirdetések száma (alapértelmezett: 100)
# --generate_dashboard: automata dashboard generálás (opcionális)
```

**Mit csinál a scraper:**

- 🔍 Ingatlan.com keresés az adott lokációban
- 📋 Lista scraping (hirdetések URL-jeinek gyűjtése)
- 📄 Részletes scraping (minden hirdetés adatainak kinyerése)
- 🤖 AI-alapú szövegelemzés és pontozás
- 💾 CSV fájlok generálása (`ingatlan_lista_*.csv`, `ingatlan_reszletes_*.csv`)

### 2️⃣ GPS Koordináták Hozzáadása

```bash
# GPS koordináták hozzáadása Google Maps API-val
python add_coordinates.py ingatlan_reszletes_budaors_20250823_220240.csv

# Eredmény: ingatlan_reszletes_budaors_20250823_220240_koordinatak_20250823_183550.csv
```

**Funkciók:**

- 🗝️ Automatikus API kulcs betöltés `.env` fájlból
- 🌍 Batch geocoding (több cím egyszerre)
- 📍 100% pontosság magyar címeknél
- ⚡ Rate limiting és duplikáció elkerülés
- 🗺️ Térképes megjelenítéshez szükséges koordináták

### 3️⃣ Interaktív Dashboard Generálás

```bash
# Automata dashboard generálás CSV alapján
python generate_dashboard.py ingatlan_reszletes_budaors_20250823_220240_koordinatak_20250823_183550.csv

# Eredmény: dashboard_budaors.py
```

**Dashboard Generator Funkciók:**

- 🎯 Automatikus lokáció felismerés CSV névből
- 📋 CSV pattern generálás (mindig a legfrissebb fájlt használja)
- 🏗️ Streamlit dashboard létrehozása template alapján
- 🚀 Opcionális azonnali indítás

### 4️⃣ Dashboard Indítás & Használat

```bash
# Dashboard indítása
python -m streamlit run dashboard_budaors.py --server.port 8501

# Böngészőben: http://localhost:8501
```

## 🎛️ Dashboard Funkciók

### 📊 Interaktív Szűrők

- 💰 **Ár szűrő**: Min-max ár tartomány
- 📐 **Terület szűrő**: m² alapú szűrés
- 🏠 **Szobaszám szűrő**: 1-8+ szoba
- 🔧 **Állapot szűrő**: új építésű, felújított, jó, stb.
- ⭐ **Modern funkciók**: zöld energia, wellness, smart tech, premium design

### 📈 Vizualizációk & Elemzések

- 🗺️ **Interaktív térkép**: GPS koordinátákkal, ár-színkódolással
- 📊 **Scatter plot elemzések**: ár vs. terület/szobaszám/modern pont
- 📋 **Statisztikai összefoglalók**: átlag, medián, szórás
- 🏷️ **Kategorikus elemzések**: hirdető típus, emelet, erkély, parkolás, építési évtized
- 🔗 **Kattintható linkek**: közvetlen átirányítás ingatlan.com-ra

### 🎯 Speciális Funkciók

- 👨‍👩‍👧‍👦 **Családbarát pontszám**: 0-100 pontos skála nagyobb családoknak
- 🏆 **Modern nettó pont**: technológiai és prémium funkciók értékelése
- 💎 **Prémium lokáció**: városrészi kategorizáció és szorzók
- 🔍 **AI szövegelemzés**: pozitív/negatív tényezők automatikus felismerése

## � Telepítési Útmutató

### Előfeltételek

```bash
# Python 3.11+ telepítése
# Git telepítése
```

### 1. Repository Klónozás

```bash
git clone https://github.com/szolzol/real_estate_analyzer_01.git
cd real_estate_analyzer_01
```

### 2. Python Környezet Beállítás

```bash
# Virtuális környezet létrehozása (opcionális, de ajánlott)
python -m venv venv
venv\Scripts\activate  # Windows
# vagy
source venv/bin/activate  # Linux/Mac

# Függőségek telepítése
pip install -r requirements.txt
```

### 3. API Kulcsok Beállítása

```bash
# .env fájl létrehozása a projekt gyökerében
echo "GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here" > .env
```

**Google Maps API kulcs beszerzése:**

1. Menj a [Google Cloud Console](https://console.cloud.google.com/)
2. Hozz létre új projektet vagy válassz meglévőt
3. Engedélyezd a "Geocoding API"-t
4. Hozz létre API kulcsot
5. Másold be a `.env` fájlba

## 🎮 Használati Példák

### Példa 1: Budaörs Teljes Elemzés

```bash
# 1. Adatgyűjtés (50 hirdetés)
python ingatlan_list_details_scraper.py --location "URL" --max_listings 50

# 2. GPS koordináták (ha szükséges)
python add_coordinates.py ingatlan_reszletes_budaors_20250823_220240.csv

# 3. Dashboard generálás
python generate_dashboard.py ingatlan_reszletes_budaors_20250823_220240_koordinatak_20250823_221556.csv

# 4. Dashboard indítás
# (automatikusan felajánlja a generálás után)
```

### Példa 2: XI. Kerület Gyors Dashboard

```bash
# Egyetlen parancs (ha már van CSV)
python generate_dashboard.py ingatlan_reszletes_xi_ker_20250823_162945.csv
```

### Példa 3: Több Lokáció Összehasonlítás

```bash
# Budaörs dashboard
python -m streamlit run dashboard_budaors.py --server.port 8501

# XI. kerület dashboard (másik port)
python -m streamlit run dashboard_xi_ker.py --server.port 8502

# XII. kerület dashboard (harmadik port)
python -m streamlit run dashboard_xii_ker.py --server.port 8503
```

## � Adatstruktúra & Mezők

### Lista CSV Mezők (`ingatlan_lista_*.csv`)

- `id`, `cim`, `ar`, `terulet`, `szobak`, `link`

### Részletes CSV Mezők (`ingatlan_reszletes_*.csv`)

- **Alapadatok**: `id`, `cim`, `teljes_ar`, `terulet`, `szobak`, `epitesi_ev`, `szint`
- **Ingatlan tulajdonságok**: `ingatlan_allapota`, `futes`, `erkely`, `parkolas`
- **Hirdető információk**: `hirdeto_tipus`, `kepek_szama`, `telefon`
- **AI elemzés**: `netto_szoveg_pont`, `modern_netto_pont`, `csaladbarati_pontszam`
- **Modern funkciók**: `van_zold_energia`, `van_wellness_luxury`, `van_smart_tech`, `van_premium_design`
- **GPS koordináták**: `geo_latitude`, `geo_longitude`, `geo_address_from_api`

## 🔒 Biztonsági & Etikai Megfontolások

- ⏱️ **Rate limiting**: Kíméletes scraping sebességgel
- 🛡️ **Anti-detection**: Chrome CDP használat böngésző szimuláció helyett
- 📄 **robots.txt tisztelet**: Csak publikusan elérhető adatok
- 🏠 **Személyes használat**: Kizárólag saját ingatlankeresési célokra
- 💰 **Nem kereskedelmi**: Semmilyen üzleti tevékenységhez nem használt

## ⚙️ Konfigurációs Opciók

### Scraper Beállítások

- `MAX_LISTINGS`: Maximum hirdetések száma (alapértelmezett: 100)
- `DELAY_BETWEEN_REQUESTS`: Kérések közötti késleltetés (ms)
- `CHROME_DEBUG_PORT`: Chrome debug port (9222)

### Dashboard Testreszabás

- `FAMILY_FRIENDLY_SCORING`: Családbarát pontszámítás súlyok
- `MODERN_FEATURES_WEIGHTS`: Modern funkciók értékelési súlyok
- `MAP_DEFAULT_ZOOM`: Térkép alapértelmezett nagyítás

## 🛠 Hibaelhárítás

### Gyakori Problémák

**1. Chrome kapcsolat hiba**

```bash
# Chrome indítása debug módban
chrome.exe --remote-debugging-port=9222
```

**2. Google Maps API hiba**

```bash
# .env fájl ellenőrzése
cat .env
# API kulcs frissítése
```

**3. CSV betöltési hiba**

```bash
# Fájlok ellenőrzése
ls ingatlan_*.csv
# Encoding ellenőrzés (UTF-8 szükséges)
```

**4. Streamlit port foglaltság**

```bash
# Másik port használata
python -m streamlit run dashboard_budaors.py --server.port 8502
```

## 📈 Jövőbeli Fejlesztések

- 🔔 **Automatikus értesítések** új hirdetésekről
- � **Email riportok** piaci változásokról
- 🤖 **ML árpredikció** modellek
- 📱 **Mobil optimalizálás**
- 🗂️ **Adatbázis integráció** (SQLite/PostgreSQL)
- 🔄 **Automatikus frissítések** időzítve

## 🤝 Közreműködés

Ez egy személyes projekt, de javaslatokat, bug reportokat szívesen fogadok:

1. Fork-old a repository-t
2. Hozz létre feature branch-et (`git checkout -b feature/new-feature`)
3. Commitold a változásokat (`git commit -am 'Add new feature'`)
4. Push-old a branch-et (`git push origin feature/new-feature`)
5. Hozz létre Pull Request-et

## 📝 Licenc

Ez egy személyes projekt, a kód csak a létrehozó engedélyével használható. Kereskedelmi célokra semmilyen esetben sem használható!

## 📞 Kapcsolat

**Projekt Tulajdonos**: szolzol  
**GitHub**: [https://github.com/szolzol/real_estate_analyzer_01](https://github.com/szolzol/real_estate_analyzer_01)
