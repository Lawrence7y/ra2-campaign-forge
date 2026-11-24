73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-IMG-PIN 报告

- canonical/基准: D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe
- patched/副本: D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\run\gamemd.exe
- 基准 sha256 期望匹配: true
- 副本 sha256 期望前缀 36a87577: true

## 第 1 步 · 钉哈希

| file | size | sha256 |
|---|---:|---|
| canonical | 4825360 | 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476 |
| patched | 4825360 | 36A875775DA89239E370AAF091DBE5D3D3C5F2F8017D9EFA6A15FCDD4801C7F4 |

## 第 2 步 · 全文件字节差异

- 差异字节总数: 73
- 差异区间个数: 9
- PE image base: 0x400000; section table identical between files: true
- VA 由 canonical 的 PE 节表换算；区间按半开 [start,end) 计。

| # | file_off_start | file_off_end | len | VA_start | VA_end | bytes_in_canonical | bytes_in_patched |
|---:|---|---|---:|---|---|---|---|
| 1 | 0xA8B76 | 0xA8B79 | 3 | 0x4A8B76 | 0x4A8B79 | B6 BB 27 | 07 6C 33 |
| 2 | 0x240428 | 0x24042B | 3 | 0x640428 | 0x64042B | 04 43 0E | 55 F3 19 |
| 3 | 0x2D059C | 0x2D059F | 3 | 0x6D059C | 0x6D059F | 90 41 05 | E1 F1 10 |
| 4 | 0x2D0635 | 0x2D0638 | 3 | 0x6D0635 | 0x6D0638 | F7 40 05 | 48 F1 10 |
| 5 | 0x2D0941 | 0x2D0944 | 3 | 0x6D0941 | 0x6D0944 | EB 3D 05 | 3C EE 10 |
| 6 | 0x2D09FB | 0x2D09FE | 3 | 0x6D09FB | 0x6D09FE | 31 3D 05 | 82 ED 10 |
| 7 | 0x2D1294 | 0x2D1297 | 3 | 0x6D1294 | 0x6D1297 | 98 34 05 | E9 E4 10 |
| 8 | 0x2D1633 | 0x2D1636 | 3 | 0x6D1633 | 0x6D1636 | F9 30 05 | 4A E1 10 |
| 9 | 0x3DF781 | 0x3DF7B2 | 49 | 0x7DF781 | 0x7DF7B2 | CC CC CC CC CC CC CC CC CC CC CC CC CC CC CC CC ... CC CC CC CC CC CC CC CC CC CC CC CC CC CC CC CC | 50 8B 44 24 04 A3 00 50 9F 00 FF 05 04 50 9F 00 ... 88 00 85 C0 74 05 E9 1A E1 EE FF E9 26 E1 EE FF |

完整机器可读差异表见 diff_ranges.tsv；长度 >32 的区间按首 16 字节 ... 末 16 字节显示。

## 第 3 步 · 指定区间同字节检查

指定地址按 VA 处理；单点 8 字节邻域按 VA 的 [addr, addr+8) 计算；比较前经 PE 节表换算为文件偏移。

| kind | name | VA_start | VA_end | file_start | file_end | len | diff_bytes | identical |
|---|---|---|---|---|---|---:|---:|---|
| range | 0x6F2B40-0x6F3267 | 0x6F2B40 | 0x6F3267 | 0x2F2B40 | 0x2F3267 | 1831 | 0 | same |
| range | 0x6F4300-0x6F44F0 | 0x6F4300 | 0x6F44F0 | 0x2F4300 | 0x2F44F0 | 496 | 0 | same |
| range | 0x43B680-0x43B740 | 0x43B680 | 0x43B740 | 0x3B680 | 0x3B740 | 192 | 0 | same |
| range | 0x43B740-0x43BCDE | 0x43B740 | 0x43BCDE | 0x3B740 | 0x3BCDE | 1438 | 0 | same |
| range | 0x43BCF0-0x43C0D0 | 0x43BCF0 | 0x43C0D0 | 0x3BCF0 | 0x3C0D0 | 992 | 0 | same |
| single8 | 0x6F322F | 0x6F322F | 0x6F3237 | 0x2F322F | 0x2F3237 | 8 | 0 | same |
| single8 | 0x6F3237 | 0x6F3237 | 0x6F323F | 0x2F3237 | 0x2F323F | 8 | 0 | same |
| single8 | 0x43B74B | 0x43B74B | 0x43B753 | 0x3B74B | 0x3B753 | 8 | 0 | same |
| single8 | 0x43B688 | 0x43B688 | 0x43B690 | 0x3B688 | 0x3B690 | 8 | 0 | same |
| single8 | 0x6F2B46 | 0x6F2B46 | 0x6F2B4E | 0x2F2B46 | 0x2F2B4E | 8 | 0 | same |
| single8 | 0x6F430B | 0x6F430B | 0x6F4313 | 0x2F430B | 0x2F4313 | 8 | 0 | same |
| single8 | 0x65A7E8 | 0x65A7E8 | 0x65A7F0 | 0x25A7E8 | 0x25A7F0 | 8 | 0 | same |
| single8 | 0x65A753 | 0x65A753 | 0x65A75B | 0x25A753 | 0x25A75B | 8 | 0 | same |

## 结论

能：本卡指定的关心 VA 区间与单点 8 字节邻域在两文件中均为同字节；已发现的差异均不在指定关心区间内。
