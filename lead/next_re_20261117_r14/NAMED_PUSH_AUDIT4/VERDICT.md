# NAMED_PUSH_AUDIT4 — NAMED_PUSH_S22_B1 全 16 行异族独立审计（VERDICT）

## 0. 前提与本审计的独立性

- 审计员：**异族**（本批执行器为 S05/S14 侧之外的第四次推送，非本审计产物）。**只采信我自己反汇编的字节**；执行器 `NAMED_PUSH_S22_B1\EVIDENCE\ROW_*.txt` 仅当线索，**未在本文引用任何执行器证据文字**。
- 镜像：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
  - SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` = 卡面期望值。
  - ImageBase `0x400000`；节表实测：`.text 00401000..007E1000`、`.rdata 007E1000..00812000`、`.data 00812000..00B79BE4`、`.rsrc`、`.detour`。
  - ⚠️ 与卡面 `[0x401000, 0x7E038D)` 的差异：实测 `.text` 虚段尾为 `007E1000`（卡面 `7E038D` 落在此段内）。本审计按实测节界扫描，全 `.text` 1,392,592 条指令、68,253 个 direct call 站点，未截断。
- 工具：capstone 5.0.7（`skipdata=True`）、pefile 2024.8.26、Python 3.12.10，无 venv、未装包。自写脚本在 `NAMED_PUSH_AUDIT4\work\`（`lib.py`/`index.py`/`facts3.py`/`chain4b.py`/`join.py`/`sigmacheck.py`/`emit.py`），全部可复算。
- 判据：`R14_COMMON.md:611`（③b 四充分条件：①跳表 ②可伪证错误码/返回约定 ③内存形状断言 ④完整循环 I/O）、`R14_COMMON.md:745-749`（**D-46(A)**：③b② 只认错误码/返回约定，bool 主输出不算）、卡面五点。
- Lead 本轮裁定（照办）：**③ 只要求函数整体合同真实，不要求落在筛出它的那个站点**。因此本文对 ③ 的判定基准是**本 entry 函数体内的真实合同**，而非 survey 命中的 `operator new` 空判断。

## 1. 取行方法（可复现）

`NAMED_PUSH_S22_B1\delta.tsv` 跳过表头、按 `\t` 切 6 列（`entry/subsystem/name/one_line_semantics/grade/evidence_path`），得 **16 数据行**。
`base_rate.tsv` 记 `rows_checked=18`，但 `delta.tsv` 只有 16 行 —— 差 2 行是 `EVIDENCE\` 下多出的 `ROW_0069C9C0.txt`/`ROW_0069CBC0.txt`（未进 delta）。**本审计只审 delta.tsv 全部 16 行**，与派单一致。
16 行 `subsystem=S22`、`grade=[已证]`、行名全为 `T_TClassFactory_<X>::slot3`。

## 2. 结构总览（我先认清这批是什么）

16 行是 `TClassFactory<X>::CreateInstance`（IClassFactory 五槽布局的 **槽 3**：槽0=QueryInterface、槽1=AddRef、槽2=Release、槽3=CreateInstance、槽4=LockServer；该槽序与 `S11-K1\_audit\VERDICT.md:44` 在案的更正一致）。
每行函数体是同一 C++ 模板的 16 次实例化，故**代码骨架相同、立即数与调用目标不同**。逐行实测骨架（`sigmacheck.py`）：

```
push esi / push edi
mov  edi,[esp+0x18]          ; ppvOut
test edi,edi / jne           ; 空 → mov eax,0x80070057 (E_INVALIDARG) ; ret 0x10
mov  eax,[esp+0x10]          ; pUnkOuter
mov  dword ptr [edi],0       ; *ppvOut = 0      ← 先置空（写方向）
test eax,eax / je            ; 非空 → mov eax,0x80040110 (CLASS_E_NOAGGREGATION) ; ret 0x10
push <sizeof(X)> / call 0x7C8E17 (operator new)
test eax,eax / je            ; → mov eax,0x8007000E (E_OUTOFMEMORY) ; ret 0x10
mov  ecx,eax / call <X::ctor>; mov esi,eax / test esi,esi / jne
mov  ecx,[esp+0x14]          ; riid
mov  eax,[esi]               ; 新建对象主虚表
push edi / push ecx / push esi
call dword ptr [eax]         ; ← 槽0 = QueryInterface   (FF 10)
mov  edi,eax / test edi,edi / jge   ; ← 消费 HRESULT
; 失败路：mov edx,[esi] / push 1 / mov ecx,esi / call dword ptr [edx+0x20]  (FF 52 20)
mov  eax,edi / pop edi / pop esi / ret 0x10
```

**16 行逐行实测签名**（每行**自身字节**都含全部要素，非引用同一条文字）：

| entry | 指令数 | 三码 | QI 调用 | 释放调用 | 置空*ppv | push 1 | ret |
|---|---:|---|---|---|---|---|---|

| 006BF810 | 48 | 80070057/80040110/8007000E | 006BF86D FF10 | 006BF87B FF5220 | 006BF828 | 006BF877 | 4×C21000 |
| 006BF990 | 48 | 80070057/80040110/8007000E | 006BF9ED FF10 | 006BF9FB FF5220 | 006BF9A8 | 006BF9F7 | 4×C21000 |
| 006BFB10 | 48 | 80070057/80040110/8007000E | 006BFB6A FF10 | 006BFB78 FF5220 | 006BFB28 | 006BFB74 | 4×C21000 |
| 006BFC90 | 48 | 80070057/80040110/8007000E | 006BFCEA FF10 | 006BFCF8 FF5220 | 006BFCA8 | 006BFCF4 | 4×C21000 |
| 006BFE10 | 49 | 80070057/80040110/8007000E | 006BFE6F FF10 | 006BFE7D FF5220 | 006BFE28 | 006BFE79 | 4×C21000 |
| 006BFF90 | 49 | 80070057/80040110/8007000E | 006BFFEF FF10 | 006BFFFD FF5220 | 006BFFA8 | 006BFFF9 | 4×C21000 |
| 006C0110 | 50 | 80070057/80040110/8007000E | 006C0174 FF10 | 006C0182 FF5220 | 006C0128 | 006C017E | 4×C21000 |
| 006C0290 | 49 | 80070057/80040110/8007000E | 006C02EF FF10 | 006C02FD FF5220 | 006C02A8 | 006C02F9 | 4×C21000 |
| 006C0410 | 49 | 80070057/80040110/8007000E | 006C046F FF10 | 006C047D FF5220 | 006C0428 | 006C0479 | 4×C21000 |
| 006C0590 | 48 | 80070057/80040110/8007000E | 006C05EA FF10 | 006C05F8 FF5220 | 006C05A8 | 006C05F4 | 4×C21000 |
| 006C0710 | 48 | 80070057/80040110/8007000E | 006C076A FF10 | 006C0778 FF5220 | 006C0728 | 006C0774 | 4×C21000 |
| 006C0890 | 48 | 80070057/80040110/8007000E | 006C08EA FF10 | 006C08F8 FF5220 | 006C08A8 | 006C08F4 | 4×C21000 |
| 006C0A10 | 48 | 80070057/80040110/8007000E | 006C0A6A FF10 | 006C0A78 FF5220 | 006C0A28 | 006C0A74 | 4×C21000 |
| 006C0B90 | 48 | 80070057/80040110/8007000E | 006C0BEA FF10 | 006C0BF8 FF5220 | 006C0BA8 | 006C0BF4 | 4×C21000 |
| 006C0D10 | 48 | 80070057/80040110/8007000E | 006C0D6A FF10 | 006C0D78 FF5220 | 006C0D28 | 006C0D74 | 4×C21000 |
| 006C0E90 | 48 | 80070057/80040110/8007000E | 006C0EEA FF10 | 006C0EF8 FF5220 | 006C0EA8 | 006C0EF4 | 4×C21000 |

## 3. 逐行判定

> 五查记法：**查1=②** 类身份独立成立；**查2=③b** 具体形态（③b② 判据）；**查3=④** 使用见证独立成立；**查4=④②不同源**；**查5=语义与实测相符**。


### 1. `006BF810` — PASS（TClassFactory<Tactical> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F37F8  slot#3 @ 007F3804  bytes 10 F8 6B 00   → 值 == 本 entry
COL  00809E48 (vt-4)   sig=0 offset=0  → TD 00841098 → 名 .?AV?$TClassFactory@VTactical@@@@
vt 五槽: [0]006BF750 [1]006BF7C0 [2]006BF7E0 [3]006BF810 [4]006BF890
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VTactical@@@@`，与行名 `T_TClassFactory_VTactical__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006BF81B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006BF833  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006BF85B  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006BF83C  68 18 0E 00 00       push     0xe18
            006BF841  E8 D1 95 10 00       call     0x7c8e17   ; = operator new
构造        006BF84D  8B C8                mov      ecx, eax
QI 站点      006BF86D  FF 10        ; call dword ptr [eax]
消费点       006BF86F  8B F8 85        ; mov edi,eax
             006BF871  85 FF 7D        ; test edi,edi
             006BF873  7D 09 8B        ; jge -> 0x6bf87e （零间隔、无 eax 覆写）
失败路释放   006BF877  6A 01        ; push 1 (delete 标志)
             006BF87B  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006BF87E  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006BF821, 006BF839, 006BF861, 006BF882
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC5C6  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006BF740  装表 006BF749  C7 00 F8 37 7F 00   ; mov [reg], 007F37F8
注册  006BC5F0  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9950（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F37F8` 在全 `.text` **仅 1 处** imm32 引用（`006BF749`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`006D1D54` 写 `[esi+0]`）。

