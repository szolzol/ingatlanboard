import pandas as pd

# Load the latest enhanced CSV
df = pd.read_csv('ingatlan_reszletes_enhanced_xii_ker_20250822_115813.csv', sep='|', encoding='utf-8', on_bad_lines='skip')

print('📋 CSV OSZLOPOK ELLENŐRZÉSE:')
print(f'Összes oszlop: {len(df.columns)}')
print()

# Enhanced location columns
enhanced_cols = ['enhanced_keruleti_resz', 'lokacio_konfidencia', 'geo_latitude', 'geo_longitude', 'geo_address_from_api']
print('🗺️ ENHANCED LOKÁCIÓ OSZLOPOK:')
for col in enhanced_cols:
    if col in df.columns:
        non_null_count = df[col].notna().sum()
        print(f'  ✅ {col}: {non_null_count}/{len(df)} értékkel')
        if col in ['geo_latitude', 'geo_longitude']:
            valid_coords = df[col].apply(lambda x: x is not None and x != '' and str(x) != 'nan').sum()
            print(f'      -> Érvényes koordináták: {valid_coords}')
    else:
        print(f'  ❌ {col}: HIÁNYZIK!')

print()

# Check all columns
print('🔍 ÖSSZES OSZLOP:')
for i, col in enumerate(df.columns, 1):
    print(f'{i:2d}. {col}')
