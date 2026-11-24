# NAMED_PUSH_AUDIT4 — S22_B1 全 16 行异族独立审计（SUMMARY）

## 0. 一句话

**16 行全部审完：PASS 14 / FAIL 2。**
FAIL = `006BFF90`、`006C0A10`（唯一成因为 ③b 成链点被指向"内嵌成员虚表 + `VectorClass<T>` 析构函数"，其自陈可伪证常量表为空 ⇒ 该行文字未构成取证；函数整体合同真实，**改字后可重提**）。

## 1. 审计身份与口径

- 审计员：**异族独立审计**（非本批执行器）。只采信我自己反汇编的字节；执行器 `EVIDENCE\ROW_*.txt` **未作任何证据引用**。
- 镜像 `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（= 卡面期望）。
- 工具：capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26 + Python 3.12.10，无 venv、未装包。
- 扫描完备性：全 `.text` 线性扫描 **1,392,592 条指令 / 68,253 个 direct call 站点 / 8,440 个数据 imm32 引用**。
- 判据：`R14_COMMON.md:611`（③b 四充分条件）+ `:745-749`（D-46(A)：③b② 只认错误码/返回约定）+ 卡面五点 + Lead 本轮裁定（③ 只要求函数整体合同真实，不要求落在 survey 命中站点）。

## 2. 计数

| 项 | 值 |
|---|---:|
| 报告行数 | **16**（`delta.tsv` 全部数据行） |
| PASS | **14** |
| FAIL | **2** |
| ④②不同源 | 16/16 `no`（不同源） |
| ③b 形态 | 16/16 `3b2`（我实测的函数整体合同） |
| ①类身份（②）| 16/16 成立 |

PASS：`006BF810` `006BF990` `006BFB10` `006BFC90` `006BFE10` `006C0110` `006C0290` `006C0410` `006C0590` `006C0710` `006C0890` `006C0B90` `006C0D10` `006C0E90`
FAIL：`006BFF90` `006C0A10`

> 注：`base_rate.tsv` 记 `rows_checked=18`，`delta.tsv` 实为 16 行；多出的 2 份 `EVIDENCE\ROW_0069C9C0.txt` / `ROW_0069CBC0.txt` 不在 delta 内，**不在本次派单范围**（派单=delta 全部 16 行）。

## 3. FAIL 逐条原因

### `006BFF90`（TClassFactory<TiberiumClass>::slot3）

- ② 成立、④ 成立、④②不同源成立、方向成立 —— **只有 ③b 的成链点假**。
- 原文：「主站点 @006BFFEF `call dword ptr [eax]`（新建 Tiberium 对象主 vt **007EB6D4** 的 slot0=**QueryInterface 00524FC0**）」。
- 实测：
  - `007EB6D4` 是 ctor `007216C0` 在 `00721734 C7 07 D4 B6 7E 00` 写进 **`[edi]`（edi = `[esi+0xC4]`，内嵌成员）** 的 `TypeList<AnimTypeClass*>` 表，**不是 this 的主虚表**；
  - 真正的主虚表是 `007217A6 C7 06 28 57 7F 00` 写的 **`007F5728`**（`[esi+0]`）；
  - `00524FC0` 是 **`VectorClass<AnimTypeClass*>` 的析构式函数**：`C7 06 F4 B6 7E 00`（改装 `007EB6F4`）+ `call 0x7C8B3D`（free）+ `ret 4`（带 delete 标志），**不比较 IID、不写 `*ppvOut`、不返 HRESULT 三态**；
  - 真 QI 是 `007F5728` 槽 0 = **`00410260`**。
- 且原文自陈的可伪证常量表为空（写作「常量 、1 处 ret」）——**它自己就承认没取到这个证据**，却仍照发模板句。

### `006C0A10`（TClassFactory<VSpawnManagerClass>::slot3）

- 同型：原文「主 vt **007F36B4** 的 slot0=**QueryInterface 006B8790**」。
- 实测：`007F36B4` 是 ctor `006B6EA0` 于 `006B6EBB C7 07 B4 36 7F 00` 写进 **`[edi]`（edi = `[esi+0x38]`，内嵌成员）** 的 `DynamicVectorClass<SpawnControl*>` 表；主虚表是 `006B6EE6 C7 06 50 36 7F 00` 的 **`007F3650`**；`006B8790` 是 `VectorClass<SpawnControl*>` 的析构式函数（`C7 06 D4 36 7F 00` + free + `ret 4`）；真 QI 为 `007F3650` 槽 0 = **`00410260`**。

### 为什么这算 FAIL 而不是"锚不干净但结论对"

上一批审计（`S15S16_3B2\_audit`）两条在案口径：
1. 「**地址全真 ≠ 主张成立**」——`006E56E0` 因"主张的检查点不成立"被判 FAIL；
2. 「间接 call 标 None 的行要**解析到底**，不解析就 PASS 等于放行一个未验证前提」。

本批这两行比"标 None"更重：它**点了一个具体函数并断言它是 QueryInterface**，而该函数是容器析构函数。③b 是 `[已证]` 的唯一载体（③a 只能留 `[静态推断]`），③b 的成链点指错函数 ⇒ 该行文字未构成取证。

> **与 Lead 本轮放宽裁定的边界**：放宽的是"③ 不必落在 survey 命中的 `operator new` 空判断站点"；**不是**"③ 的成链点可以指错函数"。这两行的函数整体合同（主 vt 槽 0 = `00410260` 的 HRESULT 契约）真实存在，所以**是"改字可重提"，不是"重挖"**。

## 4. 专项：16 行是否"共用同一段取证文字"（Lead 点名要答）

**是同一段模板文字；但 16 个函数体本身也是同一 C++ 模板的 16 次实例化。所以判据只能是"每行替换值是否为本行字节真值" —— 逐行核完：14 真 / 2 假。**

三层证据：

| 层 | 做法 | 结果 |
|---|---|---|
| 文字层 | 归一化掉地址与类名后比对 16 行 `one_line_semantics` | **收敛为同一段**（差异仅"常量"括号与 CLSID 值）⇒ 确为模板 |
| 代码层 | 归一化立即数后比对 16 个函数体 | 11 行完全相同、5 行差 1–2 条（差在 ctor 参数 push 与 `sizeof`）⇒ 模板实例化的正常形态 |
| **真值层** | 对每行**逐个替换值**回字节核（② vt/槽/COL/TD/类名；③b QI 站点/释放站点/push 1/三码/4×ret；④ 分配点/ctor/装表点/注册点/GUID） | **14 行全命中；2 行 ③b 的"主 vt / slot0"非本行值** |

结论：**这批不是"16 行共用一段空洞文字"（14 行各自站得住），但也绝不是"16 行逐行取证"**（2 行 ③b 成链假、1 行 GUID 错位、11 行 GUID 未解析）。

### 附：4 行"体积/构造差异"的说明

`006BFE10` / `006BFF90` / `006C0110` / `006C0290` / `006C0410` 的函数体比其余行多 1–2 条指令，差异在新建对象构造器的**参数 push** 与 `sizeof` 立即数（如 `006BFF90` 是 `68 28 01 00 00 push 0x128`、`006BF810` 是 `68 18 0E 00 00 push 0xe18`）。这是类大小/构造签名不同所致，不影响 ③b 形态判定。

## 5. 另需改字（不构成 FAIL，但不得按原文并入）

1. **`006BF810` 的 GUID 错位**：原文「以 CLSID **7E9580** 经 CoRegisterClassObject 注册」。实测 `007E9580` 属**前一块**（ctor `006BF5C0` = `TClassFactory<VSuperClass>`，注册点 `006BC5AE`）；本行真实 GUID 为 **`007E9950`**（`006BC5EB push`）。④ 主张本身不垮，但账上文字必须改。
2. **11 行 GUID 写成 `None`**（`006BFF90`~`006C0E90`）：实测全部可解析，须补齐：

| entry | 工厂 ctor | GUID（实测） |
|---|---|---|
| 006BF810 | 006BF740 | 007E9950（原文 7E9580 **错**） |
| 006BF990 | 006BF8C0 | 007E9930 ✓ |
| 006BFB10 | 006BFA40 | 007E9940 ✓ |
| 006BFC90 | 006BFBC0 | 007E98F0 ✓ |
| 006BFE10 | 006BFD40 | 007E9910 ✓ |
| 006BFF90 | 006BFEC0 | 007E9920（原文 None） |
| 006C0110 | 006C0040 | 007E9750（原文 None） |
| 006C0290 | 006C01C0 | 007E9900（原文 None） |
| 006C0410 | 006C0340 | 007E9730（原文 None） |
| 006C0590 | 006C04C0 | 007E9850（原文 None） |
| 006C0710 | 006C0640 | 007E98D0（原文 None） |
| 006C0890 | 006C07C0 | 007E98E0（原文 None） |
| 006C0A10 | 006C0940 | 007E9860（原文 None） |
| 006C0B90 | 006C0AC0 | 007E9870（原文 None） |
| 006C0D10 | 006C0C40 | 007E9880（原文 None） |
| 006C0E90 | 006C0DC0 | 007E9890（原文 None） |

## 6. 这 16 行的 ④ 为什么成立（方法说明，供复核）

直接调用者全 **0**（68,253 站点穷举），所以 ④ 必须走"活对象"通道。我不用执行器的说法，自己重建了整条链：

1. 宿主 `006BB9A0` 是一张 **77 块**的顺序注册表；唯一 direct caller `007CD8EA`，其上下文是 `pushfd/push esi/push esi → call dword ptr [0x7E1240]（GetModuleHandleA）→ push eax → call 006BB9A0`，即"把模块句柄传入的初始化例程"，**不是析构器**；
2. 每块骨架：`lea ecx,[ebp-0xA34] / push ecx / push 1 / push 1 / push <pUnk> / push <rclsid> / call esi`，其中 `esi = [0x7E15D8]` 在 `006BC43F` 一次性装定 = **ole32!CoRegisterClassObject**（导入名坐实）；
3. 每块的 `<pUnk>` 是紧前 `push 8 / call 0x7C8E17 / mov ecx,eax / call <TClassFactory ctor>` 造出的 **8 字节工厂实例**，ctor 内 `mov [reg], <工厂 vt>` 装表；
4. 因此该工厂 vt 挂在**堆上活对象**并被交给 COM ⇒ 槽 3 的派发由 ole32 完成（外部派发点，静态不可见），这是本形态能取到的最硬见证。
5. **㉓ 成对陷阱排除**：每个工厂 vt 在全 `.text` **恰 1 处** imm32 引用（就是该 ctor），**无析构器重装死表**；且本二进制 372 个导入中**没有任何 `atexit/_onexit`**（只有 `ExitProcess`/`FatalAppExitA`/`GetExitCodeProcess`）⇒ atexit 死表通道在本镜像上物理不存在。
6. **④②不同源**：② 的证在 `.rdata`（COL→TD→名字 + 槽值），④ 的证在 `.text`（分配/装表/注册）+ `ole32` IAT，不共用同一虚表槽。

## 7. 与派单要求的对照

| 派单要求 | 我做了什么 |
|---|---|
| 审 `NAMED_PUSH_S22_B1\delta.tsv` 全部 16 行 | 16/16，方法见 VERDICT §1 |
| ③b 用"同一函数体内 QueryInterface 的 HRESULT 分支" | 16/16 逐行给出 QI 站点 + `mov edi,eax`/`test`/`jge` + 释放站点 + `push 1` 的地址与字节 |
| 每行独立确认 QI 检查点与消费点真实存在 | 16/16 在本行**自身字节**中确认（VERDICT §2 逐行签名表） |
| 确认 16 行不是共用同一段取证文字 | 见 §4：文字是模板、代码是模板实例化、**真值层 14 真 2 假** |
| 输出目录 `NAMED_PUSH_AUDIT4` | 只写该目录；未改 `coverage.tsv`/`PANEL.md`/`R14_COMMON.md`/台账/`NAMED_PUSH_*` 任何文件 |

## 8. 产出清单

- `NAMED_PUSH_AUDIT4\VERDICT.md` —— 逐行 16 节，五查各带地址与字节 + 2 个 FAIL 的根因 + GUID 勘误表
- `NAMED_PUSH_AUDIT4\verdict.tsv` —— 16 行判定表（`entry/subsystem/verdict/ring2_at/ring3b_form/ring4_at/same_source/reason`）
- `NAMED_PUSH_AUDIT4\SUMMARY.md` —— 本文件
- `NAMED_PUSH_AUDIT4\work\` —— 自写脚本与原始输出（`lib.py` `index.py` `index.json` `facts3.py` `f3_*.json` `chain4b.py` `chain4.json` `join.py` `sigmacheck.py` `emit.py` `rowfacts.txt` `genverdict.py`），全部可复算
