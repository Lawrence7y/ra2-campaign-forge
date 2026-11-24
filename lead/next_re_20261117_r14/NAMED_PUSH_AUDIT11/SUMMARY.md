# SUMMARY — NAMED_PUSH_S22_B3 异族独立审计（11 行）

**审计身份**：异族独立审计员（不是 Hy4，不是 DeepSeek 执行器）。只采信本审计自己反汇编的字节。
**结论：PASS 11 / FAIL 0。**

| 项 | 值 |
|---|---|
| 目标 | `ra2youli\gamemd.exe` |
| SHA-256（本审计自算） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✅ 与卡面期望一致 |
| 节表实测 | `.text` VA `0x401000` / VirtualSize `0x3DF38D` / 止于 `0x7E038D` ✅ |
| 工具 | Python 3.12.10、capstone 5.0.7（`skipdata=True`）、pefile 2024.8.26；无 venv、未 pip install |
| 取证脚本 | `_work\pe.py` + `_work\s1..s25_*.py`；原始输出 `_work\s*_out.txt`、`_work\verify3.json`、`_work\facts_final.json` |
| 未采信 | 执行器 `NAMED_PUSH_S22_B3\EVIDENCE\ROW_*.txt` / `REPORT.md` 未作证据（只在取 11 个 entry 时读了 `delta.tsv` 的列） |

## 0. 11 行的取法（自己取，写在这里）

`NAMED_PUSH_S22_B3\delta.tsv` 表头 6 列：`entry / subsystem / name / one_line_semantics / grade / evidence_path`。
本审计用 `Get-Content` 逐行切 `\t` 取第 1 列（大写、无 `0x`），得**恰 11 个数据行**：

```
006C2B10 006C2C90 006C2E10 006C2F90 006C3110 006C3290 006C3410 006C3590 006C3890 006C3A10 006C3B90
```

