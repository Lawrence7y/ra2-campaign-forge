# RECONSTRUCT.md · 哪些输入没有保留字节副本、只能靠路径 + 哈希引用

- run_id：`NEXT_RE_20261112_R01`；生成：UTC `2026-11-12T07:33:07.582983+00:00` / Asia/Shanghai `2026-11-12T15:33:07.582983+08:00`
- 唯一写域：`lead\next_re_20261112\RE-N00\`；本包**没有**复制任何输入字节，只登记绝对路径、字节数、SHA-256、mtime_utc 与 `git ls-files --error-unmatch` 结果。
- 生成器：`_baseline.py`（一条命令重建 `BASELINE.json` / `INPUTS.tsv` / `CURRENT_FACTS.md` / `RECONSTRUCT.md`）。它重建的是**指纹与事实底账**，不是输入字节。

## 结论（先说清楚）

1. `RE-N00\` 内**只有**本包 5 个文件（`_baseline.py`、`BASELINE.json`、`INPUTS.tsv`、`CURRENT_FACTS.md`、`RECONSTRUCT.md`）是自包含的；它们可以由 `_baseline.py` 离线重建。
2. 下表的 **40 项输入全部没有字节副本**：只能靠「绝对路径 + sha256 + bytes + mtime」引用。若源文件被修改、删除、被游戏回写或换机，**无法从本目录离线重建这些字节**；只能回到原路径取回文件并比对 sha，不一致即须按任务书 §4.3 停批并重新定级。
3. 同理，`BASELINE.json → map_search.mix_inventory` 只记 17 个 `.mix` 容器的路径/大小/sha/头部 16 字节，**没有**容器内文件清单，更没有字节副本；MIX 索引未解析（加密头需 Blowfish 密钥与格式确认）。
4. 历史「真机运行结果」类输入（事件 JSON、抓栈样例、报告、截图）本轮无授权重放；即使有副本也不能重放为「本轮实测」，其证据等级恒为 `[转引]`。
5. §2.2 五条声称哈希本轮全部 match（5/5），两份冻结母本全部 match（2/2）；但这些是**本时点**事实，不是永久保证。

## 逐条清单（无字节副本 ⇒ 不可离线重建）

| role | 路径（相对仓库根） | bytes | sha256（完整） | 字节副本 | 离线重建 |
|---|---|---|---|---|---|
| analysis_gamemd_exe | `ra2bench/gamemd.exe` | 4825360 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 无 | 不可离线重建 |
| game_gamemd_exe | `ra2youli/gamemd.exe` | 4825360 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 无 | 不可离线重建 |
| game_ddraw_dll | `ra2youli/ddraw.dll` | 411648 | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | 无 | 不可离线重建 |
| game_ini_ddraw | `ra2youli/ddraw.ini` | 14782 | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | 无 | 不可离线重建 |
| game_ini_ra2md | `ra2youli/RA2MD.INI` | 1754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | 无 | 不可离线重建 |
| game_ini_ra2md_alias | `ra2youli/ra2md.ini` | 1754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | 无 | 不可离线重建 |
| game_ini_ra2md_benchbak | `ra2youli/RA2MD.INI.benchbak` | 1754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | 无 | 不可离线重建 |
| game_ini_ddraw_benchbak | `ra2youli/ddraw.ini.benchbak` | 14352 | `2f666b4dc048098e914137b7b7dddb8cacff2332343d7209b8c80896365e3dfb` | 无 | 不可离线重建 |
| game_ini_battlemd | `ra2youli/BATTLEMD.INI` | 2733 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` | 无 | 不可离线重建 |
| game_ini_battlemd_bak | `ra2youli/BATTLEMD.INI.ra2forge.bak` | 241 | `9f804531c1955a785159306e045ac3b60dda0092f9639103fbc68dd19e15b412` | 无 | 不可离线重建 |
| game_ini_battlemd98 | `ra2youli/BATTLEMD98.INI` | 453 | `4e3417568924891792520ad8c3ab44f42e11fdc9934fb453d4db7210bf3d2c74` | 无 | 不可离线重建 |
| game_ini_ra2 | `ra2youli/ra2.ini` | 1769 | `867f85979dc62f3d5ed9663d4ffb6aebd066760b451c072e50251812080abb3b` | 无 | 不可离线重建 |
| game_ini_ra2render | `ra2youli/ra2render.ini` | 16496 | `27c9a60c55a8a1b422d3ef06b90e3d343a93eb523a600286c937198b363ecee4` | 无 | 不可离线重建 |
| game_ini_register | `ra2youli/Register.ini` | 211 | `2ccdcb71b9f6b649ad6f8ca1b97e0cd42ee98a8000a7bafe1380c6d93aea9052` | 无 | 不可离线重建 |
| d13_driver | `lead/re_d13_ruling_20261112/_run_hl_match.py` | 15949 | `33bb2f61a7696e51eed979452f3d6d86859ebcb1d8322f348ff04bdb0ffa9426` | 无 | 不可离线重建 |
| d13_sampler_candidate | `lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py` | 55720 | `98210b4af460a75746913e35c791147982ec9d492349c9ace275ec817d51840a` | 无 | 不可离线重建 |
| d13_stackwalker | `lead/re_d13_ruling_20261112/e3_stackwalker.py` | 11180 | `261b6cd6afe87728af2da338c451946c3c3e763053b1b89419cad43ae8e6f8db` | 无 | 不可离线重建 |
| d13_static_frame_semantics | `lead/re_d13_ruling_20261112/_static_frame_semantics.py` | 7262 | `04d94cda140eab864023d31756b1f11fd9d5e0942d3318cf99ffa78dad95f4c0` | 无 | 不可离线重建 |
| d13_framesource | `lead/re_d13_ruling_20261112/e3_framesource.py` | 6195 | `86a4520cfb9a5bb6c6b2e518fc371bfe05cf9016a15b843175adf46405237159` | 无 | 不可离线重建 |
| d13_event_14412 | `lead/re_d13_ruling_20261112/_hl_match_14412.json` | 987 | `6a44085e5c4f1556aeebb844971ea9ec2a8a0868911cd8c0d3ffceb7c10793d4` | 无 | 不可离线重建 |
| d13_event_40500 | `lead/re_d13_ruling_20261112/_hl_match_40500.json` | 7139 | `353e5537aa55f60ab5af854b5e60798896493c5cb65c7c70781beadebc3538b8` | 无 | 不可离线重建 |
| d13_event_37392 | `lead/re_d13_ruling_20261112/_hl_match_37392.json` | 2432 | `f37c594e5a3a9d9cd1e0310150dc6f06a9630f16c7ba52e6268530c10ada454b` | 无 | 不可离线重建 |
| d13_event_34500 | `lead/re_d13_ruling_20261112/_hl_match_34500.json` | 176 | `37b2a2973d5b4e847acc290333055976d837ab0676c3e49bbb6475cda9bb1bdd` | 无 | 不可离线重建 |
| d13_battle_stack_sample | `lead/re_d13_ruling_20261112/_battle_stack_sample.json` | 3178 | `526dcc37338c1cbdfda1cc17c408d626b4d7d81027fd352715718b7d8c7db01e` | 无 | 不可离线重建 |
| d13_report_stall_final | `lead/re_d13_ruling_20261112/STALL_CAPTURE_FINAL.md` | 7445 | `ecb56843e9bd722b16e7ad7af23b7588e5f5ad6fb1e9e676c83780beb9659a13` | 无 | 不可离线重建 |
| d13_report_stall_success | `lead/re_d13_ruling_20261112/STALL_CAPTURE_SUCCESS.md` | 8958 | `08e001eea6c14d8641ac8fc508fb3b4da8298493b0a0c2c5efdd537a03f6030f` | 无 | 不可离线重建 |
| d13_report_static_semantics | `lead/re_d13_ruling_20261112/STATIC_FRAME_SEMANTICS.md` | 11333 | `90a692197e8cf7eed6082b65bfe6a52cdd27a3238cb0d33a15464f2ac0230892` | 无 | 不可离线重建 |
| d13_report_ruling_611 | `lead/re_d13_ruling_20261112/RULING_RECEIPT_611.md` | 14679 | `53ab925ae5e2d8f00f3a3a11f2da4267efbf5b4420b2e995f98b977206bcd650` | 无 | 不可离线重建 |
| d13_report_wow64 | `lead/re_d13_ruling_20261112/WOW64_RECEIPT.md` | 7294 | `23130c47ead63a95fb59c9d77a978ce7b02d7f65eeaec65e0ae9c019e194b887` | 无 | 不可离线重建 |
| d13_report_framesource | `lead/re_d13_ruling_20261112/FRAMESOURCE_RECEIPT.md` | 5827 | `ce2b4a84b3ad382806f2332fee801824fbb70f513be67dce8e9c5d852fb4a566` | 无 | 不可离线重建 |
| d13_report_stackwalk | `lead/re_d13_ruling_20261112/STACKWALK_RECEIPT.md` | 5266 | `4146029045975d83e4765b0b936814cfb6c8f672314ce0cc8db16dd59573fa34` | 无 | 不可离线重建 |
| d13_selftest_output | `lead/re_d13_ruling_20261112/_selftest_out.txt` | 2953 | `6c1e20b65d0ad14502a92c8756a1fc11f9369895b97130de922fdb6dcdd3b1a4` | 无 | 不可离线重建 |
| frozen_master_probe_v2 | `lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py` | 48630 | `6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9` | 无 | 不可离线重建 |
| frozen_master_earlyclose | `lead/qc161_u0400_trip/_drive_c2_x_earlyclose.py` | 9061 | `2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1` | 无 | 不可离线重建 |
| task_book | `docs/re/NEXT_RE_TASKS_20261112.md` | 34902 | `8dfa0109cc882f1503f8b5e27db2d087774e3f0ae6566725588448e253768f4f` | 无 | 不可离线重建 |
| project_direction | `docs/PROJECT_DIRECTION.md` | 10194 | `1b1f56ce022694c9aabb2f58e3d3809b689e977720e3176424d82b251763949b` | 无 | 不可离线重建 |
| pending_decisions | `lead/PENDING_DECISIONS.md` | 55191 | `f2cf2a1766e1442b0c4e41f6ce1b06a53e4df5ffcfd51bd01cb67c23837d9a7e` | 无 | 不可离线重建 |
| goal_ledger | `lead/GOAL_THREE_TARGETS_20261018.md` | 806800 | `0e3aa8d57697c1d63d6951e276f564bf17e5ddf7dc7bf474308dbdb9a845d850` | 无 | 不可离线重建 |
| map_loose_yrm_candidate | `ra2youli/[8]试验地_Pro_ProvingGrounds.yrm` | 175361 | `3e3c874572bc02199cddce05b3633888caf968e6fbb457e763fb70b9fbfd5b19` | 无 | 不可离线重建 |
| map_list_text | `lead/re_d13_ruling_20261112/_maplist_full.txt` | 7716 | `02a7d91e9e4adf3782876baf75a88e1e9b3cd793d681d79cb757e0c9632a32df` | 无 | 不可离线重建 |

