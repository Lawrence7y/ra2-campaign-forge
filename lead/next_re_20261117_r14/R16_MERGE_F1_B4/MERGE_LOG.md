# R16-MERGE-F1-B4 · 并表日志

> 批次 B4（派生集合第 55–72 行）· 审计 `R16_AUDIT_F1_B4\VERDICT.md` = PASS 18 / FAIL 0 / 必改 0
> 写域：`COVERAGE\coverage.tsv`（仅 18 行第 4 列）+ `COVERAGE\PANEL.md`（仅 1 条 M92 披露）+ 本产物目录
> 防 off-by-one：先 pin 两份目标，再以 entry + pinned `before_col4` 逐字匹配写回；写后用 pin 对照逐字节还原性自证。

## 1. 改前 / 改后文件状态

| 文件 | 状态 | mtime | 字节 | sha256 | 行数 | LF | CRLF | endsLF |
|---|---|---|---:|---|---:|---:|---:|---|
| coverage.tsv | before | 2026-11-21T00:38:08.362989+08:00 | 4,068,561 | 400D211A53AB55C7E24E85B389727934C235FBE66A7B52FB5736313DBBC69F7F | 18,499 | 18,498 | 0 | False |
| coverage.tsv | after  | 2026-11-21T00:55:34.340056+08:00 | 4,077,137 | 822B2112C64451849EF9E7D26D5E0BB02EA9E8B46CD9CCFAC465410CAC1646D8 | 18,499 | 18,498 | 0 | False |
| PANEL.md | before | 2026-11-21T00:38:08.364495+08:00 | 175,996 | 607BB21F58CE9D4660D5DD5A2BB43E9FCE294EC2845A9F11459169C80F93A252 | 645 | 645 | 0 | True |
| PANEL.md | after  | 2026-11-21T00:55:34.341059+08:00 | 178,833 | 1024A16A0F97CB000908F44B96DA7239CCEF2B69C3DDD1381DAE53AA21A81162 | 652 | 652 | 0 | True |

## 2. 18 行第 4 列 before / after

> `append = 改后第4列 − 改前第4列`（改前为改后严格前缀，18/18）。逐行 before/after 全文见 `before_col4.json` + delta.tsv。

