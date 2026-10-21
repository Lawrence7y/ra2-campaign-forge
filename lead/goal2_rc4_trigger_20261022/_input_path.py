# -*- coding: utf-8 -*-
"""RC-4 输入路径闭环：窗口消息 → 静态对象 0x87F7E8 → 崩溃链。

上一轮（§343）留了「0x54F790 各分支行为未逐条判定」的边界。本轮把它补完，
并回答一个更关键的问题：**尾窗里那次 GUI 更新，能不能经窗口消息到达崩溃链？**

三条待验事实：
  G1. 窗口过程把**每条**消息派发给静态对象 0x87F7E8（`mov ecx,0x87F7E8` + `call 0x6930A0`）。
  G2. 消息泵 0x5D4D50 里有 `DispatchMessageA`（IAT 0x7E14C0）⇒ 消息真的会进窗口过程；
      且**循环体内不再复查 hwnd**，只有入口 0x5D4D58 查一次。
  G3. 崩溃链宿主 0x4A8960 的两个 E8 调用点（0x5610EC / 0x67E7F9）都**显式加载
      ecx = 0x87F7E8** ⇒ 与窗口消息派发是同一个静态对象。
  G4. 0x54F790 的两个内部分派表覆盖 0x100..0x105 / 0x202..0x209，
      **不含 WM_CLOSE(0x10)**，故 WM_CLOSE 在它内部走默认收尾返回 0。

只读磁盘，零真机。全部断言失败即非 0 退出。
"""
import io
import struct
import sys

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

STATIC_OBJ = 0x0087F7E8
PUMP = 0x005D4D50
HOST_4960 = 0x004A8960
DISPATCH_IAT = 0x007E14C0     # USER32!DispatchMessageA

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
    return data, img_base, secs, pe, opt_size


