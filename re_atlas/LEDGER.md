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

---

## R-009 · 2026-10-21 20:1x — L-13 解：`+0x24`/`+0x64` 归属 `AbstractTypeClass`

### 1. ★ 归属纠正

**前文（R-007/§12）**：把 `+0x24` 写成 "`ScriptTypeClass` 的子对象（本族通用）"。

**实测**：`0x00410A60` 在 **`AbstractTypeClass`（`vt=0x007E2000`）的 slot 25**，
且 `SideClass`（`vt=0x007F2EC0`）继承同一槽。
⇒ `+0x24` / `+0x64` 是 **`AbstractTypeClass` 前缀里的 INI 槽对**，
所有派生类型类共享，**不是脚本专用**。

### 2. 槽语义表（`AbstractTypeClass`）

| 槽 | VA | 判读 |
|---:|---|---|
| 24 | `0x00410C20` | 空桩（`ret 4`） |
| 25 | `0x00410A60` | **`ReadINI`**（校验 `0x526810` → `push 0x31` → `0x528A10` 读） |
| 26 | `0x00410B90` | **`WriteINI`**（先写 `+0x24`，再 `lea eax,[esi+0x64]` 写第二槽） |

### 3. 未能判定的项（如实留白）

`ReadINI` 里的 `push 0x31`（=49）位于 `push <模板>` 与 `push edi`（`+0x64`）之间。
**可能是"数量上限"，也可能是"缓冲区长度"**，两者都能解释，缺一项证据。
**本轮不猜**，列 L-16。

### 4. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 异族核验 v2：GLM 已 settle，千问在限流中（7min+）

### 5. 留给下一轮

L-14/L-15/L-16 + `TeamTypeClass` 248 异族核验补做。

---

## R-010 · 2026-10-21 20:2x — L-16 保持开放 + 环境限流说明

### 1. L-16：`push 0x31` 不做判定

追了 `0x528A10` 内第 5 实参（`[esp+0x2c]`）的全部读点：
- `0x528A26` 只做 `cmp ...,2; jl` 的"至少 2"校验；
- `0x528B6F / B84 / BA4 / BAC` 都是"取进 `edi` 后走返回路径"。

**没有**任何循环上界 / `rep movs` 计数用法。⇒ 它**不是**"49 项上限"，
但也不是"缓冲区长度"。语义待定，**L-16 保持开放**。

这条记录本身是对"想当然"的一次拦截：上一版 KB 里我写的是
"两种解释都成立，缺一项证据"，实际追完之后**两种都不成立** ——
如实记为"未判定"比给一个像样的猜测更接近事实。

### 2. 异族核验 v2 状态

- GLM：1 step settled，82,547 tokens。
- 千问：8 分钟以上限流退避（`backoff after rate_limited`）。
- 环境整体 `rate_limited`（并发 1/14）。
⇒ **本轮不等**。`TeamTypeClass` 248 继续标"单通道字节实证"。
若下轮环境恢复，用 AmendWorkflow 续跑（已有 GLM 结果会走缓存）。

### 3. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`

---

## R-011 · 2026-10-21 20:3x — 本轮收尾

### 1. 本轮（19:2x–20:3x）累计产出

| 件 | 数量 |
|:---|---:|
| 提交 | 8 次（`10084ea` … `30823b6`） |
| KB 新增篇 | 1（`11_class_layouts.md`，~600 行） |
| 新增工具 | 1（`dump_class_layouts.py`） |
| 新增交接条目 | 2（H-005 / H-006） |
| 关闭的开放项 | L-3 / L-4 / L-9 / L-10 / L-12 / L-13（6 项） |
| 撤回的过度解读 | 3 条 |
| 归属纠正 | 1 条 |

### 2. 主要新增实证（按价值排序）

1. **`AbstractClass` 多继承 4 vptr**（COL.offset 0/4/8/12）—— 语料完全无记载。
2. **触发器族 8 类实例尺寸**全部实证 —— 语料此前只有 2 条。
3. **`TaskForceClass` 数组 = 8 字节 `{id,value}` 对**（`+0x9C` count / `+0xA4` base）。
4. **`AbstractTypeClass` 的 `ReadINI`/`WriteINI` 槽**（25/26），INI 槽对 `+0x24`/`+0x64`。
5. **事件派发四层树**且末项恒兜底（L1–L4 目标集合互不相交）。
6. **序列化顺序 = 先基类后派生**。

### 3. 纪律执行

三处撤回全部就地留痕，无静默修改：
- R-006 `.data` 当 `.rdata` 格式串（`0x817F6C` 等）
- R-007 `+0xA4`"两类共用容器"的跨类推广
- R-010 `push 0x31` 从"疑似上限"→追完两种解释都不成立→如实记"未判定"

新增纪律 2 条（第 4/5 条）：引用字符串常量须先验段属性；跨类同偏移不等于同字段。

### 4. 异族核验仍未完成

