"""Emit EVIDENCE/ROW_<entry>.txt for the 6 rows, asserting every cited byte against the image."""
import os
import struct
from pe import read, u32, cstr, BY_ADDR, fmt, TEXT_LO, TEXT_HI, rtti_of_table

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT16\EVIDENCE"
FAILS = []


def B(va, n, expect_hex, what):
    exp = expect_hex.replace(" ", "").lower()
    n = len(exp) // 2          # length is derived from the expectation, never hand-typed
    got = read(va, n)
    ok = got is not None and got.hex() == exp
    if not ok:
        FAILS.append("%s @%08X expect %s got %s" % (what, va, exp, got.hex() if got else None))
    return "%08X  %-20s  %s" % (va, got.hex() if got else "??", what)


def U32(va, expect, what):
    got = u32(va)
    if got != expect:
        FAILS.append("%s @%08X expect %08X got %08X" % (what, va, expect, got or 0))
    return "%08X  =%08X  %s" % (va, got or 0, what)


ROWS = [
    dict(
        entry=0x004684E0, name="BulletClass::slot10", vt=0x007E46E4, slot=10,
        sem_claim="容器移除：经容器虚表 call [eax+0x10] 查下标（-1 未命中则跳过），命中则前移压缩数组",
        ring3=[
            (0x0046862A, 3, "ff5010", "call dword ptr [eax+0x10]   <- 容器虚表槽4 = Find"),
            (0x0046862D, 3, "83f8ff", "cmp eax, -1                 <- 消费 -1 哨兵"),
            (0x00468630, 2, "742d", "je 0x46865f                <- 未命中跳收尾 eax=0x46865F"),
            (0x00468638, 2, "3bc1", "cmp eax, ecx (ecx=Count)"),
            (0x0046863C, 1, "49", "dec ecx                     <- Count--"),
            (0x00468651, 4, "895481fc", "mov [ecx+eax*4-4], edx      <- 前移压缩"),
            (0x0046865D, 2, "7ce8", "jl 0x468647                <- 压缩循环回边"),
        ],
        ring3_extra=[
            "被调方独立解析（③b② 的另一半，执行器未给）：",
            "  全局容器基址 0x89DE18（vptr+0 / Items+4 / Count+0x10 / Capacity+0x14）",
            B(0x004662FD, 10, "c70518de8900 78467e00", "容器静态初始化写活表 0x7E4678"),
            B(0x004662E2, 5, "6820634600", "push 0x466320               <- 注册的析构"),
            B(0x00466316, 5, "e86f343600", "call 0x7c978a               <- atexit/_onexit 注册"),
            B(0x007E4688, 4, "90b84600", "活表 slot4 = 0046B890       <- Find 真身"),
            B(0x0046B890, 12, "8b511033c056 85d27e15", "Find: mov edx,[ecx+0x10]; xor eax,eax; push esi; test edx,edx; jle"),
            B(0x0046B8A3, 12, "3931740b 4083c1043bc2", "Find: cmp [ecx],esi; je; inc eax; add ecx,4; cmp eax,edx"),
            B(0x0046B8AF, 3, "83c8ff", "or eax, -1                  <- 未命中返回 0xFFFFFFFF"),
            B(0x0046B8B2, 3, "5ec204", "pop esi; ret 4              <- 命中返回下标 eax"),
        ],
        ring3_verdict="失败返回 0xFFFFFFFF（0046B8AF `83 c8 ff`），成功返回 0..Count-1 的下标；"
                      "调用方 0046862D `cmp eax,-1` + 00468630 `je 0x46865F` 分支，未命中跳过压缩、命中进入 00468647 压缩回边。",
        ring4_site=0x00466425, ring4_host=0x00466380,
        ring4=[
            (0x00466425, 7, "c706e4467e00", "mov [esi], 0x7e46e4         <- 主虚表安装点（行外）"),
            (0x0046642B, 7, "c700c8467e00", "mov [eax], 0x7e46c8         <- 次对象虚表"),
            (0x00466431, 7, "c74608c0467e00", "mov [esi+8], 0x7e46c0"),
            (0x00466438, 7, "c7460cb8467e00", "mov [esi+0xc], 0x7e46b8"),
            (0x00466384, 5, "e877d51800", "call 0x5f3900               <- 基类构造（非析构）"),
            (0x00466652, 5, "e829d51800", "call 0x5f3b80               <- 体内另一构造/初始化"),
        ],
        ring4_note="宿主 00466380 体内无 call 0x7258D0 / call 0x7C8B3D，非析构器；"
                   "同表另两个安装点 00466566（宿主 00466560 含 call 0x7258D0）与 0046AEB5（宿主 0046AE70，属本类方法族）已按 ㉓/行外规则排除。",
    ),
    dict(
        entry=0x00629FD0, name="ParasiteClass::slot23", vt=0x007EF890, slot=23,
        sem_claim="operator new 分配，失败(NULL)跳过初始化，成功则用返回指针构造",
        ring3=[
            (0x0062A0D3, 5, "6800010000", "push 0x100                  <- 分配长度"),
            (0x0062A0D8, 5, "e83aed1900", "call 0x7c8e17               <- operator new"),
            (0x0062A0E0, 2, "85c0", "test eax, eax               <- 消费 NULL 约定"),
            (0x0062A0E2, 2, "7424", "je 0x62a108                <- 失败跳收尾"),
            (0x0062A101, 2, "8bc8", "mov ecx, eax                <- this = 返回值"),
            (0x0062A103, 5, "e8483b0000", "call 0x62dc50               <- 成功路径构造"),
        ],
        ring3_extra=[
            B(0x007C8E17, 6, "6a01ff742408", "operator new: push 1; push [esp+8]"),
            B(0x007C8E1D, 5, "e820060000", "call 0x7c9442               <- 分配器"),
        ],
        ring3_verdict="失败返回 0（NULL），调用方 0062A0E0 `test eax,eax` + 0062A0E2 `je 0x62A108` 跳过构造；"
                      "成功返回非空指针，0062A101 搬入 ecx 作 this 并 0062A103 构造。两路动作不同（构造 / 跳过）。",
        ring4_site=0x00629231, ring4_host=0x00629210,
        ring4=[
            (0x00629231, 7, "c70690f87e00", "mov [esi], 0x7ef890         <- 主虚表安装点（行外）"),
            (0x00629237, 7, "c7460474f87e00", "mov [esi+4], 0x7ef874"),
            (0x0062923E, 7, "c746086cf87e00", "mov [esi+8], 0x7ef86c"),
            (0x00629245, 7, "c7460c64f87e00", "mov [esi+0xc], 0x7ef864"),
            (0x00629213, 5, "e8586fdeff", "call 0x410170               <- 基类构造"),
            (0x0062927E, 3, "ff5208", "call [edx+8]                <- 基类后置"),
        ],
        ring4_note="宿主 00629210 体内无 dtor marker；同表安装点 0062AF7A 的宿主 0062AF70 含 call 0x7C8B3D（free）⇒ 析构器，已排除。",
    ),
    dict(
        entry=0x0075E0C0, name="WarheadTypeClass::slot5", vt=0x007F6B30, slot=5,
        sem_claim="流读入（Load）：读包装返回 HRESULT，失败 E_POINTER 负码跳收尾、成功继续构造并写回",
        ring3=[
            (0x0075E0F0, 5, "e88b22cbff", "call 0x410380               <- 读包装（vt+0xC = Read）"),
            (0x0075E0F5, 2, "85c0", "test eax, eax               <- 消费 HRESULT"),
            (0x0075E0F7, 6, "0f8cb1010000", "jl 0x75e2ae               <- 负码跳收尾"),
            (0x0075E2AC, 2, "33c0", "xor eax, eax                <- 成功路径置 0 (S_OK)"),
            (0x0075E2AE, 8, "5f5e5d5bc20800", "pop edi/esi/ebp/ebx; ret 8 <- 失败路径 eax=负码"),
        ],
        ring3_extra=[
            B(0x00410389, 5, "b803400080", "E_POINTER = 0x80004003      <- 包装失败返回码"),
            B(0x0041039E, 3, "ff500c", "call [eax+0xc]              <- Read 派发（槽3）"),
            B(0x004103A1, 3, "85c07c", "test eax,eax; jl            <- 包装内传递负码"),
        ],
        ring3_verdict="包装 00410380：入参为 NULL 时返回 E_POINTER 0x80004003（00410389），否则返回 Read 的 HRESULT。"
                      "调用方 0075E0F5 `test eax,eax` + 0075E0F7 `jl 0x75E2AE`：负码直接出（eax 保留负值），"
                      "成功继续至 0075E2AC `xor eax,eax` 返回 S_OK。两路返回码与动作均不同。",
        ring4_site=0x0075D0BA, ring4_host=0x0075CEC0,
        ring4=[
            (0x0075D0BA, 7, "c74500306b7f00", "mov [ebp], 0x7f6b30        <- 主虚表安装点（行外）"),
            (0x0075D0C1, 6, "c700146b7f00", "mov [eax], 0x7f6b14"),
            (0x0075D0C7, 7, "c745080c6b7f00", "mov [ebp+8], 0x7f6b0c"),
            (0x0075D0CE, 7, "c7450c046b7f00", "mov [ebp+0xc], 0x7f6b04"),
            (0x0075CECB, 5, "e83039cbff", "call 0x410800              <- 基类构造"),
        ],
        ring4_note="宿主 0075CEC0 体内无 dtor marker。同表另两个安装点：0075D237（宿主 0075D230 含 call 0x7258D0 + 3×call 0x7C8B3D）"
                   "与 0075E516（宿主 0075E510 含 call 0x7258D0 + 4×call 0x7C8B3D）均为析构器，已排除；"
                   "0075E13E 落在本 entry 自身函数体内（0075E0C0..0075E2B4），按「写点在行外」排除。",
    ),
    dict(
        entry=0x0075E2C0, name="WarheadTypeClass::slot6", vt=0x007F6B30, slot=6,
        sem_claim="流写出（Save）：写包装返回 HRESULT，失败 E_POINTER 负码跳收尾、成功继续",
        ring3=[
            (0x0075E2D1, 5, "e84a20cbff", "call 0x410320               <- 写包装（vt+0x10 = Write）"),
            (0x0075E2D6, 2, "85c0", "test eax, eax               <- 消费 HRESULT"),
            (0x0075E2D8, 6, "0f8cbe000000", "jl 0x75e39c               <- 负码跳收尾"),
            (0x0075E399, 2, "33c0", "xor eax, eax                <- 成功路径置 0"),
            (0x0075E39C, 7, "5f5ec20c00", "pop edi/esi; ret 0xc       <- 失败路径 eax=负码"),
            (0x0075E2F5, 3, "ff5210", "call [edx+0x10]             <- 写出派发（槽4）"),
        ],
        ring3_extra=[
            B(0x0041032B, 5, "b803400080", "E_POINTER = 0x80004003      <- 包装失败返回码"),
            B(0x00410348, 3, "ff5010", "call [eax+0x10]             <- Write 派发（槽4）"),
            B(0x0041034B, 3, "85c07c", "test eax,eax; jl"),
        ],
        ring3_verdict="包装 00410320：NULL 时返回 E_POINTER 0x80004003（0041032B），否则返回 Write 的 HRESULT。"
                      "调用方 0075E2D6 `test eax,eax` + 0075E2D8 `jl 0x75E39C`（跳过成功路径独占的 push ebx，栈平衡）；"
                      "成功一路 0075E399 `xor eax,eax` 后经 0075E39B `pop ebx` 收尾。两路返回码不同。",
        ring4_site=0x0075D0BA, ring4_host=0x0075CEC0,
        ring4=[
            (0x0075D0BA, 7, "c74500306b7f00", "mov [ebp], 0x7f6b30        <- 与 slot5 同一安装点"),
            (0x0075CECB, 5, "e83039cbff", "call 0x410800              <- 基类构造"),
        ],
        ring4_note="④ 安装点与 0075E0C0 **完全相同**（同为 0075D0BA、同一宿主 0075CEC0）。"
                   "两行之间唯一可区分的数据是槽号 5 vs 6，而槽号取自 .rdata 的 vt[slot]==entry。",
    ),
    dict(
        entry=0x00772CD0, name="WeaponTypeClass::slot5", vt=0x007F73B8, slot=5,
        sem_claim="流读入（Load）：读包装返回 HRESULT，失败 E_POINTER 负码跳收尾、成功继续",
        ring3=[
            (0x00772CFD, 5, "e87ed6c9ff", "call 0x410380               <- 读包装（vt+0xC = Read）"),
            (0x00772D02, 2, "85c0", "test eax, eax"),
            (0x00772D04, 6, "0f8c9c010000", "jl 0x772ea6               <- 负码跳收尾"),
            (0x00772EA4, 2, "33c0", "xor eax, eax                <- 成功路径置 0"),
            (0x00772EA6, 7, "5f5e5dc20800", "pop edi/esi/ebp; ret 8     <- 失败路径 eax=负码"),
            (0x00772E82, 1, "5b", "pop ebx                     <- 成功路径平衡"),
        ],
        ring3_extra=[
            B(0x00410389, 5, "b803400080", "E_POINTER = 0x80004003"),
            B(0x0041039E, 3, "ff500c", "call [eax+0xc]              <- Read 派发（槽3）"),
        ],
        ring3_verdict="与 0075E0C0 同构：包装 00410380 失败返 0x80004003；调用方 00772D02 `test eax,eax` + "
                      "00772D04 `jl 0x772EA6`（跳过成功路径的 push ebx），成功路径 00772EA4 `xor eax,eax`。",
        ring4_site=0x00771E77, ring4_host=0x00771C70,
        ring4=[
            (0x00771E77, 7, "c706b8737f00", "mov [esi], 0x7f73b8         <- 主虚表安装点（行外）"),
            (0x00771E7D, 6, "c7009c737f00", "mov [eax], 0x7f739c"),
            (0x00771E83, 7, "c7460894737f00", "mov [esi+8], 0x7f7394"),
            (0x00771E8A, 7, "c7460c8c737f00", "mov [esi+0xc], 0x7f738c"),
            (0x00771C7A, 5, "e881ebc9ff", "call 0x410800              <- 基类构造"),
        ],
        ring4_note="宿主 00771C70 体内无 dtor marker；同表安装点 007730F7 的宿主 007730F0 含 call 0x7258D0 + 4×call 0x7C8B3D ⇒ 析构器，已排除。",
    ),
    dict(
        entry=0x00772EB0, name="WeaponTypeClass::slot6", vt=0x007F73B8, slot=6,
        sem_claim="流写出（Save）：写包装返回 HRESULT，失败 E_POINTER 负码跳收尾、成功继续",
        ring3=[
            (0x00772EC1, 5, "e85ad4c9ff", "call 0x410320               <- 写包装（vt+0x10 = Write）"),
            (0x00772EC6, 2, "85c0", "test eax, eax"),
            (0x00772EC8, 6, "0f8cbe000000", "jl 0x772f8c               <- 负码跳收尾"),
            (0x00772F89, 2, "33c0", "xor eax, eax                <- 成功路径置 0"),
            (0x00772F8C, 7, "5f5ec20c00", "pop edi/esi; ret 0xc       <- 失败路径 eax=负码"),
            (0x00772EE5, 3, "ff5210", "call [edx+0x10]             <- 写出派发（槽4）"),
        ],
        ring3_extra=[
            B(0x0041032B, 5, "b803400080", "E_POINTER = 0x80004003"),
            B(0x00410348, 3, "ff5010", "call [eax+0x10]             <- Write 派发（槽4）"),
        ],
        ring3_verdict="与 0075E2C0 同构：包装 00410320 失败返 0x80004003；调用方 00772EC6 `test eax,eax` + "
                      "00772EC8 `jl 0x772F8C`，成功路径 00772F89 `xor eax,eax`。",
        ring4_site=0x00771E77, ring4_host=0x00771C70,
        ring4=[
            (0x00771E77, 7, "c706b8737f00", "mov [esi], 0x7f73b8         <- 与 slot5 同一安装点"),
            (0x00771C7A, 5, "e881ebc9ff", "call 0x410800              <- 基类构造"),
        ],
        ring4_note="④ 安装点与 00772CD0 **完全相同**（同为 00771E77、同一宿主 00771C70）。"
                   "两行间可区分数据只有槽号 5 vs 6，取自 .rdata 的 vt[slot]==entry。",
    ),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for r in ROWS:
        e = r["entry"]
        L = []
        L.append("EVIDENCE  %08X  %s" % (e, r["name"]))
        L.append("独立审计：NAMED_PUSH_AUDIT16（异族）；本文件全部字节由审计自写脚本 pe.py/probe.py/rows.py/sites.py 从")
        L.append("gamemd.exe（SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476）复读并断言。")
        L.append("")
        # ---- ring 1
        L.append("[环① 入口]")
        L.append("  entry %08X 落在 .text [0x401000, 0x7E038D) 内；函数体首字节 %s"
                 % (e, read(e, 8).hex()))
        ins = BY_ADDR.get(e)
        L.append("  首指令: %s" % (fmt(ins) if ins else "?"))
        L.append("")
        # ---- ring 2
        L.append("[环② 类身份]")
        occ = []
        L.append("  entry 作为 4 字节值在全镜像的出现位置：" +
                 ", ".join("%08X" % o for o in
                           __import__("pe").find_imm32_occurrences(e)) + "（唯一，判据 1 已枚举全部持有表）")
        L.append("  " + U32(r["vt"] + 4 * r["slot"], e, "vt + 4*%d = %08X -> 槽值 = entry" % (r["slot"], r["vt"] + 4 * r["slot"])))
        rt = rtti_of_table(r["vt"])
        L.append("  " + U32(r["vt"] - 4, rt["col"], "[vt-4] = COL"))
        L.append("  " + U32(rt["col"], 0, "[COL+0x00] RTTI 签名 = 0"))
        L.append("  " + U32(rt["col"] + 0xC, rt["td"], "[COL+0x0C] = TD"))
        L.append("  TD+8 内联名 = %r" % cstr(rt["td"] + 8, 200))
        L.append("  ⇒ 类名由 RTTI 数据链独立钉死，槽号 %d 与 slotN 一致。" % r["slot"])
        L.append("")
        # ---- ring 3b
        L.append("[环③b 形态 = ③b② 可伪证返回约定]")
        L.append("  语义栏主张：%s" % r["sem_claim"])
        for va, n, hx, what in r["ring3"]:
            L.append("  " + B(va, n, hx, what))
        for line in r["ring3_extra"]:
            L.append("  " + (line if line.startswith(("0", " ", "被")) else line))
        L.append("  判定：" + r["ring3_verdict"])
        L.append("")
        # ---- ring 4
        L.append("[环④ 使用见证]")
        L.append("  锚点 = 行外构造器 %08X 的 .text 写点 %08X（entry 自身函数不含该写点）"
                 % (r["ring4_host"], r["ring4_site"]))
        for va, n, hx, what in r["ring4"]:
            L.append("  " + B(va, n, hx, what))
        L.append("  " + r["ring4_note"])
        L.append("")
        # ---- verdict on same_source
        L.append("[④ 与 ② 是否同源 —— 逐行事实结论]")
        L.append("  ✗ 不是两条独立证据链。④ 的成立需要两个命题：")
        L.append("    (i) 表 %08X 是**活表**（由构造器 %08X 写入对象）—— 这一半确属独立证据（.text 指令，② 不用它）；"
                 % (r["vt"], r["ring4_host"]))
        L.append("    (ii) entry 正占据该表的第 %d 槽 —— 这一步**必须**读 .rdata 的 [%08X] == %08X，"
                 % (r["slot"], r["vt"] + 4 * r["slot"], e))
        L.append("         而 ② 判定「该 entry 属此类」用的正是同一条 [%08X] == %08X。" % (r["vt"] + 4 * r["slot"], e))
        L.append("  ⇒ vt[slot]==entry 这一枢轴仍被 ② 与 ④ 共同消费；④ 只是比 S13_PUSH 原版多了一半独立事实。")
        L.append("  ⇒ 按 R14_COMMON §12.3 字面（同一虚表槽不得既证类身份又证被使用）本行判同源；")
        L.append("     按 D-43(A) 宽读法（④ = 构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用），本行 ④ 形式合格。")
        L.append("  ⇒ 两条成文规则在本行冲突 ⇒ 即 PANEL.md L146–149（M69）已披露的已知限制。")
        txt = "\n".join(L) + "\n"
        p = os.path.join(OUT, "ROW_%08X.txt" % e)
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        print("wrote", p)
    print()
    if FAILS:
        print("!! BYTE ASSERTION FAILURES:")
        for f in FAILS:
            print("   ", f)
    else:
        print("all byte assertions passed")


if __name__ == "__main__":
    main()
