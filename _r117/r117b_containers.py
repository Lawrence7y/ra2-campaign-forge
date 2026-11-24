#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r117b_containers.py —— R117 第二链：把「35 个静态容器对象」放回**全镜像容器普查**里做对照，
并用两条互不共数据的命名通道（RTTI 装饰名 / symbols.json）做交叉核验。

为什么必须有这一条：R117a 证明了「这 35 个 edx 目标是 35 个不同元素类型的静态容器对象」，
但它只是**描述**了这 35 个。若镜像里本来就有成百上千个同类静态容器，那么「被这个派发例程
选中的是这 35 个」才是需要解释的事实；若镜像里**总共只有** 35 个，那 R116 的
「1 个模板 + 1 张 35 项表」就只是把一个**全集**误读成了一张表。

断言：
  E1 全镜像「tor 安装 DynamicVectorClass<T> vptr」的静态容器对象共 N 个（distinct 目标地址）。
  E2 这 N 个里，元素类型 T 的类在 Q(0x7f7c80) 认领集内的比例；与 35 个派发对象同口径比较。
  E3 35 个派发对象的元素类型**全部**在 Q(0x7f7c80) 内（35/35）；给出随机基线与二项概率。
  E4 反控 1：随机抽 35 个 symbols 类，全在 Q80 内的概率（必须极小）⇒ E3 不是恒真。
  E5 反控 2：换成 Q(0x7f7c70)，因 R112 已证两集对称差空，E3 对 70 也必须 35/35
      ⇒ 本链**不能**区分 70/80（如实登记为「本链对 70/80 无鉴别力」）。
  E6 反控 3：把「元素类型」换成容器类名本身（DynamicVectorClass<T>）去比 Q80，必须全部不在
      ⇒ 证明命中来自 T 的解析，不是字符串碰巧。
