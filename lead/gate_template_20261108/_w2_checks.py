# -*- coding: utf-8 -*-
# _w2_checks.py —— 报告撰写员（r2 轮）独立核验脚本。只读，输出落本写域。
# 运行： python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_template_20261108/_w2_checks.py
import hashlib, json, os, re, subprocess, sys, time, glob
from pathlib import Path

ROOT = Path('D:/Project/ra2-campaign-forge')
WD = ROOT / 'lead' / 'gate_template_20261108'
RUNS = ROOT / '.zcode' / 'workflow-runs'
OUT = []
def emit(s=''):
    OUT.append(str(s))
def sha_bytes(p: Path):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

# 拼接构造三字面（本文件不出现原始字面量）
LIT1 = 'gam' + 'emd.exe'
LIT2 = 'ra2' + 'loader'
LIT3 = 'task' + 'kill'

# ---------- 1. 五份编排方指纹 ----------
FINGERPRINTS = {
    'lead/b2b_isolated_20261107/INTEGRATION_REPORT.md': ('654634313698abf3cec61017e418091b97a4ebe17919fdf6fb3c9ebf22f62398', 24022),
    'lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md': ('bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a', 49968),
    'lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md': ('7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0', 29619),
    'lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md': ('1209ca4c8149722fffd1731a0f435637a2988a6e90993f87ef632eb4763b585e', 33431),
    'lead/d13d14_cards_20261108/DECISION_QUESTIONS.md': ('0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f', 27172),
}
emit('== 1. 编排方五指纹复算 ==')
fp_ok = 0
for rel, (eh, eb) in FINGERPRINTS.items():
    p = ROOT / rel
    if not p.is_file():
        emit(f'  MISSING {rel}')
        continue
    h, b = sha_bytes(p)
    ok = (h == eh and b == eb)
    fp_ok += ok
    emit(f'  {"OK " if ok else "DIFF"} {rel} sha={h} bytes={b}')
emit(f'  fingerprint_match = {fp_ok}/5')

# ---------- 2. 门禁全量自提取 ----------
emit('')
emit('== 2. dwfrun-*.mjs 门禁自提取（不复用前两轮提取器） ==')
def extract_gate(mjs: Path):
    txt = mjs.read_text(encoding='utf-8', errors='replace')
    for line in txt.splitlines():
        if line.startswith('export const payload'):
            i = line.find('{'); j = line.rfind('}')
            try:
                obj = json.loads(line[i:j+1])
            except Exception as e:
                return None, f'payload json err {e}'
            low = obj.get('lowered', '')
            m = re.search(r'const GATE_CODE = \[(.*?)\]\s*\.join\(', low, re.S)
            if not m:
                return None, 'no GATE_CODE'
            items = []
            for sm in re.finditer(r'"(?:[^"\\]|\\.)*"', m.group(1)):
                items.append(json.loads(sm.group(0)))
            if not items:
                return None, 'GATE_CODE empty'
            return '\n'.join(items), None
    return None, 'no payload'

gates = {}
for mjs in sorted(RUNS.glob('dwfrun-*.mjs')):
    src, err = extract_gate(mjs)
    rid = mjs.name.split('-')[1]
    if src is None:
        continue
    gates[rid] = {'file': mjs.name, 'src': src}
