import common as C

def td_name(td):
    try:
        o = C.va2off(td + 8)
    except Exception as e:
        return ('ERR', str(e))
    end = C.DATA.find(b'\x00', o, o+128)
    if end < 0:
        return ('NOEND',)
    s = C.DATA[o:end].decode('latin-1')
    return (s, s.startswith('.?A'), s.endswith('@@'))

print('tdname', td_name(0x815e38))
COL = 0x7FA4D8
chd = C.ru32(COL + 0x10); print('chd', hex(chd))
nb = C.ru32(chd + 8); print('nb', nb, type(nb))
bca = C.ru32(chd + 0xC); print('bca', hex(bca))
for i in range(nb):
    bcd = C.ru32(bca + 4*i)
    td = C.ru32(bcd) if bcd else None
    print(' i', i, 'bcd', hex(bcd) if bcd else bcd, 'td', hex(td) if td else td,
          'name', td_name(td) if td else None)
