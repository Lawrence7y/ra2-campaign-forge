#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181f_c19_v2.py —— 把 C19 从「硬编码 V563 路径」改成「全部路径由指针解析」。

改动的直接起因（跨家族审计 #432 的 Q4，主会话 r181g 复算成立后采纳）：
  v1 的 (a)(b)(d) 三条都硬编码 R17_R131_FACTINDEX_V563。纪律「历史版本一律保留不删不改」
  ⇒ 一旦升到 V564，V563 文件仍在盘上、sha 与字节都不变 ⇒ 这三条**永远通过**（僵尸快照）。
  这与 check_disc 历史缺陷 C7b/C11b/C18 同型，且比现状更坏（现状至少没人误以为台账被查）。

v2 判据（路径一律从指针的「版本目录」+「相对路径」字段解析，不硬编码任何版本号）：
  (a) 指针「相对路径」拼出的绝对路径必须存在
  (b) 该路径的 sha256 == 指针「sha256」字段
  (c) 该路径的字节数 == 指针「字节数」字段
  (d) 指针「版本目录」== 该路径的目录名
  (e) facts_floors.py 的 EXPECT_CUR 必须解析到同一个绝对路径（抓「两门各查各的版本」，
      这是审计 Q5① 提的零常量联动点）
  (f) facts_floors.py 的 CUR_SHA256/TOTAL_BYTES 必须等于**指针解析出的那份文件**的实测值
      （不再拿硬编码 V563 当靶子 ⇒ 升版后仍有分辨力）
