# COMMON-R8 PROGRESS

改动文件：`R14_COMMON.md`｜备份先行：`_hygiene\R14_COMMON.COMMON-R8.bak`（改前写入，92,609 B / SHA-256 3b812684…5aba）
改前：**92,609 B / 622 行**（split 长度，含末空行）→ 改后：**102102 B / 679 行**（+9,493 B / +57 行；只增不减，原 494 非空行 0 丢失）

## 并入清单（逐条：条项 / 加在哪个 § / 来源路径）

### A · 新增错源候选（接 §8，19→22）
1. ⑲ capstone op.index 陷阱 → §8.1 追加表，来源 `S13_K9\_audit\VERDICT.md` §4。
2. ⑳ 族级判据按族内随机算 → §8.1，来源 `S13_K10\_audit\VERDICT.md` §4。
3. ㉑ 合取判据自洽=循环论证 → §8.1，来源 `S13_K10\_audit\VERDICT.md` §4。
4. ㉒ 模板前缀不是类名 → §8.1，来源 `S13_K10\_audit\VERDICT.md` §3。
### B · 既有条款正面精化
5. ⑰ 精化（虚③④物理同源、替代证据链、待 D-39） → §8.1 ⑰ 行后，来源 `S13_K8\_audit\VERDICT.md` §五 + `S13_K10\_audit\VERDICT.md` §5。
6. ⑯ 实例增补（DV/V 同槽 + final ⇒ 归基类 VectorClass） → §8.1 ⑯ 行后，来源 `S13_K10\_audit\VERDICT.md` §3。
### C · 新事实独立小节
7. 容器族 slot1–6→method 映射表 + 旁证 1,975 槽 0 误挂 + exact 锚 → 新 §8.4，来源 `S13_K10\_audit\VERDICT.md` §2 + `S13_K9\_audit\VERDICT.md` §3。
### D · 环境/流程/现态
8. D1 coverage.tsv 格式陷阱（表头逗号/数据 TAB） → §7 环境表，来源：本段 Lead 盘上实测（SHA b903b798…）；`S13_K9\_audit\VERDICT.md` §6。
9. D2 派卡纪律增补第 20 条（盘面数字当场重读） → §6 纪律第 20 条，来源 `M23\PROGRESS.md` §2 + `S16_N2\PROGRESS.md` ①。
10. D3/D4 现态刷新（coverage 18,431/1,387/6,013/11,031、conflict=254、台账 3,370,848B/35,216 行/§1006、H25 前缀哈希只增不减、达标 3 个 S15/S16/S17、S13 216/240 proved 86） → 新 §9.0c，来源：本段单遍盘上读取 + `_hygiene\H25_baseline.json`。
### E · §1 作废索引增补
11. E1 S13_K7 exact11=0 作废 → §1，来源 `S13_K9\_audit\VERDICT.md` §4。
12. E2 S13_K8 降 00773030 提议被拒 → §1，来源 `S13_K8\_audit\VERDICT.md` §二。
13. E3 S16_N1 未动 grade 失实 → §1，来源 `S16_N1\_audit\VERDICT.md` §1/§2。
14. E4 S16_N1 DISAGREE D3 为假 → §1，来源 `S16_N1\_audit\VERDICT.md` §4-1。

## 拒绝并入（纪律 ⑨：与盘上不符则不改）
无。全部 14 条逐条对照来源 VERDICT/PROGRESS 原文与盘上实算（coverage/atlas/台账/子系统 named-proved）核实一致，并入条数 14，拒绝 0。

## 盘上核验记录（⑨ 自算）
- coverage.tsv：18,431 数据行；grade 已证 1,387 / 静态 6,013 / 未证 11,031（和=18,431）；conflict=1 254；表头逗号、数据 TAB（8 列）——与 CARD D1/D3 一致。
- atlas：12,916 数据行（下界）——与 D3 一致。
- 台账：3,370,848 B / split 35,216 行 / 最大 §1006；H25 baseline 前缀哈希逐字符相同（只增不减）——与 D3 一致。
- 子系统：S15 144/158+101/158、S16 81/90+46/90、S17 94/102+54/102、S13 216/240+proved 86——与 D4 一致。
- 原文件 494 非空行全部保留（0 丢失），只增不减。
