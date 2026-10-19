# LESSONS_ROUND3_APPENDIX · 2026-10-04 第三批经验沉淀一页式索引

> **性质**：索引页。本页只指向各归属文档的条目与出处，**不承载正文、不产生新实证、不重开任何结论、不升格证据等级**。
> **生成**：任务卡 `LESSONS-ROUND3-01`（2026-10-04）；来源 = 本轮复核卡 / 继承面审计卡 / 传播卡 / Lead 验收台账逐份实读（简写 H2R/H2F/LEG/B2R/GUARD/IMPL/P0/ACC，定义见 `LESSONS_20261003_RE_INSTRUMENTS.md` §7.0）。
> **写域**：本页为新建文件；本轮另只追加（append-only）三份既有文档，**未改任何 `lead/**`、`ra2forge/**`、`tools/**`**。
> **Lead 根**（下表出处路径的前缀）：`out/re_work/work_chain/CONTINUE_20261003/lead/`。

## 归属文档与新增条目一览

| 归属文档 | 追加位置 | 新增内容 | 条数 |
|---|---|---|---|
| `docs/re/LESSONS_20261003_RE_INSTRUMENTS.md` | §七（文档末尾追加，T1–T36/§四清单原文零改动） | T37–T43 大条目 + §7.0 简写表 + §7.1 关系表 + §7.2 本卡实跑台账 | **7** |
| `docs/re/LESSONS_20261003_AGENTS_AND_HARNESS.md` | §7（文档末尾追加，§1–§6 原文零改动） | 7.1 审计战果 6 次+两连击 / 7.2 同通道申报纪律 / 7.3 双方绕开再添实证 / 7.4 未闭合项可不全 / 7.5 卡面前提抽验 | **5** |
| `docs/WORK_CHAIN.md` | §5.7（文档末尾追加） | 「修复范围枚举」四项强制前置 + 配套三条 + 验收口径 | **1 项（含 4+3 子条）** |
| `docs/re/LESSONS_ROUND2_APPENDIX.md` | **不改** | ROUND2 索引页归 ROUND2 卡；本轮索引另立本页 | 0 |
| `docs/re/HARNESS_PLUGIN_IMPROVEMENTS.md` | **无需追加** | 本轮无插件类新实测（H2F 卡面"脚本无扩展名是刻意的——钩子纪律"属既有 P1 已登记形态，`DLC_HIGH2_FIX_REPORT.md:7`） | 0 |
| `docs/re/LESSONS_ROUND3_APPENDIX.md` | 本页（新建） | 一页式索引 | — |

## A 项 · 仪器/验证陷阱索引（RE_INSTRUMENTS §七）

