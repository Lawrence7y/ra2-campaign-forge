# -*- coding: utf-8 -*-
"""_ai2_baseline.py — 本会话独立复现基线：41 条 × 六判定器 + strict/forced fp/fn
+ 41 条零精确重合（AST 静态抽取）+ 41 条 hits 逐条比对 + P06-P12 / C01-C12 逐条自判。
只用 ast / re / hashlib / 源码 compile-exec 内存加载；不 import 保护件（不产生 __pycache__），
不写保护树，不启动真机，不写采样代码。唯一写域 lead/advset_indep_20261109/。"""
import ast
import hashlib
import re
from pathlib import Path

B = Path(r'D:/Project/ra2-campaign-forge')
DG_DIR = B / 'lead' / 'dneg_generative_20261109'
DGA = B / 'lead' / 'dg_adversarial_20261109'
H5P = B / 'lead' / 'h5_governance_20261109' / '_h5_pasteable.py'
G7P = B / 'lead' / 'gate_fp7_20261108' / '_g7_predicates.py'


def load(name, path):
    import types
    src = Path(path).read_text(encoding='utf-8')
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(src, str(path), 'exec'), m.__dict__)
    return m


DG = load('_ai2_dg', DG_DIR / '_dg_core.py')
H5 = load('_ai2_h5', H5P)
G7 = load('_ai2_g7', G7P)
DROP = load('_ai2_drop', G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
DETECTORS = ["DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"]


def detect(text):
    """复刻 _dga_adversarial.py:210-256 的六判定器。"""
    toks = [t for t in TOKS if t in text] or ["已生效"]
    r = {k: "PASS" for k in DETECTORS}
    hits = {}
    p, h = DG.dg_scan(text, toks)
    r["DG_pure"] = "CATCH" if p else "PASS"
    hits["DG_pure"] = h[0]["hit"] if h else ""
    pd, _ = DROP.r12_scan(text, toks)
    r["DG_dropin"] = "CATCH" if pd else "PASS"
    raw = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            mm = DG.DG_DROPIN_RE.search(text[:m.start()])
            if mm:
                raw.append(mm.group(0))
    hits["DG_dropin"] = raw[0] if raw else ""
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    r["H5_lit"] = "CATCH" if ml else "PASS"
    hits["H5_lit"] = ml.group(0) if ml else ""
    hg, hh = False, ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]:
                hg, hh = True, g["dn_hit"]
    r["H5_gov"] = "CATCH" if hg else "PASS"
    hits["H5_gov"] = hh
    p12, _ = G7.r12_scan(text, toks)
    r["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    r["R12_lit"] = "CATCH" if m12 else "PASS"
    hits["R12_lit"] = m12.group(0) if m12 else ""
    return r, hits


# ---- 静态抽取 CASES / FORCED（ast.literal_eval，不执行该脚本）----
tree = ast.parse((DGA / '_dga_adversarial.py').read_text(encoding='utf-8'))
assign = {}
for n in tree.body:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name):
                try:
                    assign[t.id] = ast.literal_eval(n.value)
                except Exception:
                    pass
CASES, FORCED = assign['CASES'], assign['FORCED']
print('=== (0) 41 条 CASES 静态抽取 ===')
print('  CASES n =', len(CASES), ' FORCED =', FORCED)

# ---- 零精确重合：AST 抽 4 个训练源全部字符串常量 ----
TRAIN_SRC = [DG_DIR / '_dg_step34.py', DG_DIR / '_dgv_probe.py',
             DG_DIR / '_dgv_neg2.py', DG_DIR / '_dg_step1.py']
