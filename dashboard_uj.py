"""
ELADÓ HÁZ ERD ERDLIGET - EGYSZERŰ DASHBOARD
==========================================
Új CSV formátumhoz adaptálva
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Oldal konfiguráció
st.set_page_config(
    page_title="🏠 Eladó Ház Erd Erdliget Dashboard",
    page_icon="🏠",
    layout="wide"
)

@st.cache_data(ttl=10)  # 10 másodperc cache
def load_data():
    """Adatok betöltése"""
    try:
        df = pd.read_csv("ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv", encoding='utf-8-sig')
        
        # Numerikus konverziók
        if 'nm_ar' in df.columns:
            # nm_ar: "1 278 195 Ft / m2" -> 1278195 (eltávolítjuk a szóközöket, megtartjuk a számokat)
            def parse_price_per_m2(text):
                if pd.isna(text):
                    return None
                import re
                # Kivonjuk az első számcsoportot a "Ft" előtt
                match = re.search(r'([\d\s\xa0]+)\s*Ft', str(text))
                if match:
                    # Szóközök és non-breaking space-ek eltávolítása
                    numbers = match.group(1).replace(' ', '').replace('\xa0', '')
                    return int(numbers) if numbers.isdigit() else None
                return None
            
            df['ar_szam'] = df['nm_ar'].apply(parse_price_per_m2)
        if 'teljes_ar' in df.columns:
            # teljes_ar: "170 M Ft" vagy "139,90 M Ft" -> 170 vagy 139.90 (millió Ft-ban)
            def parse_million_ft(text):
                if pd.isna(text):
                    return None
                text = str(text).replace(',', '.')  # vessző -> pont
                import re
                match = re.search(r'(\d+(?:\.\d+)?)\s*M', text)
                return float(match.group(1)) if match else None
            
            df['teljes_ar_millió'] = df['teljes_ar'].apply(parse_million_ft)
        if 'terulet' in df.columns:
            df['terulet_szam'] = pd.to_numeric(df['terulet'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        if 'szobak' in df.columns:
            df['szobak_szam'] = pd.to_numeric(df['szobak'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        if 'kepek_szama' in df.columns:
            df['kepek_szama'] = pd.to_numeric(df['kepek_szama'], errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Betöltési hiba: {e}")
        return pd.DataFrame()

def main():
    st.title("🏠 Eladó Ház Erd Erdliget - Ingatlan Dashboard")
    
    # Adatok betöltése
    df = load_data()
    
    if df.empty:
        st.error("Nem sikerült betölteni az adatokat!")
        return
    
    # Alapstatisztikák
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Összes ingatlan", len(df))
    
    with col2:
        if 'ar_szam' in df.columns:
            avg_price = df['ar_szam'].dropna().mean()
            if not pd.isna(avg_price):
                st.metric("💰 Átlag m² ár", f"{avg_price:,.0f} Ft/m²")
            else:
                st.metric("💰 Átlag m² ár", "N/A")
        else:
            st.metric("💰 Átlag m² ár", "N/A")
    
    with col3:
        if 'teljes_ar_millió' in df.columns:
            avg_total = df['teljes_ar_millió'].dropna().mean()
            if not pd.isna(avg_total):
                st.metric("🏠 Átlag teljes ár", f"{avg_total:.1f} M Ft")
            else:
                st.metric("🏠 Átlag teljes ár", "N/A")
        else:
            st.metric("🏠 Átlag teljes ár", "N/A")
    
    # Hirdető típus megoszlás
    st.header("👤 Hirdető típus megoszlás")
    if 'hirdeto_tipus' in df.columns:
        hirdeto_counts = df['hirdeto_tipus'].value_counts()
        fig_pie = px.pie(
            values=hirdeto_counts.values, 
            names=hirdeto_counts.index,
            title="Hirdetők megoszlása"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Hirdető típus adat nem érhető el")
    
    # Ár vs terület elemzés
    st.header("💰 Ár és terület összefüggés")
    if 'ar_szam' in df.columns and 'terulet_szam' in df.columns:
        df_clean = df.dropna(subset=['ar_szam', 'terulet_szam'])
        
        if len(df_clean) > 0:
            fig_scatter = px.scatter(
                df_clean,
                x='terulet_szam',
                y='ar_szam', 
                color='hirdeto_tipus' if 'hirdeto_tipus' in df.columns else None,
                title='m² ár vs. terület',
                labels={
                    'terulet_szam': 'Terület (m²)',
                    'ar_szam': 'm² ár (Ft/m²)',
                    'hirdeto_tipus': 'Hirdető típus'
                }
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("Nincs elegendő adat a grafikonhoz")
    else:
        st.warning("Ár vagy terület adat nem érhető el")
    
    # Állapot szerinti megoszlás
    st.header("🏠 Ingatlan állapot szerinti megoszlás")
    if 'ingatlan_allapota' in df.columns:
        allapot_counts = df['ingatlan_allapota'].dropna().value_counts()
        fig_bar = px.bar(
            x=allapot_counts.index,
            y=allapot_counts.values,
            title='Ingatlanok állapot szerint',
            labels={'x': 'Állapot', 'y': 'Darab'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Ingatlan állapot adat nem érhető el")
    
    # Adatok táblázat
    st.header("📊 Részletes adatok")
    
    # Hirdetés azonosító hozzáadása
    display_df = df.copy()
    
    # Oszlopok kiválasztása megjelenítéshez
    display_cols = ['cim', 'teljes_ar', 'terulet', 'nm_ar', 'szobak', 'ingatlan_allapota', 
                   'hirdeto_tipus', 'kepek_szama']
    available_cols = [col for col in display_cols if col in df.columns]
    
    # Azonosító létrehozása - csak szám, link külön
    if 'link' in df.columns:
        # Linkből kivonjuk az ID számot
        def extract_id_from_link(link):
            if pd.isna(link):
                return "N/A"
            # Az URL-ből kivonjuk az utolsó számot (pl. ingatlan.com/34877062 -> 34877062)
            import re
            match = re.search(r'(\d+)/?$', str(link))
            return match.group(1) if match else "N/A"
        
        display_df['Hirdetés ID'] = display_df['link'].apply(extract_id_from_link)
    else:
        display_df['Hirdetés ID'] = [f"ID-{i+1:03d}" for i in range(len(display_df))]
    
    # Oszlop sorrendjének beállítása - ID az első helyen
    final_cols = ['Hirdetés ID'] + available_cols
    final_available_cols = [col for col in final_cols if col in display_df.columns]
    
    if final_available_cols:
        # Első 20 sor megjelenítése
        display_subset = display_df[final_available_cols].head(20).copy()
        
        # Ha van link oszlop, akkor kattintható linkeket készítünk
        if 'link' in df.columns:
            # Link oszlop hozzáadása a táblázathoz
            link_column = []
            for idx in display_subset.index:
                original_row = df.iloc[idx] 
                if pd.notna(original_row.get('link', '')):
                    link_column.append(original_row['link'])
                else:
                    link_column.append("")
            
            display_subset['🔗 Link'] = link_column
            
        st.dataframe(
            display_subset, 
            use_container_width=True,
            column_config={
                "🔗 Link": st.column_config.LinkColumn(
                    "🔗 Link",
                    help="Hirdetés megnyitása",
                    display_text="Megnyitás"
                )
            } if 'link' in df.columns else None
        )
    else:
        st.dataframe(display_df.head(20), use_container_width=True)
    
    # CSV info
    st.info(f"📊 CSV információ: {len(df)} sor, {len(df.columns)} oszlop")
    with st.expander("🔍 Oszlopok listája"):
        st.write(list(df.columns))
    
    # Részletes elemzések
    st.header("📊 Részletes piaci elemzések")
    
    # Árelemzés részletek
    st.subheader("💰 Árelemzés részletek")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ár/m² eloszlás hisztogram
        if 'ar_szam' in df.columns:
            df_clean = df.dropna(subset=['ar_szam'])
            if len(df_clean) > 0:
                fig_hist = px.histogram(
                    df_clean,
                    x='ar_szam',
                    title='m² árak eloszlása',
                    labels={'ar_szam': 'm² ár (Ft/m²)', 'count': 'Darabszám'},
                    nbins=15
                )
                st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Teljes árak eloszlása
        if 'teljes_ar_millió' in df.columns:
            df_clean_total = df.dropna(subset=['teljes_ar_millió'])
            if len(df_clean_total) > 0:
                fig_hist_total = px.histogram(
                    df_clean_total,
                    x='teljes_ar_millió',
                    title='Teljes árak eloszlása',
                    labels={'teljes_ar_millió': 'Teljes ár (M Ft)', 'count': 'Darabszám'},
                    nbins=15
                )
                st.plotly_chart(fig_hist_total, use_container_width=True)
    
    # TOP és FLOP ingatlanok
    st.subheader("🏆 TOP és 📉 FLOP ingatlanok")
    
    if 'ar_szam' in df.columns:
        df_valid = df.dropna(subset=['ar_szam'])
        if len(df_valid) >= 6:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🏆 TOP 3 legdrágább m² ár:**")
                if 'link' in df_valid.columns:
                    top3 = df_valid.nlargest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama', 'link']]
                    for i, (_, row) in enumerate(top3.iterrows()):
                        link_text = f"[{row['cim']}]({row['link']})" if pd.notna(row.get('link')) else row['cim']
                        st.write(f"{i+1}. **{link_text}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
                else:
                    top3 = df_valid.nlargest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama']]
                    for i, (_, row) in enumerate(top3.iterrows()):
                        st.write(f"{i+1}. **{row['cim']}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
            
            with col2:
                st.write("**📉 TOP 3 legolcsóbb m² ár:**")
                if 'link' in df_valid.columns:
                    bottom3 = df_valid.nsmallest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama', 'link']]
                    for i, (_, row) in enumerate(bottom3.iterrows()):
                        link_text = f"[{row['cim']}]({row['link']})" if pd.notna(row.get('link')) else row['cim']
                        st.write(f"{i+1}. **{link_text}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
                else:
                    bottom3 = df_valid.nsmallest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama']]
                    for i, (_, row) in enumerate(bottom3.iterrows()):
                        st.write(f"{i+1}. **{row['cim']}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
    
    # Statisztikai elemzések szekció
    st.header("📈 Részletes statisztikai elemzések")
    
    # Kategória választó
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.write("**Válaszd ki a kategóriát:**")
        available_categories = []
        category_mapping = {}
        
        if 'ingatlan_allapota' in df.columns and not df['ingatlan_allapota'].dropna().empty:
            available_categories.append('Ingatlan állapota')
            category_mapping['Ingatlan állapota'] = 'ingatlan_allapota'
        
        if 'hirdeto_tipus' in df.columns and not df['hirdeto_tipus'].dropna().empty:
            available_categories.append('Hirdető típusa')
            category_mapping['Hirdető típusa'] = 'hirdeto_tipus'
        
        if 'szobak_szam' in df.columns and not df['szobak_szam'].dropna().empty:
            available_categories.append('Szobák száma')
            category_mapping['Szobák száma'] = 'szobak_szam'
        
        if available_categories:
            selected_category = st.selectbox(
                "Kategória:",
                available_categories,
                index=0
            )
            
            # Numerikus változó választó
            numeric_options = []
            if 'ar_szam' in df.columns:
                numeric_options.append('m² ár (Ft/m²)')
            if 'teljes_ar_millió' in df.columns:
                numeric_options.append('Teljes ár (M Ft)')
            if 'kepek_szama' in df.columns:
                numeric_options.append('Képek száma')
            if 'terulet_szam' in df.columns:
                numeric_options.append('Terület (m²)')
            
            if numeric_options:
                selected_numeric = st.selectbox(
                    "Elemzendő változó:",
                    numeric_options,
                    index=0
                )
    
    with col2:
        if available_categories and numeric_options:
            # Adatok előkészítése
            category_col = category_mapping[selected_category]
            
            if selected_numeric == 'm² ár (Ft/m²)':
                numeric_col = 'ar_szam'
                format_func = lambda x: f"{x:,.0f} Ft/m²"
            elif selected_numeric == 'Teljes ár (M Ft)':
                numeric_col = 'teljes_ar_millió'
                format_func = lambda x: f"{x:.1f} M Ft"
            elif selected_numeric == 'Képek száma':
                numeric_col = 'kepek_szama'
                format_func = lambda x: f"{x:.1f}"
            elif selected_numeric == 'Terület (m²)':
                numeric_col = 'terulet_szam'
                format_func = lambda x: f"{x:.0f} m²"
            
            # Statisztikák számítása
            df_stats = df.dropna(subset=[category_col, numeric_col])
            
            if len(df_stats) > 0:
                stats_table = df_stats.groupby(category_col)[numeric_col].agg([
                    'count',
                    'mean', 
                    'median',
                    'std',
                    'min',
                    'max'
                ]).round(2)
                
                # Módusz hozzáadása (leggyakoribb érték)
                def get_mode(series):
                    return series.mode().iloc[0] if not series.mode().empty else series.median()
                
                stats_table['mode'] = df_stats.groupby(category_col)[numeric_col].apply(get_mode).round(2)
                
                # Oszlopok átnevezése
                stats_table.columns = ['Darab', 'Átlag', 'Medián', 'Szórás', 'Minimum', 'Maximum', 'Módusz']
                
                # Formatting - csak a számértékeket formázzuk
                display_table = stats_table.copy()
                for col in ['Átlag', 'Medián', 'Minimum', 'Maximum', 'Módusz']:
                    if col in display_table.columns:
                        display_table[col] = stats_table[col].apply(format_func)
                
                if 'Szórás' in display_table.columns:
                    if selected_numeric == 'm² ár (Ft/m²)':
                        display_table['Szórás'] = stats_table['Szórás'].apply(lambda x: f"{x:,.0f}")
                    elif selected_numeric == 'Teljes ár (M Ft)':
                        display_table['Szórás'] = stats_table['Szórás'].apply(lambda x: f"{x:.1f}")
                    else:
                        display_table['Szórás'] = stats_table['Szórás'].apply(lambda x: f"{x:.1f}")
                
                st.write(f"**📊 {selected_numeric} statisztikák {selected_category.lower()} szerint:**")
                st.dataframe(display_table, use_container_width=True)
                
                # Box plot
                fig_box = px.box(
                    df_stats,
                    x=category_col,
                    y=numeric_col,
                    title=f'{selected_numeric} eloszlása {selected_category.lower()} szerint',
                    labels={
                        category_col: selected_category,
                        numeric_col: selected_numeric
                    }
                )
                fig_box.update_xaxes(tickangle=45)
                st.plotly_chart(fig_box, use_container_width=True)
                
                # Insights
                st.write("**💡 Főbb megállapítások:**")
                
                # Legnagyobb átlag
                max_avg_category = stats_table['Átlag'].idxmax() if not stats_table.empty else None
                if max_avg_category:
                    st.write(f"• **Legmagasabb átlag**: {max_avg_category} ({format_func(stats_table.loc[max_avg_category, 'Átlag'])})")
                
                # Legnagyobb szórás  
                max_std_category = stats_table['Szórás'].idxmax() if not stats_table.empty else None
                if max_std_category:
                    st.write(f"• **Legnagyobb változékonyság**: {max_std_category}")
                
                # Legnagyobb darabszám
                max_count_category = stats_table['Darab'].idxmax() if not stats_table.empty else None
                if max_count_category:
                    st.write(f"• **Legtöbb ingatlan**: {max_count_category} ({int(stats_table.loc[max_count_category, 'Darab'])} db)")
                
            else:
                st.warning("Nincs elegendő adat a statisztikai elemzéshez.")
        else:
            st.info("Válassz kategóriát és numerikus változót a részletes statisztikákért!")
    
    # Korrelációs elemzések
    st.header("📈 Korrelációs elemzések")
    st.write("Vizsgáld meg, hogy különböző paraméterek hogyan befolyásolják az ingatlanárakat!")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Célváltozó választás
        target_options = []
        if 'ar_szam' in df.columns:
            target_options.append('m² ár (Ft/m²)')
        if 'teljes_ar_millió' in df.columns:
            target_options.append('Teljes ár (M Ft)')
        
        if target_options:
            selected_target = st.selectbox(
                "Célváltozó (amit előre szeretnél jelezni):",
                target_options,
                index=0
            )
            
            # Magyarázó változók
            explanatory_options = []
            if 'terulet_szam' in df.columns:
                explanatory_options.append('Terület (m²)')
            if 'kepek_szama' in df.columns:
                explanatory_options.append('Képek száma')
            if 'szobak_szam' in df.columns:
                explanatory_options.append('Szobák száma')
            if 'ingatlan_allapota' in df.columns:
                explanatory_options.append('Ingatlan állapota')
            if 'hirdeto_tipus' in df.columns:
                explanatory_options.append('Hirdető típusa')
            if 'leiras' in df.columns:
                explanatory_options.append('Leírás kulcsszavak')
            
            if explanatory_options:
                selected_explanatory = st.selectbox(
                    "Magyarázó változó:",
                    explanatory_options,
                    index=0
                )
                
                # Kulcsszó input ha leírás van választva
                keyword_input = ""
                if selected_explanatory == 'Leírás kulcsszavak':
                    keyword_input = st.text_input(
                        "Kulcsszó a leírásból:",
                        placeholder="pl. garázs, kert, panoráma",
                        help="Add meg a kulcsszót amit keresünk a leírásokban"
                    )
    
    with col2:
        if target_options and explanatory_options:
            # Célváltozó beállítása
            if selected_target == 'm² ár (Ft/m²)':
                target_col = 'ar_szam'
                target_label = 'm² ár (Ft/m²)'
            else:
                target_col = 'teljes_ar_millió'
                target_label = 'Teljes ár (M Ft)'
            
            # Magyarázó változó beállítása
            if selected_explanatory == 'Terület (m²)':
                exp_col = 'terulet_szam'
                exp_label = 'Terület (m²)'
                analysis_type = 'numeric'
            elif selected_explanatory == 'Képek száma':
                exp_col = 'kepek_szama'
                exp_label = 'Képek száma'
                analysis_type = 'numeric'
            elif selected_explanatory == 'Szobák száma':
                exp_col = 'szobak_szam'
                exp_label = 'Szobák száma'
                analysis_type = 'numeric'
            elif selected_explanatory == 'Ingatlan állapota':
                exp_col = 'ingatlan_allapota'
                exp_label = 'Ingatlan állapota'
                analysis_type = 'categorical'
            elif selected_explanatory == 'Hirdető típusa':
                exp_col = 'hirdeto_tipus'
                exp_label = 'Hirdető típusa'
                analysis_type = 'categorical'
            elif selected_explanatory == 'Leírás kulcsszavak' and keyword_input:
                exp_col = 'keyword_match'
                exp_label = f'Kulcsszó: "{keyword_input}"'
                analysis_type = 'keyword'
                # Kulcsszó keresés
                df['keyword_match'] = df['leiras'].astype(str).str.contains(
                    keyword_input, case=False, na=False
                ).map({True: f'Van "{keyword_input}"', False: f'Nincs "{keyword_input}"'})
            else:
                analysis_type = 'none'
            
            # Elemzés végrehajtása
            if analysis_type != 'none':
                df_corr = df.dropna(subset=[target_col, exp_col])
                
                if len(df_corr) > 5:
                    if analysis_type == 'numeric':
                        # Numerikus korreláció
                        correlation = df_corr[target_col].corr(df_corr[exp_col])
                        
                        # Scatter plot
                        fig_corr = px.scatter(
                            df_corr,
                            x=exp_col,
                            y=target_col,
                            title=f'{target_label} vs {exp_label}',
                            labels={exp_col: exp_label, target_col: target_label}
                        )
                        
                        # Trend line hozzáadása manuálisan
                        z = np.polyfit(df_corr[exp_col], df_corr[target_col], 1)
                        p = np.poly1d(z)
                        fig_corr.add_scatter(
                            x=df_corr[exp_col],
                            y=p(df_corr[exp_col]),
                            mode='lines',
                            name='Trend',
                            line=dict(color='red', dash='dash')
                        )
                        
                        st.plotly_chart(fig_corr, use_container_width=True)
                        
                        # Korreláció értelmezése
                        st.write(f"**🔗 Korreláció**: {correlation:.3f}")
                        if abs(correlation) > 0.7:
                            st.success(f"💪 **Erős kapcsolat!** ({correlation:.1%} magyarázó erő)")
                        elif abs(correlation) > 0.4:
                            st.info(f"🤔 **Közepes kapcsolat** ({correlation:.1%} magyarázó erő)")
                        elif abs(correlation) > 0.2:
                            st.warning(f"🤷 **Gyenge kapcsolat** ({correlation:.1%} magyarázó erő)")
                        else:
                            st.error("❌ **Nincs jelentős kapcsolat**")
                            
                    else:
                        # Kategorikus elemzés (box plot)
                        fig_box_corr = px.box(
                            df_corr,
                            x=exp_col,
                            y=target_col,
                            title=f'{target_label} eloszlása {exp_label} szerint',
                            labels={exp_col: exp_label, target_col: target_label}
                        )
                        fig_box_corr.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_box_corr, use_container_width=True)
                        
                        # Csoportos statisztikák
                        group_stats = df_corr.groupby(exp_col)[target_col].agg([
                            'count', 'mean', 'std', 'min', 'max'
                        ]).round(2)
                        group_stats.columns = ['Darab', 'Átlag', 'Szórás', 'Min', 'Max']
                        
                        st.write(f"**📊 {target_label} statisztikák {exp_label} szerint:**")
                        st.dataframe(group_stats, use_container_width=True)
                        
                        # ANOVA teszt (kategóriák közötti különbség)
                        try:
                            from scipy import stats
                            groups = [group for name, group in df_corr.groupby(exp_col)[target_col]]
                            f_stat, p_value = stats.f_oneway(*groups)
                            
                            if p_value < 0.05:
                                st.success(f"✅ **Szignifikáns különbség** a kategóriák között! (p={p_value:.4f})")
                            else:
                                st.info(f"🤷 **Nincs szignifikáns különbség** (p={p_value:.4f})")
                        except:
                            st.info("Statisztikai teszt nem elérhető")
                
                else:
                    st.warning("Túl kevés adat a korrelációs elemzéshez")
            elif selected_explanatory == 'Leírás kulcsszavak' and not keyword_input:
                st.info("💡 Add meg a keresendő kulcsszót!")
        else:
            st.info("Válaszd ki a célváltozót és magyarázó változót a korrelációs elemzéshez!")
    
    # Szemantikai elemzés (Word Cloud)
    st.header("🌟 Szemantikai elemzés - Szófelhő")
    st.write("A hirdetési leírások leggyakoribb szavai")
    
    if 'leiras' in df.columns:
        try:
            # Szófelhő létrehozása
            all_descriptions = ' '.join(df['leiras'].dropna().astype(str))
            
            # Stop words és nem fontos szavak eltávolítása
            stop_words = {
                'ingatlan', 'elhelyezkedés', 'eladó', 'ház', 'lakás', 'és', 'a', 'az', 'egy', 'van', 'volt', 'lesz',
                'miatt', 'szerint', 'alatt', 'mellett', 'között', 'után', 'előtt', 'során', 'által', 'vagy',
                'csak', 'már', 'még', 'is', 'hogy', 'mint', 'amit', 'amely', 'ami', 'aki', 'ahol', 'amikor',
                'családi', 'tulajdonos', 'tulajdon', 'hirdetés', 'hirdet', 'kiadó', 'bérlő', 'bérlet',
                'keresek', 'keres', 'vásárol', 'vevő', 'eladás', 'vétel', 'adás', 'vesz', 'ad', 'kapható',
                'található', 'helyen', 'helyiség', 'helyett', 'része', 'részben', 'teljes', 'teljesen',
                'igen', 'nem', 'nincs', 'nincsenek', 'vannak', 'voltak', 'lesznek', 'lehet', 'lehetséges',
                'kell', 'kellene', 'szükséges', 'fontos', 'fontos', 'jó', 'rossz', 'nagy', 'kicsi', 'közepes'
            }
            
            # Szavak tisztítása
            import re
            words = re.findall(r'\b[a-záéíóöőúüű]{3,}\b', all_descriptions.lower())
            words = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Gyakorisági elemzés
            from collections import Counter
            word_freq = Counter(words)
            top_words = word_freq.most_common(50)
            
            if top_words:
                # Szófelhő vizualizáció plotly-val
                word_df = pd.DataFrame(top_words, columns=['Szó', 'Gyakoriság'])
                
                # Top 20 szó bar chart
                fig_words = px.bar(
                    word_df.head(20),
                    x='Gyakoriság',
                    y='Szó',
                    orientation='h',
                    title='Top 20 leggyakoribb szó a hirdetésekben',
                    labels={'Gyakoriság': 'Előfordulások száma', 'Szó': 'Szavak'}
                )
                fig_words.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_words, use_container_width=True)
                
                # Kulcsszó kategóriák
                st.write("**🏷️ Témakörök a leírásokban:**")
                
                themes = {
                    '🏠 Állapot': ['felújított', 'újszerű', 'modern', 'rendezett', 'igényes', 'tiszta'],
                    '🌳 Környezet': ['kert', 'terasz', 'balkon', 'udvar', 'zöld', 'természet', 'csend', 'nyugodt'],
                    '🚗 Parkolás': ['garázs', 'parkoló', 'autó', 'beállóhely', 'udvar'],
                    '🔧 Felszereltség': ['klíma', 'fűtés', 'kazán', 'radiátor', 'konvektor', 'kandalló'],
                    '📍 Elhelyezkedés': ['központ', 'iskola', 'bolt', 'buszmegálló', 'vonat', 'közlekedés'],
                    '💰 Értékelés': ['befektetés', 'potenciál', 'lehetőség', 'érték', 'ár', 'olcsó', 'drága']
                }
                
                theme_counts = {}
                for theme, keywords in themes.items():
                    count = sum(word_freq.get(keyword, 0) for keyword in keywords)
                    if count > 0:
                        theme_counts[theme] = count
                
                if theme_counts:
                    theme_df = pd.DataFrame(list(theme_counts.items()), columns=['Témakör', 'Említések'])
                    theme_df = theme_df.sort_values('Említések', ascending=False)
                    
                    fig_themes = px.pie(
                        theme_df,
                        values='Említések',
                        names='Témakör',
                        title='Témakörök megoszlása a hirdetésekben'
                    )
                    st.plotly_chart(fig_themes, use_container_width=True)
                
            else:
                st.warning("Nem található elegendő szöveg a szófelhő készítéséhez")
                
        except Exception as e:
            st.error(f"Hiba a szófelhő készítése során: {e}")
            st.info("Próbáld újra frissíteni az oldalt")
    
    else:
        st.warning("Nincs elérhető leírás adat a szemantikai elemzéshez")
    
    # Ingatlan értékbecslő
    st.header("🏠 Ingatlan értékbecslő")
    st.write("Add meg a saját ingatlanod paramétereit az ajánlott eladási ár kiszámításához")
    
    # Regressziós modell létrehozása
    try:
        # Numerikus adatok előkészítése
        model_df = df.dropna(subset=['ar_szam', 'terulet_szam']).copy()
        
        if len(model_df) > 10:  # Minimum 10 adat kell a modellhez
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📝 Ingatlan paraméterei:**")
                
                # Felhasználói inputok
                user_terulet = st.number_input(
                    "Terület (m²)",
                    min_value=50,
                    max_value=500,
                    value=170,  # Átlag közelebb az adatokhoz
                    step=5
                )
                
                user_telek = st.number_input(
                    "Telek mérete (m²)",
                    min_value=200,
                    max_value=3000,
                    value=1500,  # Adatok alapján reálisabb
                    step=50
                )
                
                user_szobak = st.selectbox(
                    "Szobák száma",
                    options=['2', '3', '4', '5', '6+'],
                    index=3  # 5 szoba default
                )
                
                user_allapot = st.selectbox(
                    "Ingatlan állapota",
                    options=df['ingatlan_allapota'].dropna().unique() if 'ingatlan_allapota' in df.columns else ['felújított', 'jó állapotú', 'felújítandó'],
                    index=0  # felújított default
                )
                
                user_hirdeto = st.selectbox(
                    "Hirdető típusa",
                    options=df['hirdeto_tipus'].dropna().unique() if 'hirdeto_tipus' in df.columns else ['Magánszemély', 'Ingatlanirodák'],
                    index=0  # Magánszemély default
                )
                
                # Képek száma becslés
                user_kepek = st.number_input(
                    "Képek száma",
                    min_value=1,
                    max_value=20,
                    value=8,
                    step=1
                )
            
            with col2:
                st.write("**🤖 Értékbecslés eredménye:**")
                
                # Egyszerű regressziós modell
                from sklearn.linear_model import LinearRegression
                from sklearn.preprocessing import LabelEncoder
                
                # Feature engineering
                features = []
                feature_names = []
                
                # Numerikus változók
                features.append(model_df['terulet_szam'].values)
                feature_names.append('terulet')
                
                if 'kepek_szama' in model_df.columns:
                    features.append(model_df['kepek_szama'].fillna(model_df['kepek_szama'].mean()).values)
                    feature_names.append('kepek_szama')
                
                # Kategorikus változók encoding
                if 'szobak_szam' in model_df.columns:
                    szobak_encoded = model_df['szobak_szam'].map({'2': 2, '3': 3, '4': 4, '5': 5, '6+': 6}).fillna(4)
                    features.append(szobak_encoded.values)
                    feature_names.append('szobak_szam')
                
                if 'ingatlan_allapota' in model_df.columns:
                    allapot_map = {'felújített': 3, 'jó állapotú': 2, 'közepes állapotú': 1, 'felújítandó': 0}
                    allapot_encoded = model_df['ingatlan_allapota'].map(allapot_map).fillna(1)
                    features.append(allapot_encoded.values)
                    feature_names.append('ingatlan_allapota')
                
                # Features mátrix összeállítása
                X = np.column_stack(features)
                y = model_df['teljes_ar_millió'].values
                
                # Debug információ
                st.write("**🔍 Modell információk:**")
                st.write(f"- **Tanító adatok száma**: {len(model_df)}")
                st.write(f"- **Átlag telek méret**: {model_df['terulet_szam'].mean():.0f} m²")
                st.write(f"- **Átlag ár**: {model_df['teljes_ar_millió'].mean():.1f} M Ft")
                
                # Modell tanítása
                model = LinearRegression()
                model.fit(X, y)
                
                # R² score kiszámítása
                r2_score = model.score(X, y)
                
                # Felhasználói input előkészítése
                user_features = []
                user_features.append(user_terulet)  # terulet
                
                if 'kepek_szama' in feature_names:
                    user_features.append(user_kepek)  # kepek_szama
                
                if 'szobak_szam' in feature_names:
                    szobak_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6+': 6}
                    user_features.append(szobak_map.get(user_szobak, 4))  # szobak_szam
                
                if 'ingatlan_allapota' in feature_names:
                    allapot_map = {'felújított': 3, 'jó állapotú': 2, 'közepes állapotú': 1, 'felújítandó': 0}
                    user_features.append(allapot_map.get(user_allapot, 1))  # ingatlan_allapota
                
                # Előrejelzés
                user_X = np.array(user_features).reshape(1, -1)
                predicted_price_million = model.predict(user_X)[0]  # Millió Ft-ban
                predicted_price_total = predicted_price_million * 1_000_000  # Teljes Ft-ban
                predicted_price_m2 = predicted_price_total / user_terulet
                
                # Egyszerű alternatív becslés összehasonlításhoz
                avg_price_per_m2 = df['ar_szam'].dropna().mean() if 'ar_szam' in df.columns else 1000000
                simple_prediction_total = avg_price_per_m2 * user_terulet
                simple_prediction_million = simple_prediction_total / 1_000_000
                
                # Eredmények megjelenítése
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success(f"**🤖 ML modell eredmény:**")
                    st.write(f"**{predicted_price_million:.1f} M Ft**")
                    st.write(f"**{predicted_price_m2:,.0f} Ft/m²**")
                    st.write(f"**Pontosság (R²):** {r2_score:.2f}")
                
                with col2:
                    st.info(f"**📊 Egyszerű becslés:**")
                    st.write(f"**{simple_prediction_million:.1f} M Ft**")
                    st.write(f"**{avg_price_per_m2:,.0f} Ft/m²** (átlag)")
                    st.write("*Terület × átlag m² ár*")
                
                # Hasonló ingatlanok elemzése
                similar_properties = model_df[
                    (model_df['terulet_szam'].between(user_terulet-20, user_terulet+20))
                ]
                
                if len(similar_properties) > 0:
                    avg_price = similar_properties['teljes_ar_millió'].mean()
                    min_price = similar_properties['teljes_ar_millió'].min()
                    max_price = similar_properties['teljes_ar_millió'].max()
                    
                    st.write("**🏘️ Hasonló ingatlanok (±20 m²):**")
                    st.write(f"- **Átlagár:** {avg_price:,.0f} M Ft")
                    st.write(f"- **Ár tartomány:** {min_price:,.0f} - {max_price:,.0f} M Ft")
                    st.write(f"- **Talált ingatlanok:** {len(similar_properties)} db")
                    
                    # Ár pozíció
                    if predicted_price_million < avg_price:
                        st.info(f"💡 A becsült ár {((avg_price - predicted_price_million)/avg_price*100):.1f}%-kal alacsonyabb az átlagnál")
                    elif predicted_price_million > avg_price:
                        st.info(f"💡 A becsült ár {((predicted_price_million - avg_price)/avg_price*100):.1f}%-kal magasabb az átlagnál")
                    else:
                        st.info("💡 A becsült ár az átlag körül alakul")
                
                # Árajánlási tartomány
                confidence_interval = 0.1  # ±10%
                lower_bound = predicted_price_million * (1 - confidence_interval)
                upper_bound = predicted_price_million * (1 + confidence_interval)
                
                st.write("**💰 Ajánlott ár tartomány (±10%):**")
                st.write(f"**{lower_bound:.1f} - {upper_bound:.1f} M Ft**")
                
                # Tényezők hatása
                st.write("**📈 Modell tényezői:**")
                feature_importance = abs(model.coef_)
                importance_df = pd.DataFrame({
                    'Tényező': [fn.replace('_', ' ').title() for fn in feature_names],
                    'Hatás': feature_importance
                })
                importance_df = importance_df.sort_values('Hatás', ascending=False)
                st.dataframe(importance_df, use_container_width=True)
        
        else:
            st.warning("Nincs elegendő adat (minimum 10 ingatlan szükséges) az értékbecsléshez")
            st.info(f"Jelenleg {len(model_df)} használható adat áll rendelkezésre")
    
    except Exception as e:
        st.error(f"Hiba az értékbecslés során: {e}")
        st.info("Ellenőrizd, hogy a CSV fájl tartalmazza a szükséges oszlopokat")

if __name__ == "__main__":
    main()
