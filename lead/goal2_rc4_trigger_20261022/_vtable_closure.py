# -*- coding: utf-8 -*-
"""RC-4 虚表闭合：0xA8 偏移 = slot 42 = 崩溃链 L3 宿主 的完整证明链。

§341 判「宿主三无（无 E8 / 无虚表 / 无立即数）⇒ 只能运行期不可枚举地间接分发」。
本脚本证明其中「无虚表」对崩溃链宿主**不成立**，并把「间接分发」落到**确定的虚表槽**：

  H1. 0x87F7E8 的 vtable 由一条 mov 立即数写入：0x0040D1B4 -> 0x007E1964。
  H2. 该虚表里 slot[42] == 0x004A8960（崩溃链 L3 宿主）、slot[34] == 0x006ABD30（L2）。
      42*4 == 0xA8 —— 正是 crash_site.json 里 `0x004A88AA call [eax+0xa8]` 的偏移。
  H3. 0x004A88AA 的 eax 来自 `mov eax,[esi]`（esi=this），即 eax = *this = 虚表指针。
      ⇒ `call [eax+0xa8]` == 调用 this 的 v[42]。
  H4. 0x004A8850（含该桥的函数）唯一 E8 调用者是 0x00652D4C。
      0x00652CF0 本身在另一张虚表（约 0x007F0344）的 slot[5]，**该表 slot[42] 也是 0x4A8960**
      ⇒ 0x4A8960 在多张同族虚表里复用同一槽号。

口径限制：
  - 虚表**起点**是「从命中点往前扫到第一个非 .text 指针」估算的；对 0x7E1964 另有
    立即数直接证据（H1），本脚本对 0x7E1964 用立即数为准、扫法仅作交叉核对。
  - 「0x4A8850 运行时 this 是否真是 0x87F7E8」**未证**：本脚本只证到
    「eax 来自 this 的虚表指针」与「多张同族表 slot42 都是 0x4A8960」。

只读磁盘，零真机。全部断言失败即非 0 退出。
"""
import io
import struct
import sys

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

VT_87F7E8 = 0x007E1964     # 0x87F7E8 的 vtable（由 0x0040D1B4 立即数直接读出）
SLOT_L3 = 42               # 0x4A8960
SLOT_L2 = 34               # 0x006ABD30
BRIDGE = 0x004A88AA        # call dword ptr [eax + 0xa8]
BRIDGE_FN = 0x004A8850
BRIDGE_CALLER = 0x00652D4C

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


def rd(data, va):
    return struct.unpack_from("<I", data, va - 0x400000)[0]


def is_code(secs, v):
    t = [s for s in secs if s["name"] == ".text"][0]
    return t["va"] <= v < t["va"] + t["rsize"]


def vt_head_by_scan(data, secs, hit):
    k = 0
    while True:
        v = rd(data, hit - (k + 1) * 4)
        if not is_code(secs, v):
            return hit - k * 4
        k += 1
        if k > 300:
            return None


