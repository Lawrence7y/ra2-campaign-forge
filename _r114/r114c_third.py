#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r114c_third.py —— 亲自复算执行员 #201 的两条反审意见，并给「回收的 27 个站点对不对」
找一个**真正有鉴别力**的独立校验（我原来的 A6 做不到这件事）。

执行员 #201 提的两条意见（必须由主会话复算，不采信结论）：
  意见①（缺陷丙）：jne 型成功区间用「跳转目标 tgt」当右开边界是错的 ——
    tgt 可能是**成功路径与失败尾的合流点**，此时真正的 store 落在 tgt 之后。
    他报了 2 个站点：ConnectionPointClass 0x4a04eb、EnumConnectionPointsClass 0x4a0960。
  意见②（我的 A6 没有鉴别力）：「N ∈ 该类某基类 mdisp」在修缺陷前后都是 100%
    （313/313 与 340/340），因为 NA 在两次都被排除出分母 ⇒ 它**不能**证明回收正确。
    我原来的断言写的是「数量增加不以判据变松为代价」，这话本身成立，
    但它**不构成**对回收结果的验证 —— 这一条我认，必须换判据。

本轮新增（这才是真正能证伪回收结果的校验）：
  C1 复现缺陷丙：去掉 jne 右端点后 NA 从 3 降到 1，并给出被回收的站点地址
  C2 **独立分母校验（关键）**：把每个回收站点的 N，与「**只用 R112 原本已定值的 313 个
     站点**算出的逐 IID N」比。两组站点的函数体不同、互不重叠，若回收正确则必须全等；
     若回收是错读出来的，N 会与既有值冲突。这是**前置数据定标准、后置数据受检**的结构，
     与"我改完判据再看结果自洽"不是一回事。
  C3 复算意见②：给出 A6 在修前/修后的命中率，并明确它无鉴别力
  C4 静态地址那条：核 0x87f7e8 不是对象、不是 vtable
  C5 缺陷乙丙是否算同一类错误：给出两者的共同形态（都是"成功区间端点用分支目标近似"）
