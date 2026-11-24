# S02-K2 · CRT_NAMES.md — CRT 桩函数定名表（T2）

> 证据纪律：每条 name 必须带「依据类型 + 依据地址」。命名依据为 **YRpp 外部符号表**（`JMP_STD/JMP/CALL(0x…)` 显式地址宏）或 **多锚点调用收敛 + 字节签名**。
> **无字节形态判据参与命名**（避免 `ret 0xC` 672 次 / `B8 imm32 C3` 543 次的"形态判据不特异"陷阱）。基线见 `EVIDENCE/BASELINE.txt`：随机 31 个 sub_ 地址命中 YRpp 标记均值 0.128（真实 = 31），标记是地址特异的。

## A. 靶内（S02∩atlas，327）新增定名

| entry | name | 依据类型 | 依据地址 | 分级 |
|---|---|---|---|---|
| `007C9442` | `CRT::_nh_malloc` | 多锚点调用收敛 + MSVC CRT 签名字节 | 被 `CRT::malloc@0x7C9430`（call @0x7C943A，flag=`[0xB782C4]`）与 `CRT::_new@0x7C8E17`（call @0x7C8E1D，flag=`push 1`）两个 `[已证]` 锚点调用；本体 `0x7C9442` 首指令 `cmp [esp+4],-0x20` + `call 0x7C946e` + 分配失败重试环（`0x7C9461 call 0x7D06E8` 后 `jne 0x7C9449`）= 经典 `_nh_malloc(size,flag)` | `[静态推断]` |

## B. 跨子系统归位建议（CRT 函数被弱"邻居投票"错归 S19/S06；需合并卡/审计协调）

| entry | name | 原归属 | 依据类型 | 依据地址 | 分级 |
|---|---|---|---|---|---|
| `007C8B48` | `CRT::qsort` | S19 `sub_` | YRpp 外部符号 + 字节体 | `YRpp/CRT.h:87-88` `qsort(...) { JMP_STD(0x7C8B48); }`；字节 `0x7C8B57 cmp esi,2 / jb / cmp [ebp+0x10],0 / dec esi; imul esi,[ebp+0x10]` = (num-1)\*size 快排初始化（`EVIDENCE/T2_byte_verify.txt`） | `[已证]` |
| `007C8E25` | `CRT::bsearch` | S19 `sub_` | YRpp 外部符号 + 字节体 | `YRpp/CRT.h:90-91` `bsearch(...) { JMP_STD(0x7C8E25); }`；字节 `0x7C8E2E lea edi,[eax-1] / imul edi,[ebp+0x14] / shr ebx,1` = (num-1)\*size + 折半二分查找 | `[已证]` |
| `007C5F00` | `CRT::_ftol` | S06 `sub_` | YRpp 外部符号 + 台账已证 + 字节体 | `YRpp/Unsorted.h:29 CALL(0x7C5F00)`（F2I64）；台账 §4（`0x7C5F00`=1974 调用者 / EIP 3.2%）；字节 `0x7C5F03 fnstcw / 0x7C5F1B fistp qword ptr` = double→long 截断 | `[已证]` |

## C. 洞候选（不进 delta：需按 R14-R14 四项入口证据单独裁定）

| entry | name | 依据类型 | 依据地址 | 状态 |
|---|---|---|---|---|
| `007CB302` | `CRT::vfprintf` | YRpp 外部符号 + 字节体 | `YRpp/CRT.h:107-108 { JMP_STD(0x7CB302); }`；字节 `0x7CB302 push ebx/push esi; call 0x7CB3F9; call 0x7D2B7F; call 0x7CE2A5`（格式化输出引擎） | 不在 atlas 也不在 coverage ⇒ 按"不在 atlas 区间内 ≠ 是函数"不新增行，记 `UNKNOWNS.md` |

## D. 靶内已具名（31 个 YRpp 标记，全部已名，本次不重复）

`0x7C8B3D _delete / 0x7C8D20 strcmpi / 0x7C8DF0 strrchr / 0x7C8E17 _new / 0x7C8EF4 sprintf / 0x7C91D0 strncpy / 0x7C93E8 free / 0x7C9430 malloc / 0x7C94EB fread / 0x7C9602 fwrite / 0x7CA090 memcpy / 0x7CA3C5 wcsrchr / 0x7CA405 wcslen / 0x7CA422 wcsncpy / 0x7CA45F wcscat / 0x7CA489 wcscpy / 0x7CA4B0 strstr / 0x7CA530 sscanf / 0x7CA564 swprintf / 0x7CA5D3 wcscmp / 0x7CA75B fclose / 0x7CA7D8 fprintf / 0x7CA845 fopen / 0x7CAF30 strchr / 0x7CB19C fflush / 0x7CB550 strncat / 0x7CB7BA vsprintf / 0x7CDA90 strcmp / 0x7D5408 strdup / 0x7DC720 Unsorted::RaiseError` + RTTI 槽名 7 个（`type_info::slot0` 等）。全部由 `YRpp/CRT.h` `JMP_STD` 地址逐行复算一致（`EVIDENCE/T2_yrpp_broad.txt`）。

## E. 不可定（保持 sub_）

290 个未具名靶中，除上述 `_nh_malloc` 外 **289 个无可指认命名依据**：
- 0x77–0x7B 段约 168 个：MSVC CRT/C++ runtime 内部（iostream/异常/locale/字体等），YRpp 全量地址宏在此段仅 2 处（0x776D80 `sub_53E3C0` 占位 / 0x777080 `GetResource`），无 CRT 符号可配。
- 0x7C/0x7D 段约 121 个：其中 25 个可由"≥1 个具名 CRT 锚点调用"判为 CRT 内部辅助件（`EVIDENCE/T2_callgraph.txt`），但**无法确定其标准符号名**（无外部符号、无唯一字节签名），按"拿不到依据保持 sub_"处理，不造名。
- `vfprintf` 之外的 qsort/bsearch/_ftol 已单列 B 表。

**结论**：CRT 具名符号集在 S02 靶内已基本被 YRpp 用尽；本卡新增 1 条靶内名（+ 3 条跨子系统归位候选）。`operator new`/`malloc`/`_ftol` 三锚点反查证明其地址簇（0x7C8A–0x7CE0）即为 MSVC 静态 CRT，但**其余桩函数不可凭形态定名**。
