# W177-KA · SALVAGE.md（主交付）

> 任务：离线解剖 W177-J 已落盘证据，判定 ②-b 走哪一支。本卡未启动游戏/未读进程内存/未合成输入/未 import W177-J 脚本。所有源文件只读，哈希见 `EVIDENCE\ka_source_hashes.txt`。

## 0. 一句话裁定
W177-J **确实成功进局、下单扣款、拿起 ghost、点到目标格**，但**落格被拒且未退款**；实测标志四零 + A8E9A0=1 ⇒ 静态选到 `0x47C738` 头 A 类型无关占格闸；**闸门命中与返回 al 没有被任何探针读到**，所以「就是这道闸拒的」只能是 [静态推断]，②-b 未闭合。

## 1. 可安全引用的结论
| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| S1 | JSONL 24,828 行全可解析；7 个标志/全局地址字段零缺失；dt 中位数 49 µs（20,408.2/s），均值 15,517.6/s | [已证] | `EVIDENCE\ka_flag_samples_stats.txt`；`work\ka_parse_samples.py` |
| S2 | 四标志 + 三全局取值集合恒定：`(16BF,16BE,16B7,E58)=(0,0,0,0)`、`A8E9A0=1`、`A8E7AC=0`、`A8ED6B=0`，悬停→点击窗及点击样本同值 | [已证] | 同上 |
| S3 | 下单三层：L1 credits 10000→9978（另有 credits_built=9412/credits_end=9400）；L2 NAPOWR limbo 对象存在（o1_81=1, o2_74=0）；L3 目标页 ghost 像素 0.3755 vs 无-ghost j_ingame 0.0000（辅助） | [已证]（L1/L2）· [已证]（像素）· [静态推断]（L3 机制） | `EVIDENCE\ka_run_fields.txt`；`EVIDENCE\ka_png_aux.txt` |
| S4 | 点击确实落在地图：closed_loop.ok=true，hover 回读 [113,62]，target [113,63]，click_fg_ok=true，frame 677 | [已证] | `..\W177-J\EVIDENCE\j_run.json`；JSONL idx=4710 |
| S5 | 落格失败：headA 三节点全是 InfantryClass，无 BuildingClass，ghost 仍在 limbo（o1=1），credits 9400→9400 ⇒ **拒绝 + 保持 limbo，非接受后回滚/退款** | [已证] | `EVIDENCE\ka_run_fields.txt`；JSONL |
| S6 | arg2 = BuildingTypeClass*（RTTI 链 obj→vptr 0x7E4570→COL 0x7FC618→TD 0x8193A8→`.?AVBuildingTypeClass@@`）；owner=HouseClass*；二者四标志均 0 | [已证] | `..\W177-J\EVIDENCE\j_run.json` ghost_arg2_ident；台账 §678/§691 |
| S7 | 字节级重解 `0x47C620`：`[A8E7AC]!=0→0x47CA70(al=1)`；`[arg2+16BF]!=0 & A8E9A0!=0→只扫 WhatAmI 6/0x24`；`16BF=0&(16BE|16B7)!=0→0x47C805`；`E58!=0→0x47C76B 表查且仍按 A8E9A0 扫 head A 的 WhatAmI 6`；四零 + A8E9A0!=0→`0x47C738` | [已证] | `EVIDENCE\ka_47c620_disasm.txt` |
| S8 | 0x47C738/0x47C805 的 0x47C3D0 选择子 = 0：`0x47C3D0 [ebp+0xC]` 是第二栈参（ret 0xC；`[ebp+8]` 第一、`[ebp+0x10]` 第三），调用前 push ebp=0；ebp 唯一真定义 `xor ebp,ebp@0x47C62A` | [已证] | `EVIDENCE\ka_47c3d0_prologue.txt`；`EVIDENCE\ka_47c620_disasm.txt` |
| S9 | 依 S2+S7+S8，W177-J 的静态选支 = `0x47C738` 闸（head A、selector=0、`[obj+0x14]&1`） | [静态推断] | 同上；`..\W177-J\EVIDENCE\branch_recompute.txt` |

