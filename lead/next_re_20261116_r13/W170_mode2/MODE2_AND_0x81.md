# W170 · BuildingClass 槽 73 mode 2 分支 + `[+0x81]` 字段语义（R13）

> 卡：W170-mode2｜Lead 派发｜2026-11-16｜纯静态（capstone 字节通道 + 一次 Ghidra `-noanalysis` 反编译），零真机、零活进程。
> 底座：先读 `R13_COMMON.md` 作废索引 → `R11_COMMON.md` → `R12_FACTS.md`；主台账已 grep（§664/§665/§666/§890/§914/§915）。

## 5 行摘要

1. **[已证]** mode 2 分支 `0x43F9A6..0x43FB08`（114 条可达指令、逐条打完无省略）**既不摘链也不挂链**；它从当前 cell、owner 索引数组与两个计时器算出值，写 `[this+0x700]` 与 21 个附属对象的 `+0xD4/+0xFC/+0x178`，建筑自身坐标只读。
2. **[静态推断]** mode 2 不是"传送/重设坐标"也不是"换外观/升级"，而是**附属子对象的派生状态同步**（cell 派生值 + 朝向字节的刷新）；不碰 grid 是因为**占格未变**，这只在"已放置后的运行期刷新"阶段合理。
3. **[已证]** `[+0x81]` 是 **bool 标志 = "已 Limbo / 不在世界中"**：`0x5F4D30` 摘链后置 1、`0x5F4EC0` 挂链前清 0、谓词 `0x5F5850` 见非 0 全模式空转；**不是**"已进入格子"（那是 `+0x74`），**不是**"已建成"。
4. **[已证]** `0x7014A0` = `TechnoClass::SetOwner(HouseClass*, flag)`（新 owner 写入 `[this+0x21C]`、迁移按型号计数），**不是**"设目的地/重定位/撤退"——与派发提示词的候选名不符，见 `DISAGREE.md`。
5. **[已证]** `[+0x81]` 字节写点双通道：capstone 全节 31 个对象字段写点、Ghidra 28 个（严格子集）；3 个 A-only 写点正落在 Ghidra 未建函数的孤儿区（`0x44EB7C/0x44EBD8/0x5438DB`），印证"两通道都依赖 atlas 会一起漏"的纪律。

---

## Q1 · mode 2 分支做什么？

### Q1.1 分支边界与 grid 负结果（逐指令，无省略）

入口 `0x43F9A6`，跳表 `0x43FB0C[2]=0x43F9A6`。线性反汇编从入口到 `ret 4 @0x43FB08` 共 **114 条指令**（与 Lead BFS 可达 114 一致）；紧随其后的 `0x43FB0B nop` 在 ret 之后、不计入，脚本因窗口多取 1 条而打印为 115 行。完整清单见 `EVIDENCE/Q1_mode2_branch.txt`（122 行、无 `...`）。

- **全分支 0 处** `call 0x5683C0`（挂链）/ `call 0x5687F0`（摘链）；与 Lead 的 BFS 可达 114 条、两者都不可达一致（§915-1）。
- **对建筑自身坐标字段（`+0x9C/+0xA0/+0xA4`）只读不写**：读发生在槽 `+0x1BC` 内部（`0x5F6960` 用它构造 CoordStruct）。
- 分支**唯一**对 `this` 的写入是 `mov word [edi+0x700], si`；其余写入都落在第三方对象（`[obj+0xD4]/[+0xFC]/[+0x178]`）与栈临时量。
- 末尾 `mov al,1 / ret 4` → 返回成功。

复跑：`cd work; python w170_channelA.py; type ..\EVIDENCE\Q1_mode2_branch.txt`

### Q1.2 四个虚槽在 BuildingClass 主表解析

`vt=0x7E3EBC, col_offset=0`（权威归属见 `_lead_audit/EVIDENCE_43F180_vtable.txt:27`）。`[vt+off]` 读 dword 得函数地址；atlas size 为十进制字节数。

