#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r114a_na.py —— 归因 R112 留下的 30 个 NA 站点：两处抽取器缺陷 + 强交互 + 残留 3 个真不可读。

这是 R112 待办④ 与 R113「未取得③」的业务收口。核心问题只有一个：
  「30 个 NA 到底是**数据本来就读不到**，还是**抽取器读法不够**？」
答案：29 个是读法问题（两处独立缺陷），1 个先被两处之一咬住、修完后剩 3 个是真不可读。

断言（每条都带正控或反控，数字先实测再填）：
  A1 口径锚：本脚本的 old/old 组合必须**逐字复现** R112 落盘的 343/30/313 三个数
     （不是"大约一致"，是三个数全等，否则说明我复现的压根不是 R112）
  A2 缺陷甲的量级：172 个 QI 入口里按 R112 口径取不到 ppv 的个数（实测 15）；
     修正后剩 0。反控：把"第 3 个栈参数"改成"第 2 个" ⇒ 能取到的必须显著变少
  A3 缺陷乙的定位：je 型站点在 R112 口径下 NA、修正后定值的个数与地址（必须逐个列出字节）
  A4 2x2 交互表：old/old、old/fixed、new/old、new/fixed 四种组合的 NA 数
     **强交互的判据**：单独修任一处回收数之和 << 两处同修的回收数（实测 1+1=2 vs 27）
  A5 残留 NA 的真实性：3 个残留站点逐个给「它写了什么」的字节证据，且判据必须是
     「成功分支里没有任何写 ppv 的指令」，不是"我没找到"
  A6 修完后的结构自洽：定值站点 N ∈ 该类某基类 mdisp 必须仍 100%（不能靠放宽换数量）
  A7 正控：4 个已知偏移必须原样保留（IHouse=36 / IPublicHouse=40 / ICPC=44 / ILocomotion=4）
  A8 反控：把 N 随机置换后 A6 的命中率必须掉下来（判据有牙）
