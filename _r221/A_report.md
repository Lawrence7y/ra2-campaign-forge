# R221-A 实测报告（exec hy4 / 单次脚本运行）

环境：`_r185.pe185` 只读映射 `ra2bench/gamemd.exe`；capstone `CS_MODE_32`, `detail=False`, `skipdata=True`；.text 逐字节 resync。所有数字由脚本实跑产生。

## 1. 数据区边界与衔接

| 名称 | VA | 文件偏移 | 长度 | 段 | sha256[:16] | 首 16 字节 | 尾 16 字节 |
|---|---|---|---|---|---|---|---|
| idx_8758c4 | 0x8758c4 | 4675780 | 16 | .data | 12b9d0e9faa9d946 | ffffffffffffffff0200040006000800 | ffffffffffffffff0200040006000800 |
| step_8758e4 | 0x8758e4 | 4675812 | 178 | .data | 98d29d10eef87b44 | 0700080009000a000b000c000d000e00 | b24144487e4f71572f60ce696274ff7f |
| idx_copy_8758d4 | 0x8758d4 | 4675796 | 16 | .data | 12b9d0e9faa9d946 | ffffffffffffffff0200040006000800 | ffffffffffffffff0200040006000800 |
| D_8759b4 | 0x8759b4 | 4676020 | 5696 | .data | 7464a774b456bed4 | 00000000010000000300000004000000 | 0270ffff0350ffff0330ffff0410ffff |
| S_copy_876ff4 | 0x876ff4 | 4681716 | 3360 | .data | 0b2a16a8e804da4b | 000000000000000040008000c0000001 | 1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e |
| D_879b30 | 0x879b30 | 4692784 | 5696 | .data | 7464a774b456bed4 | 00000000010000000300000004000000 | 0270ffff0350ffff0330ffff0410ffff |
| S_87b170 | 0x87b170 | 4698480 | 3360 | .data | 0b2a16a8e804da4b | 000000000000000040008000c0000001 | 1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e |
| jitterA_87bc90 | 0x87bc90 | 4701328 | 256 | .data | c01fcb18eda67fd7 | 00020406080a0c0e10121416181a1c1e | 00020406080a0c0e10121416181a1c1e |
| jitterB_87bd90 | 0x87bd90 | 4701584 | 256 | .data | 8f7cfa780a785d7c | 00000000000000000000000000000000 | 1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e |

| 零间隙断言 | 左 | 右 | 结果 |
|---|---|---|---|
| 0x8759b4+5696==0x876ff4 | 0x876ff4 | 0x876ff4 | True |
| 0x876ff4+3360==0x877d14 | 0x877d14 | 0x877d14 | True |
| 0x879b30+5696==0x87b170 | 0x87b170 | 0x87b170 | True |
| 0x87b170+3360==0x87be90 | 0x87be90 | 0x87be90 | True |
| 0x8758e4+178==0x875996 | 0x875996 | 0x875996 | True |

- 0x877d14 起 16 字节：`00000000000000000000000000000000`
- 0x87be90 起 16 字节：`94957f00000000002e3f415674797065`
- 结论：5/5 条零间隙断言成立；九段区间均落在 mapped 文件范围内。

## 2. 重复副本同一性与全文件出现位置

| 配对 | VA A / VA B | 长度 | 逐字节相同 | sha256[:16] A | sha256[:16] B | 文件偏移 → VA（全部） |
|---|---|---|---|---|---|---|
| D_pair_5696 | 0x8759b4 / 0x879b30 | 5696 | True | 7464a774b456bed4 | 7464a774b456bed4 | 4676020→0x8759b4; 4692784→0x879b30 |
| S_pair_3360 | 0x876ff4 / 0x87b170 | 3360 | True | 0b2a16a8e804da4b | 0b2a16a8e804da4b | 4681716→0x876ff4; 4698480→0x87b170 |
| idx_pair_16 | 0x8758c4 / 0x8758d4 | 16 | True | 12b9d0e9faa9d946 | 12b9d0e9faa9d946 | 4675780→0x8758c4; 4675796→0x8758d4 |

- 结论：3/3 对逐字节完全相同；全文件搜索命中数分别为 2, 2, 2。

## 3. 索引表

| 实测 8 个 int16 | 期望 | 一致 |
|---|---|---|
| [-1, -1, -1, -1, 2, 4, 6, 8] | [-1, -1, -1, -1, 2, 4, 6, 8] | True |

