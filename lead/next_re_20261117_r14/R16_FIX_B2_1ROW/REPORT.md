# R16-FIX-B2-1ROW 执行报告

> 角色：执行器（`work/cn:hy4flash-free`）· 卡号 R16-FIX-B2-1ROW · 日期 2026-11-21（R16 第 25 轮）· **1 行**
> 写域：`lead\next_re_20261117_r14\R16_FIX_B2_1ROW\`（仅此目录）；**未写 `COVERAGE\coverage.tsv`**；`gamemd.exe` 全程只读打开（`open('rb')` + `pefile.PE(..., fast_load=True)`）。
> `R16_D1_WIDE_B2\` 全程只读；`R16_FIX_B1_2ROWS\host_rule.py` 只读复用其 G1-G5 结构。

## 0. 一句话结论
**只重写这 1 行 ④、未改 grade/判定、未并表。** 把 `00473B10` 的装表点从栈临时对象 `004014AC`（宿主 `004011C0`）改到 CCFileClass 真构造器装表点 `00473A9B`（宿主 `00473A80`）；可执行规则 G1-G5 已落地并复查 B2 全 18 行，确认除本行外无其他 SUSPECT。

## 1. 0x7E16B0 写入点枚举与分类
| 项 | 值 |
|---|---:|
| 立即数字节 `b0 16 7e 00` 原始出现 | 207 |
| 其中 `mov reg,imm32`（寄存器装载，非写内存） | 22 |
| `mov [mem],0x7E16B0` 内存写入总数 | 185 |
| ├ target_kind=this | 5 |
| ├ target_kind=stack | 178 |
| ├ target_kind=static | 0 |
| ├ target_kind=other | 2 |

枚举方法：全镜像按立即数字节 `b0 16 7e 00` 扫描，capstone 从候选起点解码并要求 `ins.address+ins.size` 恰在 imm 尾，与审计 `vptr_stores.tsv` 的 185 处一致。分类口径（§2.1）：`this`=`mov [reg+0],vt` 且宿主 prologue `mov reg,ecx`、写前 reg 未被改写；`stack`=base∈{esp,ebp}；`static`=绝对地址；`other`=其余（edi 非 ecx 载体 / this+4 内嵌对象）。

## 2. 可执行宿主身份校验规则（G0-G5）
```
G0 site 指令须解码为 mov [base+disp], vt（imm32==vt，end 恰在 imm 尾）
G1 非栈：base ∉ {esp,ebp} 且非绝对地址                       # 排除栈临时对象
G2 this 对象：base∈GPR、disp==0、宿主 prologue 内 mov base,ecx 且写前 base 未被改写
G3 非析构：宿主内 site 之后无 call/jmp 到基类析构 0x431B80；
           且无 test byte [esp+X],1 + call 0x7C8B3D + ret imm 签名
G4 基类构造前序：[host,site) 内有 call 到已知基类 ctor {0x431B20, 0x47AA30}
           或到自身「从 ecx 装 vptr 并返回该寄存器」的 ctor_like 目标   # call <alloc>
