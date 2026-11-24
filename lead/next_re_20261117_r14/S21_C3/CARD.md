# S21-C3 · 按 **D-40** 补齐环③（**只做 5 行，不扩面**）

> ⚠️ **本卡的每一行都已由独立审计确认「只差 ③ 落笔」** —— 字节级证据已在审计 VERDICT 里给出，你的活是**把 ③ 写成可核查的合同**，不是重新普查。

## D-40 的 `[已证]` 最小环集（`lead\PENDING_DECISIONS.md`）
**① 入口 + ② 类属/身份 + ③ 整体合同 + ④ 使用见证，任一缺不得升。**
- **③ = 「这个函数整体做什么」** —— 读什么、写什么、返回什么、调用约定、错误路径。
- **③ 不可被「某处写了个字段」顶替**（那是当年 31 行虚高的根因）。
- 「清零 + 置默认值」这类**机械可述只算 P，不算 ③ 闭合**。

## 工作面：5 行（**以盘上为准自己核**）
| entry | 盘上 subsystem | 盘上 grade | 盘上 name |
|---|---|---|---|
| `00539760` | S21 | `[未证]` | `sub_00539760` |
| `0053AB50` | S21 | `[未证]` | `sub_0053AB50` |
| `0053AF40` | S21 | `[未证]` | **`PsyDom::Update`**（已有 YRpp 独立通道） |
| `00595740` | S21 | `[未证]` | `sub_00595740` |
| `00599650` | S21 | `[静态推断]` | `sub_00599650` |
🔑 **审计已给的 ③ 锚点（`S21_DIRECT\_audit\VERDICT.md` §4，可直接引用但须自己复核字节）**：
- `00539760` = `ScenarioClass::RecalcLighting`
- `0053AB50` = `UpdateLighting`
- `0053AF40` = `UpdateLighting`（**且有 YRpp `SuperClass.h` L190-191 的 `PsyDom::Update` 绑定**，是合法的第二条通道）
- `00595740` = `MapSeedClass::MapSeedClass`
- `00599650` = `MapClass::TryGetCellAt` / `GetWaypointCoords`
⚠️ 这 5 行的语义栏现在写的是「弱信号/模块线索/未证」⇒ **必须整栏重写**，否则行内自相矛盾（这正是 `a-S20-DIRECT` 拒行的理由）。
⚠️ `0053AF40` 已由 `M30` 命名为 `PsyDom::Update`（grade 仍 `[未证]`）⇒ **name 保持不动**，只补 ③ 与 grade。

## 每行必须产出（缺一不可）
1. **③ 整体合同**：用 2–4 句说清「它整体做什么」，**必须带指令偏移**（如 `+0x09 895E10` / `+0x16 E8…`）。
   审查标准：一个没看过这函数的人读完你的描述，能预测它对内存/全局的影响。
2. **④ 使用见证**：direct call（`E8` 指令边界 + `site+5+rel32==entry` + 非自环）**或** 活 vtable 槽位派发（构造器装的活表 + `vt[slot]==entry` + site 不共用）。给站点地址。
3. **② 类属**：RTTI 链 `[vt-4]=COL → [COL+0xC]=TD → TD+8 内联串`；**读不到 fail-closed 停下，不许猜**。
4. **新语义栏全文**（要替换盘上那一栏）：**不得**再出现「槽语义未证」「弱信号」「线索」「未定」等字样。

## ⛔ 严禁（本项目已因此回退 53 行）
- **不得只靠 direct call 就声称 `[已证]`** —— D-40 明写 ④ 单独不够；
- `atexit` 析构器装的虚表（`push <dtor>; call 0x7C978A`）不是活 vptr；
- 「entry 在自己虚表里是第 K 槽」的槽号匹配 / slot-baseline；
- 「P=R=100%」「恰命中 N」式判据自证；
- **随机基线必须按「同子系统内随机取同样多行」算**（S21 实测 35.66%；按「随机 VA 命中 target」算出的 0.166% 是**地址算术**，对语义零信息）。

## 强制自证
- **⑨ 停机核验**：盘上 n / grade / name 自己重算（数值见上表）。
- **⑲ 自检**：capstone 5.0.7 无 `op.index`（`op.mem.index`，无 index 返 **0 非 None**）。
- **扫描覆盖 `.text` 100%**（基准 **1,392,592 指令 / 68,253 `E8`@边界**，以 **VirtualSize** 为准；扫到 SizeOfRawData 会多 1,594 条零填充）。
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）—— 只报不改名。
- **`§8.5`**：`docs\re\` / `re_atlas\kb\` / 台账**不得作名字的第二条通道**。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21_C3\`
`PROGRESS.md`（≤50 行，**第一行写「补齐几行 ③」**）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S21), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`
  （**name 保持盘上现值不动**；只改 semantics + grade）
**开工 10 分钟内先落骨架；每完成 1–2 行增量落盘。严禁建 venv / pip install / import 其他卡 work 代码。**

## 核心数字
① 补齐 ③ 的行数（目标 5）② 每行的 ③ 摘要 + 指令偏移 ③ 每行的 ④ 站点 ④ 若某行补不出 ③，写清缺什么（**如实交 0 算合格**）