## 2. 不可引用的结论（及原因）
| # | 不可引用 | 为什么 |
|---|---|---|
| N1 | 「0x47C738 闸实际拒了这次点击」 | 没有任何 EIP/al/eax/返回点落盘；j_main.py 只读标志与格链，未读 0x47C620 返回值，也未在 0x47C853 下断；与台账 §994/§988「拒绝闸未定位」同层级，只能 [静态推断]。 |
| N2 | 「帧内标志从未翻转，所以走支恒定」 | 错源⑨/⑩：dt 中位数 49 µs，<49 µs 翻转必漏；点击处还有 281 ms 采样空洞（frame 677→685），闸门微秒级执行不在窗内。只能说「已采样时刻均为 0」。 |
| N3 | 「显绿/红圈 ⇒ can-place 放行/被拒」 | 错源⑫：j_ingame 非同帧基线；j_hover_anchor 与 j_after_click 绿/红比例逐值相同（0.3755/0.0902），不接受前后同色无法区分；颜色只能证明 ghost 覆盖了该屏幕区域，不能证明引擎判定。 |
| N4 | 「arg2 是 HouseClass*，标志是 HouseClass 字段」 | 真机 RTTI 推翻（S6）；台账 §678 早已证 +0x520=BuildingTypeClass。字段写点语义仍 [未证]（台账 §972 U5），不得写死为 HouseClass 字段。 |
| N5 | 「E58!=0 分支不查 head A」 | branch_recompute.txt 的说法过简：0x47C76B 后 `0x47C79E` 仍读 `[edi+0xE4]` 并按 A8E9A0 扫 WhatAmI 6；只能说它不经过 0x47C738 的类型无关 `[obj+0x14]&1` 闸。 |
| N6 | 「w177-j 的成功/失败=②-b 引擎允许/不允许」 | 这是单次单格观测（target 113,63 有 3 步兵），不是 10 格重叠构造；台账 §988 三分句仍有效：静态允许 [已证]/运行时未兑现 [已证]/拒绝闸未定位 [未证]。 |

## 3. 要闭合 ②-b 还缺的那一次观测
### 3.1 读什么、何时读、判据
- **时机**：真机放置点击时，在 `0x43F180`（Building slot 73, mode 1/3 挂链）主循环 `0x43F2AE call 0x47C620` 之后、针对目标 footprint 各格执行 `0x47C620` 的**那一次调用**；重点指令 `0x47C738 call 0x47C3D0`、`0x47C73D test eax,eax / 0x47C73F jne 0x47C853`、`0x47C853 xor al,al`，以及函数出口 `0x47CA70 mov al,1` / `0x47C6D1` / `0x47C85C`。
- **要读的量**：① 线程 EIP 是否命中 `0x47C853`（或 `0x47C738`/`0x47C805`）；② 该时刻 `eax`（0x47C3D0 返回值）与 `al`（0x47C620 返回值）；③ 同一时刻 arg2 四标志 + `[0xA8E9A0]` + `[0xA8E7AC]`（W177-J 已证为 0/0/0/0/1/0）；④ 目标格 `[cell+0xE4]` 链每节点 `[obj+0x14]&1` 与 RTTI（W177-J 已证 3×InfantryClass）。
- **判据**：EIP 命中 `0x47C853` 且 selector=0 且链上节点 `[+0x14]&1!=0` ⇒ 这次确由 0x47C738 闸拒 [已证]；若 EIP 命中 `0x47CA70(mov al,1)` 而仍未落格 ⇒ 闸放行、拒在别处（0x43F218 can-place 或其后 8 道检查）；若 0x47C620 根本未被执行 ⇒ 拒在更上层 UI/派发。三者互斥，才闭环台账 §994。
- **采样率**：事件驱动执行断点（命中即停）即可，**不需要轮询频率**；若退化为轮询 `GetThreadContext`，单条指令窗口约 1–10 ns（≈3 GHz），W177-J 的 20.4 kHz（49 µs）命中概率 ~10⁻⁵/次，即使 1000 次点击也远不足以做判据。
### 3.2 在不写进程内存前提下能否做到
- **严格按本卡约束（只读 RPM + 只读 GetThreadContext，无软断点、无 Hook、不写内存）做不到。** 软断点要写 `0xCC` 到代码页；硬件执行断点要 `SetThreadContext` 写 Dr0–Dr7（写线程上下文，超出「只读读取上下文」授权）；两者都不是纯只读观测。`0x47C853` 处只有瞬态寄存器值、无持久内存副作用，轮询采样必然漏掉 Hint/返回值（见 3.1 概率），因此**无法直接证明命中**。
- **可行但需扩权的唯一minimal方案**：保持不写进程内存/不注入/Hook，仅把线程上下文字段改为可写，设 Dr0=0x47C853（或 0x47C738）、Dr7 本地执行断点，在调试循环中捕获 `EXCEPTION_SINGLE_STEP` 并读 EIP/eax/al + 上述内存字段；这是台账 §994「真机一次断点」的可执行形态。**未经用户/lead 明示授权不得做。**
- 在扩权前，能做的只有继续加同源只读采样（W177-J 已做，仍只能 [静态推断]），或改用内存可观测副作用（目前未发现 0x47C853 有此类副作用）；**不得把 W177-J 的观测升格为 [已证] 的闸门命中。**

## 4. 与 branch_recompute.txt 的对照
- 一致：样本数 24,828、44 帧、四标志全 0/A8E9A0=1、点击帧 677、landing 未成功、arg2=BuildingTypeClass*。
- 不一致/需修正：① j_run 的 15,517.5/s 是均值，真实中位数 20,408.2/s；② 「E58!=0 → 表查（不查 head A）」过简（见 N5）；③ branch_recompute 把「该闸实际拒」降为 [静态推断] 是正确的，本卡维持不改。
- 本卡未 import 其脚本；字节级静态表由 `EVIDENCE\ka_47c620_disasm.txt` 独立复算。
