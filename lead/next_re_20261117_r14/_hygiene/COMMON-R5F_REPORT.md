# COMMON-R5F REPORT

- 备份：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\R14_COMMON.COMMON-R5F.bak`；78,136 B；SHA-256 `3f11b5f099b1f86a9106c9d5dc9f330c16685e1ef7e24203f83dcb0bc2fc1c1f`。
- 改后 `R14_COMMON.md`：79,975 B；SHA-256 `7f1f26216324ee1c70479479c0a9125809fd73c68d3735f86de9a8c5f90afe03`；仅追加 6 行。
- 快照：2026-11-18T05:29:40+08:00，一次脚本读取；`coverage.tsv` SHA-256 `9ef239c22f5c100e3a5ac65e83fafa15ca44cd626c591465c195ecfb496eec94`，`function_atlas.tsv` SHA-256 `4527079b8e1556f0f34bc2c16068ddaef7681ee2b6a5e1f2aadc61a73653db69`。
- 复算脚本：`lead\next_re_20261117_r14\_hygiene\recompute_COMMON_R5F.py`；结果：`lead\next_re_20261117_r14\_hygiene\recompute_COMMON_R5F.json`。
- 统一口径：`coverage.entry` 与 `function_atlas.entry` 均大写后相交；atlas_n=该子系统相交行数；proved=同一相交行中 grade=`[已证]`。
- named_L：`name` 非空且不以 `sub_` 开头（大小写不敏感）。
- named_S（R14-R14 原文）：named_L 上仅再排 `Class::sub_XXXXXXXX`。
- named_S（严格）：named_S(R14) 上再排 `Class::slotN` / `Class::vslotN`。
- S10 实测：atlas_n=526；named_L=513/526=97.53%；named_S(R14)=513/526=97.53%；named_S(strict)=71/526=13.50%；proved=107/526=20.34%。旧 named 511/526 来自 M7 旧截面，已作废。
- S11 实测：atlas_n=368；named_L=358/368=97.28%；named_S(R14)=358/368=97.28%；named_S(strict)=29/368=7.88%；proved=29/368=7.88%。旧 DoD-S `32/368 ｜ 34/368` 及「326 行」不可复现，已作废；实测 slot/vslot 名 329=358−29。
- 分歧：无；strict 29/368 与审计 7.88% 一致，审计所述「只剔 Class::slotN 得 36/368」属更窄口径，不是本卡两套 DoD 口径之一。
- 遗留矛盾 1 更正落点：新文件第 59 行（原 §1 第 57 行后），指明 14,715 已撤回、三分母见 §9。
- 遗留矛盾 2 更正落点：新文件第 18 行（原 §0 第 17 行后）与第 143 行（原 §2.4 第 140 行后），指向 §2.5 与 §995 拒绝闸定位。
- 其余新增落点：第 458 行（§9.0 快照口径）、第 466 行（S10 实测）、第 468 行（S11 实测）。
- 只增不删自检：备份逐行多重集在新文件中的 missing=[]（missing=0）；备份行序列仍是新文件子序列（true）；§6 从标题至 §7 前 45 行逐行严格相等。