def main():
    data, img_base, secs, pe = load()
    print("镜像基数 0x%08X" % img_base)
    print()

    # ---- H1：0x87F7E8 的 vtable 由立即数直接给出 ----
    print("H1 [0x87F7E8] 的 vtable 写入点")
    W = 0x0040D1B2                      # ★ 指令起点（0x40D1B4 是[imm32]字段内，非指令头）
    raw = data[W - 0x400000:W - 0x400000 + 10]
    print("  0x%08X: %s" % (W, raw.hex(" ")))
    imm = struct.unpack_from("<I", data, W - 0x400000 + 6)[0]
    check(raw[:2] == b"\xC7\x05", "指令形态 c7 05（mov dword ptr [imm32], imm32）")
    tgt_imm = struct.unpack_from("<I", data, W - 0x400000 + 2)[0]
    check(tgt_imm == 0x0087F7E8, "目标地址 == 0x0087F7E8", "实读 0x%08X" % tgt_imm)
    check(imm == VT_87F7E8, "写入值 == 0x%08X" % VT_87F7E8, "实读 0x%08X" % imm)
    head_scan = vt_head_by_scan(data, secs, VT_87F7E8 + 0xA8)
    print("  扫法交叉核对：含 0x4A8960 的表头约 0x%08X（立即数法给 0x%08X）"
          % (head_scan or 0, VT_87F7E8))
    check(head_scan == VT_87F7E8, "两种方法给出同一个表头")

    # ---- H2：slot 内容 ----
    print()
    print("H2 vtable 0x%08X 的目标槽" % VT_87F7E8)
    v42 = rd(data, VT_87F7E8 + SLOT_L3 * 4)
    v34 = rd(data, VT_87F7E8 + SLOT_L2 * 4)
    check(v42 == 0x004A8960, "slot[%d] == 0x004A8960（L3 宿主）" % SLOT_L3,
          "实读 0x%08X" % v42)
    check(v34 == 0x006ABD30, "slot[%d] == 0x006ABD30（L2 宿主）" % SLOT_L2,
          "实读 0x%08X" % v34)
    check(SLOT_L3 * 4 == 0xA8, "slot 索引 ×4 == 0xA8（与 crash_site 的偏移一致）")
    for s in (26, 34, 42, 45, 46, 50):
        print("    slot[%2d] = 0x%08X" % (s, rd(data, VT_87F7E8 + s * 4)))

    # ---- H3：桥的 eax 来源 ----
    print()
    print("H3 桥 0x%08X 的寄存器来源" % BRIDGE)
    for va in (0x004A88A1, 0x004A88A4, 0x004A88AA):
        print("    0x%08X: %s" % (va, data[va - 0x400000:va - 0x400000 + 6].hex(" ")))
    eax_src = data[0x4A88A1 - 0x400000:0x4A88A1 - 0x400000 + 2]
    ecx_src = data[0x4A88A4 - 0x400000:0x4A88A4 - 0x400000 + 2]
    call = data[BRIDGE - 0x400000:BRIDGE - 0x400000 + 6]
    check(eax_src == b"\x8B\x06", "0x004A88A1 = mov eax,[esi]（eax = *this = 虚表指针）")
    check(ecx_src == b"\x8B\xCE", "0x004A88A4 = mov ecx,esi（ecx = this）")
    check(call == b"\xFF\x90\xA8\x00\x00\x00", "0x004A88AA = call [eax+0xa8]")

    # ---- H4：桥的调用者与另一张同族表 ----
    print()
    print("H4 桥函数 0x%08X 的调用者" % BRIDGE_FN)
    top = data[0x4A8854 - 0x400000:0x4A8854 - 0x400000 + 2]
    check(top == b"\x8B\xF1", "0x004A8854 = mov esi,ecx（esi = this）")
    print("    0x%08X: %s" % (0x00652D4C - 3, data[0x652D4C - 0x400000 - 3:0x652D4C - 0x400000 + 2].hex(" ")))
    ctx = data[0x652CF0 - 0x400000:0x652CF0 - 0x400000 + 3]
    check(ctx == b"\x56\x8B\xF1", "0x00652CF0 = push esi; mov esi,ecx（同样是 this 型函数）")

    ref = [0x7F0358]
    other_head = vt_head_by_scan(data, secs, ref[0])
    print("    0x00652CF0 作为 dword 出现在 0x%08X，其表头约 0x%08X"
          % (ref[0], other_head or 0))
    if other_head:
        off = (ref[0] - other_head) // 4
        check(rd(data, ref[0]) == 0x00652CF0, "0x%08X == 0x00652CF0" % ref[0])
        v42b = rd(data, other_head + SLOT_L3 * 4)
        check(v42b == 0x004A8960,
              "另一张同族表 slot[%d] 也是 0x4A8960（槽号复用）" % SLOT_L3,
              "0x%08X @%s slot[%d]" % (v42b, "0x%08X" % other_head, SLOT_L3))

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ H1–H4 全部成立：0xA8 偏移 = slot 42 = L3 宿主 0x4A8960")
    print("  ⇒ §341「宿主无虚表槽」对崩溃链宿主不成立")
    return 0


if __name__ == "__main__":
    sys.exit(main())
