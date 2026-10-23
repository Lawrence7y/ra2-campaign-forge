#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""待办 7：`[0x887368]` 置值（单例创建）的触发条件定谳。

★ 要回答的问题
  §370/§371 已定谳「崩溃时 `[0x887368]` 从未置值 ⇒ 单例根本没被创建」。
  但**为什么没被创建**？即 `0x7777B8` 那条 `mov [0x887368], esi` 的**前置条件**是什么？
  这决定待办 6 的三种退出方式各会不会命中。

★ 方法（纯静态，零真机）
  1. 定位 `0x7777B8` 所在函数（WndProc，`ret 0x10` 四参数）。
  2. 解出该函数的**消息分派表**（跳转表 + 字节索引表）。
  3. 判定哪些消息走「创建」分支、哪些走「销毁」分支。
  4. 交叉验证：创建分支的前置条件（分配是否成功、构造函数、vtable 写入顺序）。

★ 输出
  每个结论都带**原始反汇编**与**表项实测值**，可离线复跑。
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import capstone

GAMEMD = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
IMG_BASE = 0x400000
WANT_SHA16 = "73201cc021497c95"

# 已定位的锚点（本脚本会重新验证，不盲信）
# ★★ 0x7775F0 **不是指令边界**（异族核验 C1 实测）：
#     0x7775EB  8b0d28768800   mov ecx,[0x887628]   ← 6 字节，止于 0x7775F1
#   0x7775F0 落在该指令的立即数内部（第 6 个字节位）。
#   真函数头是 0x7775C0（`51` = push ecx），前面 0x7775BC 是 90 填充。
#   本项目铁律：反汇编起点必须先确认是指令边界。
WNDPROC_HINT = 0x7775C0
WNDPROC_HINT_WRONG = 0x7775F0   # 保留旧值仅用于负控断言
SINGLETON = 0x00887368
WRITE_CREATE = 0x7777B8      # mov [0x887368], esi
WRITE_NULL_ON_ALLOCFAIL = 0x7777C3   # mov [0x887368], ebx (ebx=0)
WRITE_DESTROY = 0x777803     # mov [0x887368], ebx (销毁路径)
CREATE_BRANCH = 0x77778D
DESTROY_BRANCH = 0x7777F3
JT_DWORDS = 0x777A80         # 跳转表（20 个 dword）
JT_BYTES = 0x777A98          # 字节索引表（20 字节）
MSG_MAX = 0x18               # 分派边界：msg > 0x18 走另一条路

RESULTS: list[tuple[str, bool, str]] = []


