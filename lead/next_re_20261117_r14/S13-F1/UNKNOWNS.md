# S13-F1 UNKNOWNS

| # | 未决项 | 影响 | 下一步定位思路 | 分级 |
|---|---|---|---|---|
| U1 | `0x708080`（ReceiveDamage 在 NowDead 分支 @0x7027E9 调用，1846 B）的精确语义名未锚：疑为死亡处理/计分入口，内含 0x65C7E0 RNG、0x5B3A00、0x6EC250、0x56D100 等 | 不影响调用图（调用点 0x7027E9 已实证），只影响命名 | 沿其 6 个 callee 逐一查语义；真机 bp 0x7027E9 看栈 | [未证] |
| U2 | `TechnoTypeClass+0x9C` 字段名（用作 Verses 索引）的写点未在本卡独立锚定（本卡只有读点 @0x701D59 + 11 维枚举支撑） | 索引来源的「字段名」层面；索引值的传递链已实证 | 扫 TechnoTypeClass::LoadFromINI 中 `[esi+0x9C]` 写点（Armor= 键）；真机读 type+0x9C 与 Verses 倍率对照 | [静态推断]（字段语义），路径本身 [已证] |
| U3 | `GetFireError` 槽 240 的映射由 Unit 包装 @0x7413BC 的 v240 调用 + 返回值语义（FireError 枚举）推定，未逐槽做 RTTI 名核对 | 目标合法性判定的函数名层面；门控调用点已证 | 查 `re_atlas kb` 具名地址或真机断点验证 0x6FC0B0 返回值 | [静态推断] |
| U4 | 9 处 Verses FPU 访存中 V2–V6 的属主函数名未锚（V1=GetTotalDamage 0x489180 已锚） | 不影响 V1 主伤害路径；仅威胁评估/有效性判定命名 | 用 fn_at 区间逐一定界 + `re_atlas kb S13` 具名 | [静态推断] |
| U5 | BulletClass::Array 另一写点 `0x4E6891`（`mov [0xA8ED50],eax`，atlas 无函数覆盖，疑为静态清理/Reset）精确归属 | 不影响增/减点结论（两处均实证） | 查 `0x4E6860` 所属 loader/shutdown 链；真机看调用时机 | [未证] |
| U6 | 卡面「slot 85 开火」猜测的真身 `0x70E2B0`（TechnoClass v85）语义未锚 | 仅记录否证依据；不阻塞主链 | 查 0x70E2B0 是否 TurretControl 计时包装（YRpp 注释指 0x70ECE0） | [未证] |

说明：以上均不改变 FLOW.md 的 8 跳调用图与 4 个核心数字；U1–U6 为「地址已实证、命名/次要语义未锚」。
