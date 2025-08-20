"""
Model Diagnosztika - Miért alulbecsül a modell?
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
        st.metric("Érvényes ár+terület", len(valid_data))
    
    with col2:
        avg_price = valid_data['target_ar'].mean()
        med_price = valid_data['target_ar'].median()
        st.metric("Átlag ár", f"{avg_price:.1f} M Ft")
        st.metric("Medián ár", f"{med_price:.1f} M Ft")
    
    with col3:
        avg_terulet = valid_data['terulet_szam'].mean()
        med_terulet = valid_data['terulet_szam'].median()
        st.metric("Átlag terület", f"{avg_terulet:.0f} m²")
        st.metric("Medián terület", f"{med_terulet:.0f} m²")
    
    with col4:
        avg_price_per_m2 = (valid_data['target_ar'] * 1_000_000 / valid_data['terulet_szam']).mean()
        st.metric("Átlag ár/m²", f"{avg_price_per_m2:,.0f} Ft/m²")
    
    # 1. PROBLÉMA: Outlier-ek elemzése
    st.subheader("🎯 Outlier problémák")
    
    fig_scatter = px.scatter(
        valid_data,
        x='terulet_szam',
        y='target_ar',
        title='Ár vs Terület - Outlier-ek azonosítása',
        labels={'terulet_szam': 'Terület (m²)', 'target_ar': 'Ár (M Ft)'}
    )
    
    # Tesztüzenet hozzáadása
    test_point = {'terulet_szam': 144, 'target_ar': 120}  # Elvárás
    model_pred = {'terulet_szam': 144, 'target_ar': 73.7}  # Modell becslés
    
    fig_scatter.add_trace(go.Scatter(
        x=[test_point['terulet_szam']], 
        y=[test_point['target_ar']],
        mode='markers',
        marker=dict(color='green', size=15, symbol='star'),
        name='Elvárás (144m², felújított)',
        showlegend=True
    ))
    
    fig_scatter.add_trace(go.Scatter(
        x=[model_pred['terulet_szam']], 
        y=[model_pred['target_ar']],
        mode='markers',
        marker=dict(color='red', size=15, symbol='x'),
        name='Modell becslés',
        showlegend=True
    ))
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # 2. PROBLÉMA: Ár/m² eloszlás
    st.subheader("💰 Ár/m² eloszlás problémák")
    
    valid_data['ar_per_m2'] = (valid_data['target_ar'] * 1_000_000) / valid_data['terulet_szam']
    
    fig_hist = px.histogram(
        valid_data,
        x='ar_per_m2',
        nbins=30,
        title='Ár/m² eloszlás - vannak extrém értékek?'
    )
    
    # Tesztpont ár/m²
    test_price_per_m2 = (120 * 1_000_000) / 144  # 833,333 Ft/m²
    model_price_per_m2 = (73.7 * 1_000_000) / 144  # 511,805 Ft/m²
    
    fig_hist.add_vline(x=test_price_per_m2, line_dash="dash", line_color="green", 
                       annotation_text=f"Elvárás: {test_price_per_m2:,.0f} Ft/m²")
    fig_hist.add_vline(x=model_price_per_m2, line_dash="dash", line_color="red",
                       annotation_text=f"Modell: {model_price_per_m2:,.0f} Ft/m²")
    
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # 3. PROBLÉMA: Feature engineering hiányosságok
    st.subheader("🛠️ Feature Engineering Problémák")
    
    # Állapot szerinti árak
    if 'ingatlan_allapota' in df.columns:
        allapot_stats = valid_data.groupby('ingatlan_allapota').agg({
            'target_ar': ['count', 'mean', 'median'],
            'ar_per_m2': ['mean', 'median']
        }).round(1)
        
        st.write("**Állapot szerinti árak:**")
        st.dataframe(allapot_stats)
    
    # 4. AJÁNLÁSOK
    st.subheader("🎯 Modell javítási javaslatok")
    
    st.markdown("""
    ### Azonosított problémák:
    
    1. **🔴 Outlier-ek túl nagy hatása**
       - Vannak extrém alacsony árak amik eltorzítják a modellt
       - Szükség van outlier szűrésre
    
    2. **🔴 Feature scaling problémák** 
       - A terület és ár közötti nem-lineáris kapcsolat
       - Logaritmikus transzformáció kellene
    
    3. **🔴 Állapot súlyozás alulértékelt**
       - "Felújított" kategória nagyobb prémiumot érdemel
       - Interakciós feature-k hiányoznak
    
    4. **🔴 Lokációs tényezők hiánya**
       - Erdliget prémium lokáció
       - Telekméret túl alacsony súlyozás
    
    ### Megoldási javaslatok:
    
    ✅ **Outlier szűrés**: < 50M Ft és > 300M Ft kizárása  
    ✅ **Log transzformáció**: ár és terület logaritmusa  
    ✅ **Feature interakciók**: terulet × állapot  
    ✅ **Súlyozott training**: újabb ingatlanok nagyobb súly  
    ✅ **Ensemble modellek**: RandomForest + GradientBoosting  
    """)
    
    return valid_data

if __name__ == "__main__":
    analyze_model_issues()
