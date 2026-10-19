# W3-Z2 派工单 · **`Size()` 常量是否等于真实对象分配尺寸**（Q1 的另一半）

> ⚠️⚠️ **卡面重大更正（2026-10-02 02:09，Lead · 立刻生效）**
>
> **本卡立项时的前提已被推翻：Q1 的另一半已由前一张卡（ZCode S7）在 02:04 闭合。**
> S7 修好判据后给出（`yr_delta8/raw/step03_alloc.txt` 8,201 B）：
> ```
> DriveLocomotionClass   Size()=112 (0x70)
>     ALLOC  push 0x70   ; call 0x782017   (before `call 0x49F640` at 0x69626C)
> DropPodLocomotionClass Size()=48  (0x30)
>     ALLOC  push 0x30   ; call 0x782017   (before `call 0x4A5A40` at 0x696B6C)
> FlyLocomotionClass     Size()=96  (0x60)
>     ALLOC  push 0x60   ; call 0x782017   (before `call 0x4BC110` at 0x696CEC)
> HoverLocomotionClass   Size()=120 (0x78)  …
> ```
> **⇒ `push <Size() 常量>` → `call 0x782017`（operator new）→ `call <该类构造函数>`。分配尺寸就是 `Size()` 常量。**
>
> **🔴 并更正 Lead 在本卡 §3.1 里的一个错误假设**（`E-W3-24`）：
> 我写「**很可能不是 `push imm`，而是"先取 `Size()` 返回值再当参数"**」—— **错了**。
> **真正的修正是"换锚点"，不是"换形态"**：**形态① `push imm` 本来就对；错的是原先要求它必须出现在"主表 vtable 写入的 64 字节内"，而实际位置在 `call <构造函数>` 之前。**
>
> ---
> ## ⚠️ 因此本卡的任务**改为**（其余纪律与交付格式不变）
>
> **不再重新推导"是否存在分配点"，改为对 S7 的结论做【独立复核】，并把它推得更硬：**
>
> ### 任务 A · **独立复现分配点**（**不得复用 S7 的脚本**）
> 自己写扫描器，对**全部 10 个 Locomotion 类**（两侧）找出：
> ```
> 形态：push <imm> ; call <X> ; [之间若干指令] ; call <ctor>
> 要求：①<imm> == 该类的 Size() 常量  ②<ctor> == 该类的构造函数（用 vtable 写入或 YRpp JMP_THIS 判）
> ```
> **逐类给出：`类名 / Size() 常量 / push 处的 VA / call 的目标 VA / ctor 的 VA / 三者是否自洽`。**
> **并给出 `call 0x782017` 那是个什么函数**（查它是不是 CRT `operator new` / `??2@YAPAXI@Z`；**贴出它的前 10 条指令**）。
>
> ### 任务 B · **两侧对拍（这是本卡的核心增量）**
> **`Jumpjet`（144→152）与 `Rocket`（88→96）在 gamemd 侧的 `push imm` 立即数是多少？**
> - 若为 **`0x98` / `0x60`** ⇒ **分配点随 `Size()` 一起 +8** ⇒ **两处独立证据同向，Q1 两侧完全闭合**
> - 若仍为 `0x90` / `0x58` ⇒ **分配尺寸未变而 `Size()` 变了** ⇒ **这是一个重大发现**，须单独成节
> **⇒ 这一条是本卡唯一"必须做出来"的东西。**
>
> ### 任务 C · **边界与反例检查**
> 1. **是否存在与 `Size()` 常量不等**的分配形态（例如某类 `push` 了别的立即数）？**若有，如实列出。**
> 2. **`LocomotionClass`（抽象基类，`Size()=0`）是否真的没有分配点**？（**"没有"与"未找到"必须区分**）
>
> ---

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包，先整篇读卡。

## 0. 一句话背景

前一张卡（ZCode S7）已把 **`Size()` 的常量侧**钉死，两侧一致、且被第二方独立复现：
```
主表 v_main[9] = Size()，函数体为 `mov eax, imm32; ret`
Drive=0x70(112) DropPod=0x30(48) Fly=0x60(96) Hover=0x78(120) LocomotionClass=0(抽象)
Jumpjet: game 0x90(144) → gamemd 0x98(152)      ★ +8
Mech=0x34(52) Rocket: game 0x58(88) → gamemd 0x60(96)  ★ +8
Ship=0x70(112) Teleport=0x4c(76)
```
**⇒ Q1 还剩一半没有证据**：**这些常量是否等于"真实分配给该对象的字节数"？**

S7 试过但**判据失灵**，全 10 类报 `not_found - no push imm; call alloc within 64 bytes of a primary-vtable write` ⇒ **Lead 已判为 `INSTRUMENT_FAILED`（不是"没有分配点"）。**

## 1. 纪律（先读，逐条遵守）

1. **判据锚定行首/字段**，不得"关键词出现即算"。
2. **空结果必须报 `未命中 / INSTRUMENT_FAILED`**，并附**判据与扫描范围**；**不得报"无"或 `0`**。
3. **任何提取类工具必须带物理边界断言**（尺寸/数量/范围）。**先让它能红，再去修。**
4. **`None` / `[]` / `not_attempted` / 数值 —— 四种输出必须可区分。**
5. **FileOffset 用段映射**（`E-W3-01`）：`.text`/`.rdata`/`.data` = `VA−0x400000`；**`.rsrc`/`.detour` = `VA−0x6FC000`**。
6. **不确定就写"不确定 + 缺什么证据"，禁止圆。**
7. **产物原子落盘**（写 `.tmp` → 成功才 `os.replace`）+ **收尾 `assert size > 0`**。**`0 字节`产物 = 失败，不是结果。**
8. 🔴 **只读**：`ra2youli/**`、`ra2bench/**`、`ra2render/**`、`tools/**`、`docs/**`、`out/re_work/qc/**`、`out/re_work/agy/**`、前一张卡目录 `out/re_work/zcode_live/W3_20261001/yr_delta8/**`。
   **`ra2youli/`、`ra2bench/`、`ra2render/` 是现网目录 —— 一律只读，不得写入一个字节。**