| # | entry (pin 行号 1-based) | before 长度 | after 长度 | append 长度 | before 第4列（前 90 字） | append 段（前 90 字） |
|---:|---|---:|---:|---:|---|---|
| 1 | 006E6470 (L9814) | 145 | 444 | 299 | TagTypeClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax +  | ；④ 活表槽位见证：TagTypeClass::slot6（vt=007F45C4，槽 6 值=006E6470，COL=0080BCF0 offset=0，RTTI=00842C |
| 2 | 0071CDA0 (L10401) | 133 | 432 | 299 | TerrainClass 虚槽5（流读入）：以 0x5f5e80→0x410380 校验流并整体读入 Terrain；失败返负 HRESULT 原样早退，成功装 vt 0x7f52 | ；④ 活表槽位见证：TerrainClass::slot5（vt=007F522C，槽 5 值=0071CDA0，COL=0080C3E0 offset=0，RTTI=00842D |
| 3 | 0071E1D0 (L10421) | 115 | 430 | 315 | TerrainTypeClass 虚槽5（流读入）：以 0x5f9720→0x410380 校验流并整体读入 TerrainType；空/失败返负 HRESULT 原样早退，成功则 | ；④ 活表槽位见证：TerrainTypeClass::slot5（vt=007F5458，槽 5 值=0071E1D0，COL=0080C498 offset=0，RTTI=00 |
| 4 | 0071F8C0 (L10437) | 106 | 399 | 293 | TEventClass 构造: 调 0x410380 初始化，失败返回 E_POINTER(0x80004003) 经 jl 分支提前返回，成功路安装 TEventClass vt | ；④ 活表槽位见证：TEventClass::ctor（vt=007F5578，槽 5 值=0071F8C0，COL=0080C5E0 offset=0，RTTI=008446F8 |
| 5 | 0071F930 (L10438) | 144 | 439 | 295 | TEventClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + j | ；④ 活表槽位见证：TEventClass::slot6（vt=007F5578，槽 6 值=0071F930，COL=0080C5E0 offset=0，RTTI=008446F |
| 6 | 0071FA80 (L10445) | 234 | 529 | 295 | TEventClass 删除析构器（slot8，含 test byte[esp+0xc],1 → call 0x7C8B3D 释放路）：装 4 张 vt 并调基类析构 007258 | ；④ 活表槽位见证：TEventClass::slot8（vt=007F5578，槽 8 值=0071FA80，COL=0080C5E0 offset=0，RTTI=008446F |
| 7 | 007220A0 (L10496) | 98 | 401 | 303 | TiberiumClass 虚槽7（类型数组指针获取，非流 I/O）：以 0x4103E0 经 [vt+0x30] 取指针，空出参返 E_POINTER 原样早退，成功则指针 +4 | ；④ 活表槽位见证：TiberiumClass::slot7（vt=007F5728，槽 7 值=007220A0，COL=0080C7D8 offset=0，RTTI=00844 |
| 8 | 007220D0 (L10497) | 88 | 391 | 303 | TiberiumClass 虚槽6（流写出）：以 0x410320→Write 槽校验流并写出计数，失败返负 HRESULT 原样早退，成功则写计数 + 逐元素写数组后返 0。 | ；④ 活表槽位见证：TiberiumClass::slot6（vt=007F5728，槽 6 值=007220D0，COL=0080C7D8 offset=0，RTTI=00844 |
| 9 | 00726860 (L10585) | 158 | 457 | 299 | TriggerClass 流读入并就地构造（slot5）：先经 00410380 读包装读基类部分，空流返回 E_POINTER 0x80004003，本行 test eax,ea | ；④ 活表槽位见证：TriggerClass::slot5（vt=007F5858，槽 5 值=00726860，COL=0080C968 offset=0，RTTI=00842C |
| 10 | 007268D0 (L10586) | 145 | 444 | 299 | TriggerClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax +  | ；④ 活表槽位见证：TriggerClass::slot6（vt=007F5858，槽 6 值=007268D0，COL=0080C968 offset=0，RTTI=00842C |
| 11 | 00726950 (L10592) | 237 | 536 | 299 | TriggerClass 删除析构器（slot8，含 test byte[esp+0xc],1 → call 0x7C8B3D 释放路）：装 4 张 vt 并调基类析构 00725 | ；④ 活表槽位见证：TriggerClass::slot8（vt=007F5858，槽 8 值=00726950，COL=0080C968 offset=0，RTTI=00842C |
| 12 | 00727BF0 (L10612) | 162 | 477 | 315 | TriggerTypeClass 流读入并就地构造（slot5）：先经 00410380 读包装读基类部分，空流返回 E_POINTER 0x80004003，本行 test ea | ；④ 活表槽位见证：TriggerTypeClass::slot5（vt=007F5904，槽 5 值=00727BF0，COL=0080CA20 offset=0，RTTI=00 |
| 13 | 00727C80 (L10613) | 149 | 464 | 315 | TriggerTypeClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,ea | ；④ 活表槽位见证：TriggerTypeClass::slot6（vt=007F5904，槽 6 值=00727C80，COL=0080CA20 offset=0，RTTI=00 |
| 14 | 007281A0 (L10621) | 88 | 375 | 287 | TubeClass 虚槽5（流读入）：以 0x410380→Read 槽校验流并读入 Tube；失败返负 HRESULT 原样早退，成功则装 vt 0x7f59b0 后返 0。 | ；④ 活表槽位见证：TubeClass::slot5（vt=007F59B0，槽 5 值=007281A0，COL=0080CAD0 offset=0，RTTI=00844A70→ |
| 15 | 00749F30 (L10984) | 458 | 769 | 311 | VoxelAnimClass::slot23 —— ③b④ 8 邻域扫描：当 [Type+0x300] 标志置位且本帧未处理时，从 edi=0 遍历 8 个方向偏移（[edx*4+ | ；④ 活表槽位见证：VoxelAnimClass::slot23（vt=007F6318，槽 23 值=00749F30，COL=0080CDF8 offset=0，RTTI=00 |
| 16 | 0074BA30 (L11008) | 519 | 842 | 323 | VoxelAnimTypeClass::slot8 —— ③b② 标量删除析构（双注册表）：复位 4 表、call 0x7258D0 解引用后，在 DynamicVectorCla | ；④ 活表槽位见证：VoxelAnimTypeClass::slot8（vt=007F6548，槽 8 值=0074BA30，COL=0080CEB0 offset=0，RTTI= |
| 17 | 0075E0C0 (L11273) | 105 | 420 | 315 | WarheadTypeClass 流读入（Load）：经 00410380 读包装读 HRESULT，失败 E_POINTER 负码跳收尾、成功继续构造并写回；③b② 可伪证错误码 | ；④ 活表槽位见证：WarheadTypeClass::slot5（vt=007F6B30，槽 5 值=0075E0C0，COL=0080D360 offset=0，RTTI=00 |
| 18 | 0075E2C0 (L11274) | 100 | 415 | 315 | WarheadTypeClass 流写出（Save）：经 00410320 写包装写 HRESULT，失败 E_POINTER 负码跳收尾、成功继续；③b② 可伪证错误码由 tes | ；④ 活表槽位见证：WarheadTypeClass::slot6（vt=007F6B30，槽 6 值=0075E2C0，COL=0080D360 offset=0，RTTI=00 |

## 3. 九个验证项（卡面 §4）

| # | 项 | 结论 | 实测 |
|---:|---|---|---|
| 1 | 1. coverage.tsv 逐字节还原性（对照 pin） | PASS | reverted=18 append_exact=18 recon sha=400D211A bytes=4068561 expected 400D211A 4068561 |
| 2 | 2. 不变量 18498/{8:18498}/1654/1648/6/18行grade | PASS | n=18498 coldist={8: 18498} proved=1654 in=1648 out=6 grade18=True |
| 3 | 3. 仅 18 行第 4 列变化（对照 pin） | PASS | diff_count=18 match18=True bad_other=[] |
| 4 | 4. 严格前缀 18/18 且其它列同 delta 且追加段逐字 | PASS | prefix=18/18 others=18/18 append_exact=18/18 |
| 5 | 5. 六个实测数（自算，非照抄） | PASS | {"N_pre_A": 2, "N_pre_B": 0, "N_A_pre": 356, "N_A_post": 372, "N_B_pre": 188, "N_B_post": 206} |
| 6 | 6. §12.6/§12.4 命中计数 | PASS | append §12.6=18 §12.4=0; post §12.6=115 §12.4=0; pre §12.6=97 §12.4=0 |
| 7 | 7. PANEL.md 还原性（删 M92 块） | PASS | M92_at_0based=259 M91_at=[252] after_M91=True rebuilt sha=607BB21F bytes=175996 |
| 8 | 8. 达标未翻转 (strict_panel.py) | PASS | 名义=[S15,S16,S17] 严格=[S17] (期望 S15,S16,S17 / S17); rc=0 |
| 9 | 9. 行尾不混用、LF/endsLF 一致 | PASS | cov CRLF=0 LF=18498 endsLF=False; pan CRLF=0 LF=652 endsLF=True |

## 4. 六个实测数（自算，非照抄）

- N_pre_A（18 行改前第 4 列含 `④`）= **2**（`00749F30` 2 个 / `0074BA30` 1 个）
- N_pre_B（18 行改前含 `④ 活表槽位见证`）= **0**
- N_A_pre / N_A_post（全表 `[已证]` 且含 `④`）= **356 → 372**（净增 16 = 18 − 2，口径 A 不增的 2 行即同格并存旧 ④）
- N_B_pre / N_B_post（全表 `[已证]` 且含 `④ 活表槽位见证`）= **188 → 206**（净增 18）

## 5. 达标集合（strict_panel.py 口径复算，输出到本目录）

- 名义达标：**S15,S16,S17**
- 严格达标：**S17**
- 输出：`strict_panel_out.txt` / `strict_panel.json` / `strict_panel.tsv`（若脚本产出）/ `strict_panel_b4.py`

## 6. M92 披露

- 插入点：PANEL.md 第 260 行（M91 块 253–259 之后，M77 并表实算说明之前），7 行引用块。
- 三条 NIT 已照实写入：① `0071F8C0` 见证头 `::ctor`（非 `::slotN`，下游按 `::slot` 解析会漏 1 行）；② 本期 10 行本 entry 体内也装同表（`scan_F1_audit.tsv` 的 `n_install_inside_body` 系统性低估为 4）；③ 同格并存旧 ④ 2 行（`00749F30` / `0074BA30`）。
- 既有内容零删除零改字：删 M92 块后重建 sha256 == 改前 sha256（验证 #7 PASS）。

