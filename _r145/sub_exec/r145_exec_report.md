# R145 EXEC 报告（盲测，一次性取证）

1. **Q1**：正位移 `[eax + 8]` 归一化后为 `dword ptr [eax+0x8],0x401000`，RE_STORE **match=True**；负位移 `[eax - 8]` 归一化后为 `dword ptr [eax - 8],0x401000`，RE_STORE **match=False**。根因：norm 第99行字符类 `[+,*]` 不含 `-`（minus 两侧空格保留），第100行 `([+-])(\d+)` 要求符号紧跟数字故 `- 8` 不转 `-0x8`，RE_STORE 第112行要求 `]` 前紧邻 base/disp，故负位移整类被丢弃。
2. **Q2**：完整解析器站点 5729、覆盖虚表 1212；RE_STORE 严格口径站点 5724、覆盖虚表 1211；差值 站点 5 / 虚表 1。
3. **Q3**：VTS 总数 1218；完整解析器残余 6 张：0x7f7a1c(.rdata), 0x7f7aec(.rdata), 0x877000(.data), 0x877010(.data), 0x87b17c(.data), 0x87b18c(.data)；其中 .rdata：0x7f7a1c, 0x7f7aec。
4. **Q4**：0x7e6060 不在残余。0x4A8600 起 0x80 字节反汇编见 JSON；写入命中 1 处，示例 {'va': '0x4a8660', 'bytes': 'c740f860607e00', 'mn': 'mov', 'op': 'dword ptr [eax - 8], 0x7e6060', 'op_norm': 'dword ptr [eax - 8],0x7e6060'}；解析出的 mem={'base': 'eax', 'index': None, 'scale': None, 'disp': -8}；相邻步进指令 [{'va': '0x4a8667', 'bytes': '83c018', 'mn': 'add', 'op': 'eax, 0x18', 'op_norm': 'eax,0x18'}, {'va': '0x4a866a', 'bytes': '4a', 'mn': 'dec', 'op': 'edx', 'op_norm': 'edx'}]。

## 断言清单
- [PASS] Q1_positive_disp_accepted_by_RE_STORE — dword ptr [eax+0x8],0x401000
- [PASS] Q1_negative_disp_DROPPED_by_RE_STORE (bug control) — dword ptr [eax - 8],0x401000
- [PASS] full_parser_pos — dword ptr [eax+0x8] -> {'base': 'eax', 'index': None, 'scale': None, 'disp': 8}
- [PASS] full_parser_neg — dword ptr [eax - 8] -> {'base': 'eax', 'index': None, 'scale': None, 'disp': -8}
- [PASS] full_parser_sib — dword ptr [eax+ecx*4+0x10] -> {'base': 'eax', 'index': 'ecx', 'scale': 4, 'disp': 16}
- [PASS] neg_ctrl_reject_nonmem_operand — eax,ebx
- [PASS] VTS_count_equals_R144_1218 — 1218
- [PASS] RE_vt_set_subset_of_full_vt_set — RE=1211 full=1212
- [PASS] full_site_count_ge_RE_site_count — full=5729 RE=5724
- [PASS] Q4_write_to_target_found — near=1 global=1

耗时 39.79 s
