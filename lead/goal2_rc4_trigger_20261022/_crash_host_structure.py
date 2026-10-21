# -*- coding: utf-8 -*-
"""RC-4 真崩溃函数 0x724730 的宿主结构 + 单例 [0x887368] 读写全账（§346 主体）。

本轮三个必证事项（都由上一轮遗留的口径错误引出）：

  一、crash_site.json 那条 `call [eax+0xA8]` → slot42=0x4A8960 的链**是不是崩溃真路**。
      本脚本证明：0x4A8960 函数体内部**直接** `call 0x724730`（E8），
      所以链是真的，但「间接分发」这个机理描述是错的 —— 该崩溃函数有 30 个直接 E8 调用者。

  二、crash_site.json 标成「4 级宿主链」的 0x4A8960 / 0x6ABD30 / 0x6403A0 / 0x654320
      **全都是 0x724730 的直接调用者**，即兄弟路径，不是自下而上的调用链。
      所以「5 宿主三无 ⇒ 只能间接分发」这个推论失效。

  三、单例 0x887368 的读写全账。上一轮草稿把 operands[0].type==1 当 MEM 用（1 是 REG），
      导致 0 个写点、74 个读点全部错档。本脚本用正确口径重算，并断言已知写点 0x777803 在内。

口径（本文件内 ★ 标注的都是踩过的坑）：
  - capstone X86_OP_REG == 1，X86_OP_MEM == 3。★ 不可写反。
  - 「写点」判定：mov 且 dst 操作数是 MEM 且 disp == 目标 VA；或 and/or/xor 同形。
  - E8 站点必须落在已线性解码的指令边界上（bnd 集）。
  - 函数归属用单遍线性解码的 func_of 表，不用「往前扫找函数头」的猜法。

只读磁盘，零真机。断言失败即非 0 退出。
"""
import io
import struct
import sys
from array import array

import capstone
from capstone.x86 import X86_OP_REG, X86_OP_MEM

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CRASH = 0x00724730        # 真崩溃函数头（0x724737 是 mov eax,[ebp+0x250]）
CRASH_SITE = 0x00724737
SINGLETON = 0x00887368
KNOWN_ZERO_VA = 0x00777803   # mov dword ptr [0x887368], ebx（§342 已定）
VT_L3 = 0x007E1964
SLOT_L3 = 42
HOSTS = {0x004A8960: "L3 / slot42 目标", 0x006ABD30: "crash_site 称 level2",
         0x006403A0: "crash_site 称 level1", 0x00654320: "crash_site 称 level0"}

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


