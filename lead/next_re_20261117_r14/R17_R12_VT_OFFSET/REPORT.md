D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe
sha256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R12-VT-OFFSET 定偏移虚派发扫描报告

## 1. 范围与尺子

- 镜像: D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe；sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476；size 4825360 B。
- 节区: .text raw 0x1000..0x3E1000，RAWSIZE 0x3E0000 = 4063232 B；VA 0x401000..0x7E1000。每类扫描字节数 4063232 B（全 .text raw，含尾部 raw padding；virtual size 0x3DF38D）。
- 形态: mod=10 disp32；含无 SIB 与 base-only SIB（index=none）；disp 0x124 / 0x1AC。

## 2. 四类命中数表

| 类别 | 0x124 | 0x1AC | 合计 | 扫描字节数/类 |
|---|---:|---:|---:|---:|
| call [reg+disp32] | 181 | 86 | 267 | 4063232 |
| jmp [reg+disp32] | 0 | 0 | 0 | 4063232 |
| mov reg,[reg+disp32] | 55 | 15 | 70 | 4063232 |
| 附带 push/cmp/test 等 | 16 | 0 | 8 | 4063232 |
| 附带 FF 54 24 xx 栈间接 call | - | - | 9 | 4063232 |

细分其他类:
- other_cmp: 0x124=1, 0x1AC=0
- other_cmp_imm: 0x124=0, 0x1AC=0
- other_push: 0x124=0, 0x1AC=0
- other_test: 0x124=0, 0x1AC=0
- other_test_imm: 0x124=7, 0x1AC=0

## 3. 命中判定

