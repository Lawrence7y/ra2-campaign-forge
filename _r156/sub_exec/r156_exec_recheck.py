#!/usr/bin/env python3
"""R156 执行员独立复核：重算 A–F 六项承载性数字（只读输入，仅写 _r156/sub_exec）。"""
import hashlib, json, os, re

R = '/home/t628/projects/ra2-campaign-forge'
OUT = R + '/_r156/sub_exec'
FI = R + '/lead/next_re_20261117_r14/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
GOAL = R + '/lead/GOAL_THREE_TARGETS_20261018.md'
SUP = R + '/lead/next_re_20261117_r14/R17_LEDGER_1063/SUPERSEDED.md'
os.makedirs(OUT, exist_ok=True)


def sha(p):
    b = open(p, 'rb').read()
    return {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b), 'lines': b.count(b'\n')}


inputs = {'FACT_INDEX': sha(FI), 'GOAL': sha(GOAL), 'SUPERSEDED': sha(SUP)}
raw = open(FI, encoding='utf-8').read().splitlines()
rows = [dict(zip(raw[0].split('\t'), l.split('\t'))) for l in raw[1:]]
lines = open(GOAL, encoding='utf-8').read().splitlines()

# --- section/item parsing: ## §1062..1065, ### item boundaries ---
heads = [(i, l) for i, l in enumerate(lines, 1) if re.match(r'^##\s', l)]
secs = {}
for si, (i, l) in enumerate(heads):
    m = re.match(r'^##\s+§(106[2-5])(?:\s|·|$)', l)
    if not m:
        continue
    end = heads[si + 1][0] - 1 if si + 1 < len(heads) else len(lines)
    sub, items = None, {}
    for k in range(i + 1, end + 1):
        mm = re.match(r'^###\s+(.*)', lines[k - 1])
        if mm:
            h = mm.group(1)
            n = re.search(r'(?:事项\s*)(\d+)(?:\s*[.·、])?', h) or re.match(r'^(\d+)\s*[.·]', h)
            sub = int(n.group(1)) if n else -1
            items[sub] = {'heading': h, 'text': ''}
        elif sub is not None:
            items[sub]['text'] += '\n' + lines[k - 1]
    secs[m.group(1)] = {'range': [i, end], 'items': items, 'full': '\n'.join(lines[i - 1:end])}

secof = lambda c: {'1063R': '1063'}.get(c, c)


def itemtext(s, n):
    it = secs.get(secof(s), {}).get('items', {}).get(n)
    return (it['heading'] + '\n' + it['text']) if it else ''


def norm(s):
    return re.sub(r'[^\w一-鿿]+', '', s.replace('`', '').replace(' ', '').replace('　', ''), flags=re.UNICODE)


