# VERDICT — NAMED_PUSH_AUDIT8（异族独立审计）

> 审计对象：`NAMED_PUSH_S12_B1\delta.tsv` 全部 4 行（DeepSeek 产）。
> 只采信本次自己反汇编的字节：脚本 `work/audit_lib.py`（自写 PE 加载 + capstone 5.0.7 `skipdata=True`），逐行脚本 `work/v_<entry>.py`。**未引用**执行器 `EVIDENCE/ROW_*.txt` 作证据。
> 目标 `ra2youli\gamemd.exe` SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（一致）；ImageBase 0x400000，`.text=[0x401000,0x7E038D)`。
> 判据：卡片五件事 + D-40 四环；③ 只认整体合同真实且可伪证（多值状态码算，{0,1} 布尔不算）；㉓ 成对陷阱（④ 锚点落在析构器 ⇒ FAIL）。

---

## 1. `00442230` — BuildingClass::vslot91 — verdict: **PASS**

**② 类身份（独立成立）**
- delta 称槽 `007E4028`。实测 `007E4028` 4B = `30 22 44 00` = `0x00442230`（= entry）。
- 回扫（自己脚本 resolve_slot，k 从 0 枚举）：最近命中 `vtable_base=0x007E3EBC`，`slot_off=0x16C`，`slot_index=91`（(0x4028-0x3EBC)/4=91）。
- RTTI 链：`[0x7E3EB8]=0x007FC360`(COL, sig=0) → `[COL+0xC]=0x00818D60`(TD) → `TD+8` 名串 `.?AVBuildingClass@@`。主表槽 0 `[0x7E3EBC]=0x00410260`（BuildingClass 对象主虚表）。槽号 91 与线索 `vslot91` 自洽。
- 结论：② 由 `.rdata` RTTI 数据链独立钉住。

**③b 具体形态：③b②（call → cmp eax,-1 → je，错误码 -1）**
- 成链字节（自己反汇编 `0x442480..0x4425F`）：
  - `0x4424B2  mov edx,[esp+0x14]`；`[esp+0x14]` 在 `0x442481` 被写 `0x7E180C`（`C7 44 24 14 0C 18 7E 00`），另一路 `0x4422E1` 写 `0x7E17AC`（`C7 44 24 14 AC 17 7E 00`）——edx = 栈上临时向量 vptr。
  - `0x4424B6 50` push eax；`0x4424B7 8D 4C 24 18` lea ecx,[esp+0x18]（向量对象首址）。
  - `0x4424BB FF 52 10` = `call dword ptr [edx+0x10]`（虚派发 slot4 = Find）。
  - `0x4424BE 83 F8 FF` = `cmp eax,-1`；`0x4424C1 74 25` = `je 0x4424e8`。cmp 与 je 之间无 eax 覆写。
- 被调返回约定可伪证（两条可能 vptr 的 slot4 均是 Find，字节）：
  - vptr `0x7E180C` → `[-4]=0x7FA6D8`(COL,sig=0) → TD `0x816880` → `.?AV?$VectorClass@PAVTechnoClass@@@@`；slot4 `0x7E181C=0x0040BA80`，其 `0x40BA91 xor eax,eax`（命中路径 eax=下标）、`0x40BAAC 83 C8 FF` = `or eax,-1`、`0x40BAB0 C2 04 00` = `ret 4`。未找到=-1、命中=下标。
  - vptr `0x7E17AC` → `[-4]=0x7FA640`(COL,sig=0) → TD `0x8168B0` → `.?AV?$DynamicVectorClass@PAVTechnoClass@@@@`；slot4 `0x7E17BC=0x0040BB90`，其 `0x40BBAF 83 C8 FF` = `or eax,-1`、`0x40BBB3 C2 04 00` = `ret 4`。同上。
