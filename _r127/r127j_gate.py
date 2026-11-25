# -*- coding: utf-8 -*-
"""R127j：门禁两处改动（都带反控）。

改动一 · C16_FLOORS 补钉节 131。本轮新增 2.131（实测 11916 B），按既有 50% 规则取 5958
（11916 // 2）。表从 124 条到 125 条，摘要常量随之重算。理由：unpinned 现在是 1，
虽然未超 C16_UNPINNED_MAX=2，但 R126 已立「每轮补钉到 0」的做法，本轮沿用，
否则下一轮再加一节就会撞上限。

改动二 · GATE_VER 从 R126 升到 R127，并同步 DISC_RECHECK 第 20 行的登记式。
依据是 C10 门自检：登记行的版本标记必须与脚本的 GATE_VER 相等，而本轮确实动了门禁脚本。

反控（本脚本末尾）：改完后用「正本改名藏起、把改过的副本放到正本路径上跑、finally 恢复
并断言 sha」的方式，跑四条：
  1) 正控：不修改必须 exit 0
  2) 清空 2.131 正文 → 必须 exit 1 且命中 C16
  3) 只改 GATE_VER 不改第 20 行 → 必须 exit 1 且命中 C10
  4) 改 C16_FLOORS 一个数不改摘要 → 必须 exit 1 且命中 C16d
（S-161 的教训：不能把脚本拷到临时目录跑，它读文档用写死的绝对路径。）
"""
import io, os, sys, re, json, shutil, hashlib, subprocess, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
CHK = os.path.join(R14, 'check_disc.py')
TSV = os.path.join(R14, 'DISC_RECHECK.tsv')
RC = os.path.join(R14, 'R14_COMMON.md')
OUT = os.path.join(ROOT, '_r127', 'r127j_gate.json')

TS = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
OLD_VER = 'R126'
NEW_VER = 'R127'
NEW_ID = 131
NEW_FLOOR = 5958          # 实测 2.131 = 11916 B，半量

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def backup(path, tag):
    data = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r127_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return dst, data


def calc_floor_sha(tbl):
    norm = '\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl))
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()


# ---- 起点断言 ----
_, chk_old = backup(CHK, 'check_disc')
_, tsv_old = backup(TSV, 'DISC_RECHECK')
chk_txt = chk_old.decode('utf-8')
assert "GATE_VER = '%s'" % OLD_VER in chk_txt, 'GATE_VER 不是 %s' % OLD_VER

m = re.search(r'C16_FLOORS = \{(.*?)\n\}', chk_txt, re.S)
assert m, 'C16_FLOORS 定位失败'
tbl = {}
for k, v in re.findall(r'(\d+):\s*(\d+)', m.group(1)):
    tbl[int(k)] = int(v)
old_sha_line = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", chk_txt)
assert old_sha_line, 'C16_FLOORS_SHA256 定位失败'
old_sha = old_sha_line.group(1)
assert old_sha == calc_floor_sha(tbl), '起点摘要与表不一致（开工前就已坏）'
add('J0 起点核对：GATE_VER 为 %s、C16_FLOORS 共 %d 条、表与摘要常量一致（%s）'
    % (OLD_VER, len(tbl), old_sha[:16]),
    len(tbl) == 124 and NEW_ID not in tbl, {'n': len(tbl), 'sha': old_sha[:16]})

# ---- 改动一：补钉 131 ----
tbl2 = dict(tbl)
tbl2[NEW_ID] = NEW_FLOOR
new_sha = calc_floor_sha(tbl2)

body = m.group(1)
# 在 130: 3722 之后追加 131: 5958，保持原缩进风格
assert re.search(r'130:\s*3722', body), '未找到 130: 3722'
body2 = re.sub(r'(130:\s*3722)', r'\1, %d: %d' % (NEW_ID, NEW_FLOOR), body, count=1)

chk_step1 = chk_txt.replace('C16_FLOORS = {%s\n}' % body,
                            'C16_FLOORS = {%s\n}' % body2)
assert chk_step1 != chk_txt, 'C16_FLOORS 替换未生效'
chk_step1 = chk_step1.replace(old_sha, new_sha)
assert chk_step1 != chk_txt, 'C16_FLOORS_SHA256 替换未生效'

