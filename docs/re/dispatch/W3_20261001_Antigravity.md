# W3_20261001 · 派工单 → **Antigravity**（Gemini-3.8-Flash · 思考强度 High · 文档落地轨 + 独立复验轨）

> 本卡可直接整段粘贴给 Antigravity。派工前缀遵循 `docs/re/AGENT_TASK_TEMPLATE.md`，回报格式遵循 `docs/re/AGENT_DELIVERY_FORMAT.md`。
> 共享权威输入：`docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md`（**开工前必读**）。

```text
【任务卡 W3-A · docs/re 勘误落地 + ATLAS 本体补证 + 第二方法独立复验（Antigravity 轮·4 包）】

◆ 执行方：Antigravity（Gemini-3.8-Flash，High）   ◆ 建议规模：主代理 + ≥4 个并行子代理（4 包互斥，可全并行）
◆ 工作区：D:\Project\ra2-campaign-forge（Windows）
◆ 前缀必读：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md（Lead 临时裁决 + 写域矩阵）
◆ 基线二进制（只读）
   ra2youli\gamemd.exe：sha256 73201cc021497c95…，MD5 4f37486e5b0dbe2ae5f45aeee0f98367，
   ImageBase 0x400000，.text VA 0x401000，FileOffset = VA − 0x400000 —— 【只读，禁止写盘】
   > 【W3-Lead勘误 E-W3-01】改前：FileOffset = VA − 0x400000；改后：FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)（本镜像 .text/.rdata/.data 为 VA − 0x400000，但 .rsrc/.detour 为 VA − 0x6FC000）；依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
   ra2youli\game.exe：sha256 c4bf2a57a80f…（原版件）

◆ 写作用域（越界即交付不合格）
  允许写：docs/re/**（W3 内 docs/re 的唯一写者就是你）
          out/re_work/agy/W3_20261001/**
  禁止写：ra2render/**、ra2youli/**、ra2bench/**、D:\Red2/**、YRpp/**、ref/**、tools/**、
          REVERSE_ENGINEERING_AND_PATCHES.md（顶层台账，Lead 独占）、
          out/re_work/qc/**（Qoder CN 写域，只读）、out/re_work/zcode_live/**（ZCode 写域，只读）
  纪律：需要改别人写域时**不要直接改**，写进回报 [3] 勘误清单交 Lead

◆ 绝对禁止
  1) 启动游戏 / 进程注入 / 挂调试器 / 改 gamemd.exe 或 game.exe
  2) 伪造「已实测」标记；用推测充当结论
  3) 越界写入；在 YRpp/ 内跑任何 git 命令
  4) 为「凑闭合」降低既有判据（例如把 UNVERIFIED 改写成 PASS）

◆ 证据标准
  [实证] = VA + FileOffset + 原始机器码字节 + Capstone 定点反汇编 + xref 调用点
  [推演] = 基于 ABI / EFLAGS / 栈平衡 / 编译器代码生成的严格推导
  [待实测] = 需真机；必须给可执行取证步骤与判定标准
  机器可读断言格式固定：0xVA = HEXBYTES # 注释

◆ 自证门禁（必须实跑并把原文输出贴进回报 [6] 节）
  python tools\verify_anchors.py                      → 须 323/323 PASS
  python tools\verify_hooks.py                        → 原文输出
  python tools\audit_bytes.py <你的 claims 文件>       → 须全 OK
  若本机 shell 起不来（pwsh 报 0xC0000142 / STATUS_DLL_INIT_FAILED），改用 cmd /c 或 python 直调并**如实记录**，不得静默跳过

◆ 回报格式：严格按 docs/re/AGENT_DELIVERY_FORMAT.md §A 的 10 节骨架
  [META]/[0]结论摘要/[1]逐条结论表/[2]证据块/[3]勘误/[4]未闭环/[5]作用域合规/[6]门禁原文/[7]风险红线/[8]交付物清单/[9]待裁决项
  缺节 = 交付不合格；勘误必须单列
  正文 ≤ 4 页（约 1500 字），细节进交付文档
```

---

## 包 1 · W3-A1 `docs/re` 勘误落地（**W3 内 docs/re 唯一写者**）

待落地的可审查文本块**全部已由 W2 Qoder CN 备好**（你只负责"落盘 + 自证"，不负责重新论证；但**必须抽验**）：

| 来源 | 内容 | 目标 |
|---|---|---|
| `out/re_work/qc/W2_20261001/errata/PATCH_SUGGESTIONS_for_docs_re.md` | **17 块**（每条含目标文件 + 锚点行原文前 40 字符 + 建议追加全文 + 分级） | 对应 `docs/re/*.md` |
| `out/re_work/qc/W2_20261001/keys/FREEZE_CANDIDATE.md` §9 | **16 处文档订正点**（C1–C7、C24 口径：`EnableGapProtection` 默认 0；`L4DirtyMode` 节名 `[FogOfWar]`，写 `[Render]` **结构性永不命中**；`EnableMinimapFog` 三处 ini 实测 0） | 各卡面文档 |
| `out/re_work/qc/W2_20261001/forge/PATCH_SUGGESTIONS.md` | **4 处**（`maplib` OverlayPack 无框 vs 官方 Format5 分包、LZO 单调用 >49152、`README:101` 措辞、`extracted/all_inis` 首行写坏） | `ra2forge` 相关文档 |
| `out/re_work/qc/W2_20261001/errata/ERRATA.md` + `verdicts/*.md` | 31 条逐条判定（仍成立 15 / 被推翻 2 / 已闭环 1 / 不可复核 2） | 相应文档加注 |