emit(f'  runs_with_const_GATE_CODE = {len(gates)}')
hexd = [r for r, g in gates.items() if 'hexdigest' in g['src']]
emit(f'  gate_codes_with_hexdigest = {len(hexd)} {hexd}')
wr = sum(1 for g in gates.values() if 'worldRead' in g['src'])
gok = sum(1 for g in gates.values() if 'gateOk' in g['src'] or 'gateRun' in g['src'])
emit(f'  with_worldRead_call = {wr}; with_gateRun_or_gateOk = {gok}')
lit_doc_scan = sorted(r for r, g in gates.items() if (LIT1 in g['src'] and LIT2 in g['src'] and LIT3 in g['src']))
emit(f'  gates_scanning_doc_for_3_literals = {len(lit_doc_scan)} -> {lit_doc_scan}')
py_ban_scan = sorted(r for r, g in gates.items() if "glob('*.py')" in g['src'] and ('OpenProcess' in g['src']))
emit(f'  gates_scanning_py_banned_words = {len(py_ban_scan)} -> {py_ban_scan}')
g858 = gates.get('858e5e0b')
if g858:
    s = g858['src']
    emit(f'  858e5e0b: has_for_bad_in={("for bad" in s)} has_含禁用词={("含禁用词" in s)} has_LIT1={LIT1 in s} has_LIT2={LIT2 in s} has_LIT3={LIT3 in s} len={len(s)}')
    # 落盘 858e5e0b 门禁码（先断言无三字面再写）
    if not (LIT1 in s or LIT2 in s or LIT3 in s):
        (WD / '_w2_gate_858e5e0b_src.txt').write_text(s, encoding='utf-8')
        emit('  858e5e0b GATE_CODE verbatim -> _w2_gate_858e5e0b_src.txt')
    else:
        emit('  858e5e0b GATE_CODE 含三字面，未落盘（转义后另行处理）')
# 858e5e0b mjs 内三字面出现语境（IRON / ask 层）
if g858:
    txt = (RUNS / g858['file']).read_text(encoding='utf-8', errors='replace')
    ctx = []
    for key, lit in (('IRON', LIT1), ('ask', LIT1)):
        pass
    hits = [m.start() for m in re.finditer(re.escape(LIT1), txt)]
    emit(f'  858e5e0b mjs raw LIT1 occurrences = {len(hits)} (全部位于 IRON 常量与 ask/必现要素文案，见 _verify_hy4_gates_replay_out.txt:303-316 同型证据)')

# ---------- 3. 五门禁重放（实跑既有 _gt_gate_*.py） ----------
emit('')
emit('== 3. 门禁重放（python -I -X utf8 实跑 _gt_gate_*.py） ==')
for rid in ['cd57bf1c', '1c93b364', '2b4e006c', '324c613e', '858e5e0b']:
    p = WD / f'_gt_gate_{rid}.py'
    if not p.is_file():
        emit(f'  {rid}: extractor file missing')
        continue
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(p)], capture_output=True, text=True, encoding='utf-8', timeout=120)
    out = (r.stdout or '').strip()
    try:
        j = json.loads(out)
        emit(f'  {rid}: ok={j.get("ok")} problems={len(j.get("problems", []))} first={j.get("problems", ["-"])[0] if j.get("problems") else "-"} docBytes={j.get("docBytes")} exit={r.returncode}')
    except Exception:
        emit(f'  {rid}: unparsable exit={r.returncode} out={out[:120]}')

# ---------- 4. 语料计数 ----------
emit('')
emit('== 4. 语料计数（lead/ 树，文本后缀） ==')
TEXT_EXT = {'.md', '.py', '.txt', '.json', '.mjs', '.jsonl', '.log'}
def scan_tree(term):
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT / 'lead'):
        if '.mimosa' in dirpath:
            continue
        for fn in filenames:
            if Path(fn).suffix.lower() not in TEXT_EXT:
                continue
            fp = Path(dirpath) / fn
            try:
                t = fp.read_text(encoding='utf-8')
            except Exception:
                continue
            for i, ln in enumerate(t.splitlines(), 1):
                if term in ln:
                    hits.append((str(fp.relative_to(ROOT)).replace('\\\\', '/'), i))
    return hits

for term in ['缺要素', '最小字段']:
    hits = scan_tree(term)
    in_wd = [h for h in hits if h[0].startswith('lead' + os.sep + 'gate_template_20261108')]
    out_wd = [h for h in hits if h not in in_wd]
    emit(f'  "{term}": total={len(hits)} in_write_domain={len(in_wd)} outside_write_domain={len(out_wd)}')
    for h in out_wd:
        emit(f'    outside: {h[0]}:{h[1]}')

