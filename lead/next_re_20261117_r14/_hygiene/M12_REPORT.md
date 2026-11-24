# M12 合并报告（COVERAGE 唯一写者；快照 _hygiene/M12_before/）
- 时点：2026-11-18 06:12–06:15 +08:00；只写 COVERAGE/ 与 _hygiene/，未 git commit。
- 快照 SHA-256（详见 _hygiene/M12_before/SHA256SUMS.txt）：coverage 314E19BC…349FA0；PANEL 8FBDE05E…28FB；CONFLICTS 66CD43DB…60F6；PENDING 59503214…11B34。
## 并入 / 排除
- 并入 S10_K12（VERDICT=PASS）4 行：0051D6F0、0051DAF0、0051B1F0、00522340；[静态推断]→[已证]，同步真名/语义/evidence_path。
- 排除 S10_K9 5 行：K12 是返工版且只交 4 行，0051BAB0 已退 [静态推断]；按 K9 原样并入会错误把它拉回 [已证]。盘上 0051BAB0 仍 [静态推断]。
## coverage.tsv 第 5 列 grade 分布
| 项 | before | after | Δ |
|---|---:|---:|---:|
| 数据行 | 18,431 | 18,431 | 0 |
| [已证] | 1,364 | 1,368 | +4 |
| [静态推断] | 6,036 | 6,032 | −4 |
| [未证] | 11,031 | 11,031 | 0 |
## S10 现场复算（atlas W130 ∩ coverage，entry 大写）
- S10 表内 528 行；atlas_n 526；atlas 外 2 行：0041B860、005B3740。
- atlas 内 grade：已证 113 / 静态推断 400 / 未证 13；proved 113/526 = 21.48%。
- named_L 513/526 = 97.53%；named_S(R14) 513/526 = 97.53%；strict 实测 77/526 = 14.64%（并表前 73/526）。
- strict 口径修正：PANEL 原写 71 是改名前旧截面；S10_K12 审计与本次复算均得并表前 73。四行从 slot 名改真名后 strict +4 ⇒ 77；PANEL 已按现场值刷新并注明时点。
## 登记与面板
- CONFLICTS.tsv 新增 0（均为 grade 提级，非同 grade 异名/异属）；文件未变，仍 465 数据行。
- PENDING_CORRECTIONS.tsv 新增 4（四行 grade 提级，附记 name/semantics 同步来源）：235→239。
- PANEL.md 保留 named_pct_S 双列、S13 240/148 双分母、S22 不参与排名、三分母 A/B/C 不变。
- after SHA-256：coverage 915B04F7…EA5253；PANEL 2E38C371…0BB26B2D39；PENDING 88CF3B90…180A。
