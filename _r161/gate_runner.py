#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_runner.py —— R161 新建：把两道门串成一次运行，并对「两门之间的一致性」做独立复算。

存在理由（实测，R160 待办 #1）：事实层守门 `_r160/facts_floors.py` 此前**只能手动跑**，
主门禁 `check_disc.py` 全文不引用它、仓库里也没有任何 gate runner ⇒ 守门形同虚设：
跑完主门禁看到 exit 0，完全不代表台账没被动过。

本 runner 做三件事，全部可机检：
  G1  跑主门禁 check_disc.py，要求 exit 0 且 FAIL 行数为 0。
  G2  跑事实层门禁 facts_floors.py，要求 exit 0 且 FAIL 行数为 0。
  G3  **交叉一致性复算**（不依赖任何手抄常量，全部从盘上现算）：
      a) check_disc.py 的 GATE_VER == DISC_RECHECK 中「纪律号 20」那一行的 col6 登记的版本
         （**纪律号不是文件行号**：该行在 DR 是文件行 21、在 UN 是文件行 11；
          R161 审计员 #376 指出我原稿写成「第 20 行」是错口径，已按实测改正）
      b) 同一版本 == DISC_UNVERIFIABLE 中「纪律号 20」那一行的 col4 登记的版本
      c) check_disc.py 的 FREEZE_SHA256 == 现盘 sha256(DISC_UNVERIFIABLE.tsv)
      d) facts_floors.py 的 CUR_SHA256 == 现盘 sha256(V553/FACT_INDEX.tsv)
      e) facts_floors.py 的 TOTAL_BYTES == 现盘 len(V553/FACT_INDEX.tsv)
      f) check_disc.py 的 C16_FLOORS_SHA256 == 由 C16_FLOORS 表规范化重算的 sha
      g) facts_floors.py 的 MASTER_SHA256 == 由其常量规范化重算的 sha
      a/b/c 三条合起来正是「R159/R160 两轮各踩过一次」的联动坑；d/e 是台账侧的同类坑。

如实声明的边界：
  1) 两道门各自仍受同一上限约束：**同改数据与常量**能过（所有指纹类门禁的共同天花板）。
     本 runner 不消除它，只消除「两门之间悄悄不同步」和「只跑了一门」。
  2) 本 runner 自身也没有门。它的价值是**把两门串成一键**，不是「不可能被绕过」。
  3) --self-test 里的破坏性工况全部在 /tmp 副本上做，绝不改生产文件；子进程一律禁写 .pyc
     （PYTHONDONTWRITEBYTECODE=1），自测末尾实名断言生产 __pycache__ 一个 mtime 都没变。
  4) G3f 的已知失效模式是**假 FAIL**：它按源码文本重建 facts_floors 的常量来做第二实现，
     一旦有人把某个 list 写成多行（语义不变），重算即分叉。S6 把这个方向钉死 ——
     宁可报警，不静默放过。

退出码：0 全通过；1 有 FAIL；2 用法错误。
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
DR = os.path.join(TIER, 'DISC_RECHECK.tsv')
UN = os.path.join(TIER, 'DISC_UNVERIFIABLE.tsv')
LEDGER = os.path.join(TIER, 'R17_R128_FACTINDEX_V556', 'FACT_INDEX.tsv')

fails = []
QUIET = [False]
def ck(name, cond, detail=''):
    ok = bool(cond)
    if not QUIET[0]:
        print(('  PASS  ' if ok else '  FAIL  ') + name + (('  ' + str(detail)) if detail else ''))
    if not ok:
        fails.append(name + ((' [' + str(detail) + ']') if detail else ''))
    return ok

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def rb(p):
    with open(p, 'rb') as f:
        return f.read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def run(cmd, cwd, timeout=400):
    # PYTHONDONTWRITEBYTECODE=1：沙箱里 tier 的 __pycache__ 是指向生产目录的符号链接，
    # 不禁写就会把 .pyc 写回生产树（审计员 #376 第 7 条②实测指出，本脚本已按其结论修正）。
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout, env=env)
    return p.returncode, p.stdout + p.stderr

