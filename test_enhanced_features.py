"""
Enhanced Mode teszt - luxus feature-k hatása
"""

import sys
sys.path.append('.')

from analyze_descriptions_focused import IngatlanSzovegelemzo

# Teszt leírások
basic_description = "Eladó családi ház Erdligeten."

luxury_description = """
Elegáns, luxus családi ház prémium kivitelben. 
Tágas, modern belső terek designer bútorokkal. 
Parkosított kert medencével és jakuzzival.
Dupla garázs elektromos kaputelefon rendszerrel.
Klímaberendezés minden helyiségben, mosogatógép, mosógép.
Csendes, elegáns környék kiváló megközelíthetőséggel.
"""

# Szövegelemző
elemzo = IngatlanSzovegelemzo()

print("=== ENHANCED MODE TESZT ===")
print()

print("1. ALAPVETŐ LEÍRÁS:")
print(f'"{basic_description}"')
pontszamok_alap, details_alap = elemzo.extract_category_scores(basic_description)
print("Pontszámok:", pontszamok_alap)
print(f"Összesített pont: {sum(pontszamok_alap.values())}")
print()

print("2. LUXUS LEÍRÁS:")
print(f'"{luxury_description[:100]}..."')
pontszamok_luxus, details_luxus = elemzo.extract_category_scores(luxury_description)
print("Pontszámok:", pontszamok_luxus)
print(f"Összesített pont: {sum(pontszamok_luxus.values())}")
print()

print("3. KÜLÖNBSÉG:")
for kategoria in pontszamok_luxus:
    kulonbseg = pontszamok_luxus[kategoria] - pontszamok_alap.get(kategoria, 0)
    if kulonbseg != 0:
        print(f"{kategoria}: {kulonbseg:+.1f} pont különbség")

print(f"ÖSSZ KÜLÖNBSÉG: {sum(pontszamok_luxus.values()) - sum(pontszamok_alap.values()):+.1f} pont")
