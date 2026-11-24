# VERDICT — NAMED_PUSH_AUDIT9（异族独立审计）

> 审计对象：`NAMED_PUSH_S12_B2\delta.tsv` 全部 6 行（DeepSeek 产）。
> entry 取法：读该 `delta.tsv` 第 1 列（`entry`），数据行为第 2–7 行，共 6 行；subsystem 全为 S12。
> 只采信本次自己反汇编的字节：脚本 `work/audit_lib.py`（自写 PE 加载 + capstone 5.0.7 `skipdata=True`），逐行脚本 `work/v_<entry>.py`。**未引用**执行器 `EVIDENCE/ROW_*.txt` 作证据。
> 目标 `ra2youli\gamemd.exe` SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（一致）；ImageBase 0x400000，`.text=[0x401000,0x7E038D)`。
> 判据：卡片五件事 + D-40 四环；③ 只认整体合同真实且可伪证（多值状态码算，{0,1} 布尔不算）；㉓ 成对陷阱（④ 锚点落在析构器 ⇒ FAIL）。
> 用户特别要求：独立确认 ② 用**主表**（slot0=0x00410260）不是小成员表；④ 锚点**不在析构器里**——尤其 004729C0 / 004CA770（entry 自身是删除式析构器）。

---

## 1. `00453E20` — BuildingClass::vslot5 — verdict: **PASS**

**② 类身份（独立成立，主表）**
- delta 称槽 `007E3ED0`。实测 `[0x007E3ED0]=20 3E 45 00` = `0x00453E20`（= entry）。
- 自写 `resolve_slot` 回扫：`vtable_base=0x007E3EBC`, `slot_off=0x14`, `slot_index=5`；`(0x3ED0-0x3EBC)/4=5`，与线索 `vslot5` 自洽。
- RTTI 链：`[0x7E3EB8]=0x007FC360`(COL, sig=0) → `[COL+0xC]=0x00818D60`(TD) → `TD+8` = `.?AVBuildingClass@@`。
- **主表确认**：`[vtable_base 0x7E3EBC + 0] = 0x00410260`（主表槽 0）；即本槽在主表内，非小成员表。

**③b 具体形态：③b②（call → cmp eax,ebx(=0) → jl；HRESULT 失败负值/成功 0，多值状态约定）**
- 成链字节（自反汇编 `0x453E40..0x453EC8`）：
  - `0x453E46 33 DB` = `xor ebx,ebx`（ebx 归零；`0x453E46..0x453EB8` 之间无 ebx 再写，独立扫描确认）。
  - `0x453EB3 E8 98 80 2B 00` = `call 0x70BF50`。
  - `0x453EB8 3B C3` = `cmp eax, ebx`（ebx=0 ⇒ 判 eax 符号）。
  - `0x453EBA 89 44 24 10` = `mov [esp+0x10], eax`（只存栈，未覆写 eax/ebx/flags）。
  - `0x453EBE 0F 8C BA 02 00 00` = `jl 0x45417E`。cmp 与 jl 之间无判据覆写。
- 被调 `0x70BF50` 返回约定可伪证：`0x70BF5C call 0x65AB80` → `0x70BF61 33 DB`(xor ebx,ebx) → `0x70BF63 3B C3`(cmp eax,ebx) → `0x70BF65 0F 8C DE 02 00 00`(jl 0x70C249)；失败尾 `0x70C249 pop esi; 0x70C24A pop ebx; 0x70C24B C2 08 00 ret 8`（不碰 eax ⇒ 负 HRESULT 原样上抛）；成功侧 `0x70C246 8B C3 mov eax,ebx(=0)` 再落同收尾 ⇒ 成功 0。失败为负 HRESULT（多值错误码集合），非 {0,1} 布尔。
- 调用方真拿它分支且两路动作不同：
  - 失败 `jl 0x45417E`：`0x45417E pop edi/esi/ebp/ebx/ecx; 0x454183 C2 08 00 ret 8`（不碰 eax ⇒ 错误码原样上抛），整段成员读回（成员向量、`call [eax+0x10]` 等）全跳过。
  - 成功：继续 `0x453ED4 mov eax,[esi]; call [eax+0x10]` 读回，循环到 `0x454170 8B 44 24 10 mov eax,[esp+0x10]` 返回 hr(≥0)。
  - 另三站点 `0x453FED`/`0x45407A`/`0x45409C` 均为 `call [reg+0xc]` 后 `test eax,eax; jl 0x45417E` 同落点。
