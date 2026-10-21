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

---

## R-004 · 2026-10-21 19:3x — R2-1 第二轮：类尺寸与 AbstractClass 多继承

### 0. 进程与通道

`tasklist` 干净。异族核验两通道仍在冷却（至约 19:41），**本轮未派子代理**，全本地。

### 1. 完成件

`kb/11_class_layouts.md` + `tools/dump_class_layouts.py` + `evidence/class_layouts.txt`；
`kb/10_map_triggers.md` 补 §3.5（四级表复算）与 §3.6（兜底真实身份）。

### 2. 核心成果

**（A）触发器族 8 类实例尺寸首次实证**（语料此前只有 `TeamTypeClass`/`AITriggerTypeClass` 两条）：
Script 48 / Tag 56 / Trigger 72 / TEvent 88 / TAction 148 / Team 160 / TaskForce 212 / ScriptType 564。

**（B）★ `AbstractClass` 是多继承，4 个 vtable 指针**
（`+0x00/+0x04/+0x08/+0x0C`，COL.offset 依次 `0/4/8/12`）。
证据链：删除析构 `0x004105A0` 连写四次 vptr → 每个 `vtable-4` 的 COL.offset 各不相同 → 接口跳板 `sub [esp+4],4; jmp`。
**语料完全没有记载这个结构。**

**（C）`AbstractClass::GetSize` 返回 0 是桩**（`33 C0 C3`），不是"尺寸为 0"。
⇒ 任何"拿基类尺寸算派生类"的写法都会得 0。

**（D）事件派发是四层树，且末项恒为兜底**
L1 12 项 / L2 2 项 / L3 14 项 / L4 10 项；选择表最大值分别 `11`(=12−1) / `1`(=2−1) / `13`(=14−1) / `9`(=10−1)。
**四张表的目标集合互不相交** ⇒ 树形嵌套，非扁平多路。

**（E）`0x71EC63` 不是空桩**，是 `cmp ecx,0x13/0x14/0x15/0x16...` 比较链，
把控制流引向 L2 的 `0x71ECAF`（"扁平比较链"实现）。
⇒ 37 个未专属实现的 EventKind **仍会被真正求值**，不是恒 false。

### 3. ★ 本轮纠错（前轮误读，已在新文中改正）

**错误**：前轮把 `0x006DD8CB` 的 `mov dl,[ecx+0x90]` 记为"`TActionClass+0x90` 是 byte 标志"。

**真相**：该处 `ecx` 是 `Execute` 的**栈参数对象**（`0x006DD8BD: mov ecx,[esp+0x254]`），
不是 `this`（`this` 在 `esi`，`0x006DD8BB: mov esi,ecx`）。
而 `TActionClass` 自己的 `+0x90` 在 `0x006E3ECD` 被当 **dword** 读并写入存档。
⇒ 两处是**不同对象的同一偏移**，我把它们混为一谈了。

**新纪律**：**凡看到"同一偏移出现在两处"，必须先确认两处的 `ecx`/`esi` 各绑的是谁**，
再看类型是否一致。寄存器重绑定在长函数里极易被跨读。

### 4. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 冷却期内未派子代理

### 5. 留给下一轮

| # | 悬项 |
|:--|:---|
| L-1 | `AbstractClass+0x14..+0x1C` 三个 dword 语义（不进存档 ⇒ 纯运行时态） |
| L-2 | `+0x10` / `+0x20(bool)` 的业务语义 |
| L-3 | `TEventClass+0x30` / `+0x54` 两个接口对象的真实类型（`0xB0C110` 键是什么） |
| L-4 | `TaskForceClass` 212 字节内部结构 |
| L-5 | `ScriptTypeClass` 564 字节内部结构 |
| L-6 | 冷却结束后补：`TeamTypeClass` 248 的异族核验 |

---

## R-005 · 2026-10-21 19:3x — 序列化顺序 / 容器簇 / 二次异族核验

### 1. 完成件

`kb/11_class_layouts.md` §7–§9；`HANDOFF` 新增 H-005 / H-006。

### 2. 新实证