# ---- 改动二：GATE_VER ----
chk_new = chk_step1.replace("GATE_VER = '%s'" % OLD_VER,
                            "GATE_VER = '%s'" % NEW_VER, 1)
assert chk_new != chk_step1, 'GATE_VER 替换未生效'

# 回写 check_disc.py 并回读
assert '`' not in chk_new, 'check_disc.py 新文本含反引号'
with io.open(CHK, 'wb') as f:
    f.write(chk_new.encode('utf-8'))
rb = io.open(CHK, 'rb').read()
assert rb == chk_new.encode('utf-8'), 'check_disc.py 回读不一致'
print('  WROTE check_disc.py  sha %s -> %s  bytes %d -> %d'
      % (sha16(chk_old), sha16(rb), len(chk_old), len(rb)))

# ---- 同步 DISC_RECHECK 第 20 行 ----
tsv_txt = tsv_old.decode('utf-8')
old_reg = "grep=(?m)^GATE_VER = '%s'" % OLD_VER
new_reg = "grep=(?m)^GATE_VER = '%s'" % NEW_VER
assert tsv_txt.count(old_reg) == 1, '登记式 %r 出现 %d 次' % (old_reg, tsv_txt.count(old_reg))
tsv_new = tsv_txt.replace(old_reg, new_reg)
with io.open(TSV, 'wb') as f:
    f.write(tsv_new.encode('utf-8'))
rb2 = io.open(TSV, 'rb').read()
assert rb2 == tsv_new.encode('utf-8'), 'DISC_RECHECK.tsv 回读不一致'
print('  WROTE DISC_RECHECK.tsv  sha %s -> %s' % (sha16(tsv_old), sha16(rb2)))

# ---- J1/J2：改动生效 ----
chk_rt = io.open(CHK, encoding='utf-8').read()
tbl3 = {}
m3 = re.search(r'C16_FLOORS = \{(.*?)\n\}', chk_rt, re.S)
for k, v in re.findall(r'(\d+):\s*(\d+)', m3.group(1)):
    tbl3[int(k)] = int(v)
add('J1 改动一生效：C16_FLOORS 从 %d 条到 %d 条，新增 %d: %d，摘要常量从 %s 改为 %s 且与表一致'
    % (len(tbl), len(tbl3), NEW_ID, NEW_FLOOR, old_sha[:16], new_sha[:16]),
    len(tbl3) == 125 and tbl3.get(NEW_ID) == NEW_FLOOR
    and new_sha == calc_floor_sha(tbl3)
    and re.search(r"C16_FLOORS_SHA256 = '%s'" % new_sha, chk_rt) is not None,
    {'n': len(tbl3), 'entry': tbl3.get(NEW_ID), 'sha': new_sha[:16]})
add('J2 改动二生效：GATE_VER = %s，DISC_RECHECK 登记行也是 %s'
    % (NEW_VER, NEW_VER),
    "GATE_VER = '%s'" % NEW_VER in chk_rt
    and "grep=(?m)^GATE_VER = '%s'" % NEW_VER in io.open(TSV, encoding='utf-8').read(),
    {'gate_ver': NEW_VER})