G5 返回 this：终止 ret 前 6 条内有 mov eax,base
行级判定=核心 G1∧G2∧G3（与 B1 同口径；G4/G5 仅用于 canonical 选点，状态逐行记入 note）
canonical=G1∧G2∧G3∧G4∧G5
```

**G4 适配说明**：卡面示例 `0x431B20` 是 Abstract/FileClass 基类 ctor；本行宿主 `00473A80` 的直接基类是 CDFileClass，其 ctor 为 `0x47AA30`（B1 已证：`call 0x431B20 → mov [esi],0x7E1668 → mov eax,esi;ret`）。若把 G4 硬编码为仅 `0x431B20`，会错误淘汰审计推荐的 `00473A80`。故 G4 泛化为「已知基类 ctor 集合 ∪ ctor_like 目标」。

## 3. 5 个 `this` 目标逐点结论
| site | host | G1 | G2 | G3 | G4 | G5 | canonical | 结论 |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| `004019A6` | `004019A0` | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | 删除析构/析构序列，非构造器 |
| `00473A12` | `004739F0` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 真构造器（候选） |
| `00473A4F` | `00473A30` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 真构造器（候选） |
| `00473A9B` | `00473A80` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 真构造器（候选） |
| `00535A76` | `00535A70` | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | 删除析构/析构序列，非构造器 |

计数：**5 个 `this` 目标中 3 个过 G1-G5**（`00473A12`/`00473A4F`/`00473A9B`）；`004019A6`（宿主 `004019A0`，字节证据推翻审计表的 `00401980`）与 `00535A76` 均为析构序列。另 2 个非栈 reg+0 写入点 `00697A37`(edi)/`0075951E`(this+4) 因 G2 不过归 `other`，故 7 个非栈 reg+0 中恰 5 个是 `this` 目标，与卡面一致。

选点：**`site=00473A9B` / `host=00473A80`**（审计推荐）。三者皆过 G1-G5 且宿主类均为 CCFileClass（同写 `0x7E16B0`、同调基类 ctor `0x47AA30`）；取 44B 最干净的 `00473A80`（`push esi; mov esi,ecx; call 0x47AA30; …; mov [esi],0x7e16b0; mov eax,esi; pop esi; ret`）。

## 4. 新旧对照
| entry | 旧装表点 | 旧宿主 | 旧实测指令 | 旧形态 | 新装表点 | 新宿主 | 新实测指令 | 新形态 |
|---|---|---|---|---|---|---|---|---|
| 00473B10 | 004014AC | 004011C0 | `mov dword ptr [esp + 0x20], 0x7e16b0` | ctor_body(**错**) | `00473A9B` | `00473A80` | `mov dword ptr [esi], 0x7e16b0` | ctor_body |

旧点致命证据（只读回读 `gamemd.exe`）：`004014AC mov [esp+0x20],0x7e16b0` 写栈临时；`004014C0 lea ecx,[esp+0x20]` 把该临时对象当 thiscall 实参；`004014CC call 0x431B80` 调基类析构。宿主 `004011C0` 是 1729 条指令的无关函数。根因：`derive_raw.py:160 site=es[0]` 最低地址命中（185 个点中最低地址恰是栈临时），`generate.py:91 elif op: form='ctor_body'` 无 this/宿主校验。

## 5. 18 行 G1-G5 复查结果（`selfcheck18.tsv`）
| 项 | 值 |
|---|---:|
| 复查行数 | 18 |
| SUSPECT 行数 | 1 |
| SUSPECT entry | `00473B10` |

逐行点名：
- `0046C890`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `00473B10`：declared=ctor_body host_is_ctor=否 target_is_stack=是 host_is_dtor=是 → **SUSPECT**
- `004A2990`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004A8960`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004A9840`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004AAD30`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004AAE90`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004AB9B0`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004D7330`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004D94B0`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004DFB70`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `004F4320`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `004F4480`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0051D6F0`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `00523340`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**
- `0054E890`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `0054EA70`：declared=mov_abs host_is_ctor=否 target_is_stack=否 host_is_dtor=否 → **OK**
- `005B3970`：declared=ctor_body host_is_ctor=是 target_is_stack=否 host_is_dtor=否 → **OK**

结论：审计称只有 `00473B10` 一行 FAIL，独立复算一致：除本行（已重写）外其余 17 行无同类可疑（13 行 ctor_body 宿主核心规则全通、4 行 mov_abs 写静态 global；本行旧 site 为 SUSPECT，新 site 已过 G1-G5）。

## 6. 哈希与只读证明
| 项 | 值 |
|---|---|
| coverage.tsv 字节数（未改） | 4097787 |
| coverage.tsv sha256（未改） | `412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1` |
| gamemd.exe sha256（未改，只读打开） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| B2 是否已并表 | **否**（coverage.tsv `00473B10` 第 4 列无 ④，哈希与上版一致） |

## 7. 样例 ④（修正后的 `00473B10`）
```
CCFileClass 虚表槽 9(+0x24)：文件系统/MIX/压缩加密 方法（③b 细则#1 级（5 道互斥闸动作各异）；严格口径（只认跳表/循环/错误码）下本行不成立）；④ 活表槽位见证：CCFileClass::slot9（vt=007E16B0，槽 9 值=00473B10，COL=007FA590 offset=0，RTTI=00815E58→.?AVCCFileClass@@；装表点 00473A9B 位于 00473A80 体内，装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 mov dword ptr [esi], 0x7e16b0），entry 体外） ④升级句：CCFileClass::slot9（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot9，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

## 8. 产物清单
- `vt16b0_sites.tsv`（185 行全部写入点） / `delta.tsv`（仅 1 行，8 列） / `fields.tsv`（1 行） / `selfcheck18.tsv`（18 行） / `REPORT.md` / `host_rule.py`（可执行规则） / `_test_rule.py`（规则自测）

**只重写这 1 行 ④、未改 grade/判定、未并表。**