def lcs(a, b):
    best, prev = 0, [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


SECTION_RE = re.compile(r'(?<!SUPERSEDED\\)R17_LEDGER_(\d+[A-Z]?)\\SECTION\.md\((.*?)\)(?=;|$)')
NUM_RE = re.compile(r'(?:事项\s*)(\d+)|(?<!\d)(\d+)\s*[.·]')


def parts(anno):
    return [p.strip() for p in re.split(r'[/／]', anno) if p.strip()]


def resolve(code, topic):
    cand = []
    for n, it in secs.get(secof(code), {}).get('items', {}).items():
        cand.append((lcs(norm(topic), norm(it['heading'] + ' ' + it['text'])), n, it['heading']))
    cand.sort(reverse=True)
    return {'topic': topic, 'item': cand[0][1], 'score': cand[0][0], 'heading': cand[0][2]} if cand and cand[0][0] >= 4 else None


# A: evidence items pointing at R17_LEDGER_*/SECTION.md
A_items = []
for r in rows:
    for code, anno in SECTION_RE.findall(r['evidence_paths']):
        ns = NUM_RE.findall(anno)
        nums = [a or b for a, b in ns]
        rec = {'fid': r['fact_id'], 'ledger': code, 'mapped_sec': secof(code), 'annotation': anno,
               'kind': 'numeric' if nums else 'topic', 'numbers': [int(x) for x in nums], 'topic_resolutions': []}
        if not nums:
            rec['topic_resolutions'] = [x for x in (resolve(code, p) for p in parts(anno)) if x]
        A_items.append(rec)
A_numeric = [x for x in A_items if x['kind'] == 'numeric']
A_topic = [x for x in A_items if x['kind'] == 'topic']
A_resolved = [x for x in A_topic if x['topic_resolutions']]
A = {'total_section_evidence_items': len(A_items), 'numeric_items': len(A_numeric),
     'topic_items': len(A_topic), 'topic_resolved_items': len(A_resolved),
     'resolved_total': len(A_numeric) + len(A_resolved), 'details': A_items}


def named_items(fid):
    r = next(x for x in rows if x['fact_id'] == fid)
    out = set()
    for code, anno in SECTION_RE.findall(r['evidence_paths']):
        ns = NUM_RE.findall(anno)
        if ns:
            out.update((secof(code), int(a or b)) for a, b in ns)
        else:
            for p in parts(anno):
                x = resolve(code, p)
                if x:
                    out.add((secof(code), x['item']))
    return sorted(out)


FIDS = ['F04', 'F06', 'F07', 'F08', 'F09', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16']
HEX_RE = re.compile(r'0x[0-9a-fA-F]+|(?<![0-9a-fA-F])[0-9a-fA-F]{8}(?![0-9a-fA-F])')
DEC_RE = re.compile(r'(?<![\dA-Fa-fxX])(\d{3,})(?![\dA-Fa-f])')


def uniq(ms):
    out, seen = [], set()
    for m in ms:
        t = m if isinstance(m, str) else m.group(0)
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


def decs(s):
    return uniq(DEC_RE.finditer(re.sub(r'§\s*\d{3,5}', '', s).replace(',', '')))


# B/C: literal substring match in the union of named items
B = {'total': 0, 'hits': 0, 'wide_total': 0, 'wide_hits': 0, 'per_fid': {}}
C = {'total': 0, 'hits': 0, 'per_fid': {}}
for fid in FIDS:
    r = next(x for x in rows if x['fact_id'] == fid)
    ni = named_items(fid)
    txt = '\n'.join(itemtext(s, n) for s, n in ni)
    low = txt.lower()
    # 宽口径：任何 0x 后跟十六进制数字；几乎无鉴别力。
    ads = uniq(HEX_RE.finditer(r['statement']))
    adh = [a for a in ads if a.lower() in low]
    # 严格口径 B：0x + >=4 位十六进制数字，或 8 位裸十六进制。
    ads4 = [a for a in ads if (a.lower().startswith('0x') and len(a) >= 6) or (not a.lower().startswith('0x') and len(a) == 8)]
    adh4 = [a for a in ads4 if a.lower() in low]
    dns = decs(r['statement'])
    dnh = [d for d in dns if d in txt]
    B['total'] += len(ads4); B['hits'] += len(adh4)
    B['wide_total'] = B.get('wide_total', 0) + len(ads)
    B['wide_hits'] = B.get('wide_hits', 0) + len(adh)
    C['total'] += len(dns); C['hits'] += len(dnh)
    B['per_fid'][fid] = {'named_items': ni, 'addresses': ads, 'wide_hits': adh, 'strict_addresses': ads4, 'strict_hits': adh4}
    C['per_fid'][fid] = {'named_items': ni, 'decimals': dns, 'hits': dnh}

alltxt = '\n'.join(secs[s]['full'] for s in ['1062', '1063', '1064', '1065'])
alllow = alltxt.lower()

# D: F08 missing addresses
f08ad = uniq(HEX_RE.finditer(next(x for x in rows if x['fact_id'] == 'F08')['statement']))
D = {'f08_addresses': f08ad,
     'coverage': {a: {'in_1062_1065': a.lower() in alllow, 'count': alllow.count(a.lower())} for a in f08ad}}
D['missing'] = [a for a in f08ad if a.lower() not in alllow]

# E: F15 literal anchors
suptxt = open(SUP, encoding='utf-8').read()
t4 = itemtext('1063', 4)
E = {'anchors': ['129', '125', '354', '167', '267'], 'per_anchor': {}}
for a in E['anchors']:
    pat = r'(?<!\d)' + a + r'(?!\d)'
    E['per_anchor'][a] = {'superseded_count': len(re.findall(pat, suptxt)),
                          'sec1063_item4_count': len(re.findall(pat, t4))}

# F: 0x43BCF0
F = {'address': '0x43BCF0', 'in_1062_1065': '0x43bcf0' in alllow, 'count': alllow.count('0x43bcf0'), 'earlier': []}
for i, l in enumerate(lines, 1):
    if i >= secs['1062']['range'][0]:
        break
    if '43bcf0' in l.lower():
        sn = '?'
        for j in range(i, 0, -1):
            mm = re.match(r'^##\s+(§\S+)', lines[j - 1])
            if mm:
                sn = mm.group(1)
                break
        F['earlier'].append({'line': i, 'section': sn, 'text': l[:220]})

# controls (no expected result variables hardcoded as assertions)
ctrl = {
    'positive_known_address_in_named_item': '0x43f180' in itemtext('1062', 1).lower(),
    'positive_topic_resolves': any(any(y['item'] == 3 for y in x.get('topic_resolutions', [])) for x in A_topic),
    'negative_fake_address_zero': alllow.count('0xdeadbeefcafe') == 0,
    'negative_wrong_item_zero': '0x43f180' not in itemtext('1063', 1).lower(),
    'negative_unrelated_num_zero': '999999' not in alltxt,
}
assert all(ctrl.values()), ctrl

result = {'inputs': inputs,
          'section_map': {s: {'range': secs[s]['range'], 'items': {str(n): it['heading'] for n, it in secs[s]['items'].items()}} for s in secs},
          'A': A, 'B': B, 'C': C, 'D': D, 'E': E, 'F': F, 'controls': ctrl}
blob = json.dumps(result, ensure_ascii=False, indent=2)
open(OUT + '/r156_exec_recheck.json', 'w', encoding='utf-8').write(blob)
open(OUT + '/r156_exec_recheck.txt', 'w', encoding='utf-8').write(blob)
print('A resolved_total=%d (numeric=%d, topic=%d, topic_resolved=%d)' %
      (A['resolved_total'], A['numeric_items'], A['topic_items'], A['topic_resolved_items']))
print('B addresses(strict)=%d hits=%d (wide %d/%d)' % (B['total'], B['hits'], B['wide_total'], B['wide_hits']))
print('C decimals=%d hits=%d' % (C['total'], C['hits']))
print('D missing=', D['missing'])
print('E per_anchor=', json.dumps(E['per_anchor'], ensure_ascii=False))
print('F in_1062_1065=', F['in_1062_1065'], 'earlier_sections=', sorted(set(x['section'] for x in F['earlier'])))
print('controls=', json.dumps(ctrl, ensure_ascii=False))