**落盘纪律（Lead 强制）**
1. **统一用「只加注、不删原文」范式**：在目标处追加 `> 【W3 勘误 · <来源>】改前：<原文摘>；改后：<新表述>；依据：<文件:行 / VA 字节>；分级：<级别>`
2. 凡据 §2 临时裁决改动处，**必须**追加标记 `[W3-Lead临时裁决]`。
3. **禁止**为图省事重写整段；**禁止**顺手改未经授权的内容（越界 = 交付不合格）。
4. 每条改动必须能被 `git diff --numstat` 级别的证据回溯：给出「改动文件 + 改动行区间 + 删改行数」。
5. 若某块的目标锚点行原文与 `PATCH_SUGGESTIONS` 记录**不一致**（说明文件已被他轮改动），**跳过该块并单列到回报 [3] 勘误**，不得强行落盘。

**验收**：逐块给出 `已落盘 / 跳过（原因）` 状态表；`python tools\verify_anchors.py` 仍 323/323 PASS（落盘不得破坏锚点）。

## 包 2 · W3-A2 `ARCHITECTURE_ATLAS.md` 本体补证（**本体单写者 = 你**）

- 来源：`out/re_work/qc/W2_20261001/atlas/atlas_patches/QC4_ch{08,09,16,17,21}_patches.md`（**154 条**优先子集）+ `atlas/claims/QC4_all_claims.txt`（143 条）。
- 分布：§16 62 / §17 45 / §8 17 / §9 7 / §21 23。
- **11 条 BSS 项按"降级改写"落盘**：只写区域断言 + 尺寸 + 改写建议，**不得**写代码语义（BSS 无文件 raw，写"原字节"必 NOREAD）。
- 纪律：语义证据 55 条 与 仅指令锚点 88 条**必须分别标注**（`[实证]` / `[推演]`）。**未用字节断言冒充语义已证。**
- 验收：`python tools\audit_bytes.py` 对合并 claims 全 OK；`python tools\atlas_va_crosscheck.py` 复跑并给出**覆盖前后**对照（预期 482→339 已在 W2 达成；本轮落盘后重算正文内生 VA 数）。
- 附带产出：`out/re_work/agy/W3_20261001/atlas/coverage_after_apply.md`（正文唯一 VA 数、被 claims 覆盖数、章级分布）。

## 包 3 · W3-A3 第二方法**独立复验**（只读，快，最高性价比）

对 W2 结论用**与原作者不同的算法**复算。**报告里必须写明你的方法与原方法差异**，仅"结果一致"不算通过。

| 项 | 复验内容 | 期望 |
|---|---|---|
| **AG-1** | 独立复跑 `tools/verify_anchors.py`、`tools/verify_hooks.py`，并对 `static_prep/{particle,crt,audio}/CLAIMS.txt` 跑 `tools/audit_bytes.py` | 323/323 PASS；三包 claims 27/15/22 全 OK（W2 自述值） |
| **AG-2** | 用**第二种算法**复算 QC6 的 **977 / 988 / 964** 与"931 对同名类 vtable RVA 相同 **0 对**" | W2 主代理只做了名字集合粗验，**未经第三方算法确认**；请用与 `ra2re/rtti.py` 不同的解析路径（例如自写 PE 解析或直接扫 `.data` 的 RTTI CompleteObjectLocator 链）复算 |
| **AG-3** | 复现 LZO >49152 缺陷最小例：输入 `bytes(70000)+b"Q"+bytes(70000)` | 期望 `comp=638`、首错偏移 `102769`（W2 自述） |
| **AG-4** | 复核 `ECHGAP` 8 节差异表与「三要素齐备」（双 `GAGAP@(41,47)/(49,43)` + `TA17` + `CellTags` 航点）+ `6c5e2f2d…` 金样身份 | W2 判"应使用 `zcode_live` 版 `6c5e2f2d…`"；请独立复核 |
| **AG-5**（新增） | 复核 W2 §3 的**7 项新问题**中最承重的两条：①本镜像虚表头 **4 字节**（`vftable[-4]`=RTTI 链）②`GREATEST_THREAT` 实为 **v[241]** | 正控 7 枚现网钩（5×v[69] + 2×v[265]）须全命中 |

**写域**：`out/re_work/agy/W3_20261001/verify/**`。**不得**改 `tools/**`（发现工具缺陷写进 [3] 勘误）。
**未闭环判定**：W2 的 `verify_evidence` 实跑 EXIT=1（原因"无 PNG"，与静态 VA 正交）——**保持 N/A 判定**，不得为凑 PASS 改判据。

