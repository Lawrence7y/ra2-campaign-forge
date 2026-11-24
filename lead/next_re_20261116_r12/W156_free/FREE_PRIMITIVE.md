# W156 · 对象注销/释放原语 与 ②-b 成因 B 判决

卡号 W156（R12）｜2026-11-16｜写域 `lead\next_re_20261116_r12\W156_free\`
全部结论基于**静态**读 `ra2youli\gamemd.exe`（SHA-256 `73201CC0…FCF67476`，ImageBase `0x400000`），
字节通道（capstone+pefile）+ Ghidra 12.1.4 反编译双通道独立取证。
**未启动游戏、未 attach、未改任何游戏文件、未改主台账、未 git commit。**

---

## 0 · 五行摘要

1. **注销+释放原语已定位** `[已证·Ghidra反编译]`：`0x459F20`（BuildingClass deleting destructor）= `call 0x43BCF0` + `if(flag&1) call 0x7C8B3D(free,this)`；`0x43BCF0` 调 `0x45AE10`/`0x45ADD0`（`DynamicVectorClass::Delete(index)`：`Count--`+元素前移）把对象从 BldArray/FootArray/AbsArray 移除。W152「找不到对象释放原语」被推翻。
2. **「写 [0xA8EB50] 的 8 个写者」是口径错误** `[已证·双通道]`：这 8 个函数全部是**读** Count 来遍历建筑数组（4 个查询/格式化 + 3 个 callee + 1 个构造器），真正写 Count 的只有构造器 `0x43BB18`（`inc`）和 NOFUNC 初始化 `0x4E6B91`（清零）；注销走 `ecx=0xA8EB40` 间接写 `[ecx+0x10]`，字节扫描看不到绝对地址写。
3. **真正的内存释放原语 = CRT `free` `0x7C8B3D`**（→ IAT `HeapFree` `0x7E127C`）。`HeapFree` **call 站点实测 3 处**（`0x7C9428/0x7CFAAC/0x7CFEA9`），台账 §654-1 的「4 处」错，W152 的「3 处」对。`DynamicVectorClass` 的缓冲也用 `0x7C8B3D` 释放。
4. **②-b 判决 = 静态不可判**（三选一第三项）`[已证·负面边界]`：已把"释放 BuildingClass"的原语钉死为 `0x459F20`，它**内部完全不调摘链**（284 条指令无 `0x5687F0`、无 `call [vptr+0x124]`）；摘链是独立入口（槽 73 mode0 → `0x43F180` → `0x5687F0`），靠上层显式 `Unlimbo(mode 0)` + 谓词 `0x5F5850` 放行。但 `delete building` 经虚表 deleting destructor 间接发生，静态无法枚举全部 delete 站点 ⇒ 不能断言"存在具体裸 delete 站点"，也不能断言"释放前必经摘链"。
5. **机制上「绕过」是可能的、且「调过≠摘过」已二次确证** `[已证]`：谓词 `0x5F5850` 独立反编译确认 `+0x81!=0` 或（mode0 且 `+0x74==0`）即返回 0，分派器直接退出、一个链节点都不动；而析构 `0x43BCF0` 无条件移出数组+free，不校验链状态。三条硬排除全部复核成立。

> 判决强度说明：本卡把 W152 的"静态不可判"从「找不到释放原语」（能力性不可判）升级为
> 「已找到释放原语、但 delete 经虚调用不可静态枚举」（原理性不可判），并给出该原语的完整地址与字节。
> 差距只差"一条 delete building 的调用链证据"，最小取得手段见 `UNKNOWNS.md` U1。

---

## 1 · 「写 [0xA8EB50] 的 8 个写者」定性表

### 1.1 双通道引用事实（命令见 §7）

| 通道 | 对 `0xA8EB50` 的引用 | 写站点 |
|---|---|---|
| capstone 字节扫描（atlas 边界内） | 54 处引用 | **1** 处：`0x43BB18` in `0x43B740` |
| Ghidra 引用模型 | total=55, R=53, W=2, C=0, D=0, distinctFns=25 | `0x43BB18`（fn `0x43B740`）+ `0x4E6B91`（**NOFUNC**，init 清零） |

两通道对账：差异 1 处 = NOFUNC 的 `0x4E6B91`（Ghidra 见、atlas 边界法漏），两者都确认**业务代码里只有构造器写 Count**。
`[0xA8EB44]`(Items) 的写：Ghidra W=2，均在 NOFUNC（`0x4E6B67` init、`0x4E6BC7` clear），业务代码 0 写。

### 1.2 8 个函数逐个定性

> 「8 个」来自 台账 §890-6 / W152 §6 的组合口径：4 个读 Count 的小函数 + 3 个 callee + 1 个构造器。
> **关键结论：8 个里没有一个做"从数组移除 + 释放内存"。**

| # | 函数 | 大小 | 对 Count 的操作 | 真实语义（Ghidra 反编译 `EVIDENCE/ghidra_core.log`） | 是否注销原语 | 等级 |
|---|---|---|---|---|---|---|
| 1 | `0x43B740` | 1456 | **W**（`0x43BB18` `inc`）+ R | BuildingClass 构造器；`Count++; Items[oldCount]=this`（`DynamicVectorClass::Add` 内联） | 否（登记侧） | `[已证]` |
| 2 | `0x44FE60` | 82 | R×2 | 遍历建筑数组，筛 `+0x81==0 && type+0x16BF==0`，对每个调 `0x44FEC0` | 否 | `[已证]` |
| 3 | `0x452D40` | 128 | R×2 | 遍历，筛 type+0x16be/`[0xA8E7AC]`/`+0x90`/`+0x81`，调 `0x452DC0(0/2/4/6)`+`0x4533A0(1)` | 否 | `[已证]` |
| 4 | `0x44FEC0` | 466 | —（callee） | `sprintf` 格式串 `s_s_s__d__d…`，把建筑描述写入 `FUN_00528660`（"Structures" 输出/地图工具） | 否 | `[已证]` |
| 5 | `0x452DC0` | 660 | —（callee） | 建筑放置/格子占位：`FUN_00452BB0`/`0x5657A0`(GetCell)/`0x47C520`，读 `+0x520/+0x5B8` | 否 | `[已证]` |
| 6 | `0x4533A0` | 1151 | —（callee） | 同类放置/占位逻辑 | 否 | `[静态推断]`（未逐指令反编译，据调用形态与 §5 同族） |
| 7 | `0x6D9B50` | 389 | R×2 | 空间查询，读 `+0x90/+0x80/+0x74` 三重门 | 否 | `[转引 W152 §6]`＋本次字节通道确认引用 |
| 8 | `0x6D9CE0` | 523 | R×2 | 空间查询，同上 | 否 | `[转引 W152 §6]`＋本次字节通道确认引用 |

**结论**：台账 §890-6「反编译这两个及其 callee，找'移出数组 + 释放'」这条路线**走不通**——目标函数根本不是注销路径。真正的注销在原语不在引用 Count 绝对地址的函数里（见 §2）。

---

## 2 · 注销 + 释放原语（本卡核心增量）

### 2.1 三件套（Ghidra 反编译，`EVIDENCE/ghidra_core.log` / `ghidra_dtor.log` / `ghidra_dtor2.log` / `ghidra_callers.log`）

```
0x459F20  deleting destructor (30 B):
    call 0x43BCF0
    if (flag & 1) call 0x7C8B3D(this)      ; free(this) — 释放对象自身