**本行裁定：PASS**，附**必改字**：④ 的 GUID 执行器写作 `7E9580`，实测 `007E9580` 是 **TClassFactory<VSuperClass>** 的 GUID（其 ctor 006BF5C0 在 `006BC5AE` 注册）—— 执行器错位到前一块；本行真实 GUID 为 `007E9950`（`006BC5EB push`）。④ 主张本身（活类对象已注册）不因此垮，但账上文字必须改。

### 2. `006BF990` — PASS（TClassFactory<CellClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3810  slot#3 @ 007F381C  bytes 90 F9 6B 00   → 值 == 本 entry
COL  00809E98 (vt-4)   sig=0 offset=0  → TD 008410C8 → 名 .?AV?$TClassFactory@VCellClass@@@@
vt 五槽: [0]006BF8D0 [1]006BF940 [2]006BF960 [3]006BF990 [4]006BFA10
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VCellClass@@@@`，与行名 `T_TClassFactory_VCellClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006BF99B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006BF9B3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006BF9DB  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006BF9BC  68 48 01 00 00       push     0x148
            006BF9C1  E8 51 94 10 00       call     0x7c8e17   ; = operator new
构造        006BF9CD  8B C8                mov      ecx, eax
QI 站点      006BF9ED  FF 10        ; call dword ptr [eax]
消费点       006BF9EF  8B F8 85        ; mov edi,eax
             006BF9F1  85 FF 7D        ; test edi,edi
             006BF9F3  7D 09 8B        ; jge -> 0x6bf9fe （零间隔、无 eax 覆写）
