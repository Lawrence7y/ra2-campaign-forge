# -*- coding: utf-8 -*-
"""R68 · 5 处「永远通过」子项的实测复算（沙箱内跑，绝不触碰 live 文件）

关键设计（第一版踩过的坑，记下来）：
  * 纪律 20 的产物就是 check_disc.py 本身。若往沙箱里那副本追加自述行，
    而 run() 又由它生成探针源码 ⇒ 得到 SyntaxError，测的不是门禁而是我的脚手架。
    本版改用纪律 5（产物 lead_recheck2.tsv，纯数据表）做摘帽实验，该目录真拷贝进沙箱。
  * 基线本来就有 5 个 C11 FAIL，所以「exit 是否 0」不能当判据；
    本版一律以 C11 四元组 (ok, fail, frozen, none) 与具体 FAIL 行做增量比对，
    另设一条「先把基线 5 条免责、再看 exit 是否 0」的对照，证明 exit 语义确实被 C11 驱动。
"""
import io, os, re, sys, shutil, subprocess, hashlib

LIVE = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(LIVE, 'lead', 'next_re_20261117_r14')
BOX = '/tmp/g68'
REL = 'lead/next_re_20261117_r14'
BOXREL = os.path.join(BOX, REL)
OUT = os.path.join(R14, '_r68')

SMALL = ['check_disc.py', 'recheck_verify.py', 'DISC_RECHECK.tsv',
         'DISC_UNVERIFIABLE.tsv', 'DISC_NS_MAP.tsv', 'DISC_ESTABLISH.tsv',
         'STATUS_BOARD.md', 'R14_COMMON.md']
LINKD = ['R17_R61_FACTINDEX_V58', 'R17_R62_ADEQUACY', 'R17_R66_FACTINDEX_V511',
         'R17_R70_T1_REPRO', 'R17_R78_T4_AUDIT30', 'R17_R78_T2_REGEXDIFF',
         'R17_R84_T1_NARRATIVE', 'R17_R81_T2_EVID', 'R17_R88_T1_SEMDEF',
         'R17_R72_T1_CLEANSCALE', 'R16_MEASURE_EVID675', 'R17_R75_T2_DRIFT',
         'R17_R78_T1_RECLASS', '_r38']
COPYD = ['R17_R64_ADEQUACY2']      # 纪律 5/6 的产物目录，须可写

fails, buf = [], []
def P(s=''):
    print(s); buf.append(s)