**（F）序列化顺序 = 先基类后派生**
`ScriptClass::Save (0x006914E0)`：先 `call 0x00410410`（`AbstractClass::Save`），
再写自己的 `+0x2C`。⇒ 存档字节是"基类在前、派生在后"的拼接，读档必须严格对称。

**（G）`ScriptTypeClass` 容器簇在 `+0x98/+0xA0/+0xA4/+0xA8`**，
与 `TaskForceClass` 的 `+0x9C/+0xA4` 差 4 字节 ⇒ 疑同模板不同基类尺寸实例化。

**（H）`0xB0C110` 定性为引擎级字段注册表根**（489 处 `lea; push; push key; call` 模式），
非事件专用键；`TEventClass+0x30/+0x54` 只是其中两处。

### 3. 异族核验（v2，简化任务书）

首轮两路失败后重派，任务书改为"只回结构化 Verdict，不写文件、不写长报告"。
工作流 `dwfrun-c318607d`。结果待回收；若仍空交付，按 §7 再冷却并把
`TeamTypeClass` 248 长期标为"单通道"。

### 4. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 子代理任务书只读、只回结构化结果

### 5. 留给下一轮

见 `kb/11_class_layouts.md` §9 的 L-1…L-8；其中 L-7（容器簇统一建模）为下一轮首要。

---

## R-006 · 2026-10-21 19:4x — 容器簇统一模型 + 一次口径撤回

### 1. 新实证

**（I）容器三元组统一模型**：`TaskForceClass` 与 `ScriptTypeClass` 在
`+0x98 / +0xA4 / +0xA8` **完全对齐**，只有"计数"字段差 4 字节
（`0x9C` vs `0xA0`）⇒ 同一套容器布局在不同基类尺寸下**整体平移 4**。
`ScriptTypeClass+0xA0` 的 `cmp esi,[edi+0xA0]; jge` 与 `TaskForce+0x9C` 同角色，
且 `mov [esi+0xA0],edi` 证明它可写 ⇒ 计数器而非指针。

### 2. ★ 撤回一条断言（本轮自查）

**曾写**：`0x817F6C` 的格式串"实测为 `%d`"，据此推断"为每个成员生成十进制 ID"。

**撤回**：`0x817F6C`、`0x81C000`、`0x889F64` **全部落在 `.data`（可写段）**，
不是 `.rdata`。`.data` 的内容运行时可变，其**文件初始字节**恰好解出 `%d` / `%d,%d`
不构成"静态格式串"的证据。已在 KB §6 与 §10 就地更正并标注。

**同时撤回**：`0x723CE0` 曾被写作"按索引取条目"的访问器。实测体首是
`mov eax,[ecx+4]; mov ecx,[ecx]; push; push; push <模板>; call 0x7C8EF4`
⇒ 是**格式化 helper**。已更正。

**新纪律（本线第 4 条）**：
**凡引用"字符串常量"，先确认地址在 `.rdata`**（`0x7E1000..0x812000`）。
`.data` 里的字节只有"文件初始值"意义，不能当常量，也不能用于反推语义。

### 3. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 异族核验 v2 在飞（`dwfrun-c318607d`），只读复算

### 4. 留给下一轮

L-9（stride）、L-10（`+0xA8`）、L-11（模板参数来源）为下一轮首要。

---

## R-007 · 2026-10-21 19:5x — 解析路径实证 + 第二次模型撤回

### 1. 新实证

**（J）`ScriptTypeClass` slot25 是 INI 解析流程**。关键坐标：
- `+0x24` = 一个**独立子对象**（`lea ebx,[esi+0x24]`），作为 5 参调用首实参；
  `AbstractTypeClass` 的 `0x00410A60` 里也出现 `lea ebp,[ebx+0x24]` ⇒ 本族通用。
- `+0xA0` = 已处理条目计数（循环前清零、循环条件读）。
- `0x00528A10` = **`ret 0x14`（5 个 4 字节实参）**，含最小实参校验 ⇒ 疑 INI `ReadString`。
- `0x00526B00` = 把对象 `+4/+8` 清零的小结构初始化。
- `0x00727CF0` = 逐字符解析数字（`atoi` 形态）。