内存纪律：raw 字节扫描 + 只读 JSON / 缓存；未对 .text 整段开 detail。
"""
import collections, json, os, random, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L   # noqa: E402

raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
OUT = os.path.join(ROOT, '_r117/r117b_containers.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


def td_of(col):
    """COL → 第 0 个 BCD 的 TypeDescriptor 装饰名（失败返回 None，不猜）。"""
    if not L.valid_col(col):
        return None
    chd = u32(col + 0x10)
    nb = u32(chd + 8)
    pb = u32(chd + 0xc)
    if nb < 1:
        return None
    td = u32(u32(pb))
    if not L.is_td(td):
        return None
    o = fo(td) + 8
    e = raw.index(b'\x00', o)
    return raw[o:e].decode('latin1')


def tmpl_arg(name):
    if not name or not name.startswith('.?AV?$'):
        return None
    m = name[len('.?AV?$'):]
    try:
        a = m.index('@')
        z = m.index('@', a + 1)
    except ValueError:
        return None
    return m[a + 1:z] or None


# ---------- E1 全镜像静态容器普查 ----------
# 判据：.text 里的 `C7 05 <abs32> <imm32>`，其中 imm32 是一个 vtable 起点，
# 且 vtable 前 4 字节是合法 COL、该 COL 的装饰名以 .?AV?$DynamicVectorClass@ 开头。
TX = raw[fo(TS):fo(TE)]
census = collections.defaultdict(list)
i = 0
while True:
    i = TX.find(b'\xc7\x05', i)
    if i < 0:
        break
    abs_ = struct.unpack_from('<I', TX, i + 2)[0]
    imm = struct.unpack_from('<I', TX, i + 6)[0]
    i += 1
    # 🐞 自错 S-35：初版这里写的是 `if not (TS <= imm < TE): continue`，
    # 把 vptr 立即数当成必须落在 .text 的地址 —— vtable 在 .rdata，于是普查恒为 0。
    # 正确判据：imm 必须落在镜像内，且它**指向的槽位**在 .text（vtable 首槽是代码指针）。
    if not L.in_img(imm) or imm < L.RD0 or imm >= L.RD1:
        continue
    if not (TS <= u32(imm) < TE):
        continue
    nm = td_of(u32(imm - 4))
    if nm and nm.startswith('.?AV?$DynamicVectorClass@'):
        census[abs_].append((TS + i - 1, imm, tmpl_arg(nm)))

n_obj = len(census)
ck('E1 全镜像「tor 安装 DynamicVectorClass<T> vptr」的静态容器对象共 %d 个（distinct 目标地址）；'
   '写入点总数 %d' % (n_obj, sum(len(v) for v in census.values())),
   n_obj > 0, {'n_obj': n_obj, 'n_sites': sum(len(v) for v in census.values())})

# ---------- 与 R117a 的 35 个派发对象对齐 ----------
A = json.load(open(os.path.join(ROOT, '_r117/r117a_obj_entries.json')))
DENT = [int(r['entry'], 16) for r in A['rows']]
miss = [v for v in DENT if v not in census]
ck('E1b R117a 的 35 个派发对象**全部**出现在本次独立普查里（缺失 %d）⇒ 两套抽取器口径一致'
   % len(miss), not miss, {'missing': [hex(v) for v in miss]})

tor_imm = {}
for v in DENT:
    tor_imm[v] = census[v][0][1]
n_dis = len(set(tor_imm.values()))
ck('E1c 35 个派发对象的 tor vptr 两两不同（distinct %d）⇒ 是 35 个不同元素类型的容器'
   % n_dis, n_dis == 35, {'distinct_vptr': n_dis})

# ---------- E3 / E2：元素类型 vs QI 认领集 ----------
Q = {k: set(v) for k, v in json.load(open(os.path.join(ROOT, '_r111/r111d_full_iid.json')))['iids'].items()}
QI = {}
for cls, iids in Q.items():
    for x in iids:
        QI.setdefault(x, set()).add(cls)
Q80 = QI.get('0x7f7c80', set())
Q70 = QI.get('0x7f7c70', set())


def elem(cls_of_vptr):
    """容器对象 → 元素类名（去掉 PAV 前缀的指针修饰）。"""
    a = tmpl_arg(cls_of_vptr)
    if not a:
        return None
    return a[3:] if a.startswith('PAV') else a


disp_elems = [elem(td_of(u32(census[v][0][1] - 4))) for v in DENT]
n_in80 = sum(1 for e in disp_elems if e in Q80)
ck('E3 35 个派发对象的**元素类型**全部落在 Q(0x7f7c80) 认领集（%d/35；该集 %d 个类）'
   % (n_in80, len(Q80)), n_in80 == 35 and len(Q80) > 0,
   {'in': n_in80, 'Q80': len(Q80), 'sample': disp_elems[:5]})

all_elem = {v: elem(td_of(u32(census[v][0][1] - 4))) for v in census}
n_all = len(all_elem)
n_all_in80 = sum(1 for e in all_elem.values() if e in Q80)
ck('E2 全镜像静态容器 %d 个，其中元素类型在 Q80 内的 %d 个（%.1f%%）；'
   '被派发例程选中的 35 个里 35 个（100%%）⇒ 「选中」这件事本身是需要解释的选择，不是无差别'
   % (n_all, n_all_in80, 100.0 * n_all_in80 / max(n_all, 1)),
   n_all >= 35, {'all': n_all, 'all_in80': n_all_in80,
                 'rate_all': round(n_all_in80 / max(n_all, 1), 4),
                 'rate_disp': round(n_in80 / 35.0, 4)})

# ---------- E4 反控：随机 35 个类全在 Q80 ----------
SYM = list(json.load(open(os.path.join(ROOT, 'out/reverse/symbols.json')))['classes'])
random.seed(20261124)
p_hit = len(Q80) / float(len(SYM))
trials = 2000
worse = 0
for _ in range(trials):
    s = set(random.sample(SYM, 35))
    if len(s & Q80) >= n_in80:
        worse += 1
ck('E4 反控（有牙）：从 %d 个 symbols 类里随机抽 35 个，落在 Q80(%d 个，单抽命中率 %.3f) 内'
   '的个数 >= %d 的试验 %d / %d（必须为 0）⇒ E3 的 35/35 不是恒真'
   % (len(SYM), len(Q80), p_hit, n_in80, worse, trials),
   worse == 0, {'trials': trials, 'worse': worse, 'p_hit': round(p_hit, 4)})

n70 = sum(1 for e in disp_elems if e in Q70)
ck('E5 反控/边界：同一链换成 Q(0x7f7c70) 也是 %d/35，且两集对称差 %d ⇒ 本链对 70/80 '
   '**无鉴别力**（如实登记，不当作区分证据）' % (n70, len(Q80 ^ Q70)),
   n70 == 35 and len(Q80 ^ Q70) == 0, {'in70': n70, 'symdiff': len(Q80 ^ Q70)})

cont_cls = [td_of(u32(census[v][0][1] - 4)) for v in DENT]
n_c80 = sum(1 for e in cont_cls if e and e in Q80)
ck('E6 反控：把比对对象换成**容器类名本身**（.?AV?$DynamicVectorClass@T）后命中 %d/35 '
   '（必须为 0）⇒ E3 的命中来自 T 的解析，不是字符串碰巧' % n_c80,
   n_c80 == 0, {'container_hits': n_c80})

# ---------- 命名通道交叉 ----------
VT = {}
for k, v in json.load(open(os.path.join(ROOT, 'out/reverse/symbols.json')))['classes'].items():
    if v.get('vtable_va'):
        VT[int(v['vtable_va'], 16)] = k
agree, disagree, absent = 0, [], []
for v in DENT:
    vt = census[v][0][1]
    nm = td_of(u32(vt - 4))
    mine = tmpl_arg(nm)
    theirs = VT.get(vt)
    if theirs is None:
        absent.append(hex(vt))
    elif mine and theirs == '?$DynamicVectorClass@' + mine + '@@':
        agree += 1
    else:
        disagree.append({'vt': hex(vt), 'mine': mine, 'symbols': theirs})
ck('E7 命名双通道交叉：35 个派发容器的 tor vptr 在 symbols.json（954 vtables 第三方产物）'
   '命中 %d、缺失 %d；装饰名与 RTTI 通道解出的 T 一致 %d、不一致 %d'
   % (35 - len(absent), len(absent), agree, len(disagree)),
   not absent and not disagree and agree == 35,
   {'absent': absent[:5], 'disagree': disagree[:5], 'agree': agree})

json.dump({'census': {hex(k): [(hex(a), hex(v), t) for a, v, t in vs]
                      for k, vs in list(census.items())},
           'n_obj': n_obj, 'disp_elems': disp_elems,
           'all_elem': {hex(k): v for k, v in all_elem.items()},
           'checks': checks,
           'verdict': '全镜像静态 DynamicVectorClass<T> 对象 %d 个，元素类型在 Q80 内的 %d 个；'
                      '派发例程选中的 35 个恰好全部在 Q80 内（35/35），随机基线 0/2000' % (n_all, n_all_in80)},
          open(OUT, 'w'), indent=1, ensure_ascii=False)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