逐命中 site / 指令字节 / host / fn_end / 基址 / 位置断言 / 判定见 hits.tsv。
- 0x403CAC stack_ff5424 disp=0x0 bytes=ff542410 call dword ptr [esp + 0x10] host=0x403C50 fn_end=0x403CE0 assert=True base=esp => NON_TARGET(base from stack)
- 0x407CB0 mov disp=0x1AC bytes=8b91ac010000 mov edx, dword ptr [ecx + 0x1ac] host=0x407B60 fn_end=0x407EFB assert=True base=ecx => NO_CALLER_LINK
- 0x407E52 mov disp=0x1AC bytes=8b82ac010000 mov eax, dword ptr [edx + 0x1ac] host=0x407B60 fn_end=0x407EFB assert=True base=edx => NO_CALLER_LINK
- 0x4154ED call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x4154BB fn_end=0x4155D8 assert=True base=eax => NO_CALLER_LINK
- 0x415500 call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x4154BB fn_end=0x4155D8 assert=True base=edx => NO_CALLER_LINK
- 0x415B8F call disp=0x1AC bytes=ff96ac010000 call dword ptr [esi + 0x1ac] host=0x415B10 fn_end=0x415C54 assert=True base=esi => NO_CALLER_LINK
- 0x415D8C call disp=0x1AC bytes=ff90ac010000 call dword ptr [eax + 0x1ac] host=0x415D3A fn_end=0x415EB1 assert=True base=eax => NO_CALLER_LINK
- 0x41719C call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x417195 fn_end=0x4171C8 assert=True base=edx => NO_CALLER_LINK
- 0x4171AF call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x417195 fn_end=0x4171C8 assert=True base=eax => NO_CALLER_LINK
- 0x4171DA call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x4171C8 fn_end=0x4172E4 assert=True base=edx => NO_CALLER_LINK
- 0x4172BD call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x4171C8 fn_end=0x4172E4 assert=True base=edx => NO_CALLER_LINK
- 0x41A0C2 call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x41A059 fn_end=0x41A0F6 assert=True base=edx => NO_CALLER_LINK
- 0x41A0D5 call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x41A059 fn_end=0x41A0F6 assert=True base=eax => NO_CALLER_LINK
- 0x41DA05 call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x41D8F4 fn_end=0x41DA20 assert=True base=eax => NO_CALLER_LINK
- 0x41DABA call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x41DA68 fn_end=0x41DB40 assert=True base=edx => NO_CALLER_LINK
- 0x41DAE6 call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x41DA68 fn_end=0x41DB40 assert=True base=edx => NO_CALLER_LINK
- 0x41DC26 call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x41DBF1 fn_end=0x41DC50 assert=True base=eax => NO_CALLER_LINK
- 0x424495 call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x42446F fn_end=0x42456F assert=True base=eax => NO_CALLER_LINK
- 0x424AD3 call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x424A7F fn_end=0x424B23 assert=True base=edx => NO_CALLER_LINK
- 0x424AE6 call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x424A7F fn_end=0x424B23 assert=True base=eax => NO_CALLER_LINK
- 0x424CEB call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x424CE0 fn_end=0x424F00 assert=True base=eax => NO_CALLER_LINK
- 0x42519D call disp=0x124 bytes=ff9024010000 call dword ptr [eax + 0x124] host=0x425150 fn_end=0x4251F0 assert=True base=eax => NO_CALLER_LINK
- 0x426189 other_test_imm disp=0x124 bytes=f68024010000 test byte ptr [eax + 0x124], 0xe0 host=0x426157 fn_end=0x4261D0 assert=True base=eax => NO_CALLER_LINK
- 0x429F54 call disp=0x1AC bytes=ff92ac010000 call dword ptr [edx + 0x1ac] host=0x429E77 fn_end=0x42A43E assert=True base=edx => NO_CALLER_LINK
- 0x42B5AE call disp=0x1AC bytes=ff90ac010000 call dword ptr [eax + 0x1ac] host=0x42B4F8 fn_end=0x42B703 assert=True base=eax => NO_CALLER_LINK
- 0x42BFB6 call disp=0x1AC bytes=ff92ac010000 call dword ptr [edx + 0x1ac] host=0x42BEA3 fn_end=0x42C15B assert=True base=edx => NO_CALLER_LINK
- 0x42C0BA call disp=0x1AC bytes=ff92ac010000 call dword ptr [edx + 0x1ac] host=0x42BEA3 fn_end=0x42C15B assert=True base=edx => NO_CALLER_LINK
- 0x43F218 call disp=0x1AC bytes=ff96ac010000 call dword ptr [esi + 0x1ac] host=0x43F1E9 fn_end=0x43F5D8 assert=True base=esi => NO_CALLER_LINK
- 0x43F678 call disp=0x1AC bytes=ff96ac010000 call dword ptr [esi + 0x1ac] host=0x43F658 fn_end=0x43F9A6 assert=True base=esi => NO_CALLER_LINK
- 0x43FDEB call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x43FB0C fn_end=0x43FB0F assert=False base=edx => NO_CALLER_LINK
- 0x440372 call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x440138 fn_end=0x4403D4 assert=True base=edx => NO_CALLER_LINK
- 0x4405A5 call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x440580 fn_end=0x440871 assert=True base=edi => NO_CALLER_LINK
- 0x4407A0 call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x440698 fn_end=0x440871 assert=True base=edi => NO_CALLER_LINK
- 0x444445 call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x444391 fn_end=0x444492 assert=True base=edx => NO_CALLER_LINK
- 0x44447A call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x444391 fn_end=0x444492 assert=True base=edx => NO_CALLER_LINK
- 0x44459F call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x444565 fn_end=0x44498E assert=True base=edx => NO_CALLER_LINK
- 0x4445C9 call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x444565 fn_end=0x44498E assert=True base=edx => NO_CALLER_LINK
- 0x44824C call disp=0x124 bytes=ff9224010000 call dword ptr [edx + 0x124] host=0x448160 fn_end=0x448260 assert=True base=edx => NO_CALLER_LINK
- 0x44D9A1 call disp=0x1AC bytes=ff93ac010000 call dword ptr [ebx + 0x1ac] host=0x44D8FC fn_end=0x44DCB9 assert=True base=ebx => NO_CALLER_LINK
- 0x44D9CF call disp=0x1AC bytes=ff93ac010000 call dword ptr [ebx + 0x1ac] host=0x44D8FC fn_end=0x44DCB9 assert=True base=ebx => NO_CALLER_LINK
- 0x44F02D call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44EFB0 fn_end=0x44F04B assert=True base=edi => NO_CALLER_LINK
- 0x44F0A6 call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44F06B fn_end=0x44F0C4 assert=True base=edi => NO_CALLER_LINK
- 0x44F11D call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44F0C4 fn_end=0x44F13B assert=True base=edi => NO_CALLER_LINK
- 0x44F1D8 call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44F195 fn_end=0x44F1F6 assert=True base=edi => NO_CALLER_LINK
- 0x44F22A call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44F1F6 fn_end=0x44F248 assert=True base=edi => NO_CALLER_LINK
- 0x44F281 call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44F248 fn_end=0x44F29F assert=True base=edi => NO_CALLER_LINK
- 0x44F2EA call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44F29F fn_end=0x44F308 assert=True base=edi => NO_CALLER_LINK
- 0x44F399 call disp=0x1AC bytes=ff95ac010000 call dword ptr [ebp + 0x1ac] host=0x44F308 fn_end=0x44F3B7 assert=True base=ebp => NON_TARGET(base from stack)
- 0x44F429 call disp=0x1AC bytes=ff95ac010000 call dword ptr [ebp + 0x1ac] host=0x44F3B7 fn_end=0x44F5C0 assert=True base=ebp => NON_TARGET(base from stack)
- 0x44F481 call disp=0x1AC bytes=ff97ac010000 call dword ptr [edi + 0x1ac] host=0x44F3B7 fn_end=0x44F5C0 assert=True base=edi => NO_CALLER_LINK
- 其余 304 条见 hits.tsv

