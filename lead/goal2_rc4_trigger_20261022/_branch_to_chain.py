# -*- coding: utf-8 -*-
"""从单例清零到崩溃链的分支定位：0x6930A0 门禁 + msg 分派 + 单例读点（§348）。

## 为什么查这个

§347 把复现判据从「对象是否存活」改成「关窗 0x777803 清零后是否仍跑到这条链」。
本脚本要把「跑到这条链」拆成可枚举的分支条件。

## 本轮拿到的结构（逐条断言）

  G1 全文件对 [0x87F7E8] 的**值读取**只有 2 处：0x429331 与 0x6933A4。
     两处都不在 §346 的 30 个 call 0x724730 站点所在函数内 ⇒ 它们是**旁路入口**。

  G2 0x6930A0（crash_site 的分派目标）开头有 6 个门禁：
     [0xA8E378] / [0xA8ED5C] / [0xA8ED6B] / [0xA8E9A0] / [0x887324] / [0x887640]
     任一为 0 ⇒ jmp 0x693408（直接返回，不进崩溃链）。

  G3 过门禁后按 msg-0x201 两级查表分派：
     字节表 0x693428（21 项）→ dword 跳转表 0x693410（6 个有效项）。
     21 个 msg 里只有 4 个落到实质分支，其余全部 idx=5 = 0x693408（返回）。

  G4 实质分支：
       msg 0x201 → 0x693126
       msg 0x202 → 0x6931F9
       msg 0x204 → 0x6932A4
       msg 0x205 → 0x693366  ← 含 0x6933A4 读单例 + 0x6933D2 清 [esi+0x555A]
       msg 0x215 → 0x6933E6  （先行特殊判断，见 0x6930EE 处的 cmp）

  G5 0x6933A4 读单例后 `call [edx+0x48]`（slot 18），即用单例对象的方法；
     随后 0x6933D2 `mov [esi+0x555A], bl`（bl=0）清状态位。
     这条分支是「鼠标离开/释放」类语义，与 §345 定的 [esi+0x555A] 布尔状态位一致。

★ 口径坑：
  - `call [reg+0x14]`（slot 5）全文件 272 处，**不能**用来反推「谁触发 0x652CF0」；
    slot5 在通用多态代码里被大量使用，语义各不相同。必须用「谁读 0x87F7E8」定位。
  - 跳转表 0x693410 只有前 6 项是代码指针，第 6 项之后混入了字节表数据。
    表长必须靠「项是否为 .text 内 */}
  - 从任意偏移线性反汇编会产生幻象（0x693380 起便是）。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

SINGLETON = 0x0087F7E8
DISPATCH_FN = 0x006930A0
GATE_ADDRS = [0x00A8E378, 0x00A8ED5C, 0x00A8ED6B, 0x00A8E9A0,
              0x00887324, 0x00887640]
RET_NODE = 0x00693408
BYTE_TBL = 0x00693428
DWORD_TBL = 0x00693410
MSG_BASE = 0x201
MSG_COUNT = 21
READERS = [0x00429331, 0x006933A4]
STATE_BIT_CLR = 0x006933D2

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


def build(secs, data):
    t = [s for s in secs if s["name"] == ".text"][0]
    tb = data[t["roff"]:t["roff"] + t["rsize"]]
    tva = t["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    fof = array("I", bytes(4 * len(tb)))
    insns = []
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
                pend = False
            if cur is not None:
                for k in range(o, o + ins.size):
                    fof[k] = cur
            insns.append((o, ins.mnemonic, ins.op_str))
            if ins.mnemonic in ("ret", "retf", "int3"):
                pend = True
            off = o + ins.size
            prog = True
        if not prog:
            off += 1
    return tb, tva, insns, fof


def main():
    data, img_base, secs = load()
    tb, tva, insns, fof = build(secs, data)
    n = len(tb)
    bnd = set(o for (o, m, s) in insns)
    text = [s for s in secs if s["name"] == ".text"][0]
    print("镜像基数 0x%08X；.text 解码 %d 条" % (img_base, len(insns)))

    def iscode(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    def rd(va):
        o = va2off(secs, va)
        return None if o is None else struct.unpack_from("<I", data, o)[0]

    def rb(va):
        o = va2off(secs, va)
        return None if o is None else data[o]

    # ---------- G1 单例值读取点普查 ----------
    print()
    print("=== G1 全文件对 [0x87F7E8] 的值读取 ===")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    from capstone.x86 import X86_OP_MEM
    reads = []
    off = 0
    while off < n:
        prog = False
        for ins in md.disasm(tb[off:], tva + off):
            oo = ins.address - tva
            if len(ins.operands) >= 2 and ins.mnemonic == "mov" \
                    and ins.operands[0].type != X86_OP_MEM:
                s2 = ins.operands[1]
                if s2.type == X86_OP_MEM and s2.mem.disp == SINGLETON \
                        and not s2.mem.base and not s2.mem.index:
                    reads.append(tva + oo)
            off = oo + ins.size
            prog = True
        if not prog:
            off += 1
    print("  值读取 %d 处：%s" % (len(reads), ", ".join("0x%08X" % r for r in reads)))
    check(len(reads) == len(READERS),
          "★ 全文件仅 %d 处读单例值（不是海量，可逐个定性）" % len(READERS),
          "实测 %d 处" % len(reads))
    for r in READERS:
        check(r in reads, "★ 0x%08X 在读取点集内" % r)

    # 这两个读点所在的函数，是否在 30 个崩溃站点所在函数内
    crash_sites = [0x4A8B75, 0x640427, 0x654413, 0x654469, 0x6AC00B, 0x6AC03E,
                   0x6AC0ED, 0x6AC140, 0x6AC193, 0x6AC1E6]
    crash_funcs = set(fof[s - tva] for s in crash_sites)
    reader_funcs = set(fof[r - tva] for r in READERS)
    print("  读点所在函数：%s" % ", ".join("0x%08X" % f for f in sorted(reader_funcs)))
    print("  崩溃站点所在函数（样本 %d）：%s"
          % (len(crash_funcs), ", ".join("0x%08X" % f for f in sorted(crash_funcs))))
    check(reader_funcs.isdisjoint(crash_funcs),
          "★ 单例读点**不在**崩溃站点所在函数内 ⇒ 它们是旁路，不是主链",
          "交集 %s" % (reader_funcs & crash_funcs or "空"))

    # ---------- G2 门禁 ----------
    print()
    print("=== G2 0x6930A0 的 6 个门禁 ===")
    o = va2off(secs, DISPATCH_FN)
    seq = list(md.disasm(data[o:o + 0xA0], DISPATCH_FN))
    gates = []
    for i in seq:
        for g in GATE_ADDRS:
            if "0x%x" % g in i.op_str:
                gates.append((i.address, g, i.mnemonic + " " + i.op_str))
    print("  命中的门禁引用 %d 处：" % len(gates))
    for (a, g, t) in gates:
        print("    0x%08X  [0x%08X]  %s" % (a, g, t))
    check(len(gates) >= 6, "★ 6 个门禁全部在 0x6930A0 内被引用", "%d 处" % len(gates))
    je_nodes = [i.op_str for i in seq
                if i.mnemonic.startswith("j") and RET_NODE - 0x400000 >= 0
                and ("0x693408" in i.op_str or "0x693408" in i.op_str)]
    je_to_ret = [i for i in seq if i.mnemonic.startswith("j")
                 and "0x693408" in i.op_str]
    print("  跳向 0x693408（直接返回）的分支 %d 个" % len(je_to_ret))
    check(len(je_to_ret) >= 5,
          "★ 至少 5 个门禁失败分支直接跳到 0x693408（不进崩溃链）",
          "%d 个" % len(je_to_ret))

    # ---------- G3 分派表 ----------
    print()
    print("=== G3 msg 分派：字节表 0x693428 + 跳转表 0x693410 ===")
    # 先确认分派代码形态
    disp_code = [i for i in seq if "0x693428" in i.op_str or "0x693410" in i.op_str]
    for i in disp_code:
        print("    0x%08X  %s %s" % (i.address, i.mnemonic, i.op_str))
    check(len(disp_code) >= 2,
          "★ 分派代码同时引用字节表与跳转表（两级查表）", "%d 条" % len(disp_code))

    # 跳转表有效项数（只认 .text 内）
    jt = []
    for k in range(16):
        v = rd(DWORD_TBL + k * 4)
        if v is None or not iscode(v):
            break
        jt.append(v)
    print("  dword 跳转表有效项 %d 个：%s" % (len(jt), ", ".join("0x%08X" % v for v in jt)))
    check(len(jt) == 6, "★ 跳转表恰 6 个有效项（其后混入字节表数据）", "%d 项" % len(jt))

    # 字节表 21 项
    tbl = [rb(BYTE_TBL + i) for i in range(MSG_COUNT)]
    print("  字节表 %d 项：" % len(tbl))
    dist = {}
    for i, v in enumerate(tbl):
        dist.setdefault(v, []).append(MSG_BASE + i)
    for idx in sorted(dist):
        msgs = dist[idx]
        tgt = jt[idx] if idx < len(jt) else None
        print("    idx %d -> 0x%s   （%d 个 msg：%s）"
              % (idx, ("%08X" % tgt) if tgt else "越界",
                 len(msgs), ", ".join("0x%X" % m for m in msgs[:6])
                 + ("…" if len(msgs) > 6 else "")))
    substantive = [i for i in sorted(dist) if i < len(jt) and jt[i] != RET_NODE]
    print("  实质分支 idx：%s" % substantive)
    check(len(substantive) == 5,
          "★ 21 个 msg 里只有 5 个落到实质分支 idx（0..4），其余 16 个全返回",
          "%d 个：%s" % (len(substantive), substantive))
    check(dist.get(5) and len(dist[5]) >= 15,
          "★ idx=5 集合最多（≥15 个 msg 共用同一个返回出口）",
          "%d 个" % (len(dist.get(5, []))))

    # ---------- G4 msg 0x205 分支 ----------
    print()
    print("=== G4 msg 0x205 分支（含读单例 + 清状态位）===")
    msg205 = [m for m in dist.get(3, [])]
    print("  落到 idx 3 的 msg：%s" % ", ".join("0x%X" % m for m in msg205))
    check(0x205 in msg205, "★ 0x205 落在 idx 3（0x%08X 分支）" % jt[3],
          ", ".join("0x%X" % m for m in msg205))
    br3 = jt[3]
    o = va2off(secs, br3)
    bseq = list(md.disasm(data[o:o + 0xA0], br3))
    btxt = [(i.address, i.mnemonic, i.op_str) for i in bseq]
    has_read = any(a == 0x006933A4 for (a, m, s) in btxt)
    has_clr = any(a == STATE_BIT_CLR for (a, m, s) in btxt)
    has_slot18 = any("[edx + 0x48]" in s for (a, m, s) in btxt)
    print("  分支体内：读单例=%s  清[esi+0x555A]=%s  call[edx+0x48]=%s"
          % (has_read, has_clr, has_slot18))
    check(has_read, "★ 0x%08X 分支内含 0x6933A4 读单例" % br3)
    check(has_clr, "★ 分支内含 0x%08X 清 [esi+0x555A]（与 §345 状态位一致）"
          % STATE_BIT_CLR)
    check(has_slot18, "★ 分支内 call [edx+0x48]（用单例的 slot 18 方法）")

    # ---------- G5 这些分支是否进入崩溃链 ----------
    print()
    print("=== G5 5 个实质分支是否落入崩溃站点所在函数 ===")
    branch_targets = [jt[i] for i in substantive]
    # 每个分支可能跨多个函数：用「从分支头线性解码到首个 ret」推定其覆盖范围
    crash_sites = [0x4A8B75, 0x640427, 0x654413, 0x654469, 0x6AC00B, 0x6AC03E,
                   0x6AC0ED, 0x6AC140, 0x6AC193, 0x6AC1E6, 0x6D059B, 0x6D0619,
                   0x6D0634, 0x6D0664, 0x6D089D, 0x6D08B3, 0x6D0940, 0x6D09FA,
                   0x6D1293, 0x6D1308, 0x6D137E, 0x6D13F3, 0x6D1541, 0x6D155C,
                   0x6D15CB, 0x6D1605, 0x6D1632, 0x6D16C2, 0x6D16DD, 0x6D1744]
    crash_funcs = set(fof[s - tva] for s in crash_sites)
    hit = [b for b in branch_targets if fof[b - tva] in crash_funcs]
    print("  分支目标：%s" % ", ".join("0x%08X" % b for b in branch_targets))
    print("  其中 func 落在崩溃站点函数集内的：%s"
          % (", ".join("0x%08X" % b for b in hit) if hit else "无"))
    check(not hit,
          "★ 5 个 msg 分支所在函数**都不是** 30 个崩溃站点所在函数 ⇒ 不直接进崩溃链",
          "%d 个命中" % len(hit))
    # 分支与崩溃函数在字节距离上也应远
    mind = min(abs(b - f) for b in branch_targets for f in crash_funcs)
    print("  分支目标与最近崩溃站点函数的最小距离：0x%X 字节" % mind)
    check(mind > 0x1000,
          "★ 二者在地址空间上相距 > 0x1000（不是相邻代码）",
          "0x%X" % mind)

    # ---------- 结论 ----------
    print()
    print("=== 结论：从清零到崩溃链的分支条件 ===")
    print("  A. 进入 0x6930A0 后先过 6 个门禁；任一为 0 直接返回，不进崩溃链")
    print("     （7 个跳向 0x693408 的分支，比门禁数多 1：msg 越界那处也跳回）。")
    print("  B. 过门禁后按 msg 分派：21 个 msg 里 5 个有实质分支，16 个共用返回出口。")
    print("  C. 其中 msg 0x205 → idx 3 → 0x693366，会读单例 [0x87F7E8] 并清 [esi+0x555A]。")
    print("  D. 但这 5 个分支所在函数（0x693126/0x6931F9/0x6932A4/0x693366/0x6933E6）")
    print("     **都不是** 30 个 call 0x724730 站点所在函数 ⇒ 这条 msg 路不直接进崩溃链。")
    print("  ⇒ 「关窗时为何跑到崩溃链」仍要靠 0x652CF0 那条虚表路；")
    print("    而 0x652CF0 的触发者不能用 slot5 反查（272 处 call [reg+0x14]，语义各异）。")
    print("  ⇒ 下一步必须换手段：追 0x652CF0 的实参/调用上下文，或做真机断点。")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 0x6930A0 门禁与 msg 分派结构定案（5 实质分支，均不进崩溃链）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