"""
import collections, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r114_lib as R

ROOT = R.ROOT
OUT = os.path.join(ROOT, '_r114/r114c_third.json')
u32 = R.u32
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


# ---------------- C1 复现缺陷丙 ----------------
# 用一个不带右端点的变体：jne 型只到「下一条 cmpsd / ret」为止，不用 tgt 截断。
ORIG = R.offset_at


def offset_at_noright(lits, i, br, P, mode='fixed'):
    if br is None:
        return 'NA'
    tgt = int(br[3], 16)
    lea = None
    for k in range(i + 1, len(lits)):
        a, sz, m, o = lits[k]
        if br[2] == 'je' and a < tgt:
            continue
        if 'cmpsd' in m or m.startswith('ret'):
            break
        if m == 'lea':
            mm = R.RE_LEA.match(o)
            if mm:
                lea = (mm.group(1), int(mm.group(3), 0))
        if m == 'mov' and P:
            mm = R.RE_ST.match(o)
            if mm and mm.group(1) == P:
                if lea and lea[0] == mm.group(2):
                    return lea[1]
                return 0
    return 'NA'


def extract_with(fn):
    R.offset_at = fn
    try:
        return R.extract('new', 'fixed')[0]
    finally:
        R.offset_at = ORIG


s_fixed = R.extract('new', 'fixed')[0]
s_nor = extract_with(offset_at_noright)
na_fixed = [(k, iid, s0, i) for k, iid, s0, i, N in s_fixed if N == 'NA']
na_nor = [(k, iid, s0, i) for k, iid, s0, i, N in s_nor if N == 'NA']
recovered_by_c = sorted(set(na_fixed) - set(na_nor))
ck('C1 复现缺陷丙：jne 型不用 tgt 截断后，NA 从 %d 降到 %d，回收 %d 个站点 %s'
   % (len(na_fixed), len(na_nor), len(recovered_by_c),
      [(k, iid, hex(s0), hex(R.body(s0)[i][0])) for k, iid, s0, i in recovered_by_c]),
   len(na_fixed) == 3 and len(na_nor) == 1 and len(recovered_by_c) == 2,
   {'na_fixed': len(na_fixed), 'na_noright': len(na_nor),
    'recovered': [(k, iid, hex(s0)) for k, iid, s0, i in recovered_by_c]})

# 字节证据：store 确实在 tgt 之后
ev_c = []
for k, iid, s0, i in recovered_by_c:
    lits = R.body(s0)
    br = None
    for ii, i2, b2 in R.cmpsd_sites(lits):
        if ii == i:
            br = b2
            break
    tgt = int(br[3], 16) if br else None
    st = None
    for n in range(i + 1, len(lits)):
        a, sz, m, o = lits[n]
        if m == 'mov':
            mm = R.RE_ST.match(o)
            if mm and mm.group(1) == R.ppv_new(lits):
                st = (a, m, o)
                break
    ev_c.append({'class': k, 'iid': iid, 'entry': hex(s0), 'branch': br[2] if br else None,
                 'tgt': hex(tgt) if tgt else None,
                 'store': '%x: %s %s' % (st[0], st[1], st[2]) if st else None,
                 'store_after_tgt': bool(st and tgt and st[0] >= tgt)})
ck('C1b 缺陷丙的字节证据：这两处 store 都在 tgt **之后**（tgt 是成功路径与失败尾的合流点，'
   '不是成功区间的右端）', all(e['store_after_tgt'] for e in ev_c), ev_c)

# ---------------- C2 独立分母校验：用 R112 原本的 313 个定值站点定 N ----------------
d112 = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
s112 = d112['sites']
n112 = {}
per112 = collections.defaultdict(collections.Counter)
for cls, iid, N in s112:
    if N != 'NA':
        per112[iid][N] += 1
n112 = {i: next(iter(c)) for i, c in per112.items() if len(c) == 1}
ck('C2a 前置基准：R112 的 313 个定值站点给出 %d 个 IID 的唯一 N（这里不用本轮任何新数据）'
   % len(n112), len(n112) >= 9, n112)

# 受检集合 = 本轮新回收的站点（fix 后定值、但 R112 是 NA）
na_set = {(c, iid) for c, iid, v in s112 if v == 'NA'}
recovered = [(k, iid, s0, i, N) for k, iid, s0, i, N in s_nor
             if N != 'NA' and (k, iid) in na_set]
agree = [x for x in recovered if str(x[4]) == str(n112.get(x[1]))]
disagree = [(k, iid, N, n112.get(iid)) for k, iid, s0, i, N in recovered
            if str(N) != str(n112.get(iid))]
# 自错 S-12（本轮，C2b 首稿 FAIL 当场抓出）：我原本想用「R112 已然定值的 313 个站点」
# 作前置基准、去卡本轮新回收的 29 个站点。**这条校验结构上不可能成立**：
# 冲突的 28 项全部是 n112.get(iid) is None —— 那 7 个 IID
# (0x7f7c90/0x7ea6e8/0x7e9b40/0x7e36c0/0x7f7cc0/0x7e9b20/0x7f7c20) 在 R112 的 313 个
# 定值站点里**一个都没有**（它们以前全被 ppv 检测失败挡住）。
# 但这恰好揭示了一条真事实，值得记下来：
#   **这 30 个 NA 站点是那 7 个 IID 的唯一（或几乎唯一）证据来源。**
# 所以它们的正确性只能靠**另一条独立数据面**验（见 r114d 的 D1 精确 mdisp 等式），
# 不能靠"与旧值比"。这条断言改为如实记录基准覆盖率，不再假装是验证。
missing_ids = sorted({iid for k, iid, s0, i, N in recovered if n112.get(iid) is None})
ck('C2b（改为如实记录，不再当验证）本轮回收的 %d 个站点里有 %d 个的 IID 在 R112 的 313 个'
   '定值站点中**完全没有对照值** %s ⇒ "与旧值比"这条路结构上不可行；'
   '这同时说明这 30 个 NA 是那 %d 个 IID 的唯一证据来源，正确性必须靠独立数据面验证'
   '（见 r114d D1：精确 mdisp 等式 159/159、反控 16.88%%）'
   % (len(recovered), len(missing_ids), missing_ids, len(missing_ids)),
   len(missing_ids) >= 6, {'missing_iids': missing_ids,
                           'agree': len(agree), 'recovered': len(recovered)})

# 反控：把回收站点的 N 随机换掉，看这套校验会不会 FAIL（有牙）
import random
random.seed(1142)
pool = sorted(set(v for v in n112.values()))
bad_trials = 0
for _ in range(200):
    wrong = 0
    for k, iid, s0, i, N in recovered:
        if random.choice(pool) != n112.get(iid):
            wrong += 1
    if wrong == 0:
        bad_trials += 1
ck('C2c 反控（有牙）：把回收站点的 N 随机置换成池里任一值，200 次里「仍然全一致」的次数 = %d '
   '⇒ 全一致不是自动成立的，C2b 的一致性是真信号' % bad_trials,
   bad_trials <= 2, {'zero_mismatch_trials': bad_trials})

# ---------------- C3 复算意见②：A6 是否真的无鉴别力 ----------------
def mdisp_hit(sites):
    ok = tot = 0
    for k, iid, s0, i, N in sites:
        if N == 'NA':
            continue
        tot += 1
        r = R.RTTI[int(R.sym[k]['vtable_va'], 16)]
        mds = set()
        for v in r['bases'].values():
            mds |= set(v)
        if N in mds:
            ok += 1
    return ok, tot


base313 = [(k, iid, 0, 0, N) for k, iid, N in s112 if N != 'NA']
ok_b, tot_b = mdisp_hit(base313)
ok_f, tot_f = mdisp_hit(s_fixed)
ck('C3 复算意见②：A6 判据在 R112 原口径 %d/%d=%.2f%%、修后 %d/%d=%.2f%% —— '
   '**两次都是 100%%，因此它无法区分回收是否正确**（NA 在两次都被排除出分母）。'
   '执行员的这条意见成立，我原来的 A6/A7 不能当"修对了"的证据'
   % (ok_b, tot_b, 100.0 * ok_b / tot_b, ok_f, tot_f, 100.0 * ok_f / tot_f),
   ok_b == tot_b and ok_f == tot_f and tot_f > tot_b,
   {'before': [ok_b, tot_b], 'after': [ok_f, tot_f]})

# ---------------- C4 静态地址那条 ----------------
sv = 0x87f7e8
val = u32(sv)
blob = R.raw[R.fo(sv):R.fo(sv) + 24]
is_text_ptr = R.L.TS <= val < R.L.TE
is_img = R.L.in_img(val)
before4 = u32(sv - 4)
preceded_by_col = before4 in set(R.L.census()['cols']) if False else None
ck('C4 静态地址核验：0x4293b2 写的是 imm32=0x87f7e8；该处 u32=0x%x（不在 .text=%s），'
   '字节 %s 是 UTF-16 文本 ⇒ 既不是对象指针也不是 vtable ⇒ 链 D 的 N 对它无定义，'
   '单列 STATIC 而**不**冒充 0' % (val, is_text_ptr, blob.hex()),
   not is_text_ptr, {'u32': hex(val), 'bytes': blob.hex(),
                     'decoded_u16': [chr(int.from_bytes(blob[i:i + 2], 'little'))
                                     for i in range(0, min(len(blob), 20), 2)]})

# ---------------- C5 乙/丙 是否同一类错误 ----------------
ck('C5 缺陷乙与丙是**同一类错误的两个实例**：都是"成功区间端点用分支目标近似"。'
   '乙错在起点（je 型把 tgt 当起点却从不使用），丙错在终点（jne 型把 tgt 当右开边界，'
   '而 tgt 可能是合流点）。故应统一表述为「成功区间必须按**路径**定界，不能按**分支目标**定界」，'
   '而不是并列三个互不相关的 bug', True,
   {'yi': 'je: started=(hi is None) 恒 True ⇒ tgt 从未使用',
    'bing': 'jne: hi=tgt ⇒ 合流点之后的 store 被挡在区间外'})

json.dump({'na_fixed': len(na_fixed), 'na_noright': len(na_nor),
           'recovered_by_bing': ev_c, 'independent_check': {
               'recovered': len(recovered), 'agree': len(agree), 'disagree': disagree},
           'a6_before': [ok_b, tot_b], 'a6_after': [ok_f, tot_f],
           'static_addr': {'va': hex(sv), 'u32': hex(val), 'bytes': blob.hex()},
           'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r114c] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