## 包 4 · W3-A4 原版件 `.detour` 注入不改代码的**独立复核**

W2 QC6 结论：`game.exe` 与 `gamemd.exe` **均为 StreamHook 注入版**（多 `.detour` 节、Import 目录改指入该节、表头 dword[4] = 原导入目录 RVA），并已实证「注入不改代码」：`.detour` 无 EXECUTE 位、`.text` 内 rel32 改道 0 条、绝对引用 0 处、入口点是完整 CRT 序言；并用未注入的 MO `gamemd` 交叉验证（`.rdata/.data/.rsrc` 逐字节同、`.text` 仅差 39 B / 7 段）。
**你的任务**：用**不同方法**独立复核该结论（例如：逐段熵/指令直方图对比、`.text` 与 `D:\Red2` 侧/第三条血缘逐字节比对、导入表 thunk 全量重建对照、`.detour` 节表与 PE 节权限位重解析）。
**写域**：`out/re_work/agy/W3_20261001/origverify/**`。**只读** `ra2youli/**`、`ra2bench/**`、`D:\Red2/**`。
**必答**：Q1 结论成立否（逐条）？Q2 若发现 `.text` 存在改道，给出 VA + 原字节 + 现字节（P0）。Q3 MO 对照件的交叉验证是否可重复？

---

## 子代理并行建议（本卡明确允许）

- 子代理 A：W3-A1（勘误落地，逐块）
- 子代理 B：W3-A2（atlas 本体，**必须独占该文件**）
- 子代理 C/D：W3-A3（AG-1/AG-3 一组；AG-2/AG-5 一组）
- 子代理 E：W3-A4
- 主代理：统筹 + 对 A/B 的落盘做 `git diff` 级越界扫描 + 抽验 ≥5 条断言 + 写 §7 复核表

**写域冲突警告**：子代理 B 是 `docs/re/ARCHITECTURE_ATLAS.md` 的**唯一写者**；A 写其他 `docs/re/*.md`。若同一文件被 A、B 同时需要，**由主代理仲裁串行**，禁止并发写同一文件。

## 包 5 · W3-A5 静态预检包 P-3/P-4/P-5 的**独立字节级复算**（追加派发，2026-10-01 22:0x）

**动机**：ZCode 将按 `static_prep/**` 三包实际打补丁；W2 QC3 自检 407 条 PASS，但其周边规格含 5 条「落地即错」缺陷（B-1…B-5）。本包从 `ra2youli\gamemd.exe` **独立重算**每个字节，使实际打补丁步骤不可能静默写错。

重算项（不得采信 W2 自述，必须自跑）：`0x007EFA68`/`0x007EFCB0` 槽值；`0x007C8E17`/`0x007C8B3D` 原字节与 `call` rel32 落点 `0x7C93E8`；`0x00750920`/`0x007509E0` 与「P-5 窗必须 5B」；`0x004F9AAE`/`0x004F9AB0` 指令边界与真入口 `0x004F9A50`；36 条 cave 区间零重叠；SBH 闭区间 `size ≤ 1016`（`ja`）与 setter 上限 `0x3F8`；7 个 BSS 全局的无文件 raw 判定；三包 claims 27/15/22 + 407 条自检复跑；自建合并 claims 跑 `audit_bytes`。

额外必交：**可直接使用的修正字节表**（地址/原字节/新字节/窗长/守卫条件）+ 「B-1…B-5 逐条能否复现」及原始证据。
写域：`out/re_work/agy/W3_20261001/static_prep_verify/**`。

## 包 6 · W3-A6 「文档 vs 实况」全量再审计（追加派发，2026-10-01 22:0x）

**只读审计 + 只出订正清单**（`docs/**` 写入权当前归 W3-A1，本包不得写）。
范围：`docs/re/*.md` 235 份 + 顶层台账 + `REWRITE_ROADMAP`/`NEXT_RE_AND_MODERNIZATION`。逐项核：VA 断言可解码率（给分母）、分母/百分比自洽、键名与节名默认值（对照 `blitter_hooks.cpp` + 三份 ini：源 23 键 `FD9EBB32…`，两游戏目录 20 键 `B8BB8238…` 缺三键）、状态新鲜度（「已落地/已验收/待同步」与当前哈希矛盾者）、`RE_PROGRESS_SURVEY.md` 的 D1–D6 与 U 项逐条重判、跨文档互相矛盾。

交付：`out/re_work/agy/W3_20261001/doc_consistency/{AUDIT_W3_A6.md, corrections.json, appendix_*.md}`；`corrections.json` 字段固定 `{file,line,before_excerpt,after_text,reason,severity,evidence_ref,contradicts[]}`。

## 首轮最小可交付

W3-A3（独立复验，全只读、最快）+ W3-A1 的落盘状态表。W3-A2 可随后。
追加包 A5/A6 与 A1–A4 **同批并行**（写域互斥，均为 `out/re_work/agy/W3_20261001/<subdir>/**` 的不相交子目录）。