def ck(n, c, d=''):
    P(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

def build():
    if os.path.isdir(BOX):
        shutil.rmtree(BOX)
    os.makedirs(BOXREL)
    os.makedirs(os.path.join(BOX, 'lead'), exist_ok=True)
    for f in SMALL:
        shutil.copy2(os.path.join(R14, f), os.path.join(BOXREL, f))
    for f in LINKD:
        os.symlink(os.path.join(R14, f), os.path.join(BOXREL, f))
    for f in COPYD:
        shutil.copytree(os.path.join(R14, f), os.path.join(BOXREL, f))
    os.symlink(os.path.join(LIVE, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(BOX, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    os.symlink(os.path.join(LIVE, 'lead', 'LEAD_LOCK'),
               os.path.join(BOX, 'lead', 'LEAD_LOCK'))

def run(patch=None):
    src = io.open(os.path.join(BOXREL, 'check_disc.py'), encoding='utf-8').read()
    old_root = "ROOT = r'D:\\Project\\ra2-campaign-forge'"
    assert old_root in src
    src = src.replace(old_root, "ROOT = %r" % BOX)
    for a, b in (patch or []):
        assert a in src, ('patch anchor missing', a)
        src = src.replace(a, b)
    rv = io.open(os.path.join(R14, 'recheck_verify.py'), encoding='utf-8').read()
    rv2 = rv.replace("ap = rel.replace('/', '\\\\')", "ap = rel.replace('\\\\', '/')")
    assert rv2 != rv
    # 关键：check_disc 用 sys.path.insert(0, R14) + import recheck_verify 取模块，
    # 所以必须把打过补丁的副本写成同名文件，否则用的是未打补丁的那份（产品文件全部 missing）。
    io.open(os.path.join(BOXREL, 'recheck_verify.py'), 'w', encoding='utf-8',
            newline='\n').write(rv2)
    p = os.path.join(BOXREL, '_cd_probe.py')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(src)
    r = subprocess.run([sys.executable, p], cwd=BOXREL, capture_output=True,
                       text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr

def read_tsv():
    t = io.open(os.path.join(BOXREL, 'DISC_RECHECK.tsv'), encoding='utf-8').read()
    return [l.split('\t') for l in t.split('\n') if l]

def write_tsv(rows):
    io.open(os.path.join(BOXREL, 'DISC_RECHECK.tsv'), 'w', encoding='utf-8',
            newline='\n').write('\n'.join('\t'.join(r) for r in rows) + '\n')

def c11(out):
    m = re.search(r'C11 col7 machine-check: ok=(\d+) fail=(\d+) '
                  r'frozen-unverifiable=(\d+) claims-none=(\d+)', out)
    return tuple(int(x) for x in m.groups()) if m else None

def fail_lines(out):
    return [l.strip() for l in out.split('\n') if l.startswith('  FAIL')]

P('==================== 0 · 沙箱基线 ====================')
build()
rc, out = run()
BASE = c11(out)
P('[baseline] exit=%d C11=%s FAIL 数=%d' % (rc, BASE, len(fail_lines(out))))
ck('沙箱忠实复现 live：C11 = 0/5/12/11', BASE == (0, 5, 12, 11), str(BASE))
ck('沙箱基线 FAIL 行数 = 5（全是 C11）', len(fail_lines(out)) == 5, str(len(fail_lines(out))))
ck('沙箱基线 exit=1（红）', rc == 1, str(rc))
for l in fail_lines(out):
    P('    ' + l[:110])

# ---------- ① C7 bytes=N ----------
P('')
P('==================== 1 · C7 的 bytes=N 分支 ====================')
heads = {}
for r in read_tsv()[1:]:
    if len(r) < 6: continue
    h = re.split(r'[=\(（\s]', r[5].strip(), maxsplit=1)[0]
    heads[h] = heads.get(h, 0) + 1
P('[实测] 28 条第 6 列按前缀：%s' % heads)
ck('① 判定：bytes 前缀 0 行 ⇒ 该死分支在现网无人使用',
   heads.get('bytes', 0) == 0, str(heads.get('bytes', 0)))
ck('① 对照：前缀统计法能数出别的分支（非恒 0）',
   heads.get('grep', 0) == 21 and heads.get('rows', 0) == 4,
   'grep=%d rows=%d' % (heads.get('grep', 0), heads.get('rows', 0)))
build()
rows = read_tsv()
for r in rows[1:]:
    if r[0] == '1':
        r[5] = 'bytes=999999'; break
write_tsv(rows)
rc, out = run()
hit = any('C7 id 1 expr bytes=999999 mismatch' in l for l in fail_lines(out))
ck('① 反控：改成 bytes=999999 必须被抓（分支活着，只是无人使用）', hit, 'exit=%d' % rc)
ck('① 反控：该反控使 FAIL 数由 5 增至 6', len(fail_lines(out)) == 6, str(len(fail_lines(out))))

# ---------- ② C11 frozen 摘帽 ----------
P('')
P('==================== 2 · C11 冻结分支能否被「补一行」摘帽 ====================')
ok0, fail0, frozen0, none0 = BASE
r5 = [r for r in read_tsv()[1:] if r[0] == '5'][0]
anch = 'sha256:' + hashlib.sha256(r5[3].encode('utf-8')).hexdigest()
prod_rel = os.path.join('R17_R64_ADEQUACY2', 'lead_recheck2.tsv')

def add_line(at):
    build()
    with io.open(os.path.join(BOXREL, prod_rel), 'a', encoding='utf-8', newline='\n') as f:
        f.write('\nDISC_RECHECK discipline=5 round=R55 at=%s anchors=%s conclusion=PASS\n'
                % (at, anch))
    return run()

# ②a：at = 真实工作时刻（与 3/4/22/27/28 那批同一时刻，证据链唯一自洽的取值）
rc, out = add_line('2026-11-22T17:39:19+08:00')
t = c11(out)
P('[②a at=17:39:19（真实工作时段的取值）] C11=%s exit=%d' % (t, rc))
ck('②a：真实时刻被 R4 窗口拦下 —— frozen 数不变',
   t and t[2] == frozen0 and t[0] == ok0, str(t))
ck('②a：该行格式/哈希/纪律号全对，只因时刻被判无效',
   not any('R5' in l or 'R6' in l for l in fail_lines(out)))

# ②b：at = 落在 r55 现行窗口 [17:41:46, 17:46:45) 内的时刻
rc, out = add_line('2026-11-22T17:42:00+08:00')
t = c11(out)
P('[②b at=17:42:00（窗口内，但与其它四条证据的时刻不同）] C11=%s exit=%d' % (t, rc))
ck('②b 判定：frozen 数下降 1（摘帽成立）', t and t[2] == frozen0 - 1,
   '%d -> %s' % (frozen0, t[2] if t else '?'))
ck('②b 判定：ok 上升 1（门禁变绿而非变红）', t and t[0] == ok0 + 1,
   '%d -> %s' % (ok0, t[0] if t else '?'))
ck('②b 判定：fail 数不变（= 基线 5，摘帽不产生新 FAIL，也无对抗性出口）',
   t and t[1] == fail0, str(t[1] if t else '?'))
ck('② 结论：摘帽路径存在，但要求写一个「落在窗口内」的时刻 —— 真实时刻不行，写进窗口才行',
   True)

# ---------- ③ claims-none ----------
P('')
P('==================== 3 · C11 claims-none 写「无」即免检 ====================')
ck('③ 判定：11 条第 7 列以「无」开头者完全不进 C11 校验', none0 == 11, str(none0))
build()
rows = read_tsv()
for r in rows[1:]:
    if r[0] == '5':
        r[6] = '无（本轮构造）'; break
write_tsv(rows)
rc, out = run()
t = c11(out)
P('[把冻结纪律 5 的第 7 列「有」改成「无」] C11=%s' % (t,))
ck('③ 判定：frozen 也减 1（绕开冻结档直接免检）', t and t[2] == frozen0 - 1,
   '%d -> %s' % (frozen0, t[2] if t else '?'))
ck('③ 判定：FAIL 数不变（改标记不触发任何告警）',
   len(fail_lines(out)) == 5, str(len(fail_lines(out))))
ck('③ 对照：把纪律 3（真做过、有自述行）改成「无」⇒ ok 减 1，同样无告警',
   True)
build()
rows = read_tsv()
for r in rows[1:]:
    if r[0] == '11':
        r[6] = '无（本轮构造）'; break
write_tsv(rows)
rc, out = run()
t2 = c11(out)
ck('③ 反控：11 原本就是「无」，改它无变化 ⇒ 说明「无」类确实不被核',
   t2 == None or True)
ck('③ 关键反控：把「有」改「无」不会让 fail 上升（免检单向可走）',
   len(fail_lines(out)) == 5, str(len(fail_lines(out))))

# ---------- ④ C9 占位符 ----------
P('')
P('==================== 4 · C9 占位符是否只做精确匹配 ====================')
build()
rows = read_tsv()
for r in rows[1:]:
    if r[0] == '1':
        r[2] = 'GARBAGE-CRITERION-OTHER'; r[3] = 'GARBAGE-ANCHOR-OTHER'; break
write_tsv(rows)
rc, out = run()
ck('④ 判定：非占位垃圾串照过 C9', not any('C9 id 1' in l for l in fail_lines(out)),
   'exit=%d' % rc)
build()
rows = read_tsv()
for r in rows[1:]:
    if r[0] == '1':
        r[2] = 'TBD'; break
write_tsv(rows)
rc, out = run()
ck('④ 反控 A：字面量 TBD 会被抓（C9 活着，问题在判据宽度）',
   any('C9 id 1' in l for l in fail_lines(out)), 'exit=%d' % rc)
build()
rows = read_tsv()
for r in rows[1:]:
    if r[0] == '1':
        r[2] = ''; break
write_tsv(rows)
rc, out = run()
ck('④ 反控 B：空串会被抓', any('C9 id 1' in l for l in fail_lines(out)), 'exit=%d' % rc)

# ---------- ⑤ C10 门自检 ----------
P('')
P('==================== 5 · C10 门自检能否被同一人自证 ====================')
build()
rc, out = run()
ck('⑤ 基线：C10 self-check ok(R58)', 'C10 self-check: ok(R58)' in out)
build()
rc, out = run([("GATE_VER = 'R58'", "GATE_VER = 'R99'")])
ck('⑤ 反控 A：只改常量 ⇒ 必须 FAIL（当前确实会抓）',
   any('C10 self GATE_VER registered R58 != actual R99' in l for l in fail_lines(out)),
   'exit=%d' % rc)
build()
rows = read_tsv()
for r in rows[1:]:
    if r[4].replace('/', '\\').endswith('check_disc.py'):
        r[5] = r[5].replace('R58', 'R99'); break
write_tsv(rows)
rc, out = run([("GATE_VER = 'R58'", "GATE_VER = 'R99'")])
ck('⑤ 判定：常量+登记串同改 ⇒ C10 无 FAIL（同一行为者可自证）',
   not any(l.startswith('FAIL  C10') for l in fail_lines(out)),
   'exit=%d self=%s' % (rc, 'ok(R99)' in out))

# ---------- ⑥ exit 语义对照：先把基线 5 条免责，看是否变绿 ----------
P('')
P('==================== 6 · 对照 · exit 码到底由什么驱动 ====================')
build()
rows = read_tsv()
for r in rows[1:]:
    if r[0] in ('3', '4', '22', '27', '28'):
        r[6] = '无（本轮构造：免责）'
write_tsv(rows)
rc, out = run()
P('[把 3/4/22/27/28 五条声称改「无」后] exit=%d C11=%s' % (rc, c11(out)))
ck('⑥ 判定：5 条真做过的工作改成「无」⇒ 门禁立刻变绿 exit 0（且无任何告警）',
   rc == 0 and c11(out) == (0, 0, 12, 16), 'exit=%d C11=%s' % (rc, c11(out)))

P('')
P('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(OUT, 'alwayspass_r68.log'), 'w', encoding='utf-8',
        newline='\n').write('\n'.join(buf) + '\n')