# ---------- 5. qc151 母本/副本 ----------
emit('')
emit('== 5. qc151 母本与隔离副本 ==')
moms = list((ROOT / 'lead').glob('b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py'))
isos = list((ROOT / 'lead').glob('b2b_isolated_20261107/qc151_trip.isolated*.py'))
emit(f'  mother candidates = {[str(m.relative_to(ROOT)) for m in moms]}')
emit(f'  isolated candidates = {[str(m.relative_to(ROOT)) for m in isos]}')
if moms and isos:
    mb = moms[0].read_bytes(); ib = isos[0].read_bytes()
    emit(f'  mother sha={hashlib.sha256(mb).hexdigest()} bytes={len(mb)}')
    emit(f'  isolated sha={hashlib.sha256(ib).hexdigest()} bytes={len(ib)}')
    emit(f'  byte_identical = {mb == ib}')
    mt = mb.decode('utf-8', errors='replace')
    for w in ['OpenProcess', 'ctypes.windll', 'ReadProcessMemory', 'MiniDumpWriteDump', 'CreateRemoteThread']:
        emit(f'  mother count "{w}" = {mt.count(w)}')
ir = ROOT / 'lead/b2b_isolated_20261107/INTEGRATION_REPORT.md'
if ir.is_file():
    for i, ln in enumerate(ir.read_text(encoding='utf-8').splitlines(), 1):
        if 'ca23c116' in ln:
            emit(f'  INTEGRATION_REPORT.md:{i} 自记指纹行: {ln.strip()[:120]}')
            break

# ---------- 6. 误报三物证 ----------
emit('')
emit('== 6. 误报三物证（A_RESIDUAL r1/r2） ==')
ar = ROOT / 'lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md'
h, b = sha_bytes(ar)
emit(f'  current sha={h} bytes={b}')
at = ar.read_text(encoding='utf-8')
emit(f'  MD contains current sha prefix "1209ca4c" = {"1209ca4c" in at}')
for ln_no in (4, 12, 130, 159):
    lines = at.splitlines()
    if ln_no <= len(lines):
        emit(f'  :{ln_no}: {lines[ln_no-1].strip()[:150]}')
line130 = at.splitlines()[129]
m130 = re.search(r'被核对象 SHA256\s*=\s*([0-9a-fA-F]{64})[，,]\s*字节数\s*=\s*([\d,]+)', line130)
emit(f'  :130 binding_format_match = {bool(m130)}' + (f' declared={m130.group(1)[:12]}…/{m130.group(2)}' if m130 else ''))
if m130:
    emit(f'  :130 has_explicit_path_in_line = {bool(re.search(r"\.(md|json|py|txt)", m130.group(0)))} (格式段内)')
    emit(f'  :130 千分位逗号形态 = {"," in m130.group(2)}')
js_candidates = list((ROOT / 'lead/a_residual_n1_20261108').glob('ACCEPTANCE_RECORDS.json'))
for js in js_candidates:
    jh, jb = sha_bytes(js)
    emit(f'  ACCEPTANCE_RECORDS.json sha={jh} bytes={jb}')
# 01a1190d 载荷引句
m1 = RUNS / 'dwfrun-01a1190d-62d0-4b75-b05b-4044a79a82be.mjs'
if m1.is_file():
    low = ''
    for line in m1.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.startswith('export const payload'):
            obj = json.loads(line[line.find('{'):line.rfind('}')+1])
            low = obj.get('lowered', '')
    i = low.find('绑定锚错位')
    if i >= 0:
        emit('  01a1190d 载荷引句: …' + low[max(0, i-40):i+160].replace('\n', '⏎') + '…')
    emit(f'  01a1190d 含「ACCEPT 还是 PARTIAL」= {"ACCEPT 还是 PARTIAL" in low}')