失败路释放   006BF9F7  6A 01        ; push 1 (delete 标志)
             006BF9FB  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006BF9FE  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006BF9A1, 006BF9B9, 006BF9E1, 006BFA02
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC603  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006BF8C0  装表 006BF8C9  C7 00 10 38 7F 00   ; mov [reg], 007F3810
注册  006BC62D  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9930（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3810` 在全 `.text` **仅 1 处** imm32 引用（`006BF8C9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`0047BD5C` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 3. `006BFB10` — PASS（TClassFactory<EMPulseClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3828  slot#3 @ 007F3834  bytes 10 FB 6B 00   → 值 == 本 entry
COL  00809EE8 (vt-4)   sig=0 offset=0  → TD 008410F8 → 名 .?AV?$TClassFactory@VEMPulseClass@@@@
vt 五槽: [0]006BFA50 [1]006BFAC0 [2]006BFAE0 [3]006BFB10 [4]006BFB90
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VEMPulseClass@@@@`，与行名 `T_TClassFactory_VEMPulseClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006BFB1B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006BFB33  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006BFB58  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006BFB3C  6A 34                push     0x34
            006BFB3E  E8 D4 92 10 00       call     0x7c8e17   ; = operator new
构造        006BFB4A  8B C8                mov      ecx, eax
QI 站点      006BFB6A  FF 10        ; call dword ptr [eax]
消费点       006BFB6C  8B F8 85        ; mov edi,eax
             006BFB6E  85 FF 7D        ; test edi,edi
             006BFB70  7D 09 8B        ; jge -> 0x6bfb7b （零间隔、无 eax 覆写）
失败路释放   006BFB74  6A 01        ; push 1 (delete 标志)
             006BFB78  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006BFB7B  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006BFB21, 006BFB39, 006BFB5E, 006BFB7F
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC640  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006BFA40  装表 006BFA49  C7 00 28 38 7F 00   ; mov [reg], 007F3828
注册  006BC66A  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9940（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3828` 在全 `.text` **仅 1 处** imm32 引用（`006BFA49`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`004C537D` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 4. `006BFC90` — PASS（TClassFactory<LightSourceClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3840  slot#3 @ 007F384C  bytes 90 FC 6B 00   → 值 == 本 entry
COL  00809F38 (vt-4)   sig=0 offset=0  → TD 00841128 → 名 .?AV?$TClassFactory@VLightSourceClass@@@@
vt 五槽: [0]006BFBD0 [1]006BFC40 [2]006BFC60 [3]006BFC90 [4]006BFD10
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VLightSourceClass@@@@`，与行名 `T_TClassFactory_VLightSourceClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006BFC9B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006BFCB3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006BFCD8  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006BFCBC  6A 4C                push     0x4c
            006BFCBE  E8 54 91 10 00       call     0x7c8e17   ; = operator new
构造        006BFCCA  8B C8                mov      ecx, eax
QI 站点      006BFCEA  FF 10        ; call dword ptr [eax]
消费点       006BFCEC  8B F8 85        ; mov edi,eax
             006BFCEE  85 FF 7D        ; test edi,edi
             006BFCF0  7D 09 8B        ; jge -> 0x6bfcfb （零间隔、无 eax 覆写）
失败路释放   006BFCF4  6A 01        ; push 1 (delete 标志)
             006BFCF8  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006BFCFB  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006BFCA1, 006BFCB9, 006BFCDE, 006BFCFF
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC67D  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006BFBC0  装表 006BFBC9  C7 00 40 38 7F 00   ; mov [reg], 007F3840
注册  006BC6A7  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E98F0（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3840` 在全 `.text` **仅 1 处** imm32 引用（`006BFBC9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`00554869` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 5. `006BFE10` — PASS（TClassFactory<SideClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3858  slot#3 @ 007F3864  bytes 10 FE 6B 00   → 值 == 本 entry
COL  00809F88 (vt-4)   sig=0 offset=0  → TD 00841160 → 名 .?AV?$TClassFactory@VSideClass@@@@
vt 五槽: [0]006BFD50 [1]006BFDC0 [2]006BFDE0 [3]006BFE10 [4]006BFE90
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VSideClass@@@@`，与行名 `T_TClassFactory_VSideClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006BFE1B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006BFE33  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006BFE5D  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006BFE3C  68 B4 00 00 00       push     0xb4
            006BFE41  E8 D1 8F 10 00       call     0x7c8e17   ; = operator new
构造        006BFE4F  8B C8                mov      ecx, eax
QI 站点      006BFE6F  FF 10        ; call dword ptr [eax]
消费点       006BFE71  8B F8 85        ; mov edi,eax
             006BFE73  85 FF 7D        ; test edi,edi
             006BFE75  7D 09 8B        ; jge -> 0x6bfe80 （零间隔、无 eax 覆写）
失败路释放   006BFE79  6A 01        ; push 1 (delete 标志)
             006BFE7D  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006BFE80  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006BFE21, 006BFE39, 006BFE63, 006BFE84
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC6BA  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006BFD40  装表 006BFD49  C7 00 58 38 7F 00   ; mov [reg], 007F3858
注册  006BC6E4  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9910（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3858` 在全 `.text` **仅 1 处** imm32 引用（`006BFD49`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`006A4597` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 6. `006BFF90` — FAIL（TClassFactory<TiberiumClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3870  slot#3 @ 007F387C  bytes 90 FF 6B 00   → 值 == 本 entry
COL  00809FD8 (vt-4)   sig=0 offset=0  → TD 00841190 → 名 .?AV?$TClassFactory@VTiberiumClass@@@@
vt 五槽: [0]006BFED0 [1]006BFF40 [2]006BFF60 [3]006BFF90 [4]006C0010
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VTiberiumClass@@@@`，与行名 `T_TClassFactory_VTiberiumClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006BFF9B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006BFFB3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006BFFDD  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006BFFBC  68 28 01 00 00       push     0x128
            006BFFC1  E8 51 8E 10 00       call     0x7c8e17   ; = operator new
