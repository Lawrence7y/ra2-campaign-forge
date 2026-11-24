# M40 并表 PROGRESS（merge clerk M40）

合并范围：S03_C5 白名单 5 行 + S09_KPROVED2 白名单 6 行 = 11 行；黑名单 0069DEB0 整行不动。
改前/改后逐行核对依据：`_hygiene\coverage.M40.bak`（改前快照，SHA-256 见 (f)）。

(a) 行数：coverage.tsv 改前 18,431、改后 18,431（数据行均 18,431）；entry 增删 0（entry 唯一数 18,431 → 18,431）。PASS。

(b) grade 直方图（只读第 5 列）：
- [已证]：1,387 → 1,398（+11）
- [静态推断]：6,020 → 6,009（−11）
- [未证]：11,024 → 11,024（不变）
- 和：1,398 + 6,009 + 11,024 = 18,431。PASS。

(c) conflict==1：改前 254、改后 254（未新增/消解）。PASS。

(d) 11 行逐行 grep 验证（改后 grade 与 name 对照改前）：
1. 0055C7C0 [已证] name 逐字节相同 — PASS
2. 0065CF00 [已证] name 逐字节相同 — PASS
3. 0065CB50 [已证] name 逐字节相同 — PASS
4. 00473B10 [已证] name 逐字节相同 — PASS
5. 0065CCE0 [已证] name 逐字节相同 — PASS
6. 006A5840 [已证] name 逐字节相同 — PASS
7. 006D0680 [已证] name 逐字节相同 — PASS
8. 0063FB20 [已证] name 逐字节相同 — PASS
9. 005BE6D0 [已证] name 逐字节相同 — PASS
10. 004E2690 [已证] name 逐字节相同 — PASS
11. 00557730 [已证] name 逐字节相同 — PASS
另核 subsystem 列逐字节相同：11/11 PASS。

(e) 黑名单 0069DEB0：改后 grade 仍 [静态推断]，整行与改前逐字节相同（line 8682）。PASS。

(f) coverage.tsv SHA-256：
- 改前：fc7c6eb6f6d0931e117c1bec5b8e37af387d8ec43c7573eb1ca3166db87d3dc5
- 改后：7364b87f44764a3617cfaa5b0efc5b546a2300ce2a7d0dcde48a848cd2834cd4
- 备份 `_hygiene\coverage.M40.bak` SHA-256 与改前一致。PASS。

PANEL 复算：全表 [已证] 1,398 / atlas 内 1,393（11 行全在 atlas，atlas 外 5 行不变）；
S03 proved 24→29/194=14.95%（差 68），S09 proved 77→83/1051=7.90%（差 443）；
TOTAL proved 1,382→1,393/12,916=10.79%。其余 19 个子系统行一字不动。

写入域核对：仅改 coverage.tsv、PANEL.md、M40\ 与 _hygiene\coverage.M40.bak。
未改 CONFLICTS.tsv / PENDING_CORRECTIONS.tsv / 台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli；未 git commit。
