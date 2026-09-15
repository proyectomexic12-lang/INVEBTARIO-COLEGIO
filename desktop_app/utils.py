import re
from datetime import datetime
import unicodedata

def strip_accents(s):
    if not isinstance(s, str):
        return s
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def parse_currency(val):
    if val is None: return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = str(val).strip()
    if not s or s.lower() == 'nan': return 0.0
    if re.match(r'^-?\d+(\.\d+)?$', s): return float(s)
    s = s.replace('$', '').replace(' ', '')
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    else:
        if s.count('.') > 1: s = s.replace('.', '')
    try: return float(s)
    except: return 0.0

def calculate_depreciation(valor, existencia_inicial, descripcion, ubicacion, fecha_adquisicion, vida_util):
    val_cost = parse_currency(valor)
    qty = max(1, int(parse_currency(existencia_inicial)))
    val_total = val_cost * qty
    
    if val_total <= 0:
        return 0.0
        
    desc_upper = str(descripcion or '').upper()
    ubi_upper = str(ubicacion or '').upper()
    
    if 'AIRE' in desc_upper and ubi_upper in ('AULA 1', 'AULA 2', 'TRANSICION'):
        return 0.0
    elif 'IMPRESORA 3D' in desc_upper and 'LABORATORIO' in ubi_upper:
        return 1380000.0
    else:
        m = re.search(r'\b(19\d\d|20\d\d)\b', str(fecha_adquisicion or ''))
        if m:
            acq_year = int(m.group(1))
            if 2013 <= acq_year <= 2020:
                return val_total
            else:
                curr_year = datetime.now().year
                elapsed = max(0, curr_year - acq_year)
                try: life_val = int(parse_currency(vida_util))
                except: life_val = 10
                if life_val <= 0: life_val = 10
                
                if elapsed >= life_val:
                    return val_total
                elif elapsed > 0:
                    return round(val_total * (elapsed / life_val), 2)
                else:
                    return 0.0
        else:
            # Si no hay año válido, se deprecia al 100% por seguridad
            return val_total
