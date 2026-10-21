# RE-ATLAS · 本线台账 (LEDGER)

> 按轮追加，前缀校验式追加（不改历史行）。每轮记录：时间、进程状态、领的模块、
> 完成件、证据路径、留给下一轮的悬项。
> 与 `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` 严格分离——那是 GOAL-3T 的账。

---

## R-000 · 2026-10-21 18:4x — 建线 + R0 盘点 + R1 骨架

### 0. 心跳与进程检查（§8.3 / §10.1）

| 项 | 结果 |
|:---|:---|
| `tasklist` 查 `gamemd` | 无 |
| `tasklist` 查 `ra2loader` | 无 |
| GOAL-3T 台账尾部 | 已读（§325，U8 真机 V1/V2/V4 PASS；③ 门 4/5；余项全需用户在场） |
| 结论 | GOAL-3T 当前无线程在飞的真机测量 ⇒ 可做完整离线分析 |

**GOAL-3T 台账尾部要点（只读，不改）**：
- U8 loader 探针：`ra2loader.exe` 长驻、子进程 1 个、窗口 `1707×960`。
- `ra2render.dll` 加载基址 `0x543C0000`，映像 3,063,808 B。
- 母本四件哈希未动（`blitter_hooks.cpp 656e6b4e…` 等）。
- 未闭合项全部标注"需用户在场"。

⇒ 与本轮的 R0/R1 无资源冲突，且本轮**完全不碰**其禁区（帧循环、SBH、HouseClass
实例化、ra2render、P1/SBH 合批、qc151 trip、`--allow-loader`）。

### 1. 本轮领的模块

- **R0**（盘点）：语料索引、种子收录、冲突清单。
- **R1**（全局骨架）：PE 段表、RTTI 类清单与虚表、函数边界与命名覆盖率、主要全局对象。

### 2. 完成件

| 件 | 路径 | 状态 |
|:---|:---|:---|
| 语料索引（256 文件） | `out/corpus_index.json` | ✅ |
| 323 条 claims 独立复算 | `out/claims_verify.txt` | ✅ **323/323 PASS** |
| 二进制身份与 diff | `out/binary_identity.txt` | ✅ 2 字节 CheckSum 差异 |
| 符号映射（1,304 点） | `out/symbol_map.json` | ✅ 段表校验 |
| 冲突分级 | `out/conflicts.{json,txt}` | ✅ 5 REAL / 400 ALIAS / 14 NOISE |
| RTTI 解析 | `out/rtti/{hierarchy.txt,symbols.json}` | ✅ 988 类 |
| 虚表交叉 | `out/vtable_xcheck.txt` | ✅ 20/20 一致 |
| 实例尺寸交叉 | `out/size_xcheck.txt` | ✅ 12 OK / 2 翻案 / 2 口径失效 |
| 函数遍历 | `out/fn_walk.txt` | ✅ 15,224 入口 |
| 线性扫描反面样本 | `out/fn_census.txt` | ✅ 11.1% 覆盖（证明不可用） |
| 知识库正文 | `kb/00_global_skeleton.md` | ✅ |
| 地址总表 | `INDEX.md` | ✅ |
| 冲突清单 | `CONFLICTS.md` | ✅ |
| 进度 | `STATUS.md` | ✅ 本件 |

### 3. 关键发现（三条）

1. **【首报】ATLAS §11.2 `TeamTypeClass` 尺寸错**：记 288/`0x120`、取证 `0x6F29C0`；
   实测 `vtable[12]=0x006F20B0` = `B8 F8 00 00 00 C3` ⇒ **248/`0xF8`**。
   且 `0x6F29C0` 是一段浮点函数中部，既非函数头也无该指令。
2. **【双通道】ATLAS §11.2 `AITriggerTypeClass` 尺寸错**：实测 272/`0x110`；
   与语料内 E-AIT-1（`trigger_tag_abi_deep_dive.md`）完全一致，本线独立复现。
3. **【方法】`vtable[12]==GetSize` 非普适**：至少 `RadarClass`、`WWMouseClass`
   在该槽放的是访问器（体首 `mov eax,[ecx+…]`）。凡引用 §11.2 尺寸须先验体首形态。
   反向也说明：线性 capstone 扫描在本件只覆盖 .text 的 11.1%，**不可用于覆盖率分母**。

### 4. 留给下一轮