（同目录 `EVIDENCE\` 另有 `ROW_006C3710.txt`、`ROW_006C3D10.txt` 两份，但二者不在 `delta.tsv` 的 11 行内 ⇒ 本审计不审。
`base_rate.tsv` 自报 `rows_checked=13`，与本审计所见的 13 份 EVIDENCE 相符，delta 只留 11。）

11 行同族同构：`T_TClassFactory_V<Xxx>Class__::slot3`，全部落在连续类工厂区 `[006C2A40, 006C3E00)`，
各自对应一个 `IClassFactory` 实现，工厂类由 `0x6BB9A0`（类系统初始化，`size=0x2810`）构造后
以 `CoRegisterClassObject` 注册进 COM。

## 1. 总判定

**PASS 11 / FAIL 0。** 执行器本批**未虚报**（对照：同族 B1 报 16 行、实测 14 行为真）。

| entry | 类（RTTI 独立读出） | 工厂 vt / 槽 | 新建对象主 vt | 裁定 |
|---|---|---|---|---|
| 006C2B10 | AircraftTypeClass | 007F3B28 +12 (slot3) | 007E2868 (vt[0]=00410260) | PASS |
| 006C2C90 | InfantryTypeClass | 007F3B40 +12 | 007EB610 | PASS |
| 006C2E10 | BulletTypeClass | 007F3B58 +12 | 007E4948 | PASS |
| 006C2F90 | IsometricTileTypeClass | 007F3B70 +12 | 007ECC48 | PASS |
| 006C3110 | OverlayTypeClass | 007F3B88 +12 | 007EF600 | PASS |
| 006C3290 | SmudgeTypeClass | 007F3BA0 +12 | 007F3528 | PASS |
| 006C3410 | UnitClass | 007F3BB8 +12 | 007F5C70 | PASS |
| 006C3590 | BuildingClass | 007F3BD0 +12 | 007E3EBC | PASS |
| 006C3890 | InfantryClass | 007F3C00 +12 | 007EB058 | PASS |
| 006C3A10 | AnimClass | 007F3C18 +12 | 007E3354 | PASS |
| 006C3B90 | AnimTypeClass | 007F3C30 +12 | 007E3608 | PASS |

11 行的 `entry` 在全镜像 direct caller（`E8 rel32` 全扫）**均为 0** —— 与执行器所述「纯虚派发」一致。

## 2. FAIL 逐条原因

**无。** 11 行均通过五项检查。

## 3. 专门问题一：② 是否真用主虚表（slot0 = 00410260）

**结论：是，11 行全部成立；但「主虚表 slot0=00410260」指的是体内新建对象的表，不是工厂自身虚表 —— 这一点必须写清，否则会被误判。**

- **工厂自身**虚表 `vt[0]` **不是** `00410260`，而是各工厂自己的 QI（11 行依次为 `006C2A50 / 006C2BD0 / 006C2D50 /
  006C2ED0 / 006C3050 / 006C31D0 / 006C3350 / 006C34D0 / 006C37D0 / 006C3950 / 006C3AD0`）。若有人拿工厂自身
  `vt[0]` 去套「必须=00410260」，会得到全批假 FAIL —— 本审计排除了这条路。
- **对象主虚表**：本审计对每行独立追 `push <size>` → `call 0x7C8E17`（分配）→ `test eax,eax` → `mov ecx,eax` →
  `call <该类 ctor>`，在 ctor 体内取 **this 寄存器上的偏移 0 写点**，再用 `[vt-4]→COL→TD→TD+8 名串` 判类。
  11 行的对象主表 `vt[0]` 全部 `= 00410260`，且 RTTI 名与工厂模板实参逐字一致（见第 1 节表）。
- **差分检验（㉔，防「小成员表当主虚表」）**：每个 ctor 体内都还有别的虚表写点，本审计逐个列出并用 RTTI 名判死，
  只有 `dst = this` 且名 = 该类 的那一处计为主表。典型两例（正是 B1 翻车的同一类陷阱，本批未踩）：
  - `006C2C90`：ctor `005236A0` 先在 `[edi]` 上写 `007EB6D4`(`.?AV?$TypeList@PBVAnimTypeClass@@@@`) 与
    `007E4DD8`(`.?AV?$TypeList@H@@`) —— 这是成员子对象，不是主表；主表是 `005237E8` 的 `mov [esi],007EB610`。
  - `006C2F90`：ctor `005447C0` 先在 `[ebp+0x2a4]` 写 `007ECCEC`(`.?AV?$DynamicVectorClass@PAG@@`)（成员），
    主表是 `005448C8` 的 `mov [ebp],007ECC48`。

## 4. 专门问题二：④ 锚点是否落在析构器里（㉓）

**结论：11 行全部没有。㉓ 排除，依据是「装表点唯一 + 写入者是 ctor + 不在 atexit 注册路径」。**

- 每行工厂表在整个 `.text` **只有 1 处 imm 写点**，且都在 ctor 里（`mov dword ptr [eax], <vt>`）：
  `006C2A49 / 006C2BC9 / 006C2D49 / 006C2EC9 / 006C3049 / 006C31C9 / 006C3349 / 006C34C9 / 006C37C9 /
  006C3949 / 006C3AC9`。**无第二处写点**（既无析构器写点，也没有「基类死表 + 派生活表」成对争抢）。
- 这些 ctor 的唯一调用者都在初始化函数 `0x6BB9A0` 体内（如 `006C2A40` 只被 `006BCDF0` 调），
  `0x6BB9A0` 在全镜像 **imm 引用 = 0**（因此不可能被 `push <dtor>; call 0x7C978A` 的 atexit 路径注册），
  其唯一 direct caller 是 `007CD8EA`（初始化路径）。⇒ 装入的是**活表**。
- **但要记一条差点踩的坑**：有 3 行的**对象表**（不是工厂表）确实存在「ctor 写 + 另一函数回写同一张表」的成对形态：
  `006C3410`(`007F5C70`：`0073543A` 与另一函数 `00735794`)、
  `006C3590`(`007E3EBC`：`0043B9FA` 与另一函数 `0043BCFD`——项目已认定 `0043BCF0` 非构造函数)、
  `006C3B90`(`007E3608`：`00427731` 与另一函数 `0042785D`)。
  这些行的 ④ 锚在**工厂表**上，没有拿对象表充当 ④，所以不触发 ㉓；若有审计员改用对象表判 ④，这 3 行就会踩坑。

## 5. 专门问题三：每行 ③b② 的检查点与消费点是否真实

**结论：检查点（三道 imm 错误码）与消费点（`test edi,edi` / `jge` 后两路动作不同）在字节上全部真实；
但「消费点」消费的是**体内 QueryInterface 的返回值**，不是本 entry 自己的返回值 —— 这一点执行器没写清，属措辞级缺口，不判 FAIL。**

每行共同形态（以 `006C2B10` 为例，其余 10 行同构，仅偏移不同）：

```
006C2B16  85 ff                 test edi,edi / 006C2B18 75 0a jne   ; 守卫1：出参
006C2B1B  b8 57 00 07 80        mov eax,0x80070057 (E_INVALIDARG)
006C2B2E  85 c0 / 74 0a         test eax,eax / je                   ; 守卫2：pUnkOuter 必须为 NULL
006C2B33  b8 10 01 04 80        mov eax,0x80040110 (CLASS_E_NOAGGREGATION)
006C2B49  85 c0 / 74 0f         test eax,eax / je                   ; 守卫3：分配结果
006C2B5D  b8 0e 00 07 80        mov eax,0x8007000E (E_OUTOFMEMORY)
006C2B6F  ff 10                 call dword ptr [eax]  ; = 对象主表 vt[0] = 00410260 (QI)
006C2B71  8b f8                 mov edi,eax           ; 返回落 edi
006C2B73  85 ff                 test edi,edi
006C2B75  7d 09                 jge 0x6c2b80          ; 成功路
006C2B77  8b 16 / 6a 01 / 8b ce   mov edx,[esi]; push 1; mov ecx,esi
006C2B7D  ff 52 20              call [edx+0x20]       ; 失败路：主表 slot8 = 删除型析构
006C2B80  8b c7                 mov eax,edi           ; 回传 HRESULT
```

核实到的三件事：
1. **失败返回什么 / 成功返回什么**：三个 imm 错误码各自带独立早退 `ret 0x10`；成功路回传 `edi`（QI 的 HRESULT，
   实测 `00410260` 只可能返回 `0` / `0x80004003` / `0x80004002`，`ret 0xc` 共 3 处）。⇒ **可伪证**。
2. **消费点真实**：`test edi,edi` 与 `jge` 零间隔，`edi` 是 QI 返回值唯一落点（其后唯一 eax 写是成功路的 `mov eax,edi`），
   两路动作**真不同**（失败路 `push 1` + `call [edx+0x20]` 把刚建的对象删掉；成功路直接回传）。
   失败路调到的 slot8（如 `0041CFE0`）经核对是**真删除型析构**：先回写四张类表、把自己从全局容器摘除
   （含 `cmp eax,-1` 未命中哨兵）、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`（释放）。