def find_fails(out):
    return [l.strip() for l in out.split('\n') if l.strip().startswith('FAIL')]

# ---------------------------------------------------------------- G1 / G2

def g1(gate_path, gate_cwd=None):
    rc, out = run([sys.executable, gate_path], gate_cwd or os.path.dirname(gate_path), timeout=600)
    fs = find_fails(out)
    ok = (rc == 0 and not fs)
    print('  [G1] check_disc.py exit=%d FAIL=%d' % (rc, len(fs)))
    for f in fs[:6]:
        print('       ' + f[:150])
    return ok, rc, fs, out

def g2(facts_path, ledger=None):
    cmd = [sys.executable, facts_path] + ([ledger] if ledger else [])
    rc, out = run(cmd, ROOT, timeout=600)
    fs = find_fails(out)
    ok = (rc == 0 and not fs)
    print('  [G2] facts_floors.py exit=%d FAIL=%d' % (rc, len(fs)))
    for f in fs[:6]:
        print('       ' + f[:150])
    return ok, rc, fs, out

# ---------------------------------------------------------------- G3

def rows_of(txt):
    return [l.split('\t') for l in txt.replace('\r\n', '\n').split('\n') if l.strip()]

def c16_recompute(gate_txt):
    m = re.search(r'C16_FLOORS = \{\n(.*?)\n\}', gate_txt, re.S)
    if not m:
        return None, None
    floors = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+),', m.group(1)))
    norm = '\n'.join('%d:%d' % (k, floors[k]) for k in sorted(floors))
    return hashlib.sha256(norm.encode()).hexdigest(), len(floors)

def facts_canon(facts_txt):
    """按 facts_floors.py 里 canon_* 的同一规则重算 D9 主指纹。"""
    def block(name):
        m = re.search(r'^%s = \{\n(.*?)\n\}' % name, facts_txt, re.S | re.M)
        return m.group(1) if m else None
    g = block('GRADES'); f = block('FLOORS'); e = block('EVID')
    eb = block('EVIDB'); l = block('LOST')
    if None in (g, f, e, eb, l):
        return None
    def one(name):
        m = re.search(r'^%s = (\d+)$' % name, facts_txt, re.M)
        return m.group(1) if m else None
    sha543 = one('CUR_SHA256'.replace('CUR_SHA256', 'CUR_SHA256'))  # placeholder, replaced below
    m = re.search(r"^CUR_SHA256 = '([0-9a-f]{64})'", facts_txt, re.M)
    sha543 = m.group(1) if m else None
    tb = one('TOTAL_BYTES'); it = one('ITEMS'); un = one('UNIQ')
    li = one('LOST_ITEMS'); lu = one('LOST_UNIQ')
    if None in (sha543, tb, it, un, li, lu):
        return None

    def canon_g(t):
        return '\n'.join(re.findall(r"(    '[^']*': '[^']*',)", t))
    def canon_f(t):
        return '\n'.join(re.findall(r'(    \'[^\']*\': \(\d+, \d+\),)', t))
    def canon_e(t):
        out = []
        depth_ok = []
        for line in t.split('\n'):
            s = line.strip()
            if not s.startswith("'"):
                continue
            out.append('    ' + s)
        return '\n'.join(out)
    def canon_num(t):
        return '\n'.join(re.findall(r"(    '[^']*': \d+,)", t))

    gs = canon_g(g); fs = canon_f(f); es = canon_e(e); ebs = canon_num(eb); ls = canon_num(l)
    payload = '\n'.join([sha543, str(tb), gs, fs, es, ebs, ls, str(it), str(un), str(li), str(lu)])
    return hashlib.sha256(payload.encode()).hexdigest()

