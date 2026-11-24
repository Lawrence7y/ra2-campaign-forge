# S14-F1 · UNKNOWNS

| ID | 项 | 状态 | 说明 |
|---|---|---|---|
| U1 | `HouseClass::Update` 每逻辑帧恰 1 次 | `[静态推断]` | 帧号 `+1 @0x55DE81` 与 `call 0x55E160 @0x55DE9A`、`call [eax+0x5C] @0x55E269` 已证；但 `0x55DE4F..0x55DE81` 有 4 个 skip 条件，未做运行时调用计数。只写“每次 House::Update”为 `[已证]`。 |
| U2 | `House::AI` 11 个主调度块的“每帧都执行” | `[静态推断]` | 11 块按函数内源码序定位；其中 timer/`%8`/`%15`/`%100`/GameMode 门控会跳块，未逐块做调用计数。 |
| U3 | `0x4DA877` 每帧都跑 | `[已证·继承]` | 直接证据来自 `R14_COMMON §1`（`frame%16` 只跳过 `[0x4DA56E,0x4DA63B)`）；本卡只补层级，不重复真机计数。 |
| U4 | AITrigger `Team1/Team2/ConditionType/Comparator/Amount` 的命名键 | `[未证]` | 全镜像字符串扫描（`E08_ai_ini_key_xrefs.txt`）未发现这些字面键；本卡按 `[AITriggerTypes]` CSV 列位与字段读写点锚定，不写成 INI 命名键。 |
| U5 | `Comparator` 6 值的文本别名 | `[未证]` | `0x41F2C4` 跳表可证运算 `<,<=,==,>=,>,!=`；INI 里是 64-hex blob 的第 2 个 dword，别名（LessThan 等）未在二进制出现。 |
| U6 | `AI 数值字段数=9` 的口径 | `[静态推断·口径]` | 9 = 6 个 double 倍率 + 2 个 CampaignMoneyDelta int + 1 个 credit cutoff int。若审计只算 double，值为 **6**；若把 bool/int timer 全算，会 >9。 |
| U7 | `0x6CBCA0` 的字段名 `HasChargeProgressed` | `[已证·继承]` | S16-K1 审计已定名；本卡只独立复核“每 Super 恰 1 次”的循环位置与两调用点，不重做字段级状态机证明。 |
| U8 | `TeamClass` 32-byte hex blob 的其余 24 字节 | `[未证]` | `0x41F86F` 写 32 字节；已证 dword0=Amount、dword1=Comparator，剩余 6 个 dword 未逐项定名。 |
| U9 | `0xA8ED84` 等全局状态在真机中的具体分支命中率 | `[未证]` | 静态卡不做真机采样；EIP 权重未被当作调用频率。 |
