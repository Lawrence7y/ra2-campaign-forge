# S08-KPROVED2 · DISAGREE / 口径分歧记录

1. `re_atlas/evidence/rtti/symbols.json` 中 `FoggedObjectClass.col_va=008006D0` 与盘上 raw RTTI 链不一致；实际 `[vt-4]=00800768`、`[COL+0xC]=00822438`、TD+8=`.?AVFoggedObjectClass@@`。本卡以二进制 raw chain 为准，见 `EVIDENCE/S08_RTTI_FIXED.tsv`。
2. `symbols.json` 的 `DynamicVectorClass<PAVFoggedObjectClass>` vfunc_count=7 只列本类直接声明槽；raw `vt=007E44F4` slot8..13 还含继承的 VectorClass 方法（`0045AB50` 在 slot10、`0045AC30` 在 slot12）。本卡用 raw `VT_SLOT_MAP.tsv` 作为 ②/④ 槽证据；盘上 name 保持不变。
3. 随机基线卡基线为 1,392,592 指令 / 68,253 `E8`@边界；本卡 rooted traversal（`EVIDENCE/scan_stats_v2.json`）在 `.text` VirtualSize `0x401000..0x7E038D` 上得到 1,377,695 唯一指令 / 67,154 `E8`@边界，差异 1.1% / 1.6%。未据此改卡基线；本卡 8 行的 entry/边界由逐函数 Capstone 反汇编复核。
4. `0047EFE0` 现态 conflict=1；本卡不触碰该行，也不以其作为 ④/③b 证据。