## 4. 正控与反控

- 正控: 同一扫描器在全 .text 找到 7023 条任意 disp32 的 call [reg+disp32]；取样如下。确知依据: capstone 解码为 call，ModRM.mod=10、reg=2，host/fn_end 字节边界锚定。
- POSCTRL | fixed-call-1 | 0x402929 | ff960c010000 | call dword ptr [esi + 0x10c] | 0x402900 | 0x402940 | esi | True | capstone decodes call [reg+disp32]; ModRM mod=10 reg=2; boundary anchored | PASS
- POSCTRL | fixed-call-2 | 0x409A69 | ff915c010000 | call dword ptr [ecx + 0x15c] | 0x4099D3 | 0x409C40 | ecx | True | capstone decodes call [reg+disp32]; ModRM mod=10 reg=2; boundary anchored | PASS
- 反控: 同一尺子对合成缓冲区对齐 0/1、节首、节尾恰好容纳、末字节截断、起点前排除、双 disp 同时命中均按预期；.text 首尾 64 B 窗口亦已扫描，详见 controls.tsv。
- ANTI | align_offset_0 | buf[0:22] |  |  |  |  |  |  | expected=1 actual=1 offsets=['0x8'] | PASS
- ANTI | align_offset_1 | buf[0:15] |  |  |  |  |  |  | expected=1 actual=1 offsets=['0x1'] | PASS
- ANTI | section_start | buf[0:14] |  |  |  |  |  |  | expected=1 actual=1 offsets=['0x0'] | PASS
- ANTI | section_end_exact | buf[0:14] |  |  |  |  |  |  | expected=1 actual=1 offsets=['0x8'] | PASS
- ANTI | truncated_last_byte | buf[0:13] |  |  |  |  |  |  | expected=0 actual=0 offsets=[] | PASS
- ANTI | before_start_excluded | buf[6:14] |  |  |  |  |  |  | expected=0 actual=0 offsets=[] | PASS
- ANTI | two_disps | buf[0:17] |  |  |  |  |  |  | expected=2 actual=2 offsets=['0x0', '0x7'] | PASS
- ANTI | text_head_64B | 0x401000 |  |  |  |  |  |  | scanned=64 hits=0 | PASS
- ANTI | text_tail_64B | 0x7E0FC0 |  |  |  |  |  |  | scanned=64 hits=0 | PASS

## 5. 结论与边界

定偏移形态存在命中；是否构成调用方见逐条判定与 hits.tsv。
覆盖: .text raw 全范围 mod=10 disp32 的 call/jmp/mov/push/cmp/test 定偏移编码（含 base-only SIB），FF 54 24 xx 栈间接 call。
未覆盖: 这不等于该槽从不被派发；若派发方先把 vptr 读进寄存器再 call [reg+0x124]，本卡 mov 形态可覆盖但不能单独证明 call；若采用先算地址再 call、经跳板、索引型 [reg+reg*4]、disp8、段覆盖或跨节代码，仍可能漏网。

## 6. 产物
- hits.tsv、controls.tsv、work.py（可复跑）。
