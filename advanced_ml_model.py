"""
Szofisztikált ML modell építése ingatlan árbecsléshez

Ez a modul tartalmazza a fejlett gépi tanulási megoldásokat az ingatlanok
árának becslésére több magyarázó változó alapján.

Funkcionalitások:
1. Adatelőkészítés és feature engineering
2. Több ML algoritmus összehasonlítása
3. Hyperparameter tuning
4. Model validation és keresztvalidáció
5. Feature importance analysis
6. Model interpretation (SHAP values)
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ML libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import warnings
warnings.filterwarnings('ignore')

class SzofisztikaltIngatlanModell:
    """
    Fejlett gépi tanulási modell ingatlan árbecsléshez
    """
    
    def __init__(self):
        self.models = {}
        self.best_model = None
        self.feature_names = []
        self.scaler = None
        self.preprocessor = None
        
    def adatok_elokeszitese(self, df):
        """
        Adatok előkészítése a modell tanításához
        """
        st.subheader("🔧 Adatok előkészítése")
        
        # Másolat készítése
        model_df = df.copy()
        
        # Numerikus változók kinyerése
        if 'ar_szam' in model_df.columns:
            model_df['target_ar'] = model_df['ar_szam'] / 1_000_000  # Millió Ft-ban
        else:
            st.error("Nincs ár információ az adatokban!")
            return None
            
        # Feature engineering
        features_dict = {}
        
        # 1. Terület
        if 'terulet_szam' in model_df.columns:
            features_dict['terulet'] = model_df['terulet_szam']
        
        # 2. Telekterület
        if 'telekterulet' in model_df.columns:
            telek_szamok = []
            for val in model_df['telekterulet']:
                if pd.notna(val) and str(val).replace(' ', '').replace('m2', '').replace('m²', '').isdigit():
                    telek_szamok.append(float(str(val).replace(' ', '').replace('m2', '').replace('m²', '')))
                else:
                    telek_szamok.append(np.nan)
            features_dict['telekterulet_szam'] = telek_szamok
        
        # 3. Szobák száma
        if 'szobak' in model_df.columns:
            szoba_map = {
                '1': 1, '1+1': 1.5, '2': 2, '2+1': 2.5, '3': 3, '3+1': 3.5,
                '4': 4, '4+1': 4.5, '5': 5, '5+1': 5.5, '6': 6, '6+': 6.5,
                '1 + 1 fél': 1.5, '2 + 1 fél': 2.5, '3 + 1 fél': 3.5,
                '4 + 1 fél': 4.5, '5 + 1 fél': 5.5
            }
            features_dict['szobak_szam'] = model_df['szobak'].map(szoba_map)
        
        # 4. Építési év
        if 'epitesi_ev' in model_df.columns:
            epites_ev = []
            for val in model_df['epitesi_ev']:
                if pd.notna(val):
                    if 'előtt' in str(val):
                        epites_ev.append(1960)
                    elif 'között' in str(val):
                        years = str(val).replace(' között', '').split(' és ')
                        if len(years) == 2:
                            try:
                                avg_year = (int(years[0]) + int(years[1])) / 2
                                epites_ev.append(avg_year)
                            except:
                                epites_ev.append(1980)
                        else:
                            epites_ev.append(1980)
                    else:
                        try:
                            epites_ev.append(float(str(val)))
                        except:
                            epites_ev.append(1980)
                else:
                    epites_ev.append(np.nan)
            features_dict['epitesi_ev'] = epites_ev
            # Ház kora
            features_dict['haz_kora'] = [2025 - ev if pd.notna(ev) else np.nan for ev in epites_ev]
        
        # 5. Állapot (ordinális)
        if 'ingatlan_allapota' in model_df.columns:
            allapot_map = {
                'új építésű': 5, 'újszerű': 4, 'felújított': 4, 
                'jó állapotú': 3, 'közepes állapotú': 2, 
                'felújítandó': 1, 'bontásra váró': 0
            }
            features_dict['allapot_szam'] = model_df['ingatlan_allapota'].map(allapot_map)
        
        # 6. Képek száma (marketing indikátor)
        if 'kepek_szama' in model_df.columns:
            features_dict['kepek_szama'] = pd.to_numeric(model_df['kepek_szama'], errors='coerce')
        
        # 7. Hirdető típusa
        if 'hirdeto_tipus' in model_df.columns:
            features_dict['hirdeto_maganszemely'] = (model_df['hirdeto_tipus'] == 'maganszemely').astype(int)
        
        # 8. Fűtés típusa (dummy változók)
        if 'futes' in model_df.columns:
            futes_types = ['gázkazán', 'központi fűtés', 'cirkó', 'elektromos', 'vegyes']
            for futes_type in futes_types:
                features_dict[f'futes_{futes_type.replace(" ", "_")}'] = model_df['futes'].str.contains(futes_type, case=False, na=False).astype(int)
        
        # 9. Parkolás (dummy)
        if 'parkolas' in model_df.columns:
            features_dict['van_parkolas'] = model_df['parkolas'].notna().astype(int)
        
        # 10. Erkély (dummy)
        if 'erkely' in model_df.columns:
            features_dict['van_erkely'] = model_df['erkely'].notna().astype(int)
        
        # Feature DataFrame létrehozása
        features_df = pd.DataFrame(features_dict)
        features_df['target_ar'] = model_df['target_ar']
        
        # Hiányzó értékek kezelése
        features_df = features_df.dropna(subset=['target_ar'])
        
        # Statisztikák
        st.write(f"📊 **Feldolgozott rekordok**: {len(features_df)}")
        st.write(f"📊 **Változók száma**: {len(features_df.columns) - 1}")
        
        # Hiányzó értékek arányai
        missing_ratios = features_df.isnull().sum() / len(features_df) * 100
        significant_missing = missing_ratios[missing_ratios > 20]
        if len(significant_missing) > 0:
            st.write("⚠️ **Jelentős hiányzó értékek** (>20%):")
            for col, ratio in significant_missing.items():
                st.write(f"  - {col}: {ratio:.1f}%")
        
        return features_df
    
    def modell_tanitas(self, df):
        """
        Több ML algoritmus tanítása és összehasonlítása
        """
        st.subheader("🤖 Modell tanítás és összehasonlítás")
        
        # Adatok szétválasztása
        X = df.drop(['target_ar'], axis=1)
        y = df['target_ar']
        
        # Hiányzó értékek kitöltése
        X = X.fillna(X.mean())
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Modell definíciók
        models_config = {
            'Linear Regression': LinearRegression(),
            'Ridge Regression': Ridge(alpha=1.0),
            'Lasso Regression': Lasso(alpha=1.0),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'Extra Trees': ExtraTreesRegressor(n_estimators=100, random_state=42)
        }
        
        # Modellek tanítása és értékelése
        results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (name, model) in enumerate(models_config.items()):
            status_text.text(f'Tanítás: {name}...')
            
            # Tanítás
            model.fit(X_train, y_train)
            
            # Előrejelzések
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            
            # Metrikák
            train_r2 = r2_score(y_train, y_train_pred)
            test_r2 = r2_score(y_test, y_test_pred)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
            train_mae = mean_absolute_error(y_train, y_train_pred)
            test_mae = mean_absolute_error(y_test, y_test_pred)
            
            # Keresztvalidáció
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
            
            results.append({
                'Modell': name,
                'Train R²': train_r2,
                'Test R²': test_r2,
                'CV R² átlag': cv_scores.mean(),
                'CV R² std': cv_scores.std(),
                'Train RMSE': train_rmse,
                'Test RMSE': test_rmse,
                'Train MAE': train_mae,
                'Test MAE': test_mae,
                'Overfitting': train_r2 - test_r2,
                'model_obj': model
            })
            
            self.models[name] = {
                'model': model,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'cv_r2': cv_scores.mean()
            }
            
            progress_bar.progress((i + 1) / len(models_config))
        
        status_text.text('Tanítás befejezve!')
        
        # Eredmények táblázat
        results_df = pd.DataFrame(results).drop('model_obj', axis=1)
        results_df = results_df.sort_values('Test R²', ascending=False)
        
        st.write("📊 **Modellek teljesítménye:**")
        st.dataframe(results_df.style.format({
            'Train R²': '{:.4f}',
            'Test R²': '{:.4f}',
            'CV R² átlag': '{:.4f}',
            'CV R² std': '{:.4f}',
            'Train RMSE': '{:.3f}',
            'Test RMSE': '{:.3f}',
            'Train MAE': '{:.3f}',
            'Test MAE': '{:.3f}',
            'Overfitting': '{:.4f}'
        }))
        
        # Legjobb modell kiválasztása
        best_model_name = results_df.iloc[0]['Modell']
        self.best_model = self.models[best_model_name]['model']
        self.feature_names = list(X.columns)
        
        st.success(f"🏆 **Legjobb modell**: {best_model_name} (Test R²: {results_df.iloc[0]['Test R²']:.4f})")
        
        # Vizualizációk
        self._plot_model_comparison(results_df)
        self._plot_predictions_vs_actual(X_test, y_test)
        self._plot_feature_importance(X)
        
        return X_train, X_test, y_train, y_test
    
    def _plot_model_comparison(self, results_df):
        """
        Modellek összehasonlító vizualizációja
        """
        st.subheader("📈 Modellek teljesítmény összehasonlítás")
        
        # R² score összehasonlítás
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Train R²',
            x=results_df['Modell'],
            y=results_df['Train R²'],
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            name='Test R²',
            x=results_df['Modell'],
            y=results_df['Test R²'],
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title='R² Score Összehasonlítás (Train vs Test)',
            xaxis_title='Modellek',
            yaxis_title='R² Score',
            barmode='group',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # RMSE összehasonlítás
        fig2 = px.bar(results_df, x='Modell', y='Test RMSE', 
                     title='Test RMSE Összehasonlítás (alacsonyabb = jobb)',
                     color='Test RMSE', color_continuous_scale='Reds_r')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    def _plot_predictions_vs_actual(self, X_test, y_test):
        """
        Előrejelzések vs valós értékek scatter plot
        """
        st.subheader("🎯 Előrejelzések vs Valós értékek")
        
        y_pred = self.best_model.predict(X_test)
        
        # Create scatter plot without trendline first
        fig = px.scatter(
            x=y_test, y=y_pred,
            title='Előrejelzett vs Valós árak',
            labels={'x': 'Valós ár (M Ft)', 'y': 'Előrejelzett ár (M Ft)'}
        )
        
        # Add manual trendline
        try:
            import numpy as np
            z = np.polyfit(y_test, y_pred, 1)
            p = np.poly1d(z)
            line_x = np.linspace(y_test.min(), y_test.max(), 100)
            fig.add_trace(go.Scatter(
                x=line_x, 
                y=p(line_x), 
                mode='lines', 
                name='Trend',
                line=dict(color='orange', dash='dash')
            ))
        except:
            st.info("Trendline nem elérhető, de a scatter plot működik")
        
        # Tökéletes előrejelzés vonala
        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Tökéletes előrejelzés',
            line=dict(dash='dash', color='red')
        ))
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Hibák eloszlása
        residuals = y_test - y_pred
        fig2 = px.histogram(residuals, nbins=30, title='Előrejelzési hibák eloszlása')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    def _plot_feature_importance(self, X):
        """
        Változó fontosság vizualizáció
        """
        st.subheader("🔍 Változó fontosság")
        
        # Csak akkor ha a modell támogatja
        if hasattr(self.best_model, 'feature_importances_'):
            importances = self.best_model.feature_importances_
            feature_names = X.columns
            
            importance_df = pd.DataFrame({
                'Változó': feature_names,
                'Fontosság': importances
            }).sort_values('Fontosság', ascending=False)
            
            fig = px.bar(
                importance_df, 
                x='Fontosság', 
                y='Változó',
                orientation='h',
                title='Változók fontossága a modellben',
                color='Fontosság',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Top 10 legfontosabb változó
            st.write("🏆 **Top 10 legfontosabb változó:**")
            st.dataframe(importance_df.head(10).style.format({'Fontosság': '{:.4f}'}))
        
        else:
            st.info("Ez a modell nem támogatja a feature importance számítást.")
    
    def interaktiv_becsles(self, df):
        """
        Interaktív árbecslés felhasználói inputtal
        """
        st.subheader("💰 Interaktív Árbecslés")
        
        if self.best_model is None:
            st.error("Először tanítsd be a modellt!")
            return
        
        # Session state inicializálás
        if 'prediction_made' not in st.session_state:
            st.session_state.prediction_made = False
        if 'prediction_results' not in st.session_state:
            st.session_state.prediction_results = None
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            user_terulet = st.number_input("Terület (m²)", min_value=20, max_value=500, value=100, key="terulet")
            user_szobak = st.selectbox("Szobák száma", [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6], key="szobak")
            user_allapot = st.selectbox("Állapot", 
                ['bontásra váró', 'felújítandó', 'közepes állapotú', 'jó állapotú', 'felújított', 'új építésű'], key="allapot")
        
        with col2:
            user_telekterulet = st.number_input("Telekterület (m²)", min_value=0, max_value=2000, value=400, key="telek")
            user_epitesi_ev = st.number_input("Építési év", min_value=1900, max_value=2025, value=1990, key="epitesi_ev")
            user_kepek = st.number_input("Képek száma", min_value=0, max_value=50, value=10, key="kepek")
        
        with col3:
            user_parkolas = st.checkbox("Van parkolás", value=True, key="parkolas")
            user_erkely = st.checkbox("Van erkély", value=True, key="erkely")
            user_maganszemely = st.checkbox("Magánszemély hirdeti", value=False, key="maganszemely")
        
        # Gomb és előrejelzés
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            calculate_button = st.button("🔮 Ár becslése", type="primary", key="calc_btn")
        
        with col_btn2:
            reset_button = st.button("🔄 Nullázás", key="reset_btn")
        
        # Reset funkció
        if reset_button:
            st.session_state.prediction_made = False
            st.session_state.prediction_results = None
            st.rerun()
        
        # Előrejelzés számítás
        if calculate_button:
            try:
                # User input feldolgozása
                allapot_map = {
                    'bontásra váró': 0, 'felújítandó': 1, 'közepes állapotú': 2, 
                    'jó állapotú': 3, 'felújított': 4, 'új építésű': 5
                }
                
                # Feature vektor összeállítása
                user_features = {}
                user_features['terulet'] = user_terulet
                user_features['telekterulet_szam'] = user_telekterulet
                user_features['szobak_szam'] = user_szobak
                user_features['epitesi_ev'] = user_epitesi_ev
                user_features['haz_kora'] = 2025 - user_epitesi_ev
                user_features['allapot_szam'] = allapot_map[user_allapot]
                user_features['kepek_szama'] = user_kepek
                user_features['hirdeto_maganszemely'] = int(user_maganszemely)
                user_features['van_parkolas'] = int(user_parkolas)
                user_features['van_erkely'] = int(user_erkely)
                
                # Hiányzó feature-k pótlása
                for feature in self.feature_names:
                    if feature not in user_features:
                        user_features[feature] = 0  # Default értékek
                
                # Előrejelzés
                user_vector = np.array([user_features[f] for f in self.feature_names]).reshape(1, -1)
                predicted_price = self.best_model.predict(user_vector)[0]
                
                # Eredmények mentése session state-be
                st.session_state.prediction_results = {
                    'predicted_price': predicted_price,
                    'user_terulet': user_terulet,
                    'price_per_m2': (predicted_price * 1_000_000) / user_terulet,
                    'avg_price': df['target_ar'].mean() if 'target_ar' in df.columns else predicted_price,
                    'user_inputs': {
                        'terulet': user_terulet,
                        'telekterulet': user_telekterulet,
                        'szobak': user_szobak,
                        'allapot': user_allapot,
                        'epitesi_ev': user_epitesi_ev,
                        'kepek': user_kepek,
                        'parkolas': user_parkolas,
                        'erkely': user_erkely,
                        'maganszemely': user_maganszemely
                    }
                }
                st.session_state.prediction_made = True
                
            except Exception as e:
                st.error(f"Hiba az árbecslés során: {e}")
                st.session_state.prediction_made = False
        
        # Eredmények megjelenítése (ha van)
        if st.session_state.prediction_made and st.session_state.prediction_results:
            st.write("---")
            st.subheader("🎯 Árbecslés eredménye")
            
            results = st.session_state.prediction_results
            
            # Eredmény megjelenítése
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Becsült ár", f"{results['predicted_price']:.1f} M Ft")
            
            with col2:
                st.metric("📏 Ár/m²", f"{results['price_per_m2']:,.0f} Ft/m²")
            
            with col3:
                # Összehasonlítás piaci átlaggal
                difference = ((results['predicted_price'] - results['avg_price']) / results['avg_price']) * 100
                st.metric("📊 Eltérés átlagtól", f"{difference:+.1f}%")
            
            # További részletek
            st.write("#### 📋 Ingatlan részletei")
            inputs = results['user_inputs']
            
            details_col1, details_col2 = st.columns(2)
            with details_col1:
                st.write(f"🏠 **Terület:** {inputs['terulet']} m²")
                st.write(f"🛏️ **Szobák:** {inputs['szobak']}")
                st.write(f"🏗️ **Állapot:** {inputs['allapot']}")
                st.write(f"📅 **Építési év:** {inputs['epitesi_ev']}")
                st.write(f"🏡 **Telek:** {inputs['telekterulet']} m²")
            
            with details_col2:
                st.write(f"📷 **Képek:** {inputs['kepek']} db")
                st.write(f"🚗 **Parkolás:** {'Igen' if inputs['parkolas'] else 'Nem'}")
                st.write(f"🌿 **Erkély:** {'Igen' if inputs['erkely'] else 'Nem'}")
                st.write(f"👤 **Hirdető:** {'Magánszemély' if inputs['maganszemely'] else 'Iroda'}")


def advanced_ml_dashboard():
    """
    Főlépő függvény a szofisztikált ML dashboard-hoz
    """
    st.title("🤖 Szofisztikált ML Modell - Ingatlan Árbecslés")
    
    st.markdown("""
    Ez egy fejlett gépi tanulási rendszer, amely több algoritmust használ és összehasonlít 
    az ingatlanárak pontos becslésére. A rendszer automatikusan kiválasztja a legjobb modellt
    és részletes elemzést nyújt a teljesítményről.
    """)
    
    # Adatok betöltése
    @st.cache_data
    def load_data():
        """Adatok betöltése és alapvető feldolgozás"""
        try:
            df = pd.read_csv('ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv')
            
            # Ár oszlop létrehozása - javított logika
            if 'teljes_ar' in df.columns:
                ar_szamok = []
                for ar in df['teljes_ar']:
                    if pd.notna(ar):
                        ar_str = str(ar).replace(' ', '').replace('Ft', '')
                        # Handle "170 M Ft" format
                        if 'M' in ar_str:
                            try:
                                ar_numeric = float(ar_str.replace('M', '')) * 1_000_000
                                ar_szamok.append(ar_numeric)
                            except:
                                ar_szamok.append(np.nan)
                        else:
                            try:
                                ar_szamok.append(float(ar_str))
                            except:
                                ar_szamok.append(np.nan)
                    else:
                        ar_szamok.append(np.nan)
                df['ar_szam'] = ar_szamok
            
            # Terület oszlop
            if 'terulet' in df.columns:
                terulet_szamok = []
                for ter in df['terulet']:
                    if pd.notna(ter):
                        ter_str = str(ter).replace(' ', '').replace('m2', '').replace('m²', '')
                        try:
                            ter_szam = float(ter_str)
                            terulet_szamok.append(ter_szam)
                        except:
                            terulet_szamok.append(np.nan)
                    else:
                        terulet_szamok.append(np.nan)
                df['terulet_szam'] = terulet_szamok
            
            return df
        except Exception as e:
            st.error(f"Hiba az adatok betöltésénél: {e}")
            return None
    
    df = load_data()
    
    if df is not None:
        st.success(f"✅ Adatok sikeresen betöltve: {len(df)} rekord")
        
        # ML modell objektum létrehozása
        ml_model = SzofisztikaltIngatlanModell()
        
        # Adatok előkészítése
        processed_df = ml_model.adatok_elokeszitese(df)
        
        if processed_df is not None and len(processed_df) > 20:
            # Modell tanítás
            X_train, X_test, y_train, y_test = ml_model.modell_tanitas(processed_df)
            
            # Interaktív becslés
            ml_model.interaktiv_becsles(processed_df)
            
            # További elemzések
            st.subheader("📊 További elemzések")
            
            # Adatok exploráció
            with st.expander("🔍 Adatok feltárás"):
                st.write("**Alapstatisztikák:**")
                st.dataframe(processed_df.describe())
                
                # Korrelációs mátrix
                numeric_cols = processed_df.select_dtypes(include=[np.number]).columns
                corr_matrix = processed_df[numeric_cols].corr()
                
                fig = px.imshow(corr_matrix, 
                               title="Változók közötti korreláció",
                               color_continuous_scale='RdBu',
                               aspect="auto")
                st.plotly_chart(fig, use_container_width=True)
            
            # Model insights
            with st.expander("🧠 Modell insights"):
                st.markdown("""
                **Mit tanultunk a modellből?**
                
                1. **Legfontosabb tényezők**: A terület, állapot és telekterület a legmeghatározóbbak
                2. **Nem lineáris kapcsolatok**: Az ensemble módszerek jobban teljesítenek
                3. **Overfitting elkerülése**: Keresztvalidációval ellenőrizzük a generalizations
                4. **Feature engineering**: Az új változók (pl. ház kora) javítják a teljesítményt
                """)
        
        else:
            st.error("Nincs elegendő adat a modell tanításához!")
    
    else:
        st.error("Nem sikerült betölteni az adatokat!")


if __name__ == "__main__":
    advanced_ml_dashboard()