def g3(gate_path, facts_path, dr_path, un_path, ledger_path, quiet=False):
    gt = rd(gate_path); ft = rd(facts_path)
    res = []
    _saved_q = QUIET[0]
    if quiet:
        QUIET[0] = True
    m = re.search(r"^GATE_VER = '([^']+)'", gt, re.M)
    gate_ver = m.group(1) if m else None
    dr_rows = rows_of(rd(dr_path))
    r20 = next((r for r in dr_rows if r and r[0] == '20'), None)
    dr_ver = None
    if r20 and len(r20) >= 6:
        mm = re.search(r"GATE_VER = '([^']+)'", r20[5])
        dr_ver = mm.group(1) if mm else None
    un_rows = rows_of(rd(un_path))
    u20 = next((r for r in un_rows if r and r[0] == '20'), None)
    un_ver = None
    if u20 and len(u20) >= 4:
        mm = re.search(r"GATE_VER = '([^']+)'", u20[3])
        un_ver = mm.group(1) if mm else None
    res.append(ck('G3a GATE_VER 三处一致（脚本常量 / DR 纪律号20 的 col6 / UN 纪律号20 的 col4）',
                  gate_ver and gate_ver == dr_ver == un_ver, (gate_ver, dr_ver, un_ver)))
    mz = re.search(r"^FREEZE_SHA256 = '([0-9a-f]{64})'", gt, re.M)
    actual_un = sha(rb(un_path))
    res.append(ck('G3b FREEZE_SHA256 == 现盘 sha256(DISC_UNVERIFIABLE.tsv)',
                  mz and mz.group(1) == actual_un,
                  ((mz.group(1)[:16] if mz else None), actual_un[:16])))
    msha = re.search(r"^CUR_SHA256 = '([0-9a-f]{64})'", ft, re.M)
    actual_led = sha(rb(ledger_path))
    res.append(ck('G3c facts CUR_SHA256 == 现盘 V553 sha256',
                  msha and msha.group(1) == actual_led,
                  ((msha.group(1)[:16] if msha else None), actual_led[:16])))
    mtb = re.search(r'^TOTAL_BYTES = (\d+)$', ft, re.M)
    actual_len = len(rb(ledger_path))
    res.append(ck('G3d facts TOTAL_BYTES == 现盘 V553 字节数',
                  mtb and int(mtb.group(1)) == actual_len,
                  ((mtb.group(1) if mtb else None), actual_len)))
    new_c16, n16 = c16_recompute(gt)
    pin_c16 = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gt, re.M)
    res.append(ck('G3e C16_FLOORS_SHA256 == 由表重算（%d 节）' % (n16 or 0),
                  pin_c16 and new_c16 and pin_c16.group(1) == new_c16,
                  ((pin_c16.group(1)[:16] if pin_c16 else None), (new_c16 or '')[:16])))
    m_facts = re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'", ft, re.M)
    recomputed = facts_canon(ft)
    res.append(ck('G3f facts MASTER_SHA256 == 由常量规范化重算',
                  m_facts and recomputed and m_facts.group(1) == recomputed,
                  ((m_facts.group(1)[:16] if m_facts else None), (recomputed or '')[:16] if recomputed else 'recompute-failed')))
    QUIET[0] = _saved_q
    return all(res), gate_ver

# ---------------------------------------------------------------- 破坏性自测

