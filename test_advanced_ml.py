"""
Teszt a javított optimalizált modellhez
144m², 850m² telek, felújított, 5 szobás, 22 éves, parkolós ház
"""

import pandas as pd
import numpy as np
from optimized_ml_model import OptimalizaltIngatlanModell

# Modell inicializálása
model = OptimalizaltIngatlanModell()

print("🏠 Teszt ház paraméterei:")
print("- Terület: 144 m²")
print("- Telekterület: 850 m²") 
print("- Állapot: felújított")
print("- Szobák: 5")
print("- Kor: 22 év")
print("- Parkolás: igen")
print()

try:
    # Adatok előkészítése
    print("📊 Adatok előkészítése...")
    df = model.adatok_elokeszitese()
    print(f"✅ {len(df)} adat sikeresen feldolgozva")
    print()
    
    # Modell tanítása
    print("🤖 Modell tanítása...")
    model.modell_tanitas(df)
    print(f"🏆 Legjobb modell: {model.best_model_name}")
    print()
    
    # Tesztadatok
    user_terulet = 144
    user_szobak = 5
    user_allapot = 'felújított'
    user_haz_kora = 22
    user_telekterulet = 850
    user_parkolas = True
    
    # Állapot encoding (javított)
    allapot_map = {
        'bontásra váró': 0, 
        'felújítandó': 2,      
        'közepes állapotú': 4,  
        'jó állapotú': 6,      
        'felújított': 9,       # NAGY PRÉMIUM
        'új építésű': 10,      
        'újszerű': 9
    }
    
    # TELJES feature vektor összeállítása
    user_features = {
        # Alapváltozók
        'terulet': user_terulet,
        'terulet_log': np.log1p(user_terulet),
        'szobak_szam': user_szobak,
        'allapot_szam': allapot_map[user_allapot],
        'haz_kora': user_haz_kora,
        'telekterulet_szam': user_telekterulet,
        'van_parkolas': int(user_parkolas),
        
        # Származtatott változók
        'kor_kategoria': 4 if user_haz_kora < 10 else (3 if user_haz_kora < 25 else (2 if user_haz_kora < 50 else 1)),
        'telek_log': np.log1p(user_telekterulet),
        'nagy_telek': int(user_telekterulet > 600),
        'terulet_x_allapot': user_terulet * allapot_map[user_allapot],
        'm2_per_szoba': user_terulet / user_szobak
    }
    
    print("🔧 Generált feature-k:")
    for feature, value in user_features.items():
        print(f"  {feature}: {value:.2f}")
    print()
    
    # Előrejelzés
    user_vector = np.array([user_features[f] for f in model.feature_names]).reshape(1, -1)
    predicted_price_base = model.best_model.predict(user_vector)[0]
    
    print(f"🎯 Alap modell becslés: {predicted_price_base:.1f} M Ft")
    
    # Prémium korrekciók
    predicted_price = predicted_price_base
    
    if user_allapot == 'felújított' and predicted_price < 80:
        predicted_price *= 1.15
        print(f"🔧 Felújítási prémium (+15%): {predicted_price:.1f} M Ft")
    
    if user_telekterulet > 800 and predicted_price < 100:
        predicted_price *= 1.08
        print(f"🏡 Nagy telek prémium (+8%): {predicted_price:.1f} M Ft")
    
    # Erdliget lokációs prémium
    predicted_price *= 1.12
    print(f"🏘️ Erdliget prémium (+12%): {predicted_price:.1f} M Ft")
    
    print()
    print("=" * 50)
    print(f"💰 VÉGSŐ BECSLÉS: {predicted_price:.1f} M Ft")
    print(f"📏 Ár/m²: {(predicted_price * 1_000_000 / user_terulet):,.0f} Ft/m²")
    print("=" * 50)
    
    # Összehasonlítás adatsettel
    avg_price = df['target_ar'].mean()
    difference = ((predicted_price - avg_price) / avg_price) * 100
    print(f"📊 Eltérés dataset átlagtól ({avg_price:.1f}M Ft): {difference:+.1f}%")
    
    # Reális tartomány értékelése
    if 120 <= predicted_price <= 140:
        print("✅ REÁLIS TARTOMÁNYBAN! (120-140M Ft)")
    elif predicted_price < 120:
        print("⚠️ Még mindig alacsony a reális tartományhoz képest")
    else:
        print("        print("📈 Magasabb mint a reális becslés")

except Exception as e:
    print(f"❌ Hiba: {e}")
    import traceback
    traceback.print_exc()")

st.title("🤖 Szofisztikált ML Modell Teszt")

try:
    # Advanced ML modell importálása
    from advanced_ml_model import advanced_ml_dashboard, SzofisztikaltIngatlanModell
    st.success("✅ Advanced ML modell sikeresen importálva!")
    
    # Session state inicializálás a teszt környezethez
    if 'dashboard_active' not in st.session_state:
        st.session_state.dashboard_active = True
    
    # Közvetlenül futtatjuk a dashboard-ot
    st.write("---")
    try:
        advanced_ml_dashboard()
    except Exception as e:
        st.error(f"Hiba a dashboard futtatásakor: {e}")
        st.write("**Részletes hibaüzenet:**")
        st.code(str(e))
        
        # Debug információk
        st.write("**Debug információk:**")
        import traceback
        st.code(traceback.format_exc())
            
except ImportError as e:
    st.error(f"❌ Nem sikerült importálni az advanced ML modellt: {e}")
    
    st.write("**Hiányzó csomagok telepítése:**")
    st.code("""
    pip install scikit-learn>=1.3.0
    pip install matplotlib>=3.7.0
    pip install seaborn>=0.12.0
    pip install plotly>=5.15.0
    """)
    
    # Részletes hibaüzenet
    st.write("**Részletes import hiba:**")
    import traceback
    st.code(traceback.format_exc())

except Exception as e:
    st.error(f"❌ Egyéb hiba: {e}")
    import traceback
    st.code(traceback.format_exc())