## 高风险子类

### A. 游戏可写 ini（会被游戏回写，任务书 §3 第 0 步第 4 项要求启动前副本 + 退出后比较）

- `ra2youli/ddraw.ini` — bytes=14782, sha256=`c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52`（游戏可写，无启动前副本）
- `ra2youli/RA2MD.INI` — bytes=1754, sha256=`c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`（游戏可写，无启动前副本）
- `ra2youli/ra2md.ini` — bytes=1754, sha256=`c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`（游戏可写，无启动前副本）
- `ra2youli/RA2MD.INI.benchbak` — bytes=1754, sha256=`c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`（游戏可写，无启动前副本）
- `ra2youli/ddraw.ini.benchbak` — bytes=14352, sha256=`2f666b4dc048098e914137b7b7dddb8cacff2332343d7209b8c80896365e3dfb`（游戏可写，无启动前副本）
- `ra2youli/BATTLEMD.INI` — bytes=2733, sha256=`7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791`（游戏可写，无启动前副本）
- `ra2youli/BATTLEMD.INI.ra2forge.bak` — bytes=241, sha256=`9f804531c1955a785159306e045ac3b60dda0092f9639103fbc68dd19e15b412`（游戏可写，无启动前副本）
- `ra2youli/BATTLEMD98.INI` — bytes=453, sha256=`4e3417568924891792520ad8c3ab44f42e11fdc9934fb453d4db7210bf3d2c74`（游戏可写，无启动前副本）
- `ra2youli/ra2.ini` — bytes=1769, sha256=`867f85979dc62f3d5ed9663d4ffb6aebd066760b451c072e50251812080abb3b`（游戏可写，无启动前副本）
- `ra2youli/ra2render.ini` — bytes=16496, sha256=`27c9a60c55a8a1b422d3ef06b90e3d343a93eb523a600286c937198b363ecee4`（游戏可写，无启动前副本）
- `ra2youli/Register.ini` — bytes=211, sha256=`2ccdcb71b9f6b649ad6f8ca1b97e0cd42ee98a8000a7bafe1380c6d93aea9052`（游戏可写，无启动前副本）

