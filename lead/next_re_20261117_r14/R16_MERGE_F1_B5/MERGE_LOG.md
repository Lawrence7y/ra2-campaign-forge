# R16-MERGE-F1-B5 · 并表日志（F1 收官批 4 行）

> 批次 B5（派生集合第 73–76 行，收官批）· 审计 `R16_AUDIT_F1_B5\VERDICT.md` = PASS 4 / FAIL 0 / 必改 0（NIT 2）
> 写域：`COVERAGE\coverage.tsv`（仅 4 行第 4 列）+ `COVERAGE\PANEL.md`（仅 1 条 M93 披露）+ 本产物目录
> 防 off-by-one：先 pin 两份目标，再以 entry + pinned `before_col4` 逐字匹配写回；写后用 pin 对照逐字节还原性自证。
> PANEL 披露编号 **M93**，插入点紧接 M92 块之后；披露写明 **76/76 收官**。

## 1. 改前 / 改后文件状态

| 文件 | 状态 | mtime | 字节 | sha256 | 行数 | LF | CRLF | endsLF |
|---|---|---|---:|---|---:|---:|---:|---|
| coverage.tsv / before | | 2026-11-21T00:55:34.340056+08:00 | 4,077,137 | 822B2112C64451849EF9E7D26D5E0BB02EA9E8B46CD9CCFAC465410CAC1646D8 | 18,499 | 18,498 | 0 | False |
| coverage.tsv / after  | | 2026-11-21T01:03:44.193676+08:00 | 4,079,053 | 3A1DC1DD3F67B7684BF167640CEECF3EC85330CF5B54C31B65A02CA98C993D4A | 18,499 | 18,498 | 0 | False |
| PANEL.md / before | | 2026-11-21T00:55:34.341059+08:00 | 178,833 | 1024A16A0F97CB000908F44B96DA7239CCEF2B69C3DDD1381DAE53AA21A81162 | 652 | 652 | 0 | True |
| PANEL.md / after  | | 2026-11-21T01:03:44.195181+08:00 | 181,634 | 534177A6B6AC1C902FBDB634F84AD588C3BF471CBD3678E2DD86FA8571F56854 | 659 | 659 | 0 | True |

## 2. 4 行第 4 列 before / after

> `append = 改后第4列 − 改前第4列`（改前为改后严格前缀，4/4）。逐行 before/after 全文见 `before_col4.json` + `delta.tsv`。

| # | entry (pin 行号 1-based) | before 长度 | after 长度 | append 长度 | before 第4列（前 90 字） | append 段（前 90 字） |
|---:|---|---:|---:|---:|---|---|
| 1 | 00763200 (L11315) | 553 | 840 | 287 | WaveClass::slot8 —— ③b② 标量删除析构：在全局注册容器 DynamicVectorClass<WaveClass*>（全局 0xA8EC38 / 计数 0xA | ；④ 活表槽位见证：WaveClass::slot8（vt=007F6BF4，槽 8 值=00763200，COL=0080D418 offset=0，RTTI=00847EB0→ |
| 2 | 00763D90 (L11330) | 93 | 412 | 319 | WaypointPathClass 虚槽6（流写出）：以 0x410320→Write 槽校验流，失败返负 HRESULT 原样早退，成功则写头 + 逐 0xc 字节写路点数组后返 | ；④ 活表槽位见证：WaypointPathClass::slot6（vt=007F6E70，槽 6 值=00763D90，COL=0080D5C8 offset=0，RTTI=0 |
| 3 | 00772CD0 (L11625) | 99 | 410 | 311 | WeaponTypeClass 流读入（Load）：经 00410380 读包装读 HRESULT，失败 E_POINTER 负码跳收尾、成功继续；③b② 可伪证错误码由 test | ；④ 活表槽位见证：WeaponTypeClass::slot5（vt=007F73B8，槽 5 值=00772CD0，COL=0080E460 offset=0，RTTI=008 |
| 4 | 00772EB0 (L11626) | 99 | 410 | 311 | WeaponTypeClass 流写出（Save）：经 00410320 写包装写 HRESULT，失败 E_POINTER 负码跳收尾、成功继续；③b② 可伪证错误码由 test | ；④ 活表槽位见证：WeaponTypeClass::slot6（vt=007F73B8，槽 6 值=00772EB0，COL=0080E460 offset=0，RTTI=008 |

