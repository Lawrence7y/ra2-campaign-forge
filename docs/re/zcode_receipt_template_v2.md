# ZCode 统一回执模板 v2（R-RECEIPT-V2）

> **任务号**：`R-RECEIPT-V2` · **性质**：回执格式统一（非规格变更、非落地动作）
> **产出**：本文（`docs/re/zcode_receipt_template_v2.md`）+ `out/re_work/re_sprint/R_receipt_v2/**`
> **上游依据（只读汇总）**：`out/re_work/zcode_live/**/RESULT_*.md` 实际字段 · `docs/re/AGENT_DELIVERY_FORMAT.md` §A · `docs/re/dual_track_status_note.md` §3.3 · `out/re_work/re_sprint/R_b5_detail|_hd_card|_h20c_card/receipt_template.md` · landing_pack「交付回执」节
> **替代关系**：v2 为**新卡统一骨架**；既有 `receipt_template.md`（B5/HD/H20C）与各卡 RESULT 不改历史，新波次按本模板填写。
> **写作用域（本任务）**：仅 `out/re_work/re_sprint/R_receipt_v2/**` 与 `docs/re/zcode_receipt_template_v2.md`。**禁写**台账/看板/landing_pack/`ra2render/**`/`zcode_live` 证据树。

---

## 0. 一句话

一张回执必须同时给出 **七轨字段**（轨名 / 字节 / 门 / 验收 / 还原 sha256 / 未测原因 / 越界自查），缺任一轨判交付不合格；状态词**必须带轨名**，禁用单轨含混「已落地」。

---

## 1. 七轨字段（强制列，缺节即不合格）

| # | 轨名 | 必填内容 | 禁止写法 | 来源字段（RESULT 实况） |
|---|---|---|---|---|
| T1 | **轨名** | 双轨状态分列：纸面规格 / 二进制轨 / 代码轨；执行方、任务卡、主路径轨（R/L/C/S） | 无轨名「已落地/已实现/已修复」 | `[META] task/executor` · `dual_track §3.3` |
| T2 | **字节** | 每点：VA + FileOffset + 原字节 + 目标字节 + 长度等长 + 上下文/邻窗 before→after | 只写「已 NOP」不给 hex | `Q1 first byte before` · `bytes after @VA` · `context/neighbor` |
| T3 | **门** | G0.x 静态门逐条 PASS/FAIL；Q1 首字节分类（未打/外部已打/其它拒）；键门默认 0；MpActive 门 | 「门禁都过了」无原文 | `G0.1–G0.x` · `Q1` · `Enable*=默认0` · `forced-off-mp` |
| T4 | **验收** | A1..An 每项 PASS/FAIL/部分/转轨/未测 + 证据路径 + 证据等级（[实证]/[推演]/[待实测]/[实现]） | 未测项混入 PASS 行 | `A1..An` · `[1] 逐条必答项结论表` |
| T5 | **还原 sha256** | 收尾还原对照：ini/地图/DLL/游戏目录逐项 sha256（或 MD5）与接手/基线/MANIFEST 对拍；`--verify` 计数 | 「已还原」无哈希 | `[5] 还原对照` · `rollback tested` · `bench_map_verify` |
| T6 | **未测原因** | 每条未测/部分/转轨：为何未测 + 可直接执行的下一步 + 阻塞级别 P0/P1/P2 | 「时间不够」单独成句 | `[3] 未完成项` · `[4] 未闭环清单` |
| T7 | **越界自查** | 写入清单（路径+说明）/ 未触碰清单 / 例外声明 / 与 `scope_declared` 对拍 | 「未越界」无清单 | `[5] 写作用域合规声明` · `scope_declared` |

---

## 2. 回执骨架（填写顺序固定；§A 十节 + RESULT 紧凑块 + 七轨表）