构造        006BFFCF  8B C8                mov      ecx, eax
QI 站点      006BFFEF  FF 10        ; call dword ptr [eax]
消费点       006BFFF1  8B F8 85        ; mov edi,eax
             006BFFF3  85 FF 7D        ; test edi,edi
             006BFFF5  7D 09 8B        ; jge -> 0x6c0000 （零间隔、无 eax 覆写）
失败路释放   006BFFF9  6A 01        ; push 1 (delete 标志)
             006BFFFD  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0000  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006BFFA1, 006BFFB9, 006BFFE3, 006C0004
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**⇒ 查2 在本行文字层面不成立（本行判 FAIL 的唯一原因，见 §4）。** 但函数整体合同（上表）真实：主虚表为 `007F5728`（ctor `007216C0` 于 `007217A6` 写 `[esi+0]`），其槽 0 = `00410260`，即上段那套 HRESULT 契约。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC6F7  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006BFEC0  装表 006BFEC9  C7 00 70 38 7F 00   ; mov [reg], 007F3870
注册  006BC721  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9920（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3870` 在全 `.text` **仅 1 处** imm32 引用（`006BFEC9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 方向对、但 ③b 归因错**：`写出接口指针到 ppvOut，非读入` 实测成立（入口 `mov dword ptr [edi],0` 先置空、QI 收 `push edi` 并写回）；**但**第 4 列把「新建对象主 vt」写成内嵌成员表、把其 slot0 写成 QueryInterface，属**成链点归因错误**（不是方向反写，也不是 ③a/③b 子型标错）；按卡面「证据不足判 FAIL」与上批「地址全真 ≠ 主张成立」口径，本行判 FAIL。

**本行裁定：FAIL**（理由见 §4：③b 的成链地址与错误码证据被指向内嵌成员表与 VC 器析构函数，其自陈常量表为空 ⇒ 该行文字未构成取证）。

### 7. `006C0110` — PASS（TClassFactory<TubeClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3888  slot#3 @ 007F3894  bytes 10 01 6C 00   → 值 == 本 entry
COL  0080A028 (vt-4)   sig=0 offset=0  → TD 008411C0 → 名 .?AV?$TClassFactory@VTubeClass@@@@
vt 五槽: [0]006C0050 [1]006C00C0 [2]006C00E0 [3]006C0110 [4]006C0190
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VTubeClass@@@@`，与行名 `T_TClassFactory_VTubeClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C011B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C0133  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C0162  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C013C  68 C4 01 00 00       push     0x1c4
            006C0141  E8 D1 8C 10 00       call     0x7c8e17   ; = operator new
构造        006C0154  8B C8                mov      ecx, eax
QI 站点      006C0174  FF 10        ; call dword ptr [eax]
消费点       006C0176  8B F8 85        ; mov edi,eax
             006C0178  85 FF 7D        ; test edi,edi
             006C017A  7D 09 8B        ; jge -> 0x6c0185 （零间隔、无 eax 覆写）
失败路释放   006C017E  6A 01        ; push 1 (delete 标志)
             006C0182  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0185  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C0121, 006C0139, 006C0168, 006C0189
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC734  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C0040  装表 006C0049  C7 00 88 38 7F 00   ; mov [reg], 007F3888
注册  006BC75E  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9750（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3888` 在全 `.text` **仅 1 处** imm32 引用（`006C0049`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`00727FFD` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 8. `006C0290` — PASS（TClassFactory<CampaignClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F38A0  slot#3 @ 007F38AC  bytes 90 02 6C 00   → 值 == 本 entry
COL  0080A078 (vt-4)   sig=0 offset=0  → TD 008411F0 → 名 .?AV?$TClassFactory@VCampaignClass@@@@
vt 五槽: [0]006C01D0 [1]006C0240 [2]006C0260 [3]006C0290 [4]006C0310
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VCampaignClass@@@@`，与行名 `T_TClassFactory_VCampaignClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C029B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C02B3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C02DD  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C02BC  68 A0 03 00 00       push     0x3a0
            006C02C1  E8 51 8B 10 00       call     0x7c8e17   ; = operator new
构造        006C02CF  8B C8                mov      ecx, eax
QI 站点      006C02EF  FF 10        ; call dword ptr [eax]
消费点       006C02F1  8B F8 85        ; mov edi,eax
             006C02F3  85 FF 7D        ; test edi,edi
             006C02F5  7D 09 8B        ; jge -> 0x6c0300 （零间隔、无 eax 覆写）
失败路释放   006C02F9  6A 01        ; push 1 (delete 标志)
             006C02FD  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0300  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C02A1, 006C02B9, 006C02E3, 006C0304
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC771  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C01C0  装表 006C01C9  C7 00 A0 38 7F 00   ; mov [reg], 007F38A0
注册  006BC79B  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9900（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F38A0` 在全 `.text` **仅 1 处** imm32 引用（`006C01C9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`0046CB70` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 9. `006C0410` — PASS（TClassFactory<BuildingLightClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F38B8  slot#3 @ 007F38C4  bytes 10 04 6C 00   → 值 == 本 entry
COL  0080A0C8 (vt-4)   sig=0 offset=0  → TD 00841220 → 名 .?AV?$TClassFactory@VBuildingLightClass@@@@
vt 五槽: [0]006C0350 [1]006C03C0 [2]006C03E0 [3]006C0410 [4]006C0490
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VBuildingLightClass@@@@`，与行名 `T_TClassFactory_VBuildingLightClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C041B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C0433  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C045D  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C043C  68 E8 00 00 00       push     0xe8
            006C0441  E8 D1 89 10 00       call     0x7c8e17   ; = operator new
构造        006C044F  8B C8                mov      ecx, eax
QI 站点      006C046F  FF 10        ; call dword ptr [eax]
消费点       006C0471  8B F8 85        ; mov edi,eax
             006C0473  85 FF 7D        ; test edi,edi
             006C0475  7D 09 8B        ; jge -> 0x6c0480 （零间隔、无 eax 覆写）
失败路释放   006C0479  6A 01        ; push 1 (delete 标志)
             006C047D  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0480  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C0421, 006C0439, 006C0463, 006C0484
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC7AE  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C0340  装表 006C0349  C7 00 B8 38 7F 00   ; mov [reg], 007F38B8
注册  006BC7D8  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9730（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F38B8` 在全 `.text` **仅 1 处** imm32 引用（`006C0349`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`004358AF` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 10. `006C0590` — PASS（TClassFactory<WaypointPathClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F38D0  slot#3 @ 007F38DC  bytes 90 05 6C 00   → 值 == 本 entry
COL  0080A118 (vt-4)   sig=0 offset=0  → TD 00841258 → 名 .?AV?$TClassFactory@VWaypointPathClass@@@@
vt 五槽: [0]006C04D0 [1]006C0540 [2]006C0560 [3]006C0590 [4]006C0610
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VWaypointPathClass@@@@`，与行名 `T_TClassFactory_VWaypointPathClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C059B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C05B3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C05D8  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C05BC  6A 40                push     0x40
            006C05BE  E8 54 88 10 00       call     0x7c8e17   ; = operator new
