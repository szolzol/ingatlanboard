"""
Modell Diagnosztika - Miért alulbecsül a modell?
==============================================
Elemezzük ki miért jön ki 66.7M Ft helyett 120-140M Ft
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def diagnose_model_problems():
    """
    Diagnosztikai elemzés a modell alulbecslésének okairól
    """
    st.title("🔍 Modell Diagnosztika - Alulbecslés Elemzése")
    
    # Adatok betöltése
    df = pd.read_csv("ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv", encoding='utf-8-sig')
    
    # Célváltozó parse
    def parse_million_ft(text):
        if pd.isna(text):
            return None
        text = str(text).replace(',', '.')
        import re
        match = re.search(r'(\d+(?:\.\d+)?)\s*M', text)
        return float(match.group(1)) if match else None
    
    df['target_ar'] = df['teljes_ar'].apply(parse_million_ft)
    
    # Terület parse
    def parse_terulet(text):
        if pd.isna(text):
            return None
        import re
        match = re.search(r'(\d+)', str(text))
        return int(match.group(1)) if match else None
    
    df['terulet_szam'] = df['terulet'].apply(parse_terulet)
    
    st.subheader("📊 1. Adatok eloszlása")
    
    # Tiszta adatok
    clean_df = df[df['target_ar'].notna() & df['terulet_szam'].notna()].copy()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Összes adat", len(df))
        st.metric("Tiszta ár adat", len(clean_df))
    
    with col2:
        if len(clean_df) > 0:
            st.metric("Min ár", f"{clean_df['target_ar'].min():.1f} M Ft")
            st.metric("Max ár", f"{clean_df['target_ar'].max():.1f} M Ft")
    
    with col3:
        if len(clean_df) > 0:
            st.metric("Átlag ár", f"{clean_df['target_ar'].mean():.1f} M Ft")
            st.metric("Medián ár", f"{clean_df['target_ar'].median():.1f} M Ft")
    
    # Ár eloszlás
    if len(clean_df) > 0:
        fig_hist = px.histogram(clean_df, x='target_ar', nbins=20, title="Árak eloszlása")
        fig_hist.add_vline(x=120, line_dash="dash", line_color="red", annotation_text="Tesztelt ház: 120M Ft")
        fig_hist.add_vline(x=66.7, line_dash="dash", line_color="orange", annotation_text="Modell becslés: 66.7M Ft")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Terület vs ár
    st.subheader("📏 2. Terület vs Ár elemzés")
    
    if len(clean_df) > 5:
        fig_scatter = px.scatter(clean_df, x='terulet_szam', y='target_ar', 
                                title="Terület vs Ár", opacity=0.7)
        
        # Tesztelt ház kiemelése
        fig_scatter.add_scatter(x=[144], y=[120], mode='markers', 
                               marker=dict(color='red', size=15), 
                               name="Tesztelt ház (144m², 120M Ft)")
        
        fig_scatter.add_scatter(x=[144], y=[66.7], mode='markers', 
                               marker=dict(color='orange', size=15), 
                               name="Modell becslés (144m², 66.7M Ft)")
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Trend vonal
        if len(clean_df) > 10:
            # Egyszerű lineáris regresszió
            from sklearn.linear_model import LinearRegression
            X = clean_df[['terulet_szam']].dropna()
            y = clean_df['target_ar'][X.index]
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Becslés a trendvonalra
            trend_pred = model.predict([[144]])[0]
            st.info(f"📈 **Egyszerű trend alapján 144m²-re**: {trend_pred:.1f} M Ft")
            
            # R² 
            r2 = model.score(X, y)
            st.info(f"📊 **Terület-ár korreláció R²**: {r2:.3f}")
    
    # Állapot elemzés
    st.subheader("🏠 3. Állapot szerinti árak")
    
    if 'ingatlan_allapota' in df.columns:
        allapot_df = clean_df[clean_df['ingatlan_allapota'].notna()].copy()
        
        if len(allapot_df) > 0:
            allapot_summary = allapot_df.groupby('ingatlan_allapota').agg({
                'target_ar': ['count', 'mean', 'median', 'min', 'max']
            }).round(1)
            
            allapot_summary.columns = ['Darab', 'Átlag', 'Medián', 'Min', 'Max']
            allapot_summary = allapot_summary.reset_index()
            
            st.dataframe(allapot_summary, use_container_width=True)
            
            # Kiemelés a felújított házakra
            felujitott = allapot_df[allapot_df['ingatlan_allapota'].str.contains('felújított', case=False, na=False)]
            if len(felujitott) > 0:
                st.success(f"✅ **Felújított házak átlaga**: {felujitott['target_ar'].mean():.1f} M Ft ({len(felujitott)} db)")
    
    # Potenciális problémák azonosítása
    st.subheader("⚠️ 4. Potenciális problémák")
    
    problems = []
    
    # 1. Kis adatmennyiség
    if len(clean_df) < 50:
        problems.append(f"🔸 **Kis adatmennyiség**: Csak {len(clean_df)} tiszta adat → modell instabil")
    
    # 2. Outlier elemzés
    if len(clean_df) > 10:
        Q1 = clean_df['target_ar'].quantile(0.25)
        Q3 = clean_df['target_ar'].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR
        
        if 120 > upper_bound:
            problems.append(f"🔸 **120M Ft outlier**: Túl magas az adatsethez képest (felső határ: {upper_bound:.1f}M)")
    
    # 3. Terület-alapú becslés
    if len(clean_df) > 5:
        avg_price_per_m2 = (clean_df['target_ar'] * 1_000_000 / clean_df['terulet_szam']).mean()
        expected_price = (avg_price_per_m2 * 144) / 1_000_000
        problems.append(f"🔸 **Átlag m²-ár alapú becslés**: {expected_price:.1f}M Ft (átlag: {avg_price_per_m2:,.0f} Ft/m²)")
    
    # 4. Modell típus
    problems.append("🔸 **Modell limitáció**: Az ML modell túl konzervatív, nem veszi figyelembe a prémium faktorokat")
    
    # 5. Feature hiányosságok
    problems.append("🔸 **Hiányzó faktorok**: lokáció, környék prémium, renovation minősége, modern felszereltség stb.")
    
    for problem in problems:
        st.warning(problem)
    
    # Megoldási javaslatok
    st.subheader("💡 5. Megoldási javaslatok")
    
    solutions = [
        "🎯 **Modell rekalibrálás**: Magasabb base price és prémium faktorok",
        "📈 **Trend korrekcio**: Aktuális piaci trend figyelembe vétele (+15-20%)",
        "🏘️ **Lokációs prémium**: Erdliget prémium településrész (+10-15%)",
        "🔧 **Felújítási bonus**: Felújított házakra extra szorzó (+20-30%)",
        "📊 **Ensemble súlyozás**: Több modell kombinálása konzervatív helyett",
        "🎚️ **Price floor**: Minimum ár/m² garancia prémium ingatlanokra"
    ]
    
    for solution in solutions:
        st.success(solution)
    
    # Gyors korrekciós kalkulátor
    st.subheader("⚡ 6. Korrekciós Kalkulátor")
    
    if len(clean_df) > 5:
        base_prediction = 66.7  # Jelenlegi becslés
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Korrekciós faktorok:**")
            market_trend = st.slider("Piaci trend (%)", 0, 30, 15)
            location_premium = st.slider("Erdliget prémium (%)", 0, 20, 10)
            renovation_bonus = st.slider("Felújítási bonus (%)", 0, 40, 25)
            size_premium = st.slider("Méret prémium 144m² (%)", 0, 15, 8)
        
        with col2:
            # Korrigált becslés
            corrected_price = base_prediction
            corrected_price *= (1 + market_trend/100)
            corrected_price *= (1 + location_premium/100)
            corrected_price *= (1 + renovation_bonus/100)
            corrected_price *= (1 + size_premium/100)
            
            st.metric("**Korrigált becslés**", f"{corrected_price:.1f} M Ft")
            
            difference = corrected_price - base_prediction
            st.metric("**Korrекció**", f"+{difference:.1f} M Ft ({((corrected_price/base_prediction-1)*100):.0f}%)")
            
            # Reális tartomány
            if corrected_price >= 120 and corrected_price <= 140:
                st.success("✅ Reális tartományban!")
            elif corrected_price < 120:
                st.warning("⚠️ Még mindig alacsony")
            else:
                st.error("❌ Túl magas")

if __name__ == "__main__":
    diagnose_model_problems()
