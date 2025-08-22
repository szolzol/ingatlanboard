#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ENHANCED XII. KERÜLETI DASHBOARD GENERÁTOR
==========================================

Az enhanced lokáció rendszerrel újra generálja a XII. kerületi dashboardot
pontosabb lokáció kategorizálással és Google Maps integráció lehetőségével.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
import re
from collections import Counter
from datetime import datetime

# Streamlit konfiguráció
st.set_page_config(
    page_title="🏠 XII. Kerület - Enhanced Ingatlan Dashboard", 
    page_icon="🏠", 
    layout="wide"
)

# ==== ENHANCED DASHBOARD MAIN ====
def main():
    """Főfunkció - Enhanced XII. kerületi dashboard"""
    
    # Dashboard címe
    st.title("🏠 XII. Kerület Ingatlan Dashboard - Enhanced Lokáció Rendszer")
    st.markdown("---")
    
    # Adatok betöltése
    df = load_data()
    if df is None or len(df) == 0:
        st.error("❌ Nincs XII. kerületi adat!")
        return
    
    # Enhanced lokáció oszlopok ellenőrzése
    enhanced_columns = ['enhanced_keruleti_resz', 'lokacio_konfidencia', 'lokacio_elemzesi_modszer']
    has_enhanced = all(col in df.columns for col in enhanced_columns)
    
    if has_enhanced:
        st.success(f"✅ Enhanced lokáció adatok betöltve - {len(df)} rekord")
        st.info("🗺️ Ez a dashboard az Enhanced Lokáció Rendszert használja pontosabb kategorizáláshoz")
    else:
        st.warning("⚠️ Enhanced lokáció adatok nem találhatók - alapértelmezett dashboard")
    
    # Alap statisztikák
    show_basic_stats(df)
    
    if has_enhanced:
        # Enhanced lokáció elemzések
        show_enhanced_location_analysis(df)
    
    # Árelemzések
    show_price_analysis(df)
    
    # Szöveganalízis
    if 'netto_szoveg_pont' in df.columns:
        show_text_analysis(df)
    
    # Részletes adatok
    show_detailed_data(df)

def load_data():
    """XII. kerületi adatok betöltése"""
    
    # Keresés a XII. kerületi fájlokra
    xii_files = [f for f in os.listdir('.') if 'xii_ker' in f.lower() and f.endswith('.csv')]
    
    if not xii_files:
        return None
    
    # Legújabb fájl kiválasztása
    latest_file = max(xii_files, key=os.path.getmtime)
    
    try:
        # Többféle betöltési kísérlet
        separators = ['|', ';', ',']
        for sep in separators:
            try:
                df = pd.read_csv(latest_file, sep=sep, encoding='utf-8', on_bad_lines='skip')
                if len(df.columns) > 10:
                    st.info(f"📂 Adatforrás: {latest_file} (sep='{sep}')")
                    return df
            except:
                continue
                
        return None
        
    except Exception as e:
        st.error(f"Adatbetöltési hiba: {e}")
        return None

def show_basic_stats(df):
    """Alapstatisztikák megjelenítése"""
    
    st.subheader("📊 Alapstatisztikák")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Összes ingatlan", len(df))
    
    with col2:
        if 'teljes_ar' in df.columns:
            avg_price = df['teljes_ar'].dropna().apply(extract_price_number).mean()
            if pd.notna(avg_price):
                st.metric("Átlagár", f"{avg_price:.1f}M Ft")
            else:
                st.metric("Átlagár", "N/A")
        else:
            st.metric("Átlagár", "N/A")
    
    with col3:
        if 'terulet' in df.columns:
            avg_area = df['terulet'].dropna().apply(extract_area_number).mean()
            if pd.notna(avg_area):
                st.metric("Átlag terület", f"{avg_area:.0f} m²")
            else:
                st.metric("Átlag terület", "N/A")
        else:
            st.metric("Átlag terület", "N/A")
    
    with col4:
        if 'nm_ar' in df.columns:
            avg_sqm_price = df['nm_ar'].dropna().apply(extract_sqm_price).mean()
            if pd.notna(avg_sqm_price):
                st.metric("Átlag m² ár", f"{avg_sqm_price:.0f} Ft/m²")
            else:
                st.metric("Átlag m² ár", "N/A")
        else:
            st.metric("Átlag m² ár", "N/A")

