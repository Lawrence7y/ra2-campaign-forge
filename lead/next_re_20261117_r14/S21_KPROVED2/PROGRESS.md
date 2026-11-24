升了几行/8：**0/8**（证不出来，如实少交；无一行四环齐全）



- 卡号 S21-KPROVED2；开工 2026-11-18T18:18:55+08:00；写域仅本目录；目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201cc0…f67476`（实测）。
- 已读 R14_COMMON §8.6 六条 + CARD.md；system python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；未建 venv、未 pip install；无 REA MCP 可用，按派卡指定离线静态法。
- ⑨ 实测：coverage 原始 S21 = **132**（28/94/10）；atlas∩coverage = **129**（[已证]28/[静态推断]91/[未证]10）——与卡面一致。
- 扫描（VirtualSize 口径）：`.text` 4,060,045 B，**1,392,592** 指令 / **68,253** E8@边界，与基准逐字相同。⑲：`op.index` 不存在（445,633 mem 操作数），`op.mem.index` 无索引返 **0**（423,974），用独立非 skipdata Cs 实例读 detail 避开 SKIPDATA 异常。

## 关键发现（逐行集合级硬事实，见 EVIDENCE/ring_intersection.json）
- 91 条 [静态推断] 中，**64 有 RTTI 链（②有）但 0 个 E8 direct 站点（④缺）**；**23 有外部 direct call（④有）但 0 个 RTTI VA 出现（②缺）**。两集合交集 = **0 行**。② 的另一通道 YRpp `CALL/JMP_THIS(0x...)` 对 91 行命中 **0**（EVIDENCE/yrpp_bindings.json）。
- ④ 的构造器活 vtable 备选已核：写 vt 且 `vt[slot]==entry` 的行（如 0046D000 / 0046D090 / 容器 slot0 / WDT slot0）全部 **n_direct=0**；0046D090 尾部 `call 0x7C8B3D`（operator delete）且形态是 `CampaignClass::slot8` 的析构路径，不算活构造器见证（EVIDENCE/ctor_live_vtable_check.json、ctor_candidate_bodies.txt）。
- ③b 结构最像的 19 行（jmp table / 回边 / 多 cmp / 内存形状 / 错误码）与 ④ 的 23 行重合，但 **②=0**；先前 C3 白名单 2 行（0053AF40/00595740）已由 M33 落盘，本卡不重复。D-41 缺口（无虚表函数 RTTI 物理不可用）在本批是系统性拦截，非个别。

## 随机基线（按卡要求：S21 内随机取 8 行）
- weak（仅④ direct）= **23/129 = 17.83%**，E[8 命中] = **1.43 行**；strong（④+③b 结构）= **19/129 = 14.73%**，E[8] = **1.18 行**；差集 = **4 行**。该 weak/strong 只是**诊断**；由于 ②∩④=∅，两档均无一可升 [已证]（强档仍缺 ②）。

## 逐行增量
- 每完成 2 行落盘：本卡 **0 行达标**，无 delta 数据行。coverage_delta.tsv 只写 8 列表头（`name` 不动原则无行可违）。

## 交付
- `work/candidates.json`（129 行特征）、`work/scan_candidates.py`、`EVIDENCE/ring_intersection.json`、`EVIDENCE/yrpp_bindings.json`（0 命中）、`EVIDENCE/ctor_live_vtable_check.json`、`EVIDENCE/ctor_candidate_bodies.txt`、`EVIDENCE/selected_bodies.txt`、`coverage_delta.tsv`（0 数据行）。
- 结论：**升 0/8**。剩余 S21 proved 仍 28/129（门槛 65，差 37）；需 Lead 先裁 D-41 无虚表类属通道，否则本线静态取证不能闭环。