- GLM：1 step settled（82,547 tok）。
- 千问：10 分钟持续限流退避，未回。
- ⇒ `TeamTypeClass` 248 保持"单通道字节实证"，**未升级**。
- 下轮优先：环境恢复后 `AmendWorkflow` 续跑（GLM 结果走缓存，不重付费）。

### 5. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 只提交 `re_atlas/`

---

## R-012 · 2026-10-21 20:1x–21:0x — 虚表契约 + 撤回 `0xB0C110` 误读 + L-6/L-14/L-16 结清

### 0. 心跳与进程检查（§8.3 / §10.1）

| 项 | 结果 |
|:---|:---|
| `tasklist` 查 `gamemd` / `ra2loader` / `game.exe` | **全无** |
| GOAL-3T 台账尾部 | 已读（`lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`）：在飞 = HouseClass 计数器 + `units0` 单位损失曲线（T55 线） |
| 与本轮冲突 | 无。本轮做 `AbstractClass` 虚表契约 / 触发器族对象字段，与其禁区（帧循环、SBH、`HouseClass` 实例化、ra2render、P1/SBH 合批、qc151 trip）零交集 |

### 1. 异族核验终于闭环（承接 R-011 §4）

三轮才成：

| 轮 | run | 结局 | 原因 |
|:--|:--|:--|:--|
| 1 | `dwfrun-4cc83e74` | errored | 千问 + GLM 双路限流，零落盘 |
| 2 | `dwfrun-c318607d` | errored 30m48s | 千问限流卡 13 分钟；GLM settled 但**没调 `submit_result`** ⇒ typed `ask` 无结果 |
| 3 | `dwfrun-7cee3752` | ✅ completed | 改**纯文本四行协议**（`VERDICT:` / `TEAMTYPE:` / `AITRIGGER:` / `NOTE:`），脚本侧正则解析 |

**根因**：两族模型都不会主动调用 typed `ask` 要求的 `submit_result` 工具。
这不是限流问题，是**协议假设错误**——第 2 轮明明 GLM settled 了 82.5k token 却没有产出。

**结果**：GLM 5.3 `CONFIRMED(248/272)` + DeepSeek v4.1-flash `CONFIRMED(248/272)`
⇒ `TeamTypeClass` 248 / `AITriggerTypeClass` 272 升级为**已核验**（G-1/G-2 已改）。

**纪律 6（新增）**：派给非本宿主模型的 `agent().ask`，若要求结构化结果，
**优先用纯文本约定 + 脚本侧解析**，不依赖 `submit_result`。
`AmendWorkflow` 的缓存按"名字 + ask 字节相同"匹配，本轮的 v3 脚本换了名字与协议 ⇒
前两轮的 token 未复用（215,906 + 145,759 沉没），但首次即成功。

### 2. 本轮最大的发现：`vtable[11]` = `WhatAmI()`，`vtable[12]` = `GetSize()`

起点是查 L-6（`TEventClass+0x30`/`+0x54` 是什么），追 vtable 槽表时发现槽 11 全是
`mov eax, imm8; ret`，且 imm 与类身份一一对应。

| 事实 | 值 | 证据 |
|:---|:---|:---|
| 槽 11 = `WhatAmI()` | `AbstractType` 类型 ID | 59 类命中 |
| 槽 12 = `GetSize()` | 实例尺寸 | 59 类命中 |
| ID 冲突 | **0** | 59 个 ID，59 个不同类 |
| 引擎名字表 | `0x816EE0`，**74 项**，`{char* name, u32 value}` | 直读，值域 `0x00..0x49` 无空穴 |
| 三方一致 | 槽 11 字节 ↔ 名字表 ↔ YRpp `AbstractType` | ✅ |

**这修正了 G-4/G-5 的判据**：前轮只说"槽 12 不一定是 GetSize"，
正确表述是"槽 11/12 成对，先验槽 11"。已写进 `kb/20_vtable_contract.md`，
`INDEX.md` §B 表整个重做（新增"类型 ID"列）。

**给 ③ 的价值**：按类型分派不再需要 RTTI/dynamic_cast，一个 `call [vt+0x2C]` 就够。

### 3. 撤回 5：`0xB0C110` 不是"字段注册表"，是 `SwizzleManagerClass::Instance`

前轮（R-006～R-011 期间）据 489 处引用判它是"引擎级字段注册表的根"。
**本轮三处字节 + 一条社区源全推翻**：

```text
0x006CF0C8  mov dword ptr [0xB0C110], 0x7F4108   ; 静态初始化器写虚表 ⇒ 它是对象
0x007F4108  → RTTI = SwizzleManagerClass (ISwizzle, IUnknown), 10 槽
0x007F4108 slot[4] = 0x006CF240                  ; 489 处调的就是它
0x006CF2A8  mov dword ptr [edi], 0               ; ★ 登记后把原字段清零
```

社区源 `YRpp/SwizzleManagerClass.h:26` 独立佐证
`reference<SwizzleManagerClass, 0xB0C110u> const Instance{};`。

**语义定谳**：`Here_I_Am` 把 `{原指针, 字段地址}` 追加进 swizzle 向量，
**然后 `*ppField = 0`**，供存档做指针重定位。
⇒ "读了字段还是有效指针"的假设会错。已转 **H-007** 给 ③。

