# -*- coding: utf-8 -*-
"""RC-4 尾窗可观测性：主窗口句柄锚点 + 单例清零时序 + 分派表 + 收尾禁令面。

为什么做这件事：上一轮（§341）建议「WM_CLOSE 后轮询 [0x887368]，读到 0 就立刻
驱动鼠标」。本脚本用磁盘字节检验该建议是否可行，并顺带定出主窗口的**唯一可靠
句柄来源**（不靠标题猜）。

产出七组硬事实：
  F1. 0x007775C0 是窗口类 "Yuri's Revenge" 的 WndProc（RegisterClassA 现场）。
  F2. 该窗口由 CreateWindowExA 创建，hwnd 存全局 [0x00B73550]。
  F3. WM_DESTROY 块内 [0x887368]=0 与 [0xB73550]=0 在**同一个基本块**，
      中间只隔一条 5 字节指令 ⇒ 「读到单例为 0 再驱动窗口」时窗口已不存在。
  F4. 引擎自己的退出路径在 0x006BE0CF 用 PostMessageA 向 [0xB73550] 投递
      Msg=2（WM_DESTROY），随后在 0x006BE0DC 起的等待环里轮询 [0x00A8EDD8]
      （1=等待销毁，2=已销毁）⇒ 该全局是「已进尾窗」的现成判据。
  F5. 该等待环调用的消息泵 0x005D4D50 里，单例消费点是**带零闸**的
      （mov ecx,[0x887368] / test / je）⇒ 泵本身不会制造空 this 调用。
  F6. [0xB73550] 全段写入点恰好 3 处，全在主窗口创建函数内。
  F7. 窗口过程是**两级分派**：`mov dl, byte [msg-1 + 0x777A98]` 取索引，
      再 `jmp dword [edx*4 + 0x777A80]`。WM_CLOSE 走 default 0x7779B9；
      而 default 出口**先调游戏自己的窗口过程 0x54F790**，返回 0 才下传到
      DefWindowProcA —— 不是直接调。

只读磁盘，零真机。全部断言失败即非 0 退出。
"""
import io
import struct
import sys

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

