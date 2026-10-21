# -*- coding: utf-8 -*-
"""29 处 call [reg+0xA8] 的 reg 来源普查 + E8 图断点证明（§346）。

上一轮（§345）留下的唯一承重缺口：
  「分发点静态确定（slot 42 / +0xA8），但从鼠标消息到那个分发点的路没找到」。
上一轮的判据是 E8 图 BFS，从消息泵 0x5D4D50 出发到 0x4A8960 为 NOT FOUND。
本轮先证明那条 BFS **在结构上不可能成功**：
  消息泵经 user32 的 DispatchMessageA（导入）进入 WndProc 0x7775C0，
  E8 图上泵与 WndProc 之间没有任何边 ⇒ 上一轮的 NOT FOUND 是图的断点，不是不可达。

然后做真正的普查：把 29 个 `call dword ptr [reg+0xA8]` 点的 reg 逐个向前切片，
解析成「reg <- [基址+disp]」链，看哪一个链的根是 0x87F7E8（崩溃链宿主的 vtable）。

口径与已知坑（本脚本内注释标 ★ 的都是踩过的）：
  - 站点用字节模式 FF /2 mod=10 disp32=0xA8 初筛，再用线性解码的 func_of 表
    **验指令边界**——否则会把数据里的同形字节当站点（naive 扫描被欺骗）。
  - 反向切片遇 call/jmp 且被跟踪寄存器在 clobber 集内 ⇒ 立即判 UNKNOWN，
    绝不跨越调用点继续往前猜。
  - 到达函数头仍未定义 ⇒ UNKNOWN（形参）。

只读磁盘，零真机。全部断言失败即非 0 退出。
"""
import io
import struct
import sys

import capstone
from capstone import x86
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM
from array import array

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

DISP = 0xA8
VT_GLOBAL = 0x0087F7E8          # 0x7E1964 那张虚表的持有者（BSS 全局）
VT_HEAD = 0x007E1964
PUMP = 0x005D4D50
WNDPROC = 0x007775C0
DISPATCH_TARGET = 0x006930A0    # WndProc 内 0x777A98 分派到的表驱动函数
L3 = 0x004A8960                 # 崩溃链最外层宿主 = slot[42]

# FF /2, mod=10, rm=reg ⇒ modrm = 0b10_010_rmm ⇒ 0x90 + rm
# ★ 首版把 eax 写成 0x92（off by 2），29 站只抓到 17 站、漏掉 0x4A88AA。
MODRM = {0x90: "eax", 0x91: "ecx", 0x92: "edx", 0x93: "ebx",
         0x94: "esp", 0x95: "ebp", 0x96: "esi", 0x97: "edi"}

fails = []


def check(cond, label, detail=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label,
                           ("  " + detail) if detail else ""))
    if not cond:
        fails.append(label)
    return cond