- 调用方真拿 -1 分支且两路动作不同：`je 0x4424e8` 命中即跳过整段；未命中（eax=下标）则 `0x4424CB dec ecx` / `0x4424CE mov [esp+0x24],ecx`（回写 count-1）、`0x4424D9 8B 14 81 mov edx,[ecx+eax*4]` / `0x4424DC 89 54 81 FC mov [ecx+eax*4-4],edx`（数组前移压缩，**非栈写**，ecx 来自 [esp+0x18] 指向的数组）。cmp 与 je 间无 eax 覆写；单 call 非多路同一 call。
- 错误码语义：-1=未找到（多值：命中时为 0..n-1 下标），是**可枚举多值返回约定**，非 {0,1} 布尔。
- 禁止项核对：被调内部无写被当循环内非栈写（此处非栈写来自**调用方**压缩循环）；非 ③a。

**④ 使用见证（独立成立，非 direct-only）**
- 主虚表 `0x7E3EBC` 在 `.text` 的构造安装点 `0x0043B71F C7 06 BC 3E 7E 00` = `mov dword ptr [esi],0x7E3EBC`（装入活对象 [obj+0]）。
- 所在函数 `0x0043B680`：`0x43B73A mov eax,esi` / `0x43B73D ret 4`（**返 this** ⇒ 构造器）；`is_atexit_registered(0x43B680)=[]`（非 atexit）⇒ ㉓ 成对陷阱排除。
- entry 全镜像 direct caller = 0（不靠 direct，靠活虚表链）。

**④ 与 ② 不同源**：② 锚 = `.rdata` RTTI 数据链（0x7E4028 槽 + 0x7E3EB8 COL + 0x818D60 TD）；④ 锚 = `.text` 构造安装指令（0x43B71F）。两条独立通道 ⇒ same_source=no。

**语义与实测相符**：实测 = 在栈上临时 TechnoClass* 向量中 Find 目标（-1=未命中），命中则按下标做数组前移压缩移除、count--，未命中跳过。与 delta 第 4 列「Find 目标（-1=未命中），命中则压缩移除，未命中跳过」方向一致。

**verdict = PASS**

---

## 2. `00447210` — BuildingClass::vslot29 — verdict: **PASS**

> 用户特别点名行：③ 站点为「返回值先搬进 ebx 再判」。Lead 已裁定 ③ 只认函数整体合同真实；本次独立确认形态真实且可伪证（多值状态码算、{0,1} 布尔不算）。

**② 类身份（独立成立）**
- `007E3F30` 4B = `10 72 44 00` = `0x00447210`（= entry）；resolve_slot → `vtable_base=0x007E3EBC`, `slot_off=0x74`, `slot_index=29`，(0x3F30-0x3EBC)/4=29。
- RTTI：`[0x7E3EB8]=0x007FC360`(COL,sig=0) → TD `0x00818D60` → `.?AVBuildingClass@@`；主表槽 0=`0x00410260`。槽号 29 与线索 `vslot29` 自洽。② = `.rdata` RTTI 数据链独立钉住。

**③b 具体形态：③b②（call → mov ebx,eax → cmp ebx → 多路 jcc；多值状态码）**
- 成链字节（自反汇编 `0x447230..`）：
  - `0x44725F mov ecx,[esp+0x20]` / `0x447263 push ecx` / `0x447264 push ebp` / `0x447265 mov ecx,esi`（this）。
  - `0x447267 E8 54 8C 2B 00` = `call 0x6ffec0`（direct，this=esi，2 参数）。
  - `0x44726C 8B D8` = `mov ebx,eax`（**返回值搬入 ebx**）。
  - `0x44726E 83 FB 08` = `cmp ebx,8`；`0x447271 75 09` = `jne 0x44727c`。
  - call→mov→cmp→jne 全程无 ebx 覆写（call 后紧接 mov ebx,eax，再 cmp ebx）。单 call 非多路同一 call。
