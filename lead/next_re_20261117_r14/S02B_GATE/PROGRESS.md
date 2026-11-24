# S02B_GATE · PROGRESS.md（卡号 S02B-GATE）

> 纯静态定位；目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（实算全值 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`）、ImageBase `0x400000`、4,825,360 B。capstone 5.0.7 `skipdata=True`、pefile；未改只读件、未写 COVERAGE/台账/其它卡、未 patch/注入/断点（D-35/D-36 未裁）。
> 分级：字节事实 `[已证]`；「闸=单位占格拒放」这条因果在本卡按字节闭合，但真机命中仍属 D-36 未裁范围。

## 一句话结论
**拒绝闸判据 = 对象 `+0x14` 的 bit0，不是 WhatAmI。** `0x47C738` 调 `0x47C3D0`（选择子 0 / 格对象链 head A `[cell+0xE4]`），后者循环取链上对象，`0x47C427 mov al,[esi+0x14]/0x47C42A and al,1/0x47C430 je` 跳过 bit0=0、保留 bit0=1；只要链上仍有 bit0=1 对象即返回非 0 → `0x47C73F jne 0x47C853` 置 `al=0` 拒。bit0 置 1 是全 `TechnoClass` 派生对象共有的构造行为（唯一写点 `0x6F322F or al,1 → 0x6F3237`），故步兵、车辆、飞行器一律 bit0=1 ⇒ **车辆也被拒，与 LIVE-L2 5/5+5/5 全拒一致**；旧 §2.5「 InfantryClass bit0 恒 1」机理过窄，须更正。

## Q1 — 0x47C620 参数与返回
- 调用约定：`thiscall`，`ecx` = `CellClass*`（调用方 `call 0x5657A0` GetCellAt 后 `mov ecx,eax`，见 EVIDENCE/q4_q5_q6_evidence.txt:164-166）。`ret 0xc` ×10（全部 ret 均 0xc）⇒ **3 个栈参 / 12 字节**（已回溯全部 10 个 ret、无 ret imm16）。
- arg1 `[esp+0x1C]`、arg2 `[esp+0x20]`、arg3 `[esp+0x24]`（入口 esp 为返回地址；prologue `sub esp,8`+4 push 使当前 `[esp+0x20]` 对应入参 2）。arg2 = `BuildingTypeClass*`（RTTI 本卡复验：COL `0x7FC618` → TD `0x8193A8` → TD+8 内联 `.?AVBuildingTypeClass@@`；HouseClass 对照 TD `0x824500` 名字不同）；**不是 HouseClass**（§995 三）。体内 `[arg2+0x16bf]/+0x16be/+0x16b7/+0xe58` 四处标志字节均真出现（0x47C640/6DD/6EB/6F9）。
- 返回：`al`（bool），`al=1` 允许（0x47CA70/0x47CA79 `mov al,1`），`al=0` 拒（多个 `xor al,al` 出口 0x47C6D1/0x47C757/0x47C82A/0x47C853/0x47C86C 等）。调用方 `0x43F2B3 test al,al / je 0x43F504` 据此分流。

## Q2 — 枚举目标格对象的循环
- 主体在 `0x47C3D0`（不是 0x47C620 内）。循环头/回边：`0x47C427` 取对象 → `0x47C4A7 mov esi,[esi+0x30]`（next=对象 +0x30）→ `0x47C4AA test esi,esi` → `0x47C4AC jne 0x47C427`（回边）；边界 = next 链尾 NULL。
- 链表选择 `0x47C400 mov al,[ebp+0xC]`（arg2 byte）：0 → `0x47C40F mov ecx,[ecx+0xE4]`（head A）；非 0 → `0x47C407 [ecx+0xE8]`（head B）。本闸 `0x47C72F` 传 arg2=0 ⇒ 走 head A = `[cell+0xE4]`。
- `this(ecx)` 是 `CellClass*`；故遍历的是**该格对象链 `[cell+0xE4]`（头 A）或 `[cell+0xE8]`（头 B），元素 next=+0x30**，不是独立的「占用表」。`S+0xE4` 即 head A 链头。
- 取到后判：`0x47C427 mov al,[esi+0x14]/0x47C42A and al,1/0x47C430 je 0x47C4A7`（bit0=0 跳过）+ `0x47C432 cmp esi,[ebp+0x10]`（排除对象自身 arg3）；通过者经 `0x47C440 call [vt+0x48]` 取格坐标、算距离、保留最近者于 `[esp+0x14]`，循环结束 `0x47C4B2 mov eax,[esp+0x14]` 返回。

## Q3 — 判定主体：按 bit0，不按 WhatAmI
- 闸判据即 `0x47C42A and al,1` + `0x47C430 je`；被比的是对象 `+0x14` 的 bit0，立即数 1（`24 01`）。无 WhatAmI 判据参与门禁。
- 0x47C620 内确有 WhatAmI 比较，但全是 `{6 Building, 0x24 Terrain, 2 Aircraft}`（0x47C668/694/723/7B3/7EA/825），**无 1 Unit、无 15 Infantry**（印证 §2.4 比较集）；这些用于分支路径，不是拒绝判据。
- **bit0 置 1 写点（全 .text，skipdata 穷举）**：`or reg8,1 → mov [reg+0x14],reg8` 形态全镜像仅 1 处：`0x6F322F or al,1 → 0x6F3237 mov [esi+0x14],al`，宿主函数 `0x6F2B40`（TechnoClass 构造体，体内写 `.?AVTechnoClass@@` vt 0x7F4960/0x7F4944/... 于 0x6F3130/3136/313D/314A）。该路径在 0x6F31E2/31EE/31F8/320E 多支汇合于 0x6F3228、必经 0x6F3237（无绕过）。
- 分类（构造链 RTTI 逐字读）：InfantryClass 构造体 `0x517A50`（`.?AVInfantryClass@@`）→ `0x517A5B call 0x4D31E0`；AircraftClass `0x413D20`（`.?AVAircraftClass@@`）→ `0x413D2B call 0x4D31E0`；UnitClass `0x7353C0`（`.?AVUnitClass@@`）→ `0x7353CE call 0x4D31E0`；三者的中间层 FootClass 构造体 `0x4D31E0`（`.?AVFootClass@@`）→ `0x4D31EA call 0x6F2B40`。BuildingClass 构造体 `0x43B740`（`.?AVBuildingClass@@`）→ `0x43B74B call 0x6F2B40`。⇒ 三类单位共用同一 bit0 写点，无各自「同类写点」；另有 `mov [reg+0x14], imm-odd` 143 处（分布于其它函数，三个单位类构造体内 0 处），非此链。FootClass 构造体自身 `0x4D34DA/4D34E0 or dl,4` 置的是 bit2，不是 bit0。
- 结论：车辆被拒 = UnitClass 经构造链继承同一 bit0=1，闸按 bit0 无类型区分 ⇒ 解释 LIVE-L2「车辆 5/5 全拒」。

## Q4 — 0x47C738 闸输入与语义 / 三全局
- 四标志全是 `[arg2+...]`（arg2=BuildingTypeClass）：`+0x16bf`(0x47C640)、`+0x16be`(0x47C6DD)、`+0x16b7`(0x47C6EB)、`+0xe58`(0x47C6F9)。全 0 时落到 `0x47C6F9 cmp [eax+0xe58],ebp` → 不跳 0x47C76B → `0x47C701`（读 `[0xA8E9A0]`）→ 据其 0/1 分支 → 最终到 `0x47C72F` 组装 `push ebp / lea ecx,[esp+0x14] / push ebp / push ecx / mov ecx,edi / call 0x47C3D0`；`0x47C73D cmp eax,ebp / 0x47C73F jne 0x47C853` 非空即拒。`0x47C745` 另 `push 0x24; call 0x47C4D0` 为 terrain 检查（第二闸 `0x47C805` 同构）。
- 三全局（体内均真出现，按错源 14/15 核）：
  - `[0xA8E9A0]` @0x47C64E/67A/701/791/7C8，实扫 **100 读 / 23 写 / 0 inc-dec**（与 §995 二逐字一致）；体内语义：据其值选择是否先扫 head A 的 WhatAmI==2/6/0x24 预检查再进闸。
  - `[0xA8E7AC]` @首指令 0x47C620，实扫 **100 写**（含 5 处 inc/dec：inc 0x52E0BE，dec 0x443288/446FB0/44A794/65E5F6）⇒ 重入计数器非布尔开关（§8.1 ⑨）；体内语义：非 0 直接 `0x47C632 jne 0x47CA70` 放行。
  - `[0xA8ED6B]` @0x47C6A0，实扫 85 读 / 3 写；体内语义：非 0 走 `0x47C6AD` 调 `0x568300` 分支，0 则 `0x47C6A7 je 0x47C878`（另一路径）。

## Q5 — 0x47C72F 的 {0,0} 与信息来源
- 是：该调用传 `arg1=&[esp+0x14]`（其中 `[esp+0x10]=[esp+0x14]=0`，见 0x47C706/0x47C70C）、`arg2=0`、`arg3=0`，即 packed 坐标 `{0,0}` + 排除对象 NULL。它不按真实目标格选距，只做「head A 上是否存在可占对象」的存在性测试（返回最近者指针，距离基准 {0,0} 不影响存在性）。
- 「目标格有单位」信息来自 **this（ecx）= `CellClass*`**：调用方 `0x43F180` mode 1/3 挂链路径中，`0x43F210`/`0x43F2A7` 两次 `call 0x5657A0` GetCellAt 把逐格坐标（0x43F26D-0x43F290 构造的 `{X,Y}`）解析成 `CellClass*`；`0x43F2AC mov ecx,eax` 传入闸。cell 的 `[+0xE4]` 链正是该真实格的对象链。can-place `[+0x1AC]` @0x43F218（§2）与逐格校验 `call 0x47C620`@0x43F2AE 同在此路径。⇒ 格信息经「调用方逐格 GetCellAt → this」进入，不经 arg1 的 `{0,0}`。

## Q6 — slot 73 四类不对称（字节确认）
- BuildingClass `0x43F180`（2443 B / 707 insn）：体内 53 个 call，含 **1 处 `call 0x47C620`@0x43F2AE**（逐格校验）+ 2 处 GetCellAt + can-place `[+0x1AC]` ⇒ 有逐格占用校验。
- Unit/Infantry/Aircraft 共用 `0x4D3780`（138 B / 61 insn）：5 个 call，**0 处 0x47C620**；TechnoClass 基类 `0x6F4A70`（51 B）：2 个 call，**0 处 0x47C620** ⇒ 只有建筑做逐格校验，这解释「为何只有建筑能重叠、单位不能」。

## 核心数字（审计复算）
- `0x47C620`：thiscall + **3 栈参 / 12 B**（ret 0xc ×10）；arg2 = `.?AVBuildingTypeClass@@`（COL 0x7FC618/TD 0x8193A8）；四标志 +0x16BF/+0x16BE/+0x16B7/+0xE58。
- 枚举循环：回边 `0x47C4AC jne 0x47C427`，next=`+0x30`，边界 `0x47C4AA test esi,esi`；链头选择 `0x47C40F [ecx+0xE4]`（head A）/`0x47C407 [ecx+0xE8]`（head B）。
- 判据比较：`0x47C42A and al,1`（imm=1）+ `0x47C430 je 0x47C4A7`；拒绝跳转 `0x47C73F jne 0x47C853`（第二闸 `0x47C80C jne 0x47C818`）。
- bit0 置 1 写点总数：形态 `or→mov[+0x14]` **1 处**（0x6F322F→0x6F3237，TechnoClass 共用；Infantry/Unit/Aircraft 共用）；imm-odd 直写 143 处（三类单位构造体内 0）。bit2 另 1 处（0x4D34E0）。
- `0x47C738` 相关被读全局 **3 个**：`0xA8E9A0`(23W/100R)、`0xA8E7AC`(100W 含 5 inc/dec)、`0xA8ED6B`(3W/85R)。

## 对 §2.5 的更正建议
1. 把「bit0 恒 1 的 InfantryClass」改为「bit0 恒 1 的**所有 TechnoClass 派生可放置对象**（Infantry/Unit/Aircraft/Vehicle/Building），唯一写点 `0x6F322F`」：否则无法解释 LIVE-L2 车辆 5/5 全拒。
2. 把 §2.5 残留的「`[S+0xE4]` 是否=目标格占用表缺直接证据」更新为已定位：S=CellClass*（调用方 GetCellAt 得出），`[cell+0xE4]`/`[cell+0xE8]` 是格对象双链头、next=+0x30（证据 `0x47C40F/0x47C407/0x47C4A7`）；`{0,0}` 只是存在性测试的距离基准，格由 this 带入 ⇒ 「同格」前提字节闭合。总判断若升 `[已证]` 仍须 D-36 真机命中闸（未裁），本卡不越界。
3. 不写 COVERAGE/台账/COMMON；`coverage_delta.tsv` 0 行（本卡无新取得四环）。