0x43BCF0  destroying destructor (986 B):
    ; 入口重设 4 个 vptr = 0x7E3EBC/EA0/E98/E90（BuildingClass 多继承）
    i = BldArray.vptr->FindIndex(this);  if (i!=-1) call 0x45AE10(i)      ; 0xA8EB40, FindIndex=slot4(+0x10)
    i = FootArray.vptr->FindIndex(this); if (i!=-1) call 0x45AE10(i)      ; 0x8B41E0
    ...
    i = 0xB0F5B8.vptr->FindIndex(...);   if (i!=-1) call 0x45ADD0(i)
    i = AbsArray.vptr->FindIndex(...);   if (i!=-1) call 0x45ADD0(i)      ; 0xB0F640
    ... call 0x7C8B3D(成员) ×2 ...       ; free 内部成员缓冲

0x45AE10  DynamicVectorClass::Delete(index) (47 B, ret 4):
    edx = [ecx+0x10] (Count); eax = index
    if (index < Count): dec edx; [ecx+0x10] = edx; while(++i<Count) Items[i-1]=Items[i]
    return 1
```

### 2.2 为什么字节扫描找不到 `dec [0xA8EB50]`

`0x45AE10` 写的是 `[ecx+0x10]`，`ecx`=数组对象基址（`0xA8EB40` 对 BldArray），
编译期不是绝对地址 ⇒ 对 `[0xA8EB50]` 的绝对寻址扫描天然 0 命中。
这解释了两通道在"写者"问题上的表面矛盾，也是 W152 判"找不到注销"的根因。

### 2.3 释放原语链（谁真正把内存交还系统）

```
对象/缓冲释放: 0x7C8B3D (CRT free)
   ├─ if 小块:  0x7CF7E8 (small-block free, → HeapFree 0x7CFEA9)
   └─ 否则:     HeapFree(IAT 0x7E127C)  ← 全镜像 3 个 call 点
