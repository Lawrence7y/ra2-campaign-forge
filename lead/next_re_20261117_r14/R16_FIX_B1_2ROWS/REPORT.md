# R16-FIX-B1-2ROWS 执行报告

> 角色：执行器（`work/cn:hy4flash-free`）· 卡号 R16-FIX-B1-2ROWS · 日期 2026-11-21（R16 第 24 轮）· 2 行
> 写域：`lead\next_re_20261117_r14\R16_FIX_B1_2ROWS\`（仅此目录）；**未写 `COVERAGE\coverage.tsv`**；`gamemd.exe` 仅只读打开（`pefile.PE(..., fast_load=True)` + `open('rb')`）。
> `R16_D1_WIDE_B1\` 全程只读（复核旧 delta/fields 与 REPORT/审计）。

## 0. 一句话结论
**只重写这 2 行 ④、未改 grade/判定、未并表。** 把 `004322A0`/`004324B0` 的装表点从栈临时对象 `004014C4`（宿主 `004011C0`，删除析构同构）改到 CDFileClass 真构造器装表点 `0047AA3C`（宿主 `0047AA30`）； 写一个可执行宿主身份规则并据此重跑 B1 全 18 行，确认其余 16 行无同类可疑。

## 1. 0x7E1668 全镜像写入点枚举
| 项 | 值 |
|---|---:|
| 立即数字节 `68 16 7E 00` 原始出现 | 222 |
| 其中 `mov reg,imm32`（寄存器装载，**非写内存**） | 22 |
| `mov [mem],0x7E1668` 内存写入总数 | 200 |
| ├ 栈目标（base=esp/ebp） | 191 |
| └ 非栈目标（base≠esp/ebp） | 9 |
| 非栈写入点中 **真构造器**（核心规则） | 3 |
| 非栈写入点中 **严格 canonical 构造器** | 3 |

说明：审计 `vptr_stores.tsv` 用全 `.text` 线性反汇编得 199 处（191 栈 + 8 非栈）。本卡独立按立即数字节扫描 + capstone 精确解码，另检出 `00535A60`（`mov [ecx],0x7e1668; jmp 0x431B80`，8 处 `call` 引用证实为真函数起点，线性反汇编因对齐漏检），故真实内存写入为 200 处、非栈 9 处。该站点是删除析构 thunk，不是构造器；不影响 2 行修法。

严格 canonical 规则（本卡交付的可执行规则，见 `host_rule.py`）五门全通站点：`0047A9E3`(宿主 `0047A9D0`)、`0047AA10`(宿主 `0047AA00`)、`0047AA3C`(宿主 `0047AA30`)。

## 2. 可执行宿主身份校验规则
```
G0 site 指令必须是 mov [base+disp], vt（imm32==vt）
G1 非栈：base ∉ {esp,ebp} 且非绝对地址          # 排除栈临时对象
G2 this 对象：base∈GPR 且 disp==0 且宿主 prologue 内 mov base,ecx
G3 非析构：宿主内无 call/jmp 到基类析构 0x431B80 于 site 之后；
           且无 test byte [esp+X],1 + call 0x7C8B3D + ret imm 签名   # 排除 scalar deleting dtor 同构
G4 基类构造前序：宿主内 [host,site) 有 call 0x431B20       # call <alloc>
G5 返回 this：终止 ret 前 6 条内有 mov eax,base
核心判定(行自查)=G1∧G2∧G3；严格 canonical(选装表点)=G1∧G2∧G3∧G4∧G5
```

## 3. 2 行新旧装表点/形态对照
| entry | 旧装表点 | 旧宿主 | 旧实测指令 | 旧形态 | 新装表点 | 新宿主 | 新实测指令 | 新形态 |
|---|---|---|---|---|---|---|---|---|
| 004322A0 | 004014C4 | 004011C0 | `mov dword ptr [esp + 0x20], 0x7e1668` | ctor_body(**错**) | `0047AA3C` | `0047AA30` | `mov dword ptr [esi], 0x7e1668` | ctor_body |
| 004324B0 | 004014C4 | 004011C0 | `mov dword ptr [esp + 0x20], 0x7e1668` | ctor_body(**错**) | `0047AA3C` | `0047AA30` | `mov dword ptr [esi], 0x7e1668` | ctor_body |

旧点致命证据：`004014AC mov [esp+0x20],0x7e16b0; call 0x43ae50; 004014C4 mov [esp+0x20],0x7e1668; call 0x431b80; mov eax,ebp; ret` —— 写栈临时、写后调基类析构 0x431B80、返回堆结构 ebp 而非 this；与 `004019A0` 的 `test byte [esp+8],1 + call 0x7C8B3D + ret 4` 删除析构体逐指令同构。

## 4. 18 行自查结果（`selfcheck18.tsv`）
| 项 | 值 |
|---|---:|
| 自查行数 | 18 |
| SUSPECT 行数 | 2 |
| SUSPECT entry | `004322A0`、`004324B0` |

逐行点名：
- `0040B880`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0040B930`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0040F7C0`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0040F870`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0040FD90`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0040FE40`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `00410260`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `00413F80`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `0041C180`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `00431E80`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `00431F70`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004322A0`：declared=ctor_body host_is_ctor=否 target_is_stack=是 host_is_dtor=是 → **SUSPECT**
- `004324B0`：declared=ctor_body host_is_ctor=否 target_is_stack=是 host_is_dtor=是 → **SUSPECT**
- `004393D0`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004393F0`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `00459EC0`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `0046B7E0`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0046B890`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**

结论：除本批要修的 `004322A0`/`004324B0` 外，其余 16 行均无同类可疑（8 行 mov_abs 写静态 global、8 行 ctor_body 宿主核心规则全通）。

## 5. 哈希与只读证明
| 项 | 值 |
|---|---|
| coverage.tsv 字节数（未改） | 4097787 |
| coverage.tsv sha256（未改） | `412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1` |
| gamemd.exe sha256（未改，只读打开） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| B1 是否已并表 | **否**（coverage.tsv 两 entry 第4列无 ④，哈希与上版一致） |

## 6. 样例 ④（修正后的 `004322A0`）
```
[静态推断] FileSystem/MIX member (rtti-vftable)；④ 活表槽位见证：CDFileClass::slot9（vt=007E1668，槽 9 值=004322A0，COL=007FA4D8 offset=0，RTTI=00815E38→.?AVCDFileClass@@；装表点 0047AA3C 位于 0047AA30 体内，装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 mov dword ptr [esi], 0x7e1668），entry 体外） ④升级句：CDFileClass::slot9（④ 表属类与行名类一致，均为 CDFileClass；该槽即其 vt=007E1668 表 slot9，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

## 7. 产物清单
- `vt1668_sites.tsv`（9 行非栈写入点） / `delta.tsv`（仅 2 行，8 列） / `fields.tsv`（2 行） / `selfcheck18.tsv`（18 行） / `REPORT.md` / `host_rule.py`（可执行规则） / `_test_rule.py`（规则自测）

**只重写这 2 行 ④、未改 grade/判定、未并表。**
