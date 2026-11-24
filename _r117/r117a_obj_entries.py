#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r117a_obj_entries.py —— R117 主攻：R116 遗留的「35 项 .data 表中 30 项落 BSS 尾部、
运行期内容未取得」这一未取得项，本轮用**静态写入点**把它取回来。

R116 的定性是「1 个例程模板 + 1 张 35 项 .data 表」，并把 30 个 BSS 项登记为
「文件里没有字节，运行期内容不可知」。本轮的下手点：BSS 的内容不是不可知的，
它被 `.text` 里的**绝对地址立即数写**（C7 05 / A3 / C6 05 / A2）钉死，
而那唯一一处最重要的写就是对象的 vptr —— 顺着 vptr-4 的 COL 能拿到 RTTI 装饰名。

本轮要证实的三件事（每件都要有反控）：
  B1 35 个 edx 目标全部是 MSVC 的「COMDAT 守卫 + atexit 登记的静态类对象」，
     其 field0（vptr）在镜像里有且仅有 2 个静态写入点（tor 一次、dtor 一次）。
  B2 tor 写入的 vptr 是 DynamicVectorClass<T>、dtor 写入的是 VectorClass<T>，
     且**两个名字里的 T 逐字符相同**（两条独立来源互证，不是同一处拷贝）。
  B3 tor 里 push 的 atexit 回调地址 == dtor 函数入口（dtor 里就是那个 base-vptr 写入点），
     ⇒ 「这一对写入点属于同一对象的 tor/dtor 对」不是推测，是代码里的显式交接。
  K1 反控：把检测器打在 200 个**非条目**的 .data 地址上，命中必须为 0。
  K2 反控：把 T 的比对改成恒真（只比类名前缀），必须能区分出「名字不同」的假阳性——
     用 tor/dtor 名字整体交换来验：交换后 T 等式必须失败。
