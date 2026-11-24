# -*- coding: utf-8 -*-
# 独立审计反控实验：全部在原件的隔离沙箱副本上进行，不改原件。
import os, io, shutil, subprocess, sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
BS = chr(92)
BASE = 'D:' + BS + 'Project' + BS + 'ra2-campaign-forge'
R14 = os.path.join(BASE, 'lead', 'next_re_20261117_r14')
REPORT = os.path.join(R14, 'R17_R90_T4_AUDITGATE')
SB = os.path.join(REPORT, '_sandbox')
T = chr(9); NL = chr(10)

def wipe():
    if os.path.isdir(SB): shutil.rmtree(SB)
    os.makedirs(os.path.join(SB, 'lead', 'next_re_20261117_r14'), exist_ok=True)

tsvp = os.path.join(R14, 'DISC_RECHECK.tsv')
raw = io.open(tsvp, encoding='utf-8', newline='').read()
rels = []
for line in raw.split(NL)[1:]:
    if not line: continue
    c = line.split(T)
    if len(c) >= 5:
        p = c[4].strip()
        if p and p != '（文档内锚）': rels.append(p)
rels += ['lead' + BS + 'next_re_20261117_r14' + BS + 'DISC_RECHECK.tsv',
         'lead' + BS + 'next_re_20261117_r14' + BS + 'R14_COMMON.md',
         'lead' + BS + 'next_re_20261117_r14' + BS + 'STATUS_BOARD.md',
         'lead' + BS + 'GOAL_THREE_TARGETS_20261018.md']

def populate():
    for rel in rels:
        f = rel.replace(BS, '/')
        src = os.path.join(BASE, f); dst = os.path.join(SB, f)
        if not os.path.isfile(src): print('MISSING SOURCE', rel); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

wipe(); populate()
code = io.open(os.path.join(R14, 'check_disc.py'), encoding='utf-8', newline='').read()
lines = code.split(NL)
root_idx = [i for i, l in enumerate(lines) if l.startswith('ROOT = r')]
assert len(root_idx) == 1, 'ROOT line not found uniquely'
lines[root_idx[0]] = "ROOT = r'" + SB.replace(BS, BS + BS) + "'"
chk = os.path.join(SB, 'check_sandbox.py')
io.open(chk, 'w', encoding='utf-8', newline='').write(NL.join(lines))

env = dict(os.environ); env['PYTHONIOENCODING'] = 'utf-8'
def run(tag):
    r = subprocess.run([sys.executable, chk], cwd=SB, capture_output=True, text=True, encoding='utf-8', env=env)
    tail = (NL + 'STDERR:' + r.stderr.rstrip()) if r.stderr.strip() else ''
    print('===== ' + tag + ' exit=' + str(r.returncode) + ' =====')
    print(r.stdout.rstrip() + tail)
    return r.returncode

def sbtsv():
    return os.path.join(SB, 'lead', 'next_re_20261117_r14', 'DISC_RECHECK.tsv')
def restore_tsv():
    shutil.copy2(tsvp, sbtsv())
def edit_tsv(a, b):
    t = io.open(sbtsv(), encoding='utf-8', newline='').read()
    assert a in t, 'pattern not found: ' + a
    io.open(sbtsv(), 'w', encoding='utf-8', newline='').write(t.replace(a, b, 1))

print('CURRENT check_disc.py byte size =', os.path.getsize(os.path.join(R14, 'check_disc.py')))
run('A baseline')
# B: exists 行内容替换（纪律3 anchor_check.txt 声明 exists ✓(911 B)，改成 1 字节）
ap = os.path.join(SB, 'lead', 'next_re_20261117_r14', 'R17_R61_FACTINDEX_V58', 'anchor_check.txt')
orig = io.open(ap, 'rb').read()
io.open(ap, 'wb').write(b'X')
run('B exists-row artifact replaced by 1 byte')
io.open(ap, 'wb').write(orig)
# C: rows=1468 内容被改、行数不变
p22 = os.path.join(SB, 'lead', 'next_re_20261117_r14', 'R17_R84_T1_NARRATIVE', 'should_exclude.tsv')
t = io.open(p22, encoding='utf-8', errors='replace', newline='').read()
ls = t.split(NL); ls[0] = 'X' + ls[0]
io.open(p22, 'w', encoding='utf-8', newline='').write(NL.join(ls))
run('C rows=1468 content corrupted, row count unchanged')
shutil.copy2(os.path.join(BASE, 'lead', 'next_re_20261117_r14', 'R17_R84_T1_NARRATIVE', 'should_exclude.tsv'), p22)
# D: 期望数写错（复现 §2.41 反控1）
restore_tsv(); edit_tsv('rows=1468', 'rows=9999'); run('D wrong expected rows -> expect FAIL'); restore_tsv()
# E: 文件不存在（复现 §2.41 反控2）
edit_tsv('should_exclude.tsv', 'NO_SUCH_FILE_XYZ.tsv'); run('E missing artifact -> expect FAIL'); restore_tsv()
# F: 非法校验式
edit_tsv('rows=1468', 'rows=abc'); run('F bad expr -> expect BAD_EXPR FAIL'); restore_tsv()
# G: C6 灌入 100 条宽松「纪律 N」命中
prc = os.path.join(SB, 'lead', 'next_re_20261117_r14', 'R14_COMMON.md')
t = io.open(prc, encoding='utf-8', newline='').read()
io.open(prc, 'w', encoding='utf-8', newline='').write(t + NL + ('违纪律 7 测试' + NL) * 100)
run('G C6 flooded -> exit should stay 0')
shutil.copy2(os.path.join(R14, 'R14_COMMON.md'), prc)
# H: 第7列造假（无 -> 有，实际未回跑）
edit_tsv('无（仅立条当轮自带）', '有（后续轮回跑）'); run('H flip 无->有 without real re-run -> expect PASS'); restore_tsv()
# I: 第3列判据涂改成垃圾
edit_tsv('**纪律 3 · 核验器必须把「未核验」单列', 'GARBAGE-CRITERION'); run('I col3 criterion garbage -> expect PASS'); restore_tsv()
# J: 第2列节号改成不存在的 §9.99（C8 测试）
edit_tsv(T + '§2.14' + T, T + '§9.99' + T); run('J section -> §9.99 -> expect C8 FAIL'); restore_tsv()
# L: bytes=N 分支（找一条 bytes 行——本表没有，验证 C7 是否真有 bytes 断言）
print('bytes= rows in TSV =', sum(1 for l in raw.split(NL) if 'bytes=' in l))
shutil.rmtree(SB)
print('SANDBOX REMOVED')
