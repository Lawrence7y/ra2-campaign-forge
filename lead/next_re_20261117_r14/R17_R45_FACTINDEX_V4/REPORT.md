# REPORT — R17_R45_FACTINDEX_V4（FACT_INDEX v4.0）

## 1. 基底与改动范围
- 基底：R17_R44_FACTINDEX_V32\FACT_INDEX.tsv（v3.2，F01–F26，26 条）。
- F01–F26 的 26 行 TSV 逐字节未改：v4.0 文件前缀 26 行与基底逐字节一致（sha256 校验见 §5）。
- 新增 12 条：F27–F38（上限 12，未超）；未触及 R17_R44_FACTINDEX_V32 / R17_R42_F23_FIX / R17_R40_FACTINDEX_V3 / R17_R38_FACTINDEX_FIX / R17_R34_FACT_INDEX 任何文件。

## 2. 缺口分析（GAP.tsv）
- 来源三路：R14_COMMON.md 全节、COVERAGE\PANEL.md M69–M102、LEAD_LOCK 技术条（含追加段）。
- 枚举可复用规则 40 条：已覆盖 17 条、未覆盖 23 条。
- 覆盖判断全部给依据：已覆盖引索引 statement/limitations 原句；未覆盖给「全表检索命中 0 / 只触到相邻口径」的核对结果。
- 11 项必判候选逐项结论：
  - atexit 严格 68 + 字节误命中 → 未覆盖 → F27
  - ㉓ 析构重装陷阱（含 test al,1 签名）→ 未覆盖 → F28
  - AddRef/Release 桩 + vt+0x20 → 未覆盖 → F29
  - pTD/pCHD 绝对 VA → 未覆盖 → F30
  - 装饰名 TD+8 内联串 → 已覆盖 F01（F01 statement 含「TD+8 内联名串」）→ 不新增
  - COL.pSelf 恒 0 → 未覆盖 → F31（F01 只记 pSelf 的一处数值口径、无「不可判起点」禁例）
  - lea 中介 0 处 → 未覆盖 → F32（F01–F26 的「lea」全是路径串 lead 的子串）
  - 导出表 RVA=0 → 未覆盖 → F33
  - G1–G5 + host <= site < fn_end → 未覆盖 → F34（F13 只覆盖入口禁扫 C3/C2）
  - DoD 判据 ceil → 未覆盖 → F35（F25/F26 只记结果与裁定）
  - GATE_MAP → 未覆盖 → F36（F17 是 §2.10 (a′) 的另一处更正）

## 3. 新增条目逐条依据
| 新 id | 规则一句话 | 依据（节/段） |
|---|---|---|
| F27 | atexit 严格形态仅 68、其余 call 0x7C978A 为字节误命中 | LEAD_LOCK 追加 20:5x 段；HANDOFF_R16 R15 技术条；BOARD_ARCHIVE 第 99–104 轮段；台账 N9 |
| F28 | ㉓ 析构重装；删除析构签名可为 test al,1 不止 [esp+X],1 | R14_COMMON §8.1 错源㉓ / §13.5；NAMED_PUSH_AUDIT10 \VERDICT.md §2；PANEL M72 |
| F29 | AddRef/Release 为 mov eax,1; ret 4 桩，清理走 vt+0x20，逐表不逐族 | R14_COMMON §13.3；LEAD_LOCK 追加 14:1x 段；PANEL M71 |
| F30 | pTD/pCHD 为绝对 VA、按 RVA 解会 fail-closed 误判 | R14_COMMON §13.1；LEAD_LOCK 追加 19:0x 段 |
| F31 | COL.pSelf 恒 0、不能判表起点 | LEAD_LOCK 追加 20:5x 段；台账 N9；BOARD_ARCHIVE 第 99–104 轮段 |
| F32 | lea 中介虚表写入 0 处 | LEAD_LOCK 追加 20:5x 段；台账 N9；R14_COMMON §8.1 错源19 |
| F33 | 导出表 RVA=0/Size=0、V4 恒不可能 | LEAD_LOCK 追加 21:1x 段 / 22:1x 段 |
| F34 | G1–G5 装表纪律 + host <= site < fn_end(host) 位置断言 | LEAD_LOCK 方法论硬约束段 / R16 遗留段；PANEL M98–M102 |
| F35 | DoD 判据 named_S(R14)>=ceil(0.9n) 且 proved>=ceil(0.5n)，严格列 proved_strict | PANEL M47 / M52 / M44 |
| F36 | GATE_MAP 用途与其既有误记（§2.7 更正） | R14_COMMON §2.6 来源段 / §2.7；PANEL M103 |
| F37 | 矛盾分析用单问题裁决卡、第三方自算、禁复用脚本 | R14_COMMON §2.8 规则C |
| F38 | 先测基线、对照必须同质 | R14_COMMON §8.2 技术④ |

## 4. 已知未补（11 条，超出 12 上限、按「下游最容易踩坑」排序后置）
1. U13 证据同源不得双计（§8.3 R14-R17）
2. U14 单源结论一律降级为推断并标强度与依赖产物（§2.8 规则B）
3. U15 同族错误须先判口径差与真错再分别处置（§2.8 实例D）
4. U16 频率/富集判据分母必须是指令边界上的真 call（§8.2.2 技术⑩）
5. U17 族级判据判别力须按族内随机算（§8.1 错源⑳）
6. U18 合取判据自洽可能是循环论证（§8.1 错源㉑）
7. U19 RTTI 模板前缀 PAU/PAV 不是类名一部分（§8.1 错源㉒）
8. U20 同源系统性错误随机基线恒 0、必须差分检验（§8.1 错源㉔）
9. U21 P=R=100%/恰命中 N 可能是判据自证（§8.1 错源㉕）
10. U22 自报扫描规模必须给 .text 覆盖百分比且站点落在范围内（§8.1 错源㉖）
11. U23 B8 imm32 C2 04 00(ret 4) 不是 B8 imm32 C3（§8.3 新增坑）
上述规则来源均在 GAP.tsv 对应行给出，本次因 12 条上限未纳入 FACT_INDEX，留待下一轮。

## 5. 校验
- 路径解析：FACT_INDEX.tsv 全部 38 行 × evidence_paths 逐条解析 → RESOLVED 99，BROKEN 0。解析器按括号深度切分分号（避免 F17 括号内分号误切），剥离括号内段标识后按仓库根相对路径查存在性。
  - BROKEN 0，无明细。
- CR 校验：目录内 FACT_INDEX.tsv / GAP.tsv / README.md / REPORT.md 四文件 CR 计数 0（0 为合格）。
- F01–F26 前缀逐字节校验：基底 26 行 sha256 31e981b93cf9139b38ed9e481b3974b1eaf00403f353345f1dc1b4a3961d4268，v4.0 同名前缀 sha256 31e981b93cf9139b38ed9e481b3974b1eaf00403f353345f1dc1b4a3961d4268 → EQUAL（合格）。