def chk(tag: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((tag, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {tag}  {detail}")
    return bool(cond)


def main() -> int:
    import hashlib
    data = GAMEMD.read_bytes()
    sha = hashlib.sha256(data).hexdigest()

    def off(va: int) -> int:
        return va - IMG_BASE

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    def dis(va: int, n: int):
        return list(md.disasm(data[off(va):off(va) + n], va))

    print("=" * 84)
    print("== STEP 0  identity")
    print("=" * 84)
    print(f"  gamemd.exe : {sha}")
    chk("gamemd 身份", sha.startswith(WANT_SHA16), sha[:16])

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 1  三个写入点的原始字节")
    print("=" * 84)
    for va, label in ((WRITE_CREATE, "创建（存 esi）"),
                      (WRITE_NULL_ON_ALLOCFAIL, "分配失败（存 0）"),
                      (WRITE_DESTROY, "销毁（存 0）")):
        ins = dis(va, 10)[0]
        print(f"  0x{va:08X}  {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}   ← {label}")
        chk(f"0x{va:08X} 是写 {SINGLETON:#x}", str(SINGLETON) in ins.op_str or
            f"0x{SINGLETON:x}" in ins.op_str, ins.op_str)

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 1b  ★ 反汇编起点边界自检（铁律）")
    print("=" * 84)
    # ★★ §405：原实现 `probe_start = WNDPROC_HINT - 16` —— 起点跟着入口一起移动，
    #   「入口在边界集合里」于是成了自指判据：入口错移 1 字节后，新起点解出来的
    #   指令边界集合里**照样**含有新入口（0x7775C1 本身就是一条指令起点）
    #   ⇒ 变异存活。改为：
    #     ① 解码起点用**固定常量** PROBE_ANCHOR，不随 WNDPROC_HINT 移动；
    #     ② 追加独立判据「入口前 3 字节全是填充」，这条与解码起点无关。
    PROBE_ANCHOR = 0x7775B0
    boundaries = {i.address for i in dis(PROBE_ANCHOR, 0x40)}
    chk("WNDPROC_HINT 是已知指令边界（从固定锚点 0x%08X 起解码）" % PROBE_ANCHOR,
        WNDPROC_HINT in boundaries,
        f"0x{WNDPROC_HINT:08X} in {len(boundaries)} boundaries")
    # 独立判据二：函数头之前必须是填充字节（对齐填充），与解码起点无关。
    _lead = data[off(WNDPROC_HINT) - 3:off(WNDPROC_HINT)]
    chk("★★ 入口前 3 字节全是填充（独立判据，不依赖解码起点）",
        len(_lead) == 3 and all(x in (0x90, 0xCC, 0x00) for x in _lead),
        _lead.hex())
    # 负控：旧值必须**不是**边界，否则说明自检没抓到真问题
    chk("负控 旧值 0x%08X 不是边界" % WNDPROC_HINT_WRONG,
        WNDPROC_HINT_WRONG not in boundaries,
        f"0x{WNDPROC_HINT_WRONG:08X} not in boundaries")
    # 负控二：入口错移 1 字节必须被上面任一条判据抓住（否则自检形同虚设）
    _shifted = WNDPROC_HINT + 1
    _shift_lead = data[off(_shifted) - 3:off(_shifted)]
    chk("★ 负控 入口错移 1 字节 ⇒ 填充判据必须失败",
        not all(x in (0x90, 0xCC, 0x00) for x in _shift_lead),
        f"0x{_shifted:08X} 前 3 字节 {_shift_lead.hex()}")

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 2  WndProc 身份（ret 0x10 ⇒ 四参数）")
    print("=" * 84)
    # ★★★ §405 H-4 修复：窗口边界不再手选，改为**从本脚本自己的常量推出**。
    #   · 上界 = 分派表起点 `JT_DWORDS`：那是数据表，不可能落在函数体内
    #   · 下界 = `WNDPROC_HINT`：STEP 1b 已断言它是已知指令边界
    #   原实现用固定 `0x400` 窗口，只覆盖 8/11 个 ret；且「窗口里有 ret 0x10」
    #   这条既没证明唯一、也没证明窗口选对 —— 窗口一放宽就变。
    #   实测：0x400 → {0x10}；0x4C0（到表起点）→ {0x10}×11；0x500 → {0, 0x10}。
    BODY_END = JT_DWORDS
    body = dis(WNDPROC_HINT, BODY_END - WNDPROC_HINT)
    body_rets = [i for i in body if i.mnemonic == "ret"]
    body_sizes = {int(i.op_str, 16) if i.op_str else 0 for i in body_rets}
    print(f"  函数体 [0x{WNDPROC_HINT:08X}, 0x{BODY_END:08X})："
          f"指令 {len(body)} 条，ret {len(body_rets)} 个")
    for i in body_rets:
        print(f"    0x{i.address:08X}  ret {i.op_str or '0'}")

    chk("★ 函数体内全部 ret 尺寸唯一 = 0x10（0x10 ⇒ 清 4 个参数）",
        body_sizes == {0x10},
        f"sizes={sorted(body_sizes)} n={len(body_rets)}")
    chk("★ 函数体内 ret 数 = 11（多出口，但同尺寸）",
        len(body_rets) == 11, str(len(body_rets)))

    last_ret = body_rets[-1] if body_rets else None
    chk("★ 末 ret = ret 0x10 @ 0x00777A7A",
        last_ret is not None and last_ret.address == 0x777A7A
        and last_ret.op_str.strip() == "0x10",
        f"0x{last_ret.address:08X} ret {last_ret.op_str}" if last_ret else "none")

    # 帧对称：`ret 0x10`（callee 清 4 参数）与序言 push ecx/ebx/esi/edi 必须配平，
    # 否则「ret 0x10」可能只是数据被误解码成指令。
    tail_pops = []
    if last_ret is not None:
        idx_last = body.index(last_ret)
        tail_pops = [f"{i.mnemonic} {i.op_str}" for i in body[idx_last - 4:idx_last]]
    chk("★ 末 ret 前 4 条 = pop edi/esi/ebx/ecx（与序言 push 配平）",
        tail_pops == ["pop edi", "pop esi", "pop ebx", "pop ecx"], str(tail_pops))

    # 边界不是切在指令中间：末 ret 之后到表起点只有填充，且无分支落入。
    pad_start = last_ret.address + last_ret.size if last_ret else BODY_END
    pad = data[off(pad_start):off(BODY_END)]
    branch_tgts = {int(i.op_str, 16) for i in body
                   if (i.mnemonic.startswith("j") or i.mnemonic == "call")
                   and i.op_str.startswith("0x")}
    chk("★ 末 ret 到表起点之间是填充且无分支落入（边界不切指令）",
        pad_start <= BODY_END and not (branch_tgts & set(range(pad_start, BODY_END))),
        f"0x{pad_start:08X}..0x{BODY_END:08X} = {pad.hex()}")

    # ★★ 负控：证明**边界是承重的**，不是装饰。
    #    窗口只要越过函数体 0x80 字节，就会捡到下一个函数的 `ret 0`
    #    ⇒ 上面那条「唯一 = 0x10」立刻变多值。换句话说，谁把窗口改回
    #    固定值（无论 0x400 还是 0x500）都会在这条负控上暴露。
    beyond = dis(WNDPROC_HINT, (BODY_END - WNDPROC_HINT) + 0x80)
    beyond_sizes = {int(i.op_str, 16) if i.op_str else 0
                    for i in beyond if i.mnemonic == "ret"}
    chk("★★ 负控 窗口越过函数体 0x80 字节 ⇒ 尺寸集合变多值",
        len(beyond_sizes) > 1,
        f"sizes={sorted(beyond_sizes)}")

    if last_ret:
        print(f"  末 ret @ 0x{last_ret.address:08X}；"
              f"填充 {pad.hex()} 后紧接分派表 0x{JT_DWORDS:08X}")

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 3  ★ 消息分派：解跳转表")
    print("=" * 84)
    # 定位分派指令：mov dl, byte ptr [ecx + JT_BYTES] ; jmp dword ptr [edx*4 + JT_DWORDS]
    jt_ins = None
    for i in dis(0x777687, 0x40):
        if i.mnemonic == "jmp" and "edx*4" in i.op_str.replace(" ", ""):
            jt_ins = i
            break
    chk("找到跳转表间接跳转", jt_ins is not None,
        f"{jt_ins.mnemonic} {jt_ins.op_str} @ 0x{jt_ins.address:08X}" if jt_ins else "none")
    if jt_ins:
        print(f"  {jt_ins.address:08X}  {jt_ins.bytes.hex():<20} {jt_ins.mnemonic} {jt_ins.op_str}")

    # ★★★ §405：这条断言是 STEP 2 的**依据**。
    #   STEP 2 把函数体上界定在 `JT_DWORDS`（分派表是数据，不可能在函数体内）。
    #   但「JT_DWORDS 真是分派表」此前从未被断言过 —— 常量写错就整段错。
    #   这里从**指令操作数**读出基址，与本脚本常量比对。
    if jt_ins:
        _ops = jt_ins.op_str.replace(" ", "")
        _base = _ops.split("+")[-1].rstrip("]") if "+" in _ops else ""
        chk("★★ 间接跳转的基址 = JT_DWORDS（⇒ STEP 2 的函数体上界有实测依据）",
            _base.startswith("0x") and int(_base, 16) == JT_DWORDS,
            f"操作数基址 {_base or '?'} vs 常量 0x{JT_DWORDS:08X}")
    # 字节索引表同理：`mov dl, byte ptr [ecx + JT_BYTES]` 的基址要能对上常量。
    # 不猜地址，在**函数体内**找（实测 @0x7776A8，紧接在间接跳转前）。
    _idx_src = [i for i in body
                if "byte ptr" in i.op_str and f"0x{JT_BYTES:x}" in i.op_str.replace(" ", "")]
    chk("★★ 字节索引表基址 = JT_BYTES（表解法的另一半个依据）",
        len(_idx_src) == 1 and _idx_src[0].address == jt_ins.address - 6,
        f"{_idx_src[0].mnemonic} {_idx_src[0].op_str} @0x{_idx_src[0].address:08X}"
        if _idx_src else "none")

    idx_tbl = list(data[off(JT_BYTES):off(JT_BYTES) + 20])
    dword_tbl = [struct.unpack_from("<I", data, off(JT_DWORDS) + 4 * i)[0]
                 for i in range(20)]
    print(f"  字节索引表 @0x{JT_BYTES:08X} (20B): {idx_tbl}")
    print(f"  跳转表 @0x{JT_DWORDS:08X}（前 6 项有效）:")
    for i in range(6):
        print(f"    entry {i} -> 0x{dword_tbl[i]:08X}")

    # 只有 entry 0..5 是合法代码地址（其余是数据/其它函数的字节）
    valid = [i for i in range(20) if 0x400000 <= dword_tbl[i] < 0xC00000]
    chk("跳转表有效项数 >= 5", len(valid) >= 5, f"valid entries={valid}")

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 4  ★★ msg -> 目标地址 映射")
    print("=" * 84)
    WM_NAMES = {
        0x001: "WM_CREATE", 0x002: "WM_DESTROY", 0x003: "WM_MOVE",
        0x005: "WM_SIZE", 0x00F: "WM_PAINT", 0x010: "WM_CLOSE",
        0x014: "WM_ERASEBKGND", 0x112: "WM_SYSCOMMAND",
    }
    msg_map = {}
    print(f"  {'msg':>7}  {'名称':<14} {'索引':>4}  {'目标':<12} 判定")
    # ★ 边界实测（三层）：
    #   `cmp eax,0x18 / ja 0x77782B`  ⇒ msg > 0x18 走另一条路
    #   `je 0x777A5B`                 ⇒ msg == 0x18 单独接走
    #   `lea ecx,[eax-1]; cmp ecx,0x13; ja 0x7779B9`
    #                                 ⇒ 只有 msg-1 <= 0x13 即 **msg 1..0x14** 进表
    #   ⇒ 表恰 20 项，与 @0x777A98 的 20 字节索引表一致。
    #   首版写 range(1, MSG_MAX+1) 与 range(1, MSG_MAX) 都越界过。已改。
    TABLE_MSGS = 0x14
    for msg in range(1, TABLE_MSGS + 1):
        e = idx_tbl[msg - 1]
        tgt = dword_tbl[e] if e < 20 else None
        msg_map[msg] = tgt
        name = WM_NAMES.get(msg, "")
        verdict = ""
        if tgt == CREATE_BRANCH:
            verdict = "★ 创建单例"
        elif tgt == DESTROY_BRANCH:
            verdict = "★ 销毁单例"
        print(f"  0x{msg:03X}  {name:<14} {e:>4}  0x{tgt:08X}  {verdict}" if tgt else
              f"  0x{msg:03X}  {name:<14} {e:>4}  {'--':<12}")
    print(f"  0x015..0x017  （越表）        --   0x007779B9  默认分支")
    # ★ 勘误修正（§404，2026-10-24）：原文把 0x18 标成 WM_SETFONT —— 错。
    #   WM_SETFONT = 0x30，**WM_SHOWWINDOW = 0x18**。已用 capstone 按地址
    #   0x777A5B 解码复核（见 §404 §二）。
    print(f"  0x{MSG_MAX:03X}  (WM_SHOWWINDOW)  --   0x00777A5B  单独接走（不进表）")

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 5  ★★★ 定谳断言")
    print("=" * 84)
    chk("★ 单例创建只由 WM_CREATE(0x001) 触发",
        msg_map.get(0x001) == CREATE_BRANCH,
        f"WM_CREATE -> 0x{msg_map.get(0x001):08X}" if msg_map.get(0x001) else "none")
    # ★ 勘误修正（§404，2026-10-24）：原文只说「走销毁分支」，没写前置守卫。
    #   实测 0x7777F9 `cmp ecx,ebx / 0x7777FB je 0x777809` ⇒ **[0x887368] 为 0
    #   时跳过 0x777803 的清零写**。即「进销毁分支」≠「必然清零」。
    #   已用 capstone 从 0x7777F3 对齐解码复核（见 §404 §二）。
    chk("★ WM_DESTROY(0x002) 走销毁分支（不是创建）"
        "；★ 但 0x7777F9 有守卫：槽为 0 时跳过 0x777803 清零",
        msg_map.get(0x002) == DESTROY_BRANCH,
        f"WM_DESTROY -> 0x{msg_map.get(0x002):08X}"
        if msg_map.get(0x002) else "none")
    # ★★ 措辞修正（§379）：WM_CLOSE 在**本 WndProc 内**确实不直接创建/销毁，
    #   但它的默认处理 DefWindowProcA 会 DestroyWindow ⇒ 同步发 WM_DESTROY
    #   ⇒ 经 0x777803 **间接清零**单例。所以不能说"不销毁"。
    chk("★ WM_CLOSE(0x010) 本函数内不直接创建/销毁（但默认处理会间接清零）",
        msg_map.get(0x010) not in (CREATE_BRANCH, DESTROY_BRANCH),
        f"WM_CLOSE -> 0x{msg_map.get(0x010):08X}（默认分支 ⇒ DefWindowProcA）"
        if msg_map.get(0x010) else "none")
    # 除了 WM_CREATE，还有没有别的入口写 CREATE_BRANCH？
    creators = [m for m, t in msg_map.items() if t == CREATE_BRANCH]
    chk("★ 创建入口唯一（只有 WM_CREATE）", creators == [0x001], f"creators={[hex(x) for x in creators]}")

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 6  创建分支的前置条件（为什么可能不创建）")
    print("=" * 84)
    print("  WM_CREATE 分支 0x77778D 完整指令：")
    for i in dis(CREATE_BRANCH, 0x45):
        print(f"    {i.address:08X}  {i.bytes.hex():<24} {i.mnemonic} {i.op_str}")

    # 断言：分配失败会写 0（而不是不写）
    seq = dis(CREATE_BRANCH, 0x45)
    mnems = [(i.address, i.mnemonic, i.op_str) for i in seq]
    has_alloc = any("0x7c8e17" in o for _, _, o in mnems)
    has_nullcheck = any(m == "cmp" and "esi" in o for _, m, o in mnems)
    has_je_null = any(m == "je" and f"0x{WRITE_NULL_ON_ALLOCFAIL:x}" in o
                      for _, m, o in mnems)
    chk("创建分支先调分配器 0x7C8E17", has_alloc, "")
    chk("创建分支检查分配结果", has_nullcheck, "")
    chk("分配失败跳到写 0 处", has_je_null, f"je -> 0x{WRITE_NULL_ON_ALLOCFAIL:08X}")

    print()
    print("  ⇒ 关键结论：**分配失败时仍会执行 `mov [0x887368], ebx`(ebx=0)**，")
    print("    即『单例槽被写成 0』。而『从未置值』意味着**连 WM_CREATE 都没走到这个分支**。")

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== STEP 7  与待办 6 三种退出方式的对应")
    print("=" * 84)
    print("""
  待办 6 的三种退出方式：
    (i)   进 L1 局后 WM_CLOSE
    (ii)  主菜单点「退出」按钮
    (iii) 局内菜单退出到主菜单再退出

  ★★ §379 已推翻本段旧结论，以下为修正版 ★★

  旧结论（作废）："WM_CLOSE 本身不创建也不销毁单例（走默认分支 0x7779B9）"。
  错在把"走默认分支"读成"什么都不做"。默认分支恰恰是问题所在：

    WM_CLOSE → 0x54F790 返回 0 → 0x777A64 call [0x7E1394]
             = USER32!DefWindowProcA
             → DefWindowProcA 对 WM_CLOSE 默认 DestroyWindow
             → 同步发 WM_DESTROY → 0x777803 mov [0x887368], 0

  ⇒ **WM_CLOSE 必然清零单例**，不是"不改变"。
  ⇒ "退出方式"与"单例态"**不正交**：任何关窗路径都会把它清零。
  ⇒ 因此**不能用"关窗前的单例读数"做归因**（那值在崩溃瞬间必然已是 0）。

  正确的判据分两个时点，各答各的问题：
    ① 关窗前读数 singleton_before_close —— 只答「单例是否**创建过**」
       （即 WM_CREATE 到没到；这正是本脚本 STEP 4/5 的结论）
    ② 崩溃瞬间读数 singleton_at_hit —— 才是**归因**依据
       （崩溃链要求 ecx = [0x887368] = 0，只有瞬间读数能验证）

  实现见 _todo6_verdict.py v2（§380）与 _verify_wmclose_chain.py（§379，20/20）。
""")

    # ---------------------------------------------------------------
    print()
    print("=" * 84)
    print("== RESULT")
    print("=" * 84)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"  checks passed: {passed}/{total}")
    verdict = passed == total
    print(f"  RESULT: {'ALL PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
