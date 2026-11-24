"""S10-KPROVED3 step 2: detailed annotated disassembly dumps for candidate rows."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

HERE = os.path.dirname(os.path.abspath(__file__))
CLS = r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
import csv

CAND = sys.argv[1:] or [
    '004D5690','004D94B0','004DB260','00702D40','00706640','00708C30',
    '004DDDE0','00517CC0','006FB010','006FBC90','006FC030','0070E140','00707D20',
    '006F3AD0','006F3D60','004D82B0','004DBAD0','004DDED0']

def main():
    pe = core.PE()
    meta = {}
    with open(CLS, encoding='utf-8') as f:
        for c in csv.DictReader(f, delimiter='\t'):
            meta[c['entry']] = c
    os.makedirs(os.path.join(HERE, 'dumps'), exist_ok=True)
    for entry in CAND:
        c = meta.get(entry)
        if not c:
            # normalise with leading zeros
            for k in meta:
                if k.lstrip('0') == entry.lstrip('0'):
                    c = meta[k]; entry = k; break
        e = int(entry, 16)
        atlas = int(c['atlas_size'])
        ext_hi = int(c['ext_hi'], 16)
        # body hi: cap CFG extent by atlas size when it wildly overruns (stub cases)
        cap_hi = e + max(atlas, 16)
        hi = min(ext_hi, cap_hi) if ext_hi > cap_hi + 64 else ext_hi
        ins = core.disasm(pe, e, hi)
        lines = ['=== %s %s  atlas_size=%d ext_hi=%s body_hi=%08X' % (entry, c['name'], atlas, c['ext_hi'], hi)]
        for i in ins:
            off = i.address - e
            lines.append('+%05X  %08X  %-10s %s' % (off, i.address, i.mnemonic, i.op_str))
        txt = '\n'.join(lines)
        print(txt[:1500])
        print('  ... total %d insns (dump truncated on screen, full in file)\n' % len(ins))
        open(os.path.join(HERE, 'dumps', entry + '.txt'), 'w').write(txt)

if __name__ == '__main__':
    main()