| # | 悬项 | 说明 |
|:--|:---|:---|
| T-1 | 2 处尺寸勘误需 Lead 出 ATLAS 补丁块 | 本线不写 `docs/re/`；见 `CONFLICTS.md` G-1/G-2 |
| T-2 | 753 个语料命名点不在函数入口上 | 需分辨"函数体内站点"与"数据地址"，留待逐模块处理 |
| T-3 | 全局单例的解引用层级（`*` vs `**`） | 12 条仍是"社区"级，需运行时或更深静态推导 |
| T-4 | R2-1 地图/触发器模块 | 已领，种子在 `trigger_system_manifest.md`（515 VA） |

### 5. 禁区与纪律自查

- [x] 未启动 gamemd / ra2loader
- [x] 未写 `ra2youli`
- [x] 未跑 trip harness
- [x] 未改任何二进制 / 母本 / ra2render / harness
- [x] 未编译
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 未为绕过钩子改名/转码/拆分（钩子拦截了脚本内 `open(...,"w")`
      与 `sed -i`，均改为**Write/Edit + stdout 重定向**这一机制内的正规写法）

### 6. 钩子交互记录（供后续参考，非抱怨）

| 触发 | 原因 | 合规改法 |
|:---|:---|:---|
| `Write inventory.py` | 脚本内含 `open(...'w')` 绝对路径 | 改为只 `print(json)`，由 shell `>` 落盘 |
| `Write classify_conflicts.py` | 同上 | 同上（`REATLAS_JSON=1` 切换输出） |
| `Bash: sed -i ... xcheck_vtables.py` | 用 shell 改源码 | 改走 `Edit` 工具 |

⇒ 结论：**脚本内不写文件，一律 stdout 重定向**；**源码修改一律 Edit**。
这两条会成为本线的固定写法。

---

## 追加规则

- 每轮开头加 `## R-<序号> · <日期> <时间> — <模块>`。
- 只追加，不改既有行；如需更正，新开一条并引用被更正的行号/小节。
- 每轮必填：进程状态、领的模块、完成件、禁区自查。

---

## R-001 · 2026-10-21 19:0x — R2-1 触发器派发链（首个子系统）

### 0. 进程检查

`tasklist` 无 gamemd / ra2loader ⇒ 可做完整离线分析。GOAL-3T 台账尾部无变化（§325 U8）。

### 1. 领的模块

R2-1 的**触发器派发层**（`TActionClass::Execute` / `TEventClass::HasOccured` / `TeamClass::AI`），
不含 TaskForce/脚本参数（下一轮）。

### 2. 完成件

`kb/10_map_triggers.md`。

### 3. 复算结果

| 对象 | 结论 |
|:---|:---|
| `TActionClass::Execute` `0x6DD8B0` | 入口实证；跳表 `0x6DFDEC` **145/145 在 .text**，143 唯一目标 |
| `TeamClass::AI` `0x6E9050` | 入口实证；表 `0x6E9F74` **65/65 在 .text**，65 唯一（无别名） |
| `TEventClass::HasOccured` `0x71E940` | 入口实证；**两级**派发 `0x71F218`(12 dword) + `0x71F248`(49 B) |
| `TeamClass+0x3C` | 当前脚本状态字段（与入参比较后早退） |
| `TEventClass+0x2C` | 事件类型 ID；合法域 `0x0D..0x3D` |

### 4. ★ 本轮的方法论错误与更正（必须记住）

**错误**：我先把 `0x71F218` 当成 49 个 dword 的满表读，读到 `0x0B0B0B0B`、`0x01010101`，
并**误判为"填充/调试魔数"**，据此写下"表不是满表、有空洞"的结论。

**真相**：`0x71F218` 只有 **12 个 dword**；紧跟其后的是 **`0x71F248` 的 49 字节选择表**。
按 4 字节步长跨读 `table1` 尾部，就把 `table2` 的字节拼成了假 dword。
正确语义是 `target = table1[ table2[kind - 0x0D] ]`。

**触发原因**：语料 `trigger_system_manifest.md:18,27` 与 `ARCHITECTURE_ATLAS.md:2793,2869`
**都写明了 "12 目标 + 49 B 选择表"**，我的首轮 grep 只在 `docs/re/*.md` 的顶层下了
`grep "0x71F218"`，命中了但**没读那句话的全文**，就按 `cmp eax,0x30` 自行推成 49 槽满表。

**新纪律（本线自用）**：
1. **凡"跳表"结论，必须先找 `jmp [reg*4 + imm]` 的 `reg` 是怎么算出来的**，
   看清是否有前置查表/移位；有二级表时槽数 ≠ 表长。