构造        006C05CA  8B C8                mov      ecx, eax
QI 站点      006C05EA  FF 10        ; call dword ptr [eax]
消费点       006C05EC  8B F8 85        ; mov edi,eax
             006C05EE  85 FF 7D        ; test edi,edi
             006C05F0  7D 09 8B        ; jge -> 0x6c05fb （零间隔、无 eax 覆写）
失败路释放   006C05F4  6A 01        ; push 1 (delete 标志)
             006C05F8  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C05FB  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C05A1, 006C05B9, 006C05DE, 006C05FF
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC7EB  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C04C0  装表 006C04C9  C7 00 D0 38 7F 00   ; mov [reg], 007F38D0
注册  006BC815  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9850（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F38D0` 在全 `.text` **仅 1 处** imm32 引用（`006C04C9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`0076375F` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 11. `006C0710` — PASS（TClassFactory<TemporalClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F38E8  slot#3 @ 007F38F4  bytes 10 07 6C 00   → 值 == 本 entry
COL  0080A168 (vt-4)   sig=0 offset=0  → TD 00841290 → 名 .?AV?$TClassFactory@VTemporalClass@@@@
vt 五槽: [0]006C0650 [1]006C06C0 [2]006C06E0 [3]006C0710 [4]006C0790
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VTemporalClass@@@@`，与行名 `T_TClassFactory_VTemporalClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C071B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C0733  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C0758  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C073C  6A 50                push     0x50
            006C073E  E8 D4 86 10 00       call     0x7c8e17   ; = operator new
构造        006C074A  8B C8                mov      ecx, eax
QI 站点      006C076A  FF 10        ; call dword ptr [eax]
消费点       006C076C  8B F8 85        ; mov edi,eax
             006C076E  85 FF 7D        ; test edi,edi
             006C0770  7D 09 8B        ; jge -> 0x6c077b （零间隔、无 eax 覆写）
