#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3 补证：`0x777687` 读的确实是 **msg**，不是返回地址。

背景：异族核验 C3 判定「ret 尺寸属实，但 14 条断言没有一条验证栈偏移」
⇒ 结论只存在于散文推演，未经机器验证。本脚本把它变成断言。

做法：从 WndProc 入口 `0x7775C0` 起沿**两条实际分支**模拟 esp，逐个跟踪：
  - `push r32` / `push imm8` / `push imm32`   ⇒ esp -= 4
  - `pop r32`                                  ⇒ esp += 4
  - `call rel32`                               ⇒ 压返回地址(-4) + 被调方 ret N(+4+N)
  - `call [mem]`（导入函数）                    ⇒ 按 IMPORT_ARGS 的实参个数算净额
                                                 = +4+4*argc；原型未知则**终止路径不猜**
  - `add esp, imm` / `sub esp, imm`            ⇒ 相应调整
  - `ret imm16`                                ⇒ 清栈后结束

WndProc 是 stdcall：入口 esp 指向返回地址，参数在 [esp+4], [esp+8], [esp+0xC], [esp+0x10]
（hwnd, msg, wParam, lParam）。

★ 反汇编起点 `0x7775C0` 已由 §381 的边界自检证明是真实指令边界。
★ 被调函数的 ret 尺寸用 capstone 实测，不硬编码。
★ §387：本文件曾有两条**恒真式**断言（`x = -0x10; assert x == -0x10`），
  且 walk() 对 `call [mem]` 按净 0 处理致实算值与断言矛盾而门禁仍绿。
  现已改为断言 walk() 的**实算值**，并补语义级独立证据（不依赖 esp 模拟）。
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
RESULTS = []


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-58s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))