- 禁止项核对：非栈写来自**调用方**读回循环，非被调内部写；非 ③a。

**④ 使用见证（独立成立，非 direct-only，非析构）**
- 活虚表派发安装点 `0x0043B71F C7 06 BC 3E 7E 00` = `mov dword ptr [esi],0x7E3EBC`（装入活对象 [obj+0]）；第二安装点 `0x0043B9FA` 同形。
- 所在函数 `0x0043B680`：`0x43B73A mov eax,esi` / `0x43B73D ret 4`（**返 this ⇒ 构造器**）；`is_atexit_registered(0x43B680)=[]`、`(0x43B740)=[]`（非 atexit）。
- **㉓ 排除**：同虚表的另一次重装在 `0x0043BCFD`，位于函数 `0x43BCF0`（体内两次 `call 0x406060`=`operator delete`、逐层 vptr 重装、无返回值 ⇒ 析构器）；该点**不作** ④。④ 锚 = 构造安装点 0x43B71F，不在析构器。
- `direct callers of 00453E20 = []`（0 个），靠活虚表链，非 direct-only。

**④ 与 ② 不同源**：② 锚 = `.rdata` RTTI 数据链（0x7E3ED0 槽 + 0x7E3EB8 COL + 0x818D60 TD）；④ 锚 = `.text` 构造安装指令 0x43B71F。两通道独立 ⇒ same_source=no。

**语义与实测相符**：实测 = 建筑对象从存档流载入，先调 0x70BF50 取 hr，失败（eax<0）把负 HRESULT 原样上抛、成功读回全部成员后返回 0。与 delta 第 4 列方向一致。

**verdict = PASS**

---

## 2. `00465300` — BuildingTypeClass::slot6 — verdict: **PASS**

**② 类身份（独立成立，主表）**
- `[0x007E4588]=00 53 46 00` = `0x00465300`（= entry）。
- `resolve_slot` → `vtable_base=0x007E4570`, `slot_off=0x18`, `slot_index=6`；`(0x4588-0x4570)/4=6`，与线索 slot6 自洽。
- RTTI：`[0x7E456C]=0x007FC618`(COL,sig=0) → TD `0x008193A8` → `.?AVBuildingTypeClass@@`。
- **主表确认**：`[0x7E4570+0]=0x00410260`（主表槽 0）；本槽在主表内，非小成员表。

**③b 具体形态：③b②（call → test eax,eax → jl；HRESULT 失败负值/成功 0）**
- 成链字节（自反汇编 `0x465300..0x46536E`）：
  - `0x465313 E8 A8 1A 2B 00` = `call 0x716DC0`。
  - `0x465318 85 C0` = `test eax,eax`；`0x46531A 7C 4E` = `jl 0x46536A`（test→jl 间无 eax 覆写）。
- 被调 `0x716DC0` 约定可伪证：`0x716DD1 call 0x5F9950` → `0x716DD6 85 C0`(test eax,eax) → `0x716DD8 0F 8C B6 02 00 00`(jl 0x717094)；失败落 `0x717094 pop edi; 0x717095 pop esi; 0x717096 ret 0xc`（不碰 eax ⇒ 负值上抛，且因 ebx 尚未 push 合法跳过 0x717093 pop ebx）；成功侧 `0x717091 33 C0 xor eax,eax(=0)` 再落同收尾 ⇒ 成功 0。失败为负 HRESULT（多值），非布尔。
- 调用方分支两路动作不同：
  - 失败 `jl 0x46536A`：`0x46536A pop edi/esi/ebp/ebx; 0x46536E ret 0xc`（不碰 eax ⇒ 错误码上抛），跳过整段记录读回（`[ebx+0x178C]` 计数、`[ebx+0x1788]+i*0xC` 数组全不读）。
  - 成功：读计数并循环 `call [reg+0x10]` 读回每项，末尾 `0x465368 33 C0 xor eax,eax` 落同收尾 ⇒ 返回 0。
  - 另两站点 `0x465332`/`0x465355` 为流 `call [reg+0x10]` 后 `test eax,eax; jl 0x46536A` 同落点。