- 结论：索引表等于(-1,-1,-1,-1,2,4,6,8)。

## 4. 步长表

| 前 8 项 | 末 3 项 | 标准表命中 | 严格单调递增 | 首个不匹配 |
|---|---|---|---|---|
| [7, 8, 9, 10, 11, 12, 13, 14] | [27086, 29794, 32767] | 89/89 | True | None |

- 结论：实测步长表与脚本生成的 89 项标准 IMA 表命中 89/89。

## 5. 差分表生成律 D

| 基址 | 命中 | 总数 | 前 6 个不匹配 (m,n,实测,期望) |
|---|---|---|---|
| 0x879b30 | 1424 | 1424 | [] |

- 结论：律 D 在 0x879b30 命中 1424/1424。

## 6. 状态表生成律 S

| 基址 | 命中 | 总数 | min | max | 全为 32 倍数 | 前 6 个不匹配 |
|---|---|---|---|---|---|---|
| 0x87b170 | 1424 | 1424 | 0 | 2816 | True | [] |

| 附加运行 | 命中 | 总数 |
|---|---|---|
| 律 S @ 0x876ff4 | 1424 | 1424 |
| 律 S @ 0x8759b4 | 7 | 1424 |
| 律 D @ 0x8759b4 | 1424 | 1424 |

- 结论：律 S 在 0x87b170 命中 1424/1424，范围 0..2816，32 倍数=True；副本 0x876ff4 命中 1424/1424。

## 7. 反控

| 控制 | 改动 | 命中 | 总数 |
|---|---|---|---|
| K1_base_plus2 | 律 S 基址 0x87b170→0x87b172 | 564 | 1424 |
| K2_rec8_count712 | 律 S 每记录 8 字，m=0..88（712 项） | 12 | 712 |
| K3_upper87 | 律 S clamp 上界 88→87 | 1376 | 1424 |
| K4_sign_thr7 | 律 D 负号判据 n>=8→n>=7 | 1335 | 1424 |
| K5_mag_mask15 | 律 D 幅度 n&7→n&15 | 1424 | 1424 |

- 结论：五个反控命中数分别为 564, 12, 1376, 1335, 1424，均未达到主律命中数。

## 8. 引用计数（.text 逐字节 resync）

扫描：.text，文件区 [4096, 4067328)，VA 起点 0x401000，迭代 1394186 次，耗时 75.81 s。