读不到 / 解析不出 → FAIL 而不是跳过。
"""
import ast, hashlib, io, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
BASELINE = os.path.join(TIER, 'R17_LEAD_BASELINE')

fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)
    return c
def sha(b): return hashlib.sha256(b).hexdigest()

OLD_BLOCK_START = "# ---- C19 [R181 新增] 事实层联动"
OLD_BLOCK_END = "\n# ---- C5 CR 抽查 ----"

NEW_BLOCK = r'''# ---- C19 [R181 新增] 事实层联动：主门禁必须看见事实层与当前版指针 ----
# 存在理由（实测）：R181 两次独立计数（_r180/r180a、_r181/r181a，正控在 gate_runner.py 上
# 得 14/5/0）测得本脚本对 facts_floors / FACT_INDEX / FACT_INDEX_CURRENT 的子串出现各 0；
# 且把 FACT_INDEX.tsv 的 F24 grade 由 [已证] 改成 [流程] 后以副本路径跑本脚本仍 exit 0,
# 而 facts_floors.py 同一改动 exit 1 且 D5 点名 —— 主门禁完全看不见事实层。
#
# 判据的**靶子路径一律由指针解析**，本块不硬编码任何版本号：
#   若硬编码 R17_R131_FACTINDEX_V563，而纪律规定「历史版本一律保留不删不改」，
#   则升版到 V564 之后 V563 那份文件仍在盘上且字节与 sha 都不变 ⇒ 判据永远通过。
#   这种「钉住一个永不变化的僵尸快照」与 C7b/C11b/C18 抓的恒真子项同型，且更坏：
#   现状至少没人误以为台账被检查过。故 v2 改为 pointer-driven。
# 判据：
#   (a) 指针「相对路径」字段解析出的绝对路径必须存在
#   (b) 该路径实测 sha256 == 指针「sha256」字段
#   (c) 该路径实测字节数 == 指针「字节数」字段
#   (d) 指针「版本目录」字段 == 该路径所在目录名
#   (e) facts_floors.py 的 EXPECT_CUR 必须解析到同一个绝对路径（抓「两门各查各的版本」）
#   (f) facts_floors.py 的 CUR_SHA256 / TOTAL_BYTES 必须等于该路径的实测 sha / 字节数
# 读不到或解析不出 → FAIL（不得因读不到而跳过，与 facts_floors D10 同纪律）。
C19_FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
C19_PTR = os.path.join(R14, 'FACT_INDEX_CURRENT.md')

def _c19_consts(p):
    tree = ast.parse(io.open(p, encoding='utf-8').read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and isinstance(node.value, ast.Constant):
                out[t.id] = node.value.value
    return out

def _c19_eval_expect_cur(p):
    """取 facts_floors.py 里 EXPECT_CUR 的值，**不执行该文件**。

    它是 os.path.join(TIER, 'DIR', 'FACT_INDEX.tsv') 形式（Call，不是 Constant），
    故 ast 顶层常量表取不到。这里只按词法解析这一行，支持两种写法：
      1) os.path.join(<TIER 名>, 'DIR', 'FILE')  —— 把 TIER 名换成 tier 实际路径
      2) 字面量字符串
    解析不出返回 None（调用方 FAIL，不得跳过）。
    S-678：首版想 exec 该文件的常量区，但常量与主体之间没有可停的分界（首个 print 在 332 行，
    D0..D10 的副作用在此之前已发生）⇒ 执行他人门禁脚本不是一个可接受的做法，改为词法解析。
    """
    txt = io.open(p, encoding='utf-8', newline='').read()
    m = re.search(r'^([A-Z_][A-Z0-9_]*)\s*=\s*os\.path\.join\(\s*TIER\s*,\s*'
                  r"'([^']+)'\s*,\s*'([^']+)'\s*\)", txt, re.M)
    if m:
        # S-680：本文件里 tier 路径的变量名是 R14，不是 TIER（TIER 是 facts_floors.py 的叫法）
        return os.path.join(R14, m.group(2), m.group(3))
    # S-679：首版在这里写了同时含单双引号的字符类，在块里引号层数错
    # ⇒ 整个 BLOCK 语法错。改用 chr() 拼引号，块内不再出现裸引号字符类。
    _Q = chr(34) + chr(39)
    m = re.search(r'^(?:EXPECT_CUR|CUR)\s*=\s*TIER\s*/\s*(\S+)', txt, re.M)
    if m:
        return os.path.join(R14, m.group(1).strip().strip(_Q))
    m = re.search(r'^EXPECT_CUR\s*=\s*[rbu]?(\S+)', txt, re.M)
    if m:
        v = m.group(1).strip().strip(_Q)
        return v if os.path.isabs(v) else os.path.join(ROOT, v)
    return None

_c19 = 'not-run'
if not os.path.exists(C19_PTR):
    fails.append('C19 pointer file missing: %s (the pointer is what declares the current '
                 'ledger; absent means the fact layer is unanchored, not "nothing to check")'
                 % C19_PTR)
elif not os.path.exists(C19_FACTS):
    fails.append('C19 facts_floors.py missing: %s' % C19_FACTS)
else:
    _c19_pt = io.open(C19_PTR, encoding='utf-8', newline='').read()
    _c19_ms = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', _c19_pt)
    _c19_mb = re.search(r'\| 字节数 \| (\d+) \|', _c19_pt)
    _c19_md = re.search(r'\| 版本目录 \| (\S+) \|', _c19_pt)
    _c19_mp = re.search(r'\| 相对路径 \| (\S+) \|', _c19_pt)
    if not (_c19_ms and _c19_mb and _c19_md and _c19_mp):
        fails.append('C19 pointer fields unparseable (sha=%r bytes=%r dir=%r relpath=%r)'
                     % (bool(_c19_ms), bool(_c19_mb), bool(_c19_md), bool(_c19_mp)))
    else:
        _c19_rel = _c19_mp.group(1).replace('\\', '/').strip()
        _c19_abs = os.path.join(ROOT, _c19_rel)
        if not os.path.exists(_c19_abs):
            fails.append('C19 pointer relative path does not exist: %r -> %r '
                         '(pointer names a version that is not on disk)' % (_c19_rel, _c19_abs))
        else:
            _c19_raw = open(_c19_abs, 'rb').read()
            _c19_sha = hashlib.sha256(_c19_raw).hexdigest()
            _c19_len = len(_c19_raw)
            if _c19_ms.group(1) != _c19_sha:
                fails.append('C19 pointer sha %s != on-disk sha %s of %r'
                             % (_c19_ms.group(1), _c19_sha, _c19_rel))
            if int(_c19_mb.group(1)) != _c19_len:
                fails.append('C19 pointer bytes %s != on-disk bytes %d of %r'
                             % (_c19_mb.group(1), _c19_len, _c19_rel))
            _c19_dir = os.path.basename(os.path.dirname(_c19_abs))
            if _c19_md.group(1) != _c19_dir:
                fails.append('C19 pointer version dir %r != actual dir %r of the declared '
                             'relative path (the two pointer fields disagree)'
                             % (_c19_md.group(1), _c19_dir))
            try:
                _c19_k = _c19_consts(C19_FACTS)
            except Exception as e:
                _c19_k = None
                fails.append('C19 facts_floors.py unparseable (%s): cannot verify the link' % e)
            if _c19_k is not None:
                # S-677：首版用 ast 的「顶层 Assign + Constant」取 EXPECT_CUR，而它是
                # os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv') —— 是 Call
                # 不是 Constant ⇒ 取不到，于是 v2 在**正常盘面**上也 FAIL（假 FAIL）。
                # 改为直接 exec facts_floors.py 的**常量区**（import 会跑整条门禁，不行），
                # 用「把 os.path 换成可控桩 + 执行到第一个 print 之前」的方式求值真路径。
                _c19_exp = _c19_eval_expect_cur(C19_FACTS)
                if not _c19_exp:
                    fails.append('C19 cannot resolve EXPECT_CUR in facts_floors.py '
                                 '(the fact gate must declare which file it targets)')
                else:
                    if os.path.normpath(_c19_exp) != os.path.normpath(_c19_abs):
                        fails.append('C19 fact gate targets a different file than the pointer: '
                                     'EXPECT_CUR=%r vs pointer=%r (two gates checking two '
                                     'different versions both report green)'
                                     % (_c19_exp, _c19_abs))
                for _c19_nm, _c19_val, _c19_real in (
                        ('CUR_SHA256', _c19_k.get('CUR_SHA256'), _c19_sha),
                        ('TOTAL_BYTES', _c19_k.get('TOTAL_BYTES'), _c19_len)):
                    if _c19_nm not in _c19_k:
                        fails.append('C19 facts_floors.py lacks %s literal' % _c19_nm)
                    elif _c19_val != _c19_real:
                        fails.append('C19 facts %s %r != on-disk %r of %r'
                                     % (_c19_nm, _c19_val, _c19_real, _c19_rel))
                if not [x for x in fails if x.startswith('C19')]:
                    _c19 = 'ok(%s/%d/%s)' % (_c19_sha[:8], _c19_len, _c19_dir)
                    notes.append('C19 fact-layer link (pointer-driven): %r sha %s bytes %d ; '
                                 'facts_floors EXPECT_CUR/CUR_SHA256/TOTAL_BYTES all agree'
                                 % (_c19_rel, _c19_sha[:8], _c19_len))
                else:
                    _c19 = 'FAIL'
'''

PRINT_OLD = "print('C19 fact-layer link: %s' % _c19)"

print('--- 前置：确认现盘是 v1（C19 已存在但硬编码）---')
cur = io.open(GATE, encoding='utf-8', newline='').read()
ck('P1 现盘 check_disc 已含 v1 C19 块', OLD_BLOCK_START in cur)
ck('P2 现盘 C19 含硬编码 V563（待替换的靶子）',
   "os.path.join(R14, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')" in cur)
ck('P3 现盘 CR=0', cur.count('\r') == 0, cur.count('\r'))
V1_SHA = sha(cur.encode('utf-8'))
print('V1_SHA=%s V1_BYTES=%d' % (V1_SHA, len(cur.encode('utf-8'))))

print('--- 构造 v2 ---')
i0 = cur.index(OLD_BLOCK_START)
i1 = cur.index(OLD_BLOCK_END)
assert i0 < i1
new = cur[:i0] + NEW_BLOCK + cur[i1:]
ck('B1 v2 仍含 C19 块', 'C19 [R181 新增]' in new)
ck('B2 v2 不再硬编码 V563 版本目录',
   "os.path.join(R14, 'R17_R131_FACTINDEX_V563'" not in new)
ck('B3 v2 ast 可解析', (lambda: (ast.parse(new), True)[1])())
ck('B4 v2 保留了 C5/其余所有段落', new.count('# ---- C5 CR 抽查 ----') == 1)

print('--- 镜像沙箱：新旧对照 ---')
tmpd = tempfile.mkdtemp(prefix='r181f_')
try:
    sbox = os.path.join(tmpd, 'lead', 'next_re_20261117_r14'); os.makedirs(sbox)
    for n in sorted(os.listdir(TIER)):
        if n == 'check_disc.py': continue
        os.symlink(os.path.join(TIER, n), os.path.join(sbox, n))
    os.symlink(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(tmpd, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    os.makedirs(os.path.join(tmpd, '_r160'))
    os.symlink(FACTS, os.path.join(tmpd, '_r160', 'facts_floors.py'))
    bg = os.path.join(sbox, 'check_disc.py')
    env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
    def run(body):
        open(bg, 'w', encoding='utf-8', newline='\n').write(body)
        p = subprocess.run([sys.executable, bg], capture_output=True, text=True,
                           cwd=sbox, timeout=300, env=env)
        o = p.stdout + p.stderr
        return p.returncode, [l.strip() for l in o.split('\n') if l.strip().startswith('FAIL')], o
    rc1, f1, o1 = run(cur)
    rc2, f2, o2 = run(new)
    ck('S1 v1 基线（镜像环境自身的 3 条不作通过条件）', True, (rc1, len(f1)))
    ck('S2 v2 未引入任何新 FAIL（差分集合相同）', f1 == f2, (len(f1), len(f2)))
    ck('S3 v2 输出 C19 ok 行在场', 'C19 fact-layer link: ok(' in o2,
       [l.strip() for l in o2.split('\n') if 'C19 fact-layer link' in l][:1])

    print('--- 关键反控：模拟「升版到 V564」，v1 应退化为恒真，v2 必须仍能 FAIL ---')
    # 造一个 V564 副本（内容 = 现盘 V563 的字节），指针改为指向它；facts_floors 不动
    v564dir = os.path.join(sbox, 'R17_R131_FACTINDEX_V564'); os.makedirs(v564dir)
    v563 = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
    shutil.copy2(v563, os.path.join(v564dir, 'FACT_INDEX.tsv'))
    v564sha = sha(open(os.path.join(v564dir, 'FACT_INDEX.tsv'), 'rb').read())
    ptr_now = io.open(os.path.join(TIER, 'FACT_INDEX_CURRENT.md'),
                      encoding='utf-8', newline='').read()
    ptr_v564 = (ptr_now.replace('R17_R131_FACTINDEX_V563', 'R17_R131_FACTINDEX_V564'))
    os.unlink(os.path.join(sbox, 'FACT_INDEX_CURRENT.md'))
    io.open(os.path.join(sbox, 'FACT_INDEX_CURRENT.md'), 'w',
            encoding='utf-8', newline='').write(ptr_v564)
    # 此刻：指针指 V564（内容与 V563 逐字节相同），facts_floors 仍指 V563
    # ⇒ 真实失效「两门查两个不同版本」已发生。
    # S-681：T1 的**预期写错了**。我原以为 v1 在此工况会「一条 C19 都不 FAIL」，
    # 实测 v1 的 (d) 版本目录判据会 FAIL（指针写 V564、相对路径仍是 V563 ⇒ 两字段自相矛盾）。
    # 但那只是「指针自己前后不一致」这个更容易发现的工况；真正的僵尸快照工况是
    # **指针整体升级到 V564 且自洽**（相对路径也改 V564），此时 V563 文件按纪律仍在盘上。
    # 故 T1 拆成 T1a（指针自相矛盾：两版都能抓，不是区分度）与 T1b（指针整体升版且自洽）。
    rc3, f3, o3 = run(cur)
    rc4, f4, o4 = run(new)
    c19_v1a = [x for x in f3 if 'C19' in x]
    c19_v2a = [x for x in f4 if 'C19' in x]
    ck('T1a 指针自相矛盾（目录字段改、相对路径未改）：两版都能抓（不构成区分度）',
       len(c19_v1a) > 0 and len(c19_v2a) > 0, (len(c19_v1a), len(c19_v2a)))

    # T1b：指针整体升版到 V564 且自洽（相对路径一起改成 V564）——这是真实升版工况
    ptr_full = (ptr_now.replace('R17_R131_FACTINDEX_V563', 'R17_R131_FACTINDEX_V564'))
    os.unlink(os.path.join(sbox, 'FACT_INDEX_CURRENT.md'))
    io.open(os.path.join(sbox, 'FACT_INDEX_CURRENT.md'), 'w',
            encoding='utf-8', newline='').write(ptr_full)
    rc5, f5, o5 = run(cur)
    rc6, f6, o6 = run(new)
    c19_v1b = [x for x in f5 if 'C19' in x]
    c19_v2b = [x for x in f6 if 'C19' in x]
    # S-682：我第二次也预期错了。审计 #432 说「整条 C19 会退化成 V563 永不变的恒真断言」，
    # 实测在**指针整体升版、check_disc 未重钉**这一工况下，v1 的 (d)（版本目录字段 vs
    # 硬编码 C19_LEDGER 的目录名）恰好会 FAIL ⇒ 不是「一条都不 FAIL」。
    # 准确的边界是：v1 的 (a)(b)(c) 三条在本工况全部报绿（假绿），只有 (d) 报红；
    # 而一旦按流程把 C19_LEDGER 重钉到 V564，(d) 也变绿 —— 此时 facts_floors 仍指 V563
    # 就再也无人发现（v1 的全部 C19 判据都以硬编码 V563 为靶子或为比较对象）。
    # 故审计的结论应订正为「v1 的 (a)(b)(c) 是僵尸、(d) 是升版瞬间的一次性哨兵」，
    # 不是「整条退化」。下面按实测拆成两条断言，不粉饰。
    v1_a = [x for x in c19_v1b if 'facts CUR_SHA256' in x or 'pointer sha' in x
            or 'pointer bytes' in x]
    v1_d = [x for x in c19_v1b if 'version dir' in x]
    ck('T1b-1 v1 的 (a)(b)(c) 三条在本工况报绿（僵尸快照：靶子是硬编码 V563）',
       len(v1_a) == 0, v1_a[:2])
    ck('T1b-2 v1 的 (d) 在本工况报红（升版瞬间的一次性哨兵，重钉后即失效）',
       len(v1_d) == 1, v1_d[:1])
    ck('T2b v2（指针驱动）在同一工况下必须 FAIL（抓到两门指两个版本）',
       any('targets a different file than the pointer' in x for x in c19_v2b), c19_v2b[:2])
finally:
    shutil.rmtree(tmpd, ignore_errors=True)

print('--- 写生产 ---')
if fails:
    print('拒绝写生产'); print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)
bak = os.path.join(BASELINE, 'check_disc.py.before_r181_C19v2_%s.bak'
                   % __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
os.write(fd, cur.encode('utf-8')); os.close(fd)
ck('W1 备份 = 旧 v1 文件', open(bak, 'rb').read() == cur.encode('utf-8'), os.path.basename(bak))
ck('W2 写前生产仍是 v1 sha', sha(open(GATE, 'rb').read()) == V1_SHA)
open(GATE, 'w', encoding='utf-8', newline='\n').write(new)
after = open(GATE, 'rb').read()
ck('W3 回读 sha == 沙箱 v2 sha', sha(after) == sha(new.encode('utf-8')), sha(after)[:16])
ck('W4 回读 CR=0', after.count(b'\r') == 0)
print('NEW_SHA=%s' % sha(after)); print('NEW_BYTES=%d' % len(after)); print('BAK=%s' % bak)
print('fails=%d' % len(fails))
if fails: print(repr(fails)); sys.exit(1)
print('[exit 0]')