失败路释放   006C0774  6A 01        ; push 1 (delete 标志)
             006C0778  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C077B  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C0721, 006C0739, 006C075E, 006C077F
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC828  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C0640  装表 006C0649  C7 00 E8 38 7F 00   ; mov [reg], 007F38E8
注册  006BC852  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E98D0（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F38E8` 在全 `.text` **仅 1 处** imm32 引用（`006C0649`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`0071A467` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 12. `006C0890` — PASS（TClassFactory<AirstrikeClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3900  slot#3 @ 007F390C  bytes 90 08 6C 00   → 值 == 本 entry
COL  0080A1B8 (vt-4)   sig=0 offset=0  → TD 008412C0 → 名 .?AV?$TClassFactory@VAirstrikeClass@@@@
vt 五槽: [0]006C07D0 [1]006C0840 [2]006C0860 [3]006C0890 [4]006C0910
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VAirstrikeClass@@@@`，与行名 `T_TClassFactory_VAirstrikeClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C089B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C08B3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C08D8  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C08BC  6A 60                push     0x60
            006C08BE  E8 54 85 10 00       call     0x7c8e17   ; = operator new
构造        006C08CA  8B C8                mov      ecx, eax
QI 站点      006C08EA  FF 10        ; call dword ptr [eax]
消费点       006C08EC  8B F8 85        ; mov edi,eax
             006C08EE  85 FF 7D        ; test edi,edi
             006C08F0  7D 09 8B        ; jge -> 0x6c08fb （零间隔、无 eax 覆写）
失败路释放   006C08F4  6A 01        ; push 1 (delete 标志)
             006C08F8  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C08FB  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C08A1, 006C08B9, 006C08DE, 006C08FF
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC865  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C07C0  装表 006C07C9  C7 00 00 39 7F 00   ; mov [reg], 007F3900
注册  006BC88F  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E98E0（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3900` 在全 `.text` **仅 1 处** imm32 引用（`006C07C9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`0041D308` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 13. `006C0A10` — FAIL（TClassFactory<SpawnManagerClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3918  slot#3 @ 007F3924  bytes 10 0A 6C 00   → 值 == 本 entry
COL  0080A208 (vt-4)   sig=0 offset=0  → TD 008412F0 → 名 .?AV?$TClassFactory@VSpawnManagerClass@@@@
vt 五槽: [0]006C0950 [1]006C09C0 [2]006C09E0 [3]006C0A10 [4]006C0A90
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VSpawnManagerClass@@@@`，与行名 `T_TClassFactory_VSpawnManagerClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C0A1B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C0A33  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C0A58  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C0A3C  6A 74                push     0x74
            006C0A3E  E8 D4 83 10 00       call     0x7c8e17   ; = operator new
构造        006C0A4A  8B C8                mov      ecx, eax
QI 站点      006C0A6A  FF 10        ; call dword ptr [eax]
消费点       006C0A6C  8B F8 85        ; mov edi,eax
             006C0A6E  85 FF 7D        ; test edi,edi
             006C0A70  7D 09 8B        ; jge -> 0x6c0a7b （零间隔、无 eax 覆写）
失败路释放   006C0A74  6A 01        ; push 1 (delete 标志)
             006C0A78  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0A7B  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C0A21, 006C0A39, 006C0A5E, 006C0A7F
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**⇒ 查2 在本行文字层面不成立（本行判 FAIL 的唯一原因，见 §4）。** 但函数整体合同（上表）真实：主虚表为 `007F3650`（ctor `006B6EA0` 于 `006B6EE6` 写 `[esi+0]`），其槽 0 = `00410260`，即上段那套 HRESULT 契约。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC8A2  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C0940  装表 006C0949  C7 00 18 39 7F 00   ; mov [reg], 007F3918
注册  006BC8CC  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9860（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3918` 在全 `.text` **仅 1 处** imm32 引用（`006C0949`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 方向对、但 ③b 归因错**：`写出接口指针到 ppvOut，非读入` 实测成立（入口 `mov dword ptr [edi],0` 先置空、QI 收 `push edi` 并写回）；**但**第 4 列把「新建对象主 vt」写成内嵌成员表、把其 slot0 写成 QueryInterface，属**成链点归因错误**（不是方向反写，也不是 ③a/③b 子型标错）；按卡面「证据不足判 FAIL」与上批「地址全真 ≠ 主张成立」口径，本行判 FAIL。

**本行裁定：FAIL**（理由见 §4：③b 的成链地址与错误码证据被指向内嵌成员表与 VC 器析构函数，其自陈常量表为空 ⇒ 该行文字未构成取证）。

### 14. `006C0B90` — PASS（TClassFactory<SlaveManagerClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3930  slot#3 @ 007F393C  bytes 90 0B 6C 00   → 值 == 本 entry
COL  0080A258 (vt-4)   sig=0 offset=0  → TD 00841328 → 名 .?AV?$TClassFactory@VSlaveManagerClass@@@@
vt 五槽: [0]006C0AD0 [1]006C0B40 [2]006C0B60 [3]006C0B90 [4]006C0C10
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VSlaveManagerClass@@@@`，与行名 `T_TClassFactory_VSlaveManagerClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C0B9B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C0BB3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C0BD8  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C0BBC  6A 64                push     0x64
            006C0BBE  E8 54 82 10 00       call     0x7c8e17   ; = operator new
构造        006C0BCA  8B C8                mov      ecx, eax
QI 站点      006C0BEA  FF 10        ; call dword ptr [eax]
消费点       006C0BEC  8B F8 85        ; mov edi,eax
             006C0BEE  85 FF 7D        ; test edi,edi
             006C0BF0  7D 09 8B        ; jge -> 0x6c0bfb （零间隔、无 eax 覆写）
失败路释放   006C0BF4  6A 01        ; push 1 (delete 标志)
             006C0BF8  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0BFB  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C0BA1, 006C0BB9, 006C0BDE, 006C0BFF
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC8DF  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C0AC0  装表 006C0AC9  C7 00 30 39 7F 00   ; mov [reg], 007F3930
注册  006BC909  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9870（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3930` 在全 `.text` **仅 1 处** imm32 引用（`006C0AC9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`006AF39B` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 15. `006C0D10` — PASS（TClassFactory<CaptureManagerClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3948  slot#3 @ 007F3954  bytes 10 0D 6C 00   → 值 == 本 entry
COL  0080A2A8 (vt-4)   sig=0 offset=0  → TD 00841360 → 名 .?AV?$TClassFactory@VCaptureManagerClass@@@@
vt 五槽: [0]006C0C50 [1]006C0CC0 [2]006C0CE0 [3]006C0D10 [4]006C0D90
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VCaptureManagerClass@@@@`，与行名 `T_TClassFactory_VCaptureManagerClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C0D1B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C0D33  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C0D58  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C0D3C  6A 50                push     0x50
            006C0D3E  E8 D4 80 10 00       call     0x7c8e17   ; = operator new
构造        006C0D4A  8B C8                mov      ecx, eax
QI 站点      006C0D6A  FF 10        ; call dword ptr [eax]
消费点       006C0D6C  8B F8 85        ; mov edi,eax
             006C0D6E  85 FF 7D        ; test edi,edi
             006C0D70  7D 09 8B        ; jge -> 0x6c0d7b （零间隔、无 eax 覆写）