| 条目 | 一句话 | 出处（文件:行） |
|---|---|---|
| **T37** | ★ **`O_CREAT\|O_EXCL` 在 Windows 上不兜悬空 reparse point**：悬空 ⇒ `open` **成功并在目录外创建目标**，**只有活链接才 `FileExistsError`**；⇒ 必须在 `open` **之前**用 `lexists`/`islink` 拒绝（附：漏 `O_BINARY` 会做 CRLF 翻译） | `dlc_high2_audit/DLC_HIGH2_REAUDIT.md:15,103,117,126,98–104,244–248`、`dlc_high2/DLC_HIGH2_FIX_REPORT.md:12,29,127`、`ACCEPTANCE.md:1108`；**本卡实跑 §7.2 E1/E1-对照/E1-替换/E2/E4** |
| **T38** | **派生路径枚举**：修复自身引入的 `<slot>.ra2forge-stage` 不在任何判据内；四条派生名（`.bak`/`.bak.<stage>`/`<name>.<stage>`/`.removed.bak`）逐项施加同等判据 | `DLC_HIGH2_REAUDIT.md:132,244,248,312`、`dlc_legacy/DLC_LEGACY_AUDIT.md:55–59`、`ACCEPTANCE.md:1116` |
| **T39** | **"绝对句"审计法**：`never`/`不可能`/`一定`/`唯一` 每句=可证伪断言，逐句逐形态实测；本轮 3 处被推翻 + 2 处全称式不实 | `DLC_HIGH2_REAUDIT.md:14,16,21,138,185–188,262–266,286,287,290`、`DLC_HIGH2_FIX_REPORT.md:12,21,101`、`DLC_LEGACY_AUDIT.md:55–59`、`rc4_batch2_audit/RC4_BATCH2_REAUDIT.md:272,309`、`ACCEPTANCE.md:1107,1109,1114` |
| **T40** | **同名多写点检查**：安全原语用在备份写/恢复写，却没用在最大那次写（主拷贝 `copy2` L477）与记录写（`write_text` L699）；写点全表按符号取 | `DLC_HIGH2_REAUDIT.md:17,118,135,250–260,309`、`DLC_LEGACY_AUDIT.md:12,27–33,83`、`ACCEPTANCE.md:1105,1110,1111,1116` |
| **T41** | **口径陈旧自述**：报告头部"共 N 条断言"可能过期（自述 54、实跑 70、加严后 74）⇒ 数字以现跑为准，来源写"实跑件第 y 行" | `rc4_harden/GUARD_UPGRADE_51.md:64,136,198,239`、`DLC_HIGH2_FIX_REPORT.md:167`、`DLC_HIGH2_REAUDIT.md:276,290,297–313`、`RC4_BATCH2_REAUDIT.md:318`、`ACCEPTANCE.md:1173` |
| **T42** | **CRLF/LF 锚点失配**：同目录 11 件 JSON = 5 件全 CRLF + 6 件全 LF ⇒ 锚点恒 0 命中；`count==1` 断言失败须**写盘前 ABORT** | **本卡测量 §7.2 E3** + `RC4_BATCH2_REAUDIT.md:212,390`、`GUARD_UPGRADE_51.md:268`、`DLC_HIGH2_REAUDIT.md:146` |
| **T43** | **改前未快照 ⇒ 只能出"反推件"**：3 件逆还原（锚点唯一性 + `py_compile` + 行号逐位一致）必须逐件显式标注，不得当原件用 | `GUARD_UPGRADE_51.md:243,254,268`、`RC4_BATCH2_REAUDIT.md:335`、`DLC_HIGH2_REAUDIT.md:48–51` |

**明确不重复立条**：`RC4_P0_DANGLING_REPORT.md:173–177` 的 §10 五类自纠（heredoc ×2、VA 掉位、首个 `ret` 截断、退出码记账）已由 **ROUND2** 的 T18/T16/T24 收录 ⇒ 本轮只在 §7.0 登记读取（见 RE_INSTRUMENTS §7.1 表第 7 行）。

## B 项 · 协作纪律索引（AGENTS_AND_HARNESS §7）

