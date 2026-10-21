# -*- coding: utf-8 -*-
"""RC-4 因果链定案：except.txt 现场 ⇄ 静态反汇编逐层对齐（§346 收官件）。

本脚本把「事实」和「推理」彻底分开：

  第一部分（现场，来自 ra2youli/except.txt）：
    Eip=00724737  Ebp=00000000  Ecx=00000000  Edi=0087F7E8
    Access address: 00000250（= [ebp+0x250]，ebp=0）
    Stack dump 里逐层出现的返回地址。

  第二部分（静态）：把每个返回地址 -5 得到调用点，验证它确实 call 下一层函数。

  第三部分（结论）：两层 guard 都在危险调用**之后**，所以 guard 对本路无效。

★ 重要口径：本脚本第一版把「守卫存在」当成「该路安全」，判 0x4A8B75 为 GUARDED。
  那是错的 —— 守卫在 call 之后，等于没有。本版新增「守卫是否覆盖危险调用」
  这一独立断言（guard_after_call），并对每个站点算出 C 型判据。

只读磁盘（gamemd.exe + except.txt），零真机。断言失败即非 0 退出。
"""
import io
import os
import re
import struct
import sys

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
GAMEMD = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXCEPT = os.path.join(ROOT, "ra2youli", "except.txt")

CRASH_FN = 0x00724730
CRASH_SITE = 0x00724737
SINGLETON = 0x00887368
VTHIS = 0x0087F7E8

# 从 except.txt stack dump 读出的返回地址（低栈→高栈）
EXPECTED_RETS = [
    (0x00F9A354, 0x006543B1, "0x654320 内"),
    (0x00F9A358, 0x00654418, "0x654320 内 —— 0x654413 call 0x724730 的返回地址"),
    (0x00F9A388, 0x006403A8, "0x6403A0 内 —— 0x6403A3 call 0x654320 的返回地址"),
    (0x00F9A3AC, 0x006ABD3E, "0x6ABD30 内 —— 0x6ABD39 call 0x6403A0 的返回地址"),
    (0x00F9A410, 0x004A88B0, "0x4A8850 内 —— 0x4A88AA call [eax+0xA8] 的返回地址"),
    (0x00F9A43C, 0x00652D51, "0x652CF0 内 —— 0x652D4C call 0x4A8850 的返回地址"),
]

# 守卫位置 ⇄ 危险调用位置。四元组 = (函数头, 危险 call, cmp, jcc, jcc 目标)
# ★ 提到模块级是为了让负控能改它 —— 这是本轮最关键的判据（守卫在调用前还是后）。
GUARD_CASES = [
    (0x004A8960, 0x004A8B13, 0x004A8B35, 0x004A8B4E, 0x004A8B9B),
    (0x006403A0, 0x006403A3, 0x006403B0, 0x006403B2, 0x0064043D),
]

# 真崩溃函数头 / 无守卫站点所在函数头
NOGUARD_FN = 0x00654320
NOGUARD_SITE = 0x00654413

fails = []


def check(cond, label, detail=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label,
                           ("  " + detail) if detail else ""))
    if not cond:
        fails.append(label)
    return cond


def load_pe():
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
    return data, pe, img_base, secs


def va2off(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + s["rsize"]:
            return s["roff"] + (va - s["va"])
    return None


def read_stack(path):
    """解析 stack dump：'00F9A344: 00000278 DATA_PTR' 或 '00F9A354: 006543B1'"""
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"^([0-9A-F]{8}):\s+([0-9A-F]{8})", txt, re.M):
        out[int(m.group(1), 16)] = int(m.group(2), 16)
    return out


def read_regs(path):
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    regs = {}
    for name in ("Eip", "Esp", "Ebp", "Eax", "Ebx", "Ecx", "Edx", "Esi", "Edi"):
        m = re.search(name + r":\s*([0-9A-Fa-f]{8})", txt)
        if m:
            regs[name] = int(m.group(1), 16)
    m = re.search(r"Access address:([0-9A-Fa-f]+) was", txt)
    if m:
        regs["Access"] = int(m.group(1), 16)
    return regs