### 4. L-6 部分闭合：`TEventClass` 是**三个**接口字段，`Save` 是**四项**

前轮记"两个接口字段（`+0x30`/`+0x54`），`Save` 三项"。实测：

```text
ctor 0x0071F8C0:  swizzle 登记 +0x28 / +0x30 / +0x54   ← 三个
Save 0x0071F820:  基类 → +0x28 → +0x2C → +0x30 → +0x34  ← 四项
```

**`+0x28` 完全漏了**。且 `+0x54` 虽被 swizzle 登记但**不在 `Save` 里** —— 新悬项 L-20。
`+0x28`/`+0x30` 走同一三步（`p=*(obj+off)`；`vt=*(p+4)`；`call [vt+0x10](p+4)`），
确证是"外部接口对象指针"，但真实类名未定 → L-21。

### 5. L-16 结清：`push 0x31` = `AbstractTypeClass::Name[0x31]` 的容量

前轮追完"49 项上限"与"缓冲长度"两种解释都不成立，如实挂起。**本轮解出第三种**：

```text
0x00410A91  lea edi, [ebx+0x64]     ; 目标 = Name
0x00410A94  push 0x31               ; 容量 49
0x00410A98  push 0x817854           ; "Name"  (.rdata)
0x00410AA0  call 0x528A10           ; ReadString
```

社区源 `YRpp/AbstractTypeClass.h:76` `char Name [0x31];` —— **精确相等**。

⇒ 教训：连续两次猜错后不该只记"未判定"，应去**查同一函数的其它调用现场**
（`0x410AEB` 的 `push 0x20` + `"UIName"` 就是对照组）。

### 6. L-14 推进：`0x528A10` 参数顺序定序

```text
0x528A10(INI对象, 节名, 键名, 目标缓冲, 默认值, 容量) ; ret 0x14
```
依据 `0x410A94..0x410AA0` 的 push 逆序 + 栈帧偏移。
`cmp arg2, 2` 是"键名长度 ≥2"，不是前轮猜的"条目上限"。
剩余：节名缓存快速路径未展开 → L-23。

### 7. 本轮新增悬项

| # | 悬项 |
|:--|:---|
| L-17 | 15 个高频类（`House`/`Unit`/`Building`/`Bullet`/`Anim`/`NavyType`…）的 `WhatAmI` 为何不是单指令（工具模式太窄） |
| L-19 | `vtable[4]`=Load / `vtable[13]`=Save 的槽号是否全族固定（本轮只验 11/12） |
| L-20 | `TEventClass+0x54` 被 swizzle 登记但不在 `Save`，由谁存档 |
| L-21 | `TEventClass+0x28`/`+0x30` 两个外部接口对象的真实类名 |
| L-22 | `AbstractTypeClass` 实测字段边界（`+0x24` 节名 24B / `+0x3D` UIName 32B / `+0x64` Name 49B）与 YRpp `UINameLabel[0x20]` 不符 |
| L-23 | `0x528A10` 节名缓存快速路径 |

**关闭**：L-6（部分：结构已定，类名转 L-21）、**L-14**（主序已定）、
**L-15**（`0x4C4EF0` 全解）、**L-16**（完全关闭）、**L-22**（见 §7.5）。
**新开**：L-17、L-19、L-20、L-21、L-23。

### 7.5 撤回 6：L-22 不成立 —— 是**我**误读了 YRpp，不是 YRpp 有错

本轮先写了"YRpp `UINameLabel[0x20]` 与实测 24 B 不符"，随后自查发现：
我是按"`ID` 从 `+0x00` 起"去套 `AbstractTypeClass` 自己的字段表，
**忘了那 0x24 字节属于基类 `AbstractClass`**。

按"`ID` 起于 `+0x24`"重排 YRpp 字段：

```text
ID[0x18] +0x24..+0x3B | zero_3C +0x3C | UINameLabel[0x20] +0x3D..+0x5C
pad +0x5D..+0x5F | UIName(ptr) +0x60..+0x63 | Name[0x31] +0x64..+0x94
```

**四个实测偏移全部精确命中**：`+0x24`（`0x410A79`/`0x410AF2`）、
`+0x3D`（`0x410AEB`）、`+0x60`（`0x410B58`/`0x410B69`）、`+0x64`（`0x410A91`）。
⇒ YRpp 无误。

**反向校验**：`AbstractClass` 属性表
`UniqueID(+0x10) / AbstractFlags(+0x14) / unknown_18(+0x18) / RefCount(+0x1C) /
Dirty(+0x20) / padding_21[3]` 正好 **0x24** 字节，且与
`AbstractClass::Save` 只写 `+0x10` 与 `+0x20` **完全对上**
（`Dirty` 是 bool，`0x4A1CA0` 用 `setne` 归一化写）。基类前缀尺寸由此**双向闭合**。

**纪律 7（新增）**：用派生类的字段表核对字段前，先算清基类占了多少字节。

