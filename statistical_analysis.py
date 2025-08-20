"""
Statisztikai Szignifikancia Elemzés
===================================
Azonosítsuk azokat a változókat, amiknek valóban van magyarázó erejük az ingatlan árára.
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

def load_and_prepare_data():
    """Adatok betöltése és előkészítése"""
    df = pd.read_csv("ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv", encoding='utf-8-sig')
    
    # Célváltozó: teljes_ar feldolgozása
    def parse_million_ft(text):
        if pd.isna(text):
            return None
        text = str(text).replace(',', '.')
        import re
        match = re.search(r'(\d+(?:\.\d+)?)\s*M', text)
        return float(match.group(1)) if match else None
    
    df['target_ar'] = df['teljes_ar'].apply(parse_million_ft)
    
    # Terület feldolgozása
    def parse_terulet(text):
        if pd.isna(text):
            return None
        import re
        match = re.search(r'(\d+)', str(text))
        return int(match.group(1)) if match else None
    
    df['terulet_szam'] = df['terulet'].apply(parse_terulet)
    
    # Telekterület feldolgozása
    def parse_telekterulet(text):
        if pd.isna(text):
            return None
        import re
        match = re.search(r'(\d+)', str(text))
        return int(match.group(1)) if match else None
    
    df['telekterulet_szam'] = df['telekterulet'].apply(parse_telekterulet)
    
    # Szobák száma feldolgozása
    def parse_szobak(text):
        if pd.isna(text):
            return None
        text = str(text).lower()
        if 'fél' in text:
            # pl. "4 + 1 fél" -> 4.5
            import re
            nums = re.findall(r'\d+', text)
            if len(nums) >= 2:
                return int(nums[0]) + 0.5
        else:
            import re
            match = re.search(r'(\d+)', text)
            return float(match.group(1)) if match else None
        return None
    
    df['szobak_szam'] = df['szobak'].apply(parse_szobak)
    
    # Építési év feldolgozása
    def parse_epitesi_ev(text):
        if pd.isna(text):
            return None
        text = str(text)
        import re
        # Keressük meg az évszámokat
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if years:
            # Ha intervallumos (pl. "1981 és 2000 között"), vegyük a középértéket
            if len(years) >= 2:
                return (int(years[0]) + int(years[1])) / 2
            else:
                return int(years[0])
        return None
    
    df['epitesi_ev'] = df['epitesi_ev'].apply(parse_epitesi_ev)
    df['haz_kora'] = 2025 - df['epitesi_ev']
    
    # Állapot encoding
    allapot_map = {
        'bontásra váró': 0,
        'felújítandó': 1, 
        'közepes állapotú': 2,
        'jó állapotú': 3,
        'felújított': 4,
        'új építésű': 5
    }
    df['allapot_szam'] = df['allapot'].map(allapot_map)
    
    # Képek száma
    df['kepek_szama'] = pd.to_numeric(df['kepek_szama'], errors='coerce')
    
    # Hirdető típus
    df['hirdeto_maganszemely'] = (df['hirdeto_tipus'] == 'maganszemely').astype(int)
    
    # Bináris változók
    df['van_parkolas'] = df['parkolas'].notna().astype(int)
    df['van_erkely'] = df['erkely'].notna().astype(int)
    df['van_kert'] = df['kert'].notna().astype(int)
    df['van_pince'] = df['pince'].notna().astype(int)
    df['van_tetoter'] = df['tetoter'].notna().astype(int)
    df['van_klima'] = df['legkondicionalas'].notna().astype(int)
    
    # Csak azokat a sorokat tartsuk meg, ahol van ár
    df = df[df['target_ar'].notna()].copy()
    
    return df

def statistical_significance_analysis(df):
    """Statisztikai szignifikancia elemzés"""
    
    # Potenciális magyarázó változók
    potential_features = [
        'terulet_szam',
        'telekterulet_szam', 
        'szobak_szam',
        'epitesi_ev',
        'haz_kora',
        'allapot_szam',
        'kepek_szama',
        'hirdeto_maganszemely',
        'van_parkolas',
        'van_erkely',
        'van_kert',
        'van_pince',
        'van_tetoter',
        'van_klima'
    ]
    
    target = 'target_ar'
    
    results = []
    
    for feature in potential_features:
        if feature not in df.columns:
            continue
            
        # Non-null értékek
        valid_mask = df[feature].notna() & df[target].notna()
        x = df.loc[valid_mask, feature]
        y = df.loc[valid_mask, target]
        
        if len(x) < 10:  # Minimum adatmennyiség
            continue
        
        # Pearson korreláció
        pearson_corr, pearson_p = pearsonr(x, y)
        
        # Spearman korreláció (rangkorreláció)
        spearman_corr, spearman_p = spearmanr(x, y)
        
        # F-teszt a lineáris regresszióhoz
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score
        
        X = x.values.reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        # F-statisztika
        n = len(x)
        f_stat = (r2 / (1 - r2)) * (n - 2)
        f_p_value = stats.f.sf(f_stat, 1, n-2)
        
        results.append({
            'feature': feature,
            'n_samples': len(x),
            'pearson_r': pearson_corr,
            'pearson_p': pearson_p,
            'spearman_r': spearman_corr,
            'spearman_p': spearman_p,
            'r_squared': r2,
            'f_statistic': f_stat,
            'f_p_value': f_p_value,
            'significant_05': f_p_value < 0.05,
            'significant_01': f_p_value < 0.01,
            'effect_size': abs(pearson_corr)
        })
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('f_p_value')
    
    return results_df

def create_significance_dashboard():
    """Streamlit dashboard a szignifikancia elemzéshez"""
    
    st.title("🔬 Statisztikai Szignifikancia Elemzés")
    st.subheader("Mely változók befolyásolják valóban az ingatlan árát?")
    
    # Adatok betöltése
    with st.spinner("Adatok betöltése..."):
        df = load_and_prepare_data()
        results_df = statistical_significance_analysis(df)
    
    st.success(f"✅ {len(df)} ingatlan elemezve, {len(results_df)} változó tesztelve")
    
    # Szignifikancia táblázat
    st.subheader("📊 Változók statisztikai szignifikanciája")
    
    # Színkódolás a p-értékek alapján
    def color_p_values(val):
        if val < 0.001:
            return 'background-color: #d4edda; font-weight: bold'  # Erősen szignifikáns (zöld)
        elif val < 0.01:
            return 'background-color: #fff3cd; font-weight: bold'  # Szignifikáns (sárga)
        elif val < 0.05:
            return 'background-color: #f8d7da'  # Gyengén szignifikáns (rózsaszín)
        else:
            return 'background-color: #f8f9fa; color: #6c757d'  # Nem szignifikáns (szürke)
    
    # Formázott táblázat
    styled_table = results_df[['feature', 'n_samples', 'pearson_r', 'pearson_p', 
                              'r_squared', 'f_p_value', 'significant_05']].copy()
    
    styled_table.columns = ['Változó', 'Minták száma', 'Pearson r', 'Pearson p-érték', 
                           'R²', 'F-teszt p-érték', 'Szignifikáns (p<0.05)']
    
    # Formázás
    styled_table['Pearson r'] = styled_table['Pearson r'].round(3)
    styled_table['R²'] = styled_table['R²'].round(3)
    styled_table['Pearson p-érték'] = styled_table['Pearson p-érték'].apply(lambda x: f"{x:.2e}" if x < 0.001 else f"{x:.3f}")
    styled_table['F-teszt p-érték'] = styled_table['F-teszt p-érték'].apply(lambda x: f"{x:.2e}" if x < 0.001 else f"{x:.3f}")
    
    st.dataframe(
        styled_table.style.applymap(color_p_values, subset=['F-teszt p-érték']),
        use_container_width=True
    )
    
    # Szignifikáns változók kiemelése
    significant_vars = results_df[results_df['significant_05']]['feature'].tolist()
    highly_significant = results_df[results_df['significant_01']]['feature'].tolist()
    
    st.subheader("🎯 Ajánlott változók")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("**Erősen szignifikáns (p < 0.01):**")
        for var in highly_significant:
            row = results_df[results_df['feature'] == var].iloc[0]
            st.write(f"• **{var}** (r²={row['r_squared']:.3f}, p={row['f_p_value']:.2e})")
    
    with col2:
        st.warning("**Gyengén szignifikáns (0.01 ≤ p < 0.05):**")
        weak_significant = [v for v in significant_vars if v not in highly_significant]
        for var in weak_significant:
            row = results_df[results_df['feature'] == var].iloc[0]
            st.write(f"• **{var}** (r²={row['r_squared']:.3f}, p={row['f_p_value']:.3f})")
    
    # Nem szignifikáns változók
    non_significant = results_df[~results_df['significant_05']]['feature'].tolist()
    if non_significant:
        st.error("**Nem szignifikáns (p ≥ 0.05) - elhagyható:**")
        for var in non_significant:
            row = results_df[results_df['feature'] == var].iloc[0]
            st.write(f"• **{var}** (r²={row['r_squared']:.3f}, p={row['f_p_value']:.3f})")
    
    # Vizualizáció
    st.subheader("📈 Korreláció vizualizáció")
    
    # P-értékek vizualizációja
    fig = go.Figure()
    
    colors = ['green' if p < 0.01 else 'orange' if p < 0.05 else 'red' 
              for p in results_df['f_p_value']]
    
    fig.add_trace(go.Bar(
        x=results_df['feature'],
        y=-np.log10(results_df['f_p_value']),
        marker_color=colors,
        name='Szignifikancia'
    ))
    
    # Szignifikancia vonalak
    fig.add_hline(y=-np.log10(0.05), line_dash="dash", line_color="orange", 
                  annotation_text="p = 0.05")
    fig.add_hline(y=-np.log10(0.01), line_dash="dash", line_color="green", 
                  annotation_text="p = 0.01")
    
    fig.update_layout(
        title="Változók statisztikai szignifikanciája",
        xaxis_title="Változók",
        yaxis_title="-log10(p-érték)",
        xaxis_tickangle=45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Scatter plot matrix a szignifikáns változókhoz
    if len(highly_significant) > 0:
        st.subheader("🔍 Szignifikáns változók korrelációi")
        
        # Maximum 6 változó a láthatóság miatt
        vars_to_plot = highly_significant[:6] + ['target_ar']
        plot_df = df[vars_to_plot].dropna()
        
        if len(plot_df) > 10:
            fig = px.scatter_matrix(
                plot_df,
                dimensions=vars_to_plot,
                title="Szignifikáns változók korrelációs mátrixa"
            )
            fig.update_traces(diagonal_visible=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # Modell ajánlás
    st.subheader("🎯 Ajánlott ML modell változók")
    
    final_features = highly_significant.copy()
    
    # Ha túl kevés erősen szignifikáns változó van, vegyünk be néhány gyengébbet is
    if len(final_features) < 4:
        weak_significant = [v for v in significant_vars if v not in highly_significant]
        final_features.extend(weak_significant[:4-len(final_features)])
    
    st.success(f"**Ajánlott {len(final_features)} változó az ML modellhez:**")
    for i, var in enumerate(final_features, 1):
        row = results_df[results_df['feature'] == var].iloc[0]
        st.write(f"{i}. **{var}** - Pearson r: {row['pearson_r']:.3f}, R²: {row['r_squared']:.3f}")
    
    return final_features, results_df

if __name__ == "__main__":
    create_significance_dashboard()