失败路释放   006C0D74  6A 01        ; push 1 (delete 标志)
             006C0D78  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0D7B  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C0D21, 006C0D39, 006C0D5E, 006C0D7F
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC91C  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C0C40  装表 006C0C49  C7 00 48 39 7F 00   ; mov [reg], 007F3948
注册  006BC946  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9880（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3948` 在全 `.text` **仅 1 处** imm32 引用（`006C0C49`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`004718BC` 写 `[esi+0]`）。

**本行裁定：PASS**。

### 16. `006C0E90` — PASS（TClassFactory<DiskLaserClass> 槽 3）

**查1 ② 类身份**（独立自取）

```
vt   007F3960  slot#3 @ 007F396C  bytes 90 0E 6C 00   → 值 == 本 entry
COL  0080A2F8 (vt-4)   sig=0 offset=0  → TD 00841398 → 名 .?AV?$TClassFactory@VDiskLaserClass@@@@
vt 五槽: [0]006C0DD0 [1]006C0E40 [2]006C0E60 [3]006C0E90 [4]006C0F10
```

槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `.?AV?$TClassFactory@VDiskLaserClass@@@@`，与行名 `T_TClassFactory_VDiskLaserClass__::slot3` 自洽。**成立**。

**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

```
入口三闸（互斥、动作不同、各返不同 imm 错误码）:
  006C0E9B  B8 57 00 07 80 5E   ; ppvOut==NULL → E_INVALIDARG
  006C0EB3  B8 10 01 04 80 5E   ; pUnkOuter!=NULL → CLASS_E_NOAGGREGATION
  006C0ED8  B8 0E 00 07 80 5E   ; new/ctor==NULL → E_OUTOFMEMORY
分配        006C0EBC  6A 40                push     0x40
            006C0EBE  E8 54 7F 10 00       call     0x7c8e17   ; = operator new
构造        006C0ECA  8B C8                mov      ecx, eax
QI 站点      006C0EEA  FF 10        ; call dword ptr [eax]
消费点       006C0EEC  8B F8 85        ; mov edi,eax
             006C0EEE  85 FF 7D        ; test edi,edi
             006C0EF0  7D 09 8B        ; jge -> 0x6c0efb （零间隔、无 eax 覆写）
失败路释放   006C0EF4  6A 01        ; push 1 (delete 标志)
             006C0EF8  FF 52 20        ; call dword ptr [edx+0x20]
成功/失败汇合 006C0EFB  8B C7        ; mov eax,edi
返回约定     4 处 ret 0x10: 006C0EA1, 006C0EB9, 006C0EDE, 006C0EFF
```

被调 QI 的返回约定（我自己反汇编 `00410260`，60 条指令）:

```
  00410269  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER
  00410286  mov [eax],0                    ; 先置空 *ppv（写出方向）
  004102E6  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE
  004102F5  xor eax,eax   / ret 0xC        ; 命中 → S_OK
  共 3 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）
```

**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。

**查3 ④ 使用见证**（活的工厂实例，非 direct-only）

```
宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)
分配  006BC959  6A 08   ; push 8 (sizeof(TClassFactory))
ctor  006C0DC0  装表 006C0DC9  C7 00 60 39 7F 00   ; mov [reg], 007F3960
注册  006BC983  FF D6   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)
GUID  实为 007E9890（执行器写：见下）
```

`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。

- 该工厂 vt `007F3960` 在全 `.text` **仅 1 处** imm32 引用（`006C0DC9`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。
- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。

**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。

**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`004A7A3A` 写 `[esi+0]`）。

**本行裁定：PASS**。

## 4. 两个 FAIL 的成因（同一种机械替换，落在 ③b 的成链点上）

两行的失败形态完全一致：不是"锚不干净"，而是**把错误的函数指认成了 QueryInterface**：

| entry | 执行器写的"主 vt / slot0=QueryInterface" | 实测真相 |
|---|---|---|
| `006BFF90` | 主 vt `007EB6D4`、slot0=`00524FC0` | 主 vt `007F5728`（`007217A6 C7 06 28 57 7F 00` 写 `[esi+0]`）、slot0=`00410260` |
| `006C0A10` | 主 vt `007F36B4`、slot0=`006B8790` | 主 vt `007F3650`（`006B6EE6 C7 06 50 36 7F 00` 写 `[esi+0]`）、slot0=`00410260` |

`007EB6D4` 与 `007F36B4` 的来历（我逐条核过 ctor）：

```
; 007216C0 TiberiumClass ctor
007216D6  8D BE C4 00 00 00     lea edi,[esi+0xC4]        ; ← 内嵌成员，不是 this
00721734  C7 07 D4 B6 7E 00     mov [edi],0x7EB6D4         ; TypeList<AnimTypeClass*> 的表
007217A6  C7 06 28 57 7F 00     mov [esi],0x7F5728         ; ← 真正的主虚表

; 006B6EA0 SpawnManagerClass ctor
006B6EAF  8D 7E 38             lea edi,[esi+0x38]         ; ← 内嵌成员
006B6EBB  C7 07 B4 36 7F 00     mov [edi],0x7F36B4         ; DynamicVectorClass<SpawnControl*> 的表
006B6EE6  C7 06 50 36 7F 00     mov [esi],0x7F3650         ; ← 真正的主虚表
```

而被当成 "QueryInterface" 的两个函数，其实是 **`VectorClass<T>` 的析构式函数**（同一模板两份实例）：