### 7.6 L-15 全解（顺带）

`0x004C4EF0` 只有一个参数（`ret 4`），按 `"%d,%s"`（`0x82085C`，**在 `.data`**）
解析形如 `"12,GAOREP"` 的标识串，输出 `{ int, 类型对象指针 }` 两个 dword：

- `[esi]` = 解析出的整数（`0x004C4F27`）
- `[esi+4]` = 查类型表 `0xA8E34C[Items]` 命中的对象指针（`0x004C4F3E`），未找到则保持 0

`0x523C90` 是查表 helper：先短路 `"<none>"` / `"none"` 两个特殊名，
再线性比 `Items[i] + 0x24`（类型 ID 串）与目标。

**交叉印证**：`+0x24` 既是 INI 节名又是类型 ID 串 —— 同一个字段两种用途。
这把"`+0x24` 是什么"从观察变成定论。

**不做合并**：`{int, ptr}` 与 `TaskForceClass` 成员 `{id, value}` 同为 8 字节，
但**没有证据表明是同一类型**（R-007 纪律）。

### 8. 本轮产出

| 件 | 数量 |
|:---|---:|
| 新增 KB | 2（`20_vtable_contract.md`、`21_swizzle_and_object_fields.md`） |
| 新增工具 | 1（`dump_class_ids.py`） |
| 新增证据 | 1（`evidence/class_ids.txt`） |
| 新增交接 | 2（H-007 swizzle 清零、H-008 类型判定法） |
| 关闭悬项 | **5**（L-6 部分 / L-14 / L-15 / L-16 / L-22） |
| 撤回 | **2**（`0xB0C110` 字段注册表 → `SwizzleManagerClass::Instance`；L-22 是**本线误读**，YRpp 无误） |
| 核验升级 | 2（G-1、G-2 → 已核验） |
| 新增纪律 | 2（#6：非本宿主模型用纯文本协议，不依赖 `submit_result`；#7：核对派生类字段前先减基类前缀） |

### 9. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未启动 gamemd/ra2loader
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 只提交 `re_atlas/`
- [x] 未改 `.gitignore`；未改名/转码文件绕过钩子
- [x] 无整段反汇编上传（片段均 ≤20 条指令）

---

## R-013 · 2026-10-21 20:3x — L-17 结清：不是形态问题，是本线工具的两个静默空集缺陷

### 0. 心跳与进程检查

| 项 | 结果 |
|:---|:---|
| `tasklist` 查 `gamemd` / `ra2loader` / `game.exe` | **全无** |
| GOAL-3T 台账尾部 | 已读：在飞 = `--probe-frames` 早起帧 / `units0` 损失曲线（T55 线） |
| 冲突 | 无。本轮只动 `re_atlas/tools`、`kb/20`、`INDEX`、`CONFLICTS`，与其禁区零交集 |

### 1. 答案与我的预期相反

R-012 §7 我把 L-17 写成"15 个高频类的 `WhatAmI` 为何不是单指令形态，
**工具模式太窄**"。**这个前提本身是错的**：它们的 `WhatAmI` 就是标准的
`B8 imm C3`，一个字节都没特殊。

我先按 R-012 的假设去逐个读那 15 个类的 `v[11]`，结果是：

```text
HouseClass      v[11]=0x0050E360  B8 0D 00 00 00 C3   mov eax,0xD     ← 标准形态
UnitClass       v[11]=0x00746E20  B8 01 00 00 00 C3   mov eax,1       ← 标准形态
AircraftClass   v[11]=0x0041C180  B8 02 00 00 00 C3   mov eax,2       ← 标准形态
AnimClass       v[11]=0x00426580  B8 04 00 00 00 C3   mov eax,4       ← 标准形态
BuildingClass   v[11]=0x00459EC0  B8 06 00 00 00 C3   mov eax,6       ← 标准形态
BulletClass     v[11]=0x0046B550  B8 08 00 00 00 C3   mov eax,8       ← 标准形态
```

⇒ **全部命中**。所以问题在工具，不在数据。

### 2. 两个静默空集缺陷

**缺陷 1（主因）：capstone 把小立即数渲染成十进制**

```text
capstone 输出:  mov eax, 1        ← id 0x01，没有 "0x"
                mov eax, 0xd4     ← size 212，有 "0x"
```

我的判据 `a.op_str.replace(' ','').startswith('eax,0x')` 因此**跳过所有 id 0x00..0x09
与所有尺寸 < 10**。受影响的正是 `Unit`/`Aircraft`/`Anim`/`Building`/`Bullet` 及其
5 个 `TypeClass` —— 引擎最核心的 10 个类。

**缺陷 2（次因）：我自己加的尺寸上限 `0 < size < 0x4000`**

`HouseClass` = `0x160B8` = 90,296 字节，被这个上限滤掉。
当时写这个上界的理由是"类不会那么大"，属于**凭直觉设的闸**。

修法：

