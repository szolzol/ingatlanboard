import re

test_string = 'elado+lakas+uj-epitesu+ujszeru+felujitott+jo-allapotu+3-szoba-felett+orszagut+vizivaros-ii+krisztinavaros-xii'

print(f'Eredeti: {test_string}')

# Eltávolítjuk az ingatlan típust
result = re.sub(r'(elado|kiado|berlet)\+[^+]*\+?', '', test_string)
print(f'Tipus nélkül: {result}')

# Állapot szűrők
allapot_szurok = [
    'uj_epitesu', 'ujszeru', 'felujitott', 'jo_allapot', 'kituno_allapot', 
    'kozepes_allapot', 'felujitando', 'rossz_allapot', 'bonthato',
    'uj-epitesu', 'jo-allapot', 'kituno-allapot', 'kozepes-allapot',
    'epitesu', 'ujszeru', 'felujitott', 'jo', 'allapot'
]

for szuro in allapot_szurok:
    old_result = result
    result = result.replace(f'+{szuro}', '').replace(f'{szuro}+', '').replace(szuro, '')
    if old_result != result:
        print(f'Szűrő "{szuro}" után: {result}')

# Jo-allapotu kiegészítő kezelés
result = result.replace('jo-allapotu', '').replace('-allapotu', '').replace('allapotu', '')
print(f'Allapotu tisztítás után: {result}')

# Speciális "uj" kezelés
result = re.sub(r'(\+|^)uj(\+|$)', r'\1\2', result)  
result = re.sub(r'\+uj(?=\+[a-z])', '+', result) 
print(f'Uj kezelés után: {result}')

# Ár szűrők
result = re.sub(r'\+?\d+[\-_]\d+[\-_]?m?[Ff]t\+?', '', result)
print(f'Ár szűrők után: {result}')

# Szobaszám szűrők
result = re.sub(r'\+?\d+[\-_]szoba[\-_]?(felett|alatt)?\+?', '', result)
result = re.sub(r'\+?szoba[\-_]?(felett|alatt)?\+?', '', result)
result = re.sub(r'\+?(felett|alatt)\+?', '', result)
print(f'Szobaszám szűrők után: {result}')

# Dupla + jelek
result = re.sub(r'\+{2,}', '+', result)
result = result.strip('+')
print(f'Tisztítás után: {result}')

# Biztonságos fájlnév
safe_name = re.sub(r'[^\w\-_]', '_', result)
safe_name = safe_name.replace('-', '_')
safe_name = re.sub(r'_{2,}', '_', safe_name)
safe_name = safe_name.strip('_')
print(f'Végeredmény: {safe_name}')