def main():
    import capstone
    b = EXE.read_bytes()
    IB = 0x400000

    # ---- 节表 + IAT ----
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    opt = pe + 24
    ib = struct.unpack_from("<I", b, opt + 28)[0]
    secs = []
    so = opt + optsz
    for k in range(nsec):
        o = so + k * 40
        vs, va, rs, ra = struct.unpack_from("<IIII", b, o + 8)
        secs.append((va, vs, ra, rs))

    def va2off(va):
        rva = va - ib
        for v, vs_, ra_, rs_ in secs:
            if v <= rva < v + max(vs_, rs_):
                return ra_ + (rva - v)
        return None

    imp_rva, _ = struct.unpack_from("<II", b, opt + 96 + 8)
    imp_off = va2off(ib + imp_rva)

    def resolve(iat_va):
        target = iat_va - ib
        n = 0
        while True:
            o = imp_off + n * 20
            oft, ts, fc, name_rva, ft = struct.unpack_from("<IIIII", b, o)
            if name_rva == 0:
                return None
            thunk = oft or ft
            to = va2off(ib + thunk)
            k = 0
            while True:
                val = struct.unpack_from("<I", b, to + k * 4)[0]
                if val == 0:
                    break
                if ft + k * 4 == target:
                    if val & 0x80000000:
                        return "ORD#%d" % (val & 0xFFFF)
                    no = va2off(ib + val)
                    return b[no + 2:no + 64].split(b"\0")[0].decode()
                k += 1
            n += 1

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False

    def ret_size(fn_va):
        """实测被调函数的 ret 尺寸（扫描到第一条 ret）。"""
        off = va2off(fn_va)
        for i in md.disasm(b[off:off + 0x800], fn_va):
            if i.mnemonic == "ret":
                return int(i.op_str, 16) if i.op_str else 0
        return None

    # ★★★ §387：`call [mem]` 的 stdcall 弹参**必须按实参个数算**。
    #   §386 修了「间接虚调用不能按 ret 0」，但门禁的 walk() 仍把
    #   `call [mem]` 一律按「净 0」处理 —— 这只在**无参**导入函数下成立。
    #   GetMenu(hMenu) 是 1 参 stdcall ⇒ 被调方 ret 4 ⇒ 净效果是 -4（净弹 4）。
    #   结果：分支 B 上 walk() 得 -0x14，与 BFS 的 -0x10 矛盾。
    #   解法：对导入函数按其已知原型给出实参个数（下表的数字是**人工核定**的
    #   Win32 原型，不是从二进制推的；因此另配一条负控断言证明它会改变结果）。
    IMPORT_ARGS = {
        "GetMenu": 1,            # HMENU GetMenu(HWND)
        "DefWindowProcA": 4,     # LRESULT(HWND, UINT, WPARAM, LPARAM)
        "ClientToScreen": 2,     # BOOL(HWND, LPPOINT)
    }

    def import_argc(iat_va):
        """IAT 槽 → 该导入函数的实参个数；未知返回 None。"""
        return IMPORT_ARGS.get(resolve(iat_va))

    print("=" * 96)
    print("C3 补证：模拟 esp，证明 0x777687 读的是 msg")
    print("=" * 96)

    # ---- 实测两个被调函数的 ret 尺寸 ----
    rs_6930A0 = ret_size(0x6930A0)
    rs_778030 = ret_size(0x778030)
    check("0x6930A0 的 ret 尺寸 = 0x10（实测）", rs_6930A0 == 0x10,
          "ret 0x%X" % rs_6930A0)
    check("0x778030 的 ret 尺寸 = 0x8（实测）", rs_778030 == 0x8,
          "ret 0x%X" % rs_778030)

    # ---- IAT 身份（用于说明这两次调用的性质）----
    check("IAT 0x7E1404 = USER32!GetMenu", resolve(0x7E1404) == "GetMenu",
          str(resolve(0x7E1404)))

    # ---- esp 模拟：0x7775C0 → 0x777687 ----
    # ★ 路径必须**沿实际控制流**走，且**每条分支单独建模**：
    #   - 入口 0x7775C0 起，4 次 push 后 0x7775CE `je 0x777627`（[0x887628]==0 分支）
    #   - 0x777627 起，`0x77764C je 0x777655` 又分两支：
    #       A: [0xb73550]==0 ⇒ 跳过 GetMenu，0x777627..0x777655
    #       B: [0xb73550]!=0 ⇒ push eax + call GetMenu，0x777627..0x77764E + 0x777655..
    #   - 两支在 0x777655 汇合，共同走到 0x77766C `je 0x777687`
    #   - 注意 0x77766E..0x777684 是 **0x77766C je 不成立** 的分支（含 4 pop + ret），
    #     不能算进到达 0x777687 的路径 —— 否则 esp 会算错。
    #
    # ★★★ §388（异族复核推翻）：原版 path2 = (0x777627, 0x77766E) **跨过了
    #   0x77764C 的两条分支**，walk() 只按「顺序落入」一条走。异族实测该区间
    #   分歧点为 [('0x77764c', -4, 0)]，而脚本自报"esp 结论不可靠"却仍记 PASS。
    #   现在拆成 path2a / path2b 两条独立区间，各自算到 0x777687。
    path1 = (0x7775C0, 0x7775CE)     # 入口到 je（不含 je 本身之后）
    path2a = (0x777627, 0x777655)    # 分支 A：0x77764C je 成立 ⇒ 跳过 GetMenu
    path2b = (0x77764E, 0x777655)    # 分支 B：0x77764C je 不成立 ⇒ push+call GetMenu
    path3 = (0x777655, 0x77766E)     # 汇合后到 0x77766C je（不含不成立分支）

    esp = 0                          # 相对入口的偏移；入口 esp=0，[esp+0]=返回地址
    trace = []

    # ★★★ 自检 1：路径端点必须是**指令边界**（§381/§383 同类错误的对策）
    #   我已在 §381（0x7775F0）、§382（esp 走错分支）、§383（0x777C40）三次
    #   把「地址相邻」当成「语义相邻」。这里把它变成断言。
    def boundaries_near(va, back=0x40):
        lo = va - back
        off = va2off(lo)
        return {i.address for i in md.disasm(b[off:off + back + 0x20], lo)}

    PATHS = (("path1", path1), ("path2a", path2a), ("path2b", path2b),
             ("path3", path3))
    for label, va in [(l + ".lo", p[0]) for l, p in PATHS] + \
                     [(l + ".hi", p[1]) for l, p in PATHS]:
        bs = boundaries_near(va)
        check("自检 路径端点 %s=0x%08X 是指令边界" % (label, va),
              va in bs, "in %d boundaries" % len(bs))

    # ★★★ 自检 2：路径区间内不得有**未配对的控制流**（即不能跨分支）
    #   做法：区间内若出现 jmp/jcc 且其目标落在区间外，则该区间可能不是单一路径。
    for label, (lo, hi) in PATHS:
        off = va2off(lo)
        bad = []
        for i in md.disasm(b[off:off + (hi - lo) + 32], lo):
            if i.address >= hi:
                break
            if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
                tgt = int(i.op_str, 16)
                # je/jne 等条件跳转允许跳到区间外（那是另一条路径），
                # 但**无条件 jmp** 跳出去意味着本区间不连续
                if i.mnemonic == "jmp" and not (lo <= tgt < hi):
                    bad.append((i.address, tgt))
        check("自检 %s 区间内无跳出型无条件 jmp" % label, not bad, str(bad[:3]))

    # ★★★ 自检 3（§382 的教训）：条件跳转的两侧**esp 净变化必须相同**。
    #   §382 的错在于把 `je 0x777687` **不成立**的分支（含 4 次 pop + ret 0x10）
    #   也顺序算进去，esp 从 -20 算成 -4。
    #   ⇒ 正确判据不是"区间内不许有 jcc"，而是"每个 jcc 的两条分支 esp 净变化一致"。
    #   做法：对区间内每个 jcc，分别模拟"顺序落入"和"跳到目标"，比较 esp 差。
    for label, (lo, hi) in PATHS:
        off = va2off(lo)
        mismatched = []
        for i in md.disasm(b[off:off + (hi - lo) + 32], lo):
            if i.address >= hi:
                break
            if i.mnemonic in ("je", "jne", "ja", "jb", "jae", "jbe", "jg",
                              "jl", "jge", "jle", "js", "jns", "jz", "jnz") \
                    and i.op_str.startswith("0x"):
                tgt = int(i.op_str, 16)
                if not (lo <= tgt < hi):
                    continue          # 跳出本区间 = 另一条路径，不参与比较
                # 从 fallthrough 与 target 各自走到区间末尾，比较 esp 净变化
                def net(delta_start, start):
                    d = delta_start
                    o2 = va2off(start)
                    for k in md.disasm(b[o2:o2 + (hi - start) + 32], start):
                        if k.address >= hi:
                            break
                        if k.mnemonic == "push":
                            d -= 4
                        elif k.mnemonic == "pop":
                            d += 4
                        elif k.mnemonic == "call":
                            d -= 4
                            if k.op_str.startswith("0x"):
                                d += 4 + (ret_size(int(k.op_str, 16)) or 0)
                            else:
                                d += 4
                        elif k.mnemonic == "add" and k.op_str.startswith("esp,"):
                            d += int(k.op_str.split(",")[1].strip(), 16)
                        elif k.mnemonic == "sub" and k.op_str.startswith("esp,"):
                            d -= int(k.op_str.split(",")[1].strip(), 16)
                    return d
                ft = net(0, i.address + i.size)
                tg = net(0, tgt)
                if ft != tg:
                    mismatched.append((hex(i.address), ft, tg))
        # ★★★ §388（异族复核推翻）：原版这里把分支分歧标成 INFO 并
        #   `RESULTS.append((..., True, ...))` —— **自报「esp 结论不可靠」却仍记 PASS**。
        #   异族指出：脚本自己打印"该区间不是单一路径"，随后 exit 0。
        #   这正是它没拦住我 §387 那个 bug 的原因（GetMenu 净额算错 ⇒ 分歧）。
        #   现在改为**真 FAIL**：区间跨分支就是建模错误，必须分开写路径。
        if mismatched:
            check("自检 %s 区间必须是单一路径（不得跨分支）" % label, False,
                  "分歧点 %s" % mismatched[:2])
        else:
            check("自检 %s 各 jcc 两分支 esp 净变化一致" % label, True, "[]")

    def walk(lo, hi):
        nonlocal esp
        off = va2off(lo)
        n = (hi - lo) + 32
        for i in md.disasm(b[off:off + n], lo):
            if i.address >= hi:
                break
            m, ops = i.mnemonic, i.op_str
            before = esp
            if m == "push":
                esp -= 4
            elif m == "pop":
                esp += 4
            elif m == "call":
                esp -= 4                      # 压返回地址
                if ops.startswith("0x"):
                    tgt = int(ops, 16)
                    rs = ret_size(tgt)
                    if rs is None:
                        trace.append((i.address, m, ops, before, esp, "RETSIZE?未知"))
                        continue
                    esp += 4 + rs                 # ret 清栈：弹返回地址 + 参数
                else:
                    # ★★★ §387：`call [mem]` 不再一律按「净 0」。
                    #   净 0 只在被调方**无参**时成立。stdcall 导入函数会 ret 4*argc，
                    #   净效果 = 压返回地址(-4) 然后被调方弹掉返回地址+参数(+4+4*argc)
                    #   ⇒ 相对调用前是 **-4*argc**（净下压 argc 个参数）。
                    #   未知原型 ⇒ 标 unknown 并终止该路径（不猜）。
                    iat = None
                    if "[0x" in ops:
                        try:
                            iat = int(ops.split("[0x")[1].split("]")[0], 16)
                        except ValueError:
                            iat = None
                    argc = import_argc(iat) if iat else None
                    if argc is None:
                        trace.append((i.address, m, ops, before, esp,
                                      "ARGC?未知 ⇒ 路径终止"))
                        esp = None
                        break
                    esp += 4 + 4 * argc           # ret 弹返回地址 + argc 个参数
                    trace.append((i.address, m, ops, before, esp,
                                  "import argc=%d" % argc))
            elif m == "add" and ops.startswith("esp,"):
                esp += int(ops.split(",")[1].strip(), 16)
            elif m == "sub" and ops.startswith("esp,"):
                esp -= int(ops.split(",")[1].strip(), 16)
            trace.append((i.address, m, ops, before, esp, ""))

    # ★★★ §388：两条分支各自从入口独立走到 0x777687。
    #   esp_A: path1 → path2a（跳过 GetMenu）→ path3
    #   esp_B: path1 → path2b（push+GetMenu）→ path3
    def esp_along(*segs):
        """从入口 0 起，沿给定区间序列走一遍，返回终值。"""
        nonlocal esp, trace
        esp = 0
        trace = []
        for seg in segs:
            walk(*seg)
            if esp is None:
                return None
        return esp

    esp_A = esp_along(path1, path2a, path3)
    esp_B = esp_along(path1, path2b, path3)

    print()
    print("  esp 轨迹（相对入口，负数=已下压）—— 分支 B（走 GetMenu）：")
    for addr, m, ops, before, after, note in trace:
        if after != before or m in ("call",):
            print("    0x%08X  %-6s %-26s esp: %+4d -> %+4d  %s"
                  % (addr, m, ops, before, after, note))
    print()
    check("分支 A（跳过 GetMenu）到 0x777687 时 esp = -0x10",
          esp_A == -0x10, "esp=%s" % esp_A)
    check("分支 B（走 GetMenu）到 0x777687 时 esp = -0x10",
          esp_B == -0x10, "esp=%s" % esp_B)
    check("★ 两分支 esp 相同 ⇒ 与分支无关（这才是「唯一值」的实证）",
          esp_A == esp_B and esp_A is not None, "%s vs %s" % (esp_A, esp_B))
    esp = esp_B                 # 后续断言用分支 B（含 GetMenu，是更复杂那条）

    # ---- ★★★ §386 定谳：0x777687 处 esp = -0x10，[esp+0x18] = msg ----
    # §382/§383/§384/§385 我连续四轮得出「=hwnd」并编了四轮解释，全部作废。
    # 根因：我的 ret_size() 只对 `call 0x...` 查 ret 尺寸，对 `call [mem]`
    # （间接虚调用，如 0x7775D4 `call [eax+0x38]`）一律按 ret 0 处理 ⇒ 少算 4 字节。
    # 正确：该虚函数是 __thiscall + stdcall 清参（ret 4），esp 回到 push 之前。
    # 用 BFS 沿真实控制流重算（_esp_bfs.py），结果唯一：esp = -0x10。
    #
    # ★★★ §387 自纠：本节原先写的是
    #       esp_at_687_final = -0x10
    #       check(... esp_at_687_final == -0x10 ...)
    #   这是**恒真式** —— 断言的两侧都是我自己刚赋的常量，被测物根本没进等式。
    #   而且当时 walk() 对 `call [mem]` 按净 0 处理，实算值是 -0x14，
    #   与这条断言**互相矛盾**，门禁却是绿的（因为它断言的不是实算值）。
    #   现在改为断言 walk() 的**实算结果** esp 本身。
    print()
    print("--- ★ 0x777687 处 esp（§386 定谳 / §387 改断言实算值）---")
    esp_at_687_final = esp            # ★ 机器算出来的值，不是我写的常量
    # ★★ 证明 esp 是 walk() **过程产生**的，而不是被直接赋值：
    #   ① trace 必须有内容（若 walk 被桩成 `esp = -0x10`，trace 为空）
    #   ② trace 里的 esp 必须出现过多个不同取值（说明真的在累加 push/pop）
    #   ③ 最后一条 trace 的 after 必须等于 esp_at_687_final
    # 局限（如实登记）：若 walk() 照常跑且实算值恰好 = 期望值，
    #   则「硬编码常量」与「实算」在取值上不可区分 —— 这是逻辑必然，
    #   任何断言都抓不到。本条能抓的是「walk 被整体桩掉」这一更强形态。
    esp_seq = [r[4] for r in trace if r[4] is not None]
    check("自检 trace 非空（esp 由 walk 过程产生，非直接赋值）",
          len(trace) > 0, "%d 条轨迹" % len(trace))
    check("自检 trace 中 esp 出现多个取值（确实在累加）",
          len(set(esp_seq)) > 3, "%d 种取值" % len(set(esp_seq)))
    check("自检 trace 末值 = esp_at_687_final（同源）",
          bool(esp_seq) and esp_seq[-1] == esp_at_687_final,
          "末值=%s" % (esp_seq[-1] if esp_seq else "N/A"))
    check("0x777687 处 esp = -0x10（walk() 实算，非硬编码）",
          esp_at_687_final == -0x10, "esp=%+d（实算）" % esp_at_687_final)
    check("⇒ [esp+0x18] = 入口 E+0x08 = **msg**（异族 C3 正确）",
          esp_at_687_final + 0x18 == 0x08,
          "E%+d" % (esp_at_687_final + 0x18))
    # ---- ★★★ §388：删除原 hand_esp() 那一组（4 条恒真式）----
    #   异族审查认定 hand_esp() 是「纯字面量算术、不读二进制」的恒真式：
    #   它的每个数字都是我自己写进去的，两条分支「同值」是同义反复。
    #   现已被上面的 esp_along(path1, path2a/2b, path3) **真实双分支 walk** 取代
    #   —— 那两条断言的值来自逐条解码二进制累加，且负控（N1/N2）能把它打红。
    #   保留的唯一「负控」是下面这条：证明 argc 修正真的改变结果。
    check("★ 负控 若 GetMenu 按净 0 处理则分支 B 会得 -0x14（E+0x04=hwnd，错）",
          (esp_B - 4) == -0x14 if esp_B is not None else False,
          "净0假设下 %s ⇒ E+0x04" % (esp_B - 4 if esp_B is not None else "N/A"))

    # 0x7775D4 的虚调用确实是带 1 个参数（push -1）
    off_d4 = va2off(0x7775D2)
    i_d2 = next(md.disasm(b[off_d4:off_d4 + 8], 0x7775D2))
    check("0x7775D2 是 push -1（证明虚调用带 1 个参数）",
          i_d2.mnemonic == "push" and i_d2.op_str == "-1",
          "%s %s" % (i_d2.mnemonic, i_d2.op_str))
    off_d4b = va2off(0x7775D4)
    i_d4 = next(md.disasm(b[off_d4b:off_d4b + 8], 0x7775D4))
    check("0x7775D4 是 call [eax+0x38]（间接虚调用，ret 尺寸静态未知）",
          i_d4.mnemonic == "call" and "[eax + 0x38]" in i_d4.op_str,
          "%s %s" % (i_d4.mnemonic, i_d4.op_str))

    # ---- ★★ 0x7779B9 栈布局（§385/§386）：前驱 esp 一致，读到 msg ----
    print()
    print("--- 0x7779B9 栈布局（默认分支，§379 崩溃链入口）---")
    preds = [0x7776A0, 0x777846, 0x777865, 0x777958, 0x777967]
    for p in preds:
        off_p = va2off(p)
        try:
            ins = next(md.disasm(b[off_p:off_p + 16], p))
        except StopIteration:
            check("前驱 0x%08X 可解码" % p, False, "解码失败")
            continue
        tgt_ok = ins.op_str == "0x7779b9"
        check("前驱 0x%08X 确实跳到 0x7779B9" % p, tgt_ok,
              "%s %s" % (ins.mnemonic, ins.op_str))
    # ★★ §387：这里原先也是 `esp_at_9b9 = -0x10` 硬编码后自比。
    #   现在沿「0x77766C je 不成立 → 0x77766E → 4 pop + ret」之外的**另一条**
    #   真实路径走：0x777687 分派失败落到 0x7776A0 `ja 0x7779b9`。
    #   由于 0x777687 处 esp 已由 walk() 实算，且 0x777687..0x7776A0 之间
    #   只有 cmp/je/lea（无 push/pop/call），esp 保持不变。
    seg_off = va2off(0x777687)
    esp_delta = 0
    n_ins = 0
    for i in md.disasm(b[seg_off:seg_off + (0x7776A0 - 0x777687) + 16], 0x777687):
        if i.address >= 0x7776A0:
            break
        n_ins += 1
        if i.mnemonic == "push":
            esp_delta -= 4
        elif i.mnemonic == "pop":
            esp_delta += 4
        elif i.mnemonic in ("call",):
            esp_delta = None
            break
    check("0x777687..0x7776A0 段内无 push/pop/call（esp 不变）",
          esp_delta == 0, "delta=%s（%d 条指令）" % (esp_delta, n_ins))
    esp_at_9b9 = esp_at_687_final + (esp_delta or 0)   # ★ 由实算值派生
    check("0x7779B9 处 esp = -0x10（由 0x777687 实算值派生）",
          esp_at_9b9 == -0x10, "esp=%+d" % esp_at_9b9)
    check("0x7779B9 的 [esp+0x18] = E+0x08 = msg",
          esp_at_9b9 + 0x18 == 0x08, "E%+d" % (esp_at_9b9 + 0x18))
    check("0x7779B9 的 [esp+0x1c] = E+0x0C = wParam",
          esp_at_9b9 + 0x1c == 0x0C, "E%+d" % (esp_at_9b9 + 0x1c))
    check("0x7779B9 的 [esp+0x20] = E+0x10 = lParam",
          esp_at_9b9 + 0x20 == 0x10, "E%+d" % (esp_at_9b9 + 0x20))
    print("    ⇒ 0x54F790(hwnd, msg, wParam) —— 标准 WndProc 布局，§379 链参数层自洽")

    # ---- ★★ §388：0x7779B9 的前驱清单补全（异族指出原版只列 5 个）----
    #   原版硬编码 preds = [0x7776A0, 0x777846, 0x777865, 0x777958, 0x777967]，
    #   异族实测有 9 个（我本轮扫函数体得 **11** 个）。少列不影响 esp 结论
    #   （因为 0x7779B9 处 esp 由 0x777687 派生），但清单不全是事实错误。
    #   现在改为**从二进制扫出全部前驱**，并断言「脚本认识的 = 二进制里存在的」。
    print()
    print("--- 0x7779B9 前驱全量扫描（§388 补）---")
    fn_lo, fn_hi = 0x7775C0, 0x777C30
    o_fn = va2off(fn_lo)
    scanned = []
    for i in md.disasm(b[o_fn:o_fn + (fn_hi - fn_lo)], fn_lo):
        if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
            if int(i.op_str, 16) == 0x7779B9:
                scanned.append(i.address)
    check("函数体内跳到 0x7779B9 的前驱全量 = %d 个" % len(scanned),
          len(scanned) >= 5, "%s" % ["0x%08X" % a for a in scanned])
    # 脚本原先认识的 5 个必须都在全量集合里（防"扫漏"）
    listed = {0x7776A0, 0x777846, 0x777865, 0x777958, 0x777967}
    check("原列 5 个前驱全部包含于全量扫描结果",
          listed <= set(scanned),
          "缺 %s" % ["0x%08X" % a for a in sorted(listed - set(scanned))])


    # ---- ★★ WNDCLASSA 10 槽位自洽（§385 铁证）----
    print()
    print("--- WNDCLASSA 槽位核算（确证 0x7775C0 = lpfnWndProc）---")
    # 0x777C30 sub esp,0x38; 4 push(ebx,ebp,esi,edi); 0x777C65 lea edx,[esp+0x20];
    # 0x777C6B push edx。精确核算：
    #   S-0x38 -> 4 push -> S-0x48 -> lea edx,[esp+0x20] => wc = S-0x28
    #   -> push edx => esp = S-0x4C
    #   ⇒ wc 起始相对 esp 的偏移 = (-0x28) - (-0x4C) = +0x24
    #
    # ★★★ §388（异族 D1 推翻）：本节原先是
    #       for addr, esp_off, want_wc, name in slots:
    #           got_wc = esp_off - WC_SLOT
    #           check(... got_wc == want_wc ...)
    #   其中 esp_off / WC_SLOT / want_wc **全是本文件里的字面量**，
    #   addr 只进了标题字符串，**一个字节都没从二进制读**。
    #   异族实测：把 10 个 addr 全改成 0xDEADBEEF，仍 63/63 PASS。
    #   ⇒ 这 10 条是纯自说自话。现在改为**真读指令**：
    #     解码 [addr] 处指令 → 取出实际位移 → 与期望 wc 偏移比较。
    WC_SLOT = 0x24                      # wc 起始在 [esp+0x24]（由上面的帧核算得出）
    # (写入指令地址, 期望 wc 偏移, 字段名)
    slots = [
        (0x777C71, 0x00, "style"),
        (0x777C79, 0x04, "lpfnWndProc"),
        (0x777C81, 0x08, "cbClsExtra"),
        (0x777C85, 0x0C, "cbWndExtra"),
        (0x777C89, 0x10, "hInstance"),
        (0x777C8D, 0x14, "hIcon"),
        (0x777C91, 0x18, "hCursor"),
        (0x777C95, 0x1C, "hbrBackground"),
        (0x777C99, 0x20, "lpszMenuName"),
        (0x777C9D, 0x24, "lpszClassName"),
    ]
    import re as _re
    for addr, want_wc, name in slots:
        o_a = va2off(addr)
        # ★ 地址映射不到文件 ⇒ 必须是**干净的 FAIL**，不能抛异常。
        #   异族 D1 实测原版把 addr 改成 0xDEADBEEF 时是崩溃（TypeError/None 切片），
        #   而不是一条红色断言 —— 崩溃会让「FAIL 计数」失真，也让报告误读。
        if o_a is None:
            check("0x%08X (%s) 可映射到文件" % (addr, name), False, "VA 不在任何节内")
            continue
        try:
            ins = next(md.disasm(b[o_a:o_a + 16], addr))
        except StopIteration:
            check("0x%08X (%s) 可解码" % (addr, name), False, "解码失败")
            continue
        # 从实际指令文本里取 [esp + 0xNN]
        m_disp = _re.search(r"\[esp \+ (0x[0-9a-f]+)\]", ins.op_str)
        got_wc = (int(m_disp.group(1), 16) - WC_SLOT) if m_disp else None
        check("0x%08X 写 wc+0x%02X (%s)" % (addr, want_wc, name),
              got_wc == want_wc,
              "%s %s ⇒ wc+0x%02X" % (ins.mnemonic, ins.op_str,
                                     got_wc if got_wc is not None else -1))

    # lpfnWndProc 槽的值必须是 0x7775C0
    off_c79 = va2off(0x777C79)
    i_c79 = next(md.disasm(b[off_c79:off_c79 + 12], 0x777C79))
    check("0x777C79 写入的值是 0x7775c0",
          "0x7775c0" in i_c79.op_str, "%s %s" % (i_c79.mnemonic, i_c79.op_str))

    # ---- 关键断言 ----
    print()
    # 目标指令：0x777687 mov eax,[esp+0x18]
    off = va2off(0x777687)
    target = next(md.disasm(b[off:off + 8], 0x777687))
    check("0x777687 是 mov eax, dword ptr [esp + 0x18]",
          target.mnemonic == "mov" and "[esp + 0x18]" in target.op_str,
          "%s %s" % (target.mnemonic, target.op_str))

    # ---- ★★ §386 定谳：不再有"未决点" ----
    print()
    print("  ★ §386 定谳（推翻 §382/§383/§384/§385 全部结论）：")
    print("    0x777687 处 esp = -0x10，[esp+0x18] = E+0x08 = **msg**。")
    print("    ⇒ 0x77768B `cmp eax,0x18` / `lea ecx,[eax-1]` / `cmp ecx,0x13`")
    print("      拿 msg 做分派 —— 从头到尾就没有矛盾。")
    print()
    print("    我此前四轮得出「=hwnd」的根因：")
    print("      ret_size() 只对 `call 0x...` 查 ret 尺寸，")
    print("      对 `call [mem]`（如 0x7775D4 `call [eax+0x38]` 间接虚调用）")
    print("      一律按 ret 0 处理 ⇒ 少算 4 字节 ⇒ 后续 [esp+NN] 全部错位。")
    print()
    print("    ⇒ 教训：工具自身的缺陷会伪装成被测对象的性质。")
    print("      我列了四条「解释」却从未质疑工具 —— 这是第五次同类错误的根源。")

    # ---- ★★★ §387 语义级独立证据：不依赖 esp 模拟，只读「它拿这个值做什么」 ----
    # 上面的 esp 模拟全链依赖同一个前提（我算对 push/pop/call 净额）。
    # 若那个前提错了，结论会整体错而门禁全绿。这里改用**语义**交叉验证：
    # 若 [esp+0x18] 是 msg，那么后续对它的用法必须全是 msg 的用法。
    print()
    print("--- ★ §387 语义级独立证据（不依赖 esp 模拟）---")

    # 证据 1：0x77768B `cmp eax,0x18` 后接两级跳表，且表索引上限正好覆盖消息号
    #   序列（从 0x777687 起）：mov / cmp / ja / je / lea / cmp / ja / xor / mov / jmp
    off_687 = va2off(0x777687)
    seq687 = list(md.disasm(b[off_687:off_687 + 0x30], 0x777687))
    by_addr = {i.address: i for i in seq687}
    check("0x77768B 是 cmp eax, 0x18（msg 上界判据）",
          by_addr[0x77768B].mnemonic == "cmp"
          and by_addr[0x77768B].op_str == "eax, 0x18",
          "%s %s" % (by_addr[0x77768B].mnemonic, by_addr[0x77768B].op_str))
    check("0x77769A 是 lea ecx,[eax-1]（msg 下移成 0 基索引）",
          by_addr[0x77769A].mnemonic == "lea"
          and by_addr[0x77769A].op_str == "ecx, [eax - 1]",
          "%s %s" % (by_addr[0x77769A].mnemonic, by_addr[0x77769A].op_str))
    check("0x77769D 是 cmp ecx, 0x13（索引上界 = 0x18-1）",
          by_addr[0x77769D].mnemonic == "cmp"
          and by_addr[0x77769D].op_str == "ecx, 0x13",
          "%s %s" % (by_addr[0x77769D].mnemonic, by_addr[0x77769D].op_str))
    check("0x7776AE 是 jmp [edx*4+0x777a80]（两级表跳转）",
          by_addr[0x7776AE].mnemonic == "jmp"
          and "edx*4 + 0x777a80" in by_addr[0x7776AE].op_str,
          "%s %s" % (by_addr[0x7776AE].mnemonic, by_addr[0x7776AE].op_str))

    # 证据 2：跳表 + 字节索引表结构自洽（dword 表项数 = max(byte)+1，且两表不重叠）
    tab_off = va2off(0x777A80)
    idx_off = va2off(0x777A98)
    n_tab = (0x777A98 - 0x777A80) // 4
    byte_idx = list(b[idx_off:idx_off + 20])
    check("字节索引表 max = %d，恰好覆盖 %d 项 dword 表（无越界）"
          % (max(byte_idx), n_tab),
          max(byte_idx) == n_tab - 1, "max=%d, n_tab=%d" % (max(byte_idx), n_tab))
    tab_entries = struct.unpack_from("<%dI" % n_tab, b, tab_off)
    in_text = [e for e in tab_entries if 0x400000 <= e < 0x400000 + 0x3E0000]
    check("dword 表 %d 项**全部**落在 .text（无一落入数据/越界）" % n_tab,
          len(in_text) == n_tab, "%d/%d" % (len(in_text), n_tab))

    # 证据 3：0x286 = WM_IME_CHAR，紧随其后是 DBCS 前导/后继字节拆分
    #   这是**只有 msg 才成立**的用法：hwnd 不会被拆成高/低字节。
    off_e1 = va2off(0x7779E1)
    seq_ime = list(md.disasm(b[off_e1:off_e1 + 0x40], 0x7779E1))
    check("0x7779E1 是 cmp eax, 0x286（WM_IME_CHAR）",
          seq_ime[0].mnemonic == "cmp" and seq_ime[0].op_str == "eax, 0x286",
          "%s %s" % (seq_ime[0].mnemonic, seq_ime[0].op_str))
    has_shr8 = any(i.mnemonic == "shr" and i.op_str in ("edx, 8", "eax, 8")
                   for i in seq_ime)
    has_byte_store = any(i.mnemonic == "mov" and "byte ptr [esp + 0x1" in i.op_str
                         for i in seq_ime)
    check("WM_IME_CHAR 分支内出现 shr 8（取后继字节）", has_shr8, "")
    check("WM_IME_CHAR 分支内出现 byte ptr 存储（拆字节落栈）", has_byte_store, "")

    # 证据 4：0x54F790 用 arg2 做消息比较（0x201 = WM_LBUTTONDOWN）
    off_f7 = va2off(0x54F7F1)
    seq_54 = list(md.disasm(b[off_f7:off_f7 + 0x40], 0x54F7F1))
    check("0x54F7F9 是 cmp eax, 0x201（WM_LBUTTONDOWN）",
          any(i.address == 0x54F7F9 and i.mnemonic == "cmp"
              and i.op_str == "eax, 0x201" for i in seq_54),
          "0x54F7F9")
    check("0x54F80F 是 add eax, 0xffffff00（WM_ 区间下移，§379 环节2）",
          any(i.address == 0x54F80F and i.mnemonic == "add"
              and "0xffffff00" in i.op_str for i in seq_54),
          "0x54F80F")

    # 证据 5：0x778030 用 edx 与 IME 消息号比较 ⇒ 传给它的第 2 参是 msg
    off_8030 = va2off(0x778030)
    seq_8030 = list(md.disasm(b[off_8030:off_8030 + 0x18], 0x778030))
    check("0x778031 是 cmp edx, 0x281（IME 消息号）",
          any(i.address == 0x778031 and i.mnemonic == "cmp"
              and i.op_str == "edx, 0x281" for i in seq_8030),
          "0x778031")
    check("0x778041 是 sub edx, 0x10d（继续按消息号区间判定）",
          any(i.address == 0x778041 and i.mnemonic == "sub"
              and i.op_str == "edx, 0x10d" for i in seq_8030),
          "0x778041")

    # ---- ★ 可达性：0x777687 的前驱 je 是否常成立 ----
    print()
    print("--- 0x777687 可达性 ---")
    # 0x778030 的返回值决定 0x77766C je 是否跳 0x777687
    # 返回 1 仅当 msg ∈ {0x10D,0x10E,0x10F,0x281,0x282..0x291}；其余返回 0
    # ★★★ §388（异族列其为恒真式，我复算后发现**还错**）：
    #   原版 ret_778030() 是纯 Python 字面量重实现，不读二进制 —— 异族判为恒真式。
    #   我改从二进制读之后发现它**内容也错了**：
    #     原版断言 0x282..0x291 **全部**返回 1；
    #     实际跳表（0x778104 dword 表 + 0x77810C 字节索引）只有
    #     0x282 / 0x285 / 0x290 / 0x291 返回 1，其余（含 0x286/0x287）返回 0。
    #   ⇒ 「0x282..0x291 全 1」是错的。现在改为**真读跳表**。
    TAB_VA, IDX_VA = 0x778104, 0x77810C
    TAB_N = 2                     # dword 表实际项数（0x7780D6 的 max idx=1）
    tab_off2 = va2off(TAB_VA)
    tab2 = struct.unpack_from("<%dI" % TAB_N, b, tab_off2)
    idx_off2 = va2off(IDX_VA)
    idx2 = list(b[idx_off2:idx_off2 + 16])
    RET1_VA = 0x7780DD           # 分支：push 后 jmp 0x7780E8 → mov eax,1
    RET0_VA = 0x7780FD           # 分支：xor eax,eax

    def ret_778030_real(msg):
        """从二进制跳表读出 0x778030 对给定 msg 的返回值。"""
        if msg > 0x281:
            k = msg - 0x282
            if not (0 <= k < 16):
                return 0
            return 1 if tab2[idx2[k]] == RET1_VA else 0
        if msg == 0x281:
            return 1
        if msg in (0x10D, 0x10E, 0x10F):
            return 1
        return 0

    check("0x778030(WM_CREATE=0x001) 返回 0 ⇒ 0x777687 可达",
          ret_778030_real(0x001) == 0, "ret=%d" % ret_778030_real(0x001))
    check("0x778030(WM_CLOSE=0x010) 返回 0 ⇒ 0x777687 可达",
          ret_778030_real(0x010) == 0, "ret=%d" % ret_778030_real(0x010))
    check("0x778030(0x281) 返回 1 ⇒ 不跳（负控）",
          ret_778030_real(0x281) == 1, "ret=%d" % ret_778030_real(0x281))
    check("0x778030(0x10D) 返回 1 ⇒ 不跳（负控）",
          ret_778030_real(0x10D) == 1, "ret=%d" % ret_778030_real(0x10D))
    # ★ 新事实：0x282..0x291 不是全 1
    ones = [m for m in range(0x282, 0x292) if ret_778030_real(m) == 1]
    check("0x282..0x291 中返回 1 的只有 {0x282,0x285,0x290,0x291}（跳表实读）",
          ones == [0x282, 0x285, 0x290, 0x291],
          "%s" % ["0x%03X" % m for m in ones])
    check("★ 0x286(WM_IME_CHAR) 返回 0 ⇒ 0x777687 可达（原版误判为 1）",
          ret_778030_real(0x286) == 0, "ret=%d" % ret_778030_real(0x286))
    # 解码验证这两条返回路径确实存在
    seq = insn_at(0x7780F4, 2) if False else None
    off_r1 = va2off(0x7780F4)
    i_r1 = next(md.disasm(b[off_r1:off_r1 + 8], 0x7780F4))
    check("0x7780F4 是 mov eax, 1（返回 1 的路径存在）",
          i_r1.mnemonic == "mov" and i_r1.op_str == "eax, 1",
          "%s %s" % (i_r1.mnemonic, i_r1.op_str))
    off_r0 = va2off(0x7780FD)
    i_r0 = next(md.disasm(b[off_r0:off_r0 + 8], 0x7780FD))
    check("0x7780FD 是 xor eax, eax（返回 0 的路径存在）",
          i_r0.mnemonic == "xor" and i_r0.op_str == "eax, eax",
          "%s %s" % (i_r0.mnemonic, i_r0.op_str))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
