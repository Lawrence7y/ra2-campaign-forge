本批 9 行的 ④ 与 K8/K10 同形（direct call=0，仅活 vptr 安装），受 D-39 约束；Lead 未裁前不得并入 grade，只并入名字与语义。

# S13-K11 PROGRESS（每 3 行增量落盘）

## 判别力诚实声明（先写，勿谎称合同互斥=强判据）
本族合同形态判据在**同族槽上零区分力**（a-S13-K10 审计实测 1,843/1,975 = 93.3% 的族内槽直接满足“合同=槽位方法”，该数字引自卡面/审计、非本卡自算）。本卡正当性**不靠**合同互斥，而靠三件可分离事实：
① 类属独立复算：自走 RTTI 链 dword[vt-4]=COL → [COL+0xC]=TD → TD+8 内联名串，9/9 唯一 vtable 归属，名串 VA 见 EVIDENCE/CORE_NUMBERS.md；
② 槽位落点：目标地址唯一落在 vt+0x10(slot4) 或 vt+0x0C(slot3)，9/9 唯一（0040F760 全镜像 3 处出现但仅 1 处是可解 RTTI vtable）；
③ 结构证据：YRpp/ArrayClasses.h 声明序 slot3=Clear(行123/241)、slot4=FindItemIndex(行129/246)；V 版循环上界 Capacity(行134)、DV 版 Count(行251)，与体内 [ecx+8]/[esi+0x10] 对应（EVIDENCE/STRUCTURE.md）。

## 前置自检（⑨ 停机核验）
- exe ra2youli/gamemd.exe SHA-256 73201cc0…f67476（4,825,360 B）现场复算一致，只读；atlas SHA 4527079b… 一致（但本批 9 行均不在 atlas，边界由反汇编自定）。
- 盘上 coverage.tsv 9 行全部 [静态推断] + 占位名，与卡面 DISK 陈述一致（work/verify_disk.py PASS）；无不符，继续。
- 严禁建 venv / pip install / import K8/K10 work 代码：全部分析为自写 work/k11_analyze.py + work/k11_detail.py。

## 批次 1（3/9 行已完成逐条四环）
| entry | 类名(②独立复算) | slot | ④主安装点 | direct call | ⑱冲突 |
|---|---|---|---|---|---|
| 0040B820 | VectorClass<BombClass*> | 4 | 0x40B60A (C7 05 [0x87F5D8]) | 0 | 0 |
| 0040F5E0 | DynamicVectorClass<WarheadTypeClass*> | 3 | 0x40F4AD (C7 05 [0x8874C0]) | 0 | 0 |
| 0040F760 | VectorClass<WarheadTypeClass*> | 4 | 0x40F4D8 (C7 05 [0x8874C0]) | 0 | 0 |
三行体内合同已逐指令核对（BODIES.txt）：8 行 slot4 为 IsInitialized 守卫 + Capacity 上界循环 + or eax,-1(ret4)；0040F5E0 为 DV Clear（写 +0x10 Count + free + 写 {4,8,0xD}）。
## 批次 2（6/9 行已完成，追加 3 行）
| entry | 类名(②独立复算) | slot | ④主安装点 | direct call | ⑱冲突 |
|---|---|---|---|---|---|
| 0040FD30 | VectorClass<WeaponTypeClass*> | 4 | 0x40FB78 (C7 05 [0x887568]) | 0 | 0 |
| 0046B780 | VectorClass<BulletClass*> | 4 | 0x46632E (C7 05 [0x89DE18]) | 0 | 0 |
| 0048AE90 | VectorClass<DamageGroup*> | 4 | 0x489B1E (栈/this 写；无全局 C7 05) | 0 | 0 |
0048AE90 如实记录：raw-masked 扫描 C7 05 <disp32> <imm32=0x7E5144> 全 .text 0 命中，但 0x489B1E/0x48A491/0x48A4BB([esp+0x38]) 与 0x48AFD6/0x48B026/0x48B088([esi]) 共 6 处活 vptr 写，与 a-S13-K10 VERDICT §5 对 5 行 DamageGroup 的分类一致。PAU=指向 struct，类名 DamageGroup 无 U 前缀（硬约束1）。
## 批次 3（9/9 行全部完成，追加最后 3 行）
| entry | 类名(②独立复算) | slot | ④主安装点 | direct call | ⑱冲突 |
|---|---|---|---|---|---|
| 0054EA10 | VectorClass<KamikazeControl*> | 4 | 0x54E31D (C7 05 [0xABC604]) | 0 | 0 |
| 0062B1F0 | VectorClass<ParasiteClass*> | 4 | 0x6291D8 (C7 05 [0xAC4910]) | 0 | 0 |
| 0065C070 | VectorClass<RadSiteClass*> | 4 | 0x65B1A8 (C7 05 [0xB04BD0]) | 0 | 0 |
KamikazeControl 同为 PAU struct，无 U 前缀（硬约束1）。

## 交付与核心数字复算锚点
- coverage_delta.tsv：9 行 8 列（1 表头 + 9 数据行），全 S13，grade 照实交 [已证]，name_kind=类<槽语义>。
- ① 类属/名串VA：见 EVIDENCE/CORE_NUMBERS.md ①表（9/9 唯一 RTTI vtable）。
- ② slot 落点：8 行 vt+0x10(slot4)、0040F5E0 vt+0x0C(slot3)；见 CORE_NUMBERS.md ②表。
- ③ ④ 安装点：8 行 C7 05 global、0048AE90 栈/this 6 处；direct call 数 9/9=0；见 INSTALLS.tsv / DIRECT_CALLS.tsv。
- ④ direct call 全 0（指令边界 E8 rel32 与 raw E8 双查）；见 DIRECT_CALLS.tsv。
- ⑤ ⑱冲突：9 个 entry 扫 docs/re + re_atlas/kb + 台账 + COVERAGE，各仅 coverage.tsv 占位名行自身，真名冲突 0；见 CONFLICT_SCAN.txt。
- ④ 外证：活 vptr 安装点指令均为指令边界 imm32（raw-masked 与 capstone 双查一致）；exact 派发锚 0x4386AB/0x43942B 的 call [edx+0x10]+cmp eax,-1 已反汇编（DISPATCH_ANCHORS.txt）。
- 0040F5E0 的 KICKOFF 误绑复核：TypeList<PBVVoxelAnimTypeClass> vt 0x7F0D3C slot3=0x67A410（≠本行），本行自身 vt 0x7E1E84 有活安装 @0x40F4AD，体内真 DV Clear（含 +0x10）⇒ 剔除口径不成立，按本卡 ④ 计入。
- ⑨ 内部纠错记录：初稿 CORE_NUMBERS ①表 COL 列误写 vt-4 地址，复核发现 dword[vt-4] 才是 COL 结构地址，已就地改正为实测值（0x7FA708 等）；未影响 ②/③/④/⑤ 数字。

## 结论
9 行全部完成名字（9 个具名语义，无 U 前缀）+ 四环证据；按卡面照实交 [已证]，但首行 D-39 约束有效：Lead 未裁前只并名字与语义、不并入 grade。