分配对称侧:    0x7C946E (CRT malloc → HeapAlloc 0x7E1278, 5 个 call 点)
              0x4E95E0 = DynamicVectorClass::Resize → operator_new + free(旧缓冲)
```
`HeapFree` 3 个站点：`0x7C9428`(fn `0x7C93E8`) / `0x7CFAAC`(fn `0x7CF7E8`) / `0x7CFEA9`(fn `0x7CFE1C`)，全在 `0x7C93xx–0x7D0xxx` 静态 CRT 区。
**引擎对象自身不走 HeapFree 直调，而走 CRT `free 0x7C8B3D`**（二者最终都落到 HeapFree，但中间层是 CRT 堆）。台账 §667-2「引擎释放不走这两个导入」在"直接 call 点"层面成立。

---

## 3 · ②-b 成因 B 判决

### 3.1 三选一

> ## **静态不可判**（三选一第三项）

### 3.2 已证部分（把"不可判"的范围压缩到只剩一条）

1. `[已证]` 释放 BuildingClass 的原语 = `0x459F20`（deleting destructor）+ `0x43BCF0`；
   它**从实例数组移除自己**（`0x45AE10`/`0x45ADD0`）、**free 对象内存**，全流程 284+30 条指令
   **不含 `0x5687F0`、不含 `call [reg+0x124]`（槽 73）**。⇒ "释放"与"摘链"在代码里是**两个独立入口**，
   析构原语本身不保证摘链。
2. `[已证]` 摘链 `0x5687F0` 全镜像**仅 4 个直接调用点**，全在槽 73 mode 0 分派器内
   （`0x4151E0`/`0x43F180`/`0x4D3780`/`0x71BFB0`），Ghidra 引用模型 C=4、字节通道 4 处，一致。
3. `[已证]` 谓词 `0x5F5850`（本次独立反编译）:`+0x81!=0` → 返回 0；mode0 且 `+0x74==0` → 返回 0；
   否则 `+0x74=0`、返回 1。⇒ 即便上层"调用了 mode 0"，也可能一格不摘，且无错误码。

### 3.3 为什么仍是"不可判"而非"存在/不存在"

- **不能判"存在"**：要给出"释放 BuildingClass 而不先 mode0 调 `0x5687F0` 的具体站点"，
  必须枚举所有 `delete building`。`delete` 在镜像里经虚表 deleting destructor（本例 `0x459F20` 由槽引用）
  或 `call reg` 间接发生，静态调用图不可见（R11_COMMON §2-7 / §853-4）。本次 Ghidra 对 `0x43BCF0`
  只查到 **1 个直接调用者**（`0x459F20`），而 `0x459F20` 自身是被虚调用的 ⇒ 无法穷举上层 delete 站点。
- **不能判"不存在"**：同理，无法证明"每条 delete 前都必经 Unlimbo(mode0)"；而谓词空转机制
  使"调用了 mode0"也不等于"摘了链"，"必经调用"本身都不足以排除成因 B。

### 3.4 判据与最小补证

缺的证据：**一条 BuildingClass 被 delete 的完整调用链，含 delete 前后 `+0x74`/`+0x81` 与 6 格 `+0xE4` 的取值**。
最小手段（需 Lead 授权真机，本卡无授权）：建筑被摧毁瞬间同时读 `[obj+0x74]`、`[obj+0x81]` 与 6 格 `+0xE4`：
- `+0x74==0` 或 `+0x81!=0` → 谓词空转（成因 B 不需要存在，修法针对锁存/否决标志）；
- 两者正常但 6 格仍全指向 obj → 真裸 delete（成因 B 成立）；
- 6 格指向混乱 → C1 链污染（与成因 B 无关）。
纯静态的次优手段：用 Ghidra 的 "Calls to -> slot1 of BuildingClass vtable" 指向分析 + 对每个调用者做 mode0 前序数据流，
成本远高于单次真机读数。详见 `UNKNOWNS.md` U1。

---

## 4 · W152 三条硬排除复核

| 排除项 | 本卡独立复核 | 结论 |
|---|---|---|
| 第二个摘链实现不存在 | 字节通道扫非栈基址写 `[reg+0xE4/+0xE8]`：93 处 / 38 函数；带格上下文的仅 `0x47E8A0`(AddObject)/`0x47EA90`(RemoveObject)，与 W152 §2.1 一致 | **成立** `[已证]`（与 W152 数字口径不同：我 93 处/38 函数是"非栈基址写"口径，W152 136 处/65 函数是"全部同位移写"口径，两者都指向同一对函数） |
| `[0x87F924]` 367 读 0 写 | 字节通道 367R/**0W**；Ghidra 引用模型 387R/**0W**（差 20 = Ghidra 识别了 atlas 未覆盖区的读） | **成立** `[已证]`（W=0 是关键，两通道一致） |
| 三个分派器 mode0 都调 `0x5687F0` | `0x5687F0` 直接调用点 4 处：`0x4151E0`(槽143)/`0x43F180`(Building槽73)/`0x4D3780`(Foot槽73)/`0x71BFB0`(Terrain槽73)；三个槽73 分派器均在 mode0 分支调 | **成立** `[已证]` |

⇒ W152 三条硬排除全部复核成立，无翻案。

---

## 5 · 三级标签汇总

- `[已证]`：8 个写者定性（6/8 直接反编译，2/8 转引+引用确认）；HeapFree=3；注销原语三件套；谓词语义；三条硬排除；双通道引用计数。
- `[静态推断]`：`0x4533A0` 语义（未逐指令）；`delete` 经虚调用不可枚举。
- `[未证]`：是否存在具体"裸 delete building"站点（= 成因 B 判决为不可判的那一条）；真机 `+0x74/+0x81/+0xE4` 现场值。

---

## 6 · 与既有结论不符（详见 `DISAGREE.md`）

1. 台账 §654-1「HeapFree 4 处」→ 实测 **3 处**。
2. 台账 §890-6 / W152 §6「写 `[0xA8EB50]` 的函数 8 个」→ 这 8 个全是**读** Count；真正写 Count 的业务站点只有构造器 1 处（+NOFUNC init 1 处）。
3. W152 §5.1「找不到对象释放原语、找不到析构函数」→ 原语 `0x459F20/0x43BCF0/0x45AE10` 已找到；槽 0（`0x410260`）确非析构（这点 W152 对），但析构在 `0x43BCF0`，被 deleting destructor thunk `0x459F20` 调用——W152 因只查槽 0 而漏。

---

## 7 · 证据与复跑命令

全部原始输出在 `EVIDENCE/`，脚本在 `work/`。每个数字的产出命令：

```powershell
cd D:\Project\ra2-campaign-forge