| 条目 | 一句话 | 出处 |
|---|---|---|
| 7.1 | 跨通道审计战果累计 **6 次**（+⑤ HIGH-3/HIGH-4/MEDIUM-8、+⑥ 限度申报不实/拒绝层零实现）；**★ 同一不实措辞被两连击**（"W-B 不在现盘"推翻后在下一张卡复活）；计数口径按 Lead 已验收复核战果计，legacy 与 A-65 单列 | `DLC_HIGH2_REAUDIT.md:15–17,21,290`、`RC4_BATCH2_REAUDIT.md:20,225–239,302–303`、`rc4_impl_audit/RC4_IMPL_REAUDIT.md:14,81–86,152`、`ACCEPTANCE.md:1102–1116,1121–1131,1200` |
| 7.2 | 同一通道"执行者+审计者"⇒ 报告结论章必须内嵌「本轮结论需另一通道复核」；复核者=原发现者时夹具须本卡重自建 + 公开接受对自己的更正。**⚠ 卡面称 `DLC-HIGH3-FIX01` 已照此执行：本卡实读时点 `dlc_high3/` 无报告正文件 ⇒ 登记为未证实，不据此立论** | `DLC_LEGACY_AUDIT.md:4`、`ACCEPTANCE.md:1164`、`DLC_HIGH2_REAUDIT.md:4,61,293` |
| 7.3 | 「双方都绕开的缺口」再添实证：`_uninstall_legacy` **三代快照逐字节相同**（= 继承缺陷族）+ **同族判据已全部存在而 legacy 面零复用** ⇒ 代价可量化为 HIGH 4 + MEDIUM 2 + LOW 1 + INFO 2；交集法加一问"与前代是否逐字节相同" | `DLC_LEGACY_AUDIT.md:6,12,27–33,83`、`DLC_HIGH2_REAUDIT.md:35`、`ACCEPTANCE.md:1143` |
| 7.4 | **未闭合项清单 ≠ 闭合面全集**：MEDIUM-8 是继承面且未列进上一轮 §9 的 5 条未闭合项；清单外的面要靠写点闭包/路径闭包/绝对句射程三问自取 | `DLC_HIGH2_FIX_REPORT.md:176–182`、`DLC_HIGH2_REAUDIT.md:17,188,312–313`、`ACCEPTANCE.md:1110` |
| 7.5 | **卡面事实前提也要抽验**：①"某卡已照此执行"须核到文件；②"某件不在现盘"是事实主张 ⇒ 自己跑哈希普查；被推翻过的措辞要挂"已于 `<文件:行>` 被推翻"到续任卡必读项 | `RC4_BATCH2_REAUDIT.md:225–239`、`RC4_IMPL_REAUDIT.md:81–86`、`ACCEPTANCE.md:1131,1200` |

## C 项 · 工作链纪律索引（WORK_CHAIN §5.7）

| 条目 | 一句话 | 出处 |
|---|---|---|
| 5.7 强制前置 | **修一族缺陷开工第一步先交范围清单，未交不得动代码**（同族第 3 次复发的直接后果） | `DLC_HIGH2_REAUDIT.md:132,244–248,250–260`、`ACCEPTANCE.md:1102–1116` |
| 5.7-1/2/3/4 | 四项清单：**点名形态 + 派生路径 + 同语义写点 + 记录侧/读侧对称**，缺一即判"族未做完"、不得写"已修" | `DLC_HIGH2_REAUDIT.md:16,132,135,256–266,244–248` |
| 5.7 配套 | 绝对句反查 / 形态矩阵（含正向对照）/ 限度申报复算 | `DLC_HIGH2_REAUDIT.md:21,94–104,286–290`、`RC4_BATCH2_REAUDIT.md:225–239`、`ACCEPTANCE.md:1131,1200` |
| 5.7 验收口径 | 修复卡的"未闭合项"不视为闭合面全集；继承面一问 = "与前代快照是否逐字节相同" | `DLC_HIGH2_FIX_REPORT.md:176–182`、`DLC_LEGACY_AUDIT.md:6,12,83`、`ACCEPTANCE.md:1143` |

## 重复核对声明（与 ROUND2 及本文档既有条目）

1. **与 ROUND2 新增条目（T9–T36 / AGENTS §6.1–6.5 / WORK_CHAIN §5.6）无重复立条。** 本轮 7 条仪器类（T37–T43）与协作类 5 条均为 ROUND2 未覆盖的新族（平台语义 / 范围闭包 / 绝对句 / 限度申报复核 / 未闭合项可不全）。
2. **四处同族，已按纪律改为"补充出处与实例"而非另立**（逐条在正文标注）：
   - `T40` 的定位手法沿用 **T36**（按符号定位、勿引行号钉死）—— 已注明"同 T36"；
   - `T41` 与 **§四清单 32**（计数自洽）/ **T16**（期望值来源分诊）同纪律 —— 已注明为其**时间维度**补充；
   - `T42` 与 **T18**（heredoc/字段错位类仪器缺陷）同族 —— 已注明；
   - `T43` 与 **D8**（版本/指纹钉定）同族 —— 已注明为"钉晚了就钉不住"的补充实例。