| 调用点 | 槽号 | `[vt+off]` 地址 | 函数地址 | atlas size / n_instr | n_callers / is_fnptr |
|---|---|---|---|---|---|
| `call [edx+0x1E4]` | **121** | `0x7E40A0` | **`0x705D70`** | **138 B / 46** | 0 / 1 |
| `call [eax+0x1BC]` | **111** | `0x7E4078` | **`0x5F6960`** | **87 B / 27** | 0 / 1 |
| `call [edx+0x464]` | **281** | `0x7E4320` | **`0x456F80`** | **40 B / 11** | 0 / 1 |
| `call [eax+0x160]` | **88** | `0x7E401C` | **`0x41BF40`** | **53 B / 20** | 0 / 1 |

前几条指令与反编译见 `EVIDENCE/Q1_vt_slots.txt`、`EVIDENCE/ghidra_W170Dump.log:567-728`。

`[edi+0x294]` **不是虚槽**，是 `this` 的直接字段（一个关联对象指针；检查其 `+0x50` 是否回指 `this`，与台账 §666-3 `0x43FDEB` 的守卫同型），门控是否调用 `0x70E360`。

### Q1.3 逐槽语义猜测 + 依据

| 槽 | 语义猜测 | 等级 | 依据（关键字节/反编译） |
|---|---|---|---|
| `+0x1E4` → `0x705D70` | **owner 索引数组的查表取值**：返回 `[[[call [vptr+0x84]]+0xDF0)+4 + (Owner+0x16054)*4] + 0x30C`；owner = `this+0x21C`。值被写进 21 个附属对象的 `+0xD4`。 | **[已证]** 字节链；**[静态推断]** "owner 索引"命名 | `ghidra log:585-611`：`iVar3=*(int*)(param_1[0x87]+0x16054)`；`param_1[0x87]`=`+0x21C`（由 Q3 证为 HouseClass*）。`0x705D70` 有 2 处返回路径，均读 `+0x30C`。 |
| `+0x1BC` → `0x5F6960` | **`MapClass::GetCell(CoordStruct)`**：用 `this+0x9C/+0xA0/+0xA4`（建筑世界坐标）构造 CoordStruct，`ecx=0x87F7E8`（MapClass 单例），调 `0x565730` 两次；返回 `CellClass*`（越界时 `0xABDC50` 替身）。mode 2 随后读 `word [CellClass+0x10A]`。 | **[已证]** | `EVIDENCE/Q1_followup_disasm.txt` 全 27 条；`0x565730` 在 `0x56575C..0x56576F` 计算 `cell=(x>>8)+(y>>8)*512`，读 `[Map+0x13C][cell]` 得 CellClass*（`EVIDENCE/Q1_helpers.txt`）。 |
| `+0x464` → `0x456F80` | **cell 派生 16 位值的 ±500 偏置/回绕**：`if ([this+0xF0]&2){ if(arg>0x5DC) arg-=500; else arg+=500; } return arg`。输入正是上一步的 `[CellClass+0x10A]`（符号扩展 word）。 | **[已证]** 字节链；**[静态推断]** "朝向/层级归一化"用途 | `ghidra log:663-683`：`cmp al,2` / `cmp eax,0x5dc` / `add eax,0xfffffe0c`(-500) / `add eax,0x1f4`(+500)。 |
| `+0x160` → `0x41BF40` | **计时器"仍在进行"谓词**：`this+0x18C` = 起始帧(-1 表示无)、`+0x194` = 持续帧；`frame(0xA8ED84)-start < duration && 余量>0` → 1。 | **[已证]** | `ghidra log:688-724`：`cmp edx,-1` / `sub ecx,edx` / `cmp ecx,eax` / `setg cl`。`0x70E380/0x70E4B0` 用同型字段 `+0x198/0x1A0/0x1A4` 与 `+0x1B4/0x1BC/0x1C0`（`EVIDENCE/Q1_helpers.txt`）。 |

### Q1.4 判决（是传送？换外观？还是别的？）