```markdown
# RESULT_<卡号> —— <一句话标题>

> 任务卡：<landing_pack 或 dispatch 路径> · 优先级：<P0/P1/P2>
> 执行方：<ZCode|…> · 工作区：<路径> · 游戏目录：<ra2bench|ra2youli|…>
> 待验收件（接手核验）：<文件> = <字节数> B / <MD5|sha256>
> 对照旧件/基线：<路径> = <…> ✔

## 双轨状态【T1 轨名】
纸面规格：已定谳 | 待定 · <landing_pack 路径>
二进制轨（zcode_live / 进程内补丁）：已落地 | 就绪 | 待批 | n/a · <RESULT 路径>
代码轨（ra2render 源码）：已落地 | 未落地（grep N 命中）| 已勘误 | n/a · <grep/头文件/日志依据>
主路径轨：Track-C 复算 → Track-L 安装 → Track-S 回执（写明本卡实际走了哪几步）
混称检查：未出现无轨名「已落地」；未用二进制收据证明代码轨（或反向）

```
[META]
task=<任务号>  executor=<执行方/会话ID>  elapsed=<实际分钟（名义预算）>  mode=accept-edits|read-only
scope_declared=<提示词给定写作用域原文>
```

### RESULT 紧凑块（机器可读；字段并集见 §3，无值写 `n/a` 或 `未测`+T6）
```
<卡号> RESULT
- build/sha256: ra2render.dll sha256 <…>；gamemd.exe sha256 <…>（跑前跑后一致 y/n）
- install path: (ra2render hook | external patcher | 仅测量不装)
- 开关/键态: <Key>=默认0 / A2 显式=1（改后还原 y/n）；<其他键…>
- G0.x 门: 全 PASS | <哪条 FAIL>（附原文/JSON 路径）
- Q1 first byte before @<VA…>: <hex…>（=未打 | 90/=外部已打停手 | 其它=拒）
- bytes after @<VA…>: <hex…>（长度等长 L==L）
- context/neighbor unchanged: y/n（@VA=hex …）
- A1..An: A1 PASS / A2 PASS / A3 <PASS|部分|未测|转轨> / …（路径见验收表）
- 未测原因: <项>=<原因>→<下一步>·P<级>；…
- except.txt: empty | path（非空附内容/隔离说明）
- rollback tested: y/n（顺序：<逆序链>；还原 hex <…>）
- 还原 sha256: ini <…>=基线✔ | 地图 <…>=MANIFEST✔ | dll <…> | 目录 verify <n>/<n>
- 越界自查: 写 <路径…>；未触 <…>；例外 <…>；= scope_declared ✔|偏差已声明
- MP / 红线: single|dual；G-R1..R7 触碰=无|<哪条>；禁写「MP 可发布」
```

## [0] 结论摘要（≤7 行，可独立读懂）
1. …

## [1] 逐条必答项结论表【T4 验收】
| 段/项 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|
证据等级只用：[实证] / [推演] / [待实测] / [实现] / [阻塞·转轨]
锚点必须 文件:行 或 VA+hex，禁止只写「见文档」

## [2] 关键证据块【T2 字节】
每条：VA / FileOffset / 原始字节 / 目标字节 / 反汇编（如适用）/ 上下文窗 / xref
claims 机读：`0xVA = HEXBYTES # 注释` → tools/audit_bytes.py

## [3] 勘误（无则显式「无勘误」）
| 目标文件:位置 | 改前 | 改后 | 理由 | 影响面 |

## [4] 未闭环 / 未测【T6】
| 缺口 | 为何未测/未闭环 | 下一步（可直接执行） | 阻塞 P0/P1/P2 |

## [5] 写作用域合规 + 还原对照【T5 + T7】
### 5.1 改动/写入清单
| 路径 | 说明 | 字节/哈希 |
### 5.2 未触碰清单
`ra2render/**`（若非本卡写者）、台账、看板、他人 docs、`.mix`、gamemd.exe（只读证明）
### 5.3 还原对照（必答：目标 ini/地图/DLL 是否已还原）
| 对象 | 接手/基线 sha256 | 收尾 sha256 | 一致 |
### 5.4 例外声明（槽位置换/工具日志/运行期残留等）
### 5.5 越界自查结论
与 `scope_declared` 对拍：一致 ✔ | 偏差已在 5.1/5.4 声明

## [6] 门禁实跑输出（原文粘贴，不许概述）【T3 门】
python tools/verify_anchors.py → 323/323
python tools/audit_bytes.py <claims.txt> → 全 OK
（卡内 verify_*.py / bench_map_install --verify / 其它）
无法运行时：说明原因 + 等效替代证据，不得静默跳过

## [7] 风险与红线提示
显式回答：①同步/命令序 ②PRNG 消费序 ③存档结构 ④渲染像素等价性
触及者写「需要 MP 门控矩阵/真机对拍」；禁止「零风险/零 Desync/MP 可发布」

## [8] 交付物清单
| 类别 | 路径 | 数量/行数/大小 |

