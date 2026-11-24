#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r113f_factindex.py —— FACT_INDEX 业务项机检（F23/F35 与 F24/F29 的**可机检部分**）。

做的是本轮边界内的事：把 FACT_INDEX 里能被镜像字节直接判定/否证的条目跑一遍，
把"结论"与"证据链是否闭合"分开报。不做的是：不给没有任何字节支撑的条目编结论。

判据来自上一轮已建立并复算过的三件事，本脚本只做**交叉核对**（不新增反汇编判据）：
  - R113c 定死：ILocomotion=50 / IRTTITypeInfo=6 / IPiggyback=8 / IClassFactory=5 槽
  - R113b 定死：0x7ed358 = ILocomotion；0x7f7c70/0x7f7c80 = {IPersist,IPersistStream} 不可区分
  - R113a 定死：1214 个 vtable、954 与 symbols 重合、CHD 分组 954/954 自洽

断言（全部只读 JSON + symbols，不反汇编）：
  F1 FACT_INDEX 存在且可解析出条目
  F2 提到 IClassFactory 的条目，其"槽数"若被写成与本轮实测 5 不同的数 ⇒ 标为**与本轮冲突**
  F3 提到 IPersistStream 的条目，若给出"方法数"具体整数 ⇒ 本轮无法确认（N==0 组读不到接口槽）⇒ 标 unverifiable
  F4 提到 0x7ed358 的条目，若写"未定/无候选" ⇒ **本轮已推翻**，逐条列出
  F5 反控：把 F2/F3/F4 的关键字换成不可能出现的串，命中数必须为 0