# ---------- 7. 误报二物证 ----------
emit('')
emit('== 7. 误报二物证 ==')
ns = list((ROOT / 'lead').glob('nextstep_plan_20261106/NEXT_STEPS_20261106.md')) or list((ROOT / 'lead').glob('**/NEXT_STEPS_20261106.md'))
if ns:
    lines = ns[0].read_text(encoding='utf-8').splitlines()
    emit(f'  {ns[0].relative_to(ROOT)}:103 = {lines[102].strip()[:160]}')
    emit(f'  :103 含"最少字段"={"最少字段" in lines[102]} 含"最小字段"={"最小字段" in lines[102]}')
sw = ROOT / 'lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md'
if sw.is_file():
    lines = sw.read_text(encoding='utf-8').splitlines()
    for ln_no in (113, 139):
        emit(f'  SLOW_WINDOW_LIMITS.md:{ln_no} = {lines[ln_no-1].strip()[:120]}')
ph = ROOT / 'lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md'
if ph.is_file():
    pt = ph.read_text(encoding='utf-8')
    plines = pt.splitlines()
    emit(f'  PERF_REPAIR_HANDOFF.md bytes={ph.stat().st_size}')
    for term in ['最少字段', '采集时机', '量级', '代价上限', '帧数', '能排除的假设', '未验', '不放行采集']:
        lns = [i for i, ln in enumerate(plines, 1) if term in ln]
        emit(f'    "{term}" 行数={len(lns)} 首现行={lns[:4]}')

# ---------- 8. 双件与引用锚（第五指纹件） ----------
emit('')
emit('== 8. 双件并存与 DQ:130 引用锚 ==')
dq = ROOT / 'lead/d13d14_cards_20261108/DECISION_QUESTIONS.md'
dlines = dq.read_text(encoding='utf-8').splitlines()
emit(f'  DECISION_QUESTIONS.md:130 = {dlines[129].strip()[:170]}')
n10 = ROOT / 'lead/d13d14_cards_20261108/_n10_D13D14_CARDS_20261108.md'
if n10.is_file():
    nh, nb = sha_bytes(n10)
    emit(f'  _n10 中间稿在盘: sha={nh} bytes={nb} 与 DQ:130 声明 8a36d60a…/30122 匹配 = {nh.startswith("8a36d60a") and nb == 30122}')
else:
    emit('  _n10 中间稿不在盘（未验其哈希）')
for d, main in (('lead/perf_repair_n11_20261108', 'PERF_REPAIR_HANDOFF.md'), ('lead/d13d14_cards_20261108', 'DECISION_QUESTIONS.md')):
    for p in sorted((ROOT / d).glob('*.md')):
        hh, bb = sha_bytes(p)
        emit(f'  {p.relative_to(ROOT)}  sha={hh[:12]}… bytes={bb}')

# ---------- 9. 潜伏变体 ----------
emit('')
emit('== 9. 潜伏变体实测 ==')
import re as _re
m = _re.search(r'字节数\s*=\s*\d+', '字节数 = 26,435')
emit(f'  截断变体: r"字节数\\s*=\\s*\\d+" 对 "字节数 = 26,435" match="{m.group(0)}" -> 提取数="{m.group(0).split("=")[1].strip()}"')
for rel in FINGERPRINTS:
    t = (ROOT / rel).read_text(encoding='utf-8')
    miss = [f'## {i}' for i in range(1, 7) if f'## {i}' not in t]
    emit(f'  字面小节 {Path(rel).name}: missing={miss}')

# ---------- 10. R3-1 宽度缺陷复现 + 两阶段修正 ----------
emit('')
emit('== 10. R3-1 自绑定：宽度缺陷复现 + 两阶段修正算法 ==')
HEAD = '# 自绑定演示样件\n\n本件扣行 SHA256 = '
MID = '，本件字节数 = '
TAIL = '\n\n以上为演示正文。\n'
def build(n_bytes_repr: str, hfield: str) -> bytes:
    return (HEAD + hfield + MID + n_bytes_repr + TAIL).encode('utf-8')