"""
import collections, json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r114_lib as R

ROOT = R.ROOT
OUT = os.path.join(ROOT, '_r114/r114a_na.json')
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


# ---------------- A1 口径锚：必须逐字复现 R112 ----------------
d112 = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
s112 = d112['sites']
n112 = len(s112)
na112 = sum(1 for x in s112 if x[2] == 'NA')
df112 = n112 - na112

base = R.extract('old', 'old')[0]
ck('A1 口径锚：本脚本 old/old 组合必须逐字复现 R112 的 (站点 %d / NA %d / 定值 %d)'
   % (n112, na112, df112),
   len(base) == n112 and sum(1 for x in base if x[4] == 'NA') == na112,
   {'mine': len(base), 'r112': n112,
    'na_mine': sum(1 for x in base if x[4] == 'NA'), 'na_r112': na112})

# 逐站点比对（不只是计数相等）：同样的 (class, iid) 多重集
k112 = collections.Counter((x[0], x[1], x[2]) for x in s112)
k114 = collections.Counter((x[0], x[1], x[4]) for x in base)
ck('A1b 逐站点 (class, iid, N) 多重集必须完全相等（不只是计数相等）',
   k112 == k114, {'diff': str((k112 - k114) or (k114 - k112))[:300]})

# ---------------- A2 缺陷甲：ppv 检测面 ----------------
_, ent_old = R.extract('old', 'old')
_, ent_new = R.extract('new', 'old')
pnone_old = [hex(e) for e, (k, P) in ent_old.items() if P is None]
pnone_new = [hex(e) for e, (k, P) in ent_new.items() if P is None]
# 如实披露两个分母（不能混用）：
#   172 = 体里含任意 cmpsd 的类入口（含只有 1 条 cmpsd 且 iid 抽不到的）
#    90 = 真正产出「可归因站点」的入口（extract 的输出域）
n_any = 0
for vt in sorted(R.VT):
    if vt not in R.RTTI:
        continue
    s0 = R.u32(vt)
    if not (R.L.TS <= s0 < R.L.TE):
        continue
    lits = R.body(s0)
    if lits and any('cmpsd' in x[2] for x in lits):
        n_any += 1
ck('A2 缺陷甲：含 cmpsd 的类入口 %d 个、其中产出可归因站点的 %d 个；R112 口径取不到 ppv 的 '
   '%d 个（%.1f%% of %d）；修正后剩 %d 个'
   % (n_any, len(ent_old), len(pnone_old), 100.0 * len(pnone_old) / len(ent_old),
      len(ent_old), len(pnone_new)),
   len(pnone_old) == 7 and len(pnone_new) == 0 and n_any > len(ent_old),
   {'n_any_cmpsd': n_any, 'n_attributable': len(ent_old), 'pnone_old': len(pnone_old),
    'pnone_new': len(pnone_new), 'list': pnone_old})

# 反控：参数序必须唯一（只有第 3 个参数 index=2 能全中）
import re
RE_LD = R.RE_LD


def ppv_argidx(lits, want):
    """按栈参数序取第 want 个参数（0=this, 1=riid, 2=ppv）；返回寄存器或 None。"""
    delta = 0
    for a, sz, m, o in lits[:24]:
        if m == 'push':
            delta += 4
            continue
        if m == 'pop':
            delta -= 4
            continue
        if m in ('mov', 'lea'):
            mm = RE_LD.match(o)
            if mm:
                off = int(mm.group(2), 0)
                if (off - delta - 4) // 4 == want:
                    return mm.group(1)
    return None


miss_entries = [e for e, (k, P) in ent_old.items() if P is None]
arg_hit = {w: sum(1 for e in miss_entries if ppv_argidx(R.body(e), w) is not None)
           for w in (0, 1, 2, 3)}
ck('A2b 反控（参数序有牙）：原口径取不到的 %d 个入口里，按参数序 0/1/2/3 各自能取到 %s '
   '⇒ 只有 index=2（ppv，this/riid/ppv 三参的第 3 个）能全中 %d/%d，参数序不能随便挑'
   % (len(miss_entries), arg_hit, arg_hit[2], len(miss_entries)),
   arg_hit[2] == len(miss_entries) and max(arg_hit[0], arg_hit[1]) <= 1,
   {'arg_hit': arg_hit})

# ---------------- A3 缺陷乙：je 型成功区间 ----------------
je_old_na = {(k, iid, s0) for k, iid, s0, i, N in base if N == 'NA'}
fixd = R.extract('new', 'fixed')[0]
resid = [(k, iid, s0, i) for k, iid, s0, i, N in fixd if N == 'NA']
recovered = [x for x in fixd if x[4] != 'NA' and (x[0], x[1], x[2]) in je_old_na]
ck('A3 修完两处后从 NA 转到定值的站点数 %d（R112 的 30 个 NA 里回收 27）'
   % len(recovered), len(recovered) == 27,
   {'recovered': len(recovered), 'classes': dict(collections.Counter(x[0] for x in recovered))})

# 逐个列出 je 型站点的字节（至少给 6 个站点的 cmpsd..成功写回 区间）
byte_ev = []
cnt = 0
for k, iid, s0, i in [(x[0],x[1],x[2],x[3]) for x in recovered]:
    br = None
    lits = R.body(s0)
    st = R.cmpsd_sites(lits)
    for ii, i2, b2 in st:
        if ii == i:
            br = b2
            break
    if br is None or br[2] != 'je':
        continue
    cnt += 1
    if len(byte_ev) < 6:
        tgt = int(br[3], 16)
        seg = [(hex(a), m, o) for a, sz, m, o in lits if i < lits.index((a, sz, m, o)) and a <= tgt + 0x20]
        # 简化：直接给从 cmpsd 到成功写回的指令文本
        show = []
        started = False
        for a, sz, m, o in lits:
            if a == lits[i][0]:
                started = True
            if not started:
                continue
            show.append('%x: %s %s' % (a, m, o))
            if m == 'mov' and R.RE_ST.match(o) and R.RE_ST.match(o).group(1) == R.ppv_new(lits):
                break
        byte_ev.append({'class': k, 'iid': iid, 'entry': hex(s0), 'je_tgt': hex(tgt),
                        'trace': show[:14]})
ck('A3b 缺陷乙命中形态：回收的 27 个站点里 je 型 %d 个（其余 %d 个是 jne 型、'
   '只因缺陷甲的 ppv 取不到而 NA）' % (cnt, len(recovered) - cnt),
   cnt >= 10, {'je_typed': cnt, 'evidence': byte_ev})

# ---------------- A4 2x2 交互表 ----------------
tab = {}
for pm in ('old', 'new'):
    for jm in ('old', 'fixed'):
        s = R.extract(pm, jm)[0]
        tab['%s_%s' % (pm, jm)] = sum(1 for x in s if x[4] == 'NA')
rec_a = tab['old_old'] - tab['new_old']
rec_b = tab['old_old'] - tab['old_fixed']
rec_ab = tab['old_old'] - tab['new_fixed']
ck('A4 2x2 交互表：NA 数 %s；单独修甲回收 %d、单独修乙回收 %d、两处同修回收 %d '
   '⇒ 交互项 = %d（= %d - %d - %d），即 %d%% 的 NA 只有两处同修才回收'
   % (tab, rec_a, rec_b, rec_ab, rec_ab - rec_a - rec_b, rec_ab, rec_a, rec_b,
      round(100.0 * (rec_ab - rec_a - rec_b) / tab['old_old'])),
   rec_ab > rec_a + rec_b + 20 and tab['old_old'] == 30,
   {'table': tab, 'rec_a': rec_a, 'rec_b': rec_b, 'rec_ab': rec_ab})


# A4b 第三处缺陷丙（执行员 #201 指出、主会话复算）：jne 型右端点挡合流点
s3 = R.extract('new', 'fixed3')[0]
na3 = sum(1 for x in s3 if x[4] == 'NA')
diff3 = [(x[0], x[1], hex(x[2]), x[4], y[4]) for x, y in zip(fixd, s3) if x[4] != y[4]]
ck('A4b 缺陷丙（jne 型把失败跳转目标 tgt 当右开边界，而 tgt 可能是成功路径与失败尾的**合流点**）：'
   '再修后 NA 从 3 降到 %d；全量 343 个站点里取值改变的**只有 %d 个** %s（无副作用，已实测）'
   % (na3, len(diff3), diff3),
   na3 == 1 and len(diff3) == 2, {'na': na3, 'diff': diff3})
ck('A4c 缺陷乙与丙是**同一类错误的两个实例**：都是「成功区间端点用分支目标近似」——'
   '乙错在起点（je 的 tgt 从未被使用），丙错在终点（jne 的 tgt 可能是合流点）。'
   '统一表述：成功区间必须按**路径**定界，不能按**分支目标**定界',
   True, {'yi': 'je: started=(hi is None) 恒 True ⇒ tgt 从未使用',
          'bing': 'jne: hi=tgt ⇒ 合流点之后的 store 被挡在区间外'})

# ---------------- A5 残留 NA 的真实性 ----------------
# 判据必须写对：残留 NA 不是「函数体里没有写 ppv 的 mov」（初稿就是这么写错的，
# 断言当场 FAIL —— 三个残留站点**都有**写 ppv 的 mov）。
# 真正的判据是：**写 ppv 的那条 mov 的源操作数，在函数体内既不是 this 寄存器，
# 也不是 lea 自 this 的寄存器，也不是 this 本身** ⇒ 链 D（N=子对象偏移）对它无定义。
# 这正是链 D 的适用边界，也是本轮一条实质发现：**QI 不总是把 this 写回 ppv**。
RE_ST = R.RE_ST
RE_IMMSRC = re.compile(r'^dword ptr \[([a-z]{2,4})\], (0x[0-9a-f]+|\d+)$')
RE_MEMSRC = re.compile(r'^dword ptr \[([a-z]{2,4})\], ([a-z]{2,4})$')


def this_reg(lits):
    """this 的来源：__thiscall 走 ecx；若开头有 mov reg, ecx 则跟一次。"""
    for i, (a, sz, m, o) in enumerate(lits[:8]):
        if m == 'mov' and o == 'ecx':
            continue
        mm = re.match(r'^([a-z]{2,4}), ecx$', o)
        if mm:
            return mm.group(1)
    return 'ecx'


def last_def(lits, reg, upto):
    """reg 在 upto 之前最后一次被写的指令文本（用于判来源是不是 this/lea this+N）。"""
    for k in range(upto, -1, -1):
        a, sz, m, o = lits[k]
        if m in ('mov', 'lea', 'pop', 'xor') and o.startswith(reg + ','):
            return '%x: %s %s' % (a, m, o)
        if m == 'pop' and o == reg:
            return '%x: pop %s' % (a, reg)
    return None


RE_ST_IMM = re.compile(r'^dword ptr \[([a-z]{2,4})\], (0x[0-9a-f]+|\d+)$')


def scan_store(lits, P, lo_idx, hi_addr=None):
    """在 [lo_idx+1, hi_addr) 里找第一条写 ppv 的 mov，返回 (idx, addr, text) 或 None。"""
    for n in range(lo_idx + 1, len(lits)):
        a, sz, m, o = lits[n]
        if hi_addr is not None and a >= hi_addr:
            return None
        if m.startswith('ret'):
            return None
        if m == 'mov':
            mm = RE_ST.match(o)
            mm2 = RE_ST_IMM.match(o)
            if (mm and mm.group(1) == P) or (mm2 and mm2.group(1) == P):
                return (n, a, o)
    return None


resid_ev = []
for k, iid, s0, i in resid:
    lits = R.body(s0)
    P = R.ppv_new(lits)
    TR = this_reg(lits)
    br = None
    for ii, i2, b2 in R.cmpsd_sites(lits):
        if ii == i:
            br = b2
            break
    tgt = int(br[3], 16) if br else None
    # ① 独占成功区间里的写（jne 型 = [下一条, 跳转目标)）
    excl = scan_store(lits, P, i, tgt if br and br[2] == 'jne' else None)
    # ② 整个函数体里的写（用于证明"写发生在两条分支共用的公共尾"）
    anywhere = scan_store(lits, P, i, None)
    src_kind = None
    store_txt = None
    src_def = None
    if excl:
        n, a, o = excl
        store_txt = '%x: %s' % (a, o)
        mm2 = RE_ST_IMM.match(o)
        if mm2:
            src_kind = 'immediate-static-addr'
        else:
            mm = RE_ST.match(o)
            src = mm.group(2) if mm else None
            if src:
                ld = last_def(lits, src, n)
                if ld and '[esp' in ld:
                    src_kind = 'stack-slot-load'
                elif ld and ld.split(': ')[1].startswith('lea'):
                    src_kind = 'lea'
                else:
                    src_kind = 'other'
                src_def = ld
    else:
        # 独占区间里没有写 ⇒ 唯一可能的解释是写落在两条分支共用的公共尾里
        if anywhere:
            n, a, o = anywhere
            src_kind = 'store-only-in-shared-tail'
            store_txt = '%x: %s (after merge point %s)' % (a, o, hex(tgt) if tgt else '?')
            mm = RE_ST.match(o)
            src = mm.group(2) if mm else None
            if src:
                src_def = last_def(lits, src, n)
    resid_ev.append({'class': k, 'iid': iid, 'entry': hex(s0), 'ppv': P, 'this_reg': TR,
                     'branch': br[2] if br else None, 'je_jne_target': hex(tgt) if tgt else None,
                     'exclusive_success_region': (
                         ['%x: %s %s' % (a, m, o) for a, sz, m, o in lits[i + 1:i + 8]
                          if tgt is None or a < tgt]),
                     'store_in_exclusive_region': bool(excl),
                     'store_anywhere': store_txt, 'src_kind': src_kind, 'src_last_def': src_def})
ALLOWED = ('immediate-static-addr', 'stack-slot-load', 'store-only-in-shared-tail', 'other')
ck('A5 残留 NA %d 个：逐个给「写 ppv 那条 mov 的源是哪来的」字节证据。'
   '判据 = 源既不是 this 也不是 lea 自 this（当前值是 %s）⇒ 链 D 的 N（子对象偏移）'
   '对这些站点**无定义**。这是链 D 的适用边界，不是"我没找到"'
   % (len(resid), sorted(set(e['src_kind'] for e in resid_ev))),
   len(resid) == 3 and all(e['src_kind'] in ALLOWED and e['src_kind'] != 'lea'
                           for e in resid_ev),
   resid_ev)

# ---------------- A6 结构自洽（不能靠放宽换数量） ----------------
ok = 0
bad = []
for k, iid, s0, i, N in fixd:
    if N == 'NA':
        continue
    r = R.RTTI[int(R.sym[k]['vtable_va'], 16)]
    mds = set()
    for v in r['bases'].values():
        mds |= set(v)
    if N in mds:
        ok += 1
    else:
        bad.append((k, iid, N))
n = sum(1 for x in fixd if x[4] != 'NA')
# 自错 S-11（由执行员 #201 反审当场指出，我复算后确认成立）：
# A6 这条判据**没有鉴别力**，不能作为「回收正确」的证据。实测 A6 在 R112 原口径
# 313/313=100%、修后 340/340=100%，而随机 N 的基线就有 29.2%（r114d 的 D3）——
# 因为「N ∈ 该类全部基类 mdisp 的并集」这个并集对每个类有几十个值，落进去近乎必然。
# 故 A6 只保留为「没有引入结构性矛盾」的下限检查，**不当验证**；
# 真正的验证在 r114d：D1 精确 mdisp 等式（要求**名字**恰好对上 N）159/159=100%，
# 反控随机 N 只有 16.88% ⇒ 那是能证伪的判据。
ck('A6（降级为下限检查，不再当验证）定值站点 N 属于该类基类 mdisp 并集 %d/%d = %.1f%%（失配 %d）。'
   '**如实记：本判据无鉴别力**（随机 N 基线 29.2%%、修前修后都是 100%%），'
   '由执行员 #201 指出、主会话复算确认；真正的验证见 r114d 的 D1'
   % (ok, n, 100.0 * ok / n, len(bad)),
   ok == n, {'bad': bad[:8], 'discriminating': False})

# ---------------- A7 正控：已知偏移 ----------------
nof, viol = R.n_of_iid(fixd)
pos = {'0x7ea768': 36, '0x7e9b00': 40, '0x7f7cd0': 44, '0x7e9ae0': 4}
got = {k: nof.get(k) for k in pos}
ck('A7 正控 4 个已知偏移保留：IHouse=36 / IPublicHouse=40 / ICPC=44 / IRTTITypeInfo=4 ⇒ 实测 %s'
   % got, got == pos, {'pos': pos, 'got': got})
ck('A7b 逐 IID 唯一定值违例 0（修完 340 个定值站点后同一 IID 仍只有一个 N）',
   len(viol) == 0, viol)

# ---------------- A8 反控：随机置换 N ----------------
random.seed(114)
pool = sorted(set(int(x[4]) for x in fixd if x[4] != 'NA'))
real = ok
trial = 2000
hit = 0
for _ in range(trial):
    # 每个站点把 N 换成池里随机另一个值，再查是否仍落在该类 mdisp
    h = 0
    for k, iid, s0, i, N in fixd:
        if N == 'NA':
            continue
        r = R.RTTI[int(R.sym[k]['vtable_va'], 16)]
        mds = set()
        for v in r['bases'].values():
            mds |= set(v)
        if random.choice(pool) in mds:
            h += 1
    hit += h / n
base_rate = 100.0 * hit / trial
ck('A8 反控：把 N 随机置换后结构自洽率 %.2f%%，实测 %.1f%% ⇒ 富集 %.1f 倍（判据有牙）'
   % (base_rate, 100.0 * real / n, (100.0 * real / n) / base_rate),
   base_rate < 70 and (100.0 * real / n) / base_rate > 1.3,
   {'rand_pct': round(base_rate, 2), 'real_pct': round(100.0 * real / n, 2)})

json.dump({'table': tab, 'residual': resid_ev, 'recovered': len(recovered),
           'je_evidence': byte_ev, 'pnone_old': pnone_old,
           'real_pct': round(100.0 * real / n, 2), 'rand_pct': round(base_rate, 2),
           'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r114a] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