counts, all_train = [], set()
for p in TRAIN_SRC:
    s = {n.value for n in ast.walk(ast.parse(p.read_text(encoding='utf-8')))
         if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    counts.append((p.name, len(s)))
    all_train |= s
my = {c[2] for c in CASES}
ov = sorted(my & all_train)
print('=== (1) 零精确重合 ===')
print('  训练集逐件抽取串数 =', counts, ' 并集 =', len(all_train))
print('  与全部训练集精确重合 =', len(ov), ov)

# ---- 41 条逐条六判定器 ----
rows = []
print('=== (2) 41 条逐条六判定器 + hits ===')
for cid, shape, text, exp, why, attack in CASES:
    r, hits = detect(text)
    rows.append({'id': cid, 'shape': shape, 'text': text, 'expect': exp,
                 'why': why, 'attack': attack, 'verdicts': r, 'hits': hits,
                 'forced': FORCED.get(cid, exp)})
    print('  %-4s exp=%-5s DG_p=%-5s DG_d=%-5s H5_l=%-5s H5_g=%-5s R12=%-5s R12_l=%-5s hit_p=%s'
          % (cid, exp, r['DG_pure'], r['DG_dropin'], r['H5_lit'], r['H5_gov'],
             r['R12'], r['R12_lit'], repr(hits['DG_pure'])))


def score(key, forced=False):
    fp, fn, amb, fpi, fni = 0, 0, 0, [], []
    for x in rows:
        exp = x['forced'] if forced else x['expect']
        if exp == 'AMBIG':
            amb += 1
            continue
        got = x['verdicts'][key]
        if exp == 'PASS' and got == 'CATCH':
            fp += 1; fpi.append(x['id'])
        elif exp == 'CATCH' and got == 'PASS':
            fn += 1; fni.append(x['id'])
    n = len(rows) if forced else len(rows) - amb
    return n, fp, fn, fpi, fni


print('=== (3) strict（排除 5 条 AMBIG）===')
for k in DETECTORS:
    n, fp, fn, fpi, fni = score(k)
    print('  %-9s n=%d fp=%d %s fn=%d %s' % (k, n, fp, fpi, fn, fni))
print('=== (4) forced（41 条全计）===')
for k in DETECTORS:
    n, fp, fn, fpi, fni = score(k, forced=True)
    print('  %-9s n=%d fp=%d fn=%d' % (k, n, fp, fn))

# ---- 与编排方【41 条形态】给定的 DG_pure hits 逐条比对 ----
TASK_HITS = {
    'P01': '', 'P02': '', 'P03': '', 'P04': '', 'P05': '',
    'P06': '不敢不承认', 'P07': '不敢不承认', 'P08': '并不否认', 'P09': '并不否认',
    'P10': '并不否认', 'P11': '并非不宣告', 'P12': '并不否认', 'P13': '', 'P14': '',
    'P15': '', 'P16': '', 'P17': '',
    'C01': '', 'C02': '', 'C03': '', 'C04': '', 'C05': '',
    'C06': '非登记五份原件不可', 'C07': '', 'C08': '', 'C09': '', 'C10': '',
    'C11': '', 'C12': '', 'C13': '何尝不认为', 'C14': '不见得不认为',
    'C15': '岂敢不承认', 'C16': '不由得不承认', 'C17': '并非不宣告',
    'C18': '亦非不宣告', 'C19': '并非不宣告', 'C20': '不是不承认',
    'A01': '不否认', 'A02': '并不否认', 'A03': '不无', 'A04': ''}
mism = [(x['id'], TASK_HITS[x['id']], x['hits']['DG_pure'])
        for x in rows if x['hits']['DG_pure'] != TASK_HITS[x['id']]]
print('=== (5) 41 条 DG_pure hits 与编排方形态分布逐条比对 ===')
print('  不一致 =', mism, '  全同 =', len(mism) == 0)

# ---- C06 判对核验（纠偏「十二条漏判」）----
c06 = next(x for x in rows if x['id'] == 'C06')
print('=== (6) C06 判对核验 ===')
print('  C06 DG_pure =', c06['verdicts']['DG_pure'], ' hit =', repr(c06['hits']['DG_pure']))
print('  strict DG_pure fn 名单 =', score('DG_pure')[4])
print('  实际漏判条数 =', len(score('DG_pure')[4]))

# ---- 九件指纹再算 ----
print('=== (7) 九件指纹 hashlib 复算 ===')
EXP = [
 ('lead/dg_adversarial_20261109/DG_ADVERSARIAL.md','e821f91df2add452b239053f69622025d654df40cbb6a6d62536073202cf0deb',42689),
 ('lead/dg_adversarial_20261109/_dga_adversarial_out.json','395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c',55528),
 ('lead/dg_adversarial_20261109/_dga_adversarial.py','e94e29be01d62abeeb58e76570306e5bcbd46a2d706647d7a0269c0d271cd27b',29736),
 ('lead/dneg_generative_20261109/_dg_core.py','7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1',12322),
 ('lead/dneg_generative_20261109/DNEG_GENERATIVE.md','94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4',46334),
 ('lead/h5_governance_20261109/_h5_pasteable.py','b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c',8540),
 ('lead/gate_fp7_20261108/_g7_predicates.py','02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120',11743),
 ('lead/PENDING_DECISIONS.md','3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7',52419),
 ('lead/GOAL_THREE_TARGETS_20261018.md','2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede',759518)]
ok = True
for rel, sh, n in EXP:
    b = (B / rel).read_bytes()
    ok &= (hashlib.sha256(b).hexdigest() == sh and len(b) == n)
print('  ALL_9_MATCH =', ok)
print('BASELINE_SELF_RUN_DONE')