```
00524FC0  56              push esi
00524FC1  8B F1           mov esi,ecx
00524FC3  8B 46 04        mov eax,[esi+4]
00524FC6  C7 06 F4 B6 7E 00  mov [esi],0x7EB6F4     ; ← 改装 VectorClass 表
00524FD8  E8 60 3B 2A 00  call 0x7C8B3D            ; free 元素数组
00524FF8  74 09           je ...
00524FFA  56 / E8 ...
00525006  C2 04 00        ret 4                    ; 带 delete 标志位
006B8790  同型（C7 06 D4 36 7F 00 装 0x7F36D4）
```

它们既不比较 IID、也不写 `*ppvOut`、也不返回 HRESULT 三态。因此执行器那两句
"新建 X 对象主 vt 007Exxxx 的 slot0=QueryInterface 00524FC0/006B8790 … 失败返 0x80004002(E_NOINTERFACE)/0x80004003(E_POINTER)、成功返 0"
**在它自己点名的函数上为假**；其自陈的可伪证常量表恰好是空的（delta 原文写作「常量 、1 处 ret」），说明它并未取得该证据却仍照发了模板句。

> **这与上一批 `S15S16_3B2\_audit` 的 FAIL 形态同类**（"地址全真 ≠ 主张成立"、"不解析就 PASS 等于放行一个未验证前提"）。
> 但须与本轮 Lead 的 ③ 放宽裁定区分：放宽的是"③ 不必落在 survey 命中的站点"，**不是**"③ 的成链点可以指错函数"。

**可救性（给 Lead 的判断材料）**：两行的函数整体合同真实存在（主 vt `007F5728`/`007F3650` 槽 0 均为 `00410260`，即 14 行同款 QI 契约，三码 + 3 处 ret 齐备）。**改字后即可重提**，不必重挖。

## 5. 本批另外两处必须改字（不构成 FAIL，但不得按原文并入）

1. **`006BF810` 的 GUID 错位**：原文"以 CLSID 7E9580 经 CoRegisterClassObject 注册"。实测 `007E9580` 属前一块（ctor `006BF5C0`，即 `TClassFactory<VSuperClass>`，注册点 `006BC5AE`）；本行真实 GUID 为 **`007E9950`**（`006BC5EB push`）。
2. **11 行 GUID 写成 `None`**（`006BFF90` 起至 `006C0E90` 共 11 行）：实测全部可解析，见下表。`None` 不是错值，但按卡面"给地址"的要求属**未取证**，并入前须补齐。

| entry | 工厂 ctor | GUID |
|---|---|---|

| 006BF810 | 006BF740 | 007E9950 |
| 006BF990 | 006BF8C0 | 007E9930 |
| 006BFB10 | 006BFA40 | 007E9940 |
| 006BFC90 | 006BFBC0 | 007E98F0 |
| 006BFE10 | 006BFD40 | 007E9910 |
| 006BFF90 | 006BFEC0 | 007E9920 |
| 006C0110 | 006C0040 | 007E9750 |
| 006C0290 | 006C01C0 | 007E9900 |
| 006C0410 | 006C0340 | 007E9730 |
| 006C0590 | 006C04C0 | 007E9850 |
| 006C0710 | 006C0640 | 007E98D0 |
| 006C0890 | 006C07C0 | 007E98E0 |
| 006C0A10 | 006C0940 | 007E9860 |
| 006C0B90 | 006C0AC0 | 007E9870 |
| 006C0D10 | 006C0C40 | 007E9880 |
| 006C0E90 | 006C0DC0 | 007E9890 |

## 6. 关于"16 行是否共用同一段取证文字"（Lead 点名要答）

**结论：语义文字确认是同一段模板（逐行替换类名/地址）；但 16 个函数体本身也是同一 C++ 模板的 16 次实例化 —— 所以"文字相同"本身不等于造假，判据只能是"每行的替换值是否为该行字节的真值"。逐行核完的结果是 14 真 / 2 假。**

证据与做法：

1. **文字层**：把 16 行 `one_line_semantics` 的地址与类名替换掉做归一化，16 行**收敛为同一段**（唯一差异是 `常量` 括号与 `CLSID` 值）。⇒ 文字确实是模板。
2. **代码层**：把每行函数体的立即数归一化后逐条比对，**11 行完全相同、5 行差 1–2 条**（差在构造器参数 push 与 `sizeof` 不同）。这是模板实例化的正常形态，不是复制粘贴代码。
3. **真值层**（这才是判据）：对每行**逐个替换值**回字节核 —— ② 的 vt/槽/COL/TD/类名、③b 的 QI 站点/释放站点/push 1/三码/4 个 ret、④ 的分配点/ctor/装表点/注册点/GUID。
   - **14 行**：三类替换值全部命中本行字节。
   - **2 行**（`006BFF90` / `006C0A10`）：③b 的"主 vt / slot0"替换值**不是本行的值**（取了 ctor 里内嵌成员表），且其可伪证常量表为空 ⇒ 机械替换的痕迹在这里变成**假陈述**。
4. 因此：**这批不是"16 行共用一段空洞文字"（14 行各自站得住），但也绝不是"16 行逐行取证"（2 行的 ③b 成链是假的、1 行的 GUID 错位、11 行 GUID 未解析）。**

## 7. 判定汇总

- **PASS 14 / FAIL 2**
- FAIL：`006BFF90`、`006C0A10`（均为 ③b 成链指向内嵌成员表 + VC 器析构函数；函数整体合同真实，改字后可重提）
- 另需改字（不影响 PASS）：`006BF810` 的 GUID `7E9580`→`007E9950`；11 行 `CLSID None` 补真值（见 §5 表）。
- 逐行判定表：`verdict.tsv`（16 行）；概要：`SUMMARY.md`；可复算脚本与原始输出：`work\`。