**答：都不是——是"附属子对象的派生状态同步/刷新"。**

逐条排除与正面证据：

1. **不是"重设坐标/传送到新位置"** `[已证·负]`：建筑自身坐标 `+0x9C/+0xA0/+0xA4` 只被读、从未被写；分支内没有任何对 this 坐标/cell 字段的写入。写入只发生在 21 个附属对象的 `+0xD4/+0xFC`。
2. **不是"换外观/升级"** `[已证·负]`：无对 BuildingType/vptr/型号字段的写入；没有 `+0x520`（型号）或 art/type 相关写点。`+0x6ED` 读出的字节（==0xF 时经 `call [vptr+0x68](0,0)` 结果==5 改用 0x10）更像**朝向/门态编码**，不是外观 id。
3. **正面** `[已证]`：`0x43FA19 mov word [edi+0x700],si`；`0x43FA2A lea esi,[edi+0x55c]` + `0x43FA34 mov [esp+0x10],0x15` → 两个嵌套循环遍历 **21 个对象指针**，写 `[obj+0xD4]=槽+0x1E4 的值`、`[obj+0xFC]=cell/计时器派生值`、`[obj+0x178]=朝向字节`。`0x70E360 → 0x70E380/0x70E4B0` 是按 9 路跳表（`0x70E48C/0x70E574`）对计时进度插值的辅助函数。
4. **内部守卫** `[已证]`：`+0x160` 计时器未激活 **且** `[edi+0x294]` 空或其 `+0x50` 不回指 this → 跳过 `0x70E360`，直接用未插值值；这与 `0x43FB20`（BuildingClass::AI 同族函数）在 `0x43FDEB` 以 mode 2 调槽 73 前的守卫 `[esi+0x294]!=0 && [esi+0x294]+0x50==esi` 完全一致（`EVIDENCE/Q1_followup_disasm.txt`）。

**为什么不碰 grid** `[静态推断]`：这 21 个对象是建筑的**附属子对象**，其坐标/朝向是从建筑当前 cell 与动画计时**派生**出来的，本身不占格、不进 cell 链；建筑 footprint 未变 ⇒ 摘链/挂链都无意义且会破坏已有占用。放在建筑**已放置后的运行期刷新**阶段（动画推进、朝向变化、owner 变化后重算子对象状态）是合理的。mode 2 是 36 个常用 mode-2 站点（台账 §665）中"只刷新派生状态"的那类操作。

`[未证]`：`CellClass+0x10A` 的引擎级名字；`+0x55C` 那 21 个对象的类名；`+0x700` 的引擎级名字。下一条最有区分力的证据：在 Ghidra 里对 `0x43FA2A` 的 `esi` 做 pcode 指向分析，或用真机在 `0x43FA62` 读 `[obj]` 的 WhatAmI（本卡禁止真机）。

---

## Q2 · `[+0x81]` 是什么字段？

### Q2.1 全镜像写站点穷举（双通道）

通道 A：**不依赖 `function_atlas.tsv` 的 entry+size**——从 `.text` 节首 `0x401000` 逐字节线性反汇编（capstone `skipdata=True`，1,394,120 条指令 / 跳 66 字节），取所有 `op.size==1 && disp==0x81 && access&WRITE`，排除 `esp/ebp` 基址的栈局部量。

- `.text` 全部字节模式命中 **34** 个写点 → 排除 3 个栈写点（`0x4B771F/0x5D2F44/0x688E9B`）→ **31 个对象字段写点**。
- 通道 B（Ghidra `getInstructions`，独立指令模型）：对象写点 **28** 个；`onlyB=0`、**A ⊃ B 严格成立**；A-only 的 3 个正是 Ghidra 未建函数的孤儿区写点 `0x44EB7C / 0x44EBD8 / 0x5438DB`。

复跑：`python w170_channelA.py` → `EVIDENCE/Q2_plus81_census.txt`；`python w170_followup.py` → `EVIDENCE/Q2_AB_reconcile.txt`；`python w170_reclassify.py`（B 通道 W/R 重分类）。