3. **AGENTS §7.1 是 §6.1"跨通道审计战果计数"的续计**：①②在 §3.2、③④在 §6.1，本轮只补 ⑤⑥ 与"两连击"新形态，未重述前四次。
4. **AGENTS §7.3 是 §6.2"双方都绕开的缺口"的补充实例**：`_uninstall_legacy` 这个函数名 §6.2 已出现（当时只有"未动 × 未审"两条），本轮**只补最硬的证据**（三代逐字节相同 + 零复用 + 可量化代价），并明确"不重复立条"。
5. **AGENTS §7.5 是 §6.5"派工单自身要被核对"的续计**：由"引用号/前提偏差"扩到"落地与否"与"限度真伪"两类。
6. **P0 卡 §10 五类自纠已被 ROUND2 收录** → 本轮不重复（RE_INSTRUMENTS §7.1 表第 7 行显式登记）。
7. **`HARNESS_PLUGIN_IMPROVEMENTS.md` 本轮零改动**（无插件类新实测）。
8. **时效与修订锚**：所有 `lead/**` 出处行号以**本卡 2026-10-04 实读时点**为准。本卡收尾扫描另见 `ra2forge/install.py` 于 **17:08 被另一会话改写**（HIGH-3/4/MEDIUM-8 回派修复在飞；`lead/dlc_high3/` mtime 17:41、**报告正文件尚未出现**）⇒ 本文转引的 `install.py` 行号属复核卡被测修订（`e1eb9dc6…` / 45,868 B / 920 行），**复用前须按新指纹重钉**（详见 RE_INSTRUMENTS §7.0「★ 修订锚」）。该并发写入**非本卡所为**，本卡未删未盖。

## 本轮运行命令申报

**是，运行了命令**，但**全部为只读或仓库外沙箱**，且**未在仓库任何路径落件**：

| 类 | 命令 | 用途 | 落件 |
|---|---|---|---|
| 只读定位 | `ls`、`find`、`grep -n`、`sed -n`、`Read` | 定位来源件与台账行号（`lead/**` 全程只读） | 无 |
| 最小实验 | `python -X utf8 -B probe.py`（`%TEMP%` 内 `tempfile.mkdtemp` + `os.symlink` + `os.open(O_CREAT\|O_EXCL)` / `os.replace` / 前置判据） | T37 与"防呆做法可行性"独立复现（E1/E1-对照/E1-替换/E4） | 临时目录，脚本末 `shutil.rmtree`，收尾 `exists_now=False` |
| 最小实验 | `python -X utf8 -B probe2.py` | E2：`os.open` 不给 `O_BINARY` 的 CRLF 翻译（9 B→12 B） | 同上，用后即删 |
| 只读测量 | `python -X utf8 -B` 读字节计数 `\r\n`/`\n` | E3：同目录 11 件 JSON 换行构成 + 两份 md/claims 件换行计数（T42 实测基线） | 无（仅 stdout） |

**未做**：未运行游戏、未附加进程、未读/写内存；未运行门禁/补丁/`--install`；未改任何 `lead/**`、`ra2forge/**`、`tools/**`、`out/**`、二进制或游戏目录；未运行 `git`；全程 `python -B` + `PYTHONDONTWRITEBYTECODE=1`（探针内 `-B`，仓库未被 import）。

## 交付

- 新建：`docs/re/LESSONS_ROUND3_APPENDIX.md`（本页）
- 追加：`docs/re/LESSONS_20261003_RE_INSTRUMENTS.md` §七（T37–T43 + §7.0/7.1/7.2）、`docs/re/LESSONS_20261003_AGENTS_AND_HARNESS.md` §7（7.1–7.5）、`docs/WORK_CHAIN.md` §5.7
- 未动：`docs/re/LESSONS_ROUND2_APPENDIX.md`、`docs/re/HARNESS_PLUGIN_IMPROVEMENTS.md`、`lead/**`、`ra2forge/**`、`tools/**`