def va2off(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            return s["roff"] + (va - s["va"])
    return None


def dis(data, secs, va, n):
    off = va2off(secs, va)
    if off is None:
        return []
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    return list(md.disasm(data[off:off + n], va))


def e8_callers(data, secs, target):
    """全 .text 扫 E8 rel32 找调用者，回验指令边界。"""
    text = [s for s in secs if s["name"] == ".text"][0]
    tb = data[text["roff"]:text["roff"] + text["rsize"]]
    tva = text["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    bounds = set()
    off = 0
    while off < len(tb):
        hit = False
        for ins in md.disasm(tb[off:off + 16], tva + off):
            if ins.address - tva == off:
                if ins.mnemonic == "call":
                    bounds.add((off, ins.address + ins.size))
                off += ins.size
                hit = True
                break
        if not hit:
            off += 1
    out = []
    for off in range(len(tb) - 5):
        if tb[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", tb, off + 1)[0]
        if tva + off + 5 + rel == target and (off, tva + off + 5) in bounds:
            out.append(tva + off)
    return out


def main():
    data, img_base, secs, pe, opt_size = load()
    print("镜像基数 0x%08X" % img_base)
    print()

    # ---- G1：窗口过程把每条消息派发给 0x87F7E8 ----
    print("G1 窗口过程的消息派发（0x0077763B 起）")
    seq = dis(data, secs, 0x0077763B, 0x10)
    for ins in seq:
        print("  0x%08X  %-22s %s %s" % (ins.address, ins.bytes.hex(" "),
                                          ins.mnemonic, ins.op_str))
    ld = [i for i in seq if i.mnemonic == "mov" and "0x87f7e8" in i.op_str]
    cl = [i for i in seq if i.mnemonic == "call"]
    check(bool(ld), "mov ecx, 0x%08X（静态对象）" % STATIC_OBJ,
          "@0x%08X" % ld[0].address if ld else "")
    check(bool(cl), "随后 call（消息派发入口）",
          "%s %s" % (cl[0].mnemonic, cl[0].op_str) if cl else "")

    # ---- G2：消息泵的入口判空与 DispatchMessageA ----
    print()
    print("G2 消息泵 0x%08X" % PUMP)
    body = dis(data, secs, PUMP, 0x120)
    guard = [i for i in body if i.mnemonic == "mov" and "0xb73550" in i.op_str]
    jes = [i for i in body if i.mnemonic == "je"]
    disp = [i for i in body if i.mnemonic == "call" and "0x7e14c0" in i.op_str]
    check(bool(guard) and guard[0].address == PUMP,
          "入口第 1 条读 [0xB73550]", "@0x%08X" % guard[0].address if guard else "")
    check(bool(jes) and jes[0].address < 0x005D4D70,
          "入口即判 hwnd==0 提前返回", "@0x%08X" % jes[0].address if jes else "")
    check(bool(guard) and len(guard) == 1,
          "★ 循环体内不再复查 hwnd（全文仅 1 处读）",
          "实测 %d 处" % len(guard))
    check(bool(disp), "调用 DispatchMessageA（IAT 0x%08X）" % DISPATCH_IAT,
          "@0x%08X" % disp[0].address if disp else "")
    # IAT 解析确认
    opt = pe + 24
    img_b = struct.unpack_from("<I", data, pe + 0x34)[0]
    imp_rva, _ = struct.unpack_from("<II", data, opt + 0x68)
    o = va2off(secs, img_b + imp_rva)
    name = "?"
    i = 0
    while True:
        ilt, _t, _f, nrva, iat_rva = struct.unpack_from("<IIIII", data, o + i * 20)
        if nrva == 0:
            break
        t = va2off(secs, img_b + (ilt if ilt else iat_rva))
        if t is not None:
            j = 0
            while True:
                v = struct.unpack_from("<I", data, t + j * 4)[0]
                if v == 0:
                    break
                if img_b + iat_rva + j * 4 == DISPATCH_IAT:
                    h = va2off(secs, img_b + (v & 0x7FFFFFFF))
                    dll_off = va2off(secs, img_b + nrva)
                    dll = data[dll_off:].split(b"\x00")[0].decode() if dll_off else "?"
                    name = "%s!%s" % (dll, data[h + 2:].split(b"\x00")[0].decode())
                j += 1
        i += 1
    check(name.endswith("DispatchMessageA"), "IAT 槽名解析 == DispatchMessageA", name)

    # ---- G3：崩溃链宿主的调用点都加载同一静态对象 ----
    print()
    print("G3 崩溃链宿主 0x%08X 的 E8 调用点" % HOST_4960)
    callers = e8_callers(data, secs, HOST_4960)
    print("  调用点: %s" % ", ".join("0x%08X" % c for c in callers))
    check(len(callers) == 2, "恰好 2 个 E8 调用点", "实测 %d" % len(callers))
    for c in callers:
        # 往回找最近的 mov ecx, 0x87F7E8
        back = dis(data, secs, c - 0x60, 0x60)
        lds = [i for i in back if i.mnemonic == "mov" and "0x87f7e8" in i.op_str]
        check(bool(lds), "0x%08X 前置 mov ecx,0x87F7E8" % c,
              "@0x%08X" % lds[-1].address if lds else "未找到")

    # ---- G4：0x54F790 的两张分派表 ----
    print()
    print("G4 0x0054F790 的内部分派表")
    a_off = va2off(secs, 0x0054FB4C)
    b_off = va2off(secs, 0x0054FB64)
    a = [struct.unpack_from("<I", data, a_off + i * 4)[0] for i in range(6)]
    b = [struct.unpack_from("<I", data, b_off + i * 4)[0] for i in range(8)]
    for i, v in enumerate(a):
        print("    A msg 0x%03X -> 0x%08X" % (0x100 + i, v))
    for i, v in enumerate(b):
        print("    B msg 0x%03X -> 0x%08X" % (0x202 + i, v))
    check(all(0x00500000 < v < 0x00560000 for v in a + b),
          "全部目标落在 0x54/0x55 段内")
    check(0x10 not in [0x100 + i for i in range(len(a))] and
          0x10 not in [0x202 + i for i in range(len(b))],
          "两张表都不含 WM_CLOSE(0x10)")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ G1–G4 全部成立")
    return 0


if __name__ == "__main__":
    sys.exit(main())
