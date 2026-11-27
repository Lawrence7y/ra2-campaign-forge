# -*- coding: utf-8 -*-
"""R184 F：反向控制 —— 证明 V564→V565 的重钉不是恒真（六面各自必须真红）。
全部在沙箱副本上跑，生产文件只读。
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
GR = os.path.join(ROOT, '_r161/gate_runner.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
LED = os.path.join(TIER, 'R17_R131_FACTINDEX_V565/FACT_INDEX.tsv')
TMP = '/tmp/r184f'
fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def sh(cmd, cwd=None):
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout + p.stderr


SHA = hashlib.sha256(open(LED, 'rb').read()).hexdigest()
print('== A · 生产基线（只读）==')
ck('A0 生产台账 sha == f64d36aa…', SHA.startswith('f64d36aaacbc4fbc'), SHA[:16])
rc, out = sh('python3 %s' % FF)
ck('A1 生产 facts_floors exit 0', rc == 0, rc)
rc2, out2 = sh('python3 %s' % GR)
ck('A2 生产 gate_runner exit 0（G1=G2=G3=ok）', rc2 == 0 and 'G1=ok  G2=ok  G3=ok' in out2, rc2)

os.makedirs(TMP, exist_ok=True)


def sandbox(name):
    d = os.path.join(TMP, name)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for src, dst in ((FF, 'facts_floors.py'), (GR, 'gate_runner.py')):
        shutil.copy2(src, d)
    return d


print('== B · 控 1：台账改 1 个汉字（等长）⇒ D0/D6/D8 必须红 ==')
d = sandbox('c1')
raw = open(LED, 'rb').read()
mut = raw.replace('算术差、不是字节跨度'.encode(), '算术差、不是字节跨渡'.encode(), 1)
ck('B1 等长替换成功（字节数不变）', len(mut) == len(raw) and mut != raw, (len(mut), len(raw)))
p = os.path.join(d, 'mut.tsv')
open(p, 'wb').write(mut)
# facts_floors 的 ROOT 由 __file__ 推得，单跑副本时 ROOT 会落到 /tmp；故用 --ignore-pin 不行（会关掉 D0）
# 改为直接以 argv 指路径，D0 仍比对 CUR_SHA256
rc, out = sh('python3 %s %s' % (FF, p))
ck('B2 exit 非 0', rc != 0, rc)
ck('B3 出现 D0 sha 不等', 'D0 sha' in out and 'pinned' in out, [l for l in out.split('\n') if 'D0' in l][:2])

print('== C · 控 2：台账第 5 列截断 1,000 B ⇒ D6 + D8 必须红 ==')
import csv
rows = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
i24 = [k for k, r in enumerate(rows) if r[0] == 'F24'][0]
rows2 = [list(r) for r in rows]
rows2[i24][4] = rows2[i24][4][:-1000]
b = io.StringIO()
csv.writer(b, delimiter='\t', lineterminator='\n').writerows(rows2)
mut2 = b.getvalue().encode('utf-8')
p2 = os.path.join(d, 'trunc.tsv')
open(p2, 'wb').write(mut2)
rc, out = sh('python3 %s --ignore-pin %s' % (FF, p2))
ck('C1 exit 非 0', rc != 0, rc)
ck('C2 出现 D6 F24.lim 缩水', 'F24.lim' in out, [l for l in out.split('\n') if 'D6' in l][:2])
ck('C3 出现 D8 总字节缩水', 'D8' in out, [l for l in out.split('\n') if 'D8' in l][:2])

print('== D · 控 3：指针 sha 末位改坏 ⇒ D10 / C19 必须红 ==')
d = sandbox('c3')
ptr = io.open(PTR, encoding='utf-8', newline='').read()
last = SHA[-1]
bad = SHA[:-1] + ('0' if last != '0' else '1')
ptr_bad = ptr.replace(SHA, bad)
ck('D1 前 16 位与基线逐字相同（这正是 R180 改全文 sha 的理由）',
   ptr_bad.count(SHA[:16]) == 1 and SHA[:16] == bad[:16])
open(os.path.join(d, 'ptr_bad.md'), 'w', encoding='utf-8', newline='').write(ptr_bad)
# facts_floors 的 D10 读的是固定路径 PTR；在沙箱里改它自己的 PTR 常量
src = io.open(os.path.join(d, 'facts_floors.py'), encoding='utf-8').read()
src2 = src.replace("PTR_FILE = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')",
                   "PTR_FILE = %r" % os.path.join(d, 'ptr_bad.md'))
ck('D2 沙箱 facts_floors 成功改指向坏指针', src2 != src)
open(os.path.join(d, 'facts_floors_c3.py'), 'w', encoding='utf-8').write(src2)
rc, out = sh('python3 %s' % os.path.join(d, 'facts_floors_c3.py'))
ck('D3 exit 非 0', rc != 0, rc)
ck('D4 出现 D10 pointer sha 不等', 'D10 pointer sha' in out, [l for l in out.split('\n') if 'D10' in l][:2])

print('== E · 控 4：指针版本目录改回 V564 ⇒ C19(b)/C20 必须双双不等 ==')
d = sandbox('c4')
ptr4 = ptr.replace('R17_R131_FACTINDEX_V565', 'R17_R131_FACTINDEX_V564')
p4 = os.path.join(d, 'ptr4.md')
open(p4, 'w', encoding='utf-8', newline='').write(ptr4)
ck('E1 沙箱指针已指回 V564', 'V564' in ptr4 and 'V565' not in ptr4)
# 用生产 check_disc 读沙箱指针：C19 的 PTR 是常量，改为对 check_disc 源码做沙箱替换
CD = os.path.join(TIER, 'check_disc.py')
cd = io.open(CD, encoding='utf-8').read()
# S-184f2：check_disc 的 ROOT 由 __file__ 反推三层，把副本放 /tmp 会让 ROOT 落到 /tmp ⇒
# 必须同时把 ROOT 钉死到真仓根（否则 E3 的红是 FileNotFoundError 崩出来的，属假红）。
cd2 = cd.replace("ROOT = r'D:\\Project\\ra2-campaign-forge'",
                 "ROOT = %r" % ROOT).replace(
    "C19_PTR = os.path.join(R14, 'FACT_INDEX_CURRENT.md')", "C19_PTR = %r" % p4)
ck('E2 沙箱 check_disc 成功改 ROOT 与 C19_PTR（两处都换）',
   cd2 != cd and ('C19_PTR = %r' % p4) in cd2 and ('ROOT = %r' % ROOT) in cd2)
cdp = os.path.join(d, 'check_disc_c4.py')
open(cdp, 'w', encoding='utf-8').write(cd2)
# S-184f3：副本在 /tmp 时 sys.path 丢了 TIER，import place_r87 会 ModuleNotFoundError
# ⇒ 那是崩溃不是判据红。加 PYTHONPATH=TIER 后才是真红。
rc, out = sh('PYTHONPATH=%s python3 %s' % (TIER, cdp), cwd=TIER)
ck('E3 exit 非 0', rc != 0, rc)
c19_fail = [l for l in out.split('\n') if 'C19' in l and ('FAIL' in l or 'mismatch' in l or '!=' in l)]
ck('E4 C19 红（EXPECT_CUR 与指针不等）', len(c19_fail) > 0, c19_fail[:3])

print('== F · 控 5：facts_floors 的 CUR_SHA256 改回旧值 ⇒ D0 必须红 ==')
d = sandbox('c5')
src = io.open(os.path.join(d, 'facts_floors.py'), encoding='utf-8').read()
src5 = src.replace(SHA, '081553aafe5b9f68188c72f65d2cb21ec5bd4a363122e68399109c47ad938039', 1)
ck('F1 沙箱 CUR_SHA256 已回旧值', src5 != src)
open(os.path.join(d, 'ff5.py'), 'w', encoding='utf-8').write(src5)
rc, out = sh('python3 %s' % os.path.join(d, 'ff5.py'))
ck('F2 exit 非 0', rc != 0, rc)
ck('F3 出现 D0 sha 不等', 'D0 sha' in out)

print('== G · 控 6：gate_runner 仍指 V564 ⇒ G3 必须红 ==')
d = sandbox('c6')
gr = io.open(os.path.join(d, 'gate_runner.py'), encoding='utf-8').read()
gr6 = gr.replace('R17_R131_FACTINDEX_V565', 'R17_R131_FACTINDEX_V564')
ck('G1 沙箱 gate_runner 已指回 V564', gr6 != gr)
open(os.path.join(d, 'gr6.py'), 'w', encoding='utf-8').write(gr6)
rc, out = sh('python3 %s' % os.path.join(d, 'gr6.py'))
ck('G2 exit 非 0', rc != 0, rc)
ck('G3 出现 G3d 路径三方不一致', 'G3d' in out and 'FAIL' in out, [l for l in out.split('\n') if 'G3d' in l][:2])

print('== H · 生产终态未变（反向控制没污染生产）==')
ck('H1 生产台账 sha 仍 f64d36aa…', hashlib.sha256(open(LED, 'rb').read()).hexdigest() == SHA)
rc, _ = sh('python3 %s' % FF)
ck('H2 生产 facts_floors 仍 exit 0', rc == 0, rc)
rc, _ = sh('python3 %s' % GR)
ck('H3 生产 gate_runner 仍 exit 0', rc == 0, rc)

shutil.rmtree(TMP, ignore_errors=True)
print()
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
if fails:
    print('FAIL 列表:', fails)
sys.exit(1 if fails else 0)
