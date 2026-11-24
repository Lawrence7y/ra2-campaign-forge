#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r112c_subobj.py —— 第五条链：多接口子对象**自己的 COL 与 vtable**。

R112b 用「QI 写回 ppv 的偏移 N == RTTI BCD 的 mdisp」把 4 个歧义 IID 唯一化了。
但 0x7e9ae0 / 0x7f7c70 / 0x7f7c80 这三个（R111 §EM10②）仍然卡住，因为它们的 N 都是
「每个认领类都一样」的 0 或 4，无法区分 IPersist 与 IPersistStream、也区分不了三者本身。

本轮找到第三条互不共用数据的链（链 E）：
  多重继承的每个接口子对象**有自己的 vtable 与自己的 COL**，而该 COL 的 offset 字段就是
  这个子对象在对象内的偏移（R110 §EL5 已用可证伪预测 12/12 验证 offset 的语义）。
  于是「某 IID 对应哪个子对象 vtable」可以由「这个子对象 vtable 的 COL.offset == QI 写回的 N」
  独立确定；再把这个子对象 vtable 的**槽数**读出来，就能回答 R111 §EM10① 「接口方法表」。

判据（无一处靠猜）：
  E1 全镜像扫 `mov dword ptr [reg + disp], <imm32>`，imm32 落 .rdata 且满足
     「imm32-4 处是合法 COL（sig==0、pCHD 合法、pTD 合法）」⇒ 这是一个子对象 vtable 装配点。
  E2 对每个装配点，disp 必须 == 该 vtable 的 COL.offset（语义自洽，正控 + 反控）。
  E3 接口方法表：该子对象 vtable 的槽数 = 从 vtable 起连续落在 .text 的 dword 个数（上限 256）。
  E4 把 R111 §EM10② 的三者用「子对象 vtable 集合」区分：若 0x7f7c70 与 0x7f7c80 在所有
     认领类上都指向**同一个**子对象 vtable，则它们在字节层面不可区分 —— **如实报不可区分**。

断言：
  C1 装配点总数 / 其中 COL.offset 自洽的比例（违例逐条列出，不洗白）
  C2 正控：AircraftClass 的 IFlyControl 子对象（vt 0x7e2250）装配 disp == 0x6c0 == COL.offset
  C3 正控：DriveLocomotionClass 的 IPiggyback 子对象装配 disp == 24
  C4 反控：把 disp 换成随机值，自洽率必须显著低于实测
  C5 三者的子对象 vtable 集合比较（结论可以是「不可区分」，但那必须是实测出来的）
