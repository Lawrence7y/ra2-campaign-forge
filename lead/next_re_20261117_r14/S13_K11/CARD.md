# S13-K11 · 容器族收尾：审计点名的 9 行（8 条漏升 slot4 + 0040F5E0）

## 背景（全部来自 `a-S13-K10` 的独立审计，**不要重新普查全族**）
审计裁决 PARTIAL，两个明确结论：
- **"漏升（非错）8 行"**：`0040B820` `0040F760` `0040FD30` `0046B780` `0048AE90` `0054EA10` `0062B1F0` `0065C070`
  实测**同为 slot4 `FindItemIndex`**，与已升的 3 行（`0040F870` `0048AFA0` `0054EB20`）同形，却留在 `[静态推断]`。
- **`0040F5E0` 的剔除口径不成立**：KICKOFF 记的误绑事实（TypeList<PBVVoxelAnimTypeClass> vt `0x7f0d3c` slot3=`0x67A410`）**复现无误**，
  但其自身 vt `0x7e1e84` 有活安装 `mov dword ptr [0x8874c0],0x7e1e84 @0x40f4ad`，与另 42 行**同形**；体内亦为真 DV `Clear`（含 +0x10）。
  ⇒ 按本卡自己的 ④ 应计入。

盘上现值（Lead 实测）：这 9 行**全部** `[静态推断]`、名字全是占位名（`?$VectorClass::PAVBombClass:::vslot4` / `T_VectorClass_PAVBulletClass__::slot4` / `?$DynamicVectorClass::PAVWar::vslot3`）。

## 本卡唯一目标
把这 **9 行**按容器族映射定名并给四环，产出 delta。**9 行，不多不少。**

## 命名依据（审计已证，可直接用，但你必须自己复核字节）
容器族 slot→method（审计在 **395 张 7 槽族表 × 槽 1/3/4/5/6 = 1,975 槽**上验证，**跨类误挂 0 例**）：
- slot1 = `operator==`（先比 `[x+8]` 再逐元循环返 al）
- slot2 = `SetCapacity`（ret 8）
- slot3 = `Clear`（`call 0x7C8B3D` free + 只写 {4,8,0xD}；**DV 版另写 +0x10**）
- slot4 = `FindItemIndex`（回跳 + `or eax,-1` + ret 4；exact 派发锚 `0x4386AB`/`0x43942B`：`call [edx+0x10]` 后 `cmp eax,-1` 再当**下标**用）
- slot5 = `GetItemIndex`（`[ecx+0xC]` 守卫 + `(arg-Items)>>2`）
- slot6 = `GetItem`（`mov eax,[ecx+4]; mov ecx,[esp+4]; mov eax,[eax+ecx*4]; ret 4`）

## 🔴 三条硬约束（都是本轮审计抓出来的错，别再犯）
1. **类名不许编造**：RTTI 里 `.?AV?$…@PAUDamageGroup@@@` 的 **`PAU` = 指向 struct**，类名是 **`DamageGroup`**。
   `S13_K10` 造出 `UDamageGroup` 被判「镜像/KB/YRpp/台账全库无据」⇒ **本卡严禁出现 `U` 前缀类名**。
2. **⑯ 归属**：同一地址可能同处 **DV 表与 V 表的同一槽**；`VectorClass` 内 `GetItem`/`GetItemIndex` 是 `final`（DV 不覆盖）
   ⇒ 这类行必须归**基类** `VectorClass<X*>`，不得写 `DynamicVectorClass<X*>::GetItem`。
   （slot4 `FindItemIndex` 与 slot3 `Clear` 在 DV 有覆盖版，按 RTTI 实际类写。）
3. **语义不得写体内没有的东西**：V 版 `Clear` **只写 {4,8,0xD}，没有 `[this+0x10]`**（+0x10 只有 DV 版有）。
   `S13_K10` 8 行文案写「写 [this+0x10]=0(DynVec Count)」被判假陈述 ⇒ **本卡每条语义都要给出对应指令偏移**。

## 强制自证
- **② RTTI 自己解**：`[vt-4]=COL → [COL+0xC]=TD → 名在 TD+8 内联串`；读不到 **fail-closed 停下，不许猜**。
- **④ 外部见证**：活 vptr 安装点（`C7 05 <global>,<vt>`）或 exact 派发锚；**direct call 数必须如实报**（本轮实测这些行全为 0）。
- **判别力**：本族判据在**同族槽上零区分力**（审计实测 1,843/1,975 = 93.3% 的族内槽直接满足「合同=槽位方法」）。
  ⇒ 你的正当性**不能只靠合同形态**，必须给 **①类属独立复算 + ②槽位落点 + 结构证据（该槽在该类的声明序，引自 `YRpp\ArrayClasses.h` 并存行号）**。
  请在 PROGRESS 里**明确写这一点**，不要谎称「合同互斥 = 强判据」。
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`），9 个地址逐个查。
- **⑨ 停机核验**：自算值与盘上不符先停下报告。

## 🔴 grade 怎么写（重要）
本卡**照实**给 `[已证]`（四环 + 独立结构证据齐全的行），**但必须在 PROGRESS 首行注明**：
「**本批 9 行的 ④ 与 K8/K10 同形（direct call=0，仅活 vptr 安装），受 D-39 约束；Lead 未裁前不得并入 grade，只并入名字与语义。**」
⇒ 你照常交 `[已证]`，由 Lead/合并员按裁决定夺是否落 grade。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K11\`
`PROGRESS.md`（≤50 行）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S13), name, one_line_semantics, grade, evidence_path, name_kind, 缺环说明`
**每完成 3 行就增量落盘 PROGRESS.md。严禁建 venv / pip install / import S13_K10 或 K8 的 work 目录代码。**

## 核心数字（给审计员复算）
① 9 行的 ② 类属（逐行类名 + RTTI 字符串地址）② slot 落点逐行 ③ ④ 安装点地址逐行 ④ direct call 数逐行 ⑤ 9 个新名的 ⑱ 冲突扫描结果