3. **不属 ③a**：体内有 4 处条件分支与 3 个可区分错误码，非「单次调用+单次写 / 无分支线性流程」。

**必须记下的缺口**：本 entry 自身 HRESULT 的消费方在**镜像之外**（`CoRegisterClassObject` 交给 ole32，
由 `CoCreateInstance` 路径回落）。镜像内虽有 21 处 `CoCreateInstance` 调用点，但**没有一处**用的是这 11 个 CLSID
（它们用的是 `0x7E9500 / 0x7E9540 / 0x7E96E0 / 0x7F7C30 / 0x817BC0` 等），且本 entry direct caller = 0。
⇒ ③b② 的成立依据是「本 entry 自带三道可伪证错误码 + 体内对 QI 返回的真两路分支」，
**不是**「有镜像内调用者拿本 entry 的返回值分支」。执行器第 4 列把消费点写成本体那条 `jge`，措辞上把它当成了
「调用方」，实际它是「本函数对 QI 的消费」。按 D-46(A) 窄读（③b② 只认错误码/返回约定）本条仍成立，故判 PASS，
但下游若要求「镜像内消费点」应视为待补。

## 6. ④ 的证据强度（必须与 PASS 一起读）

11 行 ④ 均**没有**镜像内的派发指令（不存在「拿着该工厂指针 `call [reg+0xc]`」的站点），也**没有** direct caller。
成立的是 `R14_COMMON` §8.6 条 1 的第二种形态：