**写 0 / 写 1 分布**：

| 类别 | 站点（节选；全表 `EVIDENCE/Q2_plus81_census.txt:7-41`） | 函数 |
|---|---|---|
| **写 1** | `0x5F4E9E`, `0x5F521C`, `0x5FD20F`, `0x6EB5D2`, `0x75F9CC`, `0x543A76`, `0x543B6B`, `0x44EB7C`, `0x44EC68`… | `0x5F4D30`(摘链后)、`0x5F4EC0`(放置失败)、`0x5FC570`、`0x6EB490`、`0x75F980` … |
| **写 0** | `0x5F4F4E`, `0x543805`, `0x543A1C`, `0x5811F8`, `0x5818E0`, `0x6E9423`, `0x75F912` | `0x5F4EC0`(挂链前)、`0x543780`、`0x543A10`、`0x581140`、`0x6E9140`、`0x75F8B0` … |
| **写寄存器** | `0x44EBD8`/`0x44ECC4`…(`bl`，保存后恢复)、`0x5F392A`(`al`)、`0x6E8B1A`(`bl`)、`0x74CC25`(`dl`) | `0x44EBF0` 等——典型"临时置 1、干完恢复"惯用法 |

写值集合只有 **{0, 1, 先前保存的同字节}**，从未出现 2 或更大 → **bool 标志**，不是多状态字节。

### Q2.2 读站点统计

- 通道 A：全部 238 次读 − 6 个栈读 = **232 个对象读点**；通道 B 204 个（严格子集）。
- 用法：绝大多数是 `mov al,[obj+0x81]; test al,al` / `cmp byte [obj+0x81],0` → **布尔判定**；`0x5F5850`、`0x7014A0`（3 次）、`0x5F4D30`、`0x5F4EC0` 等都以"非 0 即 veto"方式使用。
- 未见对 `+0x81` 做数值比较（除 0）、加减、位域拆分 → **不是状态字节**。

### Q2.3 与谓词 `0x5F5850` 的联合判决

`0x5F5850` 反编译（`EVIDENCE/Q2_predicate_5F5850.txt`，79 条全列）：

```
005F5854  mov al,[esi+0x81]; test al,al; jne 0x5F591D   ; ← +0x81!=0 ⇒ 全模式返回 0 空转
005F5866  mode==2: 要求 +0x80==0 且 +0x74!=0，再 call [vptr+0x134]
005F58EC  mode==1/3: 要求 +0x74==0，置 +0x74=1，call [vptr+0x134]
005F5908  mode==0: 要求 +0x74!=0，置 +0x74=0
```
→ `+0x74` 才是"在世界中/in-grid"锁存（mode 0 清、mode 1/3 置）；`+0x81` 是更上层的**硬否决**。

**决定性极性证据**（反编译 `EVIDENCE/ghidra_W170Dump.log:2083-2474`）：

| 函数 | 与槽 73 的关系 | `+0x81` 动作 | 语义 |
|---|---|---|---|
| `0x5F4D30`（多类共享 vt） | 入口 `+0x81!=0 → return 0`；内部 **`slot73(0)` 摘链** + `0x55BAE0` 注销 + 脏矩形 | **末尾 `+0x81=1`、`+0x80=0`** | **Limbo（移出世界）** |
| `0x5F4EC0`（多类共享 vt） | 仅当 `+0x81!=0` 才做 can-place；**`slot73(1)` 挂链**前 `set coords`、后 `0x55BAA0` 入册 | **挂链前 `+0x81=0`、`+0x80=0`** | **Unlimbo（放世界）** |

`0x7014A0` 同样以 `+0x81==0` 为门控，才执行 `slot73(0)` 与 `slot73(3)`（`ghidra log:1444-1456`）——对象在 Limbo 时两次都跳过。

### Q2.4 判决

**[已证] `+0x81 == 1` ⇔ 对象处于 Limbo（不在世界中 / 格链不跟踪）；`+0x81 == 0` ⇔ 在世界中。**

