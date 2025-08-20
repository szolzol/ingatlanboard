"""
KŐBÁNYA-ÚJHEGYI LAKÓTELEP PIACI ELEMZÉS
======================================

Rendkívül sokrétű elemzés 57 ingatlan alapján
Cél: 2 szobás, 49m², 6. emeleti, felújítandó lakás árának meghatározása
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Magyar karakterek támogatása matplotlib-ban
plt.rcParams['font.family'] = 'DejaVu Sans'

class KobanyaLakotelepElementes:
    def __init__(self, csv_file):
        """Inicializálás és adatok betöltése."""
        self.df = pd.read_csv(csv_file, encoding='utf-8')
        self.clean_data()
        
    def clean_data(self):
        """Adatok tisztítása és előkészítése."""
        print("🧹 ADATOK TISZTÍTÁSA ÉS ELŐKÉSZÍTÉSE")
        print("="*60)
        
        # Ár tisztítása (M Ft -> float)
        self.df['ar_millio'] = self.df['teljes_ar'].str.replace(' M Ft', '').str.replace(',', '.').astype(float)
        
        # Terület tisztítása (m2 -> int)
        self.df['terulet_m2'] = self.df['terulet'].str.replace(' m2', '').astype(int)
        
        # m² ár tisztítása (Ft/m² -> int)
        import re
        def clean_sqm_price(price_str):
            # Minden nem számot eltávolítunk
            cleaned = re.sub(r'[^\d]', '', str(price_str))
            # Az eredeti formátum: "1 125 000 Ft / m2" -> "11250002"
            # Az utolsó 2 számjegy a "m2" részből van, ezeket eltávolítjuk
            if len(cleaned) >= 2:
                cleaned = cleaned[:-2]  # utolsó 2 karakter (m2) eltávolítása
            result = int(cleaned) if cleaned else 0
            # A tizedesjegy elcsúszás javítása - 10-zel szorozzuk
            return result * 10
        
        self.df['nm_ar_clean'] = self.df['nm_ar'].apply(clean_sqm_price)
        
        # Szobaszám tisztítása
        self.df['szobak_clean'] = self.df['szobak'].fillna(0)
        
        # Cím elemzése - lakótelep vs egyéb
        self.df['lakotelepek'] = self.df['cim'].str.contains('lakótelep|Újhegyi', na=False)
        self.df['utca_nev'] = self.df['cim'].str.extract(r', ([^,]+)$')[0]
        
        print(f"✅ Adatok tisztítva: {len(self.df)} ingatlan")
        print(f"📊 Lakótelepi ingatlanok: {self.df['lakotelepek'].sum()}")
        print(f"📊 Egyéb ingatlanok: {(~self.df['lakotelepek']).sum()}")
        
    def basic_statistics(self):
        """Alapvető statisztikák."""
        print("\n📊 ALAPVETŐ STATISZTIKÁK")
        print("="*40)
        
        stats_data = {
            'Összes ingatlan': len(self.df),
            'Átlagár (M Ft)': f"{self.df['ar_millio'].mean():.2f}",
            'Medián ár (M Ft)': f"{self.df['ar_millio'].median():.2f}",
            'Átlag terület (m²)': f"{self.df['terulet_m2'].mean():.1f}",
            'Átlag m²ár (Ft/m²)': f"{self.df['nm_ar_clean'].mean():,.0f}".replace(',', ' '),
            'Min ár (M Ft)': f"{self.df['ar_millio'].min():.2f}",
            'Max ár (M Ft)': f"{self.df['ar_millio'].max():.2f}",
            'Min terület (m²)': self.df['terulet_m2'].min(),
            'Max terület (m²)': self.df['terulet_m2'].max()
        }
        
        for key, value in stats_data.items():
            print(f"📈 {key}: {value}")
    
    def room_analysis(self):
        """Szobaszám szerinti elemzés."""
        print("\n🏠 SZOBASZÁM SZERINTI ELEMZÉS")
        print("="*40)
        
        room_stats = self.df.groupby('szobak_clean').agg({
            'ar_millio': ['count', 'mean', 'median', 'min', 'max'],
            'terulet_m2': 'mean',
            'nm_ar_clean': 'mean'
        }).round(2)
        
        print("📋 Szobaszám alapú bontás:")
        for szoba in sorted(self.df['szobak_clean'].dropna().unique()):
            if szoba > 0:
                subset = self.df[self.df['szobak_clean'] == szoba]
                print(f"\n🏠 {szoba} szobás lakások ({len(subset)} db):")
                print(f"   💰 Átlagár: {subset['ar_millio'].mean():.2f} M Ft")
                print(f"   📐 Átlag terület: {subset['terulet_m2'].mean():.1f} m²")
                print(f"   💵 Átlag m²ár: {subset['nm_ar_clean'].mean():,.0f} Ft/m²".replace(',', ' '))
                print(f"   📊 Ár tartomány: {subset['ar_millio'].min():.2f} - {subset['ar_millio'].max():.2f} M Ft")
                
    def area_analysis(self):
        """Terület szerinti elemzés."""
        print("\n📐 TERÜLET SZERINTI ELEMZÉS")  
        print("="*40)
        
        # Terület kategóriák
        self.df['terulet_kategoria'] = pd.cut(self.df['terulet_m2'], 
                                            bins=[0, 40, 50, 60, 70, 100], 
                                            labels=['≤40m²', '41-50m²', '51-60m²', '61-70m²', '71m²≤'])
        
        area_stats = self.df.groupby('terulet_kategoria').agg({
            'ar_millio': ['count', 'mean', 'median'],
            'nm_ar_clean': ['mean', 'median']
        }).round(2)
        
        print("📊 Terület kategóriák:")
        for kategoria in self.df['terulet_kategoria'].cat.categories:
            subset = self.df[self.df['terulet_kategoria'] == kategoria]
            if len(subset) > 0:
                print(f"\n📐 {kategoria} ({len(subset)} db):")
                print(f"   💰 Átlagár: {subset['ar_millio'].mean():.2f} M Ft")
                print(f"   💵 Átlag m²ár: {subset['nm_ar_clean'].mean():,.0f} Ft/m²".replace(',', ' '))
                print(f"   📊 Ár tartomány: {subset['ar_millio'].min():.2f} - {subset['ar_millio'].max():.2f} M Ft")
    
    def location_analysis(self):
        """Lokáció szerinti elemzés."""
        print("\n🗺️ LOKÁCIÓ SZERINTI ELEMZÉS")
        print("="*40)
        
        # Lakótelep vs egyéb
        print("🏢 Lakótelep vs Egyéb lokációk:")
        for is_lakotelepek, name in [(True, "Lakótelepi"), (False, "Egyéb")]:
            subset = self.df[self.df['lakotelepek'] == is_lakotelepek]
            if len(subset) > 0:
                print(f"\n🏠 {name} ingatlanok ({len(subset)} db):")
                print(f"   💰 Átlagár: {subset['ar_millio'].mean():.2f} M Ft")
                print(f"   💵 Átlag m²ár: {subset['nm_ar_clean'].mean():,.0f} Ft/m²".replace(',', ' '))
                print(f"   📐 Átlag terület: {subset['terulet_m2'].mean():.1f} m²")
        
        # Utca szerinti top 5
        print(f"\n📍 TOP 5 LEGGYAKORIBB UTCA:")
        utca_stats = self.df.groupby('utca_nev').agg({
            'ar_millio': ['count', 'mean'],
            'nm_ar_clean': 'mean'
        }).sort_values(('ar_millio', 'count'), ascending=False).head()
        
        for utca in utca_stats.index[:5]:
            subset = self.df[self.df['utca_nev'] == utca]
            print(f"   🛣️ {utca} ({len(subset)} db): {subset['ar_millio'].mean():.2f} M Ft átlag")
    
    def price_per_sqm_analysis(self):
        """m² ár részletes elemzése."""
        print("\n💰 M² ÁR RÉSZLETES ELEMZÉSE")
        print("="*40)
        
        # m² ár statisztikák
        print(f"📊 m² ár statisztikák:")
        print(f"   📈 Átlag: {self.df['nm_ar_clean'].mean():,.0f} Ft/m²".replace(',', ' '))
        print(f"   📊 Medián: {self.df['nm_ar_clean'].median():,.0f} Ft/m²".replace(',', ' '))
        print(f"   📉 Min: {self.df['nm_ar_clean'].min():,.0f} Ft/m²".replace(',', ' '))
        print(f"   📈 Max: {self.df['nm_ar_clean'].max():,.0f} Ft/m²".replace(',', ' '))
        print(f"   📊 Szórás: {self.df['nm_ar_clean'].std():,.0f} Ft/m²".replace(',', ' '))
        
        # m² ár kategóriák
        self.df['nm_ar_kategoria'] = pd.cut(self.df['nm_ar_clean'],
                                          bins=[0, 1000000, 1100000, 1200000, 1300000, 2000000],
                                          labels=['≤1M', '1-1.1M', '1.1-1.2M', '1.2-1.3M', '1.3M≤'])
        
        print(f"\n💵 m² ár kategóriák eloszlása:")
        for kategoria in self.df['nm_ar_kategoria'].cat.categories:
            count = len(self.df[self.df['nm_ar_kategoria'] == kategoria])
            percent = (count / len(self.df)) * 100
            print(f"   💰 {kategoria} Ft/m²: {count} db ({percent:.1f}%)")
    
    def target_property_analysis(self):
        """Célproperty elemzése: 2 szobás, 49m², felújítandó."""
        print("\n🎯 CÉLPROPERTY ELEMZÉS: 2 SZOBÁS, 49M², FELÚJÍTANDÓ")
        print("="*60)
        
        # 2 szobás, ~49m² lakások keresése
        target_filter = (
            (self.df['szobak_clean'] == 2.0) & 
            (self.df['terulet_m2'] >= 47) & 
            (self.df['terulet_m2'] <= 51)
        )
        
        similar_properties = self.df[target_filter]
        
        print(f"🔍 Hasonló ingatlanok (2 szoba, 47-51m²): {len(similar_properties)} db")
        
        if len(similar_properties) > 0:
            print(f"\n📊 HASONLÓ INGATLANOK STATISZTIKÁI:")
            print(f"   💰 Átlagár: {similar_properties['ar_millio'].mean():.2f} M Ft")
            print(f"   📊 Medián ár: {similar_properties['ar_millio'].median():.2f} M Ft")
            print(f"   💵 Átlag m²ár: {similar_properties['nm_ar_clean'].mean():,.0f} Ft/m²".replace(',', ' '))
            print(f"   📊 Medián m²ár: {similar_properties['nm_ar_clean'].median():,.0f} Ft/m²".replace(',', ' '))
            print(f"   📉 Min ár: {similar_properties['ar_millio'].min():.2f} M Ft")
            print(f"   📈 Max ár: {similar_properties['ar_millio'].max():.2f} M Ft")
            
            print(f"\n📋 RÉSZLETES LISTA:")
            for idx, row in similar_properties.iterrows():
                print(f"   🏠 {row['cim']}")
                print(f"      💰 {row['ar_millio']:.2f} M Ft | 📐 {row['terulet_m2']}m² | 💵 {row['nm_ar_clean']:,} Ft/m²".replace(',', ' '))
        
        # Terület alapú elemzés (49m²)
        area_filter = (self.df['terulet_m2'] == 49)
        area_49_properties = self.df[area_filter]
        
        print(f"\n📐 PONTOSAN 49M² INGATLANOK: {len(area_49_properties)} db")
        if len(area_49_properties) > 0:
            print(f"   💰 Átlagár: {area_49_properties['ar_millio'].mean():.2f} M Ft")
            print(f"   💵 Átlag m²ár: {area_49_properties['nm_ar_clean'].mean():,.0f} Ft/m²".replace(',', ' '))
        
        return similar_properties, area_49_properties
    
    def renovation_adjustment(self):
        """Felújítási állapot miatti árkiigazítás."""
        print("\n🔨 FELÚJÍTÁSI ÁLLAPOT MIATTI ÁRKIIGAZÍTÁS")
        print("="*50)
        
        print("📋 FELÚJÍTÁSI KATEGÓRIÁK ÉS ÁRKIIGAZÍTÁSOK:")
        print("   ✨ Új építésű / Felújított: 0% (referencia)")
        print("   🏠 Jó állapotú: -5% - -10%")
        print("   🔧 Közepes állapotú: -10% - -15%")
        print("   🔨 Felújítandó: -15% - -25%")
        print("   ⚠️ Erősen felújítandó: -25% - -35%")
        
        return {
            'új_felújított': 0.0,
            'jó_állapot': -0.075,  # -7.5% átlag
            'közepes_állapot': -0.125,  # -12.5% átlag  
            'felújítandó': -0.20,  # -20% átlag
            'erősen_felújítandó': -0.30  # -30% átlag
        }
    
    def floor_adjustment(self):
        """Emeleti szorzók."""
        print("\n🏢 EMELETI SZORZÓK")
        print("="*30)
        
        print("📊 EMELETI ÁRKIIGAZÍTÁSOK:")
        print("   🏠 Földszint: -8% - -12%")
        print("   🔹 1-2. emelet: -3% - -5%") 
        print("   ✅ 3-5. emelet: 0% (referencia)")
        print("   🔸 6-8. emelet: -2% - -5% (lift függő)")
        print("   ⬆️ 9+ emelet: -5% - -10% (panellakás)")
        
        return {
            'földszint': -0.10,  # -10% átlag
            '1-2_emelet': -0.04,  # -4% átlag
            '3-5_emelet': 0.0,    # referencia
            '6-8_emelet': -0.035, # -3.5% átlag (lift van)
            '9plus_emelet': -0.075 # -7.5% átlag
        }
    
    def calculate_recommended_price(self, similar_properties, area_49_properties):
        """Ajánlott ár kiszámítása."""
        print("\n🎯 AJÁNLOTT ÁR KALKULÁCIÓ")
        print("="*40)
        
        # Alapár meghatározás
        if len(similar_properties) >= 3:
            base_price_million = similar_properties['ar_millio'].median()
            base_sqm_price = similar_properties['nm_ar_clean'].median()
            data_quality = "Kiváló"
        elif len(area_49_properties) >= 2:
            base_price_million = area_49_properties['ar_millio'].mean()
            base_sqm_price = area_49_properties['nm_ar_clean'].mean()
            data_quality = "Jó"
        else:
            # Általános 2 szobás átlag
            two_room = self.df[self.df['szobak_clean'] == 2.0]
            avg_sqm_price = two_room['nm_ar_clean'].mean()
            base_price_million = (avg_sqm_price * 49) / 1_000_000
            base_sqm_price = avg_sqm_price
            data_quality = "Közepes"
        
        print(f"📊 Adatminőség: {data_quality}")
        print(f"💰 Alapár (hasonló ingatlanok): {base_price_million:.2f} M Ft")
        print(f"💵 Alap m²ár: {base_sqm_price:,.0f} Ft/m²".replace(',', ' '))
        
        # Kiigazítások alkalmazása
        renovation_adj = self.renovation_adjustment()['felújítandó']  # -20%
        floor_adj = self.floor_adjustment()['6-8_emelet']  # -3.5%
        
        total_adjustment = 1 + renovation_adj + floor_adj  # -23.5%
        
        adjusted_price = base_price_million * total_adjustment
        adjusted_sqm_price = base_sqm_price * total_adjustment
        
        print(f"\n🔧 KIIGAZÍTÁSOK:")
        print(f"   🔨 Felújítandó állapot: {renovation_adj:.1%}")
        print(f"   🏢 6. emelet: {floor_adj:.1%}")
        print(f"   📊 Összesen: {(total_adjustment-1):.1%}")
        
        print(f"\n💰 KIIGAZÍTOTT ÁRAK:")
        print(f"   💵 Ajánlott ár: {adjusted_price:.2f} M Ft")
        print(f"   💰 m²ár: {adjusted_sqm_price:,.0f} Ft/m²".replace(',', ' '))
        
        # Ár sáv meghatározás
        min_price = adjusted_price * 0.90  # -10%
        max_price = adjusted_price * 1.10  # +10%
        
        print(f"\n📊 AJÁNLOTT ÁR SÁV:")
        print(f"   📉 Minimum: {min_price:.2f} M Ft")
        print(f"   🎯 Optimális: {adjusted_price:.2f} M Ft")  
        print(f"   📈 Maximum: {max_price:.2f} M Ft")
        
        return {
            'optimális_ár': adjusted_price,
            'minimum_ár': min_price,
            'maximum_ár': max_price,
            'ajánlott_m2_ár': adjusted_sqm_price,
            'alapár': base_price_million,
            'kiigazítás': (total_adjustment-1),
            'adatminőség': data_quality
        }
    
    def competitive_analysis(self):
        """Versenyhelyzet elemzése."""
        print("\n⚔️ VERSENYHELYZET ELEMZÉSE")
        print("="*40)
        
        # Hasonló árkategóriájú ingatlanok
        avg_price = self.df['ar_millio'].mean()
        
        # Árcsoportok
        cheap = self.df[self.df['ar_millio'] <= avg_price * 0.85]
        mid_range = self.df[(self.df['ar_millio'] > avg_price * 0.85) & 
                           (self.df['ar_millio'] < avg_price * 1.15)]
        expensive = self.df[self.df['ar_millio'] >= avg_price * 1.15]
        
        print(f"💰 ÁRCSOPORTOK:")
        print(f"   💸 Olcsó (≤{avg_price*0.85:.1f}M): {len(cheap)} db ({len(cheap)/len(self.df)*100:.1f}%)")
        print(f"   💰 Közepes ({avg_price*0.85:.1f}-{avg_price*1.15:.1f}M): {len(mid_range)} db ({len(mid_range)/len(self.df)*100:.1f}%)")
        print(f"   💎 Drága (≥{avg_price*1.15:.1f}M): {len(expensive)} db ({len(expensive)/len(self.df)*100:.1f}%)")
    
    def market_recommendations(self, price_result):
        """Piaci ajánlások."""
        print("\n🎯 PIACI AJÁNLÁSOK ÉS STRATÉGIA")
        print("="*50)
        
        optimális = price_result['optimális_ár']
        
        print(f"📋 ÉRTÉKESÍTÉSI STRATÉGIA:")
        print(f"\n💡 GYORS ÉRTÉKESÍTÉS (2-4 hét):")
        print(f"   💰 Ár: {optimális * 0.92:.2f} M Ft")
        print(f"   📊 Indoklás: Agresszív árazás, gyors forgalom")
        
        print(f"\n⚖️ EGYENSÚLYI ÁRAZÁS (1-3 hónap):")
        print(f"   💰 Ár: {optimális:.2f} M Ft")
        print(f"   📊 Indoklás: Piaci átlag, megfelelő értékarány")
        
        print(f"\n💎 PRÉMIUM POZICIONÁLÁS (3-6 hónap):")
        print(f"   💰 Ár: {optimális * 1.08:.2f} M Ft")
        print(f"   📊 Indoklás: Magasabb pozicionálás, várakozás a megfelelő vevőre")
        
        print(f"\n📈 MARKETING FÓKUSZ PONTOK:")
        print("   ✅ 2 szobás lakás - ideális fiatal párnak/kiscsaládnak")
        print("   ✅ 49m² - optimális méret")  
        print("   ✅ 6. emelet - szép kilátás, csendes")
        print("   ✅ Felújítási potenciál - személyre szabható")
        print("   ✅ Lakótelep - jó közlekedés, szolgáltatások")
        
        print(f"\n⚠️ FIGYELEMFELHÍVÁSOK:")
        print("   🔨 Felújítási költségek kalkulálása (3-5M Ft)")
        print("   🏢 Emelet - lift működése fontos")
        print("   💰 Finanszírozás - kalkulálja a vevő a teljes költséget")
        
    def generate_full_report(self):
        """Teljes jelentés generálása."""
        print("🏠 KŐBÁNYA-ÚJHEGYI LAKÓTELEP - TELJES PIACI ELEMZÉS")
        print("="*80)
        print(f"📅 Elemzés dátuma: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"📊 Elemzett ingatlanok száma: {len(self.df)}")
        
        # Futtatás
        self.basic_statistics()
        self.room_analysis()
        self.area_analysis() 
        self.location_analysis()
        self.price_per_sqm_analysis()
        
        similar_props, area_49_props = self.target_property_analysis()
        price_result = self.calculate_recommended_price(similar_props, area_49_props)
        self.competitive_analysis()
        self.market_recommendations(price_result)
        
        print(f"\n" + "="*80)
        print("📊 ÖSSZEFOGLALÓ JAVASLAT")
        print("="*80)
        print(f"🎯 AJÁNLOTT HIRDETÉSI ÁR: {price_result['optimális_ár']:.2f} M Ft")
        print(f"📐 m² ÁR: {price_result['ajánlott_m2_ár']:,.0f} Ft/m²".replace(',', ' '))
        print(f"📊 ÁR SÁV: {price_result['minimum_ár']:.2f} - {price_result['maximum_ár']:.2f} M Ft")
        print(f"🔍 ADATMINŐSÉG: {price_result['adatminőség']}")
        print("="*80)

def main():
    """Főprogram."""
    csv_file = "ingatlan_final_clean_20250819_113758.csv"
    
    try:
        analyzer = KobanyaLakotelepElementes(csv_file)
        analyzer.generate_full_report()
        
    except Exception as e:
        print(f"❌ Hiba: {e}")

if __name__ == "__main__":
    main()