- 本轮无真机授权，故**未**保存任何启动前副本、也未做退出后 diff；这些 sha 是「当前盘面」值。若后续真机趟回写了配置，旧结论只能作为历史参考，不得宣称「逐字节恢复」。
- 本轮实测：`RA2MD.INI.benchbak` 与当前 `RA2MD.INI` **字节完全相同**（sha `c91c6a47…cd3c27d`、1,754 B），只是 mtime 不同 ⇒ 它不是独立的更老基线，不能替代本轮启动前副本（任务书 §3 第 0 步第 4 项明确禁止）。`ddraw.ini.benchbak`（14,352 B / `2f666b4d…`）则与 `ddraw.ini`（14,782 B / `c983abad…`）不同。见 `BASELINE.json → identical_hash_groups`。

### B. 地图载体（`[8] Proving Grounds`）

- **未定位**与标签绑定的 `.map`/`.mpr` 字节载体（`BASELINE.json → map_search.verdict`）。
- 仅 1 个散装候选：`ra2youli/[8]试验地_Pro_ProvingGrounds.yrm`（175361 B，sha `3e3c874572bc02199cddce05b3633888caf968e6fbb457e763fb70b9fbfd5b19`），`[Basic] Name=[8] Proving Grounds` 位于文件偏移 `44355`（`[Basic]` 段偏移 `44346`）——这是 `[本次实测]` 的字节证据，但**扩展名是 .yrm 而非 .map/.mpr**，且无当趟游戏加载证据 ⇒ 与当趟实际输入是否同一份，`[待运行验证]`。
- 17 个 `.mix` 容器已登记 sha/大小，明文扫描 5 种模式无命中；索引未解析，**不能排除 MIX 内副本**。要在离线条件下重建地图身份，需要：MIX 索引解析（或本地源码/符号）、实际加载文件的字节副本、选图索引与文件身份绑定证据。
- 既有材料的选图索引还不一致（`_hl_match_14412.json:4-7`=265 / `STALL_CAPTURE_SUCCESS.md:12`=268 / `_maplist_full.txt:271`=269），未裁。