## [9] 待裁决项
| # | 分叉 | 建议 | 理由 |
```

---

## 3. RESULT 紧凑块字段并集（来自 15 份 RESULT_*.md 实况）

| 字段键 | 必填 | 出现于 | 说明 |
|---|---|---|---|
| `build/sha256` | 是 | 全部 | DLL + gamemd 双哈希；跑前跑后一致 |
| `install path` | 是 | 补丁卡 | `ra2render hook` / `external patcher` / 仅测量 |
| `开关/键态` | 有键则必填 | gap/vxl/sw/h20c/hd | 默认 0 + A2 显式 1 + 收尾还原 |
| `G0.x 门` | 是 | 补丁卡 | 静态窗 MATCH；失败即停 |
| `Q1 first byte before` | 装补丁必填 | gap/vxl/sw | 未打/外部已打/其它拒 三分类 |
| `bytes after @VA` | 是 | 补丁卡 | 目标 hex + 等长 |
| `context/neighbor unchanged` | 建议 | vxl/sw/gap | 守卫窗零改动 |
| `A1..An` | 是 | 全部 | 逐项状态 + 证据 |
| `telemetry` | 有遥测则填 | vxl/sw/gap/zc10+ | 计数非零才可称生效 |
| `except.txt` | 是 | 全部 | empty/path；崩溃一票否决 |
| `rollback tested` | 改字节/ini 必填 | 补丁卡+测量卡 | y/n + 逆序链 + 还原 hex |
| `还原 sha256` | 是 | 全部 | v2 **升为独立必填键**（原散落 [5]/环境收尾） |
| `未测原因` | 有未测必填 | 全部 | v2 **升为独立必填键**（原散落 [3]/未完成项） |
| `越界自查` | 是 | 全部 | v2 **升为独立必填键**（原 [5] 声明） |
| `MP / 红线` | 是 | 全部 | G-R1..R7；禁「MP 可发布」 |
| `same-install / split-install` | 多点补丁 | gap_p223 | 安装模式 |
| `L-SW-2 applied` 等附录键 | 视卡 | sw 等 | 可选步骤显式 y/n |

**证据等级词表（全文统一）**：`[实证]` `[推演]` `[待实测]` `[实现]` `[阻塞·转轨]`
**验收状态词**：`PASS` / `FAIL` / `部分` / `未测` / `转轨` / `blocked`
**回执状态（卡级）**：`pass` / `fail` / `blocked` / `partial`

---

## 4. 七轨填写示例（对照用，非实测）

```markdown
## 双轨状态【T1】
纸面规格：已定谳 · docs/re/landing_pack_xxx.md
二进制轨：已落地 · out/re_work/zcode_live/xxx/RESULT_XXX.md（B1–B5）
代码轨：未落地（grep 0 命中）· ra2render 无 VA 三点
主路径轨：C MATCH → L A1/A2 → S 本回执

### RESULT 紧凑块（摘录）
- bytes after @0x00577EC5: 90 90 90 90 90 90（原 89 B8 34 01 00 00，6==6）
- G0.x 门: 全 PASS（g0_static_bytes.json）
- Q1 first byte before @0x00577EC5: 89（=未打）
- A1..A5: A1 PASS / A2 PASS / A3 未测 / A4 未测 / A5 未测
- 未测原因: A3/A4=遭遇战无预置建筑→另卡战役轨·P1；A5=联机对拍轨未开·P1
- 还原 sha256: ra2render.ini b8bb8238…993c = 接手快照✔；gamemd 73201cc0…F67476=基线✔
- 越界自查: 写 out/re_work/zcode_live/xxx/** + ini 副本；未触台账/看板/landing_pack；例外=工具日志→out/loadbench/；= scope_declared ✔
```

---

## 5. 硬性纪律（违反即回退重做）

1. **禁伪造实测**：未运行一律 `[待实测]` + T6 原因；禁止占位图/复用 MD5 冒充。
2. **禁省略锚点**：结论必须可回溯到 VA+hex 或 文件:行。
3. **禁越界写入**：只写 `scope_declared`；例外必须 5.4 声明；需改他人文件 → [3] 勘误交 Lead。
4. **禁混称**：状态必须带轨名（二进制轨/代码轨/纸面规格）；禁用二进制收据证明代码轨。
5. **禁伪帧数/条数**：验收表写**实际**帧号/条数/哈希。
6. **禁跳步充数**：跳过步骤在 T6 写清「跳过 X，原因 Y」。
7. **红线 G-R5**：任何回执不得出现「MP 可发布 / G4.1 已满足 / 联机安全可出厂」。
8. **崩溃一票否决**：窗口内 `except.txt` 新增/更新 ⇒ 卡级 `fail`，整批不得放行。
9. **零生效禁止放行**：断言已开但遥测计数=0 ⇒ 标 `未生效(UNVERIFIED)`，禁止 PASS。
10. **长度**：回报正文 ≤ 4 页；细节进 evidence 与 [8] 清单。

---

## 6. 与既有模板对照

| 既有 | 保留 | v2 变化 |
|---|---|---|
| `AGENT_DELIVERY_FORMAT` §A 十节 | 全保留，作骨架 §[0]–[9] | 并入 RESULT 紧凑块 + 七轨表 |
| `dual_track_status_note` §3.3 | 双轨状态节 | 升为 T1 必填轨名 |
| `R_b5_detail/receipt_template.md` | DUAL-LAN 三键、红线 G-R1..R7 | 并入 T3/T5/T7；B5 特有键作附录 |
| `R_hd_card` / `R_h20c_card` RESULT 块 | 字段键名兼容 | 统一到 §3 字段并集；缺值写 n/a |
| 各卡 landing_pack「交付回执」 | 可继续出卡内摘要 | **完整回执以本模板为准**，卡内只留指针 |

---

## 7. 本任务合规边界

- **已写**：`docs/re/zcode_receipt_template_v2.md`（本文）+ `out/re_work/re_sprint/R_receipt_v2/**`
- **未写**：台账/看板/landing_pack/`ra2render/**`/`zcode_live`/任何二进制与 ini
- **字段来源**：15 份 `RESULT_*.md` + 3 份既有 `receipt_template.md` + `AGENT_DELIVERY_FORMAT` + `dual_track_status_note` 实文汇总（见同目录 `field_census.md`）

*v2 · R-RECEIPT-V2 · 模板本身不是实测。*
