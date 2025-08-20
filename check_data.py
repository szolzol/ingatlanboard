import pandas as pd

df = pd.read_csv('ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv', encoding='utf-8-sig')
print(f'📊 Összes rekord: {len(df)}')

# Ár parsing
def parse_million_ft(text):
    if pd.isna(text): 
        return None
    import re
    match = re.search(r'(\d+(?:\.\d+)?)\s*M', str(text))
    return float(match.group(1)) if match else None

df['target_ar'] = df['teljes_ar'].apply(parse_million_ft)
valid_price = df['target_ar'].notna().sum()
print(f'💰 Érvényes ár: {valid_price}')

# Terület parsing  
def parse_terulet(text):
    if pd.isna(text): 
        return None
    import re
    match = re.search(r'(\d+)', str(text))
    return int(match.group(1)) if match else None

df['terulet_szam'] = df['terulet'].apply(parse_terulet)
valid_area = df['terulet_szam'].notna().sum()
print(f'📐 Érvényes terület: {valid_area}')

# Mindkettő együtt
clean = df[df['target_ar'].notna() & df['terulet_szam'].notna()]
print(f'✅ Mindkettő OK: {len(clean)} 🚨 ({len(clean)/len(df)*100:.1f}%)')

if len(clean) > 0:
    print(f'📈 Ár tartomány: {clean["target_ar"].min():.1f}M - {clean["target_ar"].max():.1f}M Ft')
    print(f'📏 Terület tartomány: {clean["terulet_szam"].min()}m² - {clean["terulet_szam"].max()}m²')

# Nézzük mi a gond
print("\n🔍 Mi hiányzik?")
print(f"Üres ár: {df['teljes_ar'].isna().sum()}")
print(f"Nem parseable ár: {valid_price} / {len(df)} = {len(df) - valid_price} hibás")
print(f"Üres terület: {df['terulet'].isna().sum()}")
print(f"Nem parseable terület: {valid_area} / {len(df)} = {len(df) - valid_area} hibás")

# Minta hibás adatok
print("\n📋 Minta ár formátumok:")
sample_prices = df['teljes_ar'].dropna().head(10)
for i, price in enumerate(sample_prices):
    print(f"{i+1}. '{price}'")
