# 全库文档一致性审计与「过期结论」订正清单（DOCAUDIT）

> **任务**：DOCAUDIT · 全库文档一致性审计与「过期结论」订正清单（**只产出清单，不修改任何既有文档**）
> **基线二进制**：`ra2youli/gamemd.exe`（4,825,360 B，MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，官方 1.001；ImageBase `0x00400000`，`FileOffset = VA - 0x400000`）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **审计范围**：`docs/**/*.md` 全量 **147 份**（顶层 7 + `docs/re` 89 + `docs/re/dispatch` 51；本次实测）
> **现网源码对照（只读，双快照）**：`ra2render/blitter_hooks.cpp` —— **快照 A** = 82,259 B / mtime 2026-09-26 18:42:48；**快照 B** = 86,961 B / 1,892 行 / mtime **2026-09-27 09:06:28**；`ra2render/ra2render.ini` —— 快照 A = 2,747 B（`EnableMinimapFog=1` @ :45，MD5 `190709D025C133757142062F996E0ED6`）、**快照 B** = 2,996 B（`EnableMinimapFog=0` @ :46，MD5 `0B239E604546CBEF77F70DB31E86C048`，mtime 09:06:39）；`ra2render/ra2render.h`
> **机读产物**：`out/re_work/doc_audit/`（脚本 + 5 张候选表 + `claims.txt` + 门禁输出）
> **自证门禁**：`python tools/verify_anchors.py` → **323/323 PASS**；`python tools/audit_bytes.py out/re_work/doc_audit/claims.txt` → **全部 OK**（原始输出见 §7）
> **纪律**：只读 `gamemd.exe`；未写入 `ra2render/**`；未改顶层台账、未改任何既有 `docs/**`；所有判定均可由本页给出的 VA/FileOffset/机器码/源码行号复算。

---

## 0.0 双快照声明（必读：审计期间工作树被并行会话改动）

本次审计进行中，被审计对象**同时在被其他会话改写**（实测 mtime）：

| 对象 | 快照 A（本次审计前段读取） | 快照 B（本次审计末段复读） |
|---|---|---|
| `ra2render/blitter_hooks.cpp` | 82,259 B / 2026-09-26 18:42:48 | **86,961 B / 1,892 行 / 2026-09-27 09:06:28** |
| `ra2render/ra2render.ini`（双副本同 MD5） | 2,747 B，`EnableMinimapFog=1` @ :45，MD5 `190709D0…` | **2,996 B，`EnableMinimapFog=0` @ :46，MD5 `0B239E60…`** |
| `REVERSE_ENGINEERING_AND_PATCHES.md` | 195,268 B / 2026-09-27 08:47:18 | 198,746 B / 08:56:42（§七 行号经复读**逐字未变**） |

**处置原则（本次审计的应对）**：

1. **凡涉及现网源码行号/键值的判定，本清单一律给出双快照并标注时点**，避免出现「文档刚改对、源码又变了」的二次漂移；
2. **涉及 `gamemd.exe` 的字节断言与台账 §七 行号不受影响**：`ra2youli/gamemd.exe` mtime 仍为 2026-09-25 16:10:48（未被改动），台账 §七 L211-216 / L245-247 经 09-27 09:0x 复读逐字未变；
3. 快照 B 带来两项**重要反转**（本清单已同步）：
   - R-01/R-02/R-03 的**联机门控已在快照 B 落地**（`MpActive()` + `GetEffectiveTargetScanInterval/Key` + `GetEffectiveMinimapFog`），故「落地缺口」由「未实现」变为「**已实现、待真机验收**」；
   - `EnableMinimapFog` 的 ini 现值与 API 默认值双双回到 `0`，使 `hook_gate_gap_table.md` 的 F-11 勘误（「现值 1 / 行 45」）**在快照 B 下再次过期**；
4. 由此新增 **N-11（并发写入漂移）** 与 **P1-12**：**建议 Lead 在任何订正动作前先冻结 `ra2render/**` 与 `ra2render.ini` 的写入**，否则订正清单会被新构建持续推翻。

---

## 0. 结论速览

| 项 | 对象 | 判定 | 依据强度 |
|:--:|---|---|---|
| ① | `particle_fog_owner_evidence.md:5` 依据 MD5 | **真矛盾（已过时，文档卫生级）** | 二进制实测 MD5 与 29 份文档的基线不一致 |
| ② | `INSTALLED_HOOKS_AUDIT.md` / `MP_SAFETY_REVIEW.md` / `mp_release_safety_checklist.md` 的 #7/#8/#9 VIOLATION | **已过时（默认键下应降为 RISK）**；派工单的**文件归属有误**（#7/#8/#9 表在 `MP_SAFETY_REVIEW.md`，不在 checklist）；**pointer 分支 VIOLATION 仍成立** | 现网源码 `ThrottleKey()` 逐行 + 同库 `hook_gate_gap_table.md` 已定谳；**快照 B 起联机强制 position/interval 已落地**（见 §0.0） |
| ③ | `re_sprint_S18_report.md:18` vs :88-95 | **真矛盾，且比派工单更糟**：同一对象存在 **3 个互斥数值**（89/3、91/1、83/9）；第三个数在核心交付物 `offline_verification_alternatives.md` §6 逐项矩阵内 | 机读逐行统计（可复算），9 行清单已列出 |
| ④ | `re_sprint_S20_report.md:54` 图示 vs 汇总表 | **真矛盾，实为 3 套数字**：明细 5 行求和 = A 25 / B 1 / C 9；汇总行写 A 23 / C 11；图示 23/3/9 抄自 `deep_dive_sweeps_closure.md §0.1`，而该档案 §6 总表实测 **A 29 / B 1 / C 5** | 机读表格重算 + 35 行总表逐行分类 |
| ⑤ | `open_items_sweep.md §4` 清理指令 | **确认未执行**（§4 自述为「建议」）；全库仍有 **13 处** `## N. 未决问题` 标题未改写 | 全库标题枚举 |

**扩大扫描净增的高价值新发现（均非派工单所列）**

| # | 新发现 | 级别 |
|:--:|---|:--:|
| N-1 | 顶层台账 §七 **L1 Blitter 六行槽位地址 5 行错**（§2.2 六行全错）；二进制 dword 复算 + `telemetry_and_switches_spec.md` C-2 双证 | **P0** |
| N-2 | 顶层台账 §七 **裂缝保护补丁 2/3 的「原始字节」两行错**（`89 91 34 01 00 00`；实测 `89 B8` / `89 98 34 01 00 00`，48 份文档 + `anchor_claims.txt` 均为后者） | **P0** |
| N-3 | 雷达挂钩点同一对象在 **8+ 份文档**记 `0x006574C3`，现网源码安装点是 `0x00655D38`（`ARCHITECTURE_ATLAS.md`、`HOOK_POINT_MATRIX.md` 含「唯一合法落地实现」裁决均未同步） | **P0** |
| N-4 | `deep_dive_sweeps_closure.md:378` 断言「`IsBadReadPtr` 现网代码已全面移出控制流」，实测快照 A **17 处**、快照 B **19 处**（均含 6 处在控制流上） | **P0** |
| N-11 | **审计期间工作树被并行会话改写**：`blitter_hooks.cpp`（18:42→**09-27 09:06**）、`ra2render.ini`（`EnableMinimapFog` 1→0）在本审计进行中变更，使 §② 的「落地缺口」与 F-11 勘误**再次反转** → 订正前必须先冻结写入 | **P1** |
| N-5 | `deep_dive_sweeps_closure.md §2.4` 的 `Item T-4` 与同文 §6 总表 T-4/T-5 指代不同对象 | P1 |
| N-6 | `ARCHITECTURE_ATLAS.md §9.4` 只覆盖 G-01~G-09，同库 `hook_gate_gap_table.md §5` 定谳 G-01~G-10 | P1 |
| N-7 | `telemetry_and_switches_spec.md` C-1「双份 ini 行尾 LF vs CRLF」**已被事实推翻**（两文件 MD5 全同 `190709D025C133757142062F996E0ED6`，均 2,747 B） | P1 |
| N-8 | `open_items_sweep.md:41` 声称「下列 92 项」但表仅 12 行；§2 声称 164 条、表 33 行，摘要/明细落差未声明 | P1 |
| N-9 | `open_items_sweep.md:201` 引用不存在的 `blitter_microkernel.md`（实际为 `blitter_microkernel_deep_dive.md`） | P2 |
| N-10 | 派工口径「docs/re 88 / 全库 146」与实测（89 / 147）差 1；全库 `*.md` 引用存在性扫描得 29 个不存在的引用名（多为 `out/re_work` 工作产物） | P2 |

---

## 1. 派工单 5 项逐条复核

### ① `docs/re/particle_fog_owner_evidence.md` 头部依据 MD5 —— **真矛盾（已过时，文档卫生级）**