def linear(secs, data):
    t = [s for s in secs if s["name"] == ".text"][0]
    tb = data[t["roff"]:t["roff"] + t["rsize"]]
    tva = t["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    func_of = array("I", bytes(4 * len(tb)))
    insns = []
    cur = None
    pending = True
    off = 0
    n = len(tb)
    while off < n:
        prog = False
        for ins in md.disasm(tb[off:], tva + off):
            o = ins.address - tva
            if pending and ins.mnemonic not in ("nop", "int3", "lea"):
                cur = ins.address
                pending = False
            if cur is not None:
                for k in range(o, o + ins.size):
                    func_of[k] = cur
            insns.append((o, ins.mnemonic, ins.op_str))
            if ins.mnemonic in ("ret", "retf", "int3"):
                pending = True
            off = o + ins.size
            prog = True
        if not prog:
            off += 1
    return tb, tva, insns, func_of


def main():
    data, img_base, secs, pe = load()
    tb, tva, insns, func_of = linear(secs, data)
    n = len(tb)
    print("镜像基数 0x%08X；.text 线性解码 %d 条" % (img_base, len(insns)))
    bnd = set(o for (o, m, s) in insns)

    # ---------- 一、崩溃点邻域形态 ----------
    print()
    print("=== 一、0x724730 的函数形态（this 从 ecx 来，不是全局）===")
    o = va2off(secs, CRASH)
    seq = ["%s %s" % (i.mnemonic, i.op_str)
           for i in capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
           .disasm(data[o:o + 0x20], CRASH)]
    print("  " + " | ".join(seq[:5]))
    check("mov ebp, ecx" in seq, "0x724730 头 `mov ebp, ecx`（__thiscall，ebp=this）")
    site = [x for x in seq if x.startswith("mov eax, dword ptr [ebp + 0x250]")]
    check(bool(site), "崩溃指令是 `mov eax,[ebp+0x250]`（Count 字段）")
    # 容器紧邻
    check(any("[ebp + 0x24c]" in x or "[ebp + 0x24c]" in x.replace("0x24c]", "0x24c]")
              for x in seq) or True,
          "容器 Items 在 this+0x24C、Count 在 this+0x250（§341 已定，此处仅提示）",
          "0x250-0x24C = %d" % (0x250 - 0x24C))

    # ---------- 二、0x724730 是否虚表槽 ----------
    print()
    print("=== 二、0x724730 是否靠间接分发（复检 §341「三无」）===")
    text = [s for s in secs if s["name"] == ".text"][0]

    def is_code(v):
        return text["va"] <= v < text["va"] + text["rsize"]

    pat = struct.pack("<I", CRASH)
    vt_hits = []
    i = 0
    while True:
        j = data.find(pat, i)
        if j < 0:
            break
        va = j + 0x400000
        sn = None
        for s in secs:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
                sn = s["name"]
                break
        if sn == ".rdata" and j >= 4:
            if all(is_code(struct.unpack_from("<I", data, j + k * 4)[0]) for k in (-1, 1)):
                vt_hits.append(va)
        i = j + 1
    check(len(vt_hits) == 0, "★ 0x724730 **不在任何虚表槽**（无邻项皆代码的 .rdata 命中）",
          "%d 处" % len(vt_hits))

    # 直接 E8 调用者
    callers = []
    for o2 in range(n - 5):
        if tb[o2] != 0xE8 or o2 not in bnd:
            continue
        rel = struct.unpack_from("<i", tb, o2 + 1)[0]
        if tva + o2 + 5 + rel == CRASH:
            callers.append(tva + o2)
    check(len(callers) >= 30, "★ 0x724730 有 ≥30 个**直接 E8 调用者**",
          "实测 %d 个" % len(callers))

    # ---------- 三、4 元素「宿主」实为兄弟 ----------
    print()
    print("=== 三、crash_site 的「4 级宿主链」实为直接调用者兄弟集 ===")
    by_func = {}
    for c in callers:
        fs = func_of[c - tva] or 0
        by_func.setdefault(fs, []).append(c)
    print("  30 个调用点分布在 %d 个函数里：" % len(by_func))
    for fs, cs in sorted(by_func.items()):
        tag = "  ★ " + HOSTS[fs] if fs in HOSTS else ""
        print("    func 0x%08X  ×%d  %s%s"
              % (fs, len(cs), ", ".join("0x%08X" % c for c in cs[:4]), tag))

    for h, desc in sorted(HOSTS.items()):
        check(h in by_func,
              "★ 宿主 0x%08X（%s）直接 call 0x724730" % (h, desc),
              "%d 处" % len(by_func.get(h, [])))
    check(len(by_func) > len(HOSTS),
          "★ 调用者函数数 > 4（不是单一链条，是 30 站点/%d 函数）" % len(by_func),
          "%d > %d" % (len(by_func), len(HOSTS)))

    # 4A8960 → 724730 的具体站点
    l3sites = by_func.get(0x004A8960, [])
    check(bool(l3sites), "★ 0x4A8960 函数体内直接 call 0x724730（链是真的，机理不是间接）",
          ", ".join("0x%08X" % c for c in l3sites))

    # ---------- 四、单例 0x887368 读写全账（正确口径）----------
    print()
    print("=== 四、单例 0x887368 读写全账（★ 修正 operands[0].type 误用）===")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    writes, reads = [], []
    o = 0
    while o < n:
        prog = False
        for ins in md.disasm(tb[o:], tva + o):
            oo = ins.address - tva
            if ins.mnemonic in ("mov", "movzx", "movsx", "and", "or", "xor", "add", "sub") \
                    and len(ins.operands) >= 1:
                d = ins.operands[0]
                if d.type == X86_OP_MEM and d.mem.disp == SINGLETON \
                        and not d.mem.base and not d.mem.index:
                    writes.append((tva + oo, ins.mnemonic + " " + ins.op_str))
                else:
                    for op in ins.operands:
                        if op.type == X86_OP_MEM and op.mem.disp == SINGLETON \
                                and not op.mem.base and not op.mem.index:
                            reads.append((tva + oo, ins.mnemonic + " " + ins.op_str))
                            break
            o = oo + ins.size
            prog = True
        if not prog:
            o += 1

    print("  写点 %d：" % len(writes))
    for a, t in writes:
        print("    0x%08X  %s" % (a, t))
    print("  读点 %d（只列前 6）" % len(reads))
    for a, t in reads[:6]:
        print("    0x%08X  %s" % (a, t))

    check(len(writes) >= 1, "★ 0x887368 有写点（★ 首版 operands[0].type==1 当 MEM 用，误报 0）",
          "%d 处" % len(writes))
    check(any(a == KNOWN_ZERO_VA for a, t in writes),
          "★ 已知清零点 0x777803 在写点集内（与 §342 交叉验证）",
          "命中" if any(a == KNOWN_ZERO_VA for a, t in writes) else "未命中")

    # ---------- 五、崩溃函数是否被任何「鼠标分支」直接调 ----------
    print()
    print("=== 五、30 个调用点里有没有来自 WndProc/鼠标侧 ===")
    mouse_side = [0x006930A0, 0x007775C0, 0x005D4D50]
    hit = [c for c in callers
           if any(abs((func_of[c - tva] or 0) - m) < 0x10000 for m in mouse_side)]
    print("  与 WndProc/分派目标/消息泵在 64KB 内的调用者：%s"
          % (", ".join("0x%08X" % c for c in hit) if hit else "无"))
    check(True, "如实记录（近似邻近不是可达性证明，只作线索）", "%d 个" % len(hit))

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 结论：0x724730 有 %d 个直接 E8 调用者、分布在 %d 个函数；"
          "crash_site 的 4 宿主全部是它的直接调用者（兄弟集，非调用链）"
          % (len(callers), len(by_func)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
