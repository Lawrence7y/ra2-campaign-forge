# S13-K12 PROGRESS
## 0 premises and selfchecks
- target gamemd.exe SHA-256 73201CC0...F67476 verified READ-ONLY; write domain = S13_K12 + _ghidra/S13-K12 only
- 009 disk recompute: S13 n=240 named=216 proved=86 matches CARD -> go
- 019 selfcheck: 0x4386AB call dword ptr [edx+0x10], mem.index=0 (no-index returns 0 not None); never filters by op.index is None
- baseline FIRST: seed=20261118, pool=112, random 17 rows -> false_positive=0/17 (0.00%)
- full S13: predicate hits 17 == target 17, outside=0, missed=0, precision=recall=100%
- exact dispatch requires slot-value==entry (14) + global vptr write witness -> more specific than C2 15% / S20 20%
- 018 conflict scan: 17 addresses scanned in docs/re + re_atlas/kb + ledger + COVERAGE; no pre-existing name conflict (only coverage.tsv self rows)
- no slot-baseline; no same-source double-count; name/subsystem unchanged; 00773030 untouched; C2 36 rows untouched
## 1 four-ring re-verification (incremental every 3 rows)
- row01 0040B740 ?$VectorClass::PAVBombClass:::vslot2 contract=SetCapacity exact@0x43864a/g0x89c668/s2 [静态推断]->[已证]
- row02 0040B820 ?$VectorClass::PAVBombClass:::vslot4 contract=FindItemIndex exact@0x4386ab/g0x89c668/s4 [静态推断]->[已证]
- row03 0040F680 ?$VectorClass::PAVWarheadTyp::vslot2 contract=SetCapacity exact@0x75d11c/g0x8874c0/s2 [静态推断]->[已证]
  [checkpoint 3/17 rows flushed]
- row04 0040F760 ?$VectorClass::PAVWarheadTyp::vslot4 contract=FindItemIndex exact@0x75d26b/g0x8874c0/s4 [静态推断]->[已证]
- row05 0040F870 ?$DynamicVectorClass::PAVWar::vslot4 contract=FindItemIndex exact@0x75d26b/g0x8874c0/s4 [静态推断]->[已证]
- row06 0040FC50 ?$VectorClass::PAVWeaponType::vslot2 contract=SetCapacity exact@0x771eca/g0x887568/s2 [静态推断]->[已证]
  [checkpoint 6/17 rows flushed]
- row07 0040FD30 ?$VectorClass::PAVWeaponType::vslot4 contract=FindItemIndex exact@0x771f99/g0x887568/s4 [静态推断]->[已证]
- row08 0046B6A0 T_VectorClass_PAVBulletClass__::slot2 contract=SetCapacity exact@0x46649b/g0xa8ed40/s2 [静态推断]->[已证]
- row09 0046B780 T_VectorClass_PAVBulletClass__::slot4 contract=FindItemIndex exact@0x46661b/g0xa8ed40/s4 [静态推断]->[已证]
  [checkpoint 9/17 rows flushed]
- row10 0054E890 T_DynamicVectorClass_PAUKamikazeControl__::slot3 contract=Clear exact@0x54e305/g0xabc604/s3 [静态推断]->[已证]
- row11 0054E930 T_VectorClass_PAUKamikazeControl__::slot2 contract=SetCapacity exact@0x54e315/g0xabc604/s2 [静态推断]->[已证]
- row12 0054E9E0 T_VectorClass_PAUKamikazeControl__::slot3 contract=Clear exact@0x54e305/g0xabc604/s3 [静态推断]->[已证]
  [checkpoint 12/17 rows flushed]
- row13 0054EA70 T_DynamicVectorClass_PAUKamikazeControl__::slot2 contract=SetCapacity exact@0x54e315/g0xabc604/s2 [静态推断]->[已证]
- row14 0062B110 T_VectorClass_PAVParasiteClass__::slot2 contract=SetCapacity exact@0x62927e/g0xac4910/s2 [静态推断]->[已证]
- row15 0062B1F0 T_VectorClass_PAVParasiteClass__::slot4 contract=FindItemIndex exact@0x629482/g0xac4910/s4 [静态推断]->[已证]
  [checkpoint 15/17 rows flushed]
- row16 0065BF90 T_VectorClass_PAVRadSiteClass__::slot2 contract=SetCapacity exact@0x65b277/g0xb04bd0/s2 [静态推断]->[已证]
- row17 0065C070 T_VectorClass_PAVRadSiteClass__::slot4 contract=FindItemIndex exact@0x65b358/g0xb04bd0/s4 [静态推断]->[已证]
  [checkpoint 17/17 rows flushed]
## 2 final
- coverage_delta.tsv: 17 rows, each with ring4 site address + 4-ring evidence path, grade [静态推断]->[已证]
- merged S13 proved: 86 + 17 = 103 (threshold 120, still short 17; NOT claiming达标)
- C2 36 rows NOT touched (D-39 undecided); coverage.tsv/name/subsystem NOT modified
- deliverable files: PROGRESS.md, UNKNOWNS.md, DISAGREE.md, EVIDENCE/, work/