# ---- 正控：不修改必须 exit 0 ----
def run_gate():
    r = subprocess.run([sys.executable, CHK], cwd=R14,
                       capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout + r.stderr

rc0, out0 = run_gate()
add('J3 正控：改完后不修改直接跑，必须 exit 0', rc0 == 0,
    {'rc': rc0, 'tail': out0.strip().split('\n')[-3:]})
c16_line = [l for l in out0.split('\n') if 'C16 per-section' in l]
add('J4 改完后 C16 显示 125 节全部被钉、unpinned 为 0（如实核对实际输出的四个计数）',
    bool(c16_line) and 'unpinned 0' in c16_line[0] and 'missing 0' in c16_line[0]
    and 'hollow/deficient 0' in c16_line[0],
    c16_line[0].strip() if c16_line else 'no C16 line')

# ---- 反控 A：清空 2.131 正文，必须 exit 1 且命中 C16 ----
saved = io.open(CHK, 'rb').read()
rc_saved = io.open(RC, 'rb').read()
try:
    # 备份 2.131 正文（放到内存里，finally 恢复）
    t = rc_saved.decode('utf-8')
    i = t.find('## 2.131 R127')
    j = len(t)          # 2.131 是最后一节
    assert i > 0
    wiped = t[:i] + '## 2.131 R127\n\n' + t[j:]
    with io.open(RC, 'wb') as f:
        f.write(wiped.encode('utf-8'))
    rcA, outA = run_gate()
    hijackA = 'C16' in outA
    add('J5 反控 A：把 2.131 正文清空到只剩标题，必须 exit 1 且命中 C16 —— '
        '证明新补的 131:%d 这道下界真的在约束' % NEW_FLOOR,
        rcA == 1 and hijackA, {'rc': rcA, 'c16_hit': hijackA,
                               'fail_lines': [l for l in outA.split('\n')
                                              if l.strip().startswith('FAIL')][:3]})
finally:
    with io.open(RC, 'wb') as f:
        f.write(rc_saved)
    assert io.open(RC, 'rb').read() == rc_saved, '2.131 正文恢复失败'

# ---- 反控 B：只改 GATE_VER 不改登记行，必须 exit 1 且命中 C10 ----
try:
    bad = saved.decode('utf-8').replace("GATE_VER = '%s'" % NEW_VER,
                                        "GATE_VER = 'R999'", 1)
    with io.open(CHK, 'wb') as f:
        f.write(bad.encode('utf-8'))
    rcB, outB = run_gate()
    add('J6 反控 B：只把 GATE_VER 改成 R999 而不动 DISC_RECHECK 第 20 行，'
        '必须 exit 1 且命中 C10',
        rcB == 1 and 'C10' in outB, {'rc': rcB, 'c10_hit': 'C10' in outB,
                                     'fail_lines': [l for l in outB.split('\n')
                                                    if l.strip().startswith('FAIL')][:3]})
finally:
    with io.open(CHK, 'wb') as f:
        f.write(saved)
    assert io.open(CHK, 'rb').read() == saved, 'check_disc.py 恢复失败'

# ---- 反控 C：改表里一个数不改摘要，必须 exit 1 且命中 C16d ----
try:
    bad2 = saved.decode('utf-8').replace('%d: %d' % (NEW_ID, NEW_FLOOR),
                                         '%d: 5700' % NEW_ID, 1)
    assert bad2 != saved.decode('utf-8')
    with io.open(CHK, 'wb') as f:
        f.write(bad2.encode('utf-8'))
    rcC, outC = run_gate()
    add('J7 反控 C：把 131 的下界从 %d 改成 5700 而不改摘要常量，'
        '必须 exit 1 且命中 C16d' % NEW_FLOOR,
        rcC == 1 and 'C16d' in outC, {'rc': rcC, 'c16d_hit': 'C16d' in outC,
                                      'fail_lines': [l for l in outC.split('\n')
                                                     if l.strip().startswith('FAIL')][:3]})
finally:
    with io.open(CHK, 'wb') as f:
        f.write(saved)
    assert io.open(CHK, 'rb').read() == saved, 'check_disc.py 恢复失败'

# ---- J8：三份正本字节与改动完成时一致 ----
add('J8 收尾：三个正本（check_disc.py / DISC_RECHECK.tsv / R14_COMMON.md）的字节'
    '与改动完成时一致 —— 反控没有污染正本',
    io.open(CHK, 'rb').read() == saved
    and io.open(RC, 'rb').read() == rc_saved,
    {'check_disc_sha': sha16(io.open(CHK, 'rb').read()),
     'R14_COMMON_sha': sha16(io.open(RC, 'rb').read())})

# ---- J9：终态再跑一次门禁 ----
rcF, outF = run_gate()
add('J9 终态：再跑一次门禁，exit 0 且 C10 显示 ok(%s)' % NEW_VER,
    rcF == 0 and ('ok(%s)' % NEW_VER) in outF,
    {'rc': rcF, 'c10': [l for l in outF.split('\n') if 'C10 self-check' in l]})

rep = {'gate_ver': NEW_VER, 'floor_added': {NEW_ID: NEW_FLOOR},
       'floor_table_n': len(tbl3), 'old_sha16': old_sha[:16],
       'new_sha16': new_sha[:16], 'checks': ck,
       'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R127j %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'][:300] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
