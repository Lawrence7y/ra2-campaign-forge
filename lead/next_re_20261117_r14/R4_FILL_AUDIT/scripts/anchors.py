"""Final audit pass: anchor corroboration + enumeration limits, then renderer."""
import json
import struct

import capstone

import reib

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R4_FILL_AUDIT"


def main():
    img = reib.Image()
    dis = reib.Dis(img)
    d = json.load(open(OUT + r"\scripts\audit.json", encoding='utf-8'))
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]

    calls = {}
    pos = blob.find(b'\xe8')
    while pos >= 0:
        if pos + 5 <= len(blob):
            rel = struct.unpack('<i', blob[pos + 1:pos + 5])[0]
            tgt = tv['va'] + pos + 5 + rel
            if img.is_text(tgt):
                calls.setdefault(tgt, []).append(tv['va'] + pos)
        pos = blob.find(b'\xe8', pos + 1)

    lea_hits = {}
    for entry_s, r in d['rows'].items():
        vt = r['check1']['slot_value'] and int(r['check1']['witnesses'][0]['vt'], 16)
        lea = []
        if vt:
            pat = struct.pack('<I', vt)
            p = blob.find(pat)
            while p >= 0:
                end = p + 4
                for st in range(max(0, end - 10), end):
                    ins = None
                    for i in dis.md.disasm(blob[st:end], tv['va'] + st):
                        ins = i
                        break
                    if ins is not None and ins.address + ins.size == tv['va'] + end \
                            and ins.mnemonic == 'lea':
                        lea.append(tv['va'] + st)
                        break
                p = blob.find(pat, p + 1)
        lea_hits[entry_s] = lea
        host = int(r['check4']['host'], 16)
        r['check4']['call_xrefs_to_host'] = ['%08X' % x for x in calls.get(host, [])][:6]
        r['check4']['host_is_call_target'] = host in calls
        r['enum_lea_mentions'] = ['%08X' % x for x in lea]

    with open(OUT + r"\scripts\audit.json", 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    for k, r in d['rows'].items():
        print(k, r['check4']['host'], 'callxrefs', len(r['check4']['call_xrefs_to_host']),
              'lea', len(r['enum_lea_mentions']))


if __name__ == '__main__':
    main()