- 被调 `0x6FFEC0` 返回约定可伪证（atlas size=1842，自入口对齐解码 12 个 ret，全 `ret 8`）：
  - `0x6FFF8A mov eax,7` / `0x6FFFD8 mov eax,0x37` / `0x700003 mov eax,0x37` / `0x7000E8 mov eax,4` / `0x700110 mov eax,8` / `0x700169 mov eax,4` / `0x70018E mov eax,4` / `0x7001E6 mov eax,0x1A` / `0x700569 mov eax,5` / `0x7005E3 mov eax,7` / `0x7005EF xor eax,eax`(=0)（另 1 个 ret @0x700217 无前置常量）。
  - 独立枚举返回常量集合 = **{0x0, 0x4, 0x5, 0x7, 0x8, 0x1A, 0x37}**（7 个互异值）。**是多值状态码集合，不是 {0,1} 布尔**（脚本判定 `is {0,1} bool? False`）。满足「可伪证多值约定」。
- 调用方真拿状态码分派且各路动作不同：
  - `rc==8`：`0x447273..0x447279` 弹栈 + `add esp,0xc` + `ret 8`；call 后 eax 一路到 ret 未被写，eax 仍=8 ⇒ 把 8 原样上抛、不再做事。
  - `rc==4`：`0x44727C cmp ebx,4` / `0x447280 jne 0x447366`（push edi 在 cmp 与 jne 间但不改 flags/ebx）；命中进 `0x447286` 读 `[Type+0xCD1]`、比对 `[this+0x21C]` 与全局 `0xA83D4C` 等**实质工作**。
  - `rc==5`：`0x447366 cmp ebx,5` / `0x44736B call [edx+0x3F8]` 等**另一路实质工作**。
  - `rc==1/2`：`0x4473C7 cmp ebx,1` / `0x4473CC cmp ebx,2` 继续分派；其余落默认。
- 错误码语义：多值状态码 {0,4,5,7,8,0x1A,0x37}，调用方按码分派、动作互异；可枚举、可伪证。非 {0,1} 布尔；非 ③a；被调内部写未充当循环内非栈写。

**④ 使用见证（独立成立，非 direct-only）**
- 安装点 `0x0043B71F C7 06 BC 3E 7E 00` = `mov [esi],0x7E3EBC`（装入活对象 [obj+0]）；所在函数 `0x0043B680` 收尾 `mov eax,esi; ret 4`（返 this = 构造器）；`is_atexit_registered(0x43B680)=[]` ⇒ ㉓ 排除。direct caller=0，靠活虚表链。

**④ 与 ② 不同源**：② = `.rdata` RTTI 数据链（0x7E3F30 槽 + 0x7E3EB8 COL + 0x818D60 TD）；④ = `.text` 构造安装指令 0x43B71F ⇒ same_source=no。

**语义与实测相符**：实测 = 建筑动作分派——调 0x6FFEC0 取多值状态码，按码分支（8 上抛、4/5 各走实质处理、其余默认）。与 delta 第 4 列一致。

**verdict = PASS**

---

## 3. `00447F10` — BuildingClass::vslot240 — verdict: **PASS**

**② 类身份（独立成立）**
- `007E427C` 4B = `10 7f 44 00` = `0x00447F10`（= entry）；resolve_slot → `vtable_base=0x007E3EBC`, `slot_off=0x3C0`, `slot_index=240`，(0x427C-0x3EBC)/4=240。
- RTTI：`[0x7E3EB8]=0x007FC360`(COL,sig=0) → TD `0x00818D60` → `.?AVBuildingClass@@`；主表槽 0=`0x00410260`。槽号 240 与线索 `vslot240` 自洽。② = `.rdata` RTTI 数据链独立钉住。