```python
# 不在渲染文本上做字符串判断，读结构
insn.operands[1].type == capstone.x86.X86_OP_IMM  ->  insn.operands[1].imm
# 上界放到 0x400000，并用 HRESULT 形状排除失败返回，而不是用大小排除
if 0x80000000 <= size <= 0x8000FFFF: skip
```

### 3. 修后结果

| 指标 | 修前 | 修后 |
|:---|---:|---:|
| ID+尺寸双命中类 | 59 | **69** |
| ID 冲突 | 0 | **0**（不变，仍零冲突） |
| 名字一致 | 52 | 62 |
| 引擎表未对应项 | 15 | **5** |

**新恢复的 10 个类**（ID / 尺寸）：

```text
0x01 Unit          2280    0x06 Building      1824
0x02 Aircraft      1752    0x07 BuildingType  6040
0x03 AircraftType  3600    0x08 Bullet         352
0x04 Anim           456    0x09 BulletType     760
0x05 AnimType       888    0x0D House        90296
```

### 4. 剩余 5 项各有正当原因（不是漏检）

| ID | 名称 | 原因 |
|---:|:---|:---|
| `0x00` | `<none>` | 哨兵值，无类 |
| `0x34` | `Abstract` | `AbstractClass` 的两个槽都指向 `0x004C9150` = `xor eax,eax; ret`（抽象桩） |
| `0x1F` | `Special` | `.rdata` 里搜不到 `SpecialClass` |
| `0x3A` | `AITrigger` | `.rdata` 里只有 `AITriggerTypeClass`(`0x3B`)，无 `AITriggerClass` |
| `0x40` | `NavyType` | `.rdata` 里搜不到 `NavyTypeClass` |

⇒ 这三条（`Special`/`AITrigger`/`NavyType`）是**枚举占位，引擎里无对应类**，
不列为待办。

### 5. 纪律 8（新增）

**capstone 的 `op_str` 是给人看的渲染结果，数值一律从 `operands[i].imm` 取。**
凡"解析指令取常量"的工具，必须同时输出**肯定对照**——
否则"合法地一个都没找到"与"判据全错"在日志上完全一样。

本轮就是靠"69 类、0 冲突"这个肯定对照，才确认修对了；
如果只修个别类看输出，很容易以为"还有 5 个查不到"而继续追错方向。

### 6. 本轮产出

| 件 | 内容 |
|:---|:---|
| 工具修复 | `tools/dump_class_ids.py`：结构化解码 + 去掉尺寸上限 + 按 HRESULT 排除 |
| 证据再生 | `evidence/class_ids.txt`：59 → 69 行 |
| KB 更新 | `kb/20_vtable_contract.md` §0/§3/§3.2/§3.3（新增工具陷阱一节） |
| INDEX | §B 表扩到 22 行，补 10 个核心类 |
| CONFLICTS | 新增 **G-10**（本线工具缺陷，10 类被漏） |
| 关闭悬项 | **L-17** |
| 新增纪律 | **#8**（op_str 不可用于取值；空集必须配肯定对照） |

### 7. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未启动 gamemd/ra2loader
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 只提交 `re_atlas/`
- [x] 无整段反汇编（片段均 ≤10 条指令）

---

## R-014 · 2026-10-21 20:4x — L-19 结清，并撤回"槽 4 = Load"

### 0. 心跳与进程检查

| 项 | 结果 |
|:---|:---|
| `tasklist` 查 `gamemd` / `ra2loader` / `game.exe` | **全无** |
| GOAL-3T 台账尾部 | 已读：在飞 = `--probe-frames` 早起帧 + `units0` 损失曲线 |
| 冲突 | 无。本轮只动 KB/INDEX/CONFLICTS/`re_atlas/tools` |

### 1. L-19 的答案

槽 3 / 4 / 5 / 6 / 13 **在 11 个触发器族 + `HouseClass` 上全部固定**：

| 槽 | 角色 | 是否被覆写 |
|---:|:---|:---|
| 3 | `GetClassID` | 全部覆写（各类写自己的 CLSID） |
| **4** | **`IsDirty`** | **11/11 全是同一个 `0x00410450`，无人覆写** |
| 5 | `Load` | 全部覆写 |
| 6 | COM `Save` | 全部覆写 |
| 13 | `AbstractClass::Save`（基类块） | 全部覆写 |

槽 4 的全引擎直方图：`0x00410450` 出现 **77 次**，是最高频值。
⇒ 槽 4 不随类变，因为它读的是基类字段，派生类无需覆写。

### 2. 撤回 7：槽 4 是 `IsDirty`，不是 `Load`

`kb/20_vtable_contract.md` 的未闭合表里我写"`vtable[4]` = `Load`"。**错。**

字节（`0x00410450`，全函数仅 6 条）：

```text
0x00410450  8B 4C 24 04   mov  ecx,[esp+4]
0x00410454  33 C0         xor  eax,eax
0x00410456  8A 51 20      mov  dl,[ecx+0x20]     ; Dirty
0x00410459  84 D2         test dl,dl
0x0041045B  0F 94 C0      sete al                ; ★ al = !Dirty
0x0041045E  C2 04 00      ret  4
```