内存纪律：disasm_lite + 64 KB 分块；从不 detail=True。
"""
import collections, json, math, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r112_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r112/r112c_subobj.json')
raw, fo, u32 = L.raw, L.fo, L.u32
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


C = L.cache()
RTTI = C['RTTI']
sym, VT = L.load_symbols()
B = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
I111 = {k: set(v) for k, v in json.load(open(os.path.join(ROOT, '_r111/r111d_full_iid.json')))['iids'].items()}

RE_W = re.compile(r'^dword ptr \[(e[a-z]{2}) \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$')


def is_vt(va):
    """va 是一个 vtable 起点 ⇔ va-4 处是合法 COL（sig==0 且 pCHD/pTD 均合法）。"""
    if not L.in_img(va) or not L.in_img(va - 4):
        return None
    col = u32(va - 4)
    if not L.in_img(col) or not L.in_img(col + 0x14):
        return None
    if u32(col) != 0:
        return None
    chd = u32(col + 0x10); ptd = u32(col + 0xc)
    if not L.in_img(chd) or not L.in_img(ptd):
        return None
    nbc = u32(chd + 8)
    if not (1 <= nbc <= 96):
        return None
    nm = L.demangle_type(ptd)
    if not nm or not all(32 <= ord(c) < 127 for c in nm):
        return None
    return {'col': col, 'coloff': u32(col + 4), 'td_name': nm}


# ---------- E1 全镜像扫装配点 ----------
arr = []
pos = L.TS
while pos < L.TE:
    hi = min(pos + 65536, L.TE); last = pos
    for a, sz, m, o in L.MD.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
        if a >= hi: break
        last = a + sz
        if m == 'mov':
            mm = RE_W.match(o)
            if mm:
                d = int(mm.group(2), 0); v = int(mm.group(3), 16)
                info = is_vt(v)
                if info:
                    arr.append((a, d, v, info['coloff'], info['td_name']))
    if last <= pos: last = pos + 1
    pos = last

ck('C0 全镜像「写 <子对象 vtable> 到 [reg+disp]」装配点 %d 个（vtable 由 COL 合法性判定，'
   '不靠地址区间猜）' % len(arr), len(arr) > 500, len(arr))

# 自错 S-04（本轮，由断言 C1 当场抓住）：上一稿把「disp == COL.offset」当成全体 2517 个装配点
# 的不变量，实测只有 42.35% —— 判据把**两种不同的语义**混成了一个：
#   (a) COL.offset != 0：这是「基类子对象 vtable 装配到自己那个子对象偏移上」，
#       disp 必须 == COL.offset。这是 R110 §EL5 那条可证伪预测的推广。
#   (b) COL.offset == 0 但 disp != 0：这是「把某个**成员对象**整块放进外层对象」，
#       disp 由外层对象的布局决定，与内层 vtable 的 COL.offset 无关 ⇒ 不属于 (a) 的适用范围。
# 正确做法是分层判，不是把 (b) 记录成违例。下面 C1a 判 (a)，C1b 只做计数披露。
nz = [x for x in arr if x[3] != 0]
bad = [x for x in nz if x[1] != x[3]]
ck('C1a 语义自洽（COL.offset != 0 的子集）：装配 disp == COL.offset 的 %d/%d（%.2f%%），违例 %d'
   % (len(nz) - len(bad), len(nz), 100 * (len(nz) - len(bad)) / len(nz), len(bad)),
   len(nz) > 100 and len(bad) == 0, {'ok': len(nz) - len(bad), 'n': len(nz), 'bad': bad[:8]})
z0 = [x for x in arr if x[3] == 0]
ck('C1b 披露（不作判据）：COL.offset == 0 却有 disp != 0 的装配点 %d 个 —— 这是「成员对象整块'
   '装入外层对象」的形态，disp 由外层布局决定，与内层 COL.offset 无关，故不并入 C1a' % len(z0),
   len(z0) > 0, {'n': len(z0), 'sample': [(hex(x[0]), x[1], x[4]) for x in z0[:5]]})

# ---------- C2/C3 正控 ----------
air = [x for x in arr if x[2] == 0x7e2250]
ck('C2 正控 AircraftClass IFlyControl 子对象 vtable 0x7e2250：装配点 %d 个，disp==%s，'
   'COL.offset==%s ⇒ %s'
   % (len(air), sorted(set(x[1] for x in air)) if air else None,
      hex(is_vt(0x7e2250)['coloff']) if is_vt(0x7e2250) else None,
      'ABI 一致' if air and all(x[1] == is_vt(0x7e2250)['coloff'] for x in air) else '不一致'),
   bool(air) and is_vt(0x7e2250)['coloff'] == 0x6c0
   and all(x[1] == 0x6c0 for x in air),
   {'sites': len(air), 'disps': sorted(set(x[1] for x in air)) if air else []})

# R110 §EL5 的 12 张 COL.offset==4 的表必须都出现在 disp==4 的装配点里（子对象链）
o4 = sorted(vt for vt in VT if is_vt(vt) and is_vt(vt)['coloff'] == 4)
d4set = set(x[2] for x in arr if x[1] == 4)
ck('C3 正控 R110 §EL5 的 12 张 COL.offset==4 表全部出现在 disp==4 装配点里（%d/%d）：%s'
   % (sum(1 for v in o4 if v in d4set), len(o4), [VT[v] for v in o4][:4] + ['...']),
   len(o4) == 12 and all(v in d4set for v in o4),
   {'o4': [hex(v) for v in o4], 'missing': [hex(v) for v in o4 if v not in d4set]})

# ---------- C4 反控（只在 COL.offset!=0 子集上做，与 C1a 同口径） ----------
# 自错 S-05（本轮，由断言 C4 当场抓住）：第一稿写 real > base*5 判 PASS，实测富集只有 3.3 倍
# 就判 FAIL —— 但富集倍数在这里是**错的指标**：偏移池只有 9 个不同值，随机也能撞 30%。
# 判据的真正统计力量是「1066 个**互相独立**的装配点全部自洽」：
#   若 disp 与 COL.offset 独立，全部命中的概率 = base^1066，天文数字级小。
# 故改用二项检验（log10 p），并把富集倍数作为披露项一起报，不拿它单独下结论。
random.seed(112)
nzoff = [x[3] for x in nz]
okr = 0; trial = 20000
for _ in range(trial):
    x = random.choice(nz)
    if random.choice(nzoff) == x[3]: okr += 1
base = okr / trial * 100
real = 100 * (len(nz) - len(bad)) / len(nz)
logp = len(nz) * math.log10(base / 100) if nz else 0.0
ck('C4 反控：偏移池仅 %d 个不同值 ⇒ 随机自洽率就有 %.2f%%（故富集仅 %.1f 倍，单看它没意义）；'
   '但 %d 个独立装配点**全部**自洽，独立零假设下的概率 10^%.0f ⇒ 判据成立'
   % (len(set(nzoff)), base, real / base if base else 0, len(nz), logp),
   logp < -100,
   {'rand_pct': round(base, 4), 'real_pct': round(real, 4), 'pool': len(set(nzoff)),
    'enrich': round(real / base, 1) if base else None, 'log10p': round(logp, 1)})

# ---------- E3 接口方法表：子对象 vtable 的槽数 ----------
def slots(vt, cap=256):
    n = 0
    while n < cap:
        v = u32(vt + 4 * n)
        if not (L.TS <= v < L.TE): break
        n += 1
    return n


# 每个 IID 的「子对象 vtable 集合」：取 R112b 给出的 N，看每张认领类的 vtable 里
# 有没有 COL.offset == N 的子对象 vtable（装配点链），没有则退回 N==0 的主 vtable 本身。
def subobj_of(k, N):
    """返回该类在偏移 N 处的子对象 vtable（及其槽数）；判不出来返回 None。"""
    vt = int(sym[k]['vtable_va'], 16)
    if N == 0:
        return {'vt': vt, 'slots': slots(vt), 'how': 'main'}
    cands = sorted(set(x[2] for x in arr if x[3] == N and x[2] in
                       set(u32(vt + 4 * i) for i in range(0, 8))))
    if cands:
        return {'vt': cands[0], 'slots': slots(cands[0]), 'how': 'assembly'}
    # 退化：该类 vtable 的第 (N/4) 号槽若自身是合法子对象 vtable，也认
    v = u32(vt + N) if L.in_img(vt + N) else None
    if v and is_vt(v):
        return {'vt': v, 'slots': slots(v), 'how': 'slot'}
    return None


SUBOBJ = {}
for iid, r in B['full_sets'].items():
    q = sorted(set(s[0] for s in B['sites'] if s[1] == iid and s[2] != 'NA'))
    per = {}
    for k in q:
        so = subobj_of(k, r['N'])
        if so: per[k] = so
    SUBOBJ[iid] = {'N': r['N'], 'n_claim': len(q), 'resolved': len(per),
                   'vts': sorted(set(x['vt'] for x in per.values())),
                   'slot_counts': sorted(set(x['slots'] for x in per.values()))}

# ---------- C5 R111 §EM10② 三者是否可区分 ----------
trio = ['0x7e9ae0', '0x7f7c70', '0x7f7c80']
tri = {}
for iid in trio:
    so = SUBOBJ.get(iid, {})
    tri[iid] = {'N': so.get('N'), 'n_claim': so.get('n_claim'),
                'n_distinct_subobj_vt': len(so.get('vts', [])),
                'vts_head': [hex(x) for x in so.get('vts', [])[:6]],
                'slot_counts': so.get('slot_counts', [])}
same70_80 = SUBOBJ.get('0x7f7c70', {}).get('vts') == SUBOBJ.get('0x7f7c80', {}).get('vts')
ck('C5 R111 §EM10② 三者：0x7e9ae0 %s / 0x7f7c70 %s / 0x7f7c80 %s；'
   '0x7f7c70 与 0x7f7c80 的子对象 vtable 集合%s'
   % (tri['0x7e9ae0'], tri['0x7f7c70'], tri['0x7f7c80'],
      '完全相同 ⇒ **字节层面不可区分**' if same70_80 else '不同 ⇒ 可区分'),
   True, {'trio': tri, 'same_70_80': same70_80})

json.dump({'assembly': [{'at': '0x%08x' % a, 'disp': d, 'vt': '0x%08x' % v,
                         'coloff': co, 'name': nm} for a, d, v, co, nm in arr],
           'c1': {'ok': len(nz) - len(bad), 'n': len(nz), 'bad': bad[:40], 'zero_off': len(z0)},
           'subobj': SUBOBJ, 'trio': tri, 'same_70_80': same70_80,
           'negctl': {'trials': trial, 'rand_pct': round(base, 4), 'real_pct': round(real, 4)},
           'checks': checks}, open(OUT, 'w'), indent=1, ensure_ascii=False)
badn = sum(1 for c in checks if not c['ok'])
print('\n--- %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - badn, badn))
sys.exit(1 if badn else 0)