def show_enhanced_location_analysis(df):
    """Enhanced lokáció elemzések megjelenítése"""
    
    st.subheader("🗺️ Enhanced Lokáció Elemzés")
    
    if 'enhanced_keruleti_resz' not in df.columns:
        st.warning("Enhanced lokáció adatok nem találhatók")
        return
    
    # Kerületi részek megoszlása
    col1, col2 = st.columns([2, 1])
    
    with col1:
        district_counts = df['enhanced_keruleti_resz'].value_counts()
        
        fig = px.pie(
            values=district_counts.values, 
            names=district_counts.index,
            title="XII. Kerületi Részek Megoszlása (Enhanced Rendszer)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Kerületi részek:**")
        for district, count in district_counts.items():
            percentage = (count / len(df)) * 100
            st.write(f"• {district}: {count} db ({percentage:.1f}%)")
    
    # Lokáció konfidencia elemzés
    if 'lokacio_konfidencia' in df.columns:
        st.subheader("🎯 Lokáció Konfidencia Elemzés")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                df, 
                x='lokacio_konfidencia',
                title="Lokáció Konfidencia Eloszlás",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            high_conf = (df['lokacio_konfidencia'] > 0.7).sum()
            medium_conf = ((df['lokacio_konfidencia'] > 0.4) & (df['lokacio_konfidencia'] <= 0.7)).sum()
            low_conf = (df['lokacio_konfidencia'] <= 0.4).sum()
            
            st.write("**Konfidencia kategóriák:**")
            st.write(f"• Magas (>0.7): {high_conf} db")
            st.write(f"• Közepes (0.4-0.7): {medium_conf} db") 
            st.write(f"• Alacsony (≤0.4): {low_conf} db")
    
    # Elemzési módszerek megoszlása
    if 'lokacio_elemzesi_modszer' in df.columns:
        method_counts = df['lokacio_elemzesi_modszer'].value_counts()
        
        fig = px.bar(
            x=method_counts.index,
            y=method_counts.values,
            title="Lokáció Elemzési Módszerek Megoszlása"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_price_analysis(df):
    """Árelemzések megjelenítése"""
    
    st.subheader("💰 Árelemzések")
    
    if 'teljes_ar' not in df.columns:
        st.warning("Ár adatok nem találhatók")
        return
    
    # Árak kinyerése és tisztítása
    df_price = df.copy()
    df_price['ar_szam'] = df_price['teljes_ar'].apply(extract_price_number)
    df_price = df_price.dropna(subset=['ar_szam'])
    
    if len(df_price) == 0:
        st.warning("Nincs feldolgozható ár adat")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ár eloszlás
        fig = px.histogram(
            df_price, 
            x='ar_szam',
            title="Árak Eloszlása",
            nbins=20
        )
        fig.update_xaxes(title="Ár (millió Ft)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Enhanced kerületi részek szerinti árak (ha van)
        if 'enhanced_keruleti_resz' in df_price.columns:
            fig = px.box(
                df_price,
                x='enhanced_keruleti_resz', 
                y='ar_szam',
                title="Árak Kerületi Részek Szerint"
            )
            fig.update_xaxes(tickangle=45)
            fig.update_yaxes(title="Ár (millió Ft)")
            st.plotly_chart(fig, use_container_width=True)

def show_text_analysis(df):
    """Szöveganalízis megjelenítése"""
    
    st.subheader("📝 Szöveganalízis")
    
    if 'netto_szoveg_pont' not in df.columns:
        st.warning("Szöveganalízis adatok nem találhatók")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Nettó szövegpontok eloszlása
        fig = px.histogram(
            df,
            x='netto_szoveg_pont', 
            title="Nettó Szövegpontok Eloszlása",
            nbins=20
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top kategóriák
        if 'enhanced_keruleti_resz' in df.columns:
            avg_scores = df.groupby('enhanced_keruleti_resz')['netto_szoveg_pont'].mean().sort_values(ascending=False)
            
            fig = px.bar(
                x=avg_scores.index,
                y=avg_scores.values,
                title="Átlag Szövegpontok Kerületi Részek Szerint"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def show_detailed_data(df):
    """Részletes adatok megjelenítése"""
    
    st.subheader("🔍 Részletes Adatok")
    
    # Szűrők
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'enhanced_keruleti_resz' in df.columns:
            districts = ['Összes'] + list(df['enhanced_keruleti_resz'].unique())
            selected_district = st.selectbox("Kerületi rész", districts)
        else:
            selected_district = 'Összes'
    
    with col2:
        min_price = st.number_input("Min ár (M Ft)", value=0, min_value=0)
    
    with col3:
        max_price = st.number_input("Max ár (M Ft)", value=2000, min_value=0)
    
    # Szűrés alkalmazása
    filtered_df = df.copy()
    
    if selected_district != 'Összes' and 'enhanced_keruleti_resz' in df.columns:
        filtered_df = filtered_df[filtered_df['enhanced_keruleti_resz'] == selected_district]
    
    if 'teljes_ar' in df.columns:
        filtered_df['ar_szam'] = filtered_df['teljes_ar'].apply(extract_price_number)
        filtered_df = filtered_df[
            (filtered_df['ar_szam'].between(min_price, max_price)) | 
            (filtered_df['ar_szam'].isna())
        ]
    
    st.write(f"**Szűrt eredmények:** {len(filtered_df)} ingatlan")
    
    # Megjelenítendő oszlopok kiválasztása
    display_columns = ['cim', 'teljes_ar', 'terulet']
    if 'enhanced_keruleti_resz' in filtered_df.columns:
        display_columns.append('enhanced_keruleti_resz')
    if 'lokacio_konfidencia' in filtered_df.columns:
        display_columns.append('lokacio_konfidencia')
    
    # Csak létező oszlopok megtartása
    display_columns = [col for col in display_columns if col in filtered_df.columns]
    
    # Táblázat megjelenítése
    if display_columns:
        st.dataframe(filtered_df[display_columns].head(50), use_container_width=True)

# ==== SEGÉDFÜGGVÉNYEK ====

def extract_price_number(price_str):
    """Ár szövegből szám kinyerése (millió Ft-ban)"""
    if pd.isna(price_str) or price_str == '':
        return np.nan
    
    price_str = str(price_str).lower().replace(' ', '')
    
    # Milliárd -> millió konverzió
    if 'mrd' in price_str or 'milliárd' in price_str:
        numbers = re.findall(r'[\d,]+', price_str.replace(',', '.'))
        if numbers:
            return float(numbers[0]) * 1000
    
    # Millió kinyerése
    numbers = re.findall(r'[\d,]+', price_str.replace(',', '.'))
    if numbers:
        return float(numbers[0])
    
    return np.nan

def extract_area_number(area_str):
    """Terület szövegből szám kinyerése (m²-ben)"""
    if pd.isna(area_str):
        return np.nan
    
    numbers = re.findall(r'\d+', str(area_str))
    if numbers:
        return float(numbers[0])
    
    return np.nan

def extract_sqm_price(sqm_str):
    """M² ár kinyerése"""
    if pd.isna(sqm_str):
        return np.nan
    
    numbers = re.findall(r'[\d ]+', str(sqm_str).replace(' ', ''))
    if numbers:
        return float(numbers[0])
    
    return np.nan

if __name__ == "__main__":
    main()