- **排除"已进入格子"**：进入格子由 `+0x74`  latch 表示，且 `+0x74` 由谓词随 mode 0/1/3 翻转；`+0x81` 是跨所有 mode 的硬否决，不是"在格"标志。
- **排除"已建成"**：`+0x81` 被 `BulletClass` 系列的 `0x5F4D30/0x5F4EC0` 使用（`0x7E47B8/0x7E47BC` 等虚表命中，见 `EVIDENCE/Q2_plus81_fn_ownership.txt`），子弹没有"建成"概念；且写值只有 0/1，无建造进度语义。
- **正向依据链**：摘链后写 1 → 挂链前写 0 → 谓词见 1 空转 → SetOwner 见 1 跳过摘挂，四条互相独立且方向一致。

复跑命令汇总：`python work/w170_channelA.py`；`python work/w170_ctx81.py`；`python work/w170_fn_ownership.py`；`python work/w170_reclassify.py`。原始输出全在 `EVIDENCE/`。

---

## Q3 · `0x7014A0` 的用途与"先摘后挂"

### Q3.1 函数身份（已证）

`0x7014A0` = `TechnoClass@@`(vt `0x7F4960`) **槽 245 (`+0x3D4`)**（`_lead_audit/EVIDENCE_7014A0_identity.txt:9`）。完整 321 条反汇编见 `EVIDENCE/Q3_7014A0_full.txt`；反编译见 `ghidra log:1278-1586`。

**它是 `TechnoClass::SetOwner(HouseClass* newOwner, bool flag)`**，决定性字节：

| 地址 | 指令 | 含义 |
|---|---|---|
| `0x7014A4` | `mov ebp,[esp+0x14]` | 取第 1 栈参数 = 新 owner |
| `0x7014AB/0x7014B1` | `mov eax,[esi+0x21c]` / `cmp ebp,eax` / `je 0x70188c` | 与当前 owner 相同则早退 |
| `0x701652/0x70165E` | `mov edx,[esi+0x21c]` / `mov [edx+0x548c],eax` | 改旧 owner 的登记字段 |
| `0x70163E/0x701646` | `inc dword [ebp+eax*4+0x53e4]` 等 | **新 owner 的按型号计数 +1** |
| `0x701735` | `mov [esi+0x21c],ebp` | **写入新 owner** |
| `0x701889` | `ret 8` | 2 个栈参数 |

另两处调用者均传 `(house, 1)`：`0x448BE8`、`0xDBF0A`（`EVIDENCE_7014A0_identity.txt:11-33`）。反编译中按 WhatAmI==1/2/0xF 与 ==6 分支更新 `[newOwner+0x53E4 + type*4]` / `[newOwner+0x5438 + type*4]`——典型的**所有权转移记账**。

### Q3.2 为什么先摘后挂，而不是直接改坐标

`[已证]` 序列严格是（`EVIDENCE/Q3_7014A0_full.txt:146-161`）：

```
0x701664  mov al,[esi+0x81]; test; jne 0x70167A     ; 在 Limbo 则跳过
0x701670  push 0 / call [edx+0x124]                 ; slot73(0) = 摘链（旧格）
0x70167C  call 0x70D4A0                             ; 遍历 TechnoClass::Array，重置关联对象
0x701681  mov al,[esi+0x81]; test; jne 0x701697
0x70168D  push 3 / call [eax+0x124]                 ; slot73(3) = 挂链（新 owner 下的格）
```

