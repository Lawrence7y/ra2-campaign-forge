# W176 PROGRESS · ②-b 放置失败分支与 `[+0x81]` 全读写（静态）

> 卡号 W176｜执行：本会话｜目标 `ra2youli\gamemd.exe` SHA `73201CC0…F67476`｜ImageBase `0x400000`
> 必读已执行：`R13_COMMON.md` §1/§2/§6/§7（`R14_COMMON.md` 不存在）；台账 grep 已做（§841/§914/§915-5/§920）。
> 写域仅本目录；未改游戏文件、未写台账、未 git commit。

## 结论表

| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| T1-1 | 全 `.text` 命中有 `[mem+0x81]` 字节操作数 **272 处**：写 **34**（对象字段 31 + 栈 [esp]3），读 **238**（对象字段 232 + 栈 [ebp/esp]6）；word/dword/qword 宽 **0**。 | [已证] | `EVIDENCE/T1_byte81_channelA.txt`、`EVIDENCE/T1_byte81_all.json`、`EVIDENCE/T1_byte81_channelB.txt` |
| T1-2 | 双通道一致：通道 A=全镜像线性反汇编（不依赖 atlas entry+size）；通道 B=原始字节 `disp32=0x81` 模式 + 逐指令边界验证；A=272，B 原始接受 275，其中 3 处（`0x52A739`/`0x5FF59A`/`0x78D1B4`）经边界验证为假阳性（落在别的指令内部），剔除后 A∩B=272、`onlyA=0`。 | [已证] | `work/t1_sweep81.py`、`work/t1_sweep81_channelB.py`、`work/t1_compareAB.py`、`work/t1_check3.py` |
| T1-3 | `0x43F180` **零** `[+0x81]` 读写点（707 指令穷举）；`0x7014A0`（SetOwner）6 读 0 写（`0x70158A/0x701664/0x701681/0x701697/0x701757/0x7017C0`）；`0x5F4D30`（Limbo）1 读 1 写（`0x5F4D45` R、`0x5F4E9E` W=1）；`0x5F4EC0`（Unlimbo）1 读 2 写（`0x5F4F02` R、`0x5F4F4E` W=0、`0x5F521C` W=1 回滚）；谓词 `0x5F5850` 1 读（`0x5F5854`）；slot65 剔除 `0x43CEA0`/`0x5F4B10`/`0x71CC50` 各 1 读。 | [已证] | `EVIDENCE/T1_byte81_by_function.txt`、`EVIDENCE/T1_disasm_*.txt` |
| T1-4 | 极性独立复算：Limbo 内 `0x5F4E9E mov byte [esi+0x81],1`、Unlimbo 内 `0x5F4F4E mov byte [esi+0x81],0`、Unlimbo 失败回滚 `0x5F521C mov byte [esi+0x81],1` ⇒ `[+0x81]=1` 表示"已 Limbo / 不在世界中"，与台账 §915-5 一致，非新发现。 | [已证] | `EVIDENCE/T1_disasm_005F4D30.txt:117`、`EVIDENCE/T1_disasm_005F4EC0.txt:49`、`EVIDENCE/T1_disasm_005F5210.txt:9` |
| T2-1 | can-place #1 `0x43F218 call [esi+0x1AC]`：`test eax,eax / jne 0x43F5D8` ⇒ **非零立即走失败出口** `0x43F5D8→0x43F5EC ret 4`（`xor al,al`），不挂链。 | [已证] | `EVIDENCE/T2_branchA_canplace1.txt`、`EVIDENCE/T1_disasm_0043F180.txt:52-54,315-324` |
| T2-2 | 逐格校验 `0x43F2AE call 0x47C620`：`test al,al / je 0x43F504` ⇒ **失败不返回**，跳到循环增量 `inc esi` 继续下一格；只有全部格都无成功标记 `[esp+0x23]==0` 时，`0x43F5B1 je 0x43F5D8` 才返回失败。`0x47C620` 自身 al=1 仅在 `0x47CA70`（全通过出口），其余失败出口均 `xor al,al`。 | [已证] | `EVIDENCE/T2_branchB_cellfail.txt:4-6,158,211-237`、`EVIDENCE/T2_callee_47C620.txt:64-74,364-370` |
| T2-3 | can-place #2 `0x43F678 call [esi+0x1AC]`：`test eax,eax / jne 0x43F5E0` ⇒ **非零立即失败**，但目标是**共享 epilogue** `0x43F5E0`（比 #1 少一次 `call 0x6F4A70`），终到 `0x43F5EC ret 4`，不挂链。 | [已证] | `EVIDENCE/T2_branchC_check_canplace2.txt`、`EVIDENCE/T2_branchC_failure_ret.txt` |
| T2-4 | 三处失败分支**最终去向均为 `0x43F5EC ret 4`，al=0**；唯一"不返回而继续"的是 `0x47C620` 的逐格失败（去向 `0x43F504`，循环增量）。挂链 `0x43F691 call 0x5683C0` 只在成功路径。 | [已证] | `EVIDENCE/T2_cfg_mode1.txt`、`EVIDENCE/T2_cfg_mode3.txt` |
| T2-5 | CFG BFS（mode 1/3 各 566 可达指令）显示 `0x43F658` 唯一入口 `0x43F5F7 je`，且该路径 `xor_done=False`（未经过 `0x43F241 xor ebp,ebp`），故 `ebp` 在该点仍是 mode 参数；短路（由 `[obj+0x520]+0xE58==0` 选入）上 mode 3 经 `je 0x43F686` 跳过第二处 can-place，mode 1 不跳过。**这不复活"mode 3 跳过全部检查"**：两 mode 均过 #1 与逐格校验。 | [静态推断] | `EVIDENCE/T2_cfg_mode1.txt`、`EVIDENCE/T2_cfg_mode3.txt`、`EVIDENCE/T2_shortpath_43F5EF_43F691.txt:37-52`；与台账 §914-2 / R13 §2 的措辞冲突，见 `DISAGREE.md` |
| T3-1 | "10 格重叠"候选成因 5 条与可证伪观测量已列；基底几何 NAPOWR 3×2 step2=10/step3=0 引自台账 §841/§632（本卡未重算，非新发现）。 | [静态推断] | `EVIDENCE/T3_overlap_causes.md` |
| T4-1 | 真机探针表已交付 `PROBE_TABLE.md`（含地址/宽度/触发/期望/语义假设/分级），供 W177 只读轮询。 | [已证] | `PROBE_TABLE.md` |

## 核心数字（给审计员复算）

1. **`[+0x81]` 读点 238 / 写点 34**（全 `.text` 字节宽操作数；对象字段 232 读 / 31 写，栈基 6 读 / 3 写；宽 2/4/8 = 0）。
   复算：`python work/t1_sweep81.py` → 打印 `w1 writes 34 / w1 reads 238 / w4=0`；独立通道 `python work/t1_sweep81_channelB.py` 与 `work/t1_compareAB.py` 验证边界后集合一致（272）。
2. **失败分支最终去向 = `0x43F5EC`（`ret 4`, `al=0`）**；`0x47C620` 失败即时去向 = `0x43F504`（循环继续，非 ret）。
   复算：`python work/t2_failure_trace.py` 生成 `EVIDENCE/T2_branch{A,B,C}*.txt` 逐条无截断；`python work/t2_cfg_bfs.py` 给出 mode 1/3 可达集与 rets。
3. **双通道交集 272 / 假阳性 3**（`onlyA=0`，`onlyB=3` 经线性边界验证剔除）。
   复算：`python work/t1_compareAB.py`；`python work/t1_check3.py` 打印三条 `inside insn ...` 证据。
