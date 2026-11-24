# S17-K2 · DOD 对账表（按 `PLAN_R14_SUSTAINED.md` §1 六条逐条）

> 口径权威：`COVERAGE\PANEL.md`、`coverage_README.md`；分母约定 `R14_COMMON.md` §9。
> 本卡性质：定点补缺口卡（T1 靶子清点 + T2 命名 7 行 + T3 提级 4 行），**不创建 KB 文件、不改 `COVERAGE\coverage.tsv`**。

---

## 第 1 条 — ≥90% 有名字与一行语义，且 ≥50% 达 `[已证]`

| 口径 | 分母 | named 前→后 | proved 前→后 | 门槛 | 结果 |
|---|---:|---:|---:|---|---|
| **atlas 内（下界，PANEL 列）** | 102 | 85 (83.33%) → **92 (90.20%)** | 49 (48.04%) → **53 (51.96%)** | ≥90% / ≥50% | **PASS**（named +7、proved +4） |
| **全 coverage.tsv** | 104（含 2 atlas 外行） | 87 (83.65%) → **94 (90.38%)** | 49 (47.12%) → **53 (50.96%)** | ≥90% / ≥50% | **PASS**（named +7、proved +4） |

- 分母实测：脚本 `work\t1_filter.py` 读 `COVERAGE\coverage.tsv` 全 14,495 数据行筛 `subsystem==S17` 得 104 行，再与 `function_atlas.tsv` 12,916 entry 求交得 102 行。**与 PANEL.md S17 行（102/85/49）逐位一致 ⇒ 无 DISAGREE**。
- `named_pct` 定义：`name` 非 `sub_XXXXXXXX` 且非空；`proved_pct` 定义：`grade == [已证]`。
- 前置条件：本卡只交 `coverage_delta.tsv`（7 行），须由下张 M 卡合入 `coverage.tsv` 才生效；上表 AFTER 列为 `work\verify_dod.py` 的合并模拟，原始输出 `EVIDENCE\DOD_RECOMPUTE.txt`。
- 复算命令：`python work\t1_filter.py && python work\verify_dod.py`（两脚本只读输入）。
- **未用凑数**：4 条 `[已证]` 全部有字节级双证（RTTI slot13＋call 410410 ／ 调用已知 S17 原语），无「证据文件含该地址」式弱判据。

## 第 2 条 — 核心类完整字段布局（偏移/类型/读写者）+ `GetSize` 一致

- **本卡不主攻字段布局**（那是 K 布局卡职责）。S17 涉及的 `SwizzleManagerClass`（vptr `0x7F4108`，10 槽，实例 0x34）与 `CStreamClass`（IStream 包装）的字段布局已在 `re_atlas\kb\21_swizzle_and_object_fields.md` 与 S17-F1 存档中给出。
- **GetSize 类校验**：本卡 7 行中无 `B8 imm32 C3` 型 GetSize 候选；未把 `0x4C9150`（`33 C0 C3` 抽象基类共用桩）当任何类的 GetSize（§971）。
- **跨类偏移纪律**：唯一使用的字段 `[this+0x10]`（count）/`[this+0x14]`（array）只属 0x4B6BB0 自身循环，未跨类套 `+0x94/+0x184/+0x80`。
- 结论：**本条不在本卡 DoD 通过范围（部分支撑，非本卡产物）**；交 K 布局卡继续。

## 第 3 条 — 关键数据流调用链图（入口 → 每帧更新 → 销毁/存档）

**引用已入账 §946/§948 存档/读档顺序，标明复核一致 vs 新增：**

| 环节 | 实址 / 顺序 | 来源 | 状态 |
|---|---|---|---|
| 存档总入口 | `Game_Save_Outer 0x67CEF0` → `Save_Core 0x67D300` | §946 S17-F1 已入账 | **复核一致**（本卡 T1 靶子表含此二行，grade 已证、语义不变） |
| Save_Core 内部 | 35 模板块（`0x67FDF0+0x80·i`）+ 28/29 内联向量块 + 标量块 S-1 | §946（35/35 类名全可定；审计 §2b 改 28→29） | **复核一致**（本卡未改这些行） |
| 读档入口 | `Load_Core 0x67E440`（749 B，1 处 IStream::Read）；`0x67E730`（4258 B，1660 指令，50 处读）为另一函数 | S17-F1 `_audit\VERDICT.md` 必改 3（审计订正） | **引用已入账订正**，非本卡新结论 |
| Swizzle 复位 | `Here_I_Am 0x6CF240`(slot4) / `Here_I_Am3 0x6CF2C0`(slot6) → `Reset 0x6CF350`(slot3 经 thunk `0x6CF230`) | §946 / kb/21 | **新增挂接**：本卡 T3 把 0x55AAC0/0x4B6BB0 的 swizzle 注册调用点挂到该链（见 `EVIDENCE\T2_T3_EVIDENCE.txt` E4/E6） |
| 保存原语 | `IStream::Write [vptr+0x10]` / `IStream::Read [vptr+0xC]` = CStreamClass slot4/slot3 | §946 + CStreamClass vtable `0x7E5D94` RTTI（本卡 E5 复核） | **新增复核**：0x67C690/0x539AE0/0x55AAC0 三行挂到该原语 |

