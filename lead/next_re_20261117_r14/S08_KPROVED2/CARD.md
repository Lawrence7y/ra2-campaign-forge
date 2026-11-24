# S08-KPROVED2 · S08 按 **D-42 ③b** 升 proved（目标 8 行）

## 盘上现态（Lead 实测 2026-11-18 18:1x，atlas∩coverage）
`S08`：**n=22、named=20（L 口径达标）、proved=3**，门槛 **11** ⇒ **差 8**。
`[静态推断]` **19 行**、`[未证]` 0。
19 行构成（Lead 已列）：`0040D250`（`MouseClass::vslot43`）｜`0045A070` `0045A0A0` `0045A0C0` `0045A640` `0045A680` `0045A730` `0045AB00` `0045AB50` `0045AC00` `0045AC30` `0045AC70` `0045AC90`（13 个 `FoggedObjectClass` 容器槽）｜`004D24A0` `004D2510` `004D27B0` `004D27D0` `004D2810` `004D2910`（6 个 `FoggedObjectClass::slotN`）。
⚠️ 提示：容器族槽位可参照 `R14_COMMON §8.4` 的 slot→method 映射表（slot1 `operator==` / slot2 `SetCapacity` / slot3 `Clear` / slot4 `FindItemIndex` / slot5 `GetItemIndex` / slot6 `GetItem`）—— **但映射表只给候选名，不能替代 ③b 与 ④**。

## 唯一任务：把 ③b 成立的行升 `[已证]`，目标 **8 行**

## 🔴 判据（`R14_COMMON §8.6`，**逐条照做，不得简化**）
**`[已证]` 最小环集 = ① 入口 + ② 类属/身份 + ③ 整体合同 + ④ 使用见证，任一缺不得升。**

### ② 类属（两种通道，任选其一）
1. **RTTI 链**（默认）：`[vt-4]=COL → [COL+0xC]=TD → TD+8 内联串`，且 `vt[slot]==entry`。**读不到 fail-closed，不许猜**。
2. **YRpp 地址绑定 + 字节逐项吻合**（**无虚表时唯一合法通道**）：`YRpp\` 的 `CALL(0x…)`/`JMP_THIS(0x…)` 原文行 + 该函数体内**实测逐项吻合** YRpp 声明的成员/偏移/常量。
   - ⚠️ **D-41**：无虚表函数（静态成员/自由函数/CRT/全局静态 ctor）**② 物理不可用 RTTI** ⇒ 只能走通道 2。**走不通就不升**（当前默认 (A)）。

### ③ 整体合同（**两档，只认 ③b**）
**③b 满足任一即可**：
① **跳表 / switch 多路分支**且每路可核 —— **或「多路守卫链」（≥3 道互斥闸且各闸动作不同）**；
② **可证伪的错误码 / 返回约定**（如 `GetLastError → 返回 −1`）；
③ **内存形状断言**（**≥2 张 vt 写 或 ≥10 个字段布局断言**）；
④ **完整循环 I/O**（读→判→写→推进，带边界检查）。

**③a（不升）**：单次调用 + 单次写、纯转发桩、清零 + 置默认值、无分支线性流程、**构造器薄壳**（单次基类调用 + 单张 vt 写）。

### ④ 使用见证
`direct call`（`E8` 指令边界 + `site+5+rel32==entry` + **调用者 ≠ 本行体内**）**或** 活 vtable 槽位（**构造器**装的活表 + `vt[slot]==entry` + site 不被多行共用）。
⚠️ **`atexit` 析构器装的虚表不算活 vptr**（`push <dtor>; call 0x7C978A`）。

## ⛔ 严禁（本项目已因此回退 53 行）
- **只靠 direct call 就升**（④ 单独不够）；
- 槽号匹配 / slot-baseline / 「entry 在自己虚表里第 K 槽」；
- 「P=R=100%」「恰命中 N」式判据自证；
- **单点推断当闭合**（如「常量返回 = 对象大小」—— 单点吻合不是双点闭合）。

## 强制自证
- **随机基线必须按「本子系统内随机取同样多行」算**（不是随机 VA 命中 target —— 那是地址算术，`a-S21-DIRECT` 实测差 200 倍）。
- **差分检验**：weak（仅 ④）vs strong（④ + ③b）的差集行数要报出来。
- **⑨ 停机核验**：盘上 n / proved / `[静态推断]` / `[未证]` 自己重算。
- **⑲**：capstone 5.0.7 无 `op.index`（`op.mem.index`，无 index 返 **0 非 None**）。
- **扫描覆盖 `.text` 100%**（基准 **1,392,592 指令 / 68,253 `E8`@边界**，以 **VirtualSize** 为准）。
- **⑱**：按 entry 查全库冲突（**6 位与 8 位两种写法**）。

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED2\`
`PROGRESS.md`（≤50 行，**第一行写「升了几行 / 最多几行」**）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S08), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`
  （⚠️ **name 保持盘上现值不动**；语义栏必须写 ③b 条件 + 指令偏移，**不得含「未定/弱信号/线索/槽语义未证」**）
**开工 10 分钟内先落骨架；每完成 2–3 行增量落盘。严禁建 venv / pip install。**

## 核心数字
① 升 `[已证]` 行数（目标 8）② 每行的 ② 通道与 ③b 条件 ④ 随机基线与差分 ⑤ 并入后 S08 proved