- 禁止项：非栈写（记录读回）在调用方；非 ③a。

**④ 使用见证（独立成立，非 direct-only，非析构）**
- 安装点 `0x0045E558 C7 06 70 45 7E 00` = `mov [esi],0x7E4570`（装入活对象主表）；第二安装点 `0x0045E2CD` 同形（`mov [esi],0x7E4570`）。
- 所在函数 `0x0045E520`：`0x45E573 mov eax,esi` / `0x45E576 ret 4`（**返 this ⇒ 构造器**）；`is_atexit_registered(0x45DD90)=[]`、`(0x45E520)=[]`。
- **㉓ 排除**：同虚表另一次重装在 `0x0045E58D`，位于 `0x0045E580`（`xor ebx,ebx; mov al,[esi+0xe04]; cmp al,bl` 删除标志检查 + 逐层 vptr 重装 ⇒ 标量删除式析构器）；不作 ④。④ 锚 = 构造安装 0x45E558，不在析构器。
- `direct callers of 00465300 = []`，靠活虚表链。

**④ 与 ② 不同源**：② 锚 `.rdata` RTTI 链（0x7E4588 槽 + 0x7E456C COL + 0x8193A8 TD）；④ 锚 `.text` 构造安装 0x45E558 ⇒ same_source=no。

**语义与实测相符**：建筑类型副本从存档流载入，调 0x716DC0 载入，失败负 HRESULT 上抛、成功读回记录数组返 0。与 delta 第 4 列一致。

**verdict = PASS**

---

## 3. `004728E0` — CaptureManagerClass::slot6 — verdict: **PASS**

**② 类身份（独立成立，主表）**
- `[0x007E4B58]=E0 28 47 00` = `0x004728E0`（= entry）。
- `resolve_slot` → `vtable_base=0x007E4B40`, `slot_off=0x18`, `slot_index=6`；`(0x4B58-0x4B40)/4=6`，与线索 slot6 自洽。
- RTTI：`[0x7E4B3C]=0x007FCB60`(COL,sig=0) → TD `0x0081B6C8` → `.?AVCaptureManagerClass@@`。
- **主表确认**：`[0x7E4B40+0]=0x00410260`（主表槽 0）；本槽在主表内。

**③b 具体形态：③b②（call → mov edi,eax → test edi,edi → jl；具名多值 HRESULT E_POINTER）**
- 成链字节（自反汇编 `0x4728E0..0x47295C`）：
  - `0x4728F3 E8 28 DA F9 FF` = `call 0x410320`。
  - `0x4728F8 8B F8` = `mov edi,eax`；`0x4728FA 85 FF` = `test edi,edi`；`0x4728FC 89 7C 24 18` 只存栈（不覆写 edi）；`0x472900 7C 54` = `jl 0x472956`。
  - test→jl 间无 edi 覆写；单 call。
- 被调 `0x410320` 约定可伪证：`0x410325 85 F6`(test esi,esi)/`0x410328 75 0A`(jne)；空指针路 `0x41032B B8 03 40 00 80` = `mov eax,0x80004003`(E_POINTER) → `0x410331 ret 0xc`；成功侧 `0x410372 pop edi; 0x410373 pop esi; 0x410374 ret 0xc`（不碰 eax ⇒ 原样传出内层 COM HRESULT）。eax 常量集 = `{0x0, 0x80004003}`，另有 3 个 ret 透传内层 HRESULT（多值），非 `{0,1}` 布尔。
- 调用方分支两路动作不同：
  - 失败（edi<0，E_POINTER 为负）：`jl 0x472956` → `0x472956 8B C7 mov eax,edi` → `ret 0xc`（原样上抛），跳过整个读回循环。
  - 成功（edi≥0）：`0x472902` 起读 `[ebx+0x34]` 计数、`[ebx+0x28]+i*4` 每项两个 dword（`call [reg+0x10]` ×2），末尾 `0x472952 mov edi,[esp+0x18]` 恢复 hr → 同收尾返回。
  - 另两站点 `0x472915`/`0x472942` 为流 Read 后 `test eax,eax; jl 0x472958`（收尾不碰 eax）。