**返回 `!Dirty`**，没有任何流参数或写操作 —— 这是 `IsDirty()`，不是 `Load`。
真正的 `Load` 在槽 5（派生类覆写，体首 `call 0x410380` 那个有流参数的包装）。

**为什么之前会错**：`kb/11_class_layouts.md` §6 的槽位表只写了
"槽 4 读 `+0x20` bool"，没定名；我在写 L-19 时按 YRpp 的**声明顺序**
（`GetClassID / IsDirty / Load / Save`）去想，把"第 2 个"对成了 `Load`，
实际应该是 `IsDirty`。**错误发生在"跳过一个"上**。

### 3. 顺带定名：槽 0–7 是 COM 八槽，顺序与 YRpp 一致

`QueryInterface / AddRef / Release / GetClassID / IsDirty / Load / Save / GetSizeMax`，
对应 `YRpp/AbstractClass.h:71,72,73,76,79,80,81,83`，逐一吻合。

槽 8 = 标量删除析构：`ret 4` + 返回 `esi`(this) + `test al,1` 决定 `operator delete`
⇒ YRpp 行 97 的 `~AbstractClass()`。

### 4. 新发现：槽 24 不是槽，是下一张表的 COL 指针

`0x7E1F50 + 0x60 = 0x7E1FB0`，值 `0x007FB160` 落在 `.rdata` ⇒ **不是代码**。
解出来是 `CompleteObjectLocator`：

```text
COL @0x7FB160  pTypeDescriptor = 0x8177E8
  TypeDescriptor @0x8177E8  name = ".?AVINoticeSource@@"
```

而 `0x7E1FB4`（正是 `+4`）的值是 `0x004C9150` —— 是代码。
⇒ `INoticeSource` 子表从 `0x7E1FB0`（含 `[-1]` COL）开始。

**判据**：槽值落 `.rdata` ⇒ 它是 COL 指针，表示"这里换表了"；别当虚函数。

`TEventClass` 同一位置的 COL 解出 `.?AVTextButtonClass@@` —— **无关的类**。
⇒ `.rdata` 里 vtable 的排布**不按继承关系相邻**，不能用"下一个 COL 是谁"推断接口列表。
`AbstractClass` 那条对上 `INoticeSource` 属巧合，不作证据。

### 5. 工具与证据

- 新增 `tools/dump_vtable_slots.py`：逐槽分类 `TEXT / COLPTR / ZERO`，
  `COLPTR` 自动解出 COL → TypeDescriptor → 类名。
- 证据 `evidence/vtable_slots.txt`，两次运行逐字节相同。
- **工具自身也踩了一次段边界坑**：我先用 `0x812000` 当 `.rdata` 上界，
  但 `.rdata` 实际是 `0x7E1000..0x811074`；而 COL 指向的 TypeDescriptor 在 `.data`
  （`0x812000..0xB79BE4`）。查名字时**两段都要接受**，否则只输出 `?`。
  已修，并在 docstring 写明。

### 6. 本轮产出

| 件 | 内容 |
|:---|:---|
| 新增 KB | `22_abstractclass_vtable_slots.md`（26 槽逐一定名 + COL 判据） |
| 新增工具 | `tools/dump_vtable_slots.py` |
| 新增证据 | `evidence/vtable_slots.txt` |
| INDEX | 新增 §C.0 槽位契约表 |
| 关闭悬项 | **L-19** |
| 撤回 | **7**（槽 4 = `IsDirty` 非 `Load`） |
| 新增存疑 | 槽 14/15 未定名（`or eax,-1` / `xor eax,eax`），不强行裁 |

### 7. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未启动 gamemd/ra2loader
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 只提交 `re_atlas/`
- [x] 片段均 ≤ 8 条指令

---

## R-015 · 2026-10-21 20:5x — R2-2 开局：INI 子系统类骨架

### 0. 心跳与进程检查

| 项 | 结果 |
|:---|:---|
| `tasklist` 查 `gamemd` / `ra2loader` / `game.exe` | **全无** |
| GOAL-3T 台账尾部 | 已读：仍在 `--probe-frames` / `units0` 线 |
| 冲突 | 无。本轮只动 `re_atlas/` |

### 1. 本轮做了什么

R2-1（触发器族）该收的字段已收得差不多，按 §3 优先级转入 **R2-2 INI 与规则加载**。
第一篇只做**类骨架**：`INIClass` / `CCINIClass` 的虚表、继承、静态全局。

### 2. 核心发现：`INIClass` 是多继承，RTTI 表与构造函数写的表不是同一张

- RTTI 表：`INIClass` = `0x7EA5F4`、`CCINIClass` = `0x7E1AF4`，**各 1 槽**（这次 RTTI 记账是对的）。
- 但**构造函数不写这两张表**：
  - `INIClass` ctor `0x4F2B66` 写 **`0x7EA624`**（→ `VectorClass<GraphicMenuItem*>`）
  - `CCINIClass` ctor `0x535AA0` 写 **3 个子对象 vptr**：
    `+0x0C`→`0x7E1B04`(GenericList)、`+0x10`→`0x7E1B0C`(GenericNode)、`+0x1C`→同上