`0x70D4A0` 本体（`EVIDENCE/ghidra log 与 `_lead_audit/EVIDENCE_70D4A0.txt`）：遍历 `TechnoClass::Array`，筛出 `[esi+0x294]==this` 或 `[esi+0x2B4]==this` 的对象，对其调 `[vptr+0x1F8]`、`[vptr+0x2C]`（WhatAmI）、`[vptr+0x3C8](0)`，并在 WhatAmI==2 时清 `[+0xBC]` 与 `[+0x6D2]` —— 即**清算其它对象对本对象的引用缓存**。

`[静态推断]` 原因：换 owner 会改变 (a) 两个 HouseClass 的按型号计数（上面 `+0x53E4/+0x5438`），(b) `CellClass+0x100` 占用计数与格链上节点的归属语义（§890-5），(c) 其它 Techno 对"敌人/目标"的缓存引用。这些状态都挂在格链及交叉引用上；**直接改 owner 字段会留下旧 owner 的格节点与陈旧的交叉引用**。标准安全序列因此是：旧格摘链(mode 0) → 清算引用(0x70D4A0) → 新格挂链(mode 3)，与 §914-9「先摘后挂」惯用法一致；`+0x81` 门控保证 Limbo 中的对象不做无意义的摘/挂。

注：`push 3` 与 `push 1` 在 `0x43F180` 里是**同一跳表目标** `0x43F1E9`（§914），故这里用 3 与用 1 功能等价；全镜像仅此一处传 3（台账 §665-1）。

---

## 判决总表

| 项 | 结论 | 等级 |
|---|---|---|
| mode 2 = 传送/重设坐标 | **否**（自身坐标只读） | [已证·负] |
| mode 2 = 换外观/升级 | **否**（无 type/vptr 写） | [已证·负] |
| mode 2 = 附属对象派生状态刷新（21 个对象 +0xD4/+0xFC/+0x178） | **是** | [已证] 机制 / [静态推断] 命名 |
| mode 2 不碰 grid 的生命周期合理性 | 已放置后的运行期刷新，footprint 未变 | [静态推断] |
| `[+0x81]` = 已 Limbo / 不在世界中 | **是**（写1在摘链后、写0在挂链前、谓词硬否决） | [已证] |
| `[+0x81]` = 已进格 / 已建成 | **否**（前者是 `+0x74`；子弹也用 `+0x81`） | [已证·负] |
| `0x7014A0` = 设目的地/重定位/撤退 | **否** | [已证·负] |
| `0x7014A0` = `TechnoClass::SetOwner` | **是** | [已证] |

---

## LEAD_AUDIT

以下每条可只靠"地址 + 复跑命令"独立复算，不依赖本报告的文字。

**A1 · 四个虚槽解析（BuildingClass 主表）**
从 `0x7E3EBC` 起各偏移读 dword 应为：
`[0x7E40A0]=0x705D70`(138 B) · `[0x7E4078]=0x5F6960`(87 B) · `[0x7E4320]=0x456F80`(40 B) · `[0x7E401C]=0x41BF40`(53 B)。
复跑：`cd D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\work; python w170_channelA.py; type ..\EVIDENCE\Q1_vt_slots.txt`（第 5–8 行）。

**A2 · `[+0x81]` 对象字段写点 31（A）/ 28（B），A ⊃ B**
A 通道 34 总写 − 3 栈写 = 31；B 通道 28；`onlyB=0`；A-only 三处 = `0x44EB7C/0x44EBD8/0x5438DB`。
复跑：`python w170_channelA.py`（→ `Q2_plus81_census.txt` 头 40 行）；`python w170_followup.py`（→ `Q2_AB_reconcile.txt`）；`python w170_reclassify.py`（B 通道 28 写 / 204 读）。极性核验：`type ..\EVIDENCE\Q2_plus81_write_contexts.txt`，看 `=== 005F4E9E`/`=== 005F4F4E` 两段。

**A3 · `0x7014A0` = SetOwner**
`0x7014A4 mov ebp,[esp+0x14]`；`0x7014B1 cmp ebp,[esi+0x21C]`；`0x701735 mov [esi+0x21C],ebp`；`0x701889 ret 8`。
复跑：`python w170_channelA.py; type ..\EVIDENCE\Q3_7014A0_full.txt`（第 5/9/210/319 行）；反编译对照 `..\EVIDENCE\ghidra_W170Dump.log:1278-1586`。