2. **凡读到 `0x0B0B0B0B` / `0x01010101` / `0x0B0B0100` 这类值，一律先怀疑跨表误读**，
   不要先归因为"填充魔数"。这些字节本身就是 `0b` / `01` 的字节填充。
3. **命中文档后必须读整句**，不能只确认"地址出现过"。

### 5. 禁区自查

- [x] 无游戏进程启动；无 ra2youli 写入；无编译
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 仅读字节 + 写 `re_atlas/`

### 6. 留给下一轮

| # | 悬项 |
|:--|:---|
| U-1 | 145 项 Action 的 2 组别名是哪两项（目前只知 145−143=2 对） |
| U-2 | `0x71EC63` 的双重身份：`ja` 目标 + 二级表 `0x0B` 兜底 ⇒ 语义合并已确证，待写清 |
| U-3 | 三/四级子派发（`0x71F27C`/`0x71F2C0`/`0x71F328`）独立复算 |
| U-4 | `TEventClass`/`TActionClass` 字段布局（已有 +0x2C、+0x90 两个点） |
| U-5 | TaskForceClass / ScriptClass / TagClass 从虚表出发 |

---

## R-002 · 2026-10-21 19:1x — 异族核验失败 + 通道冷却

### 1. 派发明细

按 §7「DeepSeek 执行 ⇒ 千问/GLM 核验」：

| 子代理 | 通道 | 结果 |
|:---|:---|:---|
| 千问核验 | `new-provider-3/qoder-global:qfmodel` | **failed**（77,304 tok，无 `submit_result`） |
| GLM核验 | `new-provider-2/glm-5.3-flash` | **unfinished**（进程退出时仍在飞） |

工作流 `dwfrun-4cc83e74` 于 5m36s 后 **errored（DriverError）**。

### 2. ★ 交付判据（本项目既有纪律，本轮再次验证）

**判据 = 文件是否在盘，不是运行态是否 completed。**
本轮 `re_atlas/out/verify/` 目录**被创建但为空**——两个子代理都没写出任何字节。
所以本轮**零核验交付**，两条尺寸翻案**仍未异族核验**。

### 3. 根因：通道限流，非脚本缺陷

`GetWorkflowRun` 的 health 字段：`concurrency=10/14 (rate_limited since 3m 15s ago)`。
⇒ 环境当时已在限流，两路核验都是被上游截断，不是任务书问题。

### 4. 处置（§7 纪律）

- **`qoder-global:qfmodel` 冷却 30 分钟**（至约 19:4x）。
- **`new-provider-2/glm-5.3-flash` 冷却 30 分钟**（至约 19:4x）。
- 本轮**不再重派**。改为本地整理（写文档、补 INDEX/STATUS）。
- 冷却结束后重派时，任务书要**缩短**：本轮 77k token 才失败说明任务书过大，
  下一版把"写完整 markdown 报告"降级为"只回 10 行结论 + 关键字节"。

### 5. 对结论的影响

- `TeamTypeClass` 248 / `AITriggerTypeClass` 272 这两条**保持"实证（单通道）"**，
  ⚠ **不升级为"已核验"**。
- 其中 `AITriggerTypeClass` 另有语料内 `E-AIT-1` 独立佐证 ⇒ 可视为**双通道**（本线 + 语料），
  但仍不满足 §7 的"异族模型核验"定义。
- `CONFLICTS.md` G-1 / G-2 的"核验状态"字段维持 `⏳ 待异族核验`。
- **HANDOFF H-001 的置信度措辞需回改**：原文写"实证（双通道）"，
  现澄清为"字节实证 + 语料 E-AIT-1 佐证；异族模型核验待补"。

---

## R-003 · 2026-10-21 19:2x — 路径更正：`out/` → `evidence/`

**背景**：公开仓 `.gitignore:26` 有全局 `out/` 规则 ⇒ `re_atlas/out/` 全部被忽略、无法提交。

**处置**：目录改名 `re_atlas/out` → **`re_atlas/evidence`**（不改 `.gitignore`——那是仓库既有约定，本线无权改）。所有工具与文档中的路径引用同步更新。

**对本台账前文的更正**：R-000 §2 与 R-001 中出现的 `out/xxx` 路径，
一律读作 **`evidence/xxx`**。历史行不改（前缀校验纪律），以本条为准。