- ⇒ `INIClass` 的第一个基类就是 `VectorClass<GraphicMenuItem*>`，YRpp 省略了这层。

### 3. 撤回语料错注：`0x887180` 是 `INI_Art` 不是 `RULESMD.INI`

6 处 `c7 05 <addr> f4 1a 7e 00` 证明 6 个全局被写成 `CCINIClass` 对象。
按 `YRpp/CCINIClass.h:288-296`：

```text
0x887048  INI_Rules   CCINIClass*   ← 指针！
0x887128  INI_AI      CCINIClass
0x887180  INI_Art     CCINIClass
0x887208  INI_UIMD    CCINIClass
0x8870C0  INI_RA2MD   CCINIClass
```

语料 `vxl_cache_layout.md:102` 把 `0x887180` 注成 `rulesmd.ini` **是错的**。
`INI_Rules` 是**指针**，要解引用一次；`INI_Art` 是对象，取址即 `this`。**两者不能混。**

**6 个地址全在 BSS**（≥ `0x0087E000`），磁盘无字节 ⇒ 地址→文件名只能以 YRpp 为准，标 `社区`。

### 4. 两次当场自纠

**自纠 1**：初稿写"`0x7E1B44` 是 `CCINIClass` 的 7 槽方法表"。
验 `[vt-4]` COL → `VectorClass<ScriptClass*>`，**与 INI 完全无关**。
错因：从 RTTI 表头往后找"连续 ≥4 个 `.text` 指针"的 run，那段恰好紧跟其后，
就默认是同类延续 —— **没验 COL**。

**自纠 2**：`0x887180` = `RULESMD.INI`（沿用语料注释）→ 实为 `INI_Art`。

两次都是"地址相邻/注释可信"的直觉错误，都已写进纪律。
教训是**先在 `kb/30` 里写了完整稿，验 COL 时才发现** —— 顺序应该是
"验 COL → 再写判读"，不是"写完判读 → 再顺手验一下"。

### 5. 新增纪律

- **#9**：RTTI 的 `slots` 是记账值，且 `.rdata` 里多张表首尾相接。
  按槽号遍历必须配"值落 `.text`"判据；判断归属必须验 `[vt-4]` 的 COL 名。
- **#10**：社区源（YRpp）与语料注释冲突时，**先查 YRpp 的静态地址声明**。
  本轮两处地址归属都是 YRpp 对、语料注释错。

### 6. 本轮产出

| 件 | 内容 |
|:---|:---|
| 新增 KB | `30_ini_subsystem.md` |
| CONFLICTS | **G-13**（`0x887180` 错注）、**G-14**（`.rdata` 相邻≠同类） |
| STATUS | R2-2 从 ⬜ 改为 🟢 类骨架完成 |
| 撤回 | **2 次当场自纠**（未提交进仓，但留痕在 KB §8 与本台账） |
| 新增纪律 | **#9 / #10** |
| 未闭合 | I-1…I-5 |

### 7. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未启动 gamemd/ra2loader
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 只提交 `re_atlas/`
- [x] 片段均 ≤ 10 条指令

---

## R-016 · 2026-10-21 21:0x–21:3x · R2-2 第二轮：`INISection`/`INIEntry` 布局 + 撤回 R-015 两条结构结论

### 1. 心跳与门禁

- `tasklist` 查无 `gamemd` / `ra2loader` ⇒ 可做完整分析（§8.3）。
- GOAL-3T 台账尾部：正在跑 `goal1_h1decay_20261021` 的 `--probe-frames` 早期帧路线，
  GLM 5.3 独立核验 `dwfrun-9fb1ccc3` 在飞。**渠道占用中 ⇒ 本轮不派子代理**。
- 未启动 gamemd/ra2loader；未写 `ra2youli`；未跑 trip；未编译；未改 `lead/`、`docs/re/`、
  `ra2render/`、`tools/`。

### 2. 本轮主线：`INISection` / `INIEntry` 节点布局（闭 I-4）

| 事实 | 值 | 证据 |
|:---|:---|:---|
| `INISection` 尺寸 | **`0x44`** | `0x00525DEA push 0x44` → `call 0x7C8E17` |
| `INIEntry` 尺寸 | **`0x28`** | `0x00526039 push 0x28` → `call 0x7C8E17` |
| `List<T>` 尺寸 | **`0x1C`** | `0x52ACE0` ctor + 尺寸复算等于 `0x44` |
| `INISection+0x0C` | `Name`（堆副本） | `0x00525E22`（`0x7D5408` strdup 返回值） |
| `INISection+0x10` | `List<INIEntry*>` 成员（`0x1C`） | `0x00525E2D` 写 `0x7EB744` |
| `INISection+0x2C` | `CheckedEntries`（`0x14`） | `0x0052B080`（ecx=`ebx+0x2C`）逐字段清零 |
| `INISection+0x40` | `Unknown_40` | `0x00525E44` |
| `INIEntry+0x0C` / `+0x10` | **`Key` / `Value`**（堆副本） | `0x00526079` / `0x00526087` |
| `INIEntry+0x14..+0x24` | 5 个 `unknown_*`（`+0x14/+0x18` 是堆指针，其余标量） | ctor 写入 + dtor `0x52AD50` 释放集 |

