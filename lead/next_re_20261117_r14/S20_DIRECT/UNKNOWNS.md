# S20-DIRECT UNKNOWNS

## U1 · coverage.tsv 并发写入（非本卡）
会话期间 `COVERAGE/coverage.tsv` SHA 三次变化：`502A56FE…`（开工）→ `DC471354…` → `2C599504…`（收尾）。
S20 子集始终稳定（410 行 / proved 68 / static 331 / unproved 11），11 个目标行 grade 未变；本卡只交 `coverage_delta.tsv`，由合并员串行应用。
**全库 proved 现值是移动靶**，不在本卡申报唯一值；S20 并入后 = 68+11 = **79**（门槛 205，仍差 126）。

## U2 · 2 行既非 direct 也非虚表可达
`005F3D90`、`007610A0`（均 `[未证]`）在 .text 无 direct E8 caller、.rdata 无 dword 引用 ⇒ 不属于本卡判据范围，也不进 VIRTUAL_SKIPPED（它们连虚表可达都不是）。留后续卡处理。

## U3 · ⑱ 名称 token 误报（0062DF20/0062E070）
`docs/re/landing_pack_particle.md:356` 同一行含 `ParticleClass::Update 0x0062CE40`、`ParticleSystemClass::AI 0x0062FD60` 与 `0x0062DF20/0x0062E070`。
正则按行抓到 `ParticleClass::Update`/`ParticleSystemClass::AI` 两个 token，但它们归属 **其他地址**，不是 0062DF20/0062E070 的竞争名。
本卡 **只报不改名**；这两行仍用 coverage 原名 `ParticleSystemClass::Update_A` / `Update_B`。

## U4 · 007C978A 的语义
`007C978A` = CRT `atexit`（COMMON-R9 ㉓），336 个 direct caller 均为 `push <fn>; call 0x7C978A` 的注册点。
direct call 判据成立（入口是真函数），但 `name` 维持 `sub_007C978A`（弱信号占位名），不改名、不声明 `atexit` 语义——本卡只动 grade。

## U5 · 指令计数与基准微差
本卡全扫 1,394,186 条指令 vs 项目基准 1,392,592（+1,594，0.11%），E8 边界 call **68,253 与基准逐字一致**，覆盖 100%。
差来自 capstone skipdata 对不可解码字节的边界处理，不影响 E8 集；交付站点全部落在全扫 call-site 表内。
