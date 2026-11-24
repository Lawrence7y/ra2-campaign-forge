# COMMON-R6_REPORT

- 目标：`lead/next_re_20261117_r14/R14_COMMON.md`（只增不删；§6 纪律 19 条未改）。
- 备份：`_hygiene/R14_COMMON.COMMON-R6.bak`；79,975 B；SHA-256 `7f1f26216324ee1c70479479c0a9125809fd73c68d3735f86de9a8c5f90afe03`。
- 旧文件：79,975 B；wc -l=521；split('\n').length=522。
- 新文件：87,445 B；wc -l=578；split('\n').length=579；SHA-256 `cd9c0ffd2f770e4ca462433a089400c4d32102694d6343f772edda1e61147b9b`。
- 自检：旧行多重集 missing=0；旧行序列为新文件子序列=true；§6 原文逐字一致=true。

## 落点行号

- §8 三条硬错源 ⑭/⑮/⑯：L410–416（正文 L414–416；台账 §1000 二）。
- §8.2 两项坑：L431–436（COL vt-4 L435；B8 ret4 交叉索引 L436，旧记录未改）。
- §9 DoD 现态刷新：L488–502（§9.0a 标题 L490；S22 行 L502）。
- 待裁速查校核：L532–542；§10 冲突台账现态：L544–553。
- 刷新记录追加：L577（仅追加第 13 行）。

## 现场复算（单遍盘上快照）

- 时点：截至 2026-11-18 07:0x；实读 2026-11-18 07:10:33+08:00；§1000 入账后；快照 `_hygiene/recompute_COMMON_R6.json`。
- 同读输入 SHA-256：coverage `4b243580…45cc2c4f`；CONFLICTS `31a89158…f5dbdf9497e05`；atlas `4527079b…36a73653db69`。
- coverage.tsv：数据行 **18,431**（wc -l 18,432 / split 18,433）；第 5 列 grade **[已证]=1,369**、[静态推断]=6,031、[未证]=11,031；**conflict=1=252**。
- S17：named(S) 92/102=90.20%、proved 54/102=52.94%，达标零余量（严格 named 56/102）。
- S15：named(S) 141/158=89.24%、proved 98/158=62.03%（差 2 个名字）。
- S13：named(S) 214/240=89.17%、proved 74/240=30.83%；240/148 双分母，74/148=50.00%，D-37 待裁。
- S10：named_L=named_S(R14) 513/526=97.53%、proved 114/526=21.6730%（004D85D0 未计入）。
- S11：atlas_n=368；named_L=358/368、named_S(R14)=358/368；named_S(strict)=29/368、proved=29/368。
- S22：4,851 行（coverage∩atlas），不得参与百分比排名；D-37 第二实例低收益：可迁 291 行 / 真业务类 27 / 其中 [已证] 仅 13。
- CONFLICTS.tsv：466 行（wc 含表头；465 数据行 / split 467）；字段 subsystem=180 / name=274 / grade=11；RESOLVED 64=M13 15+M14 49。
- C3 真名撞车 58 条：cov=24 / other=14 / deadlock=6；落地改名 16 行（M13 2 + M14 14）；deadlock=6 待人工裁决。

## 原文核对

- 台账：§998 L34469 / §999 L34554 / §1000 L34635。
- 错源：S10_K13/_audit/VERDICT.md:8,18-21,25；S10_K14/PROGRESS.md:6-8；S10_K9/_audit/VERDICT.md:12,24。
- 冲突/技能：C3_44/SUMMARY.md:5；HANDOFF_R14_R3.md:66；M13_REPORT.md:19-27；M14_REPORT.md:20-23；M15_REPORT.md:10-12。
