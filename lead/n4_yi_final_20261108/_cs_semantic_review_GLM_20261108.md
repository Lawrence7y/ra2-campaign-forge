# 候选语义层重签审阅回件 · GLM（独立复核，新上下文）

- 日期：2026-11-08　性质：**独立候选审阅（只审不签放行）**——按乙 V2 任务书五项必查逐条全查，非抽查。
- 签署性质仅限「**候选语义层 YES**」：不签 `APPROVE_SCOPE`、不应用母本、不放行 N-5。
- 执行者≠核验者：本轮全部脚本为审阅员本轮新写（stdin 内联 `python -I -X utf8`），未复用 R3 探针 / `_n4_ast_scan.py` / `_draft_semantics_check.py` / 定版员脚本；候选全程 **未 import、未执行**（AST 静态提取 + 行文本 difflib）。
- 零真机、零采样代码；母本/候选/设计/矩阵/V2/草案/补登/裁决/台账零改动；不 commit、不 push。

## 0 被核对象与基线指纹（本轮实算，`python -I -X utf8` + hashlib，逐件读字节）

| 对象 | SHA256 | 字节数 | 与编排方锚 |
|:--|:--|--:|:--|
| **被核对象·候选** `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | **412759** | 一致 |
| 被核对象·母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 | 一致 |
| 被核对象·V2 正文 `_n4v2_B_EXECUTION_SPEC_V2.md` | `c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801` | 28897 | 一致 |
| 被核对象·乙矩阵 `STATE_MATRIX.json` | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3558 | 一致 |
| CANDIDATE_LF.diff / B2B_DESIGN.md / 补登件 / 裁决书 / R3 / PENDING_DECISIONS / B_EXECUTION_SPEC_V2_YI.md | 11 件全部实算 | — | **11/11 与编排方指纹一致** |
| N-4 原文 `NEXT_STEPS_20261106.md` | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | 27225 | 与 V2 §2.1 绑定一致 |
| `_n4v2_ast_rerun_out.txt` ≡ `lead/bexec_n4_20261108/_n4_ast_scan_out.txt` | `9986fc2e335afa0748bfd9164c58c3eb04127c2f3db27b4e9fd91d5ee3cafdb6` | 22510 | **两件逐字节相等（本轮 diff 实跑 identical）** |

## 1 矩阵十四行逐行比对（三方：JSON ↔ V2 §4.2 ↔ 候选实码）

方法：`json.loads` 解析矩阵全文（14 数据行）＋正则提取 V2 §4.2 表 14 行（:117-130）＋ `ast.parse` 候选静态提取 `classify_except_freshness` 内全部 `_finish` 调用字面量（13 处）。实跑输出：**fully consistent rows: 14 / 14；code pairs not in matrix: set()；matrix pairs without code site: set()**。

| 文件行 | 乙 verdict | 乙 confidence | V2 逐行收录 | 取值一致 | 候选实码出口 |
|--:|:--|:--|:--|:--|:--|
| :2 | unknown | none | 是（V2:117） | 一致 | :4649 unknown/none |
| :3 | unknown | none | 是（V2:118） | 一致 | :4649 unknown/none |
| :4 | error_pre_snapshot | none | 是（V2:119） | 一致 | :4653 |
| :5 | post_read_error | none | 是（V2:120） | 一致 | :4644 |
| :6 | new_first_appearance | high | 是（V2:121） | 一致 | :4667 |
| :7 ★ | **absent_both** | **low** | 是（V2:122） | 一致 | **:4659 absent_both/low** |
| :8 | leftover_unchanged | high | 是（V2:123） | 一致 | :4691 |
| :9 ★ | leftover_unchanged | **medium**（mtime 侧缺失） | 是（V2:124） | 一致 | **:4687**（:4685-4689 `pre_mt/post_mt is None` 分支） |
| :10 | new_write | high | 是（V2:125） | 一致 | :4682 |
| :11 | rewritten_same_content | medium | 是（V2:126） | 一致 | :4697 |
| :12 | rewritten_same_content | low | 是（V2:127） | 一致 | :4694 |
| :13 | error_pre_snapshot（缺 pre.sha256） | none | 是（V2:128） | 一致 | :4674 |
| :14 | post_read_error（缺 post.sha256） | none | 是（V2:129） | 一致 | :4679 |
| :15 ★ | **vanished** | **none**（旗标） | 是（V2:130） | 一致 | **:4662 vanished/none** |

- 行数统计：完全一致 **14/14**；缺行 0；多行 0；取值不符 0。`usableAsCrashEvidence` 14 行全 False，与 `_finish` 硬编码 False（候选 :4628-4631）一致。
- 四个关键分支核对：absent_both=low（JSON:7/V2:122/码:4659）✓；vanished=none（JSON:15/V2:130/码:4662）✓；空快照=unknown/none（JSON:2-3/V2:117-118/码:4649，归一口 `:4634-4639` `st not in FRESHNESS_SNAPSHOT_STATES → "unknown"`）✓；mtime_pre 缺失=leftover_unchanged/medium（JSON:9/V2:124/码:4687）✓。**甲口径（absent_both,n/a、vanished,high、空快照折叠）在候选实码中零残留。**
- 值域：`FRESHNESS_VERDICTS` 9 值（候选 :223-226）、`FRESHNESS_CONFIDENCES` = high/medium/low/none 无 n/a（:227）、`FRESHNESS_SNAPSHOT_STATES` 4 态（:228）——本轮 grep 实证，与 V2 §4.1 相符。
- 保留登记（沿 R3:47/V2:132，非候选缺陷）：JSON:2 行 condition「跑后任意文件状态」措辞过宽——码序 read_error 出口（:4643）先于 unknown 出口（:4648），`pre=None + post.read_error` 实际落 post_read_error/none；14 行 verdict/confidence 值本身不受影响。

## 2 九 hunk 逐 hunk 比对

方法：实读 `CANDIDATE_LF.diff`（9 个 `@@` 头）＋ `B2B_DESIGN.md:662-670` §7 表＋ V2 §3.1 表（:81-89）；再以我自己的 `difflib.SequenceMatcher`（autojunk=False）对母本/候选全量行文本 diff 独立重算：**change blocks=12、deleted=13、added=255、net=242**，12 块逐一归因落进 9 个 hunk 的母本区间（212-217/4458-4463/4558-4565/4572-4591/5906-5912/5936-5942/6294-6299/6386-6391/7122-7128），**未归入块数=0**。

| Hunk | hunk 头（diff 行） | 母本锚点（V2§3.1=B2B§7） | 候选实际落点（本轮 difflib/实读） | 在范围内 |
|:--|:--|:--|:--|:--|
| H01 | `-212,6 +212,21`（:3） | :214 后插入 5 常量 | cand :215-229（+15）；常量在 :221-228 | ✓ |
| H02 | `-4458,6 +4473,10`（:25） | :4460 后追加 mtime_pre 留痕 | cand :4476-4478；`bak[name]` 三键 :4475/:4480 原样 | ✓ |
| H03 | `-4558,8 +4577,131`（:36） | :4561 前插入两函数＋:4561-4562 签名 | cand :4580-4700（+121）＋签名 :4702-4704 | ✓ |
| H04 | `-4572,20 +4714,105`（:169） | :4574-4599 函数体重写 | cand :4717-4791（-8+75）、:4795-4812（-1+18）、:4815（+1） | ✓ |
| H05 | `-5906,7 +6133,8`（:284） | :5909 finalize_trip 签名 | cand :6137 | ✓ |
| H06 | `-5936,7 +6164,8`（:294） | :5939 唯一调用点关键字传参 | cand :6167-6168（AST 实证 copy_post_except_evidence 调用点全文件恰 1 处） | ✓ |
| H07 | `-6294,6 +6523,9`（:304） | :6296 后、try 前预初始化 | cand :6526-6528（:6528 预初始化） | ✓ |
| H08 | `-6386,6 +6618,15`（:314） | :6388 后构造快照＋captured_at_iso_pre | cand :6621-6629（:6623-6624 赋值、:6625 落盘） | ✓ |
| H09 | `-7122,7 +7363,8`（:330） | :7125 后传给 finalize_trip | cand :7366-7367（finalize_trip 调用点全文件恰 1 处，AST 实证） | ✓ |

- 统计：**落在范围内 9/9**；越界 hunk 0；缺失 hunk 0。九 hunk 头与 V2 §3.1 / B2B §7 逐字一致；实测 +255/-13 与 R3:43、V2 §3.2-4、补登件 §5 一致；九 hunk `-` 侧覆盖区间均不含 E 判据块 5984-5990。
- ★ 登记一处 V2 文档措辞歧义（不阻断）：V2 §3.1:91「删除行数 0」——实测九 hunk 内删除 13 行（均在 H03/H04/H05/H06/H09 替换位）、范围外删除 0；V2 §3.2-4 自己写的是「+255/-13（R3:43）」。按「范围外删除=0」读则与实测一致，按字面「九 hunk 内删除=0」读则与 §3.2-4 冲突。属定版件文档精度事项，非候选缺陷。

## 3 候选实码与乙矩阵一致性（13 处 `_finish`）

AST 静态提取（未 import/未执行候选）：`_finish` 定义 1 处 :4628＋调用 13 处 :4644/:4649/:4653/:4659/:4662/:4674/:4679/:4682/:4687/:4691/:4694/:4697（与 R3:43、V2 §4.2:132 逐行一致）。逐处取值见 §1 表末列；11 个 (verdict,confidence) 对与矩阵 14 行的 11 个对**互为充要**（多 0、缺 0）。R3 点名的 6 处全部复核属实：:4659 absent_both/low、:4662 vanished/none、:4687 leftover_unchanged/medium、:4691 leftover_unchanged/high、:4694 rewritten_same_content/low、:4697 rewritten_same_content/medium。`is_new` 取值（None/False/True）与矩阵行语义同向（unknown/error/vanished → None）。

## 4 甲不再绑定核实

- V2 §3.2（:95-103）**明确写**「甲（B2_FIX_DESIGN.md 的 A—D 四处改动）自本件起不再绑定」，列 5 条理由（B2_PREAUDIT:17 verdict NO、:20-22 两条独立否决、甲设计 :198 自认未达可应用态、裁决 Q1:23＋补登件 §5 改登、现行候选按乙实现——按甲口径验收必 FAIL）；V2 §4.3（:134-145）甲→乙取值差异表逐项废止甲值；N-4:47 甲口径原文本轮实读确认被整体替代。
- 候选甲残留=0：① 本轮独立 difflib 证明候选=母本＋且仅＋H01–H09（12 块全落 9 区间、+255/-13；甲 A–D 为净增约 31 行的 4 处改动，若存在必产生额外块）——无夹带；② 全文 `n/a` 置信值残留 0（唯一 `[nN]/[aA]` 命中在候选 :7320 `rec.add("TERM","termination_verdict","N/A",…)`，与母本 :7079 同位逐字相同，属母本固有 TERM 字段值，非 FRESHNESS 置信域）；③ `B2_FIX_DESIGN`、`absent_both, n/a`、引号 `n/a` 全文 0 命中；④ verdict 值域 9 值/confidence 4 值均无 n/a（:223-228）。

## 5 禁止 API 与调用边

- **V2 §5.1（:163）与 N-4:49 原文逐项一致**（本轮实读两件）：十一禁止符号（MiniDumpWriteDump、SuspendThread、StackWalk／StackWalk64、ReadProcessMemory、WriteProcessMemory、VirtualAllocEx、CreateRemoteThread、SetWindowsHookEx、OpenProcess、TerminateProcess 及其包装／动态查找）＋ subprocess、os.system、ctypes 调用边＋禁止新增游戏发射与 taskkill 路径＋逐符号及调用边计数＋新增调用/导入/包装/动态解析均 FAIL＋字符串计数不能代替调用边审阅。唯一措辞差 = 「只许 A—D 内变动」→「只许 H01–H09 内变动」，系裁决 Q1＋补登件 §5 授权的替代，V2 §3.1:93 已声明授权链。
- `_n4v2_ast_rerun_out.txt` 实读：:623-633 十一符号 UNCHANGED（MiniDumpWriteDump 1/3/0/0、ReadProcessMemory 1/3/0/0、OpenProcess 5/15/0/0，余 0/0/0/0）；**:635「候选新增禁止边符号: 无」**；:639 subprocess.Popen 1→1；:641-664 ctypes 逐类一致；:666-668 getattr 13/13、importlib.util 2/2；:670-671 import 集合一致；:673 新增边 10 种/消失边 0（基线 536/候选 546）；:675-684 十条新增边全落 F 区；:612-618 存量 6 包装函数（母本既有）。且该件与 `_n4_ast_scan_out.txt` **逐字节相等**（本轮实跑比对）。
- **本轮另跑独立实现 AST 扫描**（我自己的四类计数＋全量调用边差集）：11 禁止符号 base==cand 全部 UNCHANGED；gamemd/ra2loader/taskkill 字符串常量计数 21/14/2 双方相等、YURI 与 os.system 0/0；subprocess.Popen 边 1→1；import 目标集合相等；ctypes 属性引用 301→301；调用边差集 **new=10 种 / gone=0 种**，10 种成员与计数（_finish×13、classify×3、make_pre×1、_emit_f×3、pre.get×4、post.get×4、post_observed.get×2、post_observed.update×1、out.update×1、src.stat×2）与 T3 输出 :675-684 完全一致，全部属 H03/H04 新鲜性逻辑与错误出口。**禁止符号 UNCHANGED 与新增禁止边=0 成立。**

## 结论

- **resign = YES（候选语义层）**：五项必查全部通过（14/14、9/9、13/13、甲残留 0、禁止边增量 0）。
- 边界（本 YES 不含）：不签 `APPROVE_SCOPE`、不应用母本、不放行 N-5；运行时行为未验（零真机/零采样，本判定为静态语义层）；T1/T2/T5 本轮未跑（T5 同类核验以 AST 静态提取替代 R3 的 fixture 实跑，方法不同、结论同向）。
- 未验项：母本既有 6 包装函数运行时行为；候选对母本的正式应用未发生（本轮母本指纹 517889c6…/399508 与绑定一致）。