**③b 具体形态：③b②（call → mov ebp,eax → test ebp → jne；多值状态码）**
- 成链字节（自反汇编 `0x447FA0..0x44806F`）：
  - `0x447FCF push eax` / `0x447FD0 push ecx` / `0x447FD1 push edi`（3 参数）/ `0x447FD2 mov ecx,esi`（this）。
  - `0x447FD4 E8 D7 40 2B 00` = `call 0x6fc0b0`（direct）。
  - `0x447FD9 8B E8` = `mov ebp,eax`（**返回值搬入 ebp**）。
  - `0x447FDB 85 ED` = `test ebp,ebp`；`0x447FDD 75 73` = `jne 0x448052`。
  - call→mov→test→jne 全程无 ebp 覆写（判的是 ebp，eax 未动）。单 call 非多路同一 call。
- 被调 `0x6FC0B0` 返回约定可伪证（atlas size=3208，自入口对齐解码 **32 个 ret，全 `ret 0xC`**）：
  - `0x6FCD20 xor eax,eax` → `0x6FCD26 ret` = **成功 0**；失败出口逐条带常量：`0x6FCA23 mov eax,1`、`0x6FC0EB`/`0x6FC102`/`0x6FC174`/`0x6FC64C`/`0x6FC8BB`… 多处 `mov eax,3`、`0x6FC812`/`0x6FC876`/`0x6FCAC2`… 多处 `mov eax,5`、`0x6FCD35 mov eax,6`、`0x6FCA7E`/`0x6FCD1A mov eax,8`、`0x6FCA5B mov eax,9`。
  - 独立枚举返回常量集合 = **{0x0, 0x1, 0x3, 0x5, 0x6, 0x8, 0x9}**（7 个互异值）。**是多值状态码，不是 {0,1} 布尔**（脚本判定 `is {0,1} bool? False`：虽含 1，但另有 3/5/6/8/9 多个非布尔失败码）。满足「可伪证多值约定」。
- 调用方真拿它分支且两路动作不同：
  - 非零路 `0x448052`：`pop edi` / `mov eax,ebp` / `pop esi` / `pop ebp` / `ret 0xC` → **把被调错误码原样上抛**（eax=ebp=错误码）。
  - 零路 `0x447FDF` 起继续：`0x447FE3 call [edx+0x3fc]`(slot 255)、`0x447FF8 call [eax+0x4e8]`(slot 314) 等后续判定；本函数另有自身返回码 `0x448049 mov eax,2`、`0x447FBA mov eax,3`、`0x44805C mov eax,5`、`0x447FA5 mov eax,6` 表示不同拒绝原因。
- 错误码语义：0=成功，1/3/5/6/8/9=各类失败；可枚举、可伪证。非 {0,1} 布尔；非 ③a；被调内部写未充当循环内非栈写。

**④ 使用见证（独立成立，非 direct-only）**
- 安装点 `0x0043B71F C7 06 BC 3E 7E 00` = `mov [esi],0x7E3EBC`（装入活对象 [obj+0]）；所在函数 `0x0043B680` 收尾 `mov eax,esi; ret 4`（返 this = 构造器）；`is_atexit_registered(0x43B680)=[]` ⇒ ㉓ 排除。direct caller=0，靠活虚表链。

**④ 与 ② 不同源**：② = `.rdata` RTTI 数据链（0x7E427C 槽 + 0x7E3EB8 COL + 0x818D60 TD）；④ = `.text` 构造安装指令 0x43B71F ⇒ same_source=no。

**语义与实测相符**：实测 = 建造/放置合法性判定——先查占位与类型状态，调 0x6FC0B0 做放置判定并把错误码原样上抛（0=成功，多值失败码），自身另返回 2/3/5/6 表示拒绝原因。与 delta 第 4 列一致。

**verdict = PASS**

---

## 4. `0044E8F0` — BuildingClass::vslot10 — verdict: **PASS**

**② 类身份（独立成立）**
- `007E3EE4` 4B = `f0 e8 44 00` = `0x0044E8F0`（= entry）；resolve_slot → `vtable_base=0x007E3EBC`, `slot_off=0x28`, `slot_index=10`，(0x3EE4-0x3EBC)/4=10。
- RTTI：`[0x7E3EB8]=0x007FC360`(COL,sig=0) → TD `0x00818D60` → `.?AVBuildingClass@@`；主表槽 0=`0x00410260`。槽号 10 与线索 `vslot10` 自洽。② = `.rdata` RTTI 数据链独立钉住。