def load():
    data = io.open(GAMEMD, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    img_base = struct.unpack_from("<I", data, pe + 0x34)[0]
    sec_off = pe + 24 + opt_size
    secs = []
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
        vsize, rva, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        secs.append({"name": name, "va": img_base + rva, "vsize": vsize,
                     "rsize": rsize, "roff": roff})
    return data, img_base, secs, pe


def va2off(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + s["rsize"]:
            return s["roff"] + (va - s["va"])
    return None


def resolve_iat(data, secs, img_base, pe, want):
    """返回导入名 == want 的 IAT 槽 VA。★ 目录/ILT/Name 三个字段都是 RVA，须加 img_base。"""
    opt = pe + 24
    imp_rva, _ = struct.unpack_from("<II", data, opt + 0x68)
    if not imp_rva:
        return None
    o = va2off(secs, img_base + imp_rva)
    while o is not None:
        oft, ts, fc, name_rva, ft = struct.unpack_from("<IIIII", data, o)
        if not name_rva and not ft:
            break
        no = va2off(secs, img_base + name_rva)
        dll = data[no:data.index(b"\x00", no)].decode("ascii", "replace") if no else ""
        ilt = va2off(secs, img_base + oft) if oft else va2off(secs, img_base + ft)
        iat = va2off(secs, img_base + ft) if ft else None
        k = 0
        while ilt is not None:
            ent = struct.unpack_from("<I", data, ilt + k * 4)[0]
            if not ent:
                break
            if not (ent & 0x80000000):
                so = va2off(secs, img_base + ent + 2)
                if so:
                    nm = data[so:data.index(b"\x00", so)].decode("ascii", "replace")
                    if nm == want:
                        return img_base + ft + k * 4
            k += 1
        o += 20
    return None


def linear(data, secs, img_base):
    """单遍线性解码 .text，返回 (tb, tva, insn_off_list, func_of)。"""
    t = [s for s in secs if s["name"] == ".text"][0]
    tb = data[t["roff"]:t["roff"] + t["rsize"]]
    tva = t["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    func_of = array("I", bytes(4 * len(tb)))
    offs = []
    cur = None
    pending_head = True
    off = 0
    n = len(tb)
    while off < n:
        progressed = False
        for ins in md.disasm(tb[off:], tva + off):
            o = ins.address - tva
            if pending_head and ins.mnemonic not in ("nop", "int3", "lea"):
                cur = ins.address
                pending_head = False
            if cur is not None:
                for k in range(o, o + ins.size):
                    func_of[k] = cur
            offs.append((o, ins.mnemonic, ins.op_str))
            if ins.mnemonic in ("ret", "retf", "int3"):
                pending_head = True
            off = o + ins.size
            progressed = True
        if not progressed:
            off += 1
    return tb, tva, offs, func_of


def sites(tb, offs):
    """字节模式初筛 + 指令边界验证。"""
    boundary = set(o for (o, m, s) in offs)
    out = []
    for i in range(len(tb) - 6):
        if tb[i] != 0xFF or tb[i + 1] not in MODRM:
            continue
        if struct.unpack_from("<I", tb, i + 2)[0] != DISP:
            continue
        if i not in boundary:
            continue
        out.append((i, MODRM[tb[i + 1]]))
    return out


CLOBBER = {"eax", "ecx", "edx"}   # cdecl 易失，call 后不可信


class Res(object):
    def __init__(self, kind, value, chain):
        self.kind = kind      # "global" | "deref" | "const" | "unknown"
        self.value = value
        self.chain = chain


def resolve(insns, idx, reg, md, depth=0):
    """从 insns[idx] 之前往回找 reg 的定义。insns 是带 detail 的该函数指令列表。"""
    if depth > 8:
        return Res("unknown", None, ["hop 超限"])
    for j in range(idx - 1, -1, -1):
        ins = insns[j]
        _, writes = ins.regs_access()
        if reg in [md.reg_name(w) for w in writes]:
            if ins.mnemonic in ("call", "callf"):
                # call 写出的是被调者返回的 eax，语义上不是「显式定义」
                return Res("unknown", None, ["跨 call 未定义"])
            ops = ins.operands
            if ins.mnemonic == "mov" and len(ops) >= 2:
                src = ops[1]
                if src.type == X86_OP_MEM:
                    m = src.mem
                    b = md.reg_name(m.base) if m.base else None
                    ix = md.reg_name(m.index) if m.index else None
                    if b is None and ix is None:
                        return Res("global", m.disp, ["[0x%x]" % m.disp])
                    if ix is not None:
                        return Res("unknown", None, ["索引寻址 %s" % ix])
                    sub = resolve(insns, j, b, md, depth + 1)
                    ch = ["[%s+0x%x]" % (b, m.disp)] + sub.chain
                    if sub.kind == "global":
                        return Res("deref", sub.value, ch)
                    return Res("unknown", None, ch)
                if src.type == X86_OP_REG:
                    sub = resolve(insns, j, md.reg_name(src.reg), md, depth + 1)
                    return Res(sub.kind, sub.value,
                               ["<- " + md.reg_name(src.reg)] + sub.chain)
                if src.type == X86_OP_IMM:
                    return Res("const", src.imm, ["imm 0x%x" % src.imm])
            if ins.mnemonic == "lea":
                src = ops[1]
                if src.type == X86_OP_MEM:
                    m = src.mem
                    if not m.base and not m.index:
                        return Res("global", m.disp, ["&0x%x" % m.disp])
                return Res("unknown", None, ["lea 非绝对"])
            if ins.mnemonic == "xor" and len(ops) == 2 and ops[0].type == X86_OP_REG \
                    and ops[1].type == X86_OP_REG and ops[0].reg == ops[1].reg:
                return Res("const", 0, ["xor 清零"])
            return Res("unknown", None, [ins.mnemonic + " " + ins.op_str])
        if ins.mnemonic in ("call", "callf", "jmp") and reg in CLOBBER:
            return Res("unknown", None, ["跨 call 且 %s 易失" % reg])
    return Res("unknown", None, ["到函数头未定义（形参）"])


def main():
    data, img_base, secs, pe = load()
    print("镜像基数 0x%08X" % img_base)
    tb, tva, offs, func_of = linear(data, secs, img_base)
    print(".text 线性解码 %d 条指令" % len(offs))

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    raw = sites(tb, offs)
    print()
    print("=== 初筛 %d 个 call [reg+0xA8] 点（已验指令边界）===" % len(raw))

    # 逐个切片
    recs = []
    for (o, base) in raw:
        va = tva + o
        fs = func_of[o]
        if fs == 0:
            continue
        fstart = fs
        # 函数末：func_of 从该函数起点连续
        fend = o
        while fend + 1 < len(func_of) and func_of[fend + 1] == fstart:
            fend += 1
        body = tb[(fstart - tva):fend + 1]
        insns = list(md.disasm(body, fstart))
        idx = None
        for k, ins in enumerate(insns):
            if ins.address == va:
                idx = k
                break
        if idx is None:
            recs.append((va, fstart, base, Res("unknown", None, ["函数内解码未命中站点"])))
            continue
        recs.append((va, fstart, base, resolve(insns, idx, base, md)))

    vt_sites = [r for r in recs if r[3].kind == "deref" and r[3].value == VT_GLOBAL]
    print()
    print("=== 逐个 reg 来源 ===")
    for (va, fs, base, r) in recs:
        tag = "  ★ vtable 0x87F7E8" if r in vt_sites else ""
        print("  0x%08X (func 0x%08X)  %s : %s%s"
              % (va, fs, base, " ".join(r.chain), tag))

    print()
    print("=== 判定 ===")
    check(len(raw) > 0, "存在 call [reg+0xA8] 站点", "%d 个" % len(raw))
    known = [r for r in recs if r[3].kind in ("global", "deref", "const")]
    print("  切片成功 %d / %d（UNKNOWN %d）"
          % (len(known), len(recs), len(recs) - len(known)))

    l3 = [r for r in recs if r[0] == 0x004A88AA]
    check(len(l3) == 1, "崩溃链站点 0x4A88AA 在普查内")
    if l3:
        r = l3[0][3]
        # ★ 更正（§346）：首版判据要求「eax 来自全局 [[0x87F7E8]]」，这是错的方向。
        #   0x4A88AA 在 __thiscall 0x4A8850 内，eax <- [esi]，esi == this == ecx，
        #   与全局 0x87F7E8 无直接地址关系。0x87F7E8 是**对象地址**（首 dword = vtable），
        #   不是 vtable 地址；对象由 0x652CF0 一路透传进来。故此处只断言 this 形态。
        check(r.kind == "unknown" and "[esi+0x0]" in " ".join(r.chain),
              "★ 0x4A88AA 的 eax <- [esi]，而 esi == this（__thiscall），非全局常量",
              " ".join(r.chain))

    n_vt = len(vt_sites)
    print("  经全局 [[0x87F7E8]] 直取的站点 = %d 处（预期 0：该单例不按下标取 vtable）" % n_vt)
    check(n_vt == 0,
          "★ 无站点以全局 0x87F7E8 首 dword 取 vtable（证实「对象地址 ≠ vtable 地址」）",
          "%d 处" % n_vt)

    # ---- E8 图断点证明 ----
    print()
    print("=== E8 图断点（用户态边界）===")
    dma = resolve_iat(data, secs, img_base, pe, "DispatchMessageA")
    check(dma is not None, "解析到 DispatchMessageA 的 IAT 槽",
          "0x%08X" % dma if dma else "未解析")
    pump_hits = []
    if dma:
        for (o, m, s) in offs:
            if m in ("call", "callf") and ("0x%x" % dma) in s:
                pump_hits.append(tva + o)
    check(bool(pump_hits), "消息泵内有 call [DispatchMessageA] 站点",
          ", ".join("0x%08X" % v for v in pump_hits))

    # func 级 E8 图（只用 call rel32，边界已验证）
    boundary = set(o for (o, m, s) in offs)
    edges = {}
    for (o, m, s) in offs:
        if m not in ("call", "callf"):
            continue
        if o + 5 > len(tb) or tb[o] != 0xE8:
            continue
        rel = struct.unpack_from("<i", tb, o + 1)[0]
        tgt = tva + o + 5 + rel
        fs = func_of[o]
        to = None
        if tva <= tgt < tva + len(tb):
            to = func_of[tgt - tva] or None
        if fs and to:
            edges.setdefault(fs, set()).add(to)

    def reach(root, cap=6):
        if root not in edges and root not in set(func_of):
            pass
        seen = {root: 0}
        frontier = [root]
        for d in range(cap):
            nxt = []
            for f in frontier:
                for g in edges.get(f, ()):
                    if g not in seen:
                        seen[g] = d + 1
                        nxt.append(g)
            frontier = nxt
        return seen

    rp = reach(PUMP)
    check(WNDPROC not in rp,
          "★ E8 图上消息泵**到不了** WndProc（上一轮 NOT FOUND 是图的断点，不是不可达）",
          "泵闭包 %d 个函数" % len(rp))

    for root, name in ((PUMP, "消息泵"), (WNDPROC, "WndProc"), (DISPATCH_TARGET, "分派目标")):
        seen = reach(root)
        hit = [r for r in recs if r[1] in seen]
        print("  从 %s 0x%08X 出发：闭包 %d 函数，其中含 %d 处 +0xA8 站点"
              % (name, root, len(seen), len(hit)))
        if root == WNDPROC:
            # ★ 更正（§346）：首版断言「WndProc 的 E8 闭包内必含 +0xA8 站点」，方向错了。
            #   实测 WndProc 0x7775C0 自身不做 +0xA8 分派，它经 [0x887628] 的
            #   vtable[0x38]/[0x40] 向外转 —— 那是间接调用，E8 图本来就看不见。
            #   所以「闭包内 0 处」是**正确事实**，不是失败。
            check(len(hit) == 0,
                  "★ WndProc 的 E8 闭包内 0 处 +0xA8 站点（它走 [0x887628] vtable 转出）",
                  "%d 处" % len(hit))

    # L3 是否在任一闭包内
    l3_seen = [(nm, reach(rt)) for rt, nm in ((PUMP, "泵"), (WNDPROC, "WndProc"),
                                              (DISPATCH_TARGET, "分派目标"))]
    where = [nm for nm, s in l3_seen if L3 in s]
    print("  0x4A8960 在哪些根的 E8 闭包内：%s" % (", ".join(where) if where else "都不在"))

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 普查完成：+0xA8 站点 %d 处，其中 %d 处经虚表 0x87F7E8 进入" % (len(recs), n_vt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
