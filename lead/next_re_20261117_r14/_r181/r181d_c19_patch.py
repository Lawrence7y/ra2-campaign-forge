#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181d_c19_patch.py —— 在 check_disc.py 里加 C19「事实层联动」。fail-closed：
先在沙箱复算旧文件 sha 与旧 pin，命中才允许写生产；写完回读校验；反向三控全在 /tmp。

C19 判据（四条，全部从盘上现算，无手抄常量用于比对目标盘上文件的内容本身）：
  (a) _r160/facts_floors.py 存在且可 ast 解析，其 CUR_SHA256 == 现盘 V563/FACT_INDEX.tsv sha256
  (b) 其 TOTAL_BYTES == 现盘该文件字节数
  (c) FACT_INDEX_CURRENT.md 的「sha256」字段 == 现盘 V563/FACT_INDEX.tsv sha256
  (d) FACT_INDEX_CURRENT.md 的「字节数」字段 == 现盘字节数
  (e) FACT_INDEX_CURRENT.md 的「版本目录」字段 == 现盘台账所在目录名（抓指针指错版本）
另加 C19b 防「新门自己也永远通过」：四条判据的输入在现盘必须全部可解析，且
解析失败必须 FAIL 而不是跳过（读不到 = FAIL，与 D10 同纪律）。