- 禁止项：非栈写在调用方读回循环；非 ③a。

**④ 使用见证（独立成立，非 direct-only，非析构）**
- 安装点 `0x00471807 C7 06 40 4B 7E 00` = `mov [esi],0x7E4B40`（主表装入活对象）；第二安装点 `0x004718BC` 同形。
- 所在函数 `0x004717D0`：`0x471884 mov [ecx+eax*4],esi`（挂 this 进全局表 0x89E0F4）、`0x471887 mov eax,esi` / `0x47188A ret 0xc`（**返 this ⇒ 构造器**）；`atexit(0x4717D0)=[]`、`(0x471890)=[]`。
- **㉓ 排除**：同虚表另一次重装在 `0x004729CD`，位于 `0x004729C0`（`mov ecx,0x89E0F0` 全局容器 + vptr 重装 + 后接 Find 压缩 ⇒ 删除式析构器）；不作 ④。④ 锚 = 构造安装 0x471807，不在析构器。
- `direct callers of 004728E0 = []`，靠活虚表链。

**④ 与 ② 不同源**：② 锚 `.rdata` RTTI 链（0x7E4B58 槽 + 0x7E4B3C COL + 0x81B6C8 TD）；④ 锚 `.text` 构造安装 0x471807 ⇒ same_source=no。

**语义与实测相符**：CaptureManagerClass 从流载入，先调 0x410320 校验（空指针 E_POINTER=0x80004003），失败负 HRESULT 原样上抛、成功读回计数与每项两 dword。与 delta 第 4 列一致。

**verdict = PASS**

---

## 4. `004729C0` — CaptureManagerClass::slot8（删除式析构器）— verdict: **PASS**

> 用户点名行。entry 自身是删除式析构器；④ 不得锚在析构器（㉓）。本次独立确认 ② 用主表、④ 锚同类构造器。

**② 类身份（独立成立，主表）**
- `[0x007E4B60]=C0 29 47 00` = `0x004729C0`（= entry）。
- `resolve_slot` → `vtable_base=0x007E4B40`, `slot_off=0x20`, `slot_index=8`；`(0x4B60-0x4B40)/4=8`，与线索 slot8 自洽。
- RTTI：`[0x7E4B3C]=0x007FCB60`(COL,sig=0) → TD `0x0081B6C8` → `.?AVCaptureManagerClass@@`。
- **主表确认（非小成员表）**：`[0x7E4B40+0]=0x00410260`（主表槽 0）。全镜像非 .text 中等于 entry 的 dword 引用只有 `0x7E4B60` 一处（唯一归属，正是该主表的 slot8）。

**③b 具体形态：③b②（虚派发 Find → cmp eax,-1 → je；-1=未命中，命中=下标，多值）**
- 成链字节（自反汇编 `0x4729C0..0x472A28`，注意此段就在 entry/析构器体内）：
  - `0x4729C8 B9 F0 E0 89 00` = `mov ecx,0x89E0F0`；`0x4729E8 8B 15 F0 E0 89 00` = `mov edx,[0x89E0F0]`（全局容器对象/vptr）。
  - `0x4729F3 FF 52 10` = `call dword ptr [edx+0x10]`（虚派发 slot4 = Find）；`0x4729F6 83 F8 FF` = `cmp eax,-1`；`0x4729F9 74 2D` = `je 0x472A28`。**cmp→je 之间无 eax 覆写**；单 call。