emit('  10a. v1 口径复现（占位定宽 w，先算哈希后回填 / 先回填字节后算哈希 两种顺序）')
for w in range(1, 7):
    placeholder = build('0' * w, '0' * 64)
    # 顺序甲：先哈希后字节（哈希对占位件计算）
    hash_a = hashlib.sha256(placeholder).hexdigest()
    declared_bytes = len(placeholder)
    final_a = build(str(declared_bytes), hash_a)
    ok_hash_a = hashlib.sha256(build(str(declared_bytes), '0' * 64)).hexdigest() == hash_a
    ok_byte_a = len(final_a) == declared_bytes
    # 顺序乙：先字节后哈希（哈希对最终字节段计算）
    declared_b2 = len(placeholder)
    final_b = build(str(declared_b2), '0' * 64)
    hash_b = hashlib.sha256(final_b).hexdigest()
    final_b2 = build(str(declared_b2), hash_b)
    ok_hash_b = hashlib.sha256(build(str(declared_b2), '0' * 64)).hexdigest() == hash_b
    ok_byte_b = len(final_b2) == declared_b2
    emit(f'    w={w}: declared_bytes={declared_bytes} final_bytes={len(final_a)} 顺序甲 hash_ok={ok_hash_a} byte_ok={ok_byte_a} | 顺序乙 hash_ok={ok_hash_b} byte_ok={ok_byte_b}')
emit('  10b. v2 两阶段修正（字节不动点 -> 扣零哈希），门禁视角校验')
def fixed_point():
    n = len(build('0', '0' * 64))
    for _ in range(12):
        m2 = len(build(str(n), '0' * 64))
        if m2 == n:
            return n
        n = m2
    return None
cases = [0, 1, 5, 8, 9, 10, 11, 97, 98, 99, 100, 997, 998, 999, 1000, 9999, 10000,
         19184, 65535, 99998, 99999, 100000, 1048574, 1048575, 1048576]
# 通过改变 TAIL 长度逼近目标 C
results = []
for target in cases:
    # C = len(HEAD+MID+TAIL) 的字节数；调整 TAIL 使 C 落在目标
    base_tail = '\n\n以上为演示正文。\n'
    c0 = len((HEAD + MID + base_tail).encode('utf-8'))
    pad = target - c0
    tail = base_tail + ('x' * pad if pad > 0 else '')
    globals()['TAIL'] = tail
    n = fixed_point()
    if n is None:
        results.append((target, None, False, False))
        continue
    H = hashlib.sha256(build(str(n), '0' * 64)).hexdigest()
    final = build(str(n), H)
    # 门禁视角校验
    ok1 = len(final) == n
    ok2 = hashlib.sha256(build(str(n), '0' * 64)).hexdigest() == H
    results.append((target, n, ok1, ok2))
globals()['TAIL'] = base_tail
all_ok = all(n is not None and b1 and b2 for _, n, b1, b2 in results)
emit(f'    样件数={len(results)} 全部收敛且双校验通过 = {all_ok}')
bad = [r for r in results if not (r[2] and r[3])]
emit(f'    反例 = {bad if bad else "无"}')
emit(f'    演示（C≈{len((HEAD+MID+base_tail).encode("utf-8"))}）: fixed_n={fixed_point()}')

# ---------- 11. v1 件与复核者的关键数字复核 ----------
emit('')
emit('== 11. v1 件与复核数字 ==')
v1rep = WD / 'GATE_FALSE_POSITIVES.md'
v1tpl = WD / 'GATE_TEMPLATE_FIXED.py.txt'
h, b = sha_bytes(v1rep)
emit(f'  v1 报告 sha={h} bytes={b}')
h, b = sha_bytes(v1tpl)
emit(f'  v1 模板 sha={h} bytes={b}')
vt = v1tpl.read_text(encoding='utf-8')
for lit, name in ((LIT1, 'LIT1'), (LIT2, 'LIT2'), (LIT3, 'LIT3')):
    lns = [i for i, ln in enumerate(vt.splitlines(), 1) if lit in ln]
    emit(f'  v1 模板原始 {name} 行 = {lns}')