def self_test():
    print('\n== S · 破坏性自测（全部在 /tmp 副本上，不碰生产）==')
    print('  反控 S0：当前生产态两道门都必须 exit 0（自测前提）')
    ok1, *_ = g1(GATE)
    ok2, *_ = g2(FACTS)
    ck('S0.1 生产 check_disc exit 0', ok1)
    ck('S0.2 生产 facts_floors exit 0', ok2)

    sbt = tempfile.mkdtemp(prefix='/tmp/r161_runner_')
    pydir = os.path.join(TIER, '__pycache__')
    pyc_before = {}
    if os.path.isdir(pydir):
        for n in sorted(os.listdir(pydir)):
            fp = os.path.join(pydir, n)
            if os.path.isfile(fp):
                pyc_before[n] = os.stat(fp).st_mtime_ns
    try:
        # S1：台账被等长改写（一个汉字换一个汉字，总字节不变）⇒ facts_floors 必须 FAIL
        led2 = sbt + '/FACT_INDEX.mut.tsv'
        shutil.copy2(LEDGER, led2)
        raw = rb(led2).decode('utf-8')
        i = raw.index('的')
        raw2 = raw[:i] + '是' + raw[i + 1:]
        with open(led2, 'wb') as f:
            f.write(raw2.encode('utf-8'))
        ck('S1.0 等长改写后总字节不变', len(raw2.encode()) == len(rb(LEDGER)),
           (len(raw2.encode()), len(rb(LEDGER))))
        ok, rc, fs, _ = g2(FACTS, led2)
        ck('S1.1 等长改写被 facts_floors 抓住（exit=1 且报 D0）', rc == 1 and any('D0' in x for x in fs),
           (rc, [x[:60] for x in fs[:2]]))
        # 审计员 #376 第 6 条：这条**不能**说成「等长」的功绩 —— 抓住它的只有 D0。
        # 补一条反控把作用域钉死：关掉 D0 后同一改动**全 PASS**（D6/D7/D8 对等长改写无感）。
        rc_i, out_i = run([sys.executable, FACTS, led2, '--ignore-pin'], ROOT)
        ck('S1.2 反控：同一等长改动在 --ignore-pin 下 exit 0 ⇒ 唯一防线是 D0（D6/D7/D8 感知不到等长改写）',
           rc_i == 0, (rc_i, [l.strip()[:60] for l in out_i.split('\n') if l.strip().startswith('FAIL')][:3]))

        # S2：把台账整行删掉一行 ⇒ D3 必须 FAIL（不是只靠 D0）
        led3 = sbt + '/FACT_INDEX.short.tsv'
        txt = rd(LEDGER)
        ne = [l for l in txt.split('\n') if l]
        with open(led3, 'wb') as f:
            f.write(('\n'.join(ne[:-1]) + '\n').encode('utf-8'))
        rc_s, out_s = run([sys.executable, FACTS, led3, '--ignore-pin'], ROOT)
        d3 = [l.strip() for l in out_s.split('\n') if 'D3 data rows' in l]
        ck('S2.1 少一行 + --ignore-pin 仍报 D3（结构断言独立成立，不靠 D0）',
           rc_s != 0 and any('53' in l for l in d3), (rc_s, d3[:2]))

        # S3：沙箱主门禁：把 DISC_RECHECK 第 20 行版本改掉 ⇒ C10 必须 FAIL
        # 沙箱必须「同深度镜像」才能保真：check_disc 的 C7 会逐个 grep 大量产物文件，
        # 只拷几件会得到 60+ 个 FILE_MISSING 假 FAIL（本脚本 S3 第一版就踩了这个坑）。
        # 做法：/tmp/x/lead/ 下把真实 lead/ 的每个条目**逐项符号链接**，只把 tier 目录
        # 建成实体目录，并在其中逐项链接、唯独四个待改文件用实体副本。
        sb = sbt + '/gatesb'
        os.makedirs(sb)
        # check_disc 的 ROOT 由自身位置反推三层 ⇒ 沙箱根必须镜像「仓库根 + lead/ + tier/」三层。
        # 仓库根下除 lead/ 外全部符号链接（C7 的产物路径形如 _r94/falsify_r94.py，在仓库根下）。
        # _r161 也要镜像（否则某天有 C7 行把产物指向 _r161/* 就会变成假 FAIL）；只排除本脚本
        # 自己的沙箱目录前缀，避免自指。（审计员 #376 第 7 条①提出，按其结论修正。）
        for name in os.listdir(ROOT):
            if name == 'lead' or name.startswith('r161_runner_'):
                continue
            os.symlink(os.path.join(ROOT, name), sb + '/' + name)
        os.makedirs(sb + '/lead')
        for name in os.listdir(os.path.join(ROOT, 'lead')):
            if name == 'next_re_20261117_r14':
                continue
            os.symlink(os.path.join(ROOT, 'lead', name), sb + '/lead/' + name)
        os.makedirs(sb + '/lead/next_re_20261117_r14')
        OVERRIDE = {'check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv',
                    'R14_COMMON.md', 'STATUS_BOARD.md'}
        for name in os.listdir(TIER):
            if name in OVERRIDE:
                continue
            os.symlink(os.path.join(TIER, name), sb + '/lead/next_re_20261117_r14/' + name)
        for name in OVERRIDE:
            shutil.copy2(os.path.join(TIER, name), sb + '/lead/next_re_20261117_r14/' + name)
        okb, rcb, fsb, outb = g1(sb + '/lead/next_re_20261117_r14/check_disc.py')
        ck('S3.0 沙箱主门禁基线 exit 0（保真）', rcb == 0, (rcb, [x[:70] for x in fsb[:3]]))
        dr2 = rd(sb + '/lead/next_re_20261117_r14/DISC_RECHECK.tsv')
        cur = re.search(r"GATE_VER = '([^']+)'", dr2).group(1)
        bogus = 'R999'
        dr2b = dr2.replace("GATE_VER = '%s'" % cur, "GATE_VER = '%s'" % bogus, 1)
        with open(sb + '/lead/next_re_20261117_r14/DISC_RECHECK.tsv', 'wb') as f:
            f.write(dr2b.encode('utf-8'))
        okc, rcc, fsc, outc = g1(sb + '/lead/next_re_20261117_r14/check_disc.py')
        ck('S3.1 登记版本被改 ⇒ 主门禁 FAIL 且报 C10', rcc != 0 and any('C10' in x for x in fsc),
           (rcc, [x[:70] for x in fsc[:2]]))

        # S4：runner 的聚合判据本身 —— 拿一个必定失败的假门喂给 g1/g2
        fake = sbt + '/fake_gate.py'
        with open(fake, 'w', encoding='utf-8') as f:
            f.write('print("  FAIL  synthetic")\nraise SystemExit(1)\n')
        okf, rcf, fsf, _ = g1(fake)
        ck('S4.1 假门（exit 1 + FAIL 行）被判失败', (not okf) and rcf == 1, (okf, rcf))
        fake2 = sbt + '/fake_gate2.py'
        with open(fake2, 'w', encoding='utf-8') as f:
            f.write('print("all good")\nraise SystemExit(0)\n')
        okg, rcg, fsg, _ = g1(fake2)
        ck('S4.2 假门（exit 0 无 FAIL）被判通过（防「永远 FAIL」的假阳性）', okg and rcg == 0, (okg, rcg))

        # S5：G3 的交叉一致性也要有反控 —— 把 UN 副本改一字节 ⇒ G3b 必须不成立
        shadow = sbt + '/shadow'
        os.makedirs(shadow)
        gt = rd(GATE)
        with open(shadow + '/gate.py', 'w', encoding='utf-8') as f:
            f.write(gt)
        shutil.copy2(FACTS, shadow + '/facts.py')
        shutil.copy2(DR, shadow + '/DR.tsv')
        un_b = rb(UN)
        with open(shadow + '/UN.tsv', 'wb') as f:
            f.write(un_b[:-1] + (b'X' if un_b[-1:] != b'X' else b'Y'))
        shutil.copy2(LEDGER, shadow + '/LED.tsv')
        saved = list(fails)          # 这一段故意制造 FAIL：g3 会把 G3b 记进全局 fails，先隔离
        ok5, _ = g3(shadow + '/gate.py', shadow + '/facts.py', shadow + '/DR.tsv',
                    shadow + '/UN.tsv', shadow + '/LED.tsv', quiet=True)
        fails[:] = saved
        ck('S5.1 UN 改一字节 ⇒ G3b（FREEZE 一致性）不成立', not ok5, ok5)

        # S6：G3f 的已知失效模式是**假 FAIL**（不是假 PASS）——把 EVID 写成多行后重算会变。
        # 这条把「失效方向」钉住：宁可报警也不静默放过。
        ff = rd(FACTS)
        ff2 = ff.replace("    'F17': ['lead/next_re_20261117_r14/R14_COMMON.md'],",
                         "    'F17': ['lead/next_re_20261117_r14/R14_COMMON.md',\n            ],")
        ck('S6.0 多行改写确实改动了 facts_floors 源文本', ff2 != ff)
        okg3, _ = g3(GATE, shadow + '/facts.py', DR, UN, LEDGER, quiet=True)  # 基线（单行）应通过
        ck('S6.0b 基线（未改格式）G3 全通过（否则 S6.1 的 FAIL 没有意义）', okg3, okg3)
        with open(shadow + '/facts2.py', 'w', encoding='utf-8') as f:
            f.write(ff2)
        saved = list(fails)
        okf6, _ = g3(GATE, shadow + '/facts2.py', DR, UN, LEDGER, quiet=True)
        fails[:] = saved
        ck('S6.1 把 EVID 写成多行 ⇒ G3f 报 FAIL（失效方向是「假 FAIL」而非「静默放过」）',
           (not okf6), okf6)

        # S7：跑完整个自测后，生产 __pycache__ 的 mtime 一个都没变（禁写生效）
        pyc_after = {}
        if os.path.isdir(pydir):
            for n in sorted(os.listdir(pydir)):
                fp = os.path.join(pydir, n)
                if os.path.isfile(fp):
                    pyc_after[n] = os.stat(fp).st_mtime_ns
        ck('S7.1 生产 tier 下 __pycache__ 的 .pyc 一个都没被改写（禁写生效）',
           pyc_before == pyc_after, {'before': len(pyc_before), 'after': len(pyc_after),
                                     'changed': [k for k in pyc_before if pyc_after.get(k) != pyc_before[k]]})
    finally:
        shutil.rmtree(sbt, ignore_errors=True)

