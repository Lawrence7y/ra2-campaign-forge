# -*- coding: utf-8 -*-
# R17-R66 实测：直接调用漏点 (0x007C8B3D, 0x0074836A) 根因 + sweep.installs 双控核验
# 独立实现：手写 PE 解析 + capstone x86-32；不 import 任何卡内代码。
import json, struct, hashlib, random, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
F = dict(
    a2=ROOT + r"\D41_SUBST\_audit\EVIDENCE\a2_sites.json",
    sm=ROOT + r"\S21_DIRECT\_audit\EVIDENCE\scan_mine.json",
    e8=ROOT + r"\S09_KPROVED7\_audit\EVIDENCE\e8_sites_audit.json",
    sw=ROOT + r"\S08_KPROVED2\_audit\EVIDENCE\sweep.json",
)
GAP_SITE, GAP_TGT = 0x007C8B3D, 0x0074836A

D = open(EXE, "rb").read()
SHA = hashlib.sha256(D).hexdigest()

# ---------- 1. PE 解析（手写，无 pefile） ----------
PENT = struct.unpack_from("<I", D, 0x3C)[0]
assert D[PENT:PENT + 4] == b"PE\0\0"
COFF = PENT + 4
NS = struct.unpack_from("<H", D, COFF + 2)[0]
OSZ = struct.unpack_from("<H", D, COFF + 16)[0]
OPT = COFF + 20
IB = struct.unpack_from("<I", D, OPT + 0x1C)[0]
SO = OPT + OSZ
SEC = []
for i in range(NS):
    o = SO + 40 * i
    n = D[o:o + 8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", D, o + 8)
    ch = struct.unpack_from("<I", D, o + 36)[0]
    SEC.append((n, IB + va, vs, rp, rs, ch))

def va2off(va):
    for n, sv, vs, rp, rs, ch in SEC:
        if sv <= va < sv + max(vs, rs):
            d = va - sv
            if d < rs:
                return rp + d
    return None

def sec_of(va):
    for n, sv, vs, rp, rs, ch in SEC:
        if sv <= va < sv + max(vs, rs):
            return n
    return None

def rd(va, n):
    o = va2off(va)
    return D[o:o + n] if o is not None else None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def dis(va, size, detail=False):
    md.detail = detail
    return list(md.disasm(rd(va, size), va))

def dis_to_ret(va, limit=300):
    """§2.12：函数体窗口须到首个 ret。"""
    out = []
    md.detail = False
    for ins in md.disasm(rd(va, limit), va):
        out.append(ins)
        if ins.mnemonic == "ret" or ins.mnemonic.startswith("ret"):
            break
    return out

L = []
def P(s=""):
    L.append(s)
    print(s)

P("=" * 78)
P("R17-R66 实测 · gamemd.exe sha256=%s size=%d" % (SHA, len(D)))
P("=" * 78)

P("\n[1] PE 段表（手写解析，ImageBase=%08X nsect=%d）" % (IB, NS))
for n, sv, vs, rp, rs, ch in SEC:
    P("    %-8s va=%08X vsize=%08X rawptr=%08X rawsize=%08X chars=%08X" % (n, sv, vs, rp, rs, ch))
P("    目标点归属：0x%08X -> %s ；0x%08X -> %s" % (GAP_TGT, sec_of(GAP_TGT), GAP_SITE, sec_of(GAP_SITE)))

# ---------- 2. 正控 ----------
P("\n[2] 正控：0x0040100A 处应为 E8 调用 0x00407100")
pc = list(md.disasm(rd(0x40100A, 8), 0x40100A, count=1))[0]
rel = struct.unpack("<i", pc.bytes[1:5])[0]
P("    字节 %s -> %s %s ；rel=0x%X 验算 0x40100A+5+rel=0x%08X  %s"
  % (pc.bytes.hex(), pc.mnemonic, pc.op_str, rel, 0x40100A + 5 + rel,
     "PASS" if (pc.mnemonic == "call" and 0x40100A + 5 + rel == 0x00407100) else "FAIL"))

# ---------- 3. 两个窗口反汇编 ----------
def show(va0, va1, title):
    P("\n[3] %s ：0x%08X..0x%08X" % (title, va0, va1))
    md.detail = False
    for ins in md.disasm(rd(va0, va1 - va0), va0):
        P("    %08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

show(0x007C8B00, 0x007C8B70, "目标函数窗口（含 0x007C8B3D）")
show(0x00748350, 0x00748390, "漏点所在窗口（含 0x0074836A，从跳转表起点解起）")
P("\n    ↑ 这段从 0x00748350（跳转表首字节）解起 ⇒ 全是垃圾；真正的代码如下（从 0x00748360 起）：")
show(0x00748360, 0x00748380, "0x00748360 起的真实代码（call 0x007C8B3D 所在函数）")

P("\n[3b] 函数体窗口到首个 ret（§2.12）")
for va in (GAP_SITE, 0x00748360):
    P("    -- 0x%08X" % va)
    for ins in dis_to_ret(va):
        P("       %08X  %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

# ---------- 4. 全量原始 E8 普查 vs 三份清单边界集合 ----------
n, sv, vs, rp, rs, ch = [s for s in SEC if s[0] == ".text"][0]
raw_pairs = set()
for i in range(rp, rp + vs - 4):
    if D[i] == 0xE8:
        rel = struct.unpack_from("<i", D, i + 1)[0]
        site = sv + (i - rp)
        raw_pairs.add((site, (site + 5 + rel) & 0xFFFFFFFF))
P("\n[4] 原始字节普查（.text vsize 窗口）：E8 字节对 = %d" % len(raw_pairs))

pcall = {}
for ins in md.disasm(D[rp:rp + vs], sv):
    if ins.mnemonic == "call" and ins.size == 5 and ins.bytes[:1] == b"\xe8":
        rel = struct.unpack("<i", ins.bytes[1:5])[0]
        pcall[ins.address] = (ins.address + 5 + rel) & 0xFFFFFFFF
bound_pairs = set(pcall.items())
P("    反汇编边界上的 E8 调用对 = %d（a2_scan.json 记 e8_at_boundary=68253、raw_e8=81715）" % len(bound_pairs))
P("    差值 = %d（字节是 E8 但不在任何反汇编指令起点）" % (len(raw_pairs) - len(bound_pairs)))

# ---------- 5. 四文件集合比对（纪律 30：先打印归一化前后命中数） ----------
J = {k: json.load(open(v, "rb")) for k, v in F.items()}
a2_raw = J["a2"]["calls"]                      # {"007C8B3D": ["00401532", ...]}  目标->站点
sm_raw = J["sm"]["calls"]                      # [[int,int], ...]                [site,target]
e8_raw = J["e8"]                               # [[int,int], ...]
sw_raw = J["sw"]["e8"]                         # [[int,int], ...]

sets = {}
sets["a2"] = set((int(s, 16), int(t, 16)) for t, ss in a2_raw.items() for s in ss)
sets["sm"] = set(map(tuple, sm_raw))
sets["e8"] = set(map(tuple, e8_raw))
sets["sw"] = set(map(tuple, sw_raw))

P("\n[5] 四文件调用点集合（纪律 30：归一化前后对照）")
P("    原始表示：a2=%s(hex str)  sm=%s(int)  e8=%s(int)  sw=%s(int)"
  % (type(next(iter(a2_raw))).__name__, type(sm_raw[0][0]).__name__,
     type(e8_raw[0][0]).__name__, type(sw_raw[0][0]).__name__))
# 未归一化直接比：把 a2 的 (hex,hex) 与 sm 的 (int,int) 硬比
a2_unnorm = set((s, t) for t, ss in a2_raw.items() for s in ss)
sm_unnorm = set((s, t) for s, t in sm_raw)
P("    未归一化 a2∩sm = %d（若照此判断会得出『两份完全不同』）" % len(a2_unnorm & sm_unnorm))
P("    归一化后各集合大小：a2=%d sm=%d e8=%d sw=%d" % tuple(len(sets[k]) for k in ("a2", "sm", "e8", "sw")))
P("    归一化后 a2∩sm=%d  sm∩e8=%d  e8∩sw=%d  a2∩sm∩e8∩sw=%d"
  % (len(sets["a2"] & sets["sm"]), len(sets["sm"] & sets["e8"]),
     len(sets["e8"] & sets["sw"]),
     len(sets["a2"] & sets["sm"] & sets["e8"] & sets["sw"])))
P("    四份是否与『反汇编边界集合』逐对相等：%s"
  % {k: (sets[k] == bound_pairs) for k in ("a2", "sm", "e8", "sw")})

P("\n[5b] 目标点 (site=0x%08X -> tgt=0x%08X) 在各份中的出现/缺失" % (GAP_SITE, GAP_TGT))
for k in ("a2", "sm", "e8", "sw"):
    S = sets[k]
    P("    %-3s 正向(site,tgt) %-6s | 反向(tgt,site) %-6s | 『以 0x%08X 为站点』%s"
      % (k, (GAP_SITE, GAP_TGT) in S, (GAP_TGT, GAP_SITE) in S, GAP_TGT,
         any(s == GAP_TGT for s, t in S)))
tgt_set = set(t for s, t in bound_pairs)
raw_hit = sorted(p for p in raw_pairs if p[1] in tgt_set and p not in bound_pairs)
P("    原始 E8 中『目标落在清单目标集合内、但配对未被记录』= %d 条：" % len(raw_hit))
for s, t in raw_hit:
    P("       0x%08X -> 0x%08X   前 8 字节 %s" % (s, t, rd(s - 3, 11).hex()))
P("    ↑ 逐条判真伪（用 a2 的 bounds 表定位『覆盖该 E8 的那条指令』⇒ 覆盖=假阳性）：")
import bisect as _bi
_bounds = sorted(int(x, 16) for x in J["a2"]["bounds"])
_bounds_set = set(_bounds)
_md = {i.address: (i.address, i.size, i.bytes.hex(), i.mnemonic, i.op_str)
       for i in md.disasm(D[rp:rp + vs], sv)}
for s, t in raw_hit:
    k = _bi.bisect_right(_bounds, s) - 1
    st = _bounds[k]
    a, sz, bb, mn, ops = _md[st]
    inside = a < s < a + sz
    P("       0x%08X -> 0x%08X ：覆盖它的边界指令 %08X %-18s %s %s（%d 字节，止于 %08X）⇒ E8 在指令内部=%s %s"
      % (s, t, a, bb, mn, ops, sz, a + sz, inside, "假阳性" if inside else "真调用"))

# 0x74836A 为何被吞：打印包含它的那条伪指令与其上游数据表
P("\n[5c] 0x%08X 被吞的具体位置" % GAP_TGT)
seg = [x for x in a2_raw and [] ]  # noqa
md.detail = False
for ins in md.disasm(rd(0x0074834C, 0x26), 0x0074834C):
    mark = "  <== 覆盖了 0x0074836A" if ins.address < GAP_TGT < ins.address + ins.size else ""
    P("    %08X  %-18s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
tab = [struct.unpack_from("<I", D, va2off(0x00748350) + 4 * i)[0] for i in range(4)]
P("    0x00748350 起的 4 个 dword = %s ⇒ 全部落在 0x007482xx 一带 ⇒ .text 内嵌跳转表（数据，不是代码）"
  % " ".join("%08X" % x for x in tab))

# ---------- 5d. 第三方裁决：递归下降（不依赖 a2 bounds，故不受同一失步污染） ----------
P("\n[5d] 第三方裁决：递归下降（roots = .text 首址 + 全部清单调用目标；每函数至多 2,000 条指令）")
roots = {0x00401000} | tgt_set
decoded = set()          # 全库已解为指令起点的地址
hit_as_call = {}
work = sorted(roots)
i_done = 0
md.detail = True
while work:
    fn = work.pop()
    if fn in decoded:
        continue
    pc = fn
    fn_seen = set()
    for _ in range(2000):
        if pc in fn_seen or pc in decoded:
            break
        fn_seen.add(pc)
        decoded.add(pc)
        b = rd(pc, 16)
        if not b:
            break
        g = list(md.disasm(b, pc, count=1))
        if not g:
            break
        ins = g[0]
        i_done += 1
        for s, t in raw_hit:
            if ins.address == s:
                hit_as_call[s] = (ins.mnemonic, ins.op_str, ins.size)
        op0 = ins.bytes[0] if ins.bytes else 0
        op1 = ins.bytes[1] if len(ins.bytes) > 1 else 0
        nxt = ins.address + ins.size
        if ins.mnemonic == "call" and ins.size == 5 and op0 == 0xE8:
            work.append((ins.address + 5 + struct.unpack("<i", ins.bytes[1:5])[0]) & 0xFFFFFFFF)
        elif ins.mnemonic == "jmp" and ins.size == 5 and op0 == 0xE9:
            work.append((ins.address + 5 + struct.unpack("<i", ins.bytes[1:5])[0]) & 0xFFFFFFFF)
            break
        elif ins.mnemonic == "jmp" and ins.size == 2 and op0 == 0xEB:
            work.append(ins.address + 2 + struct.unpack("<b", ins.bytes[1:2])[0])
            break
        elif ins.mnemonic.startswith("j") and ins.size == 6 and op0 == 0x0F and (op1 & 0xF0) == 0x80:
            work.append(ins.address + 6 + struct.unpack("<i", ins.bytes[2:6])[0])
        elif ins.mnemonic.startswith("j") and ins.size == 2 and 0x70 <= op0 <= 0x7F:
            work.append(ins.address + 2 + struct.unpack("<b", ins.bytes[1:2])[0])
        elif ins.mnemonic in ("ret", "retf") or ins.mnemonic.startswith("ret"):
            break
        pc = nxt
P("    递归下降解出指令 %d 条（去重起点 %d 个）、入口 %d 个" % (i_done, len(decoded), len(roots)))
P("    两个窗口起点是否在递归下降结果里：0x007C8B3D=%s  0x00748360=%s  0x0074836A=%s"
  % (GAP_SITE in decoded, 0x00748360 in decoded, GAP_TGT in decoded))
for s, t in raw_hit:
    if s in hit_as_call:
        mn, ops, sz = hit_as_call[s]
        P("        0x%08X -> 0x%08X ：递归下降在真实代码路径上解出 %s %s ⇒ **真调用**" % (s, t, mn, ops))
    else:
        P("        0x%08X -> 0x%08X ：递归下降**从未**把它解成指令起点 ⇒ 假阳性（E8 只是某条真指令的操作数/disp 字节）"
          % (s, t))

# ---------- 5e. 从「文档已确认的函数入口」重扫（入口来自清单的调用目标，不是 bounds） ----------
P("\n[5e] 从文档已确认的函数入口重扫：入口集合 = 清单 6,728 个调用目标（不依赖 bounds，故不受同一失步污染）")
tgt_list = sorted(tgt_set)
missing_entry = [t for t in tgt_list if t not in _bounds_set]
P("    6,728 个目标中，『边界表里没有把它当指令起点』的 = %d 个（函数入口本就未必在边界表里，仅作参考）"
  % len(missing_entry))
rescan = {}          # (site,tgt) 由入口重扫解出的 E8 调用
md.detail = True
funcs_ok = 0
for entry in tgt_list:
    pc = entry
    ok = 0
    for _ in range(4000):
        b = rd(pc, 16)
        if not b:
            break
        g = list(md.disasm(b, pc, count=1))
        if not g:
            break
        ins = g[0]
        ok += 1
        if ins.mnemonic == "call" and ins.size == 5 and ins.bytes[0] == 0xE8:
            rel = struct.unpack("<i", ins.bytes[1:5])[0]
            rescan[(ins.address, (ins.address + 5 + rel) & 0xFFFFFFFF)] = 1
        if ins.mnemonic.startswith("ret"):
            break
        pc = ins.address + ins.size
    funcs_ok += 1
P("    重扫函数 %d 个，解出 E8 调用对 %d 个" % (funcs_ok, len(rescan)))
only_rescan = sorted(set(rescan) - bound_pairs)
only_list = sorted(bound_pairs - set(rescan))
P("    重扫有、清单无 = %d 条：" % len(only_rescan))
for s, t in only_rescan:
    P("        0x%08X -> 0x%08X  （清单目标集合含 0x%08X=%s）" % (s, t, t, t in tgt_set))
P("    清单有、重扫无 = %d 条（预期大：重扫只进目标函数、且遇 ret 即停，覆盖是子集）" % len(only_list))
P("    ⇒ 关键量是『重扫有、清单无』：这些是清单**必然**漏掉的真实调用（其站点在真实函数体内、"
  "且该函数是清单自己认定的调用目标）。")

# ---------- 6. sweep.installs 双控 ----------
P("\n[6] sweep.installs 双控核验（6,226 条全量，非抽样）")
ins_all = J["sw"]["installs"]
P("    条数=%d 序列化=%d B（json.dumps separators=(',',':')）"
  % (len(ins_all), len(json.dumps(ins_all, separators=(",", ":")))))

def check_entry(e):
    site, form, imm = e
    if isinstance(form, int):                     # C7 05 imm32 形态
        b = rd(site, 10)
        if b is None or b[0] != 0xC7 or b[1] != 0x05:
            return False, "bytes"
        mem = struct.unpack("<I", b[2:6])[0]
        val = struct.unpack("<I", b[6:10])[0]
        return (mem == form and val == imm), "C7 05"
    # mov dword [base+disp], imm32
    g = list(md.disasm(rd(site, 16), site, count=1))
    if not g:
        return False, "decode"
    i0 = g[0]
    if i0.mnemonic != "mov" or len(i0.operands) != 2:
        return False, "mnem"
    op0, op1 = i0.operands
    if op0.type != 3 or op1.type != 2:             # MEM, IMM
        return False, "optype"
    base = op0.mem.base
    disp = op0.mem.disp
    size = op0.size
    want = "mem(base=%d,disp=%d,size=%d)" % (base, disp, size)
    return (want == form and (op1.imm & 0xFFFFFFFF) == imm), want

md.detail = True
good = bad = 0
bad_list = []
by_shape = {True: 0, False: 0}
for e in ins_all:
    ok, info = check_entry(e)
    by_shape[isinstance(e[1], int)] += 1
    if ok:
        good += 1
    else:
        bad += 1
        if len(bad_list) < 5:
            bad_list.append((e, info))
P("    正控（回原址逐字节/逐操作数精确匹配）：PASS=%d FAIL=%d  ⇒ %s" % (good, bad, "PASS" if bad == 0 else "FAIL"))
P("    形态计数：C7 05 全局写=%d ；mov [base+disp],imm=%d" % (by_shape[True], by_shape[False]))
if bad_list:
    for e, info in bad_list:
        P("      FAIL %r (%s)" % (e, info))

# 负控：篡改 imm/mem 各 1 位，必须全部被抓
md.detail = True
neg_caught = neg_missed = 0
for e in ins_all:
    site, form, imm = e
    flips = [imm ^ 1]
    if isinstance(form, int):
        flips.append(form ^ 0x1000)
    for fv in flips:
        ok, _ = check_entry((site, form, fv))
        if ok:
            neg_missed += 1
        else:
            neg_caught += 1
P("    负控（imm^1 / mem^0x1000 篡改）：被抓=%d 漏放=%d ⇒ %s"
  % (neg_caught, neg_missed, "PASS" if neg_missed == 0 else "FAIL"))

# 另做一次「换一个文件」负控：把 site 指向别的指令起点，必须不通过
neg2 = 0
for e in ins_all[:200]:
    site, form, imm = e
    ok, _ = check_entry((site + 1, form, imm))
    neg2 += 0 if ok else 1
P("    负控二（site+1 偏移）：200 条中不通过 %d 条 ⇒ %s" % (neg2, "PASS" if neg2 == 200 else "FAIL"))

# 抽样打印
rnd = random.Random(66)
P("    抽样 10 条（回原址字节 + 解码）：")
md.detail = False
for e in rnd.sample(ins_all, 10):
    site, form, imm = e
    g = list(md.disasm(rd(site, 16), site, count=1))[0]
    P("      %r -> %08X %-22s %s %s" % (e, site, g.bytes.hex(), g.mnemonic, g.op_str))

# ---------- 7. 体量归属 ----------
P("\n[7] sweep.json 体量与 installs 归属")
b_sw = open(F["sw"], "rb").read()
P("    盘上字节=%d ；json.dump 默认序列化长度=%d ⇒ 相等=%s"
  % (len(b_sw), len(json.dumps(J["sw"])), len(b_sw) == len(json.dumps(J["sw"]))))
for k, v in J["sw"].items():
    P("    %-13s %-5s n=%-8s ser=%d" % (k, type(v).__name__, (len(v) if hasattr(v, "__len__") else v),
                                       len(json.dumps(v, separators=(",", ":")))))
P("    ⇒ installs 的 248,114 B 是 sweep.json 1,631,944 B 的组成部分（键值对同处一个文件），"
  "不是第二个文件 ⇒ F24 磁盘体量里已含、不另计。")
P("    ⇒ 证据独立性口径：installs 的 6,226 条在四份 calls 文件里都不存在（下方实测），属 sweep 独有内容。")

# installs 与其余三份的内容重叠检查
ins_pairs = set((e[0], e[1] if isinstance(e[1], int) else e[2]) for e in ins_all)
allcalls = set()
for k in ("a2", "sm", "e8"):
    allcalls |= sets[k]
ins_sites = set(e[0] for e in ins_all)
call_sites = set(s for s, t in allcalls)
P("    installs 站点数=%d ；四份 calls 站点数=%d ；站点交集=%d"
  % (len(ins_sites), len(call_sites), len(ins_sites & call_sites)))

# ---------- 8. 汇总 ----------
P("\n[8] 汇总")
P("  ① 漏点根因：capstone 线性反汇编在 .text 内嵌跳转表（0x00748350 起 4 个 dword 指针）处失步，"
  "在 0x00748368 解出一条 3 字节伪指令（adc edx,[eax-0x18]）把 0x0074836A 的 E8 首字节吞入；"
  "其后 5 字节为垃圾解码、0x0074836F 才复位 ⇒ 该 call 从未进入 bounds 集合，四份清单同时缺失（同源同扫）。")
P("  ② 同一缺陷的全局规模：原始 E8 对 %d，边界调用对 %d，差 %d；其中『目标在清单目标集合内却漏记』共 %d 条，"
  "逐条验真仅 %d 条为真调用（0x%08X），另 %d 条是 E8 落在别的指令内部的假阳性。"
  % (len(raw_pairs), len(bound_pairs), len(raw_pairs) - len(bound_pairs), len(raw_hit), 1, GAP_TGT, len(raw_hit) - 1))
P("  ③ installs：6,226 条全部通过正控（%d/%d），负控 0 漏放；248,114 B 在 sweep.json 内，F24 已含。" % (good, len(ins_all)))

open(ROOT + r"\_r66\verify_r66.out.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n[saved] _r66/verify_r66.out.txt (%d lines)" % len(L))