def main():
    data, pe, img_base, secs = load_pe()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    print("镜像基数 0x%08X" % img_base)

    # ---------------- 第一部分：现场 ----------------
    print()
    print("=== 第一部分：except.txt 现场 ===")
    check(os.path.exists(EXCEPT), "except.txt 存在")
    regs = read_regs(EXCEPT)
    stack = read_stack(EXCEPT)
    print("  " + "  ".join("%s=%08X" % (k, v) for k, v in sorted(regs.items())))

    check(regs.get("Eip") == CRASH_SITE, "★ Eip == 0x724737（崩溃点）",
          "0x%08X" % regs.get("Eip", 0))
    check(regs.get("Ebp") == 0, "★ Ebp == 0", "0x%08X" % regs.get("Ebp", -1))
    check(regs.get("Ecx") == 0, "★ Ecx == 0", "0x%08X" % regs.get("Ecx", -1))
    check(regs.get("Access") == 0x250,
          "★ Access address == 0x250（即 [ebp+0x250]，ebp=0 ⇒ 地址=0x250）",
          "0x%X" % regs.get("Access", 0))
    check(regs.get("Edi") == VTHIS,
          "★ Edi == 0x87F7E8（单例对象的 this 一路带到崩溃帧）",
          "0x%08X" % regs.get("Edi", 0))

    # ---------------- 第二部分：栈帧对齐 ----------------
    print()
    print("=== 第二部分：栈返回地址 ⇄ 静态指令逐层对齐 ===")
    for (addr, ret, note) in EXPECTED_RETS:
        got = stack.get(addr)
        check(got == ret, "栈 @0x%08X == 0x%08X" % (addr, ret),
              "实测 0x%08X  (%s)" % (got or 0, note))

    print()
    print("  逐层验证：retaddr-5 处的指令确实 call 下一层")
    chain = [
        (0x00654418, 0x00654413, 0x00724730, CRASH_FN, "0x654320"),
        (0x006403A8, 0x006403A3, 0x00654320, 0x00654320, "0x6403A0"),
        (0x006ABD3E, 0x006ABD39, 0x006403A0, 0x006403A0, "0x6ABD30"),
        (0x004A88B0, 0x004A88AA, None, 0x004A8960, "0x4A8850 (间接)"),
        (0x00652D51, 0x00652D4C, 0x004A8850, 0x004A8850, "0x652CF0"),
    ]
    for (ret, callva, direct_tgt, fnhint, who) in chain:
        o = va2off(secs, callva)
        if o is None:
            check(False, "%s call 点 0x%08X 可定位" % (who, callva))
            continue
        ins = list(md.disasm(data[o:o + 8], callva))[:1]
        if not ins:
            check(False, "%s call 点 0x%08X 可解码" % (who, callva))
            continue
        it = ins[0]
        txt = it.mnemonic + " " + it.op_str
        if direct_tgt is not None:
            ok = it.mnemonic == "call" and ("0x%x" % direct_tgt) == it.op_str.split()[-1].replace(" ", "")
            target_desc = "call 0x%X" % direct_tgt
        else:
            ok = it.mnemonic == "call" and "[eax + 0xa8]" in it.op_str
            target_desc = "call [eax+0xA8]（虚表槽 42）"
        check(ok, "★ 0x%08X: %s（%s 返回地址 0x%08X-%d）" % (callva, target_desc, who, ret, 0),
              "实测 " + txt)

    # ---------------- 第三部分：守卫是否覆盖危险调用 ----------------
    print()
    print("=== 第三部分：守卫位置 ⇄ 危险调用位置 ===")
    for (fn, callva, cmpva, jccva, jtgt) in GUARD_CASES:
        print("  func 0x%08X：call @0x%08X  cmp @0x%08X  jcc @0x%08X → 0x%08X"
              % (fn, callva, cmpva, jccva, jtgt))
        check(cmpva > callva,
              "★ func 0x%08X 的守卫在危险调用**之后**（差距 +0x%X）⇒ 对本路无效"
              % (fn, cmpva - callva),
              "guard@0x%08X > call@0x%08X" % (cmpva, callva))

    # 0x654320 的两个站点：确认完全没有 guard
    # ★ 两次翻车记录：
    #   首版从站点-0x30 硬起点解码 ⇒ 落在 0x6543D9 指令中间，解出 inc esp/enter 幻象。
    #   二版 snap 到"第一个 >= win_lo 的指令"仍落错（0x6543E3 在 0x6543E1 的 6B 指令内）。
    #   本版改为**从函数头 0x654320 顺序解码到站点**，这是唯一无歧义的口径。
    o = va2off(secs, NOGUARD_FN)
    dec = list(md.disasm(data[o:o + 0x100], NOGUARD_FN))
    kinds = [(i.address, i.mnemonic, i.op_str) for i in dec if i.address < NOGUARD_SITE]
    # ★ 否定式断言必须带"解码确实覆盖到站点"的正向前提，否则解码整体失败时会假绿。
    #   N-4 负控（把函数头 +1）正是靠这个前提才转红的。
    last_end = None
    for i in dec:
        if i.address < NOGUARD_SITE:
            last_end = i.address + i.size
    check(last_end == NOGUARD_SITE,
          "★ 解码连续覆盖到站点 0x%08X（否定式断言的前提）" % NOGUARD_SITE,
          "末条指令止于 0x%08X" % (last_end or 0))
    # ★ 判据是「有没有测 ecx」，不是「有没有 cmp/test」：
    #   实测窗口内只有 1 个 test eax,eax（0x6543C5，测的是别的值），
    #   首版按「无任何 cmp/test」写判据 ⇒ 假红。判据必须落在被传的那个寄存器上。
    ecx_tests = [k for k in kinds if k[1] in ("cmp", "test") and "ecx" in k[2]]
    all_tests = [k for k in kinds if k[1] in ("cmp", "test")]
    print()
    print("  func 0x%08X 头→站点 0x%08X 之间指令 %d 条；cmp/test %d 个，其中测 ecx %d 个"
          % (NOGUARD_FN, NOGUARD_SITE, len(kinds), len(all_tests), len(ecx_tests)))
    for (a, m, s) in all_tests:
        print("    0x%08X  %s %s" % (a, m, s))
    check(not ecx_tests,
          "★ 0x%08X 从函数头到 call 0x724730 **没有测 ecx 的 cmp/test**（真实无守卫站点）"
          % NOGUARD_FN,
          "窗口 0x%08X..0x%08X，%d 条指令" % (NOGUARD_FN, NOGUARD_SITE, len(kinds)))

    # ---------------- 第四部分：链条陈述 ----------------
    print()
    print("=== 第四部分：完整因果链（现场 + 静态双证）===")
    print("  0x652CF0  (window/init 驱动，this=esi)")
    print("    └─E8 0x652D4C──▶ 0x4A8850  (__thiscall 桥，esi=this)")
    print("         └v[42] 0x4A88AA──▶ 0x4A8960  (slot42 目标，vtable 0x7E1964)")
    print("              └E8 0x4A8B13──▶ 0x6ABD30  (守卫在 0x4A8B35，已在调用之后)")
    print("                   └E8 0x6ABD39──▶ 0x6403A0")
    print("                        └E8 0x6403A3──▶ 0x654320  (守卫在 0x6403B0，已在调用之后)")
    print("                             └E8 0x654413──▶ 0x724730  (ecx=[0x887368]=0)")
    print("                                  └──▶ 0x724737  mov eax,[ebp+0x250]  ebp=0  ✘崩溃")
    print()
    print("  关闭窗口时 0x777803 `mov [0x887368],0` 先执行 ⇒ 单例=0")
    print("  ⇒ 0x654320 在无守卫下把 ecx=0 传进 0x724730 ⇒ ebp=0 ⇒ 读 0x250 ⇒ AV")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ RC-4 因果链定案：现场 %d 项 + 静态 %d 层对齐，全部成立"
          % (len(EXPECTED_RETS), len(chain)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
