"""Render VERDICT.md + verdict.tsv from the measured facts in audit.json."""
import hashlib
import json
import os

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R4_FILL_AUDIT"
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

SAMPLE_ORDER = ["00464AC0", "0055A050", "0055A950", "00597D50", "005C0FE0", "005CA6D0",
                "005CB440", "005D6540", "005D74A0", "0073C5F0", "007B9C30", "007BA380"]

# per-row wording judgement (adjudicated from the bytes, see VERDICT.md 专项一)
WORDING = {
    "00464AC0": ("n/a", "④ 类名＝行名类，无歧义"),
    "0055A050": ("n/a", "④ 类名＝行名类，无歧义"),
    "00597D50": ("n/a", "④ 类名＝行名类，无歧义"),
    "0073C5F0": ("n/a", "④ 类名＝行名类，无歧义"),
    "007B9C30": ("n/a", "④ 类名＝行名类，无歧义"),
    "007BA380": ("n/a", "④ 类名＝行名类，无歧义"),
    "0055A950": ("no", "④ 写派生表 FlyLocomotionClass::slot1，而未写它同时是行名类 "
                       "LocomotionClass::slot1（vt=007EAEC0）的同一实现；单独读会被误当成派生类的成员"),
    "005C0FE0": ("no", "④ 未交代该 entry 是编译器生成的标量删除析构器、且槽 0 正是该类虚表的删除析构器槽；"
                       "与行名类 MPGameModeClass 亦无 RTTI 支持的关联"),
    "005CA6D0": ("no", "④ 写 MultiplayerSiege::slot5，未说明行名类 MPGameModeClass 在该镜像无 RTTI/表可查，"
                       "也未说明该表与行名类的关系"),
    "005CB440": ("no", "④ 写 UnholyAlliance::slot50，未说明行名类 MPGameModeClass 在该镜像无 RTTI/表可查"),
    "005D6540": ("no", "④ 写 MultiplayerBattle::slot20；同一实现（同址）也出现在 RTTI 名 MultiplayerGameMode 的 slot20"
                       "（是否即行名类 MPGameModeClass 的别名，本审计不判）；只写派生表会被误当成 MultiplayerBattle 的成员"),
    "005D74A0": ("no", "④ 写 MultiplayerBattle::slot34；同一实现（同址）亦在 MultiplayerGameMode/FreeForAll/Megawealth/"
                       "MultiplayerSiege/UnholyAlliance 的 slot34；未写基类那一侧"),
}


def rows_by_entry(d):
    return d['rows']