### 2. ★ 第二次撤回：`+0xA4` 不是"成员数组基址"

**曾写**（§6/§10）：`+0xA4` = 成员数组基址，并据此提出"两类容器三元组完全对齐"模型。

**为什么收回**：
- `ScriptTypeClass` 的解析代码里 **`+0xA4` 根本没出现**，用的是 `+0x24`；
- `TaskForceClass` 的 `lea ebx,[edi+0xA4]` 只是把该地址**当实参传出去**，
  没有"基址 + 索引"的任何寻址证据；
- 所谓"两类在 `+0x98/+0xA4/+0xA8` 完全对齐"只是**访问频次表**的巧合，
  不是字段同一性的证据。

**保留**：只有 `+0x9C`（TaskForce）与 `+0xA0`（ScriptType）是计数，各有循环实证。

**新纪律（本线第 5 条）**：**"两个类同一偏移" ≠ "同一字段"**。
合并建模必须两侧各有独立证据（读 + 写/循环），仅有地址相邻或频次相似不算。

### 3. 这是本线本轮第二次自我纠错

第一次是 `.data` 当 `.rdata` 格式串（R-006）。两次共同根因：
**从"字节看起来像"跳到"语义就是这样"**。
第 4/5 条纪律就是针对这个：先确认段属性、先要求双侧证据。

### 4. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 异族核验 v2 在飞

### 5. 留给下一轮

L-12（`+0xA4` 真实角色）、L-13（`+0x24` 对象类型）、L-14（`0x528A10` 实参顺位）
为下一轮首要；L-9（stride）依赖 L-12 先定。

---

## R-008 · 2026-10-21 20:0x — TaskForce 数组布局完全解出（L-9/L-10/L-12 关闭）

### 1. ★ 核心成果

`TaskForceClass` 成员容器**完全确定**：

| 项 | 值 | 证据 |
|:---|:---|:---|
| 计数 | `+0x9C` (u32) | 既作下标 `ecx`，又作循环上界 |
| 数组基址 | `+0xA4` | `[esi + ecx*8 + 0xA4]` |
| **stride** | **8 字节** | `ecx*8` 伸缩；两次写差 4（`+0xA4`/`+0xA8`） |
| 元素 | `{dword @0, dword @4}` | 连续两次写同一 `ecx*8` 基址 |

`+0xA8` **不是独立字段**，是 `array[i]` 的第二半 ⇒ **L-10 关闭**。

关键指令（`0x006E8496..0x006E84B5`）：
```
mov ecx,[esi+0x9C]              ; 下标
mov [esi+ecx*8+0xA4], edx       ; 元素 +0
mov [esi+ecx*8+0xA8], eax       ; 元素 +4
mov ecx,[esi+eax*8+0xA8]        ; 读回
```

辅助证据：`0x004C4EF0` 把输入串解析进一个**两 dword 结构**（先 `mov [esi],0` /
`mov [esi+4],0` 清零再填）⇒ 与"元素 8 字节二元组"吻合。

### 2. 三项关闭 / 一项边界澄清

- **L-9（stride）** ✅ 8 字节。
- **L-10（`+0xA8`）** ✅ 是元素第二半，非独立成员。
- **L-12（`+0xA4` 角色）** ✅ 是本类的数组基址；
  **但不推广到 `ScriptTypeClass`**（后者走 `+0x24`，`+0xA4` 未出现）。
  R-007 的撤回**仍然有效**：撤回的是"跨类共用"，不是"本类作用"。

### 3. 纪律执行情况

本轮三次自纠（R-006 `.data` 当 `.rdata`、R-007 `+0xA4` 过度推广、以及本轮
把 `0x723CE0` 从"访问器"更正为"格式化 helper"）都已在 LEDGER 与 KB 就地留痕。
**没有一条被静默改掉。**

### 4. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 异族核验 v2 在飞（GLM 已 settle，千问在限流退避）

### 5. 留给下一轮

L-13（`+0x24` 对象类型）、L-14（`0x528A10` 实参顺位）、L-15（`0x4C4EF0` 实参）
＋ `TeamTypeClass` 248 的异族核验补做。