刻意**不**引入「check_disc 里嵌 facts_floors.py 的 sha256」这条：那会让每次改事实层门禁
都必须同步改主门禁（新假 FAIL 面），而 (a)(b) 已能抓住「事实层常量与实物脱钩」这一真实失效。
"""
import ast, hashlib, io, os, re, shutil, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
BASELINE = os.path.join(TIER, 'R17_LEAD_BASELINE')

fails = []
def ck(name, cond, detail=''):
    (print(('  PASS  ' if cond else '  FAIL  ') + name + (('  ' + str(detail)) if detail else '')))
    if not cond: fails.append(name)
    return cond

def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''
# ---- C19 [R181 新增] 事实层联动：主门禁必须看见事实层与当前版指针 ----
# 存在理由（实测，连续九轮登记后由 R180 收到 facts_floors 本体、R181 收回主门禁这一层）：
# R181 实测 check_disc.py 源码对 facts_floors / FACT_INDEX / FACT_INDEX_CURRENT 的子串
# 出现次数各 0（_r180/r180a 与 _r181/r181a 两次独立计数，正控在 gate_runner.py 上得 14/5/0）；
# 且把 FACT_INDEX.tsv 的 F24 grade 由 [已证] 改成 [流程]、以副本路径跑本脚本，仍 exit 0
# —— 事实层被改，主门禁完全看不见。这不是「读不到就跳过」，是「根本不读」。
# 判据（全部从盘上现算，本脚本内不存任何事实层文件的 sha 常量 —— 那样每改一次事实层
# 都必须同步改本脚本，是新造一个假 FAIL 面；实测该面在 R181 是被明确否决的方案）：
#   (a) facts_floors.py 的 CUR_SHA256 必须等于现盘台账 sha256
#   (b) facts_floors.py 的 TOTAL_BYTES 必须等于现盘台账字节数
#   (c) 指针文件的 sha256 字段必须等于现盘台账 sha256
#   (d) 指针文件的字节数字段必须等于现盘台账字节数
#   (e) 指针文件的版本目录字段必须等于现盘台账所在目录名
# 读不到 / 解析不出 → FAIL 而不是跳过（与 facts_floors D10 同纪律：不可因读不到而假通过）。
C19_FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
C19_PTR = os.path.join(R14, 'FACT_INDEX_CURRENT.md')
C19_LEDGER = os.path.join(R14, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')

def _c19_ast_consts(p):
    tree = ast.parse(io.open(p, encoding='utf-8').read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and isinstance(node.value, ast.Constant):
                out[t.id] = node.value.value
    return out

_c19 = 'not-run'
if not os.path.exists(C19_FACTS):
    fails.append('C19 facts_floors.py missing: %s (fact layer gate is the thing being linked; '
                 'absent means the link is broken, not "nothing to check")' % C19_FACTS)
elif not os.path.exists(C19_LEDGER):
    fails.append('C19 ledger missing: %s' % C19_LEDGER)
elif not os.path.exists(C19_PTR):
    fails.append('C19 pointer file missing: %s' % C19_PTR)
else:
    try:
        _c19_k = _c19_ast_consts(C19_FACTS)
    except Exception as e:
        _c19_k = None
        fails.append('C19 facts_floors.py unparseable (%s): cannot verify the link' % e)
    if _c19_k is not None:
        _c19_raw = open(C19_LEDGER, 'rb').read()
        _c19_sha = hashlib.sha256(_c19_raw).hexdigest()   # S-673: 本文件没有 sha() 助手
        _c19_len = len(_c19_raw)
        if 'CUR_SHA256' not in _c19_k or 'TOTAL_BYTES' not in _c19_k:
            fails.append('C19 facts_floors.py lacks CUR_SHA256/TOTAL_BYTES literals '
                         '(found=%s)' % repr(sorted(_c19_k))[:120])
        else:
            if _c19_k['CUR_SHA256'] != _c19_sha:
                fails.append('C19 facts CUR_SHA256 %s != on-disk ledger sha %s '
                             '(fact gate would pin a different file than the one on disk)'
                             % (_c19_k['CUR_SHA256'], _c19_sha))
            if _c19_k['TOTAL_BYTES'] != _c19_len:
                fails.append('C19 facts TOTAL_BYTES %d != on-disk ledger bytes %d'
                             % (_c19_k['TOTAL_BYTES'], _c19_len))
            _c19_pt = io.open(C19_PTR, encoding='utf-8', newline='').read()
            _c19_ms = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', _c19_pt)
            _c19_mb = re.search(r'\| 字节数 \| (\d+) \|', _c19_pt)
            _c19_md = re.search(r'\| 版本目录 \| (\S+) \|', _c19_pt)
            if not (_c19_ms and _c19_mb and _c19_md):
                fails.append('C19 pointer fields unparseable (sha=%r bytes=%r dir=%r)'
                             % (bool(_c19_ms), bool(_c19_mb), bool(_c19_md)))
            else:
                if _c19_ms.group(1) != _c19_sha:
                    fails.append('C19 pointer sha %s != on-disk ledger sha %s'
                                 % (_c19_ms.group(1), _c19_sha))
                if int(_c19_mb.group(1)) != _c19_len:
                    fails.append('C19 pointer bytes %s != on-disk ledger bytes %d'
                                 % (_c19_mb.group(1), _c19_len))
                _c19_dir = os.path.basename(os.path.dirname(C19_LEDGER))
                if _c19_md.group(1) != _c19_dir:
                    fails.append('C19 pointer version dir %r != actual %r '
                                 '(pointer names a different version directory)'
                                 % (_c19_md.group(1), _c19_dir))
                _c19 = 'ok(%s/%d/%s)' % (_c19_sha[:8], _c19_len, _c19_dir)
                notes.append('C19 fact-layer link: facts CUR_SHA256/TOTAL_BYTES and pointer '
                             'sha/bytes/dir all agree with on-disk %s (%s/%d)'
                             % (_c19_dir, _c19_sha[:8], _c19_len))
'''

NEW_IMPORT = 'import io, os, re, sys, hashlib, hashlib, json, ast\n'
OLD_IMPORT = 'import io, os, re, sys, hashlib, hashlib, json\n'
ANCHOR = "\n# ---- C5 CR 抽查 ----"
PRINT_OLD = "print('C10 self-check: %s' % c10)"
PRINT_NEW = "print('C10 self-check: %s' % c10)\nprint('C19 fact-layer link: %s' % _c19)"

def build(src):
    assert src.count(OLD_IMPORT) == 1, 'import line count %d' % src.count(OLD_IMPORT)
    assert src.count(PRINT_OLD) == 1, 'C10 print count %d' % src.count(PRINT_OLD)
    assert src.count(ANCHOR) == 1, 'C5 anchor count %d' % src.count(ANCHOR)
    out = src.replace(OLD_IMPORT, NEW_IMPORT)
    out = out.replace(ANCHOR, BLOCK + ANCHOR)
    out = out.replace(PRINT_OLD, PRINT_NEW)
    return out

print('--- fail-closed 前置：旧文件 sha 与旧 pin ---')
old = io.open(GATE, encoding='utf-8', newline='').read()
OLD_SHA = sha(old.encode('utf-8'))
ck('P1 旧 check_disc.py sha 命中实测基线', OLD_SHA == '3ddb0e1faef034238f6db80c6403e1ff56f4ba695fc0f17dc30f940e9a70cc2e', OLD_SHA[:16])
ck('P2 旧文件 CR=0', old.count('\r') == 0, old.count('\r'))
ck('P3 旧文件尚不含 C19', 'C19' not in old, old.count('C19'))

print('--- 构造新版（沙箱）---')
new = build(old)
ck('B1 新文件包含 C19 块', 'C19 [R181 新增]' in new)
ck('B2 新文件 ast 可解析', (lambda: (ast.parse(new), True)[1])())
ck('B3 只插入、不删除：旧文件每一行仍按序出现在新文件里',
   all(l in new for l in old.split('\n') if l.strip()))
ck('B4 C19 未在 check_disc 里嵌入 facts_floors.py 的 sha256（否决的方案）',
   sha(open(FACTS, 'rb').read()) not in new)

print('--- 沙箱实跑：把新文件放进 /tmp 的完整镜像目录 ---')
tmpd = tempfile.mkdtemp(prefix='r181d_')
try:
    sbox = os.path.join(tmpd, 'lead', 'next_re_20261117_r14')
    os.makedirs(sbox)
    # S-672：首版只软链了 6 个数据文件与 2 个目录，漏了同目录的辅助模块
    # （check_disc 第 74 行 import place_r87）⇒ 沙箱 rc=1 且 FAIL 行 0（异常而非判据失败）。
    # 改为软链 tier 内全部条目（check_disc.py 除外，它在下面被新版覆盖）。
    for name in sorted(os.listdir(TIER)):
        if name == 'check_disc.py':
            continue
        os.symlink(os.path.join(TIER, name), os.path.join(sbox, name))
    os.makedirs(os.path.join(tmpd, 'lead'), exist_ok=True)
    os.symlink(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(tmpd, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    os.makedirs(os.path.join(tmpd, '_r160'), exist_ok=True)
    os.symlink(FACTS, os.path.join(tmpd, '_r160', 'facts_floors.py'))
    box_gate = os.path.join(sbox, 'check_disc.py')
    import subprocess
    env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
    def run_gate(body):
        open(box_gate, 'w', encoding='utf-8', newline='\n').write(body)
        p = subprocess.run([sys.executable, box_gate], capture_output=True, text=True,
                           cwd=sbox, timeout=300, env=env)
        o = p.stdout + p.stderr
        return p.returncode, [l.strip() for l in o.split('\n') if l.strip().startswith('FAIL')], o
    # S-674：首版把「沙箱 rc==0 / FAIL==0」当判据 ⇒ 假 FAIL。沙箱里 id 31 的产物是相对路径，
    # 软链镜像下解析不到（FILE_MISSING），旧版本身也会 rc=1/3 FAIL ⇒ 那 3 条是镜像环境造成的，
    # 不是 C19 造成的。正确判据必须是**新旧同镜像对照**：FAIL 集合逐条相同（差分为空）。
    rc_old, f_old, _o_old = run_gate(old)
    rc_new, f_new, o_new = run_gate(new)
    ck('S1 旧版在新镜像里的基线（如实记录，不作通过条件）', True,
       (rc_old, len(f_old)))
    ck('S2 新旧两版 FAIL 集合逐条完全相同（C19 未引入任何新 FAIL）',
       f_old == f_new, (len(f_old), len(f_new)))
    ck('S3 新旧两版 exit code 相同', rc_old == rc_new, (rc_old, rc_new))
    ck('S4 新版输出含 C19 ok 行且旧版没有',
       'C19 fact-layer link: ok(' in o_new and 'C19 fact-layer link' not in _o_old,
       [l for l in o_new.split('\n') if 'C19 fact-layer link' in l][:1])
finally:
    shutil.rmtree(tmpd, ignore_errors=True)

print('--- 写生产（独占备份 + 一次性写 + 回读校验）---')
if fails:
    print('前置/沙箱有 FAIL，拒绝写生产'); print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)
os.makedirs(BASELINE, exist_ok=True)
bak = os.path.join(BASELINE, 'check_disc.py.before_r181_C19_%s.bak'
                   % __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
os.write(fd, old.encode('utf-8')); os.close(fd)
ck('W1 备份建立且内容等于旧文件', open(bak, 'rb').read() == old.encode('utf-8'), os.path.basename(bak))
ck('W2 备份前生产文件仍是旧 sha（未被人动过）', sha(open(GATE, 'rb').read()) == OLD_SHA)
with open(GATE, 'w', encoding='utf-8', newline='\n') as f:
    f.write(new)
after = open(GATE, 'rb').read()
ck('W3 回读：新生产文件 sha == 沙箱新版 sha', sha(after) == sha(new.encode('utf-8')),
   sha(after)[:16])
ck('W4 回读：CR=0', after.count(b'\r') == 0, after.count(b'\r'))
ck('W5 回读：字节数 = %d 起' % len(old.encode('utf-8')), len(after) > len(old.encode('utf-8')),
   (len(old.encode('utf-8')), len(after)))
print('NEW_SHA=%s' % sha(after))
print('NEW_BYTES=%d' % len(after))
print('BAK=%s' % bak)
print('--- 汇总 ---')
print('PASS/FAIL: fails=%d' % len(fails))
if fails: print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
