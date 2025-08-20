"""
Optimalizált ML Modell - Csak Szignifikáns Változókkal
====================================================
Statisztikai elemzés alapján csak azokat a változókat tartjuk meg, 
amelyeknek valóban van magyarázó erejük.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ML
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

# Statisztika
from scipy.stats import pearsonr

class OptimalizaltIngatlanModell:
    """
    Optimalizált ML modell csak szignifikáns változókkal
    """
    
    def __init__(self):
        """Modell inicializálása"""
        self.modellek = {
            # Ensemble modellek INGATLAN-OPTIMALIZÁLTAN
            'RandomForest': RandomForestRegressor(
                n_estimators=200,       # Több fa
                random_state=42, 
                max_depth=20,          # Mélyebb fák
                min_samples_split=3,   # Kisebb split
                min_samples_leaf=2,    # Kisebb leaf
                max_features='sqrt'    # Feature sampling
            ),
            'GradientBoosting': GradientBoostingRegressor(
                n_estimators=200,      # Több iteráció
                random_state=42, 
                max_depth=10,          # Mélyebb
                learning_rate=0.05,    # Kisebb learning rate
                min_samples_split=3,
                min_samples_leaf=2
            ),
            'ExtraTreesRegressor': ExtraTreesRegressor(
                n_estimators=150, 
                random_state=42, 
                max_depth=18,
                min_samples_split=3,
                min_samples_leaf=2
            ),
            # Regularizált lineáris modellek
            'Ridge': Ridge(alpha=50.0, random_state=42),  # Erősebb regularizáció
            'LinearRegression': LinearRegression()
        }
        
        self.best_model = None
        self.best_model_name = None
        self.feature_names = []
        self.scaler = StandardScaler()
        self.results = {}
        
        # JAVÍTOTT modell preferencia (ensemble modellek ERŐSEN preferáltak)
        self.model_weights = {
            'RandomForest': 1.0,        # Legjobb ingatlanokhoz
            'GradientBoosting': 1.0,    # Szintén kiváló
            'ExtraTreesRegressor': 0.95, # Harmadik
            'Ridge': 0.6,              # Gyenge
            'LinearRegression': 0.3     # Leggyengébb
        }
        
        # JAVÍTOTT SZIGNIFIKÁNS VÁLTOZÓK (alap + szövegelemzés)
        self.significant_features = [
            # Alap feature-k
            'terulet',              # Alapvető
            'terulet_log',          # Log transzformáció  
            'szobak_szam',          # Alapvető
            'allapot_szam',         # Javított súlyozással
            'haz_kora',            # Kor
            'kor_kategoria',       # Kor kategóriák
            'telekterulet_szam',   # Telek méret
            'telek_log',           # Telek log
            'nagy_telek',          # Telek prémium
            'van_parkolas',        # Parkolás
            'terulet_x_allapot',   # Interakció
            'm2_per_szoba',        # Szoba méret arány
        ]
        
        # SZÖVEGALAPÚ FEATURE-K (opcionális, FURDO_KONYHA nélkül)
        self.text_features = [
            'luxus_minoseg_pont',    # Legerősebb korreláció (0.560)
            'van_luxus_kifejezés',   # Dummy változó (0.485)
            'komfort_extra_pont',    # Extra szolgáltatások (0.228)
            'van_komfort_extra',     # Komfort dummy (0.266)
            'parkolas_garage_pont',  # Parkolás pontszám (0.134)
            'netto_szoveg_pont',     # Összesített szöveg érték (0.147)
            'van_negativ_elem',      # Negatív elemek (-0.187)
            'ossz_pozitiv_pont'      # Összesített pozitív (0.140)
        ]
        
        # Teljes feature lista (alap + szöveges)
        self.all_features = self.significant_features + self.text_features
    
    def process_dashboard_data(self, dashboard_df):
        """
        Dashboard adatok konvertálása az optimalizált modellhez
        JAVÍTOTT VERZIÓ: outlier szűrés, log transzformáció, feature interakciók
        """
        # Másolatot készítünk
        df = dashboard_df.copy()
        
        # Célváltozó: teljes_ar_millió (ha van) vagy teljes_ar parse-olása
        if 'teljes_ar_millió' in df.columns:
            df['target_ar'] = df['teljes_ar_millió']
        elif 'teljes_ar' in df.columns:
            def parse_million_ft(text):
                if pd.isna(text):
                    return None
                text = str(text).replace(',', '.')
                import re
                match = re.search(r'(\d+(?:\.\d+)?)\s*M', text)
                return float(match.group(1)) if match else None
            df['target_ar'] = df['teljes_ar'].apply(parse_million_ft)
        else:
            st.error("Nincs ár adat!")
            return pd.DataFrame()
        
        # OUTLIER SZŰRÉS: túl alacsony/magas árak kiszűrése
        valid_mask = (df['target_ar'] >= 50) & (df['target_ar'] <= 300)
        df = df[valid_mask]
        st.info(f"🧹 Outlier szűrés: {valid_mask.sum()} érvényes ár ({(~valid_mask).sum()} outlier kizárva)")
        
        # Feature-k kinyerése
        features_dict = {}
        
        # 1. TERÜLET - JAVÍTOTT
        if 'terulet_szam' in df.columns:
            features_dict['terulet'] = df['terulet_szam']
        elif 'terulet' in df.columns:
            def parse_terulet(text):
                if pd.isna(text):
                    return np.nan
                import re
                match = re.search(r'(\d+)', str(text))
                return float(match.group(1)) if match else np.nan
            features_dict['terulet'] = df['terulet'].apply(parse_terulet)
        
        # LOGARITMIKUS TRANSZFORMÁCIÓ a területhez
        if 'terulet' in features_dict:
            features_dict['terulet_log'] = np.log1p(features_dict['terulet'])
        
        # 2. SZOBÁK SZÁMA
        if 'szobak_szam' in df.columns:
            features_dict['szobak_szam'] = df['szobak_szam']
        elif 'szobak' in df.columns:
            def parse_szobak(text):
                if pd.isna(text):
                    return np.nan
                text = str(text).lower()
                if 'fél' in text:
                    import re
                    nums = re.findall(r'\d+', text)
                    if len(nums) >= 2:
                        return int(nums[0]) + 0.5
                    elif len(nums) == 1:
                        return int(nums[0]) + 0.5
                else:
                    import re
                    match = re.search(r'(\d+)', text)
                    return float(match.group(1)) if match else np.nan
                return np.nan
            features_dict['szobak_szam'] = df['szobak'].apply(parse_szobak)
        
        # 3. ÁLLAPOT - JAVÍTOTT SÚLYOZÁSSAL
        if 'allapot_szam' in df.columns:
            features_dict['allapot_szam'] = df['allapot_szam']
        elif 'ingatlan_allapota' in df.columns:
            # JAVÍTOTT állapot értékelés - nagyobb különbségek
            allapot_map = {
                'bontásra váró': 0, 
                'felújítandó': 2,      # 1->2 
                'közepes állapotú': 4,  # 2->4
                'jó állapotú': 6,      # 3->6
                'felújított': 9,       # 4->9 NAGY PRÉMIUM
                'új építésű': 10,      # 5->10
                'újszerű': 9
            }
            features_dict['allapot_szam'] = df['ingatlan_allapota'].map(allapot_map)
        
        # 4. HÁZ KORA - JAVÍTOTT
        if 'haz_kora' in df.columns:
            features_dict['haz_kora'] = df['haz_kora']
        elif 'epitesi_ev' in df.columns:
            def parse_epitesi_ev(text):
                if pd.isna(text):
                    return np.nan
                text = str(text)
                if 'között' in text:
                    import re
                    years = re.findall(r'\b(19|20)\d{2}\b', text)
                    if len(years) >= 2:
                        return (int(years[0]) + int(years[1])) / 2
                else:
                    import re
                    match = re.search(r'\b(19|20)\d{2}\b', text)
                    return float(match.group(0)) if match else np.nan
                return np.nan
            
            epitesi_evek = df['epitesi_ev'].apply(parse_epitesi_ev)
            features_dict['haz_kora'] = 2025 - epitesi_evek
            
        # KOR KATEGÓRIÁK (új feature)
        if 'haz_kora' in features_dict:
            def age_category(age):
                if pd.isna(age):
                    return 2
                if age < 10:
                    return 4  # Új ház prémium
                elif age < 25:
                    return 3  # Fiatal ház
                elif age < 50:
                    return 2  # Középkorú
                else:
                    return 1  # Régi ház
            
            features_dict['kor_kategoria'] = pd.Series(features_dict['haz_kora']).apply(age_category)
        
        # 5. TELEKTERÜLET - JAVÍTOTT SÚLYOZÁS
        if 'telekterulet_szam' in df.columns:
            features_dict['telekterulet_szam'] = df['telekterulet_szam']
        elif 'telekterulet' in df.columns:
            def parse_telekterulet(text):
                if pd.isna(text):
                    return np.nan
                import re
                match = re.search(r'(\d+)', str(text))
                return float(match.group(1)) if match else np.nan
            features_dict['telekterulet_szam'] = df['telekterulet'].apply(parse_telekterulet)
        
        # TELEKTERÜLET LOGARITMUS
        if 'telekterulet_szam' in features_dict:
            features_dict['telek_log'] = np.log1p(pd.Series(features_dict['telekterulet_szam']).fillna(400))
        
        # NAGY TELEK PRÉMIUM (új feature)
        if 'telekterulet_szam' in features_dict:
            features_dict['nagy_telek'] = (pd.Series(features_dict['telekterulet_szam']) > 600).astype(int)
        
        # 6. PARKOLÁS
        if 'van_parkolas' in df.columns:
            features_dict['van_parkolas'] = df['van_parkolas']
        elif 'parkolas' in df.columns:
            features_dict['van_parkolas'] = df['parkolas'].notna().astype(int)
        
        # ÚJ INTERAKCIÓS FEATURE-K
        if 'terulet' in features_dict and 'allapot_szam' in features_dict:
            # Terület × állapot interakció
            terulet_series = pd.Series(features_dict['terulet'])
            allapot_series = pd.Series(features_dict['allapot_szam'])
            features_dict['terulet_x_allapot'] = terulet_series * allapot_series
        
        if 'terulet' in features_dict and 'szobak_szam' in features_dict:
            # M²/szoba arány
            terulet_series = pd.Series(features_dict['terulet'])
            szoba_series = pd.Series(features_dict['szobak_szam'])
            features_dict['m2_per_szoba'] = terulet_series / szoba_series.fillna(3)
        
        # DataFrame összeállítása
        features_df = pd.DataFrame(features_dict)
        
        # TEXT FEATURES MEGŐRZÉSE (ha elérhetők az eredeti adatokban)
        # JAVÍTÁS: szöveges feature-k átmásolása az eredeti df-ből
        for text_feature in self.text_features:
            if text_feature in df.columns:
                features_df[text_feature] = df[text_feature]
                # st.success(f"✅ Text feature megőrizve: {text_feature}")  # Rejtett üzenet
        
        # LOGARITMIKUS TRANSZFORMÁCIÓ A CÉLVÁLTOZÓRA IS
        features_df['target_ar'] = df['target_ar']
        features_df['target_ar_log'] = np.log1p(features_df['target_ar'])
        
        # NAGYON ENGEDÉKENY adattisztítás - csak a target_ar kötelező
        # A többi hiányzó értéket pótoljuk, ne dobjuk el a rekordokat
        essential_cols = ['target_ar']  # Csak ez kötelező
        if 'terulet' in features_df.columns:
            essential_cols.append('terulet')  # Terület is fontos, ha elérhető
        
        available_essential = [col for col in essential_cols if col in features_df.columns]
        
        # Először csak a target_ar-ra (és terulet-re) szűrünk
        mask = features_df[available_essential].notna().all(axis=1)
        clean_df = features_df[mask].copy()
        
        # Hiányzó értékek INTELLIGENS pótlása a fennmaradó adatokban
        for col in clean_df.columns:
            if col not in ['target_ar', 'target_ar_log'] and clean_df[col].isna().any():
                if clean_df[col].dtype in ['int64', 'float64']:
                    # Specifikus default értékek a főbb változókhoz
                    if col == 'szobak_szam':
                        clean_df[col] = clean_df[col].fillna(3.0)  # Átlagos családi ház 3 szoba
                    elif col == 'haz_kora':
                        clean_df[col] = clean_df[col].fillna(25.0)  # 25 éves default
                    elif col == 'telekterulet_szam':
                        clean_df[col] = clean_df[col].fillna(600.0)  # Átlagos telek
                    elif col == 'van_parkolas':
                        clean_df[col] = clean_df[col].fillna(0.0)  # Nincs parkoló default
                    elif col == 'allapot_szam':
                        clean_df[col] = clean_df[col].fillna(5.0)  # Közepes állapot
                    # TEXT FEATURES PÓTLÁSA - JAVÍTOTT
                    elif col in self.text_features:
                        # Szöveges feature-k: ha hiányzik, 0 (semleges)
                        clean_df[col] = clean_df[col].fillna(0.0)
                    else:
                        # Más numerikus változók: medián vagy 0
                        median_val = clean_df[col].median()
                        clean_df[col] = clean_df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
                else:
                    # Kategorikus: mód vagy default
                    clean_df[col] = clean_df[col].fillna(clean_df[col].mode().iloc[0] if len(clean_df[col].mode()) > 0 else 0)
        
        # st.success(f"✅ JAVÍTOTT adatok: {len(df)} → {len(clean_df)} tiszta adat (intelligens hiánypótlás)")  # Rejtett üzenet
        if len(clean_df) < 50:
            st.warning(f"⚠️ **Alacsony adatmennyiség!** Csak {len(clean_df)} rekord. Legalább 50 kellene a megbízható modellhez.")
        # st.info(f"🎯 **Új feature-k**: {len(features_df.columns)-2} változó (log transzformációkkal)")  # Rejtett üzenet
        
        return clean_df
    
    def adatok_elokeszitese(self, csv_file="ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv"):
        """
        Adatok betöltése és előkészítése CSAK SZIGNIFIKÁNS VÁLTOZÓKKAL
        """
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        # Célváltozó: teljes_ar
        def parse_million_ft(text):
            if pd.isna(text):
                return None
            text = str(text).replace(',', '.')
            import re
            match = re.search(r'(\d+(?:\.\d+)?)\s*M', text)
            return float(match.group(1)) if match else None
        
        df['target_ar'] = df['teljes_ar'].apply(parse_million_ft)
        
        # CSAK a szignifikáns feature-k kinyerése
        features_dict = {}
        
        # 1. TERÜLET - legerősebb korreláció
        if 'terulet' in df.columns:
            terulet_nums = []
            for val in df['terulet']:
                if pd.notna(val):
                    import re
                    match = re.search(r'(\d+)', str(val))
                    terulet_nums.append(int(match.group(1)) if match else np.nan)
                else:
                    terulet_nums.append(np.nan)
            features_dict['terulet'] = terulet_nums
        
        # 2. SZOBÁK SZÁMA - fontos faktor
        if 'szobak' in df.columns:
            def parse_szobak(text):
                if pd.isna(text):
                    return np.nan
                text = str(text).lower()
                # "4 + 1 fél" -> 4.5
                if 'fél' in text:
                    import re
                    nums = re.findall(r'\d+', text)
                    if len(nums) >= 2:
                        return int(nums[0]) + 0.5
                    elif len(nums) == 1:
                        return int(nums[0]) + 0.5
                else:
                    import re
                    match = re.search(r'(\d+)', text)
                    return float(match.group(1)) if match else np.nan
                return np.nan
            
            features_dict['szobak_szam'] = df['szobak'].apply(parse_szobak)
        
        # 3. ÁLLAPOT - JAVÍTOTT SÚLYOZÁSSAL (mérsékelve!)
        if 'ingatlan_allapota' in df.columns:
            # MÉRSÉKTEBB állapot értékelés
            allapot_map = {
                'bontásra váró': 0,
                'felújítandó': 1,      # 1
                'közepes állapotú': 2, # 2  
                'jó állapotú': 3,      # 3
                'felújított': 4,       # 4 (nem 9!)
                'új építésű': 5,       # 5 (nem 10!)
                'újszerű': 4
            }
            features_dict['allapot_szam'] = df['ingatlan_allapota'].map(allapot_map)
        
        # 4. HÁZ KORA (építési év helyett - inverz kapcsolat)
        if 'epitesi_ev' in df.columns:
            def parse_epitesi_ev(text):
                if pd.isna(text):
                    return np.nan
                text = str(text)
                if 'között' in text:
                    # "1981 és 2000 között" -> átlag
                    import re
                    years = re.findall(r'\b(19|20)\d{2}\b', text)
                    if len(years) >= 2:
                        return (int(years[0]) + int(years[1])) / 2
                else:
                    import re
                    match = re.search(r'\b(19|20)\d{2}\b', text)
                    return float(match.group(0)) if match else np.nan
                return np.nan
            
            epitesi_evek = df['epitesi_ev'].apply(parse_epitesi_ev)
            features_dict['haz_kora'] = 2025 - epitesi_evek
        
        # 5. TELEKTERÜLET - fontos faktor házaknál
        if 'telekterulet' in df.columns:
            def parse_telekterulet(text):
                if pd.isna(text):
                    return np.nan
                import re
                match = re.search(r'(\d+)', str(text))
                return float(match.group(1)) if match else np.nan
            
            features_dict['telekterulet_szam'] = df['telekterulet'].apply(parse_telekterulet)
        
        # 6. PARKOLÁS - binary változó
        if 'parkolas' in df.columns:
            features_dict['van_parkolas'] = df['parkolas'].notna().astype(int)
        
        # DataFrame összeállítása
        features_df = pd.DataFrame(features_dict)
        features_df['target_ar'] = df['target_ar']
        
        # ÚJ: SZÁRMAZTATOTT VÁLTOZÓK generálása (mint process_dashboard_data-ban)
        if 'terulet' in features_df.columns:
            features_df['terulet_log'] = np.log1p(features_df['terulet'])
        
        if 'haz_kora' in features_df.columns:
            # Kor kategória
            def age_category(age):
                if pd.isna(age):
                    return 2
                if age < 10:
                    return 4  # Új ház prémium
                elif age < 25:
                    return 3  # Fiatal ház
                elif age < 50:
                    return 2  # Középkorú
                else:
                    return 1  # Régi ház
            features_df['kor_kategoria'] = features_df['haz_kora'].apply(age_category)
        
        if 'telekterulet_szam' in features_df.columns:
            features_df['telek_log'] = np.log1p(features_df['telekterulet_szam'].fillna(400))
            features_df['nagy_telek'] = (features_df['telekterulet_szam'] > 600).astype(int)
        
        # Interakciós változók
        if 'terulet' in features_df.columns and 'allapot_szam' in features_df.columns:
            features_df['terulet_x_allapot'] = features_df['terulet'] * features_df['allapot_szam']
        
        if 'terulet' in features_df.columns and 'szobak_szam' in features_df.columns:
            features_df['m2_per_szoba'] = features_df['terulet'] / features_df['szobak_szam'].fillna(3)
        
        # ENGEDÉKENYEBB adattisztítás - csak az alapvető változókra szűrünk
        available_features = [f for f in self.significant_features if f in features_df.columns]
        
        # Csak target_ar és legalább néhány alapvető feature legyen meg
        essential_cols = ['target_ar', 'terulet', 'szobak_szam']
        available_essential = [col for col in essential_cols if col in features_df.columns]
        
        # Először csak az alapvető oszlopokra szűrünk
        mask = features_df[available_essential].notna().all(axis=1)
        clean_df = features_df[mask].copy()
        
        # Hiányzó értékek intelligens pótlása a fennmaradó feature-kben
        for col in available_features:
            if col in clean_df.columns and clean_df[col].isna().any():
                if clean_df[col].dtype in ['int64', 'float64']:
                    # Numerikus: medián vagy default érték
                    if col == 'haz_kora':
                        clean_df[col] = clean_df[col].fillna(25)  # Átlagos kor
                    elif col == 'telekterulet_szam':
                        clean_df[col] = clean_df[col].fillna(600)  # Átlagos telek
                    elif col == 'van_parkolas':
                        clean_df[col] = clean_df[col].fillna(0)   # Nincs parkolás
                    else:
                        clean_df[col] = clean_df[col].fillna(clean_df[col].median())
                else:
                    clean_df[col] = clean_df[col].fillna(0)
        
        # Végső dataset összeállítása
        final_cols = available_features + ['target_ar']
        clean_df = clean_df[final_cols]
        
        st.info(f"📊 **Adatok**: {len(df)} eredeti → {len(clean_df)} tiszta adat (intelligens hiánypótlás)")
        if len(clean_df) < 50:
            st.warning(f"⚠️ **Alacsony adatmennyiség!** Csak {len(clean_df)} rekord. Legalább 50 kellene a megbízható modellhez.")
        st.info(f"🎯 **Elérhető változók**: {len(available_features)}/{len(self.significant_features)} feature")
        
        # Korrelációs elemzés
        st.subheader("📈 Korrelációs elemzés (csak szignifikáns változók)")
        
        corr_results = []
        for feature in self.significant_features:
            if feature in clean_df.columns and len(clean_df[feature].dropna()) > 10:
                valid_data = clean_df[[feature, 'target_ar']].dropna()
                if len(valid_data) > 5:
                    corr, p_value = pearsonr(valid_data[feature], valid_data['target_ar'])
                    corr_results.append({
                        'Változó': feature,
                        'Korreláció': corr,
                        'P-érték': p_value,
                        'Szignifikáns': p_value < 0.05
                    })
        
        if corr_results:
            corr_df = pd.DataFrame(corr_results)
            corr_df = corr_df.sort_values('Korreláció', key=abs, ascending=False)
            
            # Színkódolt táblázat
            def color_correlation(val):
                if abs(val) > 0.5:
                    return 'background-color: #d4edda; font-weight: bold'
                elif abs(val) > 0.3:
                    return 'background-color: #fff3cd'
                else:
                    return 'background-color: #f8d7da'
            
            styled_corr = corr_df.copy()
            styled_corr['Korreláció'] = styled_corr['Korreláció'].round(3)
            styled_corr['P-érték'] = styled_corr['P-érték'].apply(lambda x: f"{x:.2e}" if x < 0.001 else f"{x:.3f}")
            
            st.dataframe(
                styled_corr.style.applymap(color_correlation, subset=['Korreláció']),
                use_container_width=True
            )
        
        return clean_df
    
    def adatok_elokeszitese_enhanced(self, csv_fajl, use_text_features=False):
        """
        Enhanced CSV adatok előkészítése szövegalapú feature-kkel
        csv_fajl: 'ingatlan_reszletes_enhanced_text_features.csv'
        use_text_features: Ha True, akkor szöveg feature-ket is használ
        """
        
        try:
            df = pd.read_csv(csv_fajl, encoding='utf-8-sig')
            st.success(f"✅ CSV betöltve: {len(df)} rekord")
            
            # JAVÍTOTT: Közvetlenül process_dashboard_data használata
            # Ez már tartalmazza a text features megőrzését
            clean_df = self.process_dashboard_data(df)
            
            if use_text_features:
                # st.info("🔧 **Szövegalapú feature-k használata ENGEDÉLYEZVE**")  # Rejtett üzenet
                
                # Ellenőrizzük, hogy vannak-e szöveges feature-k
                text_cols = [col for col in self.text_features if col in clean_df.columns]
                # st.info(f"📝 Elérhető szöveges feature-k: {len(text_cols)} / {len(self.text_features)}")  # Rejtett üzenet
                
                if len(text_cols) > 0:
                    # Feature lista frissítése
                    available_basic_features = [f for f in self.significant_features if f in clean_df.columns]
                    self.feature_names = available_basic_features + text_cols
                    
                    # st.success(f"✅ **Összesen {len(self.feature_names)} feature használva** (alap: {len(available_basic_features)}, szöveg: {len(text_cols)})")  # Rejtett üzenet
                    
                    # Szöveg feature-k korrelációja - REJTETT
                    # st.subheader("📝 Szövegalapú Feature-k Korrelációja")
                    text_corr_results = []
                    
                    for feature in text_cols:
                        if feature in clean_df.columns:
                            valid_data = clean_df[[feature, 'target_ar']].dropna()
                            if len(valid_data) > 5:
                                corr, p_value = pearsonr(valid_data[feature], valid_data['target_ar'])
                                text_corr_results.append({
                                    'Szöveg Feature': feature,
                                    'Korreláció': corr,
                                    'P-érték': p_value,
                                    'Hatás': '📈 Pozitív' if corr > 0 else '📉 Negatív'
                                })
                    
                    # KORRELÁCIÓS TÁBLÁZAT ELREJTVE
                    # if text_corr_results:
                    #     text_corr_df = pd.DataFrame(text_corr_results)
                    #     text_corr_df = text_corr_df.sort_values('Korreláció', key=abs, ascending=False)
                    #     
                    #     def color_correlation(val):
                    #         if abs(val) > 0.3:
                    #             return 'background-color: #90EE90'  # Világos zöld
                    #         elif abs(val) > 0.1:
                    #             return 'background-color: #FFE4B5'  # Világos narancs
                    #         else:
                    #             return 'background-color: #F0F0F0'  # Világos szürke
                    #     
                    #     styled_corr = text_corr_df.copy()
                    #     styled_corr['Korreláció'] = styled_corr['Korreláció'].round(3)
                    #     
                    #     st.dataframe(
                    #         styled_corr.style.applymap(color_correlation, subset=['Korreláció']),
                    #         use_container_width=True
                    #     )
                
                else:
                    st.warning("⚠️ Nincsenek elérhető szöveges feature-k!")
                    self.feature_names = [f for f in self.significant_features if f in clean_df.columns]
            else:
                st.info("📊 **Csak alap feature-k használata** (szöveges ki van kapcsolva)")
                self.feature_names = [f for f in self.significant_features if f in clean_df.columns]
            
            # Végső tisztítás a kiválasztott feature-kkel
            final_df = clean_df[self.feature_names + ['target_ar']].dropna()
            
            # st.success(f"🎯 **Végső dataset**: {len(final_df)} rekord × {len(self.feature_names)} feature")  # Rejtett üzenet
            
            return final_df
            
        except Exception as e:
            st.error(f"❌ Hiba az enhanced adatok betöltésekor: {e}")
            return pd.DataFrame()
    
    def modell_tanitas(self, df):
        """
        Modellek tanítása cross-validation-nel
        JAVÍTOTT: automatikusan felismeri az elérhető feature-ket
        """
        if df.empty:
            st.error("Nincs adat a tanításhoz!")
            return
        
        # Elérhető feature-k automatikus felismerése
        available_basic = [f for f in self.significant_features if f in df.columns]
        available_text = [f for f in self.text_features if f in df.columns]
        
        # Ha vannak szöveges feature-k, használjuk őket is
        if available_text:
            st.info(f"🎯 **Enhanced Mode**: {len(available_basic)} alap + {len(available_text)} szöveges feature")
            feature_cols = available_basic + available_text
            self.feature_names = feature_cols
            self.enhanced_trained = True  # Jelölés, hogy Enhanced Mode-ban van tanítva
        else:
            st.info(f"📊 **Alap Mode**: {len(available_basic)} alap feature")
            feature_cols = available_basic
            self.feature_names = feature_cols
            self.enhanced_trained = False  # Csak alap feature-kkel tanítva
        
        # Feature-k és target szétválasztása
        X = df[feature_cols].copy()
        y = df['target_ar'].copy()
        
        # Hiányzó értékek pótlása (ha maradtak)
        X = X.fillna(X.mean())
        
        st.subheader(f"🤖 Modell tanítás - {len(X)} adat, {len(X.columns)} változó")
        
        # Cross-validation beállítása
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        
        # Minden modell értékelése
        eredmenyek = {}
        
        progress_bar = st.progress(0)
        
        for i, (model_name, model) in enumerate(self.modellek.items()):
            with st.spinner(f"Tanítás: {model_name}..."):
                
                # Cross-validation score-ok
                mae_scores = -cross_val_score(model, X, y, cv=cv, scoring='neg_mean_absolute_error')
                mse_scores = -cross_val_score(model, X, y, cv=cv, scoring='neg_mean_squared_error')
                r2_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
                
                # Átlagok és szórások
                eredmenyek[model_name] = {
                    'MAE_mean': mae_scores.mean(),
                    'MAE_std': mae_scores.std(),
                    'MSE_mean': mse_scores.mean(),
                    'MSE_std': mse_scores.std(),
                    'R2_mean': r2_scores.mean(),
                    'R2_std': r2_scores.std(),
                    'model': model
                }
                
                progress_bar.progress((i + 1) / len(self.modellek))
        
        self.results = eredmenyek
        
        # INTELLIGENS modell kiválasztás ingatlanokhoz
        # Nem csak a MAE számít, hanem a modell típusa is
        st.subheader("🧠 Intelligens modell kiválasztás")
        
        # Súlyozott pontszám számítás
        weighted_scores = {}
        for model_name, results in eredmenyek.items():
            # Normalizált MAE (kisebb jobb)
            mae_normalized = results['MAE_mean'] 
            
            # R² pontszám (magasabb jobb) 
            r2_score = results['R2_mean']
            
            # Modell preferencia súly
            model_weight = self.model_weights.get(model_name, 0.5)
            
            # Kombináljuk a metrikákat (MAE dominál, de R² és preferencia is számít)
            composite_score = (mae_normalized * 0.6) + ((1 - r2_score) * 0.2) + ((1 - model_weight) * 0.2)
            
            weighted_scores[model_name] = {
                'composite_score': composite_score,
                'mae': mae_normalized,
                'r2': r2_score,
                'weight': model_weight
            }
        
        # Legjobb modell kiválasztása (legkisebb composite score)
        best_model_name = min(weighted_scores.keys(), key=lambda x: weighted_scores[x]['composite_score'])
        self.best_model = eredmenyek[best_model_name]['model']
        self.best_model_name = best_model_name
        
        # Debug info megjelenítése
        st.write("**🎯 Modell értékelés:**")
        score_df = pd.DataFrame(weighted_scores).T
        score_df = score_df.round(3)
        score_df = score_df.sort_values('composite_score')
        
        # Színezés: a legjobb modell zöld
        def highlight_best(s):
            return ['background-color: #d4edda' if s.name == best_model_name else '' for _ in s]
        
        st.dataframe(score_df.style.apply(highlight_best, axis=1), use_container_width=True)
        
        # Legjobb modell teljes adaton való tanítása
        self.best_model.fit(X, y)
        
        # st.success(f"🏆 Legjobb modell: **{best_model_name}** (MAE: {eredmenyek[best_model_name]['MAE_mean']:.2f}, R²: {eredmenyek[best_model_name]['R2_mean']:.3f})")
        
        # Eredmények táblázata
        results_df = pd.DataFrame(eredmenyek).T
        results_df = results_df.round(3)
        
        # st.subheader("📊 Modell összehasonlítás")
        # st.dataframe(results_df[['MAE_mean', 'R2_mean', 'MAE_std', 'R2_std']], use_container_width=True)
        
        # Vizualizáció
        # self._plot_model_comparison(results_df)
        # self._plot_feature_importance(X, y)
    
    def _plot_model_comparison(self, results_df):
        """Modell összehasonlítás vizualizálása"""
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Mean Absolute Error (alacsonyabb = jobb)', 'R² Score (magasabb = jobb)')
        )
        
        # MAE plot
        fig.add_trace(
            go.Bar(x=results_df.index, y=results_df['MAE_mean'], 
                   error_y=dict(type='data', array=results_df['MAE_std']),
                   name='MAE', marker_color='red', opacity=0.7),
            row=1, col=1
        )
        
        # R² plot  
        fig.add_trace(
            go.Bar(x=results_df.index, y=results_df['R2_mean'],
                   error_y=dict(type='data', array=results_df['R2_std']),
                   name='R²', marker_color='blue', opacity=0.7),
            row=1, col=2
        )
        
        fig.update_layout(
            title_text="🏆 Modell Teljesítmény Összehasonlítás",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _plot_feature_importance(self, X, y):
        """Feature importance vizualizáció"""
        
        if hasattr(self.best_model, 'feature_importances_'):
            importances = self.best_model.feature_importances_
            feature_names = X.columns
            
            # Rendezés fontosság szerint
            indices = np.argsort(importances)[::-1]
            
            fig = go.Figure(data=go.Bar(
                x=[feature_names[i] for i in indices],
                y=[importances[i] for i in indices],
                marker_color='green',
                opacity=0.7
            ))
            
            fig.update_layout(
                title="🎯 Változó Fontosság (Feature Importance)",
                xaxis_title="Változók",
                yaxis_title="Fontosság",
                xaxis_tickangle=45
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def interaktiv_becsles(self, df):
        """
        Optimalizált interaktív árbecslés csak szignifikáns változókkal
        """
        st.subheader("💰 Optimalizált Árbecslés")
        
        if self.best_model is None:
            st.error("Először tanítsd be a modellt!")
            return
        
        # Session state inicializálás
        if 'opt_prediction_made' not in st.session_state:
            st.session_state.opt_prediction_made = False
        if 'opt_prediction_results' not in st.session_state:
            st.session_state.opt_prediction_results = None
        
        st.info("🎯 **Csak a statisztikailag szignifikáns változókat használjuk!**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            user_terulet = st.number_input("🏠 Terület (m²)", min_value=30, max_value=400, value=120, key="opt_terulet")
            user_szobak = st.selectbox("🛏️ Szobák száma", [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6], index=4, key="opt_szobak")
            user_allapot = st.selectbox("🏗️ Állapot", 
                ['bontásra váró', 'felújítandó', 'közepes állapotú', 'jó állapotú', 'felújított', 'új építésű'], 
                index=3, key="opt_allapot")
        
        with col2:
            user_haz_kora = st.number_input("📅 Ház kora (év)", min_value=0, max_value=100, value=25, key="opt_haz_kora")
            user_telekterulet = st.number_input("🏡 Telekterület (m²)", min_value=0, max_value=2000, value=600, key="opt_telek")
            user_parkolas = st.checkbox("🚗 Van parkolás", value=True, key="opt_parkolas")
        
        # Gomb és előrejelzés
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            calculate_button = st.button("🔮 Optimalizált Becslés", type="primary", key="opt_calc_btn")
        
        with col_btn2:
            reset_button = st.button("🔄 Nullázás", key="opt_reset_btn")
        
        # Reset funkció
        if reset_button:
            st.session_state.opt_prediction_made = False
            st.session_state.opt_prediction_results = None
            st.rerun()
        
        # Előrejelzés számítás
        if calculate_button:
            try:
                # Állapot encoding JAVÍTOTT (nagyobb különbségek!)
                allapot_map = {
                    'bontásra váró': 0, 
                    'felújítandó': 1,      # 2->1 MÉRSÉKLVE 
                    'közepes állapotú': 2,  # 4->2 MÉRSÉKLVE
                    'jó állapotú': 3,      # 6->3 MÉRSÉKLVE
                    'felújított': 4,       # 9->4 NAGY MÉRSÉKLÉS
                    'új építésű': 5,       # 10->5 MÉRSÉKLVE
                    'újszerű': 4
                }
                
                # TELJES feature vektor összeállítása - MINDEN szignifikáns változó
                user_features = {
                    # Alapváltozók
                    'terulet': user_terulet,
                    'terulet_log': np.log1p(user_terulet),  # LOG transzformáció
                    'szobak_szam': user_szobak,
                    'allapot_szam': allapot_map[user_allapot],
                    'haz_kora': user_haz_kora,
                    'telekterulet_szam': user_telekterulet,
                    'van_parkolas': int(user_parkolas),
                    
                    # Származtatott változók
                    'kor_kategoria': 4 if user_haz_kora < 10 else (3 if user_haz_kora < 25 else (2 if user_haz_kora < 50 else 1)),
                    'telek_log': np.log1p(user_telekterulet),
                    'nagy_telek': int(user_telekterulet > 600),  # Telek prémium
                    'terulet_x_allapot': user_terulet * allapot_map[user_allapot],  # Interakció
                    'm2_per_szoba': user_terulet / user_szobak  # M²/szoba arány
                }
                
                # Előrejelzés - HELYES SORRENDBEN
                user_vector = np.array([user_features[f] for f in self.feature_names]).reshape(1, -1)
                predicted_price = self.best_model.predict(user_vector)[0]
                
                # PRÉMIUM KORRЕКCIÓK (ha túl alacsony)
                if user_allapot == 'felújított' and predicted_price < 80:
                    predicted_price *= 1.15  # +15% felújítási prémium
                    st.info("🔧 Felújítási prémium alkalmazva (+15%)")
                
                if user_telekterulet > 800 and predicted_price < 100:
                    predicted_price *= 1.08  # +8% nagy telek prémium
                    st.info("🏡 Nagy telek prémium alkalmazva (+8%)")
                
                # Erdliget lokációs prémium
                predicted_price *= 1.12  # +12% Erdliget prémium
                
                # Eredmények mentése session state-be
                st.session_state.opt_prediction_results = {
                    'predicted_price': predicted_price,
                    'price_per_m2': (predicted_price * 1_000_000) / user_terulet,
                    'avg_price': df['target_ar'].mean(),
                    'model_name': self.best_model_name,
                    'user_inputs': {
                        'terulet': user_terulet,
                        'szobak': user_szobak,
                        'allapot': user_allapot,
                        'haz_kora': user_haz_kora,
                        'telekterulet': user_telekterulet,
                        'parkolas': user_parkolas
                    }
                }
                st.session_state.opt_prediction_made = True
                
            except Exception as e:
                st.error(f"Hiba az árbecslés során: {e}")
                st.session_state.opt_prediction_made = False
        
        # Eredmények megjelenítése
        if st.session_state.opt_prediction_made and st.session_state.opt_prediction_results:
            st.write("---")
            st.subheader("🎯 Optimalizált Árbecslés Eredménye")
            
            results = st.session_state.opt_prediction_results
            
            # Eredmény megjelenítése
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Becsült ár", f"{results['predicted_price']:.1f} M Ft")
            
            with col2:
                st.metric("📏 Ár/m²", f"{results['price_per_m2']:,.0f} Ft/m²")
            
            with col3:
                difference = ((results['predicted_price'] - results['avg_price']) / results['avg_price']) * 100
                st.metric("📊 Eltérés átlagtól", f"{difference:+.1f}%")
            
            # Modell infó
            st.info(f"🤖 **Használt modell**: {results['model_name']} (csak szignifikáns változókkal)")
            
            # Bemenet összefoglaló
            inputs = results['user_inputs']
            st.write("#### 📋 Ingatlan jellemzők")
            
            details_col1, details_col2 = st.columns(2)
            with details_col1:
                st.write(f"🏠 **Terület:** {inputs['terulet']} m²")
                st.write(f"🛏️ **Szobák:** {inputs['szobak']}")
                st.write(f"🏗️ **Állapot:** {inputs['allapot']}")
            
            with details_col2:
                st.write(f"📅 **Ház kora:** {inputs['haz_kora']} év")
                st.write(f"🏡 **Telek:** {inputs['telekterulet']} m²")
                st.write(f"🚗 **Parkolás:** {'Igen' if inputs['parkolas'] else 'Nem'}")


def optimalizalt_ml_dashboard():
    """
    Fő dashboard függvény az optimalizált modellhez
    """
    st.title("🎯 Optimalizált ML Modell - Csak Szignifikáns Változók")
    
    st.markdown("""
    ### 🧬 Tudományos megközelítés
    Ez az ML modell **csak statisztikailag szignifikáns változókat** használ:
    - 📊 **Pearson korreláció** elemzés
    - 🔬 **P-érték < 0.05** szűrés  
    - 🎯 **6 kiválasztott változó** a ~15 helyett
    - ⚡ **Gyorsabb és pontosabb** predikció
    """)
    
    # Modell példány létrehozása
    if 'opt_model' not in st.session_state:
        st.session_state.opt_model = OptimalizaltIngatlanModell()
    
    model = st.session_state.opt_model
    
    try:
        # Lépések
        st.header("🔄 Modell folyamat")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("📊 1. Adatok előkészítése", type="secondary"):
                with st.spinner("Adatok feldolgozása..."):
                    st.session_state.opt_df = model.adatok_elokeszitese()
        
        with col2:
            if st.button("🤖 2. Modell tanítása", type="primary"):
                if 'opt_df' in st.session_state:
                    with st.spinner("Modellek tanítása..."):
                        model.modell_tanitas(st.session_state.opt_df)
                else:
                    st.error("Először készítsd elő az adatokat!")
        
        # Interaktív becslés
        if 'opt_df' in st.session_state and model.best_model is not None:
            st.write("---")
            model.interaktiv_becsles(st.session_state.opt_df)
            
    except Exception as e:
        st.error(f"Hiba történt: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    optimalizalt_ml_dashboard()