| 目标 | 指令数 | 最小 VA | 最大 VA | 操作数文本样例 | 前 6 个位点 |
|---|---|---|---|---|---|
| 0x8758c4 | 3 | 0x7c639b | 0x7c65be | ax, word ptr [ecx + 0x8758c4] | 0x7c639b mov ax, word ptr [ecx + 0x8758c4]; 0x7c649f mov ax, word ptr [ecx + 0x8758c4]; 0x7c65be mov ax, word ptr [ecx + 0x8758c4] |
| 0x8758d4 | 0 | None | None | None |  |
| 0x8758e4 | 3 | 0x7c63cd | 0x7c65f0 | ax, word ptr [ecx + 0x8758e4] | 0x7c63cd mov ax, word ptr [ecx + 0x8758e4]; 0x7c64d1 mov ax, word ptr [ecx + 0x8758e4]; 0x7c65f0 mov ax, word ptr [ecx + 0x8758e4] |
| 0x8759b4 | 8 | 0x7c6808 | 0x7c6952 | eax, dword ptr [edx*2 + 0x8759b4] | 0x7c6808 add eax, dword ptr [edx*2 + 0x8759b4]; 0x7c6837 add eax, dword ptr [edx*2 + 0x8759b4]; 0x7c6868 add eax, dword ptr [edx*2 + 0x8759b4]; 0x7c6898 add eax, dword ptr [edx*2 + 0x8759b4]; 0x7c68c6 add eax, dword ptr [edx*2 + 0x8759b4]; 0x7c68f6 add eax, dword ptr [edx*2 + 0x8759b4] |
| 0x876ff4 | 8 | 0x7c680f | 0x7c6959 | dx, word ptr [edx + 0x876ff4] | 0x7c680f mov dx, word ptr [edx + 0x876ff4]; 0x7c683e mov dx, word ptr [edx + 0x876ff4]; 0x7c686f mov dx, word ptr [edx + 0x876ff4]; 0x7c689f mov dx, word ptr [edx + 0x876ff4]; 0x7c68cd mov dx, word ptr [edx + 0x876ff4]; 0x7c68fd mov dx, word ptr [edx + 0x876ff4] |
| 0x879b30 | 24 | 0x7c7428 | 0x7c7d0a | eax, dword ptr [edx*2 + 0x879b30] | 0x7c7428 add eax, dword ptr [edx*2 + 0x879b30]; 0x7c7457 add eax, dword ptr [edx*2 + 0x879b30]; 0x7c7488 add eax, dword ptr [edx*2 + 0x879b30]; 0x7c74b8 add eax, dword ptr [edx*2 + 0x879b30]; 0x7c74e6 add eax, dword ptr [edx*2 + 0x879b30]; 0x7c7516 add eax, dword ptr [edx*2 + 0x879b30] |
| 0x87b170 | 24 | 0x7c742f | 0x7c7d11 | dx, word ptr [edx + 0x87b170] | 0x7c742f mov dx, word ptr [edx + 0x87b170]; 0x7c745e mov dx, word ptr [edx + 0x87b170]; 0x7c748f mov dx, word ptr [edx + 0x87b170]; 0x7c74bf mov dx, word ptr [edx + 0x87b170]; 0x7c74ed mov dx, word ptr [edx + 0x87b170]; 0x7c751d mov dx, word ptr [edx + 0x87b170] |
| 0x87bc90 | 21 | 0x7c747b | 0x7c7eca | dl, byte ptr [ebx + 0x87bc90] | 0x7c747b or dl, byte ptr [ebx + 0x87bc90]; 0x7c74dc or dl, byte ptr [ebx + 0x87bc90]; 0x7c753a or dl, byte ptr [ebx + 0x87bc90]; 0x7c75a7 or dl, byte ptr [ebx + 0x87bc90]; 0x7c76b8 or dl, byte ptr [ebx + 0x87bc90]; 0x7c76ed or dl, byte ptr [ebx + 0x87bc90] |
| 0x87bd90 | 24 | 0x7c744c | 0x7c7ee4 | dl, byte ptr [ebx + 0x87bd90] | 0x7c744c or dl, byte ptr [ebx + 0x87bd90]; 0x7c74ac or dl, byte ptr [ebx + 0x87bd90]; 0x7c750a or dl, byte ptr [ebx + 0x87bd90]; 0x7c7568 or dl, byte ptr [ebx + 0x87bd90]; 0x7c76a0 or dl, byte ptr [ebx + 0x87bd90]; 0x7c76d2 or dl, byte ptr [ebx + 0x87bd90] |

- 结论：九个目标中引用数分别为 0x8758c4=3, 0x8758d4=0, 0x8758e4=3, 0x8759b4=8, 0x876ff4=8, 0x879b30=24, 0x87b170=24, 0x87bc90=21, 0x87bd90=24；仅统计操作数文本含目标十六进制的指令。

## 9. 抖动表属性

| 属性 | 值 |
|---|---|
| A_rc_eq_2c | True |
| B_rc_eq_2r | True |
| B_eq_transpose_A | True |
| A_eq_B | False |
| sha256[:16] A | c01fcb18eda67fd7 |
| sha256[:16] B | 8f7cfa780a785d7c |

- 结论：A[r][c]=2c=True，B[r][c]=2r=True，B=A^T=True，A=B=False。

## 附：跳转表

- 0x7c7758 (8 dword): 0x7c75c1, 0x7c7694, 0x7c76ac, 0x7c76c4, 0x7c76e0, 0x7c76f8, 0x7c771c, 0x7c7740
- 0x7c7778 (4 dword): 0x7c73e2, 0x7c73f8, 0x7c7408, 0x7c7418

## 与卡片期望不一致的项

- 无（所有卡片期望项实测一致）。

## 口径问题

- 0x876ff4/0x87b170 的 3360 B 区间与 0x87bc90/0x87bd90 两张 256 B 抖动表地址重叠；按卡片给定基址独立读取，未去重。
- K2 按“每记录 8 个字、m 走 0..88”解释为 8*89=712 项，不是 1424 项。
- K5 的 n&15 对幅度公式无影响（bit3 不参与 d 的四个分项），故命中数与律 D 相同。
- K1 基址 0x87b172 读 1424 字会跨过 0x87be90 名义表尾 2 字节。
- 第 8 组为逐字节 resync 静态扫描（skipdata=True），数据字节可能被判为指令；只报实测，不判真伪。
- 律 D/S 使用第 4 组实测步长表；标准表由脚本生成并断言 89 项且端点 7/32767。