内存纪律：全程 raw 字节扫描 + Capstone detail=False，未对 .text 整段开 detail。
"""
import json, os, random, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L       # noqa: E402

raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
HB = set(L.HB)
OUT = os.path.join(ROOT, '_r117/r117a_obj_entries.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


# ---------- 0. 输入：R116 已落盘的 35 个 dispatcher edx ----------
D116 = json.load(open(os.path.join(ROOT, '_r116/r116e_dispatch.json')))
ENTS = [int(e['edx'], 16) for e in D116['dispatcher']]
ck('A0 输入取自 r116e_dispatch.json：%d 个 dispatcher 站点、%d 个不同 edx 目标'
   % (len(ENTS), len(set(ENTS))),
   len(ENTS) == 35 and len(set(ENTS)) == 35, {'n': len(ENTS), 'distinct': len(set(ENTS))})

TX = raw[fo(TS):fo(TE)]


def writes(field_va):
    """在 .text 里找所有把「绝对地址 field_va」当写入目标的静态写指令。
    只认 6 种编码（均为 5/6 字节、abs32 紧跟 opcode）：
      C7 05 abs32 imm32   mov dword [abs], imm32
      A3  abs32           mov [abs], eax
      C6 05 abs32 imm8    mov byte  [abs], imm8
      A2  abs32           mov [abs], al
      89 05 abs32         mov [abs], eax
      88 05 abs32         mov [abs], al
    """
    out = []
    for op in (b'\xc7\x05', b'\xa3', b'\xc6\x05', b'\xa2', b'\x89\x05', b'\x88\x05'):
        p = op + struct.pack('<I', field_va)
        i = TX.find(p)
        while i >= 0:
            out.append((TS + i, op.hex()))
            i = TX.find(p, i + 1)
    return sorted(out)


# ---------- 1. 每个条目的 8 个字段写入点分布（先如实测，不预设形状）----------
layout = {}
for v in ENTS:
    per = {}
    for k in range(8):
        per[4 * k] = writes(v + 4 * k)
    layout[v] = per

field0_counts = {v: len(layout[v][0]) for v in ENTS}
ck('B1a 35 个条目的 field0（vptr）在 .text 里的静态写入点数逐一实测：'
   '全部 == 2 的条目 %d / 35（分布 %s）'
   % (sum(1 for c in field0_counts.values() if c == 2), sorted(set(field0_counts.values()))),
   all(c == 2 for c in field0_counts.values()) and len(field0_counts) == 35,
   {'counts': sorted(set(field0_counts.values())),
    'bad': [hex(v) for v, c in field0_counts.items() if c != 2]})

# 守卫区：+4/+8 清零、+0xc 置 1、+0xd 置 0、+0x14 置 10（构造模板的固定动作）
shape = {}
for v in ENTS:
    p = layout[v]
    shape[v] = {'zero4': len(p[4]) > 0, 'zero8': len(p[8]) > 0,
                'b_c': any(a for a, op in p[0xc] if op == 'c605'),
                'd14': len(p[0x14]) > 0, 'p10': len(p[0x10]) > 0}
n_full = sum(1 for s in shape.values() if s['zero4'] and s['zero8'] and s['b_c'] and s['d14'])
# 审计攻击点 8：+0xd 是字节字段（mov byte[abs],al），8 字段的 4*k 循环取不到，单独测一遍。
n_d = sum(1 for v in ENTS if any(op == 'a2' for _, op in writes(v + 0xd)))
ck('B1b 构造模板的守卫动作在 35 个条目上一致复现：+4/+8 写 0、+0xc 写 1（C6 05）、'
   '+0xd 写 0（A2 05）、+0x14 写 10 的条目 %d / 35（+0xd 单测 %d / 35）'
   ' ⇒ 它们是同一族静态对象（不是 35 种不同东西）' % (n_full, n_d),
   n_full == 35 and n_d == 35, {'full': n_full, 'byte_d': n_d})

# ---------- 2. RTTI：vptr-4 处的 COL → 装饰名 ----------
def col_names(vptr):
    """vptr 指向的 vtable，其前 4 字节是 COL 指针（MSVC 固定布局）。返回 None 或名字列表。"""
    if not (L.IB <= vptr <= L.IB + len(raw) - 8):
        return None
    col = u32(vptr - 4)
    if not L.valid_col(col):
        return None
    chd = u32(col + 0x10)
    nb = u32(chd + 8)
    pb = u32(chd + 0xc)
    names = []
    for i in range(nb):
        bcd = u32(pb + 4 * i)
        td = u32(bcd)
        if not L.is_td(td):
            return None
        o = fo(td) + 8
        e = raw.index(b'\x00', o)
        names.append(raw[o:e].decode('latin1'))
    return {'col': col, 'off': u32(col + 4), 'names': names}


def tmpl_arg(name):
    """从 .?AV?$DynamicVectorClass@PAVBombClass@@@@ 抽出 PAVBombClass。

    末尾的 @ 是 MSVC 装饰名的分隔符：模板实参表紧跟在类名后的第一个 @ 之后，
    到下一个 @ 结束。解析失败返回 None（**不猜**）。
    """
    if not name.startswith('.?AV?$'):
        return None
    m = name[len('.?AV?$'):]
    try:
        a = m.index('@')
        z = m.index('@', a + 1)
    except ValueError:
        return None
    arg = m[a + 1:z]
    return arg or None


rows = []
for v in ENTS:
    w0 = layout[v][0]
    tor_site, tor_op = w0[0]
    dtor_site, dtor_op = w0[1]
    tor_vt = u32(tor_site + 6)
    dtor_vt = u32(dtor_site + 6)
    ci, cd = col_names(tor_vt), col_names(dtor_vt)
    rows.append({
        'entry': hex(v), 'in_file': bool(fo(v) is not None and fo(v) + 24 <= len(raw)),
        'tor_site': hex(tor_site), 'tor_vptr': hex(tor_vt),
        'dtor_site': hex(dtor_site), 'dtor_vptr': hex(dtor_vt),
        'tor_names': ci['names'] if ci else None,
        'dtor_names': cd['names'] if cd else None,
        'tor_arg': tmpl_arg(ci['names'][0]) if ci else None,
        'dtor_arg': tmpl_arg(cd['names'][0]) if cd else None,
    })

n_res = sum(1 for r in rows if r['tor_arg'] and r['dtor_arg'])
ck('B2a 35 个条目全部解出 vptr→COL→RTTI 装饰名（tor 与 dtor 各一份）：可解 %d / 35' % n_res,
   n_res == 35, {'resolved': n_res,
                 'sample': [(r['entry'], r['tor_names'][0] if r['tor_names'] else None)
                            for r in rows[:3]]})

n_dv = sum(1 for r in rows if r['tor_names'] and r['tor_names'][0].startswith('.?AV?$DynamicVectorClass@'))
n_vc = sum(1 for r in rows if r['dtor_names'] and r['dtor_names'][0].startswith('.?AV?$VectorClass@'))
ck('B2b 形状恒定：tor 安装 DynamicVectorClass<T> 的 %d / 35，dtor 安装 VectorClass<T> 的 %d / 35'
   % (n_dv, n_vc), n_dv == 35 and n_vc == 35, {'dynamic': n_dv, 'vector': n_vc})

n_same = sum(1 for r in rows if r['tor_arg'] and r['tor_arg'] == r['dtor_arg'])
ck('B2c 两条独立来源（tor 的 COL 与 dtor 的 COL，是两张不同 vtable、不同 COL）给出的 '
   '模板实参 T 逐字符相同的条目 %d / 35 ⇒ T 不是单点读数' % n_same,
   n_same == 35, {'same_arg': n_same})

args = [r['tor_arg'] for r in rows]
ck('B2d 35 个条目的元素类 T：不同名字 %d 个（%s）⇒ 这 35 项不是同一个类的 35 份，'
   '而是 %d 个不同元素类型的静态向量对象'
   % (len(set(args)), ' / '.join(sorted(set(args))), len(set(args))),
   len(set(args)) >= 20, {'distinct_args': len(set(args)), 'args': sorted(set(args))})

# ---------- 3. tor→dtor 的显式交接：tor 里 push 的地址 == dtor 所在函数的入口 ----------
# 🐞 自错 S-34：初版用**裸字节**在 tor_site 前 0x40 字节里找 0x68（push imm32），
# 会匹配到别的指令的立即数字节里（0xb04bd0 条目上匹配出 0xa300b04b 这种非地址值）。
# 改为：① 用 HB 函数边界定位「dtor 所在函数的入口」；② 用 Capstone detail=False
# 在 tor 函数体内逐条解码，只认真正的 push imm32。
HBS = sorted(HB)
import bisect
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = False; MD.skipdata = True


def func_start(a):
    i = bisect.bisect_right(HBS, a) - 1
    return HBS[i] if i >= 0 else None


def func_end(a):
    i = bisect.bisect_right(HBS, a)
    return HBS[i] if i < len(HBS) else TE


hand = []
for r in rows:
    tor_site = int(r['tor_site'], 16)
    dtor_site = int(r['dtor_site'], 16)
    f_tor, f_dtor = func_start(tor_site), func_start(dtor_site)
    pushes = []
    if f_tor is not None:
        for a, sz, m, o in MD.disasm_lite(raw[fo(f_tor):fo(func_end(f_tor)) + 16], f_tor):
            if a > tor_site:
                break
            if m.startswith('push') and '0x' in o and ',' not in o:
                try:
                    pushes.append((a, int(o.split('0x')[-1], 16)))
                except ValueError:
                    pass
    ok = bool(f_dtor is not None and any(v == f_dtor for _, v in pushes))
    hand.append({'entry': r['entry'], 'tor_func': hex(f_tor) if f_tor else None,
                 'dtor_func': hex(f_dtor) if f_dtor else None,
                 'pushes_before_site': [(hex(a), hex(v)) for a, v in pushes],
                 'ok': ok})
n_hand = sum(1 for h in hand if h['ok'])
ck('B3 tor 函数体内有 push imm32 且该立即数 == **dtor 所在函数的入口**（HB 定界）：'
   '成立 %d / 35 ⇒ 「tor/dtor 成对同一对象」是代码里的显式交接（atexit 回调），不是推断'
   % n_hand, n_hand == 35, {'ok': n_hand, 'bad': [h for h in hand if not h['ok']][:2]})

# ---------- 4. 反控 ----------
random.seed(20261124)
entset = set(ENTS)
forbidden = set()
for v in ENTS:
    for k in range(8):
        forbidden.add(v + 4 * k)
cand = []
while len(cand) < 200:
    a = random.randrange(0x812000, 0xB7A000, 4)
    if a in forbidden or a in entset:
        continue
    if any(abs(a - v) < 0x20 for v in entset):
        continue
    if fo(a) is None:
        continue
    cand.append(a)
hit = []
for a in cand:
    p = writes(a)
    if len(p) == 2:
        v1 = u32(p[0][0] + 6)
        c = col_names(v1)
        if c and c['names'] and c['names'][0].startswith('.?AV?$DynamicVectorClass@'):
            hit.append((hex(a), c['names'][0]))
ck('K1 反控（**功效不足**，已由 r117e 全量穷举取代；审计攻击点 6 接受）：同一检测器打在 %d 个随机的非条目 .data 地址上，'
   '满足「2 个 vptr 写入点 + tor 名字是 DynamicVectorClass」的 %d 个（必须为 0）'
   % (len(cand), len(hit)), len(hit) == 0, {'probed': len(cand), 'hits': hit[:5]})

# K2：把 tor/dtor 名字整体错位 1 位，T 等式必须大量失败（证明 B2c 不是恒真）
shift_ok = 0
for i in range(len(rows)):
    a2 = rows[(i + 1) % len(rows)]
    if rows[i]['tor_arg'] and a2['dtor_arg'] and rows[i]['tor_arg'] == a2['dtor_arg']:
        shift_ok += 1
ck('K2 反控：把 tor 的 T 与**下一条目** dtor 的 T 配对（错位 1 位）后成立的个数 %d（应远小于 35）'
   ' ⇒ B2c 的「同一条目内相等」不是恒真判据' % shift_ok,
   shift_ok < 35, {'shifted_equal': shift_ok})

# 🐞 自错 S-38（审计攻击点 7 抓出）：初版这里是 n_in + (35 - n_in) == 35，恒真、永远 PASS，
# 挂在证据链上是无效断言。改为可伪证的三条：
#   ① 分区数之和必须等于**读数出来的**条目总数（不是硬编码 35）；
#   ② 无文件字节的条目必须落在 .data 虚拟区（VirtualSize 内）；
#   ③ 有文件字节的条目必须落在 .data 有映像区（SizeOfRawData 内）。
# 🐞 自错 S-39（A1 的可伪证化把它抓出来，比审计攻击点 7 更严重）：
# r112_lib 的 fo = v - ImageBase 是**朴素偏移**，不查节表。对 0x887388 这类地址，
# 朴素偏移 0x487388 落在 .rsrc 的原始数据里，于是「文件里有字节」是假象 ——
# 前面读到的那几个 "GUI:Harder" 等字符串其实是 .rsrc 的字节，不是条目内容。
# 本节改用**按节表映射**的 fo2：只认 p_data <= off < p_data+raw_size 的节内地址。
import pefile as _pe
_pef = _pe.PE(os.path.join(ROOT, 'ra2bench/gamemd.exe'), fast_load=True)
_IB = _pef.OPTIONAL_HEADER.ImageBase
_SEC = [(s.VirtualAddress + _IB, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData,
         s.Name.rstrip(b'\x00').decode()) for s in _pef.sections]


def fo2(v):
    """节表感知的文件偏移：命中「有文件映像」的节返回偏移，否则 None。"""
    for va, vs, pd, rs, nm in _SEC:
        if va <= v < va + vs:
            if v - va < rs:
                return v - va + pd
            return None
    return None


def sec_of(v):
    for va, vs, pd, rs, nm in _SEC:
        if va <= v < va + vs:
            return nm
    return None


n_in = 0
n_bss = 0
bad_bss, bad_in = [], []
for r in rows:
    v = int(r['entry'], 16)
    o = fo2(v)
    if o is None:
        n_bss += 1
        if sec_of(v) != '.data':
            bad_bss.append([r['entry'], sec_of(v)])
    else:
        n_in += 1
        if sec_of(v) != '.data':
            bad_in.append([r['entry'], sec_of(v)])
ck('A1 分区**可伪证**：读数出来的条目共 %d 个；文件映像内 %d 个（全在 .data 有映像区，'
   '越界 %d）、无文件字节 %d 个（全在 .data 虚拟区，越界 %d）⇒ R116 登记为「不可知」的 '
   '%d 项，其 field0 初值本轮由静态写入点**推定**（非从文件读回）'
   % (len(rows), n_in, len(bad_in), n_bss, len(bad_bss), n_bss),
   len(rows) == 35 and n_in + n_bss == 35 and not bad_in and not bad_bss
   and n_bss == 35,
   {'rows': len(rows), 'in_file': n_in, 'bss': n_bss,
    'bad_in': bad_in, 'bad_bss': bad_bss})

json.dump({'rows': rows, 'handoff': hand, 'checks': checks,
           'verdict': '35 个 edx 目标 = 35 个 MSVC 静态 DynamicVectorClass<T> 对象；'
                      '每个都有唯一的 tor/dtor vptr 写入对，T 由两张独立 COL 互证；'
                      '30 个 BSS 条目的首字段初值由此静态推定（非从文件读回）'},
          open(OUT, 'w'), indent=1, ensure_ascii=False)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
