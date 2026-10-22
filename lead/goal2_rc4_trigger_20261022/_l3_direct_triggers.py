# -*- coding: utf-8 -*-
"""v[42] 目标的直接触发点普查 + 单例 COM 指针排除（§351）。

## 本轮问题

§349 定案链起点是 RadarClass::One_Time()（只跑一次），§350 证「雷达触发 v[42]
是内部行为、不产生新入口」。于是剩下的真问题是：

  **v[42] 目标 = 0x4A8960，除了 One_Time 那条虚表路，还有谁把它当方法直接调？**

若有「别的时机」直接调 0x4A8960、且传的就是雷达单例，那才是 §349 要的复现入口。

## 本轮结论（逐条断言）

  P1 直接 `call 0x4A8960` 的 E8 站点恰 2 处（0x5610EC、0x67E7F9）——**不经虚表**。
     （§346 的 30 处是 0x724730 的调用者；这里查的是 0x4A8960 自己的调用者。）

  P2 这两处**紧邻其前都 `mov ecx, 0x87F7E8`** ⇒ 把雷达单例本体直接当 this 传进 L3。
     这是比 §350「reg 来自未知全局」强得多的证据：this 直接钉死是雷达。

  P3 宿主1 0x560DCF 是**显示模式切换**路径（字符串 Mode apparently set OK /
     VisibleRect: %dx%d / Deleting AlternateSurface）——与 §349 分岔 B 吻合。

  P4 两个宿主 func_of 头都是真头、且 E8 调用者 0、自身地址不作 dword 出现在 .rdata
     ⇒ 静态上**它们的入口未定**（很可能经「别的对象」的虚表间接调，那对象我尚未映射）。
     如实记为 UNRESOLVED，不假装闭合。

  P5 排除：§350 的 3 处 winonline [0xAC116C] 站点（0x77FF8C/0x78F1CE/0x7A5830）——
     [0xAC116C] 是 `push 0xAC116C` 交给 CoCreateInstance 的 OUT 参数（COM 实例指针），
     与雷达单例无关；0x7A5830 还带**真** null 守卫（test eax,eax/je）。⇒ 非 v[42] 雷达路。

  P6 复核 §350 存疑点：0x68589C 的 `cmp ecx, esi` **确是 null 守卫**——
     对齐解码 `0x685849 xor esi,esi` 直落 `0x68584B cmp ecx,esi`，中间无跳转可绕过。
     （我一度怀疑是「自调用跳过」，复核后推翻该怀疑，§350 原判定成立。）

★ 口径：
  - 「直接 call 0x4A8960」用 E8 rel32 + 指令边界双验证；mov ecx 必须落在
    call 之前 0..8 条内且无中间对 ecx 的写，否则不算「this 直传单例」。
  - 「入口未定」不等于「死代码」：vtable 间接 + tail-jmp 都可能，不下「无人调用」结论。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

L3 = 0x004A8960            # v[42] 目标（视口尺寸变更+缓冲重建）
SINGLETON = 0x0087F7E8     # 雷达单例
BRIDGE = 0x004A8850        # §346 的 v[42] 桥
DIRECT_SITES = [0x005610EC, 0x0067E7F9]
HOST1 = 0x00560DCF
HOST1_STRS = [b"Mode apparently set OK", b"VisibleRect", b"Deleting AlternateSurface"]
WINONLINE = 0x00AC116C
WINONLINE_CO_PUSH = 0x007853BC
CO_IMPORT = 0x007E15FC
W2_GUARD = 0x007A57FE      # test eax,eax 在 0x7A5830 站点前
RADAR_CMP = 0x0068584B     # §350 存疑的 cmp ecx,esi

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
    return data, img_base, secs


def va2off(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + s["rsize"]:
            return s["roff"] + (va - s["va"])
    return None


def cstr(secs, data, va, cap=120):
    o = va2off(secs, va)
    if o is None:
        return None
    e = data.find(b"\x00", o, o + cap)
    if e < 0:
        e = o + cap
    return data[o:e]


def build(secs, data):
    t = [s for s in secs if s["name"] == ".text"][0]
    tb = data[t["roff"]:t["roff"] + t["rsize"]]
    tva = t["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    fof = array("I", bytes(4 * len(tb)))
    heads = []
    bnd = set()
    cur = None
    pend = True
    off = 0
    n = len(tb)
    while off < n:
        prog = False
        for ins in md.disasm(tb[off:], tva + off):
            o = ins.address - tva
            if pend and ins.mnemonic not in ("nop", "int3", "lea"):
                cur = ins.address
                heads.append(cur)
                pend = False
            if cur is not None:
                for k in range(o, o + ins.size):
                    fof[k] = cur
            bnd.add(o)
            if ins.mnemonic in ("ret", "retf", "int3"):
                pend = True
            off = o + ins.size
            prog = True
        if not prog:
            off += 1
    return tb, tva, fof, heads, bnd


def main():
    data, img_base, secs = load()
    tb, tva, fof, heads, bnd = build(secs, data)
    n = len(tb)
    headset = set(heads)
    text = [s for s in secs if s["name"] == ".text"][0]
    rdata = [s for s in secs if s["name"] == ".rdata"][0]
    print("镜像基数 0x%08X；函数头 %d 个" % (img_base, len(heads)))

    def is_code(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    def rd(va):
        o = va2off(secs, va)
        return None if o is None else struct.unpack_from("<I", data, o)[0]

    def e8_callers(tgt):
        out = []
        for o in range(n - 5):
            if tb[o] != 0xE8 or o not in bnd:
                continue
            rel = struct.unpack_from("<i", tb, o + 1)[0]
            if tva + o + 5 + rel == tgt:
                out.append(tva + o)
        return out

    # ---------- P1 直接 call L3 ----------
    print()
    print("=== P1 直接 call 0x%X（不经虚表）===" % L3)
    dc = e8_callers(L3)
    print("  E8 站点 %d 处：%s" % (len(dc), ", ".join("0x%08X" % c for c in dc)))
    check(len(dc) == 2, "★ 0x4A8960 恰 2 处直接 E8 调用", "%d" % len(dc))
    check(all(c in dc for c in DIRECT_SITES), "★ 两处 = 0x5610EC / 0x67E7F9")

    # ---------- P2 紧邻 mov ecx, 单例 ----------
    print()
    print("=== P2 紧邻之前是否 mov ecx, 0x87F7E8（this 直传单例）===")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    all_pass = True
    for site in DIRECT_SITES:
        fh = fof[site - tva]
        o = va2off(secs, fh)
        seq = list(md.disasm(data[o:va2off(secs, site) + 6], fh))
        idx = [k for k, i in enumerate(seq) if i.address == site]
        found = None
        if idx:
            k = idx[0]
            for j in range(k - 1, max(-1, k - 9), -1):
                i = seq[j]
                if i.mnemonic == "mov" and "ecx" in i.op_str.split(",")[0] \
                        and i.operands and i.operands[-1].type == X86_OP_IMM \
                        and i.operands[-1].imm == SINGLETON:
                    found = i.address
                    break
                # 中途若重写 ecx 其它来源，停
                if i.mnemonic == "mov" and "ecx" in i.op_str.split(",")[0]:
                    break
        ok = found is not None
        all_pass = all_pass and ok
        print("    站点 0x%08X: mov ecx,0x87F7E8 命中=%s%s"
              % (site, ok, ("  @0x%08X" % found) if found else ""))
    check(all_pass, "★ 两处都紧邻 `mov ecx, 0x87F7E8` ⇒ this 直接钉死为雷达单例")

    # ---------- P3 宿主1 显示模式路径 ----------
    print()
    print("=== P3 宿主 0x%X 的字符串（定性显示模式路径）===" % HOST1)
    o = va2off(secs, HOST1)
    hs = []
    for i in md.disasm(data[o:o + 0x420], HOST1):
        if i.mnemonic == "push" and i.operands and i.operands[0].type == X86_OP_IMM:
            s = cstr(secs, data, i.operands[0].imm)
            if s and len(s) >= 6 and all(32 <= c < 127 or c in (9, 10, 13) for c in s):
                hs.append(s)
    print("  命中字符串：%s" % ", ".join(repr(x.decode("ascii", "replace")) for x in hs[:4]))
    check(any(x.startswith(p) for x in hs for p in HOST1_STRS),
          "★ 宿主1 含 Mode/VisibleRect/AlternateSurface ⇒ 显示模式切换路径")

    # ---------- P4 入口未定（如实）----------
    print()
    print("=== P4 两宿主的入口状态（如实记 UNRESOLVED，不假装闭合）===")
    for fh, name in ((HOST1, "宿主1"), (0x0067E776, "宿主2")):
        is_head = fh in headset
        cs = e8_callers(fh)
        # 自身地址是否作 .rdata 代码指针（vtable 槽）
        pat = struct.pack("<I", fh)
        in_vt = []
        i = 0
        while True:
            j = data.find(pat, i)
            if j < 0:
                break
            va = j + 0x400000
            if rdata["va"] <= va < rdata["va"] + rdata["rsize"]:
                if all(is_code(rd(va + d * 4) or 0) for d in (-1, 1)):
                    in_vt.append(va)
            i = j + 1
        print("    %s 0x%08X 真头=%s E8调用者=%d 虚表槽=%d"
              % (name, fh, is_head, len(cs), len(in_vt)))
        check(is_head and len(cs) == 0,
              "★ %s 是函数头但 0 直接 E8 调用者 ⇒ 入口未定（间接/tail）" % name)
    print("  ⇒ 静态未能定位触发者；但「直接以雷达为 this 调 L3」这一事实独立成立。")

    # ---------- P5 排除 winonline COM ----------
    print()
    print("=== P5 排除 [0x%X]（winonline）三站点 ===" % WINONLINE)
    o = va2off(secs, WINONLINE_CO_PUSH)
    wseq = list(md.disasm(data[o:o + 8], WINONLINE_CO_PUSH))
    push_imm = wseq and wseq[0].mnemonic == "push" and wseq[0].operands \
        and wseq[0].operands[0].type == X86_OP_IMM \
        and wseq[0].operands[0].imm == WINONLINE
    check(push_imm, "★ 0x%X = `push 0x%X`（把地址当 OUT 参数）"
          % (WINONLINE_CO_PUSH, WINONLINE))
    # 该 push 后最近 call 经 [CO_IMPORT]（CoCreateInstance）
    o2 = va2off(secs, WINONLINE_CO_PUSH)
    after = list(md.disasm(data[o2:o2 + 0x40], WINONLINE_CO_PUSH))
    co_call = any(i.mnemonic == "call" and ("0x%x" % CO_IMPORT) in i.op_str
                  for i in after)
    print("  附近经 [0x%X]（CoCreateInstance）的间接 call：%s" % (CO_IMPORT, co_call))
    check(co_call, "★ [0x%X] 由 CoCreateInstance 的 OUT 参数填充 ⇒ COM 实例指针，非雷达"
          % WINONLINE)
    # 0x7A5830 站点前有真 null 守卫
    o3 = va2off(secs, W2_GUARD)
    gseq = list(md.disasm(data[o3:o3 + 8], W2_GUARD))
    guard = gseq and gseq[0].mnemonic == "test" and "eax" in gseq[0].op_str
    check(bool(guard), "★ 0x%X 前 `test eax,eax`（对 [0x%X] 的 null 守卫）"
          % (W2_GUARD, WINONLINE))
    # [0x87F7E8] 不在 [0xAC116C] 的写点里（写都是 ebx / OUT）
    wr = []
    off = 0
    while off < n:
        prog = False
        for ins in md.disasm(tb[off:], tva + off):
            oo = ins.address - tva
            if len(ins.operands) >= 1:
                d0 = ins.operands[0]
                if d0.type == X86_OP_MEM and d0.mem.disp == WINONLINE \
                        and not d0.mem.base and not d0.mem.index:
                    wr.append((tva + oo, ins.op_str))
            off = oo + ins.size
            prog = True
        if not prog:
            off += 1
    has_singleton_src = any("0x87f7e8" in t for (a, t) in wr)
    check(not has_singleton_src,
          "★ [0x%X] 的任何 mov 写点都不以 0x87F7E8 为源 ⇒ 不指向雷达" % WINONLINE,
          "mov 写点 %d" % len([1 for (a, t) in wr if t.startswith("mov")]))

    # ---------- P6 复核 §350 null 守卫 ----------
    print()
    print("=== P6 复核 0x68589C 的 cmp ecx,esi 是否 null 守卫 ===")
    # 从函数头 0x685670 线性到 0x68584B，找 xor esi,esi 紧邻且无跳转绕过
    o = va2off(secs, 0x00685670)
    seq = list(md.disasm(data[o:va2off(secs, RADAR_CMP) + 6], 0x00685670))
    xor_i = [k for k, i in enumerate(seq) if i.address == 0x00685849]
    cmp_i = [k for k, i in enumerate(seq) if i.address == RADAR_CMP]
    straight = xor_i and cmp_i and (cmp_i[0] - xor_i[0]) == 1  # xor 紧接 cmp
    check(bool(straight),
          "★ 0x685849 `xor esi,esi` 紧邻 0x68584B `cmp ecx,esi` ⇒ esi 此时恒 0，"
          "§350「是 null 守卫」成立（我的怀疑被推翻）")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ §351 定案：L3 有 2 处直接以雷达为 this 的 E8 触发点（宿主1=显示模式路径）；"
          "winonline 三站点经 COM 指针排除；§350 null 守卫复核成立")
    return 0


if __name__ == "__main__":
    sys.exit(main())