### C. 历史真机运行结果

- `lead/re_d13_ruling_20261112/_hl_match_14412.json` 等事件 JSON 只保存统计值与事件；`STALL_CAPTURE_FINAL.md:92-94` 自认**没有保存完整 3493 个样本序列**，因此 229 s 零Δ段连「用已有数据离线重算」都做不到，更无法离线重建采集过程。
- `_battle_stack_sample.json`、四份 RECEIPT、两份 STALL 报告、`STATIC_FRAME_SEMANTICS.md` 均为转引材料；本轮无授权、无原始活进程读数，不能重放。

### D. 来源/身份类材料（本轮根本没有）

- `ra2bench/gamemd.exe` 的「官方未修改原版」来源证明（发行介质、数字签名、构建记录、供应链）**不在本轮输入中**；只有「两份 exe 字节相同」与「§610 靶件指纹一致」两个实测事实。无法据此离线重建「原版对照臂」。
- 用户 2026-11-12 是否明示「统一真机以及一切操作」的原始会话记录不在本轮输入中；授权台账与回执冲突未裁（`CURRENT_FACTS.md §3`）。

## 要让它变成「可离线重建」，需要补什么

1. 在唯一写域内保存输入字节副本（或至少：受控只读引用 + 每次执行前重算 sha + 漂移即停批）；对本表 40 项逐一给出可验证来源。
2. 真机趟：为每个游戏可写 ini 保存启动前副本，退出后逐字节比较并恢复（任务书 §3 第 0 步第 4 项），不能用更老的 `.benchbak` 替代本轮基线。
3. 地图：解析 MIX 索引或保存实际加载的 `.yrm/.mpr` 字节 + 选图索引/文件哈希绑定；保持「未定位」直到有证据。
4. 采集：补授权后把帧号读数逐条流式落盘（NDJSON/CSV，含单调时钟、UTC、读取状态、状态标签），使摘要可离线复算（RE-N01）。
5. 来源：补发行介质/签名/构建记录，或明确写「原版对照臂未建立」，不得用分析镜像冒充。

## 本包自身的可重建性

- 命令：`python lead/next_re_20261112/RE-N00/_baseline.py`（纯离线，只读磁盘，零真机、零 git 写操作）。
- 重建产物：`BASELINE.json`（指纹 + 主机/工具链/git + 逐项 verification + 原始命令输出）、`INPUTS.tsv`、`CURRENT_FACTS.md`、`RECONSTRUCT.md`（本文件）。
- 重跑时若任一输入漂移，`verification.doc_2_2[*].match` / `verification.frozen_masters[*].match` 会自动变 `false` 并如实标出；不会静默沿用 2026-11-12 早些时候的哈希。

## 未覆盖项

- 未复制/归档任何输入字节；未归档 17 个 MIX 容器内部文件；未保存游戏可写配置的启动前副本；未重放任何历史真机采集；未解析 MIX 索引；未做来源/签名验证。
- 未执行任何 git 写操作；未对 291 条他人未提交改动做内容审阅。

## 未知项

- 上表各输入在未来是否被改动、由谁改动、改动后 sha 是多少；`_baseline.py` 重跑前无法预测。
- `[8] Proving Grounds` 的 `.map`/`.mpr` 是否在 MIX 内、当趟实际加载哪一份；选图索引 265/268/269 的差异原因。
- 分析镜像的官方原版身份；用户 2026-11-12 真机明示的原始记录及其生效范围。
- 历史 3493 个样本序列、229 s 段的原始读数能否从其它目录找回（本轮输入清单内没有）。

---
*本文件由 `_baseline.py` 生成；逐条 sha 均为本轮 `hashlib` 实算，未转引。*
