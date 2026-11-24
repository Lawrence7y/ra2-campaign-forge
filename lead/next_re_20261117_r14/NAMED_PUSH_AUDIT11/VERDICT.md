# VERDICT — NAMED_PUSH_S22_B3 异族独立审计（11 行）

- 目标：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
- SHA-256：`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（本审计用 `hashlib` 自算，与卡面期望一致）
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（本审计以 PE 节表实测：`.text` VA `0x401000`，VirtualSize `0x3DF38D`）
- 工具：capstone **5.0.7**（`skipdata=True`）+ pefile **2024.8.26**，Python **3.12.10**，无 venv、未 pip install
- 取证脚本：`_work\pe.py`（PE/VA 映射 + RTTI 链 + 全 `.text` 指令边界扫描）+ `_work\s1..s23_*.py`；原始输出 `_work\s*_out.txt`
- **未引用**执行器 `EVIDENCE\ROW_*.txt` 作为证据；行内每个地址/字节均由本审计脚本本机反汇编得出（下文 `sNN` 指脚本编号）

## 判定口径（照 `R14_COMMON.md` §8.6 / §12.3 / 错源 ㉓）

- ② `[vt-4]=COL → [COL+0xC]=TD → TD+8 串`，且 `vt[slot]==entry`
- ③b② 可证伪错误码/返回约定（D-46(A) 窄读：只认错误码/返回约定）
- ④ direct call 或 活 vtable 槽位派发（构造器装的活表 + `vt[slot]==entry` + site 不共用）；`atexit` 析构器装的表不算（㉓）
- ②④ 不得同源（同一个虚表槽不能既证身份又证被使用）

## 本批 11 行的共同结构（先给一次，逐行只写差异）

11 行全部是 `TClassFactory<V<Xxx>Class>` 的 **slot3（IClassFactory::CreateInstance）**，位于一段连续的类工厂区
`[006C2A40, 006C3E00)`。该区每个工厂类占 4 个函数：`ctor`（trampoline 装表）、`slot0=QI`、`slot1=AddRef`、
`slot2=Release`、`slot3=本 entry`、`slot4=LockServer`。实测例（`006C2B10` 所在工厂 007F3B28）：

```
007F3B24  COL 0080A8E8          ; vt-4
007F3B28  slot0 006C2A50  QI(this,riid,ppv)  ret 0xc，ppv 空返 0x80004003
007F3B2C  slot1 006C2AC0  AddRef(this)       InterlockedIncrement [this+4]，ret 4
007F3B30  slot2 006C2AE0  Release(this)      InterlockedDecrement [this+4]，ret 4
007F3B34  slot3 006C2B10  <<< 本 entry        CreateInstance  ret 0x10
007F3B38  slot4 006C2B90  LockServer(this,flag) ret 8
```

**该 vtable 是「显式 this 的 stdcall」**：`QI(this,riid,ppv)` 3 栈参→`ret 0xc`；`AddRef/Release(this)` 1 栈参→`ret 4`；
`slot3(this,pUnkOuter,riid,ppvOut)` 4 栈参→`ret 0x10`。四个栈参与 `IClassFactory::CreateInstance` 完全自洽
（本审计最初按 thiscall 误算成「多一个参数」，已用 `_work\s13_qi.py`/`s19_iid.py` 逐槽复算纠正）。

**「主虚表 slot0 = 00410260」这条约束指的是体内新建对象的对象主虚表，不是工厂自身虚表**（工厂自身 `vt[0]=006C2A50`，
是该工厂的 QI）。本审计对 11 行逐一追了 `alloc → ctor → mov [this],vt`，取 **this 寄存器**上的偏移 0 写点，
再用 `[vt-4]→COL→TD→名串` 验类名，结果全部命中「对象主虚表 `vt[0]=00410260` 且类名 = 工厂模板实参」。

---

## 006C2B10 — `T_TClassFactory_VAircraftTypeClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3B28+12 = 007F3B34`（slot#3），该 4 字节值 `006C2B10` 即本 entry。
- `[vt-4] = 0080A8E8`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841748`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VAircraftTypeClass@@@@`。类名与行名中的 `TClassFactory<VAircraftTypeClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C2A50`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C2B1B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C2B33` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C2B5D` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 3600` → `call 0x7C8E17`(@`006C2B41`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 0041C8B0`。
- 主站点：`006C2B6F` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c2b80`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C2B79` `push 1` + `mov ecx,esi` + `006C2B7D` `call [edx+0x20]`（=主虚表 slot8 = `0041CFE0`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C2A49`：`mov dword ptr [eax], 007F3B28`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E95B0`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCE0A`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3B28` 在**整个 `.text` 只有 1 处 imm 写点**（`006C2A49`），无析构器写点、无成对死表；写入者 `006C2A40` 是 ctor，其唯一调用者是初始化函数内的 `006BCE0A` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080A8E8` / TD `00841748` / 名串）与槽值 `007F3B28+12`；④ 的取材料是 `.text` 的装表指令 `006C2A49` 与注册指令 `006BCE0A`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 AircraftTypeClass 对象主 vt `007E2868` 的 slot0=`00410260`」：本审计追 `0041C8B0` 得 `0041C900` 处 `mov [this], 007E2868`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVAircraftTypeClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `0041C906`(dst `eax`) → `007E284C` (.?AVAircraftTypeClass@@) — ctor 内首个 ret 之前
  - `0041C90C`(dst `esi + 8`) → `007E2844` (.?AVAircraftTypeClass@@) — ctor 内首个 ret 之前
  - `0041C913`(dst `esi + 0xc`) → `007E283C` (.?AVAircraftTypeClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVAircraftTypeClass@@` 的那一处（`0041C900`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C2C90 — `T_TClassFactory_VInfantryTypeClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3B40+12 = 007F3B4C`（slot#3），该 4 字节值 `006C2C90` 即本 entry。
- `[vt-4] = 0080A938`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841780`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VInfantryTypeClass@@@@`。类名与行名中的 `TClassFactory<VInfantryTypeClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C2BD0`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C2C9B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C2CB3` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C2CDD` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 3792` → `call 0x7C8E17`(@`006C2CC1`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 005236A0`。
- 主站点：`006C2CEF` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c2d00`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C2CF9` `push 1` + `mov ecx,esi` + `006C2CFD` `call [edx+0x20]`（=主虚表 slot8 = `00524D70`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C2BC9`：`mov dword ptr [eax], 007F3B40`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E95A0`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCE47`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3B40` 在**整个 `.text` 只有 1 处 imm 写点**（`006C2BC9`），无析构器写点、无成对死表；写入者 `006C2BC0` 是 ctor，其唯一调用者是初始化函数内的 `006BCE47` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080A938` / TD `00841780` / 名串）与槽值 `007F3B40+12`；④ 的取材料是 `.text` 的装表指令 `006C2BC9` 与注册指令 `006BCE47`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 InfantryTypeClass 对象主 vt `007EB610` 的 slot0=`00410260`」：本审计追 `005236A0` 得 `005237E8` 处 `mov [this], 007EB610`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVInfantryTypeClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `00523709`(dst `edi`) → `007EB6D4` (.?AV?$TypeList@PBVAnimTypeClass@@@@) — ctor 内首个 ret 之前
  - `00523724`(dst `edi`) → `007EB6D4` (.?AV?$TypeList@PBVAnimTypeClass@@@@) — ctor 内首个 ret 之前
  - `0052373F`(dst `edi`) → `007E4DD8` (.?AV?$TypeList@H@@) — ctor 内首个 ret 之前
  - `005237EE`(dst `eax`) → `007EB5F4` (.?AVInfantryTypeClass@@) — ctor 内首个 ret 之前
  - `005237F4`(dst `esi + 8`) → `007EB5EC` (.?AVInfantryTypeClass@@) — ctor 内首个 ret 之前
  - `005237FB`(dst `esi + 0xc`) → `007EB5E4` (.?AVInfantryTypeClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVInfantryTypeClass@@` 的那一处（`005237E8`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C2E10 — `T_TClassFactory_VBulletTypeClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3B58+12 = 007F3B64`（slot#3），该 4 字节值 `006C2E10` 即本 entry。
- `[vt-4] = 0080A988`（COL，位于 `.rdata`）→ `[COL+0xC] = 008417B8`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VBulletTypeClass@@@@`。类名与行名中的 `TClassFactory<VBulletTypeClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C2D50`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C2E1B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C2E33` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C2E5D` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 760` → `call 0x7C8E17`(@`006C2E41`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 0046BBC0`。
- 主站点：`006C2E6F` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c2e80`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C2E79` `push 1` + `mov ecx,esi` + `006C2E7D` `call [edx+0x20]`（=主虚表 slot8 = `0046C890`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C2D49`：`mov dword ptr [eax], 007F3B58`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E95D0`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCE84`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3B58` 在**整个 `.text` 只有 1 处 imm 写点**（`006C2D49`），无析构器写点、无成对死表；写入者 `006C2D40` 是 ctor，其唯一调用者是初始化函数内的 `006BCE84` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080A988` / TD `008417B8` / 名串）与槽值 `007F3B58+12`；④ 的取材料是 `.text` 的装表指令 `006C2D49` 与注册指令 `006BCE84`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 BulletTypeClass 对象主 vt `007E4948` 的 slot0=`00410260`」：本审计追 `0046BBC0` 得 `0046BCE6` 处 `mov [this], 007E4948`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVBulletTypeClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `0046BCEC`(dst `eax`) → `007E492C` (.?AVBulletTypeClass@@) — ctor 内首个 ret 之前
  - `0046BCF2`(dst `esi + 8`) → `007E4924` (.?AVBulletTypeClass@@) — ctor 内首个 ret 之前
  - `0046BCF9`(dst `esi + 0xc`) → `007E491C` (.?AVBulletTypeClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVBulletTypeClass@@` 的那一处（`0046BCE6`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C2F90 — `T_TClassFactory_VIsometricTileTypeClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3B70+12 = 007F3B7C`（slot#3），该 4 字节值 `006C2F90` 即本 entry。
- `[vt-4] = 0080A9D8`（COL，位于 `.rdata`）→ `[COL+0xC] = 008417F0`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VIsometricTileTypeClass@@@@`。类名与行名中的 `TClassFactory<VIsometricTileTypeClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C2ED0`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C2F9B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C2FB3` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C2FE5` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 780` → `call 0x7C8E17`(@`006C2FC1`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 005447C0`。
- 主站点：`006C2FF7` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3008`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C3001` `push 1` + `mov ecx,esi` + `006C3005` `call [edx+0x20]`（=主虚表 slot8 = `0054A170`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C2EC9`：`mov dword ptr [eax], 007F3B70`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E95F0`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCEC1`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3B70` 在**整个 `.text` 只有 1 处 imm 写点**（`006C2EC9`），无析构器写点、无成对死表；写入者 `006C2EC0` 是 ctor，其唯一调用者是初始化函数内的 `006BCEC1` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080A9D8` / TD `008417F0` / 名串）与槽值 `007F3B70+12`；④ 的取材料是 `.text` 的装表指令 `006C2EC9` 与注册指令 `006BCEC1`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 IsometricTileTypeClass 对象主 vt `007ECC48` 的 slot0=`00410260`」：本审计追 `005447C0` 得 `005448C8` 处 `mov [this], 007ECC48`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVIsometricTileTypeClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `00544811`(dst `ebp + 0x2a4`) → `007ECCEC` (.?AV?$DynamicVectorClass@PAG@@) — ctor 内首个 ret 之前
  - `005448CF`(dst `ebp + 4`) → `007ECC2C` (.?AVIsometricTileTypeClass@@) — ctor 内首个 ret 之前
  - `005448D6`(dst `ebp + 8`) → `007ECC24` (.?AVIsometricTileTypeClass@@) — ctor 内首个 ret 之前
  - `005448DD`(dst `ebp + 0xc`) → `007ECC1C` (.?AVIsometricTileTypeClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`ebp`) 且 RTTI 名 = `.?AVIsometricTileTypeClass@@` 的那一处（`005448C8`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C3110 — `T_TClassFactory_VOverlayTypeClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3B88+12 = 007F3B94`（slot#3），该 4 字节值 `006C3110` 即本 entry。
- `[vt-4] = 0080AA28`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841828`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VOverlayTypeClass@@@@`。类名与行名中的 `TClassFactory<VOverlayTypeClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C3050`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C311B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C3133` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C315D` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 700` → `call 0x7C8E17`(@`006C3141`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 005FE250`。
- 主站点：`006C316F` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3180`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C3179` `push 1` + `mov ecx,esi` + `006C317D` `call [edx+0x20]`（=主虚表 slot8 = `005FEF30`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C3049`：`mov dword ptr [eax], 007F3B88`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E9600`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCEFE`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3B88` 在**整个 `.text` 只有 1 处 imm 写点**（`006C3049`），无析构器写点、无成对死表；写入者 `006C3040` 是 ctor，其唯一调用者是初始化函数内的 `006BCEFE` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080AA28` / TD `00841828` / 名串）与槽值 `007F3B88+12`；④ 的取材料是 `.text` 的装表指令 `006C3049` 与注册指令 `006BCEFE`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 OverlayTypeClass 对象主 vt `007EF600` 的 slot0=`00410260`」：本审计追 `005FE250` 得 `005FE2F1` 处 `mov [this], 007EF600`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVOverlayTypeClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `005FE2F7`(dst `eax`) → `007EF5E4` (.?AVOverlayTypeClass@@) — ctor 内首个 ret 之前
  - `005FE2FD`(dst `esi + 8`) → `007EF5DC` (.?AVOverlayTypeClass@@) — ctor 内首个 ret 之前
  - `005FE304`(dst `esi + 0xc`) → `007EF5D4` (.?AVOverlayTypeClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVOverlayTypeClass@@` 的那一处（`005FE2F1`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C3290 — `T_TClassFactory_VSmudgeTypeClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3BA0+12 = 007F3BAC`（slot#3），该 4 字节值 `006C3290` 即本 entry。
- `[vt-4] = 0080AA78`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841860`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VSmudgeTypeClass@@@@`。类名与行名中的 `TClassFactory<VSmudgeTypeClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C31D0`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C329B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C32B3` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C32DD` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 676` → `call 0x7C8E17`(@`006C32C1`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 006B5260`。
- 主站点：`006C32EF` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3300`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C32F9` `push 1` + `mov ecx,esi` + `006C32FD` `call [edx+0x20]`（=主虚表 slot8 = `006B6160`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C31C9`：`mov dword ptr [eax], 007F3BA0`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E9610`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCF3B`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3BA0` 在**整个 `.text` 只有 1 处 imm 写点**（`006C31C9`），无析构器写点、无成对死表；写入者 `006C31C0` 是 ctor，其唯一调用者是初始化函数内的 `006BCF3B` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080AA78` / TD `00841860` / 名串）与槽值 `007F3BA0+12`；④ 的取材料是 `.text` 的装表指令 `006C31C9` 与注册指令 `006BCF3B`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 SmudgeTypeClass 对象主 vt `007F3528` 的 slot0=`00410260`」：本审计追 `006B5260` 得 `006B529B` 处 `mov [this], 007F3528`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVSmudgeTypeClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `006B52A1`(dst `eax`) → `007F350C` (.?AVSmudgeTypeClass@@) — ctor 内首个 ret 之前
  - `006B52A7`(dst `esi + 8`) → `007F3504` (.?AVSmudgeTypeClass@@) — ctor 内首个 ret 之前
  - `006B52AE`(dst `esi + 0xc`) → `007F34FC` (.?AVSmudgeTypeClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVSmudgeTypeClass@@` 的那一处（`006B529B`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C3410 — `T_TClassFactory_VUnitClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3BB8+12 = 007F3BC4`（slot#3），该 4 字节值 `006C3410` 即本 entry。
- `[vt-4] = 0080AAC8`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841898`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VUnitClass@@@@`。类名与行名中的 `TClassFactory<VUnitClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C3350`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C341B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C3433` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C345F` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 2280` → `call 0x7C8E17`(@`006C3441`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 007353C0`。
- 主站点：`006C3471` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3482`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C347B` `push 1` + `mov ecx,esi` + `006C347F` `call [edx+0x20]`（=主虚表 slot8 = `00746E80`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C3349`：`mov dword ptr [eax], 007F3BB8`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E96F0`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCF78`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3BB8` 在**整个 `.text` 只有 1 处 imm 写点**（`006C3349`），无析构器写点、无成对死表；写入者 `006C3340` 是 ctor，其唯一调用者是初始化函数内的 `006BCF78` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080AAC8` / TD `00841898` / 名串）与槽值 `007F3BB8+12`；④ 的取材料是 `.text` 的装表指令 `006C3349` 与注册指令 `006BCF78`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 UnitClass 对象主 vt `007F5C70` 的 slot0=`00410260`」：本审计追 `007353C0` 得 `0073543A` 处 `mov [this], 007F5C70`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVUnitClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `00735440`(dst `eax`) → `007F5C54` (.?AVUnitClass@@) — ctor 内首个 ret 之前
  - `00735446`(dst `esi + 8`) → `007F5C4C` (.?AVUnitClass@@) — ctor 内首个 ret 之前
  - `0073544D`(dst `esi + 0xc`) → `007F5C44` (.?AVUnitClass@@) — ctor 内首个 ret 之前
  - `0073579A`(dst `ebx`) → `007F5C54` (.?AVUnitClass@@) — **另一函数**（首个 ret @0073577D 之后）
  - `007357A0`(dst `esi + 8`) → `007F5C4C` (.?AVUnitClass@@) — **另一函数**（首个 ret @0073577D 之后）
  - `007357A7`(dst `esi + 0xc`) → `007F5C44` (.?AVUnitClass@@) — **另一函数**（首个 ret @0073577D 之后）

  ⚠ **同表另一写点**：`00735794` 也写 `007F5C70`。其中落在 ctor 之外（析构侧/另一个函数）的那处属 ㉓ 的「成对」形态；本行的 ④ 锚在**工厂表**（`007F3BB8`，装表点 `006C3349` 唯一），**未**拿对象表充当 ④，故不触发 ㉓。若仅凭「对象表的某处写点」判 ④，这一行会踩坑——本审计已排除该路径。

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVUnitClass@@` 的那一处（`0073543A`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C3590 — `T_TClassFactory_VBuildingClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3BD0+12 = 007F3BDC`（slot#3），该 4 字节值 `006C3590` 即本 entry。
- `[vt-4] = 0080AB18`（COL，位于 `.rdata`）→ `[COL+0xC] = 008418C8`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VBuildingClass@@@@`。类名与行名中的 `TClassFactory<VBuildingClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C34D0`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C359B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C35B3` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C35DF` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 1824` → `call 0x7C8E17`(@`006C35C1`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 0043B740`。
- 主站点：`006C35F1` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3602`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C35FB` `push 1` + `mov ecx,esi` + `006C35FF` `call [edx+0x20]`（=主虚表 slot8 = `00459F20`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C34C9`：`mov dword ptr [eax], 007F3BD0`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E96A0`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BCFB5`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3BD0` 在**整个 `.text` 只有 1 处 imm 写点**（`006C34C9`），无析构器写点、无成对死表；写入者 `006C34C0` 是 ctor，其唯一调用者是初始化函数内的 `006BCFB5` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080AB18` / TD `008418C8` / 名串）与槽值 `007F3BD0+12`；④ 的取材料是 `.text` 的装表指令 `006C34C9` 与注册指令 `006BCFB5`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 BuildingClass 对象主 vt `007E3EBC` 的 slot0=`00410260`」：本审计追 `0043B740` 得 `0043B9FA` 处 `mov [this], 007E3EBC`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVBuildingClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `0043BA00`(dst `ebp`) → `007E3EA0` (.?AVBuildingClass@@) — ctor 内首个 ret 之前
  - `0043BA07`(dst `esi + 8`) → `007E3E98` (.?AVBuildingClass@@) — ctor 内首个 ret 之前
  - `0043BA0E`(dst `esi + 0xc`) → `007E3E90` (.?AVBuildingClass@@) — ctor 内首个 ret 之前
  - `0043BD05`(dst `esi + 4`) → `007E3EA0` (.?AVBuildingClass@@) — **另一函数**（首个 ret @0043BCDB 之后）
  - `0043BD0C`(dst `esi + 8`) → `007E3E98` (.?AVBuildingClass@@) — **另一函数**（首个 ret @0043BCDB 之后）
  - `0043BD13`(dst `esi + 0xc`) → `007E3E90` (.?AVBuildingClass@@) — **另一函数**（首个 ret @0043BCDB 之后）
  - `0043C073`(dst `edi`) → `007E43E8` (.?AV?$VectorClass@PAVInfantryClass@@@@) — **另一函数**（首个 ret @0043BCDB 之后）
  - `0043C098`(dst `ebp`) → `007E43E8` (.?AV?$VectorClass@PAVInfantryClass@@@@) — **另一函数**（首个 ret @0043BCDB 之后）

  ⚠ **同表另一写点**：`0043BCFD` 也写 `007E3EBC`。其中落在 ctor 之外（析构侧/另一个函数）的那处属 ㉓ 的「成对」形态；本行的 ④ 锚在**工厂表**（`007F3BD0`，装表点 `006C34C9` 唯一），**未**拿对象表充当 ④，故不触发 ㉓。若仅凭「对象表的某处写点」判 ④，这一行会踩坑——本审计已排除该路径。

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVBuildingClass@@` 的那一处（`0043B9FA`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C3890 — `T_TClassFactory_VInfantryClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3C00+12 = 007F3C0C`（slot#3），该 4 字节值 `006C3890` 即本 entry。
- `[vt-4] = 0080ABB8`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841928`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VInfantryClass@@@@`。类名与行名中的 `TClassFactory<VInfantryClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C37D0`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C389B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C38B3` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C38DF` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 1776` → `call 0x7C8E17`(@`006C38C1`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 00517A50`。
- 主站点：`006C38F1` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3902`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C38FB` `push 1` + `mov ecx,esi` + `006C38FF` `call [edx+0x20]`（=主虚表 slot8 = `00523350`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C37C9`：`mov dword ptr [eax], 007F3C00`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E9680`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BD02F`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3C00` 在**整个 `.text` 只有 1 处 imm 写点**（`006C37C9`），无析构器写点、无成对死表；写入者 `006C37C0` 是 ctor，其唯一调用者是初始化函数内的 `006BD02F` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080ABB8` / TD `00841928` / 名串）与槽值 `007F3C00+12`；④ 的取材料是 `.text` 的装表指令 `006C37C9` 与注册指令 `006BD02F`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 InfantryClass 对象主 vt `007EB058` 的 slot0=`00410260`」：本审计追 `00517A50` 得 `00517ACC` 处 `mov [this], 007EB058`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVInfantryClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `00517AD2`(dst `eax`) → `007EB03C` (.?AVInfantryClass@@) — ctor 内首个 ret 之前
  - `00517AD8`(dst `esi + 8`) → `007EB034` (.?AVInfantryClass@@) — ctor 内首个 ret 之前
  - `00517ADF`(dst `esi + 0xc`) → `007EB02C` (.?AVInfantryClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVInfantryClass@@` 的那一处（`00517ACC`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C3A10 — `T_TClassFactory_VAnimClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3C18+12 = 007F3C24`（slot#3），该 4 字节值 `006C3A10` 即本 entry。
- `[vt-4] = 0080AC08`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841958`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VAnimClass@@@@`。类名与行名中的 `TClassFactory<VAnimClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C3950`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C3A1B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C3A33` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C3A5B` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 456` → `call 0x7C8E17`(@`006C3A41`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 00422720`。
- 主站点：`006C3A6D` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3a7e`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C3A77` `push 1` + `mov ecx,esi` + `006C3A7B` `call [edx+0x20]`（=主虚表 slot8 = `00426590`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C3949`：`mov dword ptr [eax], 007F3C18`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E9670`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BD06C`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3C18` 在**整个 `.text` 只有 1 处 imm 写点**（`006C3949`），无析构器写点、无成对死表；写入者 `006C3940` 是 ctor，其唯一调用者是初始化函数内的 `006BD06C` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080AC08` / TD `00841958` / 名串）与槽值 `007F3C18+12`；④ 的取材料是 `.text` 的装表指令 `006C3949` 与注册指令 `006BD06C`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 AnimClass 对象主 vt `007E3354` 的 slot0=`00410260`」：本审计追 `00422720` 得 `00422847` 处 `mov [this], 007E3354`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVAnimClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `0042284D`(dst `esi + 4`) → `007E3338` (.?AVAnimClass@@) — ctor 内首个 ret 之前
  - `00422854`(dst `esi + 8`) → `007E3330` (.?AVAnimClass@@) — ctor 内首个 ret 之前
  - `0042285B`(dst `esi + 0xc`) → `007E3328` (.?AVAnimClass@@) — ctor 内首个 ret 之前

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVAnimClass@@` 的那一处（`00422847`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**

---

## 006C3B90 — `T_TClassFactory_VAnimTypeClass__::slot3`

**第 1 项 ② 类身份（独立成立）**

- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `007F3C30+12 = 007F3C3C`（slot#3），该 4 字节值 `006C3B90` 即本 entry。
- `[vt-4] = 0080AC58`（COL，位于 `.rdata`）→ `[COL+0xC] = 00841988`（TD，位于 `.data`）→ TD+8 内联名串 `.?AV?$TClassFactory@VAnimTypeClass@@@@`。类名与行名中的 `TClassFactory<VAnimTypeClass>` 逐字吻合。
- 工厂自身 `vt[0] = 006C3AD0`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。
- 结论：**② 成立**。

**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**

入口三道 imm 错误码守卫（字节内可核）：

| 守卫 | 地址 | 字节 | 立即数 | 语义 |
|---|---|---|---|---|
| 1 | `006C3B9B` | `b8 57 00 07 80` | `0x80070057` | ppvOut 为空 |
| 2 | `006C3BB3` | `b8 10 01 04 80` | `0x80040110` | pUnkOuter 非空（禁止聚合） |
| 3 | `006C3BDD` | `b8 0e 00 07 80` | `0x8007000e` | 分配/构造失败 |

- 分配→构造接线：`push 888` → `call 0x7C8E17`(@`006C3BC1`) → `test eax,eax` → `je` 失败码 → `mov ecx,eax` → `call 00427530`。
- 主站点：`006C3BEF` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， 即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / `7d 09 jge 0x6c3c00`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。
- 两路动作不同：失败路 `006C3BF9` `push 1` + `mov ecx,esi` + `006C3BFD` `call [edx+0x20]`（=主虚表 slot8 = `00428EA0`，该函数先回写四张类虚表、再把自己从全局容器摘除、末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。
- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。
- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。

**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**

- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，ctor 唯一装表点 `006C3AC9`：`mov dword ptr [eax], 007F3C30`（字节 `c7 00 ...`）。
- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `007E9620`; call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；本行注册点 `006BD0A9`。
- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。
- ㉓ 检查：`007F3C30` 在**整个 `.text` 只有 1 处 imm 写点**（`006C3AC9`），无析构器写点、无成对死表；写入者 `006C3AC0` 是 ctor，其唯一调用者是初始化函数内的 `006BD0A9` 附近，`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。
- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。
- 结论：**④ 成立**。

**第 4 项 ②④ 是否同源 → 不同源**

- ② 的取材料是 `.rdata` 的 RTTI 链（COL `0080AC58` / TD `00841988` / 名串）与槽值 `007F3C30+12`；④ 的取材料是 `.text` 的装表指令 `006C3AC9` 与注册指令 `006BD0A9`。段不同、地址不同、证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。
- 结论：**不同源（same_source=no）**。

**第 5 项 语义与实测是否相符**

- 第 4 列称「新建 AnimTypeClass 对象主 vt `007E3608` 的 slot0=`00410260`」：本审计追 `00427530` 得 `00427731` 处 `mov [this], 007E3608`，`vt[0] = 00410260`，`[vt-4]→COL→名串 = .?AVAnimTypeClass@@` ⇒ **吻合，且是主表不是小成员表**。
- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。
- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。
- 结论：**相符**。

**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：

  - `00427737`(dst `eax`) → `007E35EC` (.?AVAnimTypeClass@@) — ctor 内首个 ret 之前
  - `0042773D`(dst `esi + 8`) → `007E35E4` (.?AVAnimTypeClass@@) — ctor 内首个 ret 之前
  - `00427744`(dst `esi + 0xc`) → `007E35DC` (.?AVAnimTypeClass@@) — ctor 内首个 ret 之前
  - `00427863`(dst `esi + 4`) → `007E35EC` (.?AVAnimTypeClass@@) — **另一函数**（首个 ret @0042784D 之后）
  - `0042786A`(dst `esi + 8`) → `007E35E4` (.?AVAnimTypeClass@@) — **另一函数**（首个 ret @0042784D 之后）
  - `00427871`(dst `esi + 0xc`) → `007E35DC` (.?AVAnimTypeClass@@) — **另一函数**（首个 ret @0042784D 之后）

  ⚠ **同表另一写点**：`0042785D` 也写 `007E3608`。其中落在 ctor 之外（析构侧/另一个函数）的那处属 ㉓ 的「成对」形态；本行的 ④ 锚在**工厂表**（`007F3C30`，装表点 `006C3AC9` 唯一），**未**拿对象表充当 ④，故不触发 ㉓。若仅凭「对象表的某处写点」判 ④，这一行会踩坑——本审计已排除该路径。

  只有 dst = this(`esi`) 且 RTTI 名 = `.?AVAnimTypeClass@@` 的那一处（`00427731`）被计为对象主虚表；其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。

**本行裁定：`PASS`**