**与 YRpp 的对照**：`INIEntry` 7 个字段偏移**完全一致**；`INISection` 按
`Node(0x0C)+Name(4)+List(0x1C)+CheckedEntryList(0x14)+Unknown_40(4)=0x44`
逐字节吻合 `push 0x44`。

### 3. 本轮主要发现：节查找是 CRC32 排序数组，不是链表

`GetSection`（`0x526810`）查的是 `INIClass+0x28` 处一个 **8 字节元素**的排序数组
（`{u32 hash, INISection*}`），用 `0x52B750` 二分、`0x52B720` 比较器比。
哈希是**标准 CRC32**（表 `0x0081F7B4` 全部 256 项与 `0xEDB88320` 反射多项式生成表逐项相等；
`0x4A1FB0` 是更新步，`0x4A1DE0` 是其分块版本）。

比较器**只比哈希、不复核名字**，命中后也不做字符串复核 ⇒
**节名/键名大小写敏感**。这对编译器是硬约束：`[InfantryTypes]` ≠ `[infantrytypes]`。

**另一条易错点**：未命中返回 **`0xB7882C`**（BSS 共享空对象，19 处 `.text` 引用），
**不是 NULL**。任何"判 NULL 即不存在"的写法在本子系统里是错的（纪律 #13）。

### 4. 撤回（两次，均为 R-015 的结论）

**撤回 1：`INIClass : VectorClass<GraphicMenuItem*>`。**
`0x004F2B60` 是**析构函数**，写 `0x7EA624` 是析构时恢复基类 vptr。
`INIClass` 自己的表是 `0x7EA5F4`（单槽 = 析构 `0x004F2810`），
构造函数 `0x535AA0` 的 `0x00535B27` 写的正是它。→ CONFLICTS **G-15**

**撤回 2：`CCINIClass` 三基类多继承。**
`+0x0C/+0x10/+0x1C` 是**一个** `List<INISection>` 成员（vptr + First 哨兵 + Last 哨兵）。
→ CONFLICTS **G-16**

**外加一次"差点伪造的冲突"**：写 §9.4 时我把 `List<T>` 尺寸算成 `0x28`，
据此准备登记"YRpp 结构尺寸错"。复算发现正确值是 `0x1C`，YRpp **是对的**。
已在 KB §9.4 与 CONFLICTS **G-17** 留痕。

### 5. 新增纪律

- **#11**：`mov [reg], <vtable>` 在构造函数与析构函数里字节相同、语义相反。
  构造 = 清零串 + **最后**写本类 vptr；析构 = 先释放字段 + 写 vptr 后紧跟
  `test byte [esp+8],1` / `free(this)` / `ret 4`。
- **#12**：**"N 个 vptr" ≠ "N 个基类"**。模板容器实例含 1 个容器 vptr + 2 个哨兵 vptr。
  归属判据 = 找该容器的构造函数，看它对哪块内存做了同一组写。
- **#13**：本子系统"未找到"返回哨兵 `0xB7882C` 而非 NULL。

### 6. 本轮产出

| 件 | 内容 |
|:---|:---|
| 新增工具 | `tools/dump_ini_nodes.py`（正对照 `AbstractClass` 先行 + 256 项 CRC 表全比） |
| 新增证据 | `evidence/ini_nodes.txt`（133 行，两次运行字节相同） |
| 改写 KB | `30_ini_subsystem.md` §1/§3/§5/§8 重写 + 新增 §9 |
| CONFLICTS | **G-15**（撤回继承）、**G-16**（撤回多继承）、**G-17**（撤回"YRpp 尺寸错"） |
| 关闭悬项 | **I-1 / I-4 / I-5** 闭合，**I-2** 部分闭合 |
| 新增悬项 | L-24（`+0x3C`）、L-25（`CCINIClass` 尺寸）、L-26（`0x52B390` vs `0x52B430`）、L-27（dirty 语义）、L-28（见下） |

### 7. 悬项（末尾一条占位已在本轮当场修正）

> L-28 原拟为"`GetKeyName` 的 `+0x30` 是 Capacity 还是 Count"。本轮**已当场解掉**：
> `0x00526D4F mov ecx,[eax+0x30]` 后紧跟 `cmp edx,ecx` / `jge` 早退，
> `+0x30` 是**键数上界**（即 `Count`），不是容量。占位改记为 **已闭**，不留 L-28。

### 8. 禁区自查

- [x] 无游戏进程；无 ra2youli 写入；无编译；未启动 gamemd/ra2loader；未跑 trip
- [x] 未改 `lead/`、`docs/re/`、`ra2render/`、`tools/`
- [x] 只提交 `re_atlas/`
- [x] 片段均 ≤ 13 条指令（§3.2 最长）
