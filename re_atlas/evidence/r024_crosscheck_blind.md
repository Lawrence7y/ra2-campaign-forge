# R-024/025 异族盲验

二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`（只读，未修改）。
读字节方式：`.text`/`.data` 的 `rawptr == RVA`，故统一 `fo = va - 0x400000`；与题给 `0x1000+(va-0x401000)` 完全等价（已用 PE 段表核对）。
解码：capstone 5.0.7，按函数体起止区间**线性**解码，全程 0 个解码空洞（每条指令地址连续），未使用单次大段 `md.disasm()`。

## Q1 Read_General
- 不同键名总数：**279**（`Read*` 直接调用 280 次，1 个键被读两次 → 去重 279）
- 函数体范围：`0x0066D530` .. `0x00671E98`（`ret 4` 结束），判据：
  - 起：入口 `55 8B EC 83 E4 F8 81 EC C4 00 00 00`（`push ebp; mov ebp,esp; and esp,-8; sub esp,0xC4`）
  - 止：`0x671E8B C2 04 00` 与 `0x671E96 C2 04 00` 后紧跟 `90` 填充至 `0x671E9F`，下一函数从 `0x671EA0` 起（`A1 A0 0C 7F 00` = `mov eax,[0x7F0CA0]`）
  - 区间内共 5076 条指令；`push ebp/mov ebp,esp` 仅出现在 `0x66D530` 一处；无 `call` 落到本区间内部；分支目标全部落在指令边界上（0 个错位）
- ret 情况：**2 条 `ret 4`**（`0x671E8B`、`0x671E96`），**存在冷块**：
  - `0x66D558: 0F 84 30 49 00 00` = `je 0x671E8E` —— 该条件跳转**跨过**第一条 `ret 4`，落到紧随其后的失败分支块（`0x671E8E: 5F 5E 32 C0 5B 8B E5 5D C2 04 00` = `pop edi; pop esi; xor al,al; pop ebx; mov esp,ebp; pop ebp; ret 4`）
  - 语义：命中块 `mov al,1 ... ret`；未命中块 `xor al,al ... ret`。冷块属于同一函数，不是被复用的邻接函数体
- 读取器构成：ReadInteger 104、ReadDouble 97、ReadString 63、ReadBool 16（合计 280）；280 次调用的"节名"实参**全部**解析为 `dword ptr [0x7F0C9C]`（该全局指向 `0x826278 "General"`）
- 唯一重复键：`EngineerCaptureLevel`（`0x83B414`）在 `0x671E0B` 与 `0x671E30` 各读一次（ReadDouble），分别写 `[esi+0x17F8]` / `[esi+0x17FC]`
- 代表性键名：`DamageFireTypes` `OreTwinkle` `BarrelExplode` `DeadBodies` `IonBlast` `WeatherConClouds` `DominatorDamage` `ChronoPlacement` `SelfHealUnitFrames` `VeteranRatio` `V3RocketPitchFinal` `TalkBubbleTime`

## Q2 Read_AudioVisual
- 不同键名总数：**152**（`Read*` 直接调用 153 次，1 个键被读两次 → 去重 152）
- 函数体范围与判据：`0x006691E0` .. `0x0066B8FF`
  - 起：入口 `A1 7C 0C 7F 00 81 EC BC 00 00 00 53 55 56 57`（`mov eax,[0x7F0C7C]; sub esp,0xBC; push ebx/ebp/esi/edi`，无 `push ebp` 帧）
  - 止：`0x66B8EE C2 04 00`、`0x66B8FD C2 04 00`，之后无填充，下一函数从 `0x66B900` 起（`A1 80 0C 7F 00` = `mov eax,[0x7F0CA0]`）
  - 区间内 2719 条指令，全部可达（0 不可达字节），分支目标 0 错位，`call` 无落入区间内部者
- ret 情况：2 条 `ret 4`（`0x66B8EE`、`0x66B8FD`），同样有冷块：`0x669207: 0F 84 E4 26 00 00` = `je 0x66B8F1`，跨过第一条 `ret` 进入 `pop edi; pop esi; pop ebp; xor al,al; pop ebx; add esp,0xBC; ret 4`
- 读取器构成：ReadString 113、ReadDouble 20、ReadInteger 16、ReadBool 4；153 次调用节名实参全部为 `dword ptr [0x7F0C7C]`（指向 `0x839EA8 "AudioVisual"`）
- 唯一重复键：`Smoke`（`0x836F0C`）在 `0x66B20B` 与 `0x66B24A` 各读一次（ReadString），分别写 `[esi+0xBAC]` / `[esi+0xBB0]`
- 唯一间接调用：`0x66B560 call dword ptr [eax+0xC]`（虚函数，非 INI 读取）

## Q3 12 个列表型键

全部 **在**，且全部走 `ReadString`（`0x00528A10`）。键名压栈均为紧邻 `call` 前的 `68 xx xx xx xx`，imm 即字符串常量 VA。

| 键 | 在? | 调用地址 | 读取器 |
|---|---|---|---|
| BarrelDebris | 在 | `0x66D6F5`（keypush `0x66D6ED`=`0x83CF2C`） | ReadString |
| BaseUnit | 在 | `0x66F7E2`（keypush `0x66F7DA`=`0x83C764`） | ReadString |
| BridgeExplosions | 在 | `0x66DBB0`（keypush `0x66DBA8`=`0x83CEDC`） | ReadString |
| DamageFireTypes | 在 | `0x66D57B`（keypush `0x66D573`=`0x83CF58`） | ReadString |
| DeadBodies | 在 | `0x66D9AA`（keypush `0x66D9A2`=`0x825A20`） | ReadString |
| DropPod | 在 | `0x66D8A8`（keypush `0x66D8A0`=`0x83CF00`） | ReadString |
| ExplosiveVoxelDebris | 在 | `0x66EFB7`（keypush `0x66EFAF`=`0x83C964`） | ReadString |
| MetallicDebris | 在 | `0x66DAAD`（keypush `0x66DAA5`=`0x83CEF0`） | ReadString |
| RepairBay | 在 | `0x66F36A`（keypush `0x66F362`=`0x83C818`） | ReadString |
| Shipyard | 在 | `0x66F5A6`（keypush `0x66F59E`=`0x83C7D0`） | ReadString |
| WeatherConBolts | 在 | `0x66DE33`（keypush `0x66DE2B`=`0x83CEA4`） | ReadString |
| WeatherConClouds | 在 | `0x66DD30`（keypush `0x66DD28`=`0x83CEB4`） | ReadString |

字节样本：`0x66D573: 68 58 CF 83 00`（`push 0x83CF58`），`0x66D57B: E8 90 B4 EB FF`（`call 0x528A10`，rel32 校验 = 0x66D57B+5-0x104B70）。
注意 `DropPod` 精确匹配的是 `0x83CF00` 这一份；文件内另有 `DropPodPuff/DropPodWeapon/DropPodHeight` 等，不能混算。

## 我踩到的坑
- **函数体远超 6KB**：Read_General 实测 `0x4970` ≈ 18.4KB（5076 条指令），Read_AudioVisual `0x2720` ≈ 9.8KB（2719 条指令）。题面"每函数 ≤6KB"仅对其中一段成立，不能按预设窗口截断，否则会漏读约 2/3 的键。
- **结尾不是单 ret**：两函数都是"正常出口 ret + 冷块 ret"，冷块由入口附近的 `je` 从上方跨过第一条 `ret` 进入。只扫到第一个 `ret` 会漏掉最后 1 次读取（`TalkBubbleTime` / `FallBackCoefficient`），也就少 1 个键。
- **`push` 窗口会被 fpu 序列打断**：ReadDouble 的实参走 `sub esp,8; fstp qword ptr [esp]`，不是 `push`，按"连续 push 计数"会得到 2/3/4/5 混杂的参数个数。可靠判据是"最后一个 push = 节名、倒数第二个 push = 键名 imm"，用该判据 280/153 次调用全部解析成功、无一例外。
- **键名不等于"读到的键"**：`Read_General` 里还有 86 个字符串常量（`TeamDelays`、`AlliedBaseDefenseCounts`、`AIIonCannon*` …）是传给 `0x475D70`/`0x67BB10`/`0x67BAC0`/`0x474620` 等**包装函数**的，包装函数内部才 `call 0x528A10`。若把包装也算进"本函数直接调用"，General 会是 279+86=365、AV 会是 152+8=160。本报告的 279/152 严格按"函数体内的 `Read*` 直接调用"口径。
- **`0x474620` 是 ReadDouble 的薄包装**（`0x474631 call 0x5283D0`，默认值 `-1.0`），容易被误当成普通读取器；`SlaveMinerShortScan`、`Stray`、`CloseEnough`、`CameraRange` 都走它。
- **键常量在 .data 而非 .rdata**：`DeadBodies` 位于 `0x825A20`（`.data` RVA 区内，文件偏移恰为 `0x425A20`），其余键在 `0x83xxxx`。用"只搜 .rdata 字符串"的做法会漏。
- **同键双读是原样存在的**：`EngineerCaptureLevel`×2、`Smoke`×2，不是解码重复。若用"调用次数"当键数会得出 280/153 而非 279/152。

## 置信度边界
- 只做静态解码，未运行游戏、未挂调试器，因此**不能确认**这些键运行时真的被 INI 命中（`Read*` 返回默认值也算一次调用）；键名是否正确只到"立即数指向的 ASCII 串"这一步。
- 统计口径限于"函数体区间内的 `call` 目标 ∈ {0x528A10, 0x5276D0, 0x5283D0, 0x5295F0}"。经包装函数（86 / 8 个键）和虚调用（`0x66B560`）间接读到的键未计入 Q1/Q2 主数。
- 无法排除同一 `General` 节的其他键在**别的函数**里被读取（例如 `Rules`/`AI` 相关类），本报告不主张 279/152 是全部 General/AudioVisual 键名。
- 两函数体边界靠"`ret 4` + 填充/下一函数序言 + 无内部 `call` 目标 + 全部字节可达"四重判据确定，未依赖任何符号表或调试信息；若该二进制存在手写跳转表/异常表入口则会漏判，本次扫描未见间接跳转（Read_General 0 个，Read_AudioVisual 1 个虚调用且不在两 `ret` 之后）。