- 被调 Find 可字节钉死：`0x47176D C7 05 F0 E0 89 00 D4 4A 7E 00` 静态初始化把全局 `0x89E0F0` 的 vptr 设为 `0x007E4AD4`；其 `[-4]@0x7E4AD0=0x007FCA18`(COL,sig=0) → TD `0x0081B620` → `.?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@`；slot4 `[0x7E4AE4]=0x00472FD0`。Find 体：`0x472FD3 xor eax,eax`（命中路径 eax=下标）、`0x472FEF 83 C8 FF or eax,-1`、`0x472FF3 C2 04 00 ret 4` ⇒ 未命中=-1、命中=下标（多值下标约定，非布尔）。
- **哨兵确被检查并分支**：`cmp eax,-1`@0x4729F6 + `je 0x472A28`@0x4729F9；未命中直接跳 `0x472A28` 跳过整段移除；命中则 `0x472A05 49`(dec ecx)、`0x472A08 89 0D 00 E1 89 00`(count-- 回写)、`0x472A17 8B 14 81`/`0x472A1A 89 54 81 FC`（数组前移压缩，写全局数组 `0x89E0F4`，**调用方非栈写**）。
- **析构语义 ③b② 判断**：本行 ③ 的被调是 **Find 的 -1/下标多值返回约定**（真实、可伪证：Find 体内 `or eax,-1` 与命中下标两条出口字节均可枚举），调用方拿它 `cmp/je` 分支且两路动作不同（跳过 vs count--+压缩）。**非栈写来自调用方压缩循环、非被调内部写；非 ③a**。析构语义本身不削弱该函数整体合同的可伪证性 ⇒ ③b② 成立。
- 禁项核对：通过。

**④ 使用见证（独立成立，非 direct-only，锚构造器非析构）**
- **④ 锚 = 同类构造器安装点 `0x00471807 C7 06 40 4B 7E 00` = `mov [esi],0x7E4B40`**（装入活对象主表）；第二安装点 `0x004718BC` 同形。
- 所在函数 `0x004717D0`：`0x471887 mov eax,esi` / `0x471889 pop esi` / `0x47188A ret 0xc`（**返 this ⇒ 构造器**）；`is_atexit_registered(0x4717D0)=[]`、`(0x471890)=[]`。
- **㉓ 成对陷阱排除（用户重点）**：本行 entry `0x004729C0` 自身确为**删除式析构器**——体内 `0x4729CD` 处有同虚表重装，且 `0x472A3E call 0x7C8B3D`(operator delete)、`0x472A5A call 0x4101F0`(基类析构)、`0x472A67/0x472A96 call 0x7C8B3D`；若拿 `0x4729CD` 作 ④ 即 ㉓ 违规。**执行器已把 ④ 改锚同类构造器 0x471807，本次独立确认 0x471807 在构造器 0x4717D0 内、不在析构器** ⇒ ④ 锚点合规。
- `direct callers of 004729C0 = []`，靠活虚表链。

**④ 与 ② 不同源**：② 锚 `.rdata` RTTI 链（0x7E4B60 槽 + 0x7E4B3C COL + 0x81B6C8 TD）；④ 锚 `.text` 构造器安装 0x471807 ⇒ same_source=no。

**语义与实测相符**：删除式析构器——先在全局 `DynamicVectorClass<CaptureManagerClass*>`(0x89E0F0) 中 Find 自身（未命中=-1），命中则 count-- 并前移压缩移除，再清成员 + 基类析构 0x4101F0 + flags&1 时 operator delete。与 delta 第 4 列一致。

**verdict = PASS**

---

## 5. `004CA3C0` — FactoryClass::slot6 — verdict: **PASS**

**② 类身份（独立成立，主表）**
- `[0x007E88E8]=C0 A3 4C 00` = `0x004CA3C0`（= entry）。
- `resolve_slot` → `vtable_base=0x007E88D0`, `slot_off=0x18`, `slot_index=6`；`(0x88E8-0x88D0)/4=6`，与线索 slot6 自洽。
- RTTI：`[0x7E88CC]=0x00800610`(COL,sig=0) → TD `0x00822290` → `.?AVFactoryClass@@`。
- **主表确认**：`[0x7E88D0+0]=0x00410260`（主表槽 0）；非 .text 中等于 entry 的 dword 引用只有 `0x7E88E8` 一处。

**③b 具体形态：③b②（call → test eax,eax → jl；具名多值 HRESULT E_POINTER）**
- 成链字节（自反汇编 `0x4CA3C0..0x4CA422`）：
  - `0x4CA3D2 E8 49 5F F4 FF` = `call 0x410320`。
  - `0x4CA3D7 85 C0` = `test eax,eax`；`0x4CA3D9 7C 44` = `jl 0x4CA41F`（test→jl 间无 eax 覆写；单 call）。
