# UNKNOWNS · AUDIT-ATEXIT

## U1 【口径】coverage.tsv 在本次测量中途被改写
开工实测 `[已证]` = **1,415**（与卡面一致，⑨ 通过）；测量中该文件 mtime 变为 06:42:39Z、`[已证]` = **1,449**。
处置：钉住快照 `work\snapshot\coverage_pinned.tsv`（SHA-256 `502a56fe…7baf6`）重算全部数字；
旧 1,415 结果一并保留（A=19 / B=0 / C=1,064 / D=332）。**两版结论一致：B=0。** 若 Lead 以 1,415 为基线，取括号内那组。

## U2 【技术】构造器经寄存器传 this 的全局写入，abs-store 判据看不见
本卡判据只把 `mov dword[<abs global>],<vt>` 当“全局锚定写入”。若构造器是
`mov ecx,<global>; call <ctor>` 而 `<ctor>` 内是 `mov [esi],<vt>`（典型：非容器类单例），
该 global 的活值写入不可见 ⇒ 会被判成“只有析构器写过”= 假 B。
- 实测规模：`mov [abs],reg` 且 reg 由 vt 立即数装入的站点**全镜像仅 12 处 / 11 个 global**，
  已单列 `work\absreg_stores.pkl`；命中 0 处与本卡 B 类相关。
- 唯一实际踩中者：`005656D0`（见 PROGRESS §4），已手验改判 A。
- **残余不确定性**：若某 global 的构造路径既非 abs-store 也非该 12 处模式（例如 **lea + 间接传递**），
  本判据会漏其活值。目前没有证据表明存在，但也**没有穷举证明不存在**。

## U3 【判据边界】D-2 = 309 行不是“干净”，是“未证”
D-2 的表只被 `mov [reg],<vt>` 装到**堆对象**上，没有静态 global 可查，故无法静态区分
“构造器装的（活）”与“析构器装的（非活）”。
- 已测：这 309 张表**没有一张**在 atexit 注册函数内被写入 ⇒ 不含本卡的 atexit 污染情形。
- 未测：它们是否由**普通析构器**（非 atexit）装入。启发式尝试（“安装者是否为某表 slot 0/1”）
  在 26 行对照上只能到 21/22 命中（会把 `~VectorClass<T>` 系基类表误判为活值），**故未采用**。
- ⇒ D-2 的正确读法是“环④ 未证（无静态接收者）”，与 a-S20 的 12 行同族缺陷，**不是本卡判其错**。

## U4 【语义】A 类 ≠ 环④ 完整有效
A 只断言“该表是某个 global 的活 vptr、entry 在其对应槽”。它**不**断言存在一条真实派发
（接收者证据、调用点槽号、调用者可归属），后者是 a-S20 的轴。引用 A 时勿越界。

## U5 【口径】atexit 注册函数集的检出精度
用“`call 0x7C978A` 前 40 条指令内的 `push <code imm>`”收集，得 336 个 atexit 调用 / 321 个注册函数。
- 已知**假阳性**：`0x40D1B0`（MouseClass 初始化器）被 40 条窗口误纳（其自身 `push 0x40d260` 才是注册；真正
  atexit 调用在 `0x40D20F`）。方向安全（假阳性只会多判“析构器侧”⇒ 偏 B，不会偏 A）。
- 未做：`_onexit` / 其他 terminators 未纳入（卡面只给 `0x7C978A`）。

## U6 【副产品】D-1 的 23 行值得 Lead 单看
它们 `[已证]` 但**全镜像无任何代码或数据引用**（无 direct call、无立即数、无任何 code-pointer 槽），
例如 `00402190`、`0054E690 Kamikaze::Kamikaze`、`006B6FA0 SpawnManagerClass::SpawnManagerClass`、
`005B3740 MissionClass::GetMissionName(idx)`。本卡不裁决其 grade，仅登记（`EVIDENCE\row_class.tsv` basis 列）。