- 构造器装的**活**表（装表点唯一、非 atexit）+ `vt[slot]==entry` + `site 不共用`（11 行 11 个不同 site/vt，无争抢）；
- 加强项（本审计自己挖的，执行器未给）：工厂对象是 `new(8)` 的堆对象，ctor 装表后立刻
  `push CLSID; push factory; push 1; push 1; push &cookie; call [0x7E15D8]` = **`CoRegisterClassObject`**
  （注册点 `006BCE0A / 006BCE47 / 006BCE84 / 006BCEC1 / 006BCEFE / 006BCF3B / 006BCF78 / 006BCFB5 /
  006BD02F / 006BD06C / 006BD0A9`），CLSID 各不同（如 AircraftTypeClass = `007E95B0`）；
  且该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 **`IID_IClassFactory`**(`007F7CA0`) ⇒ 注册出去的确实是
  可被 COM 派发 `CreateInstance` 的类工厂。

补充纠正一条本审计自己先算错、后改正的读法：该 vtable 是**显式 this 的 stdcall**（`QI(this,riid,ppv)` `ret 0xc`、
`AddRef/Release(this)` `ret 4`、`slot3(this,pUnkOuter,riid,ppvOut)` `ret 0x10`），四个栈参与
`IClassFactory::CreateInstance` 完全自洽，不存在「多一个参数」的问题。

## 7. 与执行器自报的差异

- 执行器 11 行标 `[已证]`；本审计 **11 PASS / 0 FAIL** ⇒ **虚报率 0/11 = 0%**（对照：B1 批 2/16、S15S16 批 4/11）。
- 执行器给出的**每一个地址与数值**（三道守卫、主站点、`jge` 目标、失败路、槽地址、COL/TD、工厂 ctor、
  宿主 `0x6BB9A0`、对象主 vt）本审计逐项复算，**11 行全对，无一处偏移错、无一处张冠李戴**。
- 两处**措辞级**（不影响裁定，但下游引用时须改写）：
  1. 「主虚表 slot0=00410260」在 11 行里说的是**体内新建对象**的表；工厂自身 `vt[0]` 不是 `00410260`。
  2. 「调用方真拿它分支」在本批指的是**本函数对 QI 返回值的消费**；本 entry 返回值的镜像内消费方不存在。

## 8. 复现

```powershell
cd D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work
$env:PYTHONIOENCODING="utf-8"
py -3 s1_bodies.py      # 11 行函数体
py -3 s8_deep.py        # 工厂 vt / RTTI / 守卫 / QI / 对象 ctor 初探
py -3 s12_verify2.py    # 按 this 寄存器 + RTTI 名选对象主虚表（差分）
py -3 s16_clsid.py      # 每行 CLSID 与 CoCreateInstance 消费点
py -3 s17_slots.py      # 工厂各槽语义 + 全 .text 虚表写点/CLSID 引用
py -3 s20_table.py      # 11 行汇总表（含 vt[0]=00410260 与 RTTI 名比对）
py -3 s23_tsv.py ; py -3 s24_verdict.py   # 生成 verdict.tsv / VERDICT.md
```