9. **不得启动游戏 / 注入 / 调试 / 改任何二进制。**

## 2. 基准（**你仍要自己各算一次**）
| 件 | sha256 | 大小 |
|---|---|---|
| `ra2youli/game.exe` | `c4bf2a57a80ff8d1aa9fbc77f6095c385c1b2ca274ba3f5a4a44aa7446caea5b` | 4,497,680 B |
| `ra2youli/gamemd.exe` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 4,825,360 B |

## 3. 做什么

### 3.1 主轴：**找"用这个尺寸去分配"的调用点**
**不要再用 S7 那条窄判据**（`push imm; call alloc` 且必须在 vtable 写入 64 字节内）。**换一条：以"常量"为索引反查全 `.text`。**

对**每个** `Size()` 常量 `S`（`0x30 0x34 0x4c 0x58 0x60 0x70 0x78 0x90`，以及 gamemd 侧的 `0x98 0x60`），在 `game.exe` / `gamemd.exe` 的 `.text` 里**穷举**下面所有形态（**逐条给出命中数**）：
```
① push S                      ; MSVC 常见
② mov ecx, S   (紧接 call)     ; __thiscall 参数
③ mov dword ptr [esp+N], S
④ lea eax, [S] / mov eax, S   (其后 call operator new)
⑤ call ??2@YAPAXI@Z / ??_U@YAPAXI@Z / 该项目 CRT 里的 operator new 符号
⑥ 任何"先取 Size() 返回值再当参数"的形态：call <该类的 Size() 槽> 后 push eax / mov ecx,eax
```
**⇒ 关键**：**`Size()` 是与 `new` 配套的**（MFC/COM 常用模式：`p = new BYTE[GetSize()]` 或 `operator new(Size())`）。**所以最可能的形态是 `call <Size() thunk>` 后立刻 `push eax` / `mov ecx,eax`。**
**⇒ 请优先查 ⑥**，并给出该形态在两侧的命中点。

### 3.2 次轴：**类工厂 / CLSID 创建路径**
`Jumpjet` / `Rocket` 有 GUID（S7 已取）：`Jumpjet 92612C46-F71F-11D1-9FAC6000-0508B55B`、`Rocket B7B49766-E576-11D3-D99B1000-974BE82F`。
⇒ **查 `CoCreateInstance` / `IClassFactory::CreateInstance` 的调用点**，看**分配尺寸从哪来**（是否经 `Size()`）。
**若能证明"工厂按 `Size()` 分配"⇒ Q1 直接闭合。**

### 3.3 结论形态（`[0]` 必答）
1. **`Size()` 常量是否等于真实分配尺寸**：`是 / 否 / 证据不足`（**三选一，给判据**）
2. **若"是"**：给出**至少 2 个类的分配点原文**（`调用点 VA + 指令序列 + 该处用到的尺寸立即数`）
3. **若"否"**：给出**实际分配尺寸**与**差异**（例如"分配 152 但 `Size()` 报 144"）
4. **若"证据不足"**：**明确写出"查了哪些形态、各命中多少、还缺什么证据"**

### 3.4 顺带（**若有余力，不勉强**）
`?$CComObjectVCChatEventSinkATL` 的 `primary_slots` **两侧不同（game 9 / gamemd 10）而 `iloco` 相同** —— **本族唯一的主表槽数差异**，请给出这 1 个槽是什么（目标 VA + 首指令）。

## 4. 交付（**写域仅此一处**）
`out/re_work/zcode_live/W3_20261001/z2_alloc_size/`
- `Z2_ALLOC.md`（§A 十节骨架，`docs/re/AGENT_DELIVERY_FORMAT.md`，`[0]` 直答 §3.3 四问）
- `z2_alloc.json`（机读：每个类的 `size_const` / `alloc_sites[]`（VA+指令+用的尺寸）/ `verdict`）
- `verify_z2.py`（**EXIT=0**：①§3.3 四问均有结论 ②报告引用的指令能在 `raw/` 逐字检出 ③两侧哈希与 §2 一致）
- `raw/stepNN_*.txt`（**按步命名，禁止同名覆盖**）

## 5. 门禁与回报
**开工先跑** `python tools\verify_anchors.py`（须 **323/323 PASS**，末尾原文贴进报告）。
**若有 claims 文件，跑** `python tools\audit_bytes.py <file>` 并贴 `OK/MISMATCH` 计数。

**回报 `[0]`**：①`Size()` 是否等于真实分配尺寸（是/否/证据不足）②判据一句话 ③命中数（按形态①–⑥分列）④若"证据不足"，缺什么。

**底线**：**宁可交"⑥ 形态查了、命中 0、判 INSTRUMENT_FAILED、缺 CRT 符号表"，也不要交"应该会通过"。**
**本卡唯一的价值就是回答 Q1 的另一半 —— 答不了就如实说答不了。**
