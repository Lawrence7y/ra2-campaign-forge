# S02-K2 · DISAGREE.md

| # | 议题 | 派卡/面板说 | 盘上实测 | 处置 |
|---|---|---|---|---|
| D1 | **S02 `proved` 数** | 卡面 §2 / HANDOFF：「`[已证]` **30**（9.17%）」；PANEL.md S02 行：`proved_n=31`（9.48%） | `coverage.tsv` ∩ `function_atlas.tsv` 的 S02 行中 grade=`[已证]` **31** 行（9.48%）；PANEL 与盘值一致 | 采盘上 **31**，不凑卡面 30。STATUS_BOARD「派卡口径警告」：Lead 数字可能有误，执行员实测优先。已记 `EVIDENCE/T1_counts.txt` |
| D2 | 卡面「327 函数里很多是 CRT，批量定名最大收益」 | 预期大量可名 | YRpp 全部 31 个 CRT 地址名**已全部在 coverage 具名**；靶内仅剩 1 个可加名（`_nh_malloc`，且为 `[静态推断]`），另 3 个 CRT 函数被错归 S19/S06 | 如实报告：CRT 具名符号集在 S02 靶内已被 YRpp 用尽；不以形态匹配造名（基线 `EVIDENCE/BASELINE.txt`） |
| D3 | 卡面「IAT 可把调用 CRT API 的 thunk 对上」 | IAT 作为命名通道 | IAT 无 MSVCRT.dll（17 个 DLL 全是 Win32/DDraw/D Sound/bink/xyr）；CRT 为**静态链接**，函数体自带实现（malloc 读 `[0xB782C4]` 堆句柄）⇒ IAT 不能名这些 CRT 桩 | IAT 仍用于 T4（except.txt 写入链：CreateFileA/WriteFile/SetUnhandledExceptionFilter 全经 IAT 核实），但**不能用于 T2 命名** |
| D4 | 卡面「`0x7C8E17` operator new 反查同类地址簇」 | 反查可得 CRT 簇 | 反查证实 `0x7C8E17`/`0x7C9430` 同调 `0x7C9442`（`_nh_malloc`）⇒ 得 1 名；但 `0x7C8E25`/`0x7C8B48` 是 bsearch/qsort（YRpp），不靠簇推 | 用 YRpp 显式地址而非"地址簇猜测"定名，符合"不许按看起来像就命名" |
| D5 | S02 靶内含非 CRT 错归（音频线程等） | S02 = CRT/内存池/异常守卫 | `0x407780`/`0x4095B0`/`0x53E6B0`/`0x53E4F0`/`0x53E550` 等属音频/UI/输入，仅因"region guess"归 S02（`EVIDENCE/T2_inventory.txt` 地址带 + 文本证据 `EVIDENCE/T2_textref.json` 未落盘但脚本可复跑） | 不在本卡改写（会连锁 S19/S06/S09 计数）；列 U5 建议后续卡处理。delta 仅含 CRT 相关行 |
| D6 | except.txt 写入「函数」定位 | 待找 | 写入函数 `0x4C8FE0` 在 atlas gap（前序 `0x4C85E0+2556=0x4C8FD4` + 4 nop），非 atlas 收录；但四项入口证据满足（`0x6BE06F jmp` 直指） | 按纪律 2 判真入口并写明依据，不因"不在 atlas"否认其存在 |
| D7 | `[0xB782C4]` 写者 | T3 期望双通道 | 全 `.text` 0 写点；malloc 只读 | 不虚报写者；记 U3，该全局语义仅 `[静态推断]` |
| D8 | D-35 / ②-a 补丁 | 待裁决 | 本卡严格遵守 (A)：未复制、未改 `ra2youli\`、未注入、未写内存 | 无分歧，声明合规 |
