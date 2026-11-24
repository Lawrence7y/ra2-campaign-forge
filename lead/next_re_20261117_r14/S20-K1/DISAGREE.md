# S20-K1 DISAGREE（与旧文档/台账冲突引节号）

> 口径：以**本卡字节级 RTTI/imm32/读写点**为准；旧文档仅作线索。每条带旧出处与本卡证据。

| # | 旧表述（出处） | 本卡实测 | 判定 |
|---|---|---|:---|
| D1 | "类名按头文件名推断"（错源④，`R14_COMMON.md` §8.1 ④；`docs/re/fx_draw_chain.md` 全篇按 `AnimClass/ParticleClass/ParticleSystemClass` 称呼） | RTTI 实测名恰为 `.?AVAnimClass@@`/`.?AVParticleClass@@`/`.?AVParticleSystemClass@@`/`.?AVVoxelAnimClass@@`（TD 0x8182C8/0x8366E8/0x836748/0x845E50） | **一致**（但来源是 RTTI 实测，非头文件）；若 RTTI 名不同本卡会 fail-closed 并在本表记录，实测无差异 |
| D2 | `vtables_v2.json` 槽数 13,351 / 1214 表（R14 §8.1 错源①） | 本卡自 `.rdata` 实测 **14,044 槽 / 1,214 表**，与审计基线一致；JSON 794 表各少 1 末槽 | **旧 JSON 错**，本卡未采用；S20 主表槽数（124/123/122/122）为实测值 |
| D3 | "AnimClass IsFogged 有半透明淡出公式" / "`+0x184` 是隐藏 bool"（`docs/re/fx_draw_chain.md` §2.2/§7-Q1/§6-H-FX13；R7 §19.5 已勘误为硬切+DelayTimer） | 字节：`+0x184` 是 int，Update `dec`（0x424390）、DrawIfVisible `test;xor al,al;ret 0xC`（0x422C70）；`+0x199`/`+0x19D` 是硬切 `jne 0x4238A3`，黑雾仅 0x42362C 置灯色 0，无渐变 | **支持 R7 勘误**，否证淡出公式；旧 H-FX13"写 +0x184 跳过绘制"风险应升 `[高]`（会推迟动画启动，R7 §19.5 同） |
| D4 | ParticleClass 槽 69 表项 `0x7EFA68` / PSys `0x7EFCB0`（`bullet_particle_fog_deep_dive.md` §5.1、`R7_vxl_fx_gap.md` §19.2） | RTTI 主表 `0x7EF954+0x114=0x7EFA68`、`0x7EFB9C+0x114=0x7EFCB0`，槽值分别 `0x62CEC0`/`0x62E280` | **一致**（本卡重新取证，非引用） |
| D5 | ParticleClass 实例尺寸 0x138 / ParticleSystemClass 0x100（`bullet_particle_fog_deep_dive.md` §5.2 / `fx_draw_chain.md`） | v[12] `B8 38 01 00 00 C3`(0x62D970)/`B8 00 01 00 00 C3`(0x630200) + 8/24 分配对 | **一致**（双通道证实） |
| D6 | "`0x508F60` = 每帧迷雾更新总入口"（台账 §962，已作废索引） | 本卡更新入口只按 vtable 槽/调用点定：Anim v23 `0x423AC0`、PSys `0x62DF20`/`0x62E070`；未引用 `0x508F60` | **遵守作废索引**；未使用该错标 |
| D7 | "视口内对象每帧无条件 Draw" / "引擎无裁剪"（台账 §919/§920，已由 §924/§925 覆盖） | 本卡 Draw 全 0 直接调用者、经 v[65]；Anim v[65] `0x422C70` 有 +0x184 门；共享 `0x5F4B10` 有脏标记/视口逻辑（R14 §4.4/§4.5 已入账） | **不重复旧错**；本卡不声明"无条件绘制" |
| D8 | 字段跨类套用（R14 §8.1 ⑥ / KB §12："`+0x94` 在别的类是函数指针"） | 本卡字段语义只用各类自己的写者+读者；`+0xF4`(PSys) 有 0x62DCFA 写 29 + 0x62E352 读；未把 `+0xF4` 套到 ParticleClass | **未冲突**（纪律遵守）；如后续 N 卡跨类套用需警惕此反例 |

> 无"新发现与台账冲突"需要本卡改台账；本卡不写台账、不改 coverage.tsv（只交 `coverage_delta.tsv`）。