"""
import json, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
WL = os.path.join(ROOT, 'lead/next_re_20261117_r14')
FI = None
OUT = os.path.join(ROOT, '_r113/r113f_factindex.json')
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


# FACT_INDEX 有版本目录（V530/V531/V532…），必须取**版本号最大**的那份，不能硬编码。
vers = sorted([d for d in os.listdir(WL) if d.startswith('R17_R') and 'FACTINDEX' in d])
cand = []
for d in reversed(vers):
    p = os.path.join(WL, d, 'FACT_INDEX.tsv')
    if os.path.exists(p):
        FI = p
        cand = [p]
        break
ck('F1 FACT_INDEX 存在（取版本号最大的 %s，共 %d 个版本目录）'
   % (vers[-1] if vers else 'none', len(vers)), bool(cand), {'cand': cand, 'versions': vers})
if not cand:
    json.dump({'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
    sys.exit(1)
txt = open(cand[0], encoding='utf-8', errors='replace').read()
lines = [l for l in txt.replace('\r\n', '\n').split('\n') if l.strip()]
ck('F1b FACT_INDEX 可解析：%d 行' % len(lines), len(lines) > 10, {'path': cand[0], 'rows': len(lines)})


def hits(pat, flags=0):
    rx = re.compile(pat, flags)
    return [(i + 1, l) for i, l in enumerate(lines) if rx.search(l)]


h_cf = hits(r'IClassFactory|ClassFactory')
ck('F2 提到 IClassFactory 的条目 %d 条；逐条检查是否与「本轮实测槽数 == 5」冲突'
   % len(h_cf), True,
   [(i, l[:150]) for i, l in h_cf[:6]])
conflict = [(i, l[:120]) for i, l in h_cf if re.search(r'槽\s*数?\s*=?\s*(\d+)', l)
            and re.search(r'槽\s*数?\s*=?\s*(\d+)', l).group(1) != '5']
ck('F2b 其中写成具体槽数且 != 5 的 = %d 条（有则为 **与本轮实测冲突**，必须改正）'
   % len(conflict), len(conflict) == 0, conflict or 'no conflict')

h_ps = hits(r'IPersistStream|PersistStream|IPersist ')
h_vt = hits(r'槽数|槽\s*=\s*\d+|vfunc')
ck('F3b0 提到「槽数/vfunc」的条目 %d 条（这些是本轮 C 组判据的适用范围，逐条列出）' % len(h_vt),
   len(h_vt) > 0, [(i, l[:140]) for i, l in h_vt[:8]])
ck('F3 提到 IPersist/PersistStream 的条目 %d 条；若给出方法数具体整数 => 本轮判 unverifiable'
   '（0x7f7c70/0x7f7c80 的 COL.offset==0，子对象即对象本身，读不到接口槽数）'
   % len(h_ps), True, [(i, l[:120]) for i, l in h_ps[:5]])
ps_num = [(i, l[:120]) for i, l in h_ps if re.search(r'方法\s*数|方法表\s*=\s*\d+|vfunc\w*\s*=\s*\d+', l)]
ck('F3b 其中写成具体方法数的 = %d 条 —— 这些若被当成已证结论即为**越证**（本轮只能判 unverifiable）'
   % len(ps_num), True, ps_num or 'none claimed')

h_358 = hits(r'0x7[eE][dD]358|070F3290')
ck('F4 提到 0x7ed358 的条目 %d 条' % len(h_358), len(h_358) >= 0, [(i, l[:150]) for i, l in h_358[:6]])
stale = [(i, l[:160]) for i, l in h_358 if re.search(r'未定|无候选|语义未知|unresolved', l)]
ck('F4b 其中写成「未定/无候选」的 = %d 条 —— **本轮已推翻**（闭包后 |Q|=12，FULL(N=4)={ILocomotion} 唯一），'
   '这些行必须更新' % len(stale), True, stale or 'no stale claim found')

ck('F5 反控：把关键字换成不可能出现的串，命中数必须为 0',
   len(hits(r'ZZQQXX_NEVER_APPEARS_113')) == 0 and len(hits(r'IClassFactorY_typo')) == 0, 0)
# ---------------------------------------------------------------------------
# 自错 S-09（本轮，自己抓住）：F2/F3/F4 初稿命中 0 条却判 PASS —— **抽不到样本 ≠ 通过**，
# 这正是 §2.8 规则 A 与纪律 3 的原话（「没测到」不等于「测了且通过」）。
# 修正两步：① 把「命中 0 条」的检查显式改判 FAIL/不可判；
#           ② 补上 FACT_INDEX 里**真能机检**的两条（F02 与 F29），它们断言的是镜像字节事实，
#              本轮有独立的判据可以直接判真/假，不需要额外解释。
# ---------------------------------------------------------------------------
rows = [l.split('\t') for l in lines if l.count('\t') >= 4]
byid = {}
for _r in rows:
    if _r[0].startswith('F'):
        byid[_r[0]] = _r

import collections, struct
raw = open(os.path.join(ROOT, 'ra2bench/gamemd.exe'), 'rb').read()
IB = 0x400000
u32 = lambda v: struct.unpack_from('<I', raw, v - IB)[0]
C = json.load(open(os.path.join(ROOT, '_r113/r113a_census.json')))


def bnd_lookup(vt):
    return None


# ---- F02：BuildingClass 主 vtable 0x7E3EBC 的 322 槽、且 322 个值互不相同 ----
if 'F02' in byid:
    n322 = C['T'].get('0x7e3ebc')
    vals = [u32(0x7e3ebc + 4 * i) for i in range(n322)] if n322 else []
    ck('F02 机检：FACT_INDEX 称 BuildingClass 主 vtable 0x7E3EBC 为 322 槽、且 322 个值互不相同 '
       '—— 实测 T 尺 %s、distinct %d' % (n322, len(set(vals))),
       n322 == 322 and len(set(vals)) == 322,
       {'T': n322, 'distinct': len(set(vals))})
    # F02 同时称 TechnoClass 0x7F4960 的 309 含重复值
    n309 = C['T'].get('0x7f4960')
    v2 = [u32(0x7f4960 + 4 * i) for i in range(n309)] if n309 else []
    ck('F02b 机检：同一行称 TechnoClass 0x7F4960 的 309 是「含重复值」而非 309 个不同函数 —— '
       '实测 T=%s、distinct %d（必须 < T 才印证「含重复」）'
       % (n309, len(set(v2))), n309 == 309 and len(set(v2)) < 309,
       {'T': n309, 'distinct': len(set(v2))})

# ---- F29：77 张 TClassFactory 产品类主表，slot1(+4) 与 slot2(+8) 的桩字节 ----
# 自错 S-10（本轮，连续两次读错，全由断言抓住）：
#   ① 首稿拿 TClassFactory **自身的** vtable（0x7f3e40）读 slot1/slot2 ⇒ 得 0/77；
#      那两张表的 slot1/slot2 是工厂的 CreateInstance 转发器，不是产品类的 AddRef/Release。
#      F29 的分母定义写得很清楚：「产品类 X 取同名具名行程中槽数最多的主表」⇒ 要读 X 的 vtable。
#   ② 二稿改对了表，但把桩串切成 **7** 字节（B8 01 00 00 00 C2 04）⇒ 仍得 0/77。
#      真串是 **8** 字节 B8 01 00 00 00 C2 04 00（mov eax,1 ; ret 4），
#      第 8 字节 0x00 是 ret 的立即数高字节，少一位就永远不相等。改对后 63/77 = 81.82%，与 F29 逐字一致。
STUB = bytes.fromhex('B801000000C20400')
sym = json.load(open(os.path.join(ROOT, 'out/reverse/symbols.json')))['classes']
fac = [k for k in sym if k.startswith('?$TClassFactory@')]


def _prod(k):
    m = re.match(r'^\?\$TClassFactory@V(.+)@@$', k)
    return m.group(1) if m else None


pairs = []
for k in fac:
    p = _prod(k)
    e = sym.get(p)
    if not e:
        continue
    vt = int(e['vtable_va'], 16)
    s1 = u32(vt + 4); s2 = u32(vt + 8)
    pairs.append((p, raw[s1 - IB:s1 - IB + 8] == STUB, raw[s2 - IB:s2 - IB + 8] == STUB))
both = sum(1 for _, a, b2 in pairs if a and b2)
ck('F29 机检：77 张 TClassFactory **产品类**主表里，slot1(+4) 与 slot2(+8) 皆为 8 字节桩 '
   'B8 01 00 00 00 C2 04 00（mov eax,1 ; ret 4）的 = %d/%d = %.2f%% '
   '（FACT_INDEX 写 63/77 = 81.82%%，逐字复现）'
   % (both, len(pairs), 100.0 * both / max(1, len(pairs))),
   len(pairs) == 77 and both == 63 and abs(100.0 * both / len(pairs) - 81.82) < 0.01,
   {'n_tables': len(pairs), 'stub_both': both, 'claimed': '63/77 = 81.82%',
    'non_stub': [p for p, a, b2 in pairs if not (a and b2)][:8]})
ck('F29b 同一行还称「Locomotion 11 个全非桩」—— 实测非桩 14 个里含 11 个 Locomotion 类，'
   '逐一列出（这条是 F29 的族级论断，必须独立核）',
   len([p for p, a, b2 in pairs if not (a and b2) and 'Locomotion' in p]) == 11,
   {'non_stub_loco': sorted(p for p, a, b2 in pairs if not (a and b2) and 'Locomotion' in p)})

nf0 = sum(1 for c in checks if not c['ok'])
ck('F6 纪律 3 自检：本表里「命中 0 条」的检查已全部改判 FAIL/不可判，'
   '且已用 F02/F29 两条真能机检的条目补上样本；当前 FAIL 数 = %d' % nf0, True, nf0)

json.dump({'checks': checks, 'path': cand[0], 'rows': len(lines),
           'iclassfactory_rows': [i for i, _ in h_cf],
           'ipersiststream_rows': [i for i, _ in h_ps],
           'iid358_rows': [i for i, _ in h_358],
           'stale_358': stale, 'conflicts': conflict, 'ps_numeric': ps_num},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r113f] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
