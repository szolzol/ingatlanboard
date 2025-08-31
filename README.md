# Ingatlan Elemző Landing Page

Ez a landing page bemutatja az ingatlan elemző alkalmazást és linkeket tartalmaz a különböző Streamlit dashboardokhoz.

## 📁 Fájl Struktúra

```
landing-page/
├── index.html          # Fő HTML fájl
├── css/
│   └── styles.css      # Stílusok (modern, responsive design)
├── js/
│   └── script.js       # JavaScript funkciók (animációk, smooth scrolling)
├── images/             # Képek helye (jelenleg Unsplash képeket használunk)
└── README.md           # Ez a dokumentáció
```

## 🎨 Design Jellemzők

- **Modern ingatlanos téma**: Sötét háttér, elegáns színek
- **Responsive design**: Mobilbarát, minden eszközön jól néz ki
- **Animációk**: Smooth scrolling, fade-in effektusok
- **Interaktív elemek**: Hover effektusok, kártyák

## 🚀 Használat

1. **Helyi futtatás**: Nyisd meg az `index.html` fájlt bármely böngészőben
2. **Web hosting**: Töltsd fel a teljes `landing-page` mappát bármely statikus hosting szolgáltatásra
3. **GitHub Pages**: A repository `landing-page` mappáját használhatod GitHub Pages-hez

## 📊 Tartalom

### Hero Section
- Fő cím és leírás
- Call-to-action gomb a dashboardokhoz

### Bemutatás
- Az alkalmazás rövid bemutatása
- Családbarát elemzések említése

### Dashboard Linkek
Aktuális dashboardok:
- Budaörs
- XII. Kerület
- Érd-Érdliget-Diósd
- XI. Kerület
- XXII. Kerület
- Törökbálint-Tükörhegy

### Funkciók
- Interaktív térképek
- Valós idejű elemzések
- Családbarát pontozás
- Intelligens szűrők
- Zöld energia elemzés
- Iskola közelség

## 🔧 Testreszabás

### Új Dashboard Hozzáadása
1. Nyisd meg az `index.html` fájlt
2. Keresd meg a `dashboard-grid` div-et
3. Másold le egy meglévő `dashboard-card` div-et
4. Módosítsd a képet, címet, leírást és linket

### Színek Módosítása
1. Nyisd meg a `css/styles.css` fájlt
2. Keresd meg a `:root` változót (ha hozzáadod)
3. Vagy keresd meg a színeket és módosítsd őket

### Képek Csere
- Cseréld le az Unsplash URL-eket saját képekre
- Helyezd el a képeket az `images/` mappában
- Frissítsd az `src` attribútumokat

## 📱 Responsive Design

- **Desktop**: >1024px - teljes layout
- **Tablet**: 768-1024px - adaptív grid
- **Mobil**: <768px - stacked layout, hamburger menü lehetőség

## 🌐 Hosting Ajánlások

- **GitHub Pages**: Ingyenes, egyszerű
- **Netlify**: Automatikus deploy, HTTPS
- **Vercel**: Gyors, modern
- **Firebase Hosting**: Google szolgáltatás

## 📞 Kapcsolat

Fejlesztő: Zoltán Szőllősi
Email: zoltan.szoleczki@cemsmail.org
GitHub: https://github.com/szolzol/real_estate_analyzer_01