# 字节通道：写 [A8EB50] 站点、HeapFree IAT call、87F924 读写、5687F0 调用点、cell+E4/E8 写
cd lead\next_re_20261116_r12\W156_free\work
python w156_scan.py            > ..\EVIDENCE\scan_byte_channel.log 2>&1
python w156_dump5.py           > ..\EVIDENCE\dump5_capstone.log 2>&1
python w156_dump_4e6b.py       > ..\EVIDENCE\dump_4e6b.log 2>&1
python w156_array_writes.py    > ..\EVIDENCE\array_writes.log 2>&1
python w156_dump_reg.py        > ..\EVIDENCE\dump_reg.log 2>&1
python w156_dump_absdel.py     > ..\EVIDENCE\dump_absdel.log 2>&1
python w156_dtor_scan.py       > ..\EVIDENCE\dtor_scan.log 2>&1

# Ghidra 通道（-noanalysis，输出重定向，未用 Select-Object 截断）
$bat='D:\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat'
$proj='D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_ghidra\W156'
$sp='D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W156_free\work'
& $bat $proj gamemd_auto -process gamemd.exe -noanalysis -scriptPath $sp -postScript W156Core.java    *> ..\EVIDENCE\ghidra_core.log 2>&1
& $bat $proj gamemd_auto -process gamemd.exe -noanalysis -scriptPath $sp -postScript W156Vt2.java     *> ..\EVIDENCE\ghidra_vt2.log 2>&1
& $bat $proj gamemd_auto -process gamemd.exe -noanalysis -scriptPath $sp -postScript W156Final.java   *> ..\EVIDENCE\ghidra_final.log 2>&1
& $bat $proj gamemd_auto -process gamemd.exe -noanalysis -scriptPath $sp -postScript W156Dtor.java    *> ..\EVIDENCE\ghidra_dtor.log 2>&1
& $bat $proj gamemd_auto -process gamemd.exe -noanalysis -scriptPath $sp -postScript W156Dtor2.java   *> ..\EVIDENCE\ghidra_dtor2.log 2>&1
& $bat $proj gamemd_auto -process gamemd.exe -noanalysis -scriptPath $sp -postScript W156Verify.java  *> ..\EVIDENCE\ghidra_verify.log 2>&1
& $bat $proj gamemd_auto -process gamemd.exe -noanalysis -scriptPath $sp -postScript W156Callers.java *> ..\EVIDENCE\ghidra_callers.log 2>&1
```

---

## LEAD_AUDIT（独立可抽验的核心数字）

> 以下三项请用独立脚本复算，不复用本卡代码。

1. **写 `[0xA8EB50]` 的站点清单（双通道）**
   - 期望：字节通道（atlas 边界内）**1 处**=`0x43BB18`，字节 `89 0d 50 eb a8 00`（`mov [0xa8eb50],ecx`），归属 `0x43B740`。
   - Ghidra 引用模型 W=**2**：`0x43BB18` + `0x4E6B91`（NOFUNC，字节 `a3 50 eb a8 00` = `mov [0xa8eb50],eax`，init 清零）。
   - 对 `[0xA8EB50]` 全部引用：Ghidra total=**55** R=53 W=2 distinctFns=**25**；字节通道 54。
   - 抽验命令：`python w156_scan.py`（§(1)(1b)）+ Ghidra `getReferencesTo(0xA8EB50)`。

2. **`HeapFree` IAT（`0x7E127C`）call 站点 = 3**
   - 期望站点：`0x7C9428`、`0x7CFAAC`、`0x7CFEA9`（字节形态 `ff 15 7c 12 7e 00`）。
   - 反驳台账 §654-1 的"4 处"。对照：`HeapAlloc 0x7E1278` = **5** 处（与台账一致，证明扫描口径可信）。

3. **注销/释放原语字节序列与调用关系**
   - `0x45AE10`（Delete index）关键字节：`4a 89 51 10`（`dec edx; mov [ecx+0x10],edx`）+ 前移循环 `8b 34 82 / 89 74 82 fc`。
   - `0x43BCF0` 调 `0x45AE10` 于 `0x43BD95`（`e8 76 f0 01 00`）与 `0x43BDBC`（`e8 4f f0 01 00`）；
     调 `0x7C8B3D`(free) 于 `0x43C083`/`0x43C0AB`。
   - `0x459F20`（deleting destructor，30 B）= `call 0x43BCF0` + `call 0x7C8B3D`；Ghidra 查 `0x43BCF0` 直接引用仅 **1** 处（`0x459F23`）。
   - 关键否定证据：`0x43BCF0` 全 284 条指令中 `0x5687F0` 引用数 = **0**、`[reg+0x124]` 引用数 = **0**（判"析构不摘链"的锚点）。