# ---------------------------------------------------------------- main

def main():
    mode = 'run'
    for a in sys.argv[1:]:
        if a == '--self-test':
            mode = 'self-test'
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        else:
            print('unknown arg: %s' % a)
            return 2

    print('=== gate_runner.py · R161 · %s ===' % ('self-test' if mode == 'self-test' else 'production'))
    print('\n== G1 · 主门禁 check_disc.py ==')
    ok1, rc1, f1, out1 = g1(GATE)
    ck('G1 主门禁 exit 0 且 FAIL 0', ok1, (rc1, len(f1)))

    print('\n== G2 · 事实层门禁 facts_floors.py ==')
    ok2, rc2, f2, out2 = g2(FACTS)
    ck('G2 事实层门禁 exit 0 且 FAIL 0', ok2, (rc2, len(f2)))

    print('\n== G3 · 两门之间的一致性（全部从盘上现算）==')
    ok3, gate_ver = g3(GATE, FACTS, DR, UN, LEDGER)

    if mode == 'self-test':
        self_test()

    print('\n== SUMMARY ==')
    print('  GATE_VER=%s  G1=%s  G2=%s  G3=%s' %
          (gate_ver, 'ok' if ok1 else 'FAIL', 'ok' if ok2 else 'FAIL', 'ok' if ok3 else 'FAIL'))
    print('  BOUNDARY: both gates share the same ceiling (co-editing data+constants still passes);')
    print('            this runner only removes "only one gate was run" and "the two gates drifted apart".')
    if fails:
        print('[exit 1] %d FAIL : %s' % (len(fails), fails[:6]))
        return 1
    print('[exit 0]')
    return 0

if __name__ == '__main__':
    sys.exit(main())