- 被调 `0x410320`：`0x410325 test esi,esi`/`0x410328 jne`；空指针 `0x41032B mov eax,0x80004003`(E_POINTER) → `0x410331 ret 0xc`；成功侧 `ret 0xc` 不碰 eax（透传内层 HRESULT）。失败负 HRESULT / 成功 ≥0，具名多值，非 {0,1} 布尔。
- 调用方分支两路动作不同：
  - 失败 `jl 0x4CA41F`：`0x4CA41F pop edi/esi/ebx; 0x4CA422 ret 0xc`（不碰 eax ⇒ 错误码上抛），跳过整段读回。
  - 成功：`0x4CA3DB` 起读 `[edi+0x50]` 计数、`[edi+0x44]+i*4` 工厂项（`call [reg+0x10]`），末尾 `0x4CA41D 33 C0 xor eax,eax` 落同收尾 ⇒ 返回 0。
  - 另两站点 `0x4CA3EE`/`0x4CA40D` 为流 Read 后 `test eax,eax; jl`；其中 `0x4CA40D` 跳 `0x4CA41D`(xor eax,eax，吞错返 0)——正说明只有 `0x4CA3D9` 是上抛路径，两路差别实质。
- 禁止项：非栈写在调用方读回循环；非 ③a。

**④ 使用见证（独立成立，非 direct-only，非析构）**
- 安装点 `0x004C991A C7 06 D0 88 7E 00` = `mov [esi],0x7E88D0`（主表装入活对象）；第二安装点 `0x004CA2C7 C7 07 D0 88 7E 00` = `mov [edi],0x7E88D0`（实地构造并写子表）。
- 所在函数 `0x004C98B0`：`0x4C99FB mov eax,esi` / `0x4C99FD pop esi` / `0x4C9A02 ret`（**返 this ⇒ 构造器**，函数体无 free/基类析构）；`is_atexit_registered(0x4C98B0)=[]`、`(0x4CA270)=[]`。
- **㉓ 排除**：同虚表另一次重装在 `0x004CA776`，位于 `0x004CA770`（`mov dl,1` 删除标志 + vptr 重装 + `call 0x7258D0` + `call [edx+0x10]` Find + `cmp eax,-1` ⇒ 删除式析构器）；不作 ④。④ 锚 = 构造安装 0x4C991A，不在析构器。
- `direct callers of 004CA3C0 = []`，靠活虚表链。

**④ 与 ② 不同源**：② 锚 `.rdata` RTTI 链（0x7E88E8 槽 + 0x7E88CC COL + 0x822290 TD）；④ 锚 `.text` 构造安装 0x4C991A ⇒ same_source=no。

**语义与实测相符**：FactoryClass 从流载入，先调 0x410320 校验（空指针 E_POINTER=0x80004003），失败负 HRESULT 上抛、成功逐项读回工厂项返 0。与 delta 第 4 列一致。

**verdict = PASS**

---

## 6. `004CA770` — FactoryClass::slot8（删除式析构器，两容器）— verdict: **PASS**

> 用户点名行。entry 自身是删除式析构器（含两处 Find 压缩）；④ 不得锚在析构器（㉓）。本次独立确认 ② 用主表、④ 锚同类构造器。

**② 类身份（独立成立，主表）**
- `[0x007E88F0]=70 A7 4C 00` = `0x004CA770`（= entry）。
- `resolve_slot` → `vtable_base=0x007E88D0`, `slot_off=0x20`, `slot_index=8`；`(0x88F0-0x88D0)/4=8`，与线索 slot8 自洽。
- RTTI：`[0x7E88CC]=0x00800610`(COL,sig=0) → TD `0x00822290` → `.?AVFactoryClass@@`。
- **主表确认（非小成员表）**：`[0x7E88D0+0]=0x00410260`（主表槽 0）；非 .text 中等于 entry 的 dword 引用只有 `0x7E88F0` 一处（正是该主表 slot8）。