**调用链图（本卡确认的部分，存档方向）：**
```
Game_Save_Outer 0x67CEF0 ──E8──> Save_Core 0x67D300
    ├── E8 ──> AirstrikeClass::Save 0x41D6E0 ──E8──> AbstractClass::Save 0x410410   [NEW 本卡]
    ├── E8 ──> NeuronClass::Save   0x43A5D0 ──E8──> AbstractClass::Save 0x410410   [NEW 本卡]
    ├── swizzle 注册: Swizzle_RegisterPointerArray 0x4B6BB0 ──E8──> Here_I_Am 0x6CF240 [NEW 本卡]
    ├── Load_SwizzledObject 0x55AAC0 ──E8──> Here_I_Am3 0x6CF2C0 / Here_I_Am 0x6CF240 [NEW 本卡]
    └── Load_COM_ObjectVector 0x67C690 ──IAT──> ole32!OleLoadFromStream 0x7E15F8 [NEW 本卡]
```
- **本卡新增**：7 行中 5 行有 E8/IAT 直连已知原语（见图中 `[NEW 本卡]`）；**复核一致**：Game_Save_Outer/Save_Core/Swizzle 原语本体未改。

## 第 4 条 — INI 键与全局变量表

- 本卡涉及的全局变量（逐字节实测）：`0xB0C110` = `SwizzleManagerClass::Instance`（kb/21）；`0xA8ED84` = CurrentFrame（S17-F1 N4，Neuron Save 帧差读点）；`0x7E15F8` = ole32!OleLoadFromStream（IAT）；`0x7F7C90` = IID_IPersistStream；`0x89F75C` = COPYPROTECTION 映射基址（本卡判为非 S17）。
- INI 键：本卡未触及（存档/读档不读 INI 键）；`WChat\SysID` 是注册表键（`0x49F8B0`），**非游戏 INI 键且非 S17**，见 `DISAGREE.md`。
- 结论：**全局变量表本卡有增量，INI 键无增量**。

## 第 5 条 — 真机验证（≥2 条关键运行时事实）

- **S17 真机卡现状**：`STATUS_BOARD.md` LIVE_QUEUE 第 4 项 `S17-V1`（S17 存档）为 **WAIT_DEP**（前置 S17-F1 已入账 §946），**但本轮 STATUS_BOARD 仍未把它从 WAIT_DEP 提为 RUNNING**；即 **S17 尚无真机卡交付**。
- 本卡性质为静态定点卡，**不启动真机、不动 LIVE_LOCK**。
- 缺什么：S17-V1 未派发/未取 `LIVE_LOCK`；真机至少需验证 2 条关键运行时事实，候选（依据本卡静态证据）：
  1. 存档时 `0x4B6BB0` 循环注册指针数组后 `[this+0x10]` 个字段被 Here_I_Am 清零（kb/21 §0.1 已静态证，缺真机）；
  2. `0x67C690` 的 OleLoadFromStream 循环次数 = `IStream::Read` 读出的 count（本卡 E5，缺真机）。
- 结论：**本条未通过（真机卡缺位），需另立 S17-V1 并取锁**。

## 第 6 条 — `KB\Sxx_<名称>.md` 交付 + 异族审计 + 台账结题节

- `re_atlas\kb\00_INDEX.md` §E 显示 **22 个子系统全缺** `KB\Sxx_<名称>.md`（现仅 00/10/11/20/21/22/30 等通用篇，无 S17 专篇）。
- **本卡不创建 KB 文件**（派卡明示），仅在 `UNKNOWNS.md` 标记缺口。
- 台账：S17-F1 已入账 §946（PARTIAL，35/35 类名全可定）；本卡待审计后由 Lead 起新节。
- 结论：**本条未通过（KB S17 专篇缺位）**，属全局缺口非本卡产物。

---

## 汇总

| 条 | 本卡是否通过 | 说明 |
|---|---|---|
| 1 | **PASS** | 双口径均跨 90%/50%（atlas 90.20/51.96；full 90.38/50.96） |
| 2 | 部分（非本卡产物） | 字段布局/GetSize 归 K 布局卡；本卡未违规 |
| 3 | **部分 PASS**（本卡有新增） | 调用链图已给 5 条新增 E8/IAT 直连；余沿用 §946/§948 |
| 4 | 部分 | 全局变量有增量；INI 键无 |
| 5 | **FAIL（缺真机卡）** | S17-V1 仍 WAIT_DEP，需另立卡 |
| 6 | **FAIL（缺 KB）** | 22 子系统全缺，本卡按令不创建 |