**③b 具体形态：③b②（虚派发 call [edx+0x10] → cmp eax,-1 → je；错误码 -1）**
- 成链字节（自反汇编 `0x44EA60..0x44EB10`）：
  - `0x44EA77 8B 96 6C 06 00 00` = `mov edx,[esi+0x66c]`（成员向量 vptr）；`0x44EA7E 8D BE 6C 06 00 00` = `lea edi,[esi+0x66c]`（容器 this）。
  - `0x44EA88 50` push eax（参数）；`0x44EA89 8B CF` mov ecx,edi。
  - `0x44EA8F FF 52 10` = `call dword ptr [edx+0x10]`（虚派发 slot4 = Find）。
  - `0x44EA92 83 F8 FF` = `cmp eax,-1`；`0x44EA95 74 21` = `je 0x44eab8`。cmp 与 je 之间无 eax 覆写。
- 被调返回约定可伪证（成员 vptr `0x7E43C8`）：
  - `[-4]=0x007FC298`(COL,sig=0) → TD `0x00818D28` → `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@`（InfantryClass* 成员向量）。
  - slot4 `0x7E43D8=0x0045A610`，其 `0x45A62F 83 C8 FF` = `or eax,-1`、`0x45A633 C2 04 00` = `ret 4`；命中路径 eax=下标（`xor eax,eax` 起、`inc eax` 累加）。未找到=-1、命中=下标，字节可伪证。
  - 成员 vptr 由构造器安装：`0x43B6DB C7 86 6C 06 00 00 C8 43 7E 00` = `mov dword ptr [esi+0x66c],0x7e43c8`。
- 调用方真拿 -1 分支且两路动作不同：未命中 `je 0x44eab8` 跳过整段；命中（eax=下标）则 `0x44EA9E dec ecx` / `0x44EAA1 mov [edi+0x10],ecx`（回写 count-1）、`0x44EAAA 8B 14 81 mov edx,[ecx+eax*4]` / `0x44EAAD 89 54 81 FC mov [ecx+eax*4-4],edx`（数组前移压缩，**非栈写**，来自调用方）。cmp-je 间无 eax 覆写；**非多路同一 call**——同函数 `0x44EAD9` 是对另一成员容器 `this+0x684`（vptr 由 `0x43B709 mov [esi+0x684],0x7e43c8` 装同表）的独立 Find，属不同对象。
- 错误码语义：-1=未找到、0..n-1=下标，多值可枚举；非 {0,1} 布尔。被调内部写未充当循环内非栈写（压缩写在调用方）；非 ③a。

**④ 使用见证（独立成立，非 direct-only）**
- 安装点 `0x0043B71F C7 06 BC 3E 7E 00` = `mov [esi],0x7E3EBC`（装入活对象 [obj+0]）；所在函数 `0x0043B680` 收尾 `mov eax,esi; ret 4`（返 this = 构造器）；`is_atexit_registered(0x43B680)=[]` ⇒ ㉓ 排除。direct caller=0，靠活虚表链。

**④ 与 ② 不同源**：② = `.rdata` RTTI 数据链（0x7E3EE4 槽 + 0x7E3EB8 COL + 0x818D60 TD）；④ = `.text` 构造安装指令 0x43B71F ⇒ same_source=no。

**语义与实测相符**：实测 = 对本对象内成员 `DynamicVectorClass<InfantryClass*>`（this+0x66c 与 +0x684）虚派发 Find 目标（-1=未命中），命中则 count-- 并前移压缩移除，未命中跳过。与 delta 第 4 列一致。

**verdict = PASS**

> 用户特别点名行：③ 站点为「返回值先搬进 ebp 再判」。独立确认形态真实且可伪证（多值状态码算、{0,1} 布尔不算）。