**③b 具体形态：③b②（两处独立站点、两个不同全局容器，均 Find → cmp eax,-1 → je）**
- **站点一**（容器 `0xA83E30`）：`0x4CA7A1 mov ecx,0xA83E30`、`mov edx,[0xA83E30]`；`0x4CA7AA FF 52 10 call [edx+0x10]`；`0x4CA7AD 83 F8 FF cmp eax,-1`；`0x4CA7B0 74 2D je 0x4CA7DF`。cmp→je 无 eax 覆写。静态初始化 `0x4E6E7D C7 05 30 3E A8 00 A4 9F 7E 00` 写 vptr `0x7E9FA4`；`[-4]@0x7E9FA0=0x00801610`(COL,sig=0) → TD `0x008234E0` → `.?AV?$DynamicVectorClass@PAVFactoryClass@@@@`；slot4 `[0x7E9FB4]=0x004EC2D0`，其 `0x4EC2D3 xor eax,eax`、`0x4EC2EF 83 C8 FF or eax,-1`、`0x4EC2F3 ret 4` ⇒ 未命中=-1/命中=下标。命中：`0x4CA7BC dec ecx`、`0x4CA7BF mov [0xA83E40],ecx`(count--)、`0x4CA7CE/0x4CA7D1 mov [ecx+eax*4-4],edx`(压缩，全局数组非栈写)。
- **站点二**（容器 `0xB0F720`）：`0x4CA7EF mov edx,[0xB0F720]`；`0x4CA803 FF 52 10 call [edx+0x10]`；`0x4CA806 83 F8 FF cmp eax,-1`；`0x4CA809 74 2D je 0x4CA838`。静态初始化 `0x7252ED C7 05 20 F7 B0 00 EC 91 7E 00` 写 vptr `0x7E91EC`；`[-4]@0x7E91E8=0x008009B0`(COL,sig=0) → TD `0x008225E8` → `.?AV?$DynamicVectorClass@PAVAbstractClass@@@@`；slot4 `[0x7E91FC]=0x004E0550`，其 `0x4E056F or eax,-1`、`0x4E0573 ret 4` 同形。命中：`0x4CA815 dec ecx`、`0x4CA818 mov [0xB0F730],ecx`、`0x4CA827/0x4CA82A mov [ecx+eax*4-4],edx`。
- 两站点 call 地址/容器全局/this 各异，非多路同一 call；非栈写均在调用方压缩循环；非 ③a。
- **析构语义 ③b② 判断**：两被调均为 Find 的 -1/下标多值返回约定（字节可伪证：两条出口 `or eax,-1` 与命中下标均可枚举），调用方 `cmp/je` 分支且两路动作不同（跳过 vs count--+压缩）⇒ ③b② 成立。

**④ 使用见证（独立成立，非 direct-only，锚构造器非析构）**
- **④ 锚 = 同类构造器安装点 `0x004C991A C7 06 D0 88 7E 00` = `mov [esi],0x7E88D0`**（主表装入活对象）；第二安装点 `0x004CA2C7 mov [edi],0x7E88D0`。
- 所在函数 `0x004C98B0`：`0x4C99FB mov eax,esi` / `0x4C9A02 ret`（**返 this ⇒ 构造器**）；`is_atexit_registered(0x4C98B0)=[]`、`(0x4CA270)=[]`。
- **㉓ 成对陷阱排除（用户重点）**：本行 entry `0x004CA770` 自身确为**删除式析构器**——`0x4CA774 mov dl,1`（删除标志）、`0x4CA776` 同虚表重装，体内 `0x4CA84E/0x4CA877/0x4CA8A6 call 0x7C8B3D`(operator delete ×3)、`0x4CA86A call 0x4101F0`(基类析构)。若拿 `0x4CA776` 作 ④ 即 ㉓ 违规。**执行器已把 ④ 改锚同类构造器 0x4C991A，本次独立确认 0x4C991A 在构造器 0x4C98B0 内、不在析构器** ⇒ ④ 锚点合规。
- `direct callers of 004CA770 = []`，靠活虚表链。

**④ 与 ② 不同源**：② 锚 `.rdata` RTTI 链（0x7E88F0 槽 + 0x7E88CC COL + 0x822290 TD）；④ 锚 `.text` 构造器安装 0x4C991A ⇒ same_source=no。

**语义与实测相符**：删除式析构器——在两个全局容器 `DynamicVectorClass<FactoryClass*>`(0xA83E30) 与 `DynamicVectorClass<AbstractClass*>`(0xB0F720) 中各 Find 自身（未命中=-1），命中则 count-- 并前移压缩移除，再清成员 + 基类析构 0x4101F0 + flags&1 时 operator delete。与 delta 第 4 列一致。

**verdict = PASS**

---