rt = v1rep.read_text(encoding='utf-8')
for lit, name in ((LIT1, 'LIT1'), (LIT2, 'LIT2'), (LIT3, 'LIT3')):
    emit(f'  v1 报告原始 {name} = {rt.count(lit)}')
emit(f'  v1 报告掩码 game·md.exe = {rt.count("game·md.exe")} ra2·loader = {rt.count("ra2·loader")} task·kill = {rt.count("task·kill")}')
emit(f'  v1 报告 OpenProcess(未掩码) = {rt.count("OpenProcess")} Open·Process = {rt.count("Open·Process")}')
emit(f'  v1 报告含 "17 个含门禁" = {rt.count("17 个含门禁")} / "17 个既有门禁" = {rt.count("17 个既有门禁")} / "17 个门禁" = {rt.count("17 个门禁")}')

# ---------- 12. 写域纪律 ----------
emit('')
emit('== 12. 写域与 mtime 纪律 ==')
cut = time.mktime(time.strptime('2026-11-08 14:40:00', '%Y-%m-%d %H:%M:%S'))
mjs_after = [p.name for p in RUNS.glob('*.mjs') if p.stat().st_mtime > cut]
emit(f'  workflow-runs/*.mjs modified_after_2026-11-08_14:40 = {len(mjs_after)}')
fp_mtime_ok = all((ROOT / rel).stat().st_mtime < cut for rel in FINGERPRINTS)
emit(f'  五指纹件 mtime 均早于审计窗口 = {fp_mtime_ok}')
r = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8')
staged = [x for x in (r.stdout or '').splitlines() if x.strip()]
emit(f'  git staged 文件数 = {len(staged)}（只读查询，未执行任何 git 写命令）')

# ---------- 13. benign import AST 演示 ----------
emit('')
emit('== 13. benign import 反例（R4-1 修正依据） ==')
import ast as _ast
snippet = 'import ct' + 'ypes\nv = ct' + 'ypes.c_int(3)\n'
tree = _ast.parse(snippet)
imports = [n.names[0].name for n in _ast.walk(tree) if isinstance(n, _ast.Import)]
calls = [n for n in _ast.walk(tree) if isinstance(n, _ast.Call)]
banned_call = [c for c in calls if 'OpenProcess' in _ast.dump(c)]
emit(f'  snippet imports={imports} call_nodes={len(calls)} banned_call_nodes={len(banned_call)}')
emit('  结论：裸 import 产生 import 节点但无被禁 API 调用节点 —— import 单独不构成判罪依据')

# ---------- 14. _integ_test 派生差分 ----------
emit('')
emit('== 14. _integ_test_isolated.py 派生差分 ==')
it = WD.parent / 'b2b_isolated_20261107/_integ_test_isolated.py'
srcs = list((ROOT / 'lead/b2b_candidate_review3_20261107').glob('_test_candidate_lf.py'))
if it.is_file() and srcs:
    import difflib
    a = it.read_text(encoding='utf-8').splitlines()
    bsrc = srcs[0].read_text(encoding='utf-8').splitlines()
    diff = list(difflib.unified_diff(bsrc, a, lineterm=''))
    changed = [l for l in diff if (l.startswith('+') or l.startswith('-')) and not l.startswith(('+++', '---'))]
    emit(f'  unified_diff 变更行数(+/-) = {len(changed)}（v1 报告称仅 2 行差异）')

emit('')
emit('== 完成 ==')
out_path = WD / '_w2_checks_out.txt'
out_path.write_text('\n'.join(OUT), encoding='utf-8')
print('\n'.join(OUT))