- **文件:行**：`docs/re/particle_fog_owner_evidence.md:5`
- **原文摘录**：
  > `> **依据二进制**：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`（MD5: `1011CE1B58C9B9BA...`, PE 32-bit x86）`
- **独立复核（二进制实测，非引用他人结论）**：`ra2youli/gamemd.exe` 的 MD5 = `4F37486E5B0DBE2AE5F45AEEE0F98367`（4,825,360 B），与 `docs/re/anchor_claims.txt` 头部基线、`ARCHITECTURE_ATLAS.md:6`、`mp_landing_consistency.md:5` 等 29 处一致。
- **波及面**：全库 `1011CE1B` 命中 5 处 —— 本文 :5（源头）、`docs/RE_COORDINATION.md:1039`（已登记「待修」）、`landing_pack_particle.md:40`（下游警告行）、`out/re_work/fixpack/_orig_landing_pack_particle.md:40`、`out/re_work/fixpack/_newB.json`。
- **判定**：**真矛盾 / 已过时**。但**本文机器码级结论不受影响**：抽验其核心断言仍与基线一致 —— `0x0062CF5F = 0F 85 26 03 00 00`（`jne 0x0062D28B`，见 §7 `claims.txt` PART 3），证实其对前序「黑雾 ret 8 原语」假说的自我更正**成立**。
- **根因**：该文档由独立取证方撰写，头部 MD5 取自取证机另一份镜像（截断/过期），属**证据溯源标注**缺陷，非结论缺陷。
- **附带**：`landing_pack_particle.md:39` 已用本轮实测 MD5 覆盖，故 ① 只需订正源头一处；订正后 :40 的警告行会变成新的历史陈述，须一并处理（见 §4 P2-2）。

### ② VIOLATION #7/#8/#9「指针哈希 desync」是否过期 —— **已过期（默认键下），但派工单文件归属有误，且 pointer 分支结论仍成立**

**先纠正一处归属**（避免 Lead 改错文件）：

| 文档 | 承载的判定 | 原文行 |
|---|---|---|
| `docs/re/MP_SAFETY_REVIEW.md` | **#7/#8/#9 = VIOLATION×3**（真正的「#7/#8/#9」表在此） | :19、:53、:63、:73、:112、:120、:269-271、:293-299、**:445（§8 勘误附录仍写「维持不变」）** |
| `docs/re/INSTALLED_HOOKS_AUDIT.md` | 同等结论，措辞为「**禁止**」 | :67、:68、:69、:150、:162、:262 |
| `docs/re/mp_release_safety_checklist.md` | 用 MP-G02（VIOLATION）/ MP-G08（RISK），**没有** #7/#8/#9 表 | :63、:69 |

**现网源码复核（当前工作树，未改写）**：

```c++
// ra2render/blitter_hooks.cpp:159-184
// L2 分片键（缺陷2 修复）：旧实现 unitHash = 指针地址>>4 ……
int g_targetScanKey = 1;   // 0=pointer(旧,仅单机) 1=position(默认,联机安全)
static uint32_t ThrottleKey(void *pThis) {
    if (!g_targetScanKey) { return (uint32_t)(uintptr_t)pThis >> 4; }        // :169 pointer 分支
    if (!pThis || IsBadReadPtr(…+0x9C, 8)) return 0;                         // :171
    int locX = *(int*)((uint8_t*)pThis + 0x9C);
    int locY = *(int*)((uint8_t*)pThis + 0xA0);                              // :175-176
    return ((locX*0x9E3779B1u) ^ (locY*0x85EBCA77u)) >> 4;                   // :177-179
}
```
- 三处节流调用点 `:436` / `:457` / `:495` 均已改为 `unitHash = ThrottleKey(pThis)`；**已不存在**被审计文档引用的 `:404/:425/:463` 处的 `(uintptr_t)pThis >> 4`。
- `ra2render.ini:49 = TargetScanKey=position`（第二个 `[Logic]` 段内）；`blitter_hooks.cpp:91-92` 读取默认值即 `"position"`。
- **同库已有最新定谳**：`hook_gate_gap_table.md:36`「#7/#8/#9 在默认键下从 **VIOLATION → RISK**（待对拍）；pointer 分支仍是 VIOLATION」；:142-150 给出 position 键为 `CurrentFrame` 纯函数的推导；`docs/RE_COORDINATION.md:648`「默认 position 键下 L2=RISK（非 VIOLATION）；VIOLATION 仅 pointer 分支」。

**判定**：
1. **「指针哈希 desync」对 #7/#8/#9 在默认配置下已不成立** → VIOLATION / 禁止 属**已过时结论**，应降级为 **RISK（待对拍）**。
2. **VIOLATION 未完全消失**：`TargetScanKey` 仍是可配项，`pointer` 分支保留旧指针键（`:168-169`）⇒ pointer 分支仍为 VIOLATION，「禁止联机用 pointer」结论仍有效。
3. **关键补充（双快照，原文档均未覆盖）**：
   - **快照 A**（82,259 B / 09-26 18:42）：`ra2render/**` **不存在任何 `MpActive()` / 联机检测代码**（对 `MpActive|Multiplayer|ForceSinglePlayer|MpStateWrites|MpAutoDowngrade|EnableThreatRetention` 全量 grep **0 命中**）⇒ R-01/R-02/R-03 未落地；
   - **快照 B**（86,961 B / 09-27 09:06:28）：**已落地** —— `MpActive()`（`:58-80`，主判定 `*(uint8_t*)0x00A8D5F8 & 0x02`，与 F-10 裁定一致）、`GetEffectiveTargetScanInterval()`（`:82-87`，联机返回 1 = R-03/G-08）、`GetEffectiveTargetScanKey()`（`:89-94`，联机返回 1 = position，R-02/G-02）、`GetEffectiveMinimapFog()`（`:96-106`，联机强制 false）、`CheckMpGateTransition()`（`:108-133`，含红字告警 `:129-131`）。
   ⇒ **文档侧仍须降级判定（结论过期），但工程侧缺口在快照 B 已闭合**；残留项转为「待真机验收」（见 §6 U-3 已结案、U-2 仍开）。
4. 由此，MP-G02 的准确形态是：**默认配置已安全；快照 B 起联机强制 position 已实现，仅剩「单端误配 + 无联机检测失败」的残余面**。

### ③ `re_sprint_S18_report.md` 第 18 行 vs 第 88 行表格 —— **真矛盾，且实测存在 3 个互斥数值**

| # | 位置 | 原文数字 | 机读复核 |
|:--:|---|---|---|
| a | `re_sprint_S18_report.md:18` | 「**89 项达到 `[极高]`**（占比 96.7%），**3 项达到 `[高]`**（占比 3.3%）」 | 89+3=92 ✓ 自洽 |
| b | `re_sprint_S18_report.md:88-95` 表 | 31+14+18+16+12 = **91** 极高；1+0+0+0+0 = **1** 高；汇总行 :95「**91 (98.9%)** / **1 (1.1%)**」 | 91+1=92 ✓ 自洽 |
| c | `re_sprint_S18_report.md:107`（台账草稿） | 「91 项极高、1 项高置信度」 | 与 b 同 |
| d | **核心交付物** `offline_verification_alternatives.md:95-100` §1 汇总 | Sub-1「极高 (96.8%)」、Sub-2~5「极高 (100%)」→ **91/1** | 与 b 同 |
| e | **核心交付物** `offline_verification_alternatives.md:1948` §7.3 | 「**89 项 `[极高]`**（96.7%）；**3 项 `[高]`**（3.3%）」 | 与 a 同 |
| f | **核心交付物** `offline_verification_alternatives.md §6 逐项矩阵`（:1757-1850，92 行） | 逐行第 6 列置信度单元格 **实测 = 极高 83 / 高 9**（92 行，无第三值） | **与 a、b 均不同** |

- **机读复算方法**：解析 Markdown 表，只接受首列为纯数字的行（序号 01~92），取第 6 列（表头「置信度」）去反引号后精确匹配 `极高` / `高`（`极高` 不会误匹配 `高`，因反引号位置不同）。脚本：`out/re_work/doc_audit/verify_specific2.py`。
- **9 行「高」清单（可直接定位订正）**：`B-R01`(:1759)、`B-R10`(:1768)、`B-R11`(:1769)、`B-R18`(:1776)、`B-R27`(:1785)、`B-A11`(:1801)、`B-N14`(:1818)、`B-L04`(:1826)、`B-M10`(:1848)。
- **判定**：**真矛盾**（派工单所述 18 行 vs 88 行矛盾成立），并**扩大为三值冲突**，第 f 项落在交付物本体上 ⇒ 矛盾不是「S18 报告抄错」，而是**「逐项矩阵」与「各处汇总」从未对齐**。
- **不作猜测**：谁是真值需 Lead 裁定（属"逐项数据 vs 多处汇总"，外部机械手段无法裁决原意）。见 §6 U-1。

### ④ `re_sprint_S20_report.md` 第 54 行图示 vs 汇总表 —— **真矛盾，实为 3 套数字**

- **图示**（:52-56）：A 类 **23 项(65.7%)** ｜ B 类 **3 项(8.6%)** ｜ C 类 **9 项(25.7%)**
- **明细表**（:60-66）逐行：`pathfinding 7=6/0/1`、`targeting 6=5/0/1`、`rle_blit 9=7/0/2`、`MP_SAFETY_REVIEW 5=2/1/2`、`nonrle 8=5/0/3` → **列求和 = A 25 / B 1 / C 9 = 35**。
- **汇总行**（:67）：`| **全量汇总** | **35** | **23** | **1** | **11** | **100%** |` → **A 23 / B 1 / C 11**。
- **上游档案** `deep_dive_sweeps_closure.md §0.1`（:34/:38/:40/:42）：`A 23 / B 3 / C 9`（S20 图示即抄自此）。
- **上游档案 §6 总表**（:506-540，35 行）逐行分类**机读统计 = A 29 / B 1 / C 5**；按文档：`pathfinding 7/0/0`、`targeting 6/0/0`、`rle_blit 7/0/2`、`mp_safety 2/1/2`、`nonrle 7/0/1`。
- **判定**：**真矛盾**，且派工单描述需修正：
  1) S20 自身：图示 23/3/9 ⟷ 明细行求和 25/1/9 ⟷ 汇总行 23/1/11（**三处两两不符**）；
  2) 与上游 §0.1（23/3/9）一致的是**图示**，而 §0.1 与**自己的 §6 总表（29/1/5）也不符**。
  ⇒ 同一对象（35 项清零分类）全库存在 **4 组数字：23/3/9、25/1/9、23/1/11、29/1/5**，其中只有 §6 总表逐项可复算。
- **机读证据**：`out/re_work/doc_audit/candidates_table.md`（通用合计行自检命中 S20:67 两处：A 列声明 23 / 数据行求和 25；C 列声明 11 / 数据行求和 9）。

### ⑤ `open_items_sweep.md §4` 清理指令 —— **确认只是建议，且未实际执行**

- **原文**（`docs/re/open_items_sweep.md:229-231`）：
  > `## 4. 全库文档标记清理与操作指引（Cleanup Directives）`
  > `为防止后续波次或外部审查人员再次被历史遗留的 `未决`、`待实测` 字样误导，**建议**对全库各文档执行如下标准化清理作业：`
- **独立复核（全库标题枚举）**：§4 点名要求改写的标题**一个都没改**。实测仍存 **13 处**未加闭环标注的 `未决问题` 章节（下列 13 项，**枚举已于 2026-09-27 由 DA2 补全 `vxl_cache_layout.md:10`**）：
  `superweapon_re.md:606`、`clock_frame_loop.md:376`、`rle_blit_family.md:638`、`fx_draw_chain.md:459`、`radar_minimap_dots.md:226`、`audio_input_hotspots.md:424`、`house_team_ai_update.md:325`、`net_sync_checksum.md:412`、`nonrle_blit_and_named_hotspots.md:270`、`pathfinding_locomotion.md:384`、`visibility_gap_spysat.md:400`、`vxl_render_sort.md:393`、**`vxl_cache_layout.md:10`**（`## 一、未决问题（Q1–Q8）结论总表`；**DA2 补正本行原只列 12 项、与「13 处」计数不符 —— 已补全**）（另 `open_items_sweep.md` 自身 §2 仅在表内写「标记可清理」）。
  全库 grep `历史未决问题` 仅命中 `open_items_sweep.md` 自身的 4 条**指令文本**（:234/:237/:240/:243）⇒ **零执行**。
- **判定**：**成立（未执行）**；性质为**文档卫生 + 误导面**（后续波次按 `未决` 字样重复派工），非结论错误。§4 措辞「建议」+ §2「标明可清理」把执行责任外置，属**未闭环的交接缺口**。

---
## 2. 扩大扫描：方法、抽取规则与误报过滤

### 2.1 流水线（全部脚本在 `out/re_work/doc_audit/`，可复跑）

| 脚本 | 作用 | 输出 |
|---|---|---|
| `scan_docs.py` | 遍历 `docs/**/*.md`（147 份）：抽取全部 `0x…` 地址（归一化 8 位）、`+0xNN` 偏移、计数断言，并计算每处地址出现行的「符号签名」 | `scan_raw.json`（6,943 唯一地址 / 454 唯一偏移 / 1,046 条计数断言） |
| `analyze.py` | ① 地址符号签名互斥候选；② 10 个主题的计数口径分组；③ **通用表格合计行自检** | `candidates_addr.md`、`candidates_num.md`、`candidates_table.md` |
| `analyze_tight.py` | 收紧规则 v2：**同一行 ≥2 个地址则丢弃该行符号归属**（不可判定）、地址出现在 2~8 份文档、两侧均含符号型 token 且交集为空 | `candidates_addr_tight.json`（359 对 / 157 唯一地址） |
| `analyze_yrpp.py` | 用 `YRpp/*.h` 的 `JMP_THIS(0x…)` 建「地址→类」映射（963 条），与文档类名声明比对 | `candidates_yrpp.md`（257 对） |
| `check_refs.py` | 抽取并校验文档内 `*.md` 引用是否存在 | `candidates_missing_ref.md`（1,479 次引用 / 29 个不存在的引用名） |
| `verify_vtable_claims.py`、`verify_vtable2.py` | 对「槽位 VA → 原始实现 VA」类声明做 **dword 复算**，不等则在全镜像反查真实槽位 | 见 §3.1（N-1） |
| `verify_specific.py`、`verify_specific2.py`、`verify_specific3.py`、`verify_specific4.py` | S18/S20/`deep_dive` 口径定点复算、MP 判定条目计数、G 编号覆盖、矩阵逐行置信度统计 | 结论已内联本页 |
| `gen_claims.py` | 从 `gamemd.exe` 实测字节生成 `claims.txt` | `claims.txt`（26 条断言，经 `audit_bytes.py` 全 OK） |

### 2.2 抽取规则（明确、可辩护）

1. **地址**：`\b0x([0-9A-Fa-f]{6,8})\b` → `0x%08X`（消除前导零/大小写差异）。
2. **符号签名**：同一行的反引号代码跨度 + `Class::Method` + `Hook_*`/`ADDR_*` + 编号族（`G-01`/`F-02`/`H-D1`/`B-R05`/`P-M3`/`T-4`…）。
3. **计数断言**：含 `共/合计/总计/全量/全部/累计/小计` 或数值 ≥5 的「数字+量词（项/条/处/个/类/份/行/字节…）」。
4. **表格自检**：任一表格中首列匹配 `全量汇总|合计|总计|全库总计|小计` 的行，其每个纯数字单元格 vs 其余数据行同列求和（**不依赖任何外部口径**，纯内部一致性）。
5. **虚表声明**：`(槽位VA, 声明目标VA)` → 读 `FileOffset(槽位VA)` 的 4 字节小端比对；不等则全镜像反查该目标 dword 的真实位置。

### 2.3 误报过滤依据（为什么剩下的是真候选）

| 误报类型 | 例子 | 过滤依据 |
|---|---|---|
| 命名体系不同（同一对象） | `ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G` 与 `?$RLEBlitTransXlat@G::Blit` | 符号集互斥但均可回溯到同一 `0x004960A0` ⇒ 判「命名漂移」而非冲突 |
| 同路段并列多个地址 | `NEXT_RE_AND_MODERNIZATION.md` 的「地址 + 符号」两列表格 | 规则②「一行 ≥2 地址 ⇒ 不归属符号」，剔出 15,037 行次 |
| 基类/派生类不同写法 | `0x006DA7D0`：`TacticalClass` 与 `CellClass` | YRpp 中该地址同属 `TacticalClass.h`（`NOVTABLE` 标记），判同一对象 |
| 引用工作产物路径 | `out/re_work/**` 下已清理的中间文件 | 只保留 `docs/**` 内、且非产物路径的缺失引用 |
| 全角/半角与空格 | `( *(uint8_t*)0xA8D5F8 & 0x02 )` 之类写法 | 归一化后同址同义 |
| **规则本身无法裁决「原意」** | S18 的 89/3 与 91/1 | 明确列入 §6 未闭环，交 Lead 裁定，**不静默取舍** |

> `candidates_addr.md`（942 组）与 `candidates_yrpp.md`（257 对）保留为**原始候选池**（表内已标注误报来源）；进入 §4 清单的条目都经过人工读原文 + 二进制/源码裁决。

---

## 3. 新发现的不一致候选（已人工判定，含误报说明）

### 3.1 N-1 顶层台账 L1 Blitter 虚表槽位整组错（**P0**）

**声明侧**：`REVERSE_ENGINEERING_AND_PATCHES.md §2.2:56-61`（虚表基址 `0x007F1BE0` 等 6 行）与 **§七:211-216**（槽位 `0x007F1BE4` 等 6 行）。
**裁决侧（二进制 dword 复算，FileOffset = VA − 0x400000）**：
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

| 台账声明槽位 | 实测 dword | 声明目标 | 判定 | **真实槽位（全镜像反查）** |
|---|---|---|---|---|
| `0x007F1BE4` | `0xFFFFFF3E` | 0x00494B60 | 错 | **0x007E56F4** |
| `0x007F10C4` | `0x004F4410` | 0x004912B0 | 错 | **0x007E5A24** |
| `0x007E55C4` | `0x004960A0` | 0x004960A0 | 对（Lead 已更正过） | — |
| `0x007F1044` | `0x004104A0` | 0x007BC890 | 错 | **0x007F7BF8** |
| `0x007F1504` | `0x00000078` | 0x00492670 | 错 | **0x007E59F4** |
| `0x007F0FC4` | `0x004104F0` | 0x007BC7F0 | 错 | **0x007F7BC8** |

- 邻域反证：`0x007F1BD0~0x007F1BF4` 的 dword 为 `0x0000004B / 0xFFFFFF30 / 0xFFFFFF39` 等（小整数/负数），**不是函数指针表**；而 `0x007E56E0~0x007E570C` 为连续 `0x0049xxxx` 代码指针（真虚表）。
- **同库独立记载**：`telemetry_and_switches_spec.md:215`（C-2）给出与本次实测**逐字一致**的正确映射，并指出「台账内部也自相矛盾 —— v1.5.7 行（L540-544）的 `0x007E55C4` 等与 `ra2render.h` 一致」。⇒ 本次为**独立复算确认**，且该 C-2 订正**至今未施加到台账**。
- **影响**：按台账 §七/§2.2 的槽位地址挂钩或审计，全部「找不到补丁」（C-2 原文语）。
- 误报排除：`0x007E56F0+4`、`0x007E5A20+4`、`0x007F7BF4+4`、`0x007E59F0+4`、`0x007F7BC4+4`（`INSTALLED_HOOKS_AUDIT.md`、`hook_gate_gap_table.md` 写法）**全部 dword 复核通过** ⇒ 两组写法不是「两套等价地址」，而是**一错一对**。

### 3.2 N-2 顶层台账裂缝保护补丁 2/3 原始字节错（**P0**）

- **声明侧**：`REVERSE_ENGINEERING_AND_PATCHES.md:245-246`
  > `| 裂缝保护热补丁 2 | 0x00577EC5 | 89 B8 34 01 00 00 | 6 字节 90 (NOP)〔勘误 ASM-FIX-9〕原记 `89 91 34 01 00 00`（`mov [ecx+0x134], edx`）全镜像 0 命中；实测断言 0x00577EC5: 89 B8 34 01 00 00（`mov [eax+0x134], edi`） | …`
  > `| 裂缝保护热补丁 3 | 0x00577B60 | 89 98 34 01 00 00 | 6 字节 90 (NOP)〔勘误 ASM-FIX-9〕原记 `89 91 34 01 00 00` 全镜像 0 命中；实测断言 0x00577B60: 89 98 34 01 00 00（`mov [eax+0x134], ebx`） | …`
- **实测**：`0x00577EC5 = 89 B8 34 01 00 00`；`0x00577B60 = 89 98 34 01 00 00`（§7 `claims.txt` PART 3）。
- **旁证（48 份文档 + 唯一事实源）**：`anchor_claims.txt:68-69`、`ARCHITECTURE_ATLAS.md:1264/1266`、`landing_pack_gap_spysat.md:24/68/423-424`、`re_sprint_S1_report.md:220/224`、`pending_execution_master_table.md:45-46/120-121` 等**全部**为 `89 B8` / `89 98`；`89 91 34 01 00 00` 全库 **0 命中**（除台账这两行）。
- 注：补丁 1（`0x00568273 = 89 99 34 01 00 00`）实测**正确**（台账 :244 亦正确）。
- 误报排除：寄存器语义不同（`edi` vs `ebx`）恰恰说明这两行不是「简写」，而是**错的字节串** —— 台账 :245/:246 连寄存器都写成了同一个 `ecx` 形态。

### 3.3 N-3 雷达挂钩点：同一对象多份文档记 `0x006574C3`，现网安装点 `0x00655D38`（**P0**）

- **现网源码事实**：`blitter_hooks.cpp` 快照 A 的 `:1492`（= 快照 B 的 `:1596`）处 `rel32 = &Hook_RadarPlot_Cell_Proxy - (0x00655D38 + 5)`；快照 A `:51` 注释「Plot_Cell 0x655D38 跳板（路线 A）」；`ra2render.h:73` 的 `ADDR_RADAR_PLOT_CALLSITE 0x006574C3` **已非安装点**（`hook_gate_gap_table.md:107` 明示「仅为文档宏」）。
- **字节证据**：`0x006574C3 = E8 88 E7 FF FF`（原版调用点原文，镜像只读故仍为此形态）；`0x00655D38 = 89 44 24 28 A1 50 35 B7 00`（路线 A 9 字节区）。
- **未同步的文档（按严重度）**：

| 文档:行 | 原文要点 | 判定 |
|---|---|---|
| `ARCHITECTURE_ATLAS.md:517-518` | 「#### 1. 主调用点代理覆写（`0x006574C3`）… **挂钩位置**：`0x006574C3`（原版指令：`E8 88 E7 FF FF call 0x00655C50`）」 | **已过时**（该文件 mtime 23:15，晚于路线 A 落地 18:42） |
| `ARCHITECTURE_ATLAS.md:99`、:1886` | 拓扑图「雷达小地图主循环覆写 (0x006574C3 + 0x0065719A)」、「RadarClass::Plot_Cell @ 0x006574C3」 | 已过时（:1886 还把 `Plot_Cell` 归到调用点地址，函数本体实为 `0x00655C50`） |
| `HOOK_POINT_MATRIX.md:314`（并 :150/:303/:357/:358） | 「**裁定 0x006574C3（调用点覆写）+ 0x0065719A（跳帧抑制）为小地图唯一合法落地实现**」 | **已过时**（裁决对象已变；`0x00655F48` 废弃结论仍成立） |
| `INSTALLED_HOOKS_AUDIT.md:111`（#20） | 「调用点 `0x006574C3`（call rel32 等长）+ `0x00655C50` 前 5 字节蹦床」 | 已过时 |
| `MP_SAFETY_REVIEW.md:166`、:282` | 同上 | 已过时（SAFE 判定不受影响） |
| `telemetry_and_switches_spec.md:70` | 「调用点 **0x006574C3**（call rel32 等长替换 L1448-1461）+ Plot_Cell 前 5 字节跳板」 | 已过时 |
| `v160_static_contract.md:14`、:27`、:33`、:35` | 「**机器码替换**：`0x006574C3` 处 5 字节 `E8 88 E7 FF FF` 被重定向至代理函数」 | 已过时（属 v1.6.0 构建快照，需标注「后被路线 A 取代」） |
| `REVERSE_ENGINEERING_AND_PATCHES.md:247`（§七） | 「L5 小地图 Plot 代理 ｜ `0x006574C3` ｜ `E8 88 E7 FF FF` ｜ `E8 [Hook_RadarPlot_Proxy]` ｜ …（v1.6.0 已挂载）」 | 已过时（台账属只读红线，**建议由 Lead 裁定是否订正**） |
| `mp_autodowngrade_spec.md:289` | 「`Hook_RadarPlot_Proxy` `0x6574C3`」 | 已过时 |
| `radar_minimap_dots.md:279`、`re_sprint_S10_report.md:46/108`、`v160_acceptance.md:39` | 作为**原版调用链事实**记录 `0x006574C3: call 0x00655C50` | **无问题**（原版镜像事实，非补丁点） |

- **误报说明**：`0x006574C3` 本身确实存在（原版 `call 0x00655C50`），引用它不算「错地址」；**错的是把它当成现网补丁安装点**。这一区分直接决定 P0/P1 分级（见 §4）。

### 3.4 N-4 `deep_dive_sweeps_closure.md`：`IsBadReadPtr`「已全面移出控制流」不成立（**P0**）

- **原文**（`docs/re/deep_dive_sweeps_closure.md:375-378`）：
  > `### 4.1 Item M-1：IsBadReadPtr 参与逻辑帧控制流风险清零 [实证]`
  > `严禁使用 IsBadReadPtr 进行游戏状态分支判定。**现网代码已全面移出控制流**，由引擎单例池与对象生命期指针边界做静态门控。`
- **实测（双快照，结论在两侧都成立）**：
  - **快照 A**（82,259 B）：**17 处** `IsBadReadPtr`，其中 **6 处在逻辑/节流控制流上**：`:171`（`ThrottleKey` 读 `+0x9C` 前判定，失败即 return 0 参与分片）、`:435`、`:456`、`:494`（`currentFrame = IsBadReadPtr(...) ? *p : 0` → 直接影响 `currentFrame > 0` 节流门）、`:487`、`:489`（Retention 短路门）；其余 11 处在 TYPE/扫描辅助路径（`:601/604/609/625/628/633/664/666/791/810/1597`）。
  - **快照 B**（86,961 B / 1,892 行）：**19 处**（新增 `:64`、`:70`），控制流相关行号平移为 `:269`（`ThrottleKey`）、`:533`、`:555`、`:594`（`currentFrame` 门）、`:587`、`:589`（Retention 短路门）。
  ⇒ 两侧均**不支持**「已全面移出控制流」的断言。
- **上游同源意见（未落地）**：`MP_SAFETY_REVIEW.md:100/122/410` 只列为「低概率边界 / 建议移出」，**并未断言已移出** ⇒ `deep_dive_sweeps_closure.md:378` 的「已全面移出」是该档案**自行加码**。
- **判定**：**已过时/不实**（影响判断：读者会认为 M-1 风险已清零，而「控制流依赖」仍在；§6 总表 #23 处置状态亦写「彻底移除…已确证定谳」）。属**规格与现状混写**，应改为「规格：应移出；现状：17 处仍在，未落地」。
- 误报排除：已逐行读源码确认，均为可编译语句，非注释。

### 3.5 N-5 `T-4` / `T-5` 指代漂移（P1）

- `docs/re/deep_dive_sweeps_closure.md:284` 小节标题「`### 2.4 Item T-4：现网 L2 Hook 与 Target Retention 联机安全闭环`」，正文讲 Retention/节流（`:287-288`）。
- 同文 §6 总表：`#11 T-4 = 三路寻敌枚举分工`（`:516`）、`#12 T-5 = Target Retention 联机安全红线`（`:517`）。
- ⇒ **同一档案内 T-4 指代两个不同对象**；且 §6 表的「三路寻敌枚举分工」「空间哈希升级确定性规范」(T-6) 在 §2 正文**无对应小节**（§2 只有 2.1~2.4）。
- 误报排除：不是「T-4 合并了 T-4/T-5」的表述歧义 —— `:285` 的「源文索引」只指 `targeting_deep_dive.md §5.1/§5.2`，未覆盖 T-4 的三路枚举（`§4.3`）。

### 3.6 N-6 G 编号覆盖不一致（P1）

- `docs/re/hook_gate_gap_table.md:244`「执行缺口表 ｜ **G-01～G-10 全量** ｜ §5」；:272` 给出 **G-10** 裁定（`UnlockGameSpeed` 死键 / RLE 死宏 / 死代码 #10：判 SAFE 级卫生项，P2）。
- `docs/re/ARCHITECTURE_ATLAS.md §9.4`（:1530-1544）标题即「**G-01 ~ G-09** 联机安全门控矩阵总览」，矩阵只有 G-01~G-09（机读：该文件中 G-01…G-09 全部命中，**无 G-10**）。
- `hook_gate_gap_table.md:258` 自己也声明「权威落点…`ARCHITECTURE_ATLAS.md §9.4 L1530-1544（G-01～G-09 联机安全门控矩阵）`」⇒ 缺口表**知情**地面向 9 条矩阵，但 §5 又按 G-01…G-10 全量运作。
- 判定：**口径不一致（轻）**：G-10 属「卫生项」而非「安全门控」，atlas 只列门控并非错误，但**未加范围声明**，按 G 编号全量检索会漏 1 条。

### 3.7 N-7 `telemetry_and_switches_spec.md` C-1 已被事实推翻（P1）

- 原文（:214）：「双份 ini 内容一致但行尾不一致：`ra2render/ra2render.ini` 为 LF，`ra2youli/ra2render.ini` 为 CRLF；去 CR 后 diff 为空」。
- 实测：两文件 **MD5 完全相同** = `190709D025C133757142062F996E0ED6`，均 2,747 B；`Compare-Object` 逐行比对 **IDENTICAL**（49 行）⇒ 行尾差异已不存在。
- 判定：**已消解（stale）**。C-1 的「影响=低」无害，但会把后续审计引向不存在的差异。

### 3.8 N-8 / N-9 摘要 vs 明细、引用不存在的文件（P1/P2）

- `docs/re/open_items_sweep.md:41`「下列 **92 项**条目…」→ 其下表格实际 **12 行**（`B-01`~`B-12`）；§2（:166`）「**164 处**条目」→ 表实际 **33 行**；§0 图示 164/26/92 = 282 自洽，但**「表是样本而非全量」未声明**。
- `docs/re/open_items_sweep.md:201` 引用 `blitter_microkernel.md §8` —— **该文件不存在**（实际为 `blitter_microkernel_deep_dive.md`，机读于 `candidates_missing_ref.md`）。
- 其余 27 个「不存在引用」多为 `out/re_work/**` 历史产物（如 `matrix_5fields.md`、`fixpack_diff_F01-F13.md`）与 `PROTOCOL.md`（`out/loadbench/PROTOCOL.md` **实测不存在**，全库被引用 43 次）⇒ 见 §4 P2-5。

---
### 3.9 N-11 审计期间工作树被并行会话改写（P1，程序性发现）

- **实测时间线**（`Get-Item` 逐次读取）：
  - `ra2render/blitter_hooks.cpp`：审计前段 = 82,259 B / 2026-09-26 18:42:48 → 审计末段 = **86,961 B / 2026-09-27 09:06:28**（同业会话写入）；
  - `ra2render/ra2render.ini`：2,747 B（`EnableMinimapFog=1` @ :45）→ **2,996 B（`EnableMinimapFog=0` @ :46）**；
  - `REVERSE_ENGINEERING_AND_PATCHES.md`：195,268 B / 08:47:18 → 198,746 B / 08:56:42（§七 行号经复读逐字未变）；
  - `docs/re/weapons_damage_production.md`、`docs/re/shroud_click_interaction.md` 等同期亦被其他任务写入（`out/re_work/damage_pipeline/**`、`out/re_work/shroud_click/**` 活跃）。
- **影响**：本清单 §② 与 P0-4…P0-7、P1-8、P1-12、U-3 均因这次写入**发生反转**（R-01/R-02/R-03 落地、ini 现值回到 0）。若不冻结写入就执行订正，会立刻产生新的过期结论（P1-12 即是实例）。
- **判定**：**程序性/流程性发现**（非文字矛盾）。建议 Lead：① 冻结 `ra2render/**` + `ra2render.ini`；② 以**同一构建**为口径重跑本清单的源码依赖项（脚本已备）；③ 在台账 §九 登记本次「审计期间构建漂移」事件。
- **误报排除**：这与「文档陈旧」性质不同 —— 本项是本审计捕获的**活体改动**，故以 mtime + 尺寸 + MD5 三元组留证（见 §0.0 表）。

---

## 4. 最小就地订正清单（Lead 按此执行）

> **约定**：改前原文为本次审计读到的**逐字文本**（行号以本次快照为准，文件若有追加会略移）。
> 「风险」列说明订正副作用；凡涉及**证据/裁决文档原始记录**的订正，一律建议以**勘误块**追加（保留原文），与 `MP_SAFETY_REVIEW.md §8` 和 `hook_gate_gap_table.md` 附录的既有惯例一致。

### 4.0 执行状态（Lead 回填，2026-09-27 10:05）

> 本清单为**审计快照**；执行状态由 Lead 随推进回填。**行号以各自执行时的文件为准**——部分文件已历多轮订正，行号已漂移（例如 `deep_dive_sweeps_closure.md` 的 §6 总表区由 `:506-540` 移至 `:513-547`）。

| 编号 | 状态 | 执行方 / 依据 |
|---|---|---|
| **P1-1 / P1-2** | ✅ **已定谳 + 已订正**：S18 真值 = **83 极高 / 9 高**（`re_sprint_S18_report.md:18` 与 `offline_verification_alternatives.md:1948` 均已就地勘误） | DSH-DA3（台账 `[v1.6.9]`）；Lead 独立复算确认 |
| **P1-3 / P1-4（S20 计数组）** | ✅ **已定谳 + 已订正**：S20 真值 = **A 29 / B 1 / C 5**（报告图示与明细/汇总两处已勘误） | DSH-DA3；Lead 独立复算（35 行逐行） |
| **P0-8 / P0-9**（本台账 §七 裂缝补丁字节 / §2.2 与 §七 Blitter 槽位） | ✅ **已执行**（13 处就地订正，原值保留对照） | **Lead**（台账 `[v1.6.5]`） |
| **P0-1 / P0-2 / P0-3 / P0-4 / P0-5 / P0-6 / P0-7 / P1-12** | 🔄 **执行中**（独占写 6 份文档） | DSH-DA1（`b0fa0b76-…`） |
| **P0-10 / P1-5~P1-11（含 P1-10 / P1-11）** | 🔄 **执行中**（独占写 5 份文档） | DSH-DA2（`3f112321-…`） |
| **closure 专项三项**：§0.1 图示 `23/3/9` → `29/1/5`；`N-7` 标题补「C 类」；`:521`/`:541` 两处字节串改为 `D1 F8` / `52 8B 54 24 20` | ⏳ **待派 DA3b**（该文件正被 DA2 独写，须待其交回后再动） | Lead 裁定；实测由 DSH-DA3 提供 |
| **U-1（S18 真值）/ U-2（N-7 归类）** | ✅ **已裁定**：83/9；`N-7` **维持 C 类**（⇒ 分布 29/1/5） | **Lead**（台账 `[v1.6.9]`） |
| **U-3 / U-4** | ⏳ U-3 → 并入 closure 专项（DA3b）；U-4 → 已由本表 P1-1/P1-2 回填闭环 | — |

> **快照提示（DA3 双快照声明）**：`deep_dive_sweeps_closure.md` 在 DA3 执行期间被 DA2 改写（§6 总表区 `:506-540` → `:513-547`，MD5 `EADE7522…`）；DA3 已用快照 B 重跑逐行重算，**29/1/5 不变**。今后引用该文档行号须注明快照。

---

### P0 · 影响判断的过期结论（10 项）

| 编号 | 目标 文件:行 | 改前原文（摘） | 改后文本（建议） | 理由 | 风险 |
|:--:|---|---|---|---|---|
| **P0-1** | `docs/re/ARCHITECTURE_ATLAS.md:517-518` | `#### 1. 主调用点代理覆写（0x006574C3）` ／ `- **挂钩位置**：0x006574C3（原版指令：E8 88 E7 FF FF call 0x00655C50）；` | `#### 1. Plot_Cell 内部下沉代理（0x00655D38，路线 A）` ／ `- **挂钩位置**：0x00655D38（9B：E9 rel32 + 4×90；跳板还原后 jmp 0x00655D41）。旧口径 0x006574C3（原版 E8 88 E7 FF FF call 0x00655C50）为 v1.6.0 及以前方案，路线 A 落地后已废弃；` | 源码 `blitter_hooks.cpp:1492`；字节 `0x00655D38` / `0x006574C3`（`claims.txt` PART 1）；`hook_gate_gap_table.md:37/102` 已定谳 | 低。须**同步** :99、:1886 两处拓扑图同址；:1886 的「RadarClass::Plot_Cell @ 0x006574C3」应改为 `Plot_Cell(0x00655C50) 内部 0x00655D38` |
| **P0-2** | `docs/re/ARCHITECTURE_ATLAS.md:99`、:1886` | `R6["雷达小地图主循环覆写 (0x006574C3 + 0x0065719A)"]` ／ `- 雷达小地图工作表面与地形缓存覆写 (RadarClass::Plot_Cell @ 0x006574C3)` | `R6["雷达小地图绘制代理覆写 (Plot_Cell 内部 0x00655D38 + 0x0065719A)"]` ／ `- 雷达小地图工作表面与地形缓存覆写 (RadarClass::Plot_Cell 0x00655C50 内 0x00655D38 下沉代理)` | 同 P0-1 | 低（纯文字） |
| **P0-3** | `docs/re/HOOK_POINT_MATRIX.md:314`（连带 :150/:303/:357/:358） | `> 1. **裁定 0x006574C3（调用点覆写）+ 0x0065719A（跳帧抑制）为小地图唯一合法落地实现**。` | 追加勘误块（**不要原地改写**）：`> **[路线 A 后订正 · 2026-09-27]** 现网安装点为 Plot_Cell 内部 0x00655D38（9B）+ 0x0065719A；0x006574C3 仅存 ADDR_RADAR_PLOT_CALLSITE 死宏。原「唯一合法实现=0x006574C3」的裁决由本订正取代；0x00655F48 废弃结论不变。` | 源码 + `hook_gate_gap_table.md:107`（明示死宏） | 中。文内含「裁决」字样，直接改写会抹掉审计痕迹 ⇒ **必须勘误块** |
| **P0-4** | `docs/re/INSTALLED_HOOKS_AUDIT.md:67-69`、:150`、:162`、:262` | :150`「…**禁止** ｜ 节流键 (ptr>>4 + CurrentFrame) % interval 含**指针位移**（:404-407, :463-466）…」`；:262`「**联机唯一硬红灯**：#7/#8（+#9 联用）节流哈希含指针位移…任何联机构建必须 TargetScanInterval=1 或改用 CurrentFrame 纯函数轮转」` | 在 §2.2 表下加勘误块：`> **[缺陷2 修复后订正 · 2026-09-27]** 三处节流键已收敛为 ThrottleKey()（:167-184），默认 TargetScanKey=position ⇒ #7/#8/#9 默认键下由「禁止/VIOLATION」降为 **RISK（待对拍）**；**TargetScanKey=pointer 分支仍为 VIOLATION**。旧行号 :404/:425/:463 已移植为 :436/:457/:495（快照 A），快照 B 再平移为 :534/:556/:595，`ThrottleKey()` 由 :167-184 移至 :264-282。` | 源码快照 A `:167-184/:436/:457/:495/:91-92`、快照 B `:264-282/:534/:556/:595/:169-171`、`ra2render.ini:49`（快照 B :51）；`hook_gate_gap_table.md:36` | 低。注意本文件其余「装了但没生效」10 条候选结论与本文无关，**勿连带改** |
| **P0-5** | `docs/re/MP_SAFETY_REVIEW.md:445`（§8 附录「维持不变的结论」行），连带 :19/:53/:63/:73/:269-271` | :445`「**维持不变的结论**：§0 判定（VIOLATION×3 = #7/#8/#9…）、§3.1 的 >>4 指针哈希推导…**全部维持**」` | 在 §8 勘误表**追加一行**（:444 已声明「不改动正文」，故只追加）：`序号 §0 L19 / §2.1 L53,L63,L73 / §5 L269-271 ｜ 本文口径 VIOLATION×3（指针哈希） ｜ **订正（时点差）**：本文基于 17:18 构建；现网 18:42 构建已改用 ThrottleKey() 且默认 position ⇒ 默认键下 RISK；pointer 分支维持 VIOLATION。§3.1 的 >>4 推导仅对 pointer 分支仍成立。§4.1「TargetScanInterval=1 即解除唯一硬违规」仍成立且更强（默认键已非硬违规）` | 源码 mtime 18:42:48 晚于本文引用的 17:18 构建；`hook_gate_gap_table.md §0` 已列出该时点差 | 低。该文既有纪律为「只追加不改正文」（:444），须遵守 |
| **P0-6** | `docs/re/mp_release_safety_checklist.md:63`（MP-G02 行） | `\| **MP-G02** \| TargetScanKey 联机回退指针键 \| 默认 position，但允许配 pointer \| **VIOLATION**(指针地址随机化必分叉) \| …` | 「MP 风险判定」列改为 `**RISK**（默认 position 下确定性；仅当单端误配 pointer 才 VIOLATION）`，同格补 `**[落地状态]** 快照 A（09-26 18:42）：现网无 MpActive() 检测（grep 0 命中）⇒ R-02 未实现；快照 B（09-27 09:06）：已落地（MpActive()+GetEffectiveTargetScanKey 联机强制 position）；残留面=单端误配 + 检测失败` | 源码双快照对比（见 §0.0）；`hook_gate_gap_table.md:36`；`docs/RE_COORDINATION.md:648` | 中。**不要把 R-02 的 P0 优先级一并降级**：判定降级 ≠ 落地缺口消失（快照 B 后才可议降级） |
| **P0-7** | `docs/re/mp_release_safety_checklist.md:62`（MP-G01 行「现网状态」列） | `\| API 默认 1；<br>INI 现值 0 \| **VIOLATION**（配置缺失风险） \|` | （双快照，二者必居其一并按 Lead 冻结时点定稿）：`\| API 默认 0（快照 B :182；快照 A 为 1 @ :103）；<br>INI 现值 0（快照 B ra2render.ini:46，MD5 0B239E60…） \| **VIOLATION**（键缺失/漏配即静默全开） \|` | 实测：快照 A `EnableMinimapFog=1` @ ini:45（MD5 `190709D0…`，2,747 B）；**快照 B `=0` @ ini:46（MD5 `0B239E60…`，2,996 B）且 API 默认已改 0（R-01 落地）**；F-11 已把缺口重述为「键缺失即静默全开」（`hook_gate_gap_table.md:38/:276`） | 低。**注意**：本项在快照 B 下「INI 现值 0」重新成立（行号 44→46），但 F-11 勘误「现值 1 / 行 45」反而变成过期陈述 ⇒ 见 P1-12 |
| **P0-8** | `REVERSE_ENGINEERING_AND_PATCHES.md §七:245-246`（**只读红线：仅报告，改否由 Lead 裁定**） | `\| 裂缝保护热补丁 2 \| 0x00577EC5 \| 89 91 34 01 00 00 \| …` ／ `\| 裂缝保护热补丁 3 \| 0x00577B60 \| 89 91 34 01 00 00 \| …` | 改为 `89 B8 34 01 00 00`（补丁 2，`mov [eax+0x134], edi`）与 `89 98 34 01 00 00`（补丁 3，`mov [eax+0x134], ebx`） | 实测字节（`claims.txt` PART 3）+ `anchor_claims.txt:68-69` + 全库 48 份文档一致 | 低。按错字节写补丁会**拆错指令边界**（`z3_troubleshoot_net_fix_gap.md:66` 已列为可能原因之一） |
| **P0-9** | `REVERSE_ENGINEERING_AND_PATCHES.md §七:211-216` 与 §2.2:56-61`（**只读红线：仅报告**） | `\| **L1 Blitter** \| 0x007F1BE4 \| 0x00494B60 \| …`（等 6 行；§2.2 为虚表基址 0x007F1BE0 等） | 槽位改为 `0x007E56F0(+4)` / `0x007E5A20(+4)` / `0x007E55C0(+4)` / `0x007F7BF4(+4)` / `0x007E59F0(+4)` / `0x007F7BC4(+4)`；§2.2 同为基址 `0x007E56F0` 等 | dword 复算 + 真实槽位反查（`claims.txt` PART 4）；`telemetry_and_switches_spec.md:215` C-2 独立同结论 | 中。台账是唯一速查入口 ⇒ 建议 Lead 先跑 §7 门禁再改；注意 v1.5.7 行（L540-544）已正确，勿反向覆盖 |
| **P0-10** | `docs/re/deep_dive_sweeps_closure.md:378`（连带 :528 表 #23） | `严禁使用 IsBadReadPtr 进行游戏状态分支判定。现网代码已全面移出控制流，由引擎单例池与对象生命期指针边界做静态门控。` | `严格遵守：改用实体活跃状态（IsInPlay / Health>0 / InLimbo==0）做门控，**禁止**让 OS 页属性参与控制流。**现状核对（双快照）：快照 A 有 17 处 IsBadReadPtr（:171/:435/:456/:487/:489/:494 参与节流/短路控制流）；快照 B 有 19 处（:269/:533/:555/:587/:589/:594 参与控制流）⇒ 本项为「规格已定、代码未落地」**，不得记为「已清零」。` | 源码逐行（真值）；`MP_SAFETY_REVIEW.md:100/122/410` 亦只列为「建议移出」 | 低，但会**撤销**一条已被引用的「风险清零」结论 ⇒ 须同步 :528 表 #23 处置状态列 |

### P1 · 口径矛盾（12 项）

| 编号 | 目标 文件:行 | 改前原文（摘） | 改后文本（建议） | 理由 | 风险 |
|:--:|---|---|---|---|---|
| **P1-1** | `docs/re/re_sprint_S18_report.md:18` | `评定置信度：**89 项达到 [极高] 置信度**（占比 96.7%），**3 项达到 [高] 置信度**（占比 3.3%），**0 项存在逻辑盲区或未闭环漏洞**。` | **先裁定再改**（见 §6 U-1）。保守写法：`评定置信度：逐项矩阵（offline_verification_alternatives.md §6）实测 **83 项 [极高] / 9 项 [高]**；本报告 §3 汇总表口径为 **91 / 1**；差异待裁定。` | 机读：§6 矩阵 92 行 = 83 极高 + 9 高；而 §1:95-100、§7.3:1948、本报告 :18/:95/:107 与之互不相同 | 高。属「数字真值」问题，改任一侧都会改写证据文档 ⇒ **必须先裁定** |
| **P1-2** | `docs/re/offline_verification_alternatives.md:1948`（§7.3） | `- 92 项运行时未决中，**89 项 [极高] 置信度**（占比 96.7%），**3 项 [高] 置信度**（占比 3.3%）…` | 同 P1-1 裁定的结果；若裁定「以 §6 矩阵为准」则改为 `83 / 9` 并注明「统计口径 = §6 逐项矩阵」 | 同 P1-1 | 高（同） |
| **P1-3** | `docs/re/offline_verification_alternatives.md:95-100`（§1 汇总表） | `\| **Sub-1** \| 渲染与微内核族 \| B-R01 ~ B-R32 \| **32 项** \| … \| 极高 (96.8%) \|` | 同裁定；若以矩阵为准应改为 `极高 (84.4%)（27/32）`，并同步「合计」行的 `极高` 描述 | 矩阵实测 Sub-1 = 27 极高 / 5 高（B-R01/R10/R11/R18/R27） | 高（同） |
| **P1-4** | `docs/re/re_sprint_S20_report.md:67`（汇总行） | `\| **全量汇总** \| **35** \| **23** \| **1** \| **11** \| **100%** \|` | `\| **全量汇总** \| **35** \| **25** \| **1** \| **9** \| **100%** \|`（= 上方 5 行逐行求和）；**或**按 `deep_dive_sweeps_closure §6` 改为 `29 / 1 / 5`；二者择一由 Lead 裁定 | 机读：明细 5 行求和 = 25/1/9；档案 §6 总表 = 29/1/5；现汇总行 23/1/11 与**任一侧**都不符 | 中。仅改汇总行可让表内自洽，但仍与上游档案冲突 ⇒ 建议同时声明「以 §6 为准」 |
| **P1-5** | `docs/re/re_sprint_S20_report.md:54-55` | `│     23 项        │     │       3 项       │     │       9 项       │`（及 :55 的 `(65.7%) (8.6%) (25.7%)`） | 按 P1-4 的裁定同步：`25 / 1 / 9`（本报告明细口径）或 `29 / 1 / 5`（§6 口径），百分比同步重算 | 同 P1-4；图示现与 §0.1 一致但与两处表格都不一致 | 中。分母 35 不变 |
| **P1-6** | `docs/re/deep_dive_sweeps_closure.md:34`（§0.1 图示）及 :38/:40/:42 | `│     23 项        │     │       3 项       │     │       9 项       │`；`1. **A 类…（共 23 项）**`；`2. **B 类…（共 3 项）**`；`3. **C 类…（共 9 项）**` | 按 §6 总表逐行实测改为 `**A 类 29 项 / B 类 1 项 / C 类 5 项**`，并在 §0.1 注明「统计口径 = §6 总表逐行分类」 | 机读 §6（35 行）分类 = 29/1/5；与 §0.1 的 23/3/9 **三项全错** | 中。会连带推翻 S20 图示（P1-5）；若 Lead 反以 §0.1 为准，则须改 §6 的 6 行分类标记（清单已备） |
| **P1-7** | `docs/re/deep_dive_sweeps_closure.md:284` | `### 2.4 Item T-4：现网 L2 Hook 与 Target Retention 联机安全闭环 [实证]` | `### 2.4 Item T-5：现网 L2 Hook 与 Target Retention 联机安全闭环 [实证]`，并在 §6 表 #11 旁注「T-4/T-6 的论据见归档条目」 | §6 表 #12 即 `T-5 = Target Retention`；#11 `T-4 = 三路寻敌枚举` 在 §2 无专节 | 低（标题编号）；会改变「条目覆盖完整性」读法 ⇒ 建议同时补 T-4/T-6 指针行 |
| **P1-8** | `docs/re/hook_gate_gap_table.md:102`、:129` | :102`…API=**1** :103-104；ini=**0** :44…`；:129`\| **EnableMinimapFog** \| **1** :103-104 \| **0** :44 \|…` | 采用与本文件 :38 相同的**就地订正 + 原文对照**写法：`ini=**1** :45（现值；:44 为注释行）`，或至少加 `※见附注 1（F-11 订正：现值 1 / 行 45）` | `附录:276` 只声明正文 `L38` / `L129` 两处陈旧，**漏了 :102**（第三处）；:38 已就地订正，:102/:129 未订正 | 低。本文件惯例是「正文保留原文 + 附录说明」⇒ 二选一须与 Lead 口径一致，**不要一边就地改一边留旧附录** |
| **P1-9** | `docs/re/ARCHITECTURE_ATLAS.md:1530`（§9.4 标题） | `### 9.4 G-01 ~ G-09 联机安全门控矩阵总览 [实证]` | `### 9.4 G-01 ~ G-09 联机安全门控矩阵总览（G-10 为死代码/死键卫生项，裁定见 hook_gate_gap_table.md §5）[实证]` | `hook_gate_gap_table.md:244` 记「G-01～G-10 全量」，:272` 有 G-10 裁定 | 低（纯范围声明） |
| **P1-10** | `docs/re/telemetry_and_switches_spec.md:214`（C-1 行） | `\| C-1 \| **双份 ini 内容一致但行尾不一致**：ra2render/ra2render.ini 为 LF，ra2youli/ra2render.ini 为 CRLF；去 CR 后 diff 为空 \|…` | 该行加注：`**[已消解 · 2026-09-27 复核]** 两文件现 MD5 全同 190709D025C133757142062F996E0ED6（2,747 B，49 行逐行相同）⇒ 行尾差异不存在` | 本次实测 MD5 / 行数 / 逐行比对 | 低 |
| **P1-11** | `docs/re/open_items_sweep.md:41`、:166` | `下列 92 项条目在原理和静态汇编层面…`；`下表汇总原文档中因历史未决标记残留，但已由 S1–S15…给出 [实证] 的 164 处条目` | `下列 92 项中**摘录 12 项**（全量矩阵见 offline_verification_alternatives.md §6）`；`下表汇总…**共 164 条，本表列示 33 条代表条目**` | 表行数实测 12 / 33 | 低（措辞）；可防止后续审计误以为「表即全量」 |

| **P1-12** | `docs/re/hook_gate_gap_table.md:38`（F-11 就地订正行）与 :129 | :38`「**【F-11 正文级订正 · Lead · 2026-09-27】** 改前证据已过期：`ra2render.ini:45` 现值实为 `EnableMinimapFog=1`（双副本一致，Lead 实测）；缺口应重述为「**键缺失即静默全开**」（API 默认 1）」` | 重述为：**【F-11 二次订正 · 2026-09-27 09:06 后】** 该订正本身已成为过期陈述：`ra2render.ini:46` 现值已改为 `EnableMinimapFog=0`（MD5 `0B239E60…`，2,996 B），且 API 默认值已改为 `0`（`blitter_hooks.cpp:182`，R-01 落地）⇒ G-01 缺口收敛为「**API 默认 0 + ini 0；仅当显式配 1 才开启**」；R-01 由 P0 转为「已落地/待验收」 | 快照 B 实测（ini:46 / 源码 :182 / `g_enableMinimapFog = false` @ :16） | 中。**这是「订正被订正」**：若只在快照 A 时点执行订正，会立刻造出新的过期结论 ⇒ 必须先冻结写入（见 §0.0） |

### P2 · 文档卫生（7 项）

| 编号 | 目标 文件:行 | 改前原文（摘） | 改后文本（建议） | 理由 | 风险 |
|:--:|---|---|---|---|---|
| **P2-1** | `docs/re/particle_fog_owner_evidence.md:5` | `（MD5: 1011CE1B58C9B9BA..., PE 32-bit x86）` | `（MD5: 4f37486e5b0dbe2ae5f45aeee0f98367，4,825,360 B，官方 1.001）`；如需留痕附注：`〔原文误记 1011CE1B58C9B9BA…，经复核为取证机另一镜像；本文结论不受影响〕` | 二进制实测 MD5；`docs/RE_COORDINATION.md:1039` 已登记待修 | 低。**须同时处理 P2-2** |
| **P2-2** | `docs/re/landing_pack_particle.md:40` | `> **警告**：particle_fog_owner_evidence.md 头部记 MD5 1011CE1B58C9B9BA... （截断/可能过期）。**以本轮实测 MD5 为准**；…` | 保留警告但补时点：`> **警告（2026-09-26 时点）**：…（该头部已于 2026-09-27 订正为 4f37486e…；本条保留为审计痕迹）` | 与 P2-1 联动 | 低 |
| **P2-3** | `docs/re/open_items_sweep.md:201` | `\| blitter_microkernel.md \| §8 \| 30 变体 this 布局与 ZRead 边界 \| **S13** \|…` | `\| blitter_microkernel_deep_dive.md \| §8 \|…` | 机读引用存在性：`blitter_microkernel.md` **不存在** | 低 |
| **P2-4** | 13 处 `## N. 未决问题` 标题（清单见 §1-⑤） | 例：`docs/re/superweapon_re.md:606「## 7. 未决问题（不确定标「待实测」）」` | 按 `open_items_sweep.md §4` 执行：改为 `## 7. 历史未决问题（已于专项冲刺 S2 终局闭环）` 等，并在段首加闭环报告指针 | §4 指令 **0 执行**（全库 `历史未决问题` 仅命中指令文本自身） | 低但**量大（13 文件）**：建议只加「闭环指针 + 标题后缀」，**不删原表**，保历史可追溯 |
| **P2-5** | `docs/RE_COORDINATION.md`（43 处 `out/loadbench/PROTOCOL.md` 引用）等 | `- out/loadbench/PROTOCOL.md …` | 加注「（该路径实测不存在；PROTOCOL.md 未交付/已清理）」或改指 `docs/re/EVIDENCE_STANDARD.md` | 实测 `out/loadbench` 存在但 `PROTOCOL.md` **不存在**（`candidates_missing_ref.md`） | 低 |
| **P2-6** | `docs/RE_COORDINATION.md:1040` | `…docs/re/INSTALLED_HOOKS_AUDIT.md(17:46) 与 mp_release_safety_checklist.md 判 **VIOLATION 的 #7/#8/#9「指针哈希 desync」**…` | `…INSTALLED_HOOKS_AUDIT.md(17:46) 与 **MP_SAFETY_REVIEW.md** 判 VIOLATION 的 #7/#8/#9…（mp_release_safety_checklist.md 侧对应 **MP-G02/MP-G08**）…` | 事实：#7/#8/#9 表体在 `MP_SAFETY_REVIEW.md`（:19/:269-271），checklist 无该编号表 | 低，但**重要**：否则 Lead 会去 checklist 找不存在的行 |
| **P2-7** | 派工单口径（非文档内） | `docs/re/ 下 88 份 md` / 全库 `146 份 md` | 记录本次实测：`docs/re` **89**、`docs/re/dispatch` 51、顶层 7、全库 **147**（本文件落地后 148） | `Get-ChildItem -Recurse -Filter *.md docs` 计数 | 低（仅口径记录，防后续「全量扫描」漏 1 份） |

---
## 5. 影响面与「最小性」说明

1. **不触碰二进制与源码**：全部订正均为文档文字/数字；P0-8/P0-9 涉及顶层台账（红线只读），本清单只给建议文本，**是否写入由 Lead 决定**。
2. **坚持「证据/裁决文档不改正文」**：`MP_SAFETY_REVIEW.md`、`deep_dive_sweeps_closure.md`、`HOOK_POINT_MATRIX.md` 均承载审计痕迹 ⇒ 建议一律**追加勘误块**（与 `MP_SAFETY_REVIEW.md §8`、`hook_gate_gap_table.md` 附录一致）。
3. **P0 与 P1 的分界**：P0 = 读者照该文行动会做错事（挂错钩子点、按错字节写补丁、误以为风险已清零、去错文件找条目）；P1 = 数字/编号对不上但行动不会错。
4. **未做（明确边界）**：未反汇编 `ra2youli/ra2render.dll` 以确认运行时补丁站点（见 U-2）；未对 S18/S20 的数字做「真值裁决」（见 U-1）——两者超出静态文档审计的可判定范围。

---

## 6. 未闭环项（无法判定 / 需裁定）

| 编号 | 未闭环事项 | 原因（为什么静态手段不够） | 下一步取证方法 |
|:--:|---|---|---|
| **U-1** | S18 置信度真值（89/3 vs 91/1 vs **83/9**） | 属「逐项数据」与「多处汇总」的互斥；机械手段只能证实互斥，**无法判定作者原意**（且 9 行「高」是否笔误需作者确认） | 由 Lead 裁定唯一口径；若选「矩阵为准」，逐条复核 §1-③ 所列 9 行；复算脚本 `out/re_work/doc_audit/verify_specific2.py` |
| **U-2** | `ra2render.dll` 运行时是否仍残留 `0x006574C3` 补丁 | 本任务只读 `docs/**` 与 `ra2render` 源码，**未反汇编已构建的 `ra2youli/ra2render.dll`**（128,512 B，MD5 `3BAD50FB7798521EA0DDF1311A8434DC`） | 用 `pefile` + `capstone` 全量扫描该 DLL 的常量与 `rel32` 基准（`routeA_implementation_audit.md` 已给出 6 条指令 RVA 的检索方法），或真机内存 dump |
| **U-3** | ~~R-01/R-02/R-03 未落地~~ → **已结案（快照 B）** | 快照 A：无 `MpActive()`（0 命中）⇒ 未落地；**快照 B（09-27 09:06:28）：已落地** —— `MpActive()`（`:58-80`，读 `0x00A8D5F8 & 0x02`）+ `GetEffectiveTargetScanInterval()`（`:82-87`，联机→1）+ `GetEffectiveTargetScanKey()`（`:89-94`，联机→position）+ `GetEffectiveMinimapFog()`（`:96-106`，联机→false）+ API 默认改 0（`:182`）+ ini `EnableMinimapFog=0`（:46） | **残留**：仍属 `[待实测]`（无真机验收）；须由 ZCode 出「联机 INI 写 pointer → 日志红字 + 生效 position」的实测证据（`mp_release_safety_checklist.md:63` 的验收方法即此） |
| **U-4** | `0x00577EC5` / `0x00577B60` 台账字节错的成因（简写还是抄错） | 两行连寄存器都写成 `ecx`（`89 91`），而全库正确写法为 `edi` / `ebx`；成因不可由现状反推 | 检索 `out/re_work/re_sprint/S1`、`S12` 早期探针输出中是否曾出现 `89 91` 形态；无则判「笔误」 |
| **U-5** | `open_items_sweep.md` 的 92 项 B 类是否有「全量枚举表」在别处 | 本表 12 行 + 上游 92 项描述；`offline_verification_alternatives.md §6` 有 92 行逐项矩阵（本次已核 B-R/A/N/L/M 五族 92 个编号**无缺号**）⇒ 很可能只是未指向它 | 交叉确认 §6 的 92 行编号与 S16 原始 92 项是否一一对应（编号连续性已核） |
| **U-6** | `B-R01` 等 9 行「高」是否属「渲染族 5 项」的有意降级 | `re_sprint_S18_report.md:90` 把渲染族写为 31 极高 / 1 高，与矩阵的 27/5 冲突；两种都可能是有意为之 | 需 S18 作者 / Lead 确认；证据已备（9 行行号 + 单元格原文） |

---

## 7. 改动文件 + 门禁输出

### 7.1 本次改动（严格遵守写作用域）

| 路径 | 操作 | 说明 |
|---|---|---|
| `docs/re/doc_consistency_fix_list.md` | **新建** | 本清单（唯一新文档） |
| `out/re_work/doc_audit/` | **新建目录** | 10 个脚本 + 5 张候选表/JSON + `claims.txt` + 门禁输出 + `README.md` |

**未改动**：`gamemd.exe`（只读，mtime 仍为 2026-09-25 16:10:48）、`ra2render/**`（其 mtime 变化来自**其他会话**，非本任务 —— 见 §0.0/N-11）、`REVERSE_ENGINEERING_AND_PATCHES.md`、其余 `docs/re/*.md`、`ra2youli/**`、`YRpp/**`、`tools/**`。

**只读留证**：本任务的全部写入仅两处 —— 本文件与 `out/re_work/doc_audit/**`；其余 mtime 变化经 §0.0 三元组（mtime+尺寸+MD5）归因于并行会话。

### 7.2 门禁 1：`python tools/verify_anchors.py`（实跑原文）

```text
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
```

### 7.3 门禁 2：`python tools/audit_bytes.py out/re_work/doc_audit/claims.txt`（实跑原文，尾部）

```text
合计 26 条：OK=26  MISMATCH/NOREAD=0
```

**26 条断言的覆盖面**（全部 OK；逐条原文见 `out/re_work/doc_audit/gate_audit_bytes.txt`）：

- 雷达挂钩组（P0-1 / P0-2 / P0-3 依据）：`0x00655D38`、`0x006574C3`、`0x0065719A`、`0x00655C50`
- L2 节流组（P0-4 / P0-5 / P0-6 依据）：`0x006F8DF0`、`0x00647260`
- 台账订正组（P0-8 / P0-9 依据）：`0x00568273`、`0x00577EC5`、`0x00577B60`、`0x007F1BE4`（实测 `3E FF FF FF` = `0xFFFFFF3E`，**非有效槽位**）
- 其余交叉核对锚点：`0x006D3D99`、`0x007C8E17`、`0x007C8B3D`、`0x00750920`、`0x007509E0`、`0x0047F40F`、`0x0047F4AE`、`0x0062CF5F`、`0x0055DE73` + 8 个虚表槽 dword

> **一致性交叉核对（机械判据）**：若把 `0x00577EC5` / `0x00577B60` 两行按**台账现文**的字节（`89 91 34 01 00 00`）写入 `claims.txt`，`audit_bytes.py` 会直接报 MISMATCH —— 这正是 P0-8 的机械判据；`0x007F1BE4` 一行实测 `3E FF FF FF` 则给出 P0-9 的机械判据。

---

*DOCAUDIT 交付 · 2026-09-27 · 只读审计；未修改任何既有文档与二进制；全部判定可由 §7 两道门禁与 `out/re_work/doc_audit/` 脚本复算。*