## 3. 九个验证项（卡面 §4）

| # | 项 | 结论 | 实测 |
|---:|---|---|---|
| 1 | 1. coverage.tsv 逐字节还原性（pin+before_col4 自证） | PASS | reverted=4 append_exact=4 recon sha=822B2112 bytes=4077137 expected 822B2112 4077137 |
| 2 | 2. 不变量 18498/{8:18498}/1654/1648/6/4行grade | PASS | n=18498 coldist={8: 18498} proved=1654 in=1648 out=6 grade4=True |
| 3 | 3. 仅 4 行第 4 列变化（对照 pin） | PASS | diff_count=4 match4=True bad_other=[] diff_e=['00763200', '00763D90', '00772CD0', '00772EB0'] |
| 4 | 4. 严格前缀 4/4 且其它列同 delta 且追加段逐字 | PASS | prefix=4/4 others=4/4 append_exact=4/4 |
| 5 | 5. 六个实测数（自算，非照抄） | PASS | {"N_pre_A": 1, "N_pre_B": 0, "N_A_pre": 372, "N_A_post": 375, "N_B_pre": 206, "N_B_post": 210} |
| 6 | 6. §12.6/§12.4 命中计数 | PASS | append §12.6=4 §12.4=0; post §12.6=119 §12.4=0; pre §12.6=115 §12.4=0 |
| 7 | 7. PANEL.md 还原性（删 M93 块） | PASS | M93_at_0based=266 M92_at=[259] after_M92=True insert_before_1based=267 rebuilt sha=1024A16A bytes=178833 76_76_marker=True |
| 8 | 8. 达标未翻转 (strict_panel.py) | PASS | 名义=[S15,S16,S17] 严格=[S17] (期望 S15,S16,S17 / S17); rc=0 |
| 9 | 9. 行尾不混用、LF/endsLF 一致 | PASS | cov CRLF=0 LF=18498 endsLF=False (before LF=18498 endsLF=False); pan CRLF=0 LF=659 endsLF=True (before LF=652+7 endsLF=True) |

## 4. 六个实测数（自算，非照抄）

- N_pre_A（4 行改前第 4 列含 `④`）= **1**（00763200，散文式 `④` 计数 1）
- N_pre_B（4 行改前含 `④ 活表槽位见证`）= **0**
- N_A_pre / N_A_post（全表 `[已证]` 且含 `④`）= **372 → 375**（净增 3 = 4 − 1，00763200 改前已含 ④ 故口径 A 不增）
- N_B_pre / N_B_post（全表 `[已证]` 且含 `④ 活表槽位见证`）= **206 → 210**（净增 4）

## 5. 达标集合（strict_panel.py 口径复算，输出到本目录）

- 名义达标：**S15,S16,S17**
- 严格达标：**S17**
- 输出：`strict_panel_b5.py` / `strict_panel_out.txt`（脚本按 B4 同法复制 `RULING_R15_20261119\work\strict_panel.py` 并把 OUT 改到本目录）

## 6. M93 披露（76/76 收官）

- 插入点：PANEL.md 第 267 行（M92 块之后、M77 并表实算说明之前），7 行引用块，M92 在 0-based 259。
- 内容：PASS 4 / FAIL 0 / 必改 0（32/32）；口径 A 372→375（净增 3）、口径 B 206→210（净增 4）；**76/76 收官**（18+18+18+18+4）。
- 两条审计 NIT 已照实写入：① `00763200` 同一格并存旧散文式 ④ 与新成文 ④（计数 1→2，审计核 188 行 witness 行 ④ 计数均 ≥2，合先例，下游按行去重）；② `00772CD0`/`00772EB0` 共用装表指令 `00771E77`，按「2 行 / 1 安装事件」记录。
- 既有内容零删除零改字：删 M93 块后重建 sha256 == 改前 sha256（验证 #7 PASS）。