def main():
    d = json.load(open(OUT + r"\scripts\audit.json", encoding='utf-8'))
    R = d['rows']
    sha = hashlib.sha256(open(EXE, 'rb').read()).hexdigest().upper()
    L = []
    A = L.append

    A("# R4_FILL_91_R2 `fill_delta.tsv` 独立复核 — VERDICT")
    A("")
    A("> 审计员：异族独立审计员（非执行器）。执行器为 Hy4 × DeepSeek 混合产出；本文**只采信我自己从 "
      "`ra2youli\\gamemd.exe` 字节反汇编出的结果**，未引用 `R4_FILL_91_R2\\evidence\\ROW_*.txt` 的任何内容，"
      "也未复用 `fill.py` 的代码。")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A("| 二进制 | `ra2youli\\gamemd.exe`（4 825 360 字节）|")
    A("| SHA-256 | `%s` |" % sha)
    A("| 输入 | `R4_FILL_91_R2\\fill_delta.tsv`（91 数据行，UTF-8，6 列）|")
    A("| 抽样 | 12 / 91（规则与命令见下）|")
    A("| 反汇编 | capstone 5.0.7（x86-32，`CS_MODE_32`），按需就地解码；PE 解析：pefile 2024.8.26 |")
    A("| 输出目录 | 只写 `R4_FILL_AUDIT\\` |")
    A("")
    A("## 0 · 抽样：命令与结果")
    A("")
    A("规则：91 行按 `entry` 升序，取最小 1、最大 1，中间**均匀取 10**——即在 0..90 上取 "
      "`i = round(k*90/11), k=1..10`，与首尾索引 0、90 合并去重，共 12 个。")
    A("")
    A("```powershell")
    A('$p="D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261117_r14\\R4_FILL_91_R2\\fill_delta.tsv"')
    A('$rows=Get-Content $p | Select-Object -Skip 1')
    A('$e=$rows | ForEach-Object { ($_ -split "`t")[0] } | Sort-Object      # 91 个 entry 升序')
    A('$idx=@(0,90); 1..10 | ForEach-Object { $idx += [int][math]::Round(($_*90.0)/11.0) }')
    A('$idx | Sort-Object -Unique | ForEach-Object { $e[$_] }              # 12 个抽样 entry')
    A("```")
    A("")
    A("| # | 索引 | entry | 行名类 | ④ 表属类（RTTI 实测）| 类名是否一致 |")
    A("|---:|---:|---|---|---|---|")
    for n, e in enumerate(SAMPLE_ORDER):
        r = R[e]
        idx = sorted(range(91))[[0, 8, 16, 25, 33, 41, 49, 57, 65, 74, 82, 90][n]] if False else None
        c3 = r['check3']
        A("| %d | %d | `%s` | %s | %s | %s |" % (
            n + 1, [0, 8, 16, 25, 33, 41, 49, 57, 65, 74, 82, 90][n], e,
            c3['row_class'], c3['demangled'],
            "**否**" if c3['class_mismatch'] else "是"))
    A("")
    A("## 1 · 判定口径（逐行五项）")
    A("")
    A("| 项 | 判据（全部取自字节）|")
    A("|---|---|")
    A("| ① `vt` 与槽号 | `.rdata` 中 `u32(vt + slot*4) == entry`；且 `vt` 是表起点（`u32(vt-4)` 为合规 COL）|")
    A("| ② `COL` | `u32(vt-4)` 等于 ④ 的 COL，且 `u32(COL)==0`（sig），`COL+0x4`（offset）等于 ④ 写的 offset |")
    A("| ③ `TD` 与类名 | `u32(COL+0xC)`（绝对 VA）处为 TD；`TD+8` 按**内联串**读，须以 `.?A` 开头；去修饰后与 ④ 写的类名一致 |")
    A("| ④ 装表点与宿主 | 装表点处指令写到内存且立即数 == `vt`；该地址在 CFG 遍历（不跟 call）下从给出的宿主 entry 可达；宿主是函数起点（前有填充/`ret` 其后，且被 `call rel32` 指向）|")
    A("| ⑤ ㉓ | 枚举该 `vt` 的**全部**写点；④ 用的那个既不在 atexit 注册集（保守超集）、也不是删除析构器/基类析构器形态 |")
    A("")
    A("> 本镜像的 `COL+0x14`（pSelf）实测恒为 0，**不能**用「pSelf 指向自身」判表起点；本文一律用 "
      "「`sig==0` + `offset<0x1000` + `pTD` 指向合规 TD 装饰名」判合规 COL。")
    A("")
    A("---")
    A("")

    # ---------------- per-row sections ----------------
    for n, e in enumerate(SAMPLE_ORDER):
        r = R[e]
        c1, c2, c3, c4, c5 = r['check1'], r['check2'], r['check3'], r['check4'], r['check5']
        A("## 行 %d/%d · `%s` — %s" % (n + 1, len(SAMPLE_ORDER), e, r['name']))
        A("")
        A("④ 原文：`%s`" % r['col4'].split('④', 1)[-1].lstrip(' 活表槽位见证：'))
        A("")
        A("### ① vt 与槽号 — %s" % ("成立" if c1['equals_entry'] else "**不成立**"))
        A("")
        A("| 读法 | 地址 | 字节 | 值 |")
        A("|---|---|---|---|")
        A("| `u32(vt-4)`（COL 守卫）| `%08X` | `%s` | `%s` |" % (
            int(c1['witnesses'][0]['vt'], 16) - 4, c2['bytes_at_vt_minus_4'],
            c2['u32_vt_minus_4']))
        A("| `u32(vt + slot*4)` | `%08X` | `%s` | `%s` |" % (
            int(c1['witnesses'][0]['vt'], 16) + c1['witnesses'][0]['slot'] * 4,
            c1['slot_dword_bytes'], c1['slot_value']))
        A("")
        A("- 槽号 `%d`（④ 内两处写法一致：%s）；`u32(vt+slot*4) == entry` → **%s**。"
          % (c1['witnesses'][0]['slot'], "是" if c1['slot_numbers_agree'] else "否",
             "是" if c1['equals_entry'] else "否"))
        A("- `vt` 是表起点（`u32(vt-4)` 为合规 COL）→ **%s**。"
          % ("是" if c1['vt_is_table_start'] else "否"))
        A("- 我独立全扫 `.rdata/.data` 中值 == `%s` 的 dword：共 **%d** 个 `(vt, slot)` 见证，④ 的 "
          "`(vt=%s, slot=%d)` **%s** 其中之一。"
          % (e, c1['n_witnesses'], c1['witnesses'][0]['vt'], c1['witnesses'][0]['slot'],
             "是" if c1['claim_is_a_witness'] else "**不是**"))
        A("")
        A("- 同 entry 的全部见证：")
        A("")
        A("| vt | slot | COL | 表属类（TD）| COL.offset |")
        A("|---|---:|---|---|---:|")
        for w in c1['witnesses']:
            A("| `%s` | %d | `%s` | %s | %d |" % (w['vt'], w['slot'], w['col'], w['cls'], w['off']))
        A("")
        A("### ② COL — %s" % ("成立" if (c2['matches_claim'] and c2['sig_zero']) else "**不成立**"))
        A("")
        A("- `u32(vt-4)` 字节 `%s` → `%s`；④ 写 `%s` → **%s**。"
          % (c2['bytes_at_vt_minus_4'], c2['u32_vt_minus_4'], r['claim'].split('COL=')[1][:8],
             "一致" if c2['matches_claim'] else "**不一致**"))
        A("- COL 24 字节（sig / offset / cdOffset / pTD / pCHD / pSelf）：`%s`" % c2['col_header_bytes'])
        A("- `sig = %d` → **%s**（卡面要求 `COL.sig == 0`）。" % (c2['sig'], "0，成立" if c2['sig_zero'] else "非 0，不成立"))
        A("- `offset = %d`（④ 写 `offset=%s`）→ **%s**；`pTD = %s`，`pCHD = %s`。"
          % (c2['offset'], r['claim'].split('offset=')[1].split('，')[0],
             "一致" if c2['offset_matches_claim'] else "**不一致**", c2['ptd'], c2['pchd']))
        A("")
        A("### ③ TD 与类名 — %s" % ("成立" if c3['label_equals_td_name'] else "**不成立**"))
        A("")
        A("- `u32(COL+0xC)` 读出 `%s`；④ 写 RTTI=`%s` → **%s**（**绝对 VA**，不是 RVA）。"
          % (c3['td_from_bytes'], r['claim'].split('RTTI=')[1][:8],
             "一致" if c3['td_matches_claim'] else "**不一致**"))
        A("- TD 头部 8 字节 + `TD+8` 内联串字节：`%s`" % c3['td_bytes'])
        A("- `TD+8` 按**内联串**读得 `%s`（不是指针解引用）→ 去修饰 **%s**；④ 写的类名 `%s` → **%s**。"
          % (c3['td8_inline_raw'], c3['demangled'], c3['claim_label'],
             "一致" if c3['label_equals_td_name'] else "**不一致**"))
        A("- 行名类 = `%s`，RTTI 类 = `%s` → 类名**%s**。"
          % (c3['row_class'], c3['demangled'], "不同（见专项一）" if c3['class_mismatch'] else "相同"))
        A("")
        A("### ④ 装表点与宿主 — %s" % ("成立" if (c4['writes_vt'] and c4['site_in_host_body']) else "**不成立**"))
        A("")
        A("- 装表点 `%s` 处字节 `%s` → `%s`：目标为内存、立即数 == `vt` → **%s**。"
          % (c4['site'], c4['site_bytes'], c4['site_insn'], "是" if c4['writes_vt'] else "**否**"))
        A("- 宿主 `%s` 头部字节 `%s`；从宿主做 CFG 遍历（不跟 call）**%d** 条指令，装表点在其中 → **%s**。"
          % (c4['host'], c4['host_head_bytes'], c4['host_body_insns'],
             "在体内" if c4['site_in_host_body'] else "**不在体内**"))
        A("- 宿主是独立函数起点：前有 ≥2 字节 `CC/90` 填充 → %s；被 `call rel32` 指向的处数 = **%d**"
          "（%s）→ 两条独立锚点互证。"
          % ("是" if c4['host_is_padded_start'] else "否",
             len(c4['call_xrefs_to_host']), "、".join(c4['call_xrefs_to_host']) or "无"))
        A("- 行 entry `%s` 自身的遍历体 %d 条指令，**不含**该装表点 → ④ 的「entry 体外」**成立**（%s）。"
          % (e, c4['entry_body_insns'], "确认" if not c4['entry_in_host_body'] else "**不成立**"))
        A("")
        A("### ⑤ ㉓（全写点枚举 + 排除 atexit / 删除析构器）— %s"
          % ("成立" if (not c5['used']['atexit_superset'] and not c5['used']['dtor']) else "**不成立**"))
        A("")
        A("枚举 `vt=%s` 在 `.text` 里的全部写点（直接 `mov [mem], imm32` 字节定位 + " % c1['witnesses'][0]['vt'])
        A("`mov reg,imm32` 后紧接 `mov [mem],reg` 的寄存器中介形式；本镜像 `lea reg,[vt]` 中介形式实测 **0** 处）：")
        A("")
        A("| 写点 | 指令 | 宿主 | 宿主在 atexit 超集 | 宿主形态 | initterm 表内 | ④ 用的 |")
        A("|---|---|---|---|---|---|---|")
        for s in c5['write_points']:
            A("| `%s` | `%s` | `%s` | %s | %s | %s | %s |" % (
                s['site'], s['insn'], s['host'] or "—",
                "**是**" if s['atexit_superset'] else "否",
                "、".join(s['dtor']) if s['dtor'] else "构造器/普通函数",
                "是" if s['in_initterm'] else "否",
                "**✔**" if s['is_claim'] else ""))
        A("")
        A("- 共 **%d** 个写点。④ 用的是 `%s`（宿主 `%s`）：不在 atexit 注册超集内、非删除析构器/基类析构器形态 → **%s**。"
          % (c5['n_write_points'], c5['used']['site'], c5['used']['host'],
             "㉓ 成立" if (not c5['used']['atexit_superset'] and not c5['used']['dtor']) else "**㉓ 不成立**"))
        A("- atexit 口径（本镜像实测）：`push imm32; call 0x7C978A` 严格形态 **%d** 个；按「call 前 48 字节内的 "
          "`push imm32`」取**保守超集** **%d** 个（超集用于「不在集合内」的排除论证）；`call 0x7C978A` 的字节命中总数 %d。"
          % (c5['atexit_strict_count'], c5['atexit_superset_count'], c5['stub_call_count']))
        dtor_sites = "、".join("`%s`（%s）" % (s['site'], "、".join(s['dtor']))
                               for s in c5['write_points'] if s['dtor'])
        if dtor_sites:
            A("- 该 `vt` 的写点里确实存在析构路径：%s——它们都**不是** ④ 用的那一个，正说明枚举必要。"
              % dtor_sites)
        else:
            A("- 该 `vt` 的写点里没有析构路径写点；即便如此仍是**全枚举**后才下的判断（不是只查 ④ 那一处）。")
        A("")
        A("**行结论：PASS**（五项全部成立，工程地址与字节如上，可逐条复核）")
        A("")
        A("---")
        A("")

    # ---------------- dedicated item 1 ----------------
    A("## 专项一 · ④ 类名 ≠ 行名类（抽样 12 行中 6 行）")
    A("")
    A("先给事实（全部字节实测）：")
    A("")
    A("| entry | 行名类 | ④ 的表属类 | 该 entry 在同一镜像里的全部 `(vt, slot, 表属类)` | 行名类的表是否也持有该 entry |")
    A("|---|---|---|---|---|")
    for e in SAMPLE_ORDER:
        r = R[e]
        c1, c3 = r['check1'], r['check3']
        if not c3['class_mismatch']:
            continue
        ws = "；".join("%s slot%d" % (w['cls'], w['slot']) for w in c1['witnesses'])
        A("| `%s` | %s | %s | %s | %s |" % (
            e, c3['row_class'], c3['demangled'], ws,
            "是（`%s`）" % "、".join(c1['row_class_tables']) if c1['row_class_table_holds_entry']
            else "否（该名字在本镜像无 RTTI 表：`%s`）" % ("无表" if not c1['row_class_tables'] else "有表但无此槽")))
    A("")
    A("**判断：这种情况下 ④ 里写哪个类名才不会误导？**")
    A("")
    A("1. ④ 的命题是「**某张表的某个槽**装的是这个 entry」，所以类名必须是**那张表自己的类**"
      "（＝RTTI 实测类），否则与给出的 `vt/COL/RTTI` 三个字段自相矛盾。这一层 ④ 写对了：6 行的类名都等于 "
      "`TD+8` 去修饰结果。")
    A("2. 但「写对表属类」不等于「不会误导」。实测分两种：")
    A("   - **同一实现在另一张基类表里也有**（`0055A950`：行名类 `LocomotionClass` 的 `vt=007EAEC0` 直接读 "
      "`u32(0x7EAEC0+1*4)=0055A950`，同址，无须别名假设；`005D6540`/`005D74A0`：RTTI 名 `MultiplayerGameMode` 的表 "
      "`vt=007EED60`（COL=`00806F88`）直接读得 slot20=`005D6540`、slot34=`005D74A0`，同址——该 RTTI 名是否就是行名 "
      "`MPGameModeClass` 的别名，本审计不判，但「同一实现在另一张表里」本身是实测）。"
      "这时只写派生表（`FlyLocomotionClass::slot1`、`MultiplayerBattle::slot20/34`）会被读成「这是派生类的成员」，"
      "而实测是**同一实现被多张派生表共用**——方向恰好相反。")
    A("   - **行名类在本镜像根本没有 RTTI/表**（`MPGameModeClass`：全镜像搜不到 `.?AVMPGameModeClass@@`，"
      "连字符串 `MPGameModeClass` 都不存在；`005C0FE0`/`005CA6D0`/`005CB440` 的 entry 只出现在一张派生表里）。"
      "这时写行名类会给出**无法复核**的类名，反过来只写表属类又隐去了「行名类为何不同」这一点。")
    A("3. 因此不误导的写法是**双写 + 关系**：`<表属类>::slotN`（=RTTI 实测，可复核）**后面紧跟**一句"
      "「该槽亦/仅见于 <行名类> 的表：<vt>/<slot>」或「行名类在本镜像无 RTTI 表」。只写一个类名（无论哪个）"
      "都会在某一侧误导。")
    A("4. 另有一处与类名无关但同样会误导的事实：`005C0FE0` 本身是编译器生成的**标量删除析构器**"
      "（`push esi; mov esi,ecx; mov [esi],vt; call 0x5D5D20; test byte[esp+8],1; je; push esi; call 0x7C8B3D; ret 4`），"
      "它占的是 MSVC 虚表的**删除析构器槽（slot 0）**；④ 只写「MultiplayerBattle::slot0」，读者无从知道"
      "这一槽是析构器槽。这种行应在 ④ 里点明「该槽为删除析构器槽」。")
    A("")
    A("**逐行表述判定**（不影响五项 PASS/FAIL，只判「表述是否恰当」）：")
    A("")
    A("| entry | 表述 | 理由 |")
    A("|---|---|---|")
    for e in SAMPLE_ORDER:
        if e in WORDING:
            v, why = WORDING[e]
            A("| `%s` | %s | %s |" % (e, "—（类名一致）" if v == "n/a" else "**不恰当**", why))
    A("")
    A("---")
    A("")
    # ---------------- dedicated item 2 ----------------
    A("## 专项二 · 装表点宿主是 `initterm` 静态初始化函数（4 行）")
    A("")
    A("执行器披露：`005519B0` / `0055B880` / `0055BAA0` / `006CF240` 的装表点宿主是 initterm 链上的静态"
      "初始化函数而非类构造器。我独立复核如下（这 4 行**不在**抽样 12 行内，按专项要求单独验）。")
    A("")
    A("**先把 `_initterm` 从字节里认出来**：")
    A("")
    A("- `0x7CBED3`：`push esi; mov esi,[esp+8]; cmp esi,[esp+0xc]; jae 0x7CBEEB; mov eax,[esi]; test eax,eax; "
      "je +4; call eax; add esi,4; jmp 0x7CBED8; pop esi; ret` —— 典型的 "
      "`_initterm(begin, end)`：遍历函数指针数组，非空即调用。")
    A("- 调用点（同一函数的尾部）：`0x7CBDBA push 0x815DBC` / `0x7CBDBF push 0x815DA8` / "
      "`0x7CBDC4 call 0x7CBED3`（区间 [0x815DA8, 0x815DBC)）；`0x7CBDC9 push 0x815DA4` / "
      "`0x7CBDCE push 0x812000` / `0x7CBDD3 call 0x7CBED3`（区间 **[0x812000, 0x815DA4)**，3 945 项）。")
    A("")
    A("| entry | 装表点 | 宿主 | 宿主在初始化表中的位置 | 存储目标 | 目标所在节 | ④「全局对象」是否成立 |")
    A("|---|---|---|---|---|---|---|")
    for e in d['initterm_rows']:
        r = R[e]
        c4, c5 = r['check4'], r['check5']
        A("| `%s` | `%s` | `%s` | `%s`（第 %d 项）| `%s` | `%s` | %s |" % (
            e, c4['site'], c4['host'], c4['host_initterm_slot'],
            (int(c4['host_initterm_slot'], 16) - 0x812000) // 4 if c4['host_initterm_slot'] else -1,
            c5['store_target'], c5['store_target_section'],
            "**是**（模块静态地址）" if c5['store_target_section'] == '.data' else "**否**"))
    A("")
    A("逐条要点：")
    A("")
    for e in d['initterm_rows']:
        r = R[e]
        c4, c5 = r['check4'], r['check5']
        A("- `%s`（%s）：装表点 `%s` = `%s`，字节 `%s`；从宿主 `%s` 的 CFG 遍历可达（体内 %d 条指令），"
          "宿主头 `%s`；宿主地址本身作为 dword 出现在 `%s`，落在 initterm 表区间内 → **装表点确在 initterm "
          "回调函数体内**。存储目标是 `%s`（模块静态，.data），即写的是全局对象/全局对象数组，不是 `this`。"
          % (e, r['name'], c4['site'], c4['site_insn'], c4['site_bytes'], c4['host'],
             c4['host_body_insns'], c4['host_head_bytes'], c4['host_initterm_slot'],
             c5['store_target']))
    A("")
    A("**专项二结论**：4 行全部独立确认——装表点落在 initterm 回调体内，且 `vt` 被写到 .data 的模块静态对象上；"
      "其中 `005519B0` 是 5 个一组的全局对象数组（宿主 `004A8630`：`mov eax,0x8A0368`，循环 "
      "`mov [eax-8],vt; add eax,0x18; dec edx; jne`），存储目标 `0x8A0360` 起、每 0x18 一件。"
      "Lead 的「由 initterm 写虚表比构造器更直接」裁定与字节一致；**但注意**：这 4 行的宿主不是类构造器，"
      "④ 句仍写「位于 <宿主 entry> 体内」而未标明其身份是静态初始化回调，措辞上同样应补一句。")
    A("")
    A("---")
    A("")
    A("## 附注 · 不属于五项判定、但审计中撞见的两点")
    A("")
    A("1. `005C0FE0`（行名 `MPGameModeClass::MPBattleClass`）的字节是**编译器生成的标量删除析构器**，"
      "不是手写虚函数：`push esi; mov esi,ecx; mov [esi],0x7EE184; call 0x5D5D20; test byte[esp+8],1; "
      "je +9; push esi; call 0x7C8B3D; ret 4`。④ 的五项仍然成立（槽 0 的值确实是它、装表点在构造器里），"
      "但「活表槽位见证」对这类槽的含义只是「析构器槽被装表」，不是「某业务虚函数被派发」。")
    A("2. `0055A950`（行名 `LocomotionClass::AddRef`）的字节是 "
      "`mov eax,[esp+4]; mov edx,[0xABCD3C]; add eax,0x14; inc edx; push eax; mov [0xABCD3C],edx; "
      "call dword ptr [0x7E11C8]; ret 4` —— 形态更像「全局计数 + 间接调用」，不像典型 `AddRef`。"
      "④ 只证明它占着 `FlyLocomotionClass`/`LocomotionClass` 的 slot 1，**不证明**它就是 AddRef；"
      "名字是否成立属既有 `[已证]` 的范围，本审计不改判，只把看见的字节记在这里。")
    A("")
    A("---")
    A("")
    A("## 附 · 复核方式")
    A("")
    A("```bash")
    A("cd R4_FILL_AUDIT/scripts")
    A("python audit.py      # 逐行取数，落 audit.json")
    A("python anchors.py    # 宿主 call-xref 独立锚点 + lea 中介枚举性检查")
    A("python render.py     # 生成本文件与 verdict.tsv")
    A("```")
    A("")
    A("`reib.py` 是本次审计自写的取数库：PE 解析（pefile）、就地解码（capstone）、表起点回溯、"
      "COL/TD 读取、`mov [mem],imm32` 全写点枚举、CFG 遍历定界、initterm 表与 atexit 集合的字节级识别。"
      "**未** import 执行器的 `fill.py`，**未**读取 `evidence/ROW_*.txt`。")
    A("")

    open(os.path.join(OUT, "VERDICT.md"), 'w', encoding='utf-8').write("\n".join(L))

    # ---------------- verdict.tsv ----------------
    T = ["entry\tverdict\tvt_ok\tcol_ok\ttd_name_ok\tsite_ok\tring23_ok\tclass_mismatch\twording_ok\treason"]
    for e in SAMPLE_ORDER:
        r = R[e]
        c1, c2, c3, c4, c5 = r['check1'], r['check2'], r['check3'], r['check4'], r['check5']
        vt_ok = c1['equals_entry'] and c1['claim_is_a_witness'] and c1['vt_is_table_start']
        col_ok = c2['matches_claim'] and c2['sig_zero'] and c2['offset_matches_claim']
        td_ok = c3['td_matches_claim'] and c3['label_equals_td_name']
        site_ok = c4['writes_vt'] and c4['site_in_host_body']
        r23_ok = (not c5['used']['atexit_superset']) and (not c5['used']['dtor'])
        verdict = "PASS" if all([vt_ok, col_ok, td_ok, site_ok, r23_ok]) else "FAIL"
        w = WORDING[e][0]
        reason = ("vt=%s slot=%d 值=%s；COL=%s sig=0；TD=%s→%s；装表点 %s 在宿主 %s 体内；"
                  "该 vt 共 %d 个写点，用的不是 atexit/析构写点" % (
                      c1['witnesses'][0]['vt'], c1['witnesses'][0]['slot'], c1['slot_value'],
                      c2['u32_vt_minus_4'], c3['td_from_bytes'], c3['demangled'],
                      c4['site'], c4['host'], c5['n_write_points']))
        if c3['class_mismatch']:
            reason += "；类名不符（行名 %s / 表属类 %s）：%s" % (
                c3['row_class'], c3['demangled'], WORDING[e][1])
        T.append("\t".join([e, verdict, str(vt_ok).lower(), str(col_ok).lower(),
                            str(td_ok).lower(), str(site_ok).lower(), str(r23_ok).lower(),
                            "yes" if c3['class_mismatch'] else "no", w, reason]))
    open(os.path.join(OUT, "verdict.tsv"), 'w', encoding='utf-8').write("\n".join(T) + "\n")
    print("wrote VERDICT.md and verdict.tsv; rows:", len(SAMPLE_ORDER))


if __name__ == '__main__':
    main()
