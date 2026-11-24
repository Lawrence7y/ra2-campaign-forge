D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe	sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R28-R12-REPAIR · 报告

## 范围、钉死与边界

- 实际镜像：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`；sha256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，与期望 `73201CC0…F67476` 一致。
- 纯静态只读；未建进程、未调试、未启动 gamemd；未修改 `R17_R12_VT_OFFSET` 下任何文件；产物只写 `R17_R28_R12_REPAIR`。
- 数据扫描：`.rdata` raw 200,704 B、`.data` raw 442,368 B，共 643,072 B；形态计数扫描 `.text` raw 4,063,232 B/类。反汇编只在可信入口到首个解码 ret 的界内进行。
- 可信入口：RTTI 链枚举 1,214 张 vtable、14,044 个槽值（唯一 6692），9 个已知 ctor（含 `0x5A6510`），再加严格解码确认的 E8 直接调用目标/padding 起点/ret 边界起点；总计 19435 个入口锚点。
- 入口判定**未使用**按字节扫 `C3`/`C2`。host = 能严格线性解码到 site 且首个解码 ret 在 site 之后的**最早**可信入口；fn_end = 该 ret 的 `address+size`（不含填充）。
- 时限说明：本轮实际执行超过卡定 8 分钟预算；数值仍按上述只读静态证据给出，未以猜测补洞。

## Q1 · 缺陷规模

- 354 行全部重新归因；未解出 3 行。
- host 改变：**129** 行；fn_end 改变：**125** 行；position_assert 翻转：**5** 行。
- 反例已复核：`0x5A6860` 旧 `host=0x5A6810/fn_end=0x5A6920`，新 `host=0x5A6510/fn_end=0x5A691C`，与卡面实测一致。

| class | 行数 | host 变 | fn_end 变 | assert 翻转 |
|---|---:|---:|---:|---:|
| call | 267 | 84 | 76 | 1 |
| mov | 70 | 35 | 39 | 3 |
| stack_ff5424 | 9 | 4 | 4 | 0 |
| other_cmp | 1 | 1 | 1 | 0 |
| other_test_imm | 7 | 5 | 5 | 1 |

## Q2 · verdict 受影响

- `base_source` 为空或未解析：**43** 行。
- `verdict = NON_TARGET(base from stack)`：**64** 行。
- 其中在新 host 下重算 `base_source` 后显示对象/寄存器传递、应改判的：**19** 行（含已知反例 `0x5A6860`）。
- 误判同类 site：0x457597, 0x467B8E, 0x4B25B1, 0x4D3A8C, 0x4D3E11, 0x4D3EAC, 0x521019, 0x5229A2, 0x5A6860, 0x64D52F, 0x65E578, 0x6A1C02, 0x739428, 0x739565, 0x7395B4, 0x739670, 0x739AA1, 0x73AE7E, 0x743F36。
- 判据：若 base 寄存器由对象指针/对象成员/其它寄存器装入（如 `mov edx, dword ptr [ebp]`、`mov eax, esi`），不再因源码文本含 ebp/esp 就判 stack；base_reg 真为 esp/ebp 才保留 stack 判名。

## Q3 · 可替换修正表

- `host_fix.tsv` 含全部 354 行：site / class / disp / 旧host / 新host / 旧fn_end / 新fn_end / 旧verdict / 建议verdict / 变更原因 / 重算base_source。
- `hits.tsv` 未改；勘误只以修正表形式落盘。

## Q4 · 形态命中数是否改变

**不改变。** 证据不是断言：`recount_shapes()` 在 `.text` raw 上按前缀+disp32 重新扫出下列数，与 R12 报告表逐项相等；原 `work.py` 的 `scan_disp`/`scan_ff5424` 先产出计数与 site，之后才调用 `analyze()` 附加 host/fn_end/verdict，host 列从未进入计数路径。

| 形态 | R12 报告 | 本次重扫 |
|---|---:|---:|
| call@0x124 | 181 | 181 |
| call@0x1AC | 86 | 86 |
| jmp@0x124 | 0 | 0 |
| jmp@0x1AC | 0 | 0 |
| mov@0x124 | 55 | 55 |
| mov@0x1AC | 15 | 15 |
| other_cmp@0x124 | 1 | 1 |
| other_cmp@0x1AC | 0 | 0 |
| other_cmp_imm@0x124 | 0 | 0 |
| other_cmp_imm@0x1AC | 0 | 0 |
| other_test@0x124 | 0 | 0 |
| other_test@0x1AC | 0 | 0 |
| other_test_imm@0x124 | 7 | 7 |
| other_test_imm@0x1AC | 0 | 0 |
| stack_ff5424 | 9 | 9 |

- 用户点名的 267 / 86 / 70 / 9 / 7 / 1 分别对应：call 合计 267（0x124=181、0x1AC=86）、0x1AC call=86、mov 合计 70（55+15）、stack_ff5424=9、other_test_imm@0x124=7、other_cmp@0x124=1；全部逐项重扫一致。

## 产物

- `REPORT.md`：本报告
- `host_fix.tsv`：354 行逐行修正表
- `stats.tsv`：Q1/Q2/Q4 统计
- `work.py`：可复跑脚本
- `entries.json`、`interim.json`：入口集与中间结果（辅助证据）