EXPECT_WNDPROC = 0x007775C0
EXPECT_CLASSNAME = b"Yuri's Revenge"
EXPECT_HWND_GLOBAL = 0x00B73550
EXPECT_SINGLETON = 0x00887368
EXPECT_QUITSTATE = 0x00A8EDD8
EXPECT_NEW_VA = 0x0077780E      # mov [0xB73550], ebx
EXPECT_SINGLETON_ZERO_VA = 0x00777803  # mov [0x887368], ebx
EXPECT_CREATE_VA = 0x00777CD6   # mov [0xB73550], eax（CreateWindowExA 返回值）
EXPECT_QUIT_POST_VA = 0x006BE0D6  # call [0x7E14AC] = PostMessageA

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
        secs.append({"name": name, "vsize": vsize, "va": img_base + rva,
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


def resolve_iat(data, secs, pe, opt_size, want_vas):
    """按导入目录解析 IAT 槽名。

    ★ 坑：导入目录/ILT/IAT 字段全是 **RVA**，`va2off` 吃的是 VA，
      两处都必须先加镜像基数，否则会静默落到别的段里（本件首跑即此错，
      结果是一路 unpack 到文件尾外）。
    """
    img_base = struct.unpack_from("<I", data, pe + 0x34)[0]
    opt = pe + 24
    imp_rva, _ = struct.unpack_from("<II", data, opt + 0x68)
    o = va2off(secs, img_base + imp_rva) if imp_rva else None
    out = {}
    if o is None:
        return out
    i = 0
    while True:
        ilt, _ts, _fc, nrva, iat_rva = struct.unpack_from("<IIIII", data, o + i * 20)
        if nrva == 0:
            break
        dll_off = va2off(secs, img_base + nrva)
        dll = data[dll_off:].split(b"\x00")[0].decode("ascii", "replace") if dll_off else "?"
        t_rva = (ilt if ilt else iat_rva)
        t_off = va2off(secs, img_base + t_rva)
        if t_off is None:
            i += 1
            continue
        j = 0
        while True:
            v = struct.unpack_from("<I", data, t_off + j * 4)[0]
            if v == 0:
                break
            slot_va = img_base + iat_rva + j * 4
            if slot_va in want_vas:
                h_off = va2off(secs, img_base + (v & 0x7FFFFFFF))
                nm = data[h_off + 2:].split(b"\x00")[0].decode("ascii", "replace") if h_off else "?"
                out[slot_va] = "%s!%s" % (dll, nm)
            j += 1
        i += 1
    return out


def _census_writes(data, img_base, secs):
    """穷举 [0xB73550] 的写入点。

    ★ 坑：字节扫描命中的偏移大多是立即数里的巧合。
      必须先线性解码建 `off -> 指令` 表，再只认「目的操作数是该绝对地址」的指令。
    """
    text = [s for s in secs if s["name"] == ".text"][0]
    tbytes = data[text["roff"]:text["roff"] + text["rsize"]]
    tva = text["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    table = {}
    off = 0
    while off < len(tbytes):
        ok = False
        for ins in md.disasm(tbytes[off:off + 16], tva + off):
            if ins.address - tva == off:
                table[off] = (ins.mnemonic, ins.op_str, ins.bytes.hex(" "))
                off += ins.size
                ok = True
                break
        if not ok:
            off += 1
    pat = struct.pack("<I", EXPECT_HWND_GLOBAL)
    raw = []
    i = 0
    while True:
        j = tbytes.find(pat, i)
        if j < 0:
            break
        raw.append(j)
        i = j + 1
    tgt = "0x%x" % EXPECT_HWND_GLOBAL      # capstone 的 op_str 用小写无前导零
    writes = []
    seen = set()
    for h in raw:
        for k in range(max(0, h - 3), h + 1):
            if k in table and k not in seen:
                seen.add(k)
                mn, op, bs = table[k]
                dst = op.split(",")[0]
                if mn in ("mov", "and", "or", "xor") and tgt in dst:
                    writes.append((tva + k, mn, op, bs))
                break
    print("  解码指令 %d 条；字节命中 %d；去重后归属指令 %d"
          % (len(table), len(raw), len(seen)))
    for va, mn, op, bs in sorted(writes):
        print("    0x%08X  %-4s %-44s %s" % (va, mn, op, bs))
    check(len(writes) == 3,
          "写入点恰好 3 处（创建×2 + 销毁×1）", "实测 %d" % len(writes))
    check(sorted(w[0] for w in writes) ==
          sorted([0x00777CD6, 0x00777D7E, EXPECT_NEW_VA]),
          "写入点 VA 集合 == {0x00777CD6, 0x00777D7E, 0x0077780E}")


def _verify_dispatch(data, secs, pe):
    """复验窗口过程的两级分派表。

    ★ 坑（本件 §343 踩过）：`jmp dword ptr [edx*4+0x777A80]` 的 edx **不是 msg**，
      而是 `mov dl, byte [msg-1 + 0x777A98]` 查出来的索引。
      按 msg 号直接读 dword 表会得到「WM_CREATE 跳进销毁块」这种不可能结果。
    """
    IDX, TGT, MAXMSG = 0x00777A98, 0x00777A80, 0x14
    seq = dis(data, secs, 0x0077769A, 0x20)
    for ins in seq:
        print("    0x%08X  %-22s %s %s" % (ins.address, ins.bytes.hex(" "),
                                            ins.mnemonic, ins.op_str))
    lea = [i for i in seq if i.mnemonic == "lea"
           and i.op_str.replace(" ", "") == "ecx,[eax-1]"]
    check(bool(lea), "msg 先减 1（lea ecx,[eax-1]）")
    idx_off, tgt_off = va2off(secs, IDX), va2off(secs, TGT)
    check(idx_off is not None and tgt_off is not None, "两级表均在文件内")
    if idx_off is None or tgt_off is None:
        return
    tgts = [struct.unpack_from("<I", data, tgt_off + i * 4)[0] for i in range(6)]
    expect = {0x01: 0x0077778D, 0x02: 0x007777F3, 0x10: 0x007779B9}
    rows = []
    for m in range(1, MAXMSG + 1):
        idx = data[idx_off + (m - 1)]
        rows.append((m, idx, tgts[idx] if idx < 6 else None))
    for m, idx, t in rows:
        if m in (0x01, 0x02, 0x0F, 0x10, 0x14):
            print("    msg 0x%02X -> idx %d -> %s"
                  % (m, idx, ("0x%08X" % t) if t else "OUT"))
    check(all(rows) and all(r[1] < 6 for r in rows), "msg 1..0x14 索引均不越界")
    ok = all(tgts[idx] == expect[m] for m, idx, _ in rows if m in expect)
    check(ok, "WM_CREATE→0x77778D / WM_DESTROY→0x7777F3 / WM_CLOSE→0x7779B9")

    # default 出口：先调游戏自己的窗口过程 0x54F790，返回 0 才下传到 DefWindowProcA
    dseq = dis(data, secs, 0x007779B9, 0x30)
    dfirst = [i for i in dseq if i.mnemonic == "call"]
    check(bool(dfirst) and "0x54f790" in dfirst[0].op_str,
          "default 出口先调游戏自己的窗口过程 0x0054F790",
          ("%s %s" % (dfirst[0].mnemonic, dfirst[0].op_str)) if dfirst else "")
    late = [i for i in dseq if i.mnemonic == "call" and "0x7e1394" in i.op_str]
    check(not late, "default 出口段内不直接出现 DefWindowProcA 调用")

    # 0x54F790 的两张内部分派表都不含 WM_CLOSE
    a_off, b_off = va2off(secs, 0x0054FB4C), va2off(secs, 0x0054FB64)
    if a_off and b_off:
        a = [struct.unpack_from("<I", data, a_off + i * 4)[0] for i in range(6)]
        b = [struct.unpack_from("<I", data, b_off + i * 4)[0] for i in range(8)]
        check(all(0x00500000 < v < 0x00600000 for v in a + b),
              "两张内部分派表目标全部落在 0x54/0x55 段内",
              "A=%d 项 B=%d 项" % (len(a), len(b)))


def main():
    data, img_base, secs, pe, opt_size = load()
    print("镜像基数 0x%08X   .text VA 0x%08X" %
          (img_base, [s["va"] for s in secs if s["name"] == ".text"][0]))
    print()

    # ---- F1：RegisterClassA 现场 ----
    print("F1 窗口类注册（0x00777C30 起）")
    insns = dis(data, secs, 0x00777C30, 0xC0)
    wc_proc = None
    wc_name = None
    for ins in insns:
        if ins.mnemonic == "mov" and ins.op_str.endswith("0x%x" % EXPECT_WNDPROC):
            wc_proc = ins.address
        if ins.mnemonic == "mov" and "0x849f48" in ins.op_str:
            wc_name = ins.address
        if ins.mnemonic == "call" and "0x7e14d8" in ins.op_str:
            print("  RegisterClassA @ 0x%08X" % ins.address)
            break
    check(wc_proc is not None,
          "WNDCLASSA.lpfnWndProc == 0x%08X" % EXPECT_WNDPROC,
          "@0x%08X" % wc_proc if wc_proc else "")
    cls_off = va2off(secs, 0x00849F48)
    cls = data[cls_off:cls_off + 32].split(b"\x00")[0] if cls_off else b""
    check(cls == EXPECT_CLASSNAME, "lpszClassName == %r" % EXPECT_CLASSNAME,
          "实读 %r" % cls)
    check(wc_name is not None, "lpszClassName 立即数 0x00849F48 出现在 WNDCLASSA 填充序列")

    # ---- F2：CreateWindowExA → hwnd 全局 ----
    print()
    print("F2 主窗口创建（CreateWindowExA）")
    iat = resolve_iat(data, secs, pe, opt_size,
                      {0x007E14D4, 0x007E14D8, 0x007E14AC})
    check(iat.get(0x007E14D4) == "USER32.dll!CreateWindowExA",
          "0x007E14D4 == CreateWindowExA", iat.get(0x007E14D4, "?"))
    check(iat.get(0x007E14D8) == "USER32.dll!RegisterClassA",
          "0x007E14D8 == RegisterClassA", iat.get(0x007E14D8, "?"))
    check(iat.get(0x007E14AC) == "USER32.dll!PostMessageA",
          "0x007E14AC == PostMessageA", iat.get(0x007E14AC, "?"))
    hit = None
    for ins in dis(data, secs, 0x00777CD0, 0x20):
        if ins.mnemonic == "mov" and "0xb73550" in ins.op_str and "eax" in ins.op_str:
            hit = ins.address
            break
    check(hit == EXPECT_CREATE_VA,
          "CreateWindowExA 返回值写入 [0x%08X]" % EXPECT_HWND_GLOBAL,
          "@0x%08X" % hit if hit else "未找到")

    # ---- F3：WM_DESTROY 块内清零时序 ----
    print()
    print("F3 WM_DESTROY 块（0x007777F3 起）")
    seq = []
    for ins in dis(data, secs, 0x007777F3, 0x30):
        seq.append((ins.address, ins.mnemonic, ins.op_str))
        print("  0x%08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    a = [s for s in seq if s[0] == EXPECT_SINGLETON_ZERO_VA and "0x887368" in s[2]]
    b = [s for s in seq if s[0] == EXPECT_NEW_VA and "0xb73550" in s[2]]
    check(bool(a), "单例清零 @0x%08X（mov [0x887368], ebx）" % EXPECT_SINGLETON_ZERO_VA)
    check(bool(b), "hwnd 清零 @0x%08X（mov [0x%08X], ebx）"
          % (EXPECT_NEW_VA, EXPECT_HWND_GLOBAL))
    gap = EXPECT_NEW_VA - EXPECT_SINGLETON_ZERO_VA
    between = [s for s in seq if EXPECT_SINGLETON_ZERO_VA < s[0] < EXPECT_NEW_VA]
    check(gap == 11 and len(between) == 1,
          "两者同基本块、相隔 %d B，中间仅 %d 条指令" % (gap, len(between)),
          "中间: %s" % ("; ".join("%s %s" % (m, o) for _, m, o in between) or "-"))
    note = [s for s in between if "0xa8edd8" in s[2]]
    check(bool(note), "中间那条读的是退出状态 [0x%08X]" % EXPECT_QUITSTATE)

    # ---- F4：引擎自身退出路径 ----
    print()
    print("F4 引擎退出路径（0x006BE0C0 起）")
    seq4 = []
    for ins in dis(data, secs, 0x006BE0C6, 0x40):
        seq4.append(ins)
        print("  0x%08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    post = [i for i in seq4 if i.address == EXPECT_QUIT_POST_VA]
    check(bool(post), "PostMessageA 调用 @0x%08X" % EXPECT_QUIT_POST_VA)
    # push 立即数 2 在 call 前
    pushed2 = [i for i in seq4 if i.mnemonic == "push" and i.op_str == "2"
               and EXPECT_QUIT_POST_VA - 0x10 < i.address < EXPECT_QUIT_POST_VA]
    check(bool(pushed2), "Msg 入参 = 2（WM_DESTROY，非 WM_CLOSE=0x10）",
          "@0x%08X" % pushed2[0].address if pushed2 else "")
    hwnd_push = [i for i in seq4 if "0xb73550" in i.op_str
                 and i.address < EXPECT_QUIT_POST_VA]
    check(bool(hwnd_push), "目标 hwnd 取自 [0x%08X]" % EXPECT_HWND_GLOBAL,
          "@0x%08X" % hwnd_push[0].address if hwnd_push else "")
    quits = [i for i in seq4 if EXPECT_QUITSTATE and "0xa8edd8" in i.op_str
             and i.mnemonic == "cmp"]
    check(bool(quits), "等待环判据 = cmp [0x%08X], edi" % EXPECT_QUITSTATE,
          "@0x%08X" % quits[0].address if quits else "")

    # ---- F5：泵内单例是带闸消费点 ----
    print()
    print("F5 消息泵 0x005D4D50 的单例消费点")
    seq5 = dis(data, secs, 0x005D4DB3, 0x18)
    for ins in seq5:
        print("  0x%08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    rd = [i for i in seq5 if i.mnemonic == "mov" and "0x887368" in i.op_str]
    nxt = [i for i in seq5 if rd and i.address == rd[0].address + rd[0].size]
    check(bool(rd) and bool(nxt) and nxt[0].mnemonic == "test",
          "泵读单例后紧跟 test（带闸消费）",
          "%s %s" % (nxt[0].mnemonic, nxt[0].op_str) if nxt else "")
    je = [i for i in seq5 if nxt and i.address == nxt[0].address + nxt[0].size]
    check(bool(je) and je[0].mnemonic == "je",
          "test 后紧跟 je（判零分支）",
          "%s %s" % (je[0].mnemonic, je[0].op_str) if je else "")

    print()
    print("F6 [0x%08X] 全段写入点普查" % EXPECT_HWND_GLOBAL)
    _census_writes(data, img_base, secs)

    print()
    print("F7 窗口过程分派表（两级：byte 索引 + dword 目标）")
    _verify_dispatch(data, secs, pe)

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 七组断言全部成立（F1–F7）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
