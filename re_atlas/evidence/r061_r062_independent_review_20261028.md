# R-061/R-062 独立复核报告（RE-ATLAS 线 C 线 · 冻结候选升格前复核 · 2026-10-28）

- 复核员：RE-ATLAS C 线独立复核员（全新上下文；**同族降级**——原定异族 qfmodel 通道持续网络故障不可用，本轮按 R-061 先例降级同族会话模型新上下文执行，已登记台账；独立性=全新上下文+亲自取证，未复用任何前轮探针/脚本/结论）。
- 纪律执行：镜像只读、未运行游戏；本轮新写入仅 2 个文件——本报告 + `re_atlas/tools/_crev_recon.py`、`re_atlas/tools/_crev_engine.py`（`_crev_` 前缀临时脚本）；门禁/变异套件/证据书/冻结清单/LEDGER/STATUS/INDEX/`gamemd.exe` 全程未触碰。
- 工具链：Python 3.12.10 + capstone 5.0.7；PE 段表自算：ImageBase=0x400000，ENTRY=0x7CD80F，.text=[0x401000,0x7E1000)（raw off=0x1000，size=0x3E0000），与门禁同界。

---

## 0. 复核范围与证据版本（哈希自验，全部本人读回）

| 文件 | 宣称值 | 本轮实测 | 判定 |
|:--|:--|:--|:--|
| `ra2youli/gamemd.exe` | `73201cc0…f67476` | 同 | ✓（`ra2bench/gamemd.exe` 同哈希，两副本一致） |
| `re_atlas/tools/r061_witness_this_contract.py` | `3080309a…1ebfc` | 同 | ✓ |
| `re_atlas/tools/r062_upward_trace_contract.py` | `611ca4d4…1dff`（R-062 书 §1 宣称） | 同 | ✓ |
| `re_atlas/tools/mutate_r061_gate.py` | （无宣称） | `89a7956f…4cc4e3` | 登记 |
| `re_atlas/tools/mutate_r062_gate.py` | `1e8d600de6f096ee…`（R-062 书 §3 宣称） | 同 | ✓ |
| `out/_r061_freeze5.json` | `6330e5de…ca8`（书内 §5 宣称） | 同 | ✓（**任务书写作 `out/_r061_freeze.json`，盘面实件为 `_r061_freeze5.json`——任务书文件名笔误**，证据书与套件内名称/哈希一致） |
| `out/_r062_freeze.json` | `1e4e0ba0…881ab214` 前缀 | `1e4e0ba0b42c…1488f1d4360914881ab214` | ✓ |
| `out/_r061_freeze_run1.txt` | 前缀 `8deb04a4` | `8deb04a4ffe3…` | ✓ |
| `out/_r062_freeze_run1.txt` | 前缀 `a366c932` | `a366c932ba88…` | ✓ |
| `re_atlas/evidence/r061_witness_this.md` | （本轮实测登记） | `a9258862…c453c93` | 登记 |
| `re_atlas/evidence/r062_upward_trace.md` | （本轮实测登记） | `bd37de71…8323b` | 登记 |

清单内嵌守卫：`_r061_freeze5.json`/`_r062_freeze.json` 件内 `gate_sha256`/`image_sha256` 与盘上门禁/镜像逐字一致（`_crev_recon.py` 实测）。

---

## 1. 复跑：门禁与变异套件 — CONFIRMED

### 1.1 门禁全量复跑（本人执行）

```
$ python re_atlas/tools/r061_witness_this_contract.py
  PASS 194 / FAIL 0；末行：== 194/194 PASS ==；G61_EXIT=0
$ python re_atlas/tools/r062_upward_trace_contract.py
  PASS 126 / FAIL 0；末行：== 126/126 PASS ==；G62_EXIT=0
```
R-062 控制标签逐行 PASS：`U-ctl-*` global-load 164/3/90/2/118、`U-vptrstore-*` 三站、`U-rtti-name`（'.?AVGenericList@@'）、`U-rtti-ctl`（vfp 0x7F9594）、`U-lea-adj`（17）、`U-p1f-*` 五钉、`U-noverdict-drift`。

### 1.2 变异套件全量复跑（本人执行，两套件均全量双路、未抽样）

```
$ python re_atlas/tools/mutate_r061_gate.py     # 194 例 × splice+full 双路，全量
  baseline 194/194 PASS
  …（194 行逐例 EXACT，含红集打印；全程零 SURVIVED/EXC/MISMATCH）
  == FREEZE-SUITE TALLY ==
  cases=194 exact=194 survived=0 exc=0 splice-mismatch=0 full-mismatch=0
  labels=194 covered-by-literals=194 uncovered=0 phantom-expectations=0
  == 194/194 cases exact-killed (freeze-candidate, pending independent review) ==
  MUT61_EXIT=0
$ python re_atlas/tools/mutate_r062_gate.py     # 112 例 × splice+full 双路，全量
  baseline 126/126 PASS
  …（112 行逐例 EXACT；全程零 SURVIVED/EXC/MISMATCH）
  == R-062 FREEZE-SUITE TALLY ==
  cases=112 exact=112 survived=0 exc=0 splice-mismatch=0 full-mismatch=0
  labels=126 covered-by-literals=126 uncovered=0 phantom-expectations=0
  == 112/112 cases exact-killed (pending independent review) ==
  MUT62_EXIT=0
```

两套件运行期间 STALE 三哈希守卫通过（gate/image/manifest 与冻结值一致方才执行）；套件为只读执行（打印至 stdout，不落盘）。逐例红集打印与冻结字面量的全等另经 §1.3 三字段对账独立确认。

### 1.3 冻结链三字段对账（`_crev_recon.py`，**全量**而非抽 20）

- 套件 `CASES` 字面量（AST 提取，未执行套件）↔ 冻结清单 (case, mut, red)：**194/194 与 112/112 三字段全等，problems=0**。
- `out/_r06{1,2}_freeze_run1.txt` ↔ 清单：case 集全等、EXACT 计数 194/112 全中、tally 六字段全等、`EXIT=0` 在场；R-061 run1 打印红集 ↔ 清单 red **194/194** 逐例全等。
- 溯源闭合：`out/_r061_mut_calib5.txt` / `out/_r062_mut_calib2.txt` 内嵌 `JSON_MANIFEST` 与冻结清单**逐字节全等**（R-062 侧排除 `round` 字段，见 §9 观察-3）。
- `python re_atlas/tools/r062_upward_trace_contract.py --dump`（EXIT=0）输出 88 行与件内 `CHAIN` 字面量**键集全等、逐行 (verdict, chain) 全等**——"CHAIN 88 行冻结字面量由 --dump 机器生成"声明成立。

## 2. 函数边界与调用点独立重导 — CONFIRMED（13/13 全查，超出抽 3 要求）

`_crev_engine.py` 自有引擎（自写 PE 解析、线性解码 **1,394,120** 条对齐指令、**6,719** 个对齐 E8 头、自写 pred 图（jcc 双边/jmp 仅 taken/ret 断边）、自写反向 BFS；**不 import 门禁模块**）：

- **13/13 宿主**：`reach(site) ∩ E8头集 == {host}` 全部单例成立；caller 计数 **757/2/5/7/1/306/650/67/5/3/0/651/3** 与书 §1 表逐值全中。被抽验三点：
  - `0x5283D0`：heads-in-reach={0x5283d0}，cnt=**306** ✓，头签名 `83ec0c33c053` ✓；
  - `0x5276D0`：heads-in-reach={0x5276d0}，cnt=**757** ✓，头签名 `83ec0c33c053` ✓；
  - 冷入口 `0x5293E3`：E8 头集=∅、cnt=**0** ✓；冷头 `0x529394` 字节=`33c03bf00f84` ✓；全镜像 `jmp→0x529394` **仅 `0x52949C` 一处** ✓；`0x529394 ∈ reach(0x5293E3)`（尾跳入边活）✓；冷块**不**在 `0x529160` 站点 reach 内（书"0x529160 闭包不含它"）✓。
- 交叉验证（前向 BFS，调用边不跟随）：三宿主 `site ∈ fwd(host)` 均真，地址相邻头**零泄漏**。

## 3. 88 caller 分类：完整性/互斥/求和/字节 — CONFIRMED

自有分类器（自写 ret 框定 + 寄存器链回溯，同文档语义、异实现）：

- **求和与互斥**：verdict 直方图 = {param-slot 54, stack-object 17, local-slot 1, param1-forward 3, unknown-reg 12, unknown-thunk 1}，**sum=88**；逐 caller 单一 verdict（互斥由构造保证）；walked 集合 == CHAIN 键集合（**完整性**，无多无漏）。
- **88/88 行** verdict 与链字节序列同 `CHAIN` 冻结字面量**全等**（mismatches=0）；并对**全部 88 行**做了"自有导出写者地址 → 盘上原始字节 == 冻结链 hex"三方核对（`rd()` 直读文件），**0 差**——超出抽 10 行要求。
- **param1-forward 3 行（0x68A754/0x68A772/0x68A790）定性**：五钉独立全中——F 头 `0x689E90` 前 10 字节=`558bec83e4f883ec3453`、F 唯一 E8 caller=[0x687853]、`8b7d08`@0x689E9C（caller 帧 `mov edi,[ebp+8]`＝arg1）、G 帧 `8b7c2418`@0x687744、F 帧 `[esp+0x18]` 写者=0。定性"caller 第一参数原样转发"成立；书内明记"身份仍不命名/UNKNOWN 保留"，**无过度**。
- **unknown-reg 12 行**：自有扫描同判"链死在入向 callee-saved（帧内无写者）"；书内"再上一跳未穷尽＝UNKNOWN 保留"——**无不足**（未把可继续上行的行写成定论）。
- **param-slot 过度认定审计**：55 行（param-slot 54 + local-slot 1）帧内对 verdict 槽的 `lea`（取址传引用）命中 **0/55**——本轮未发现"零写入但实为被 callee 经引用写"的反证形态。（残余局限见 §11。）

## 4. GenericList 构造证据 — CONFIRMED（1 处标题级措辞红项，见 §8）

- **三窗 8 字节钉**（盘上直读）：`0x7787C0`=`c7442438041b7e00`、`0x779BB3`=`c7442424041b7e00`、`0x779E33`=`c7442424041b7e00`——`mov dword ptr [esp+X], 0x7E1B04` 形态全中 ✓。
- **自有 RTTI 链 walk**：`[0x7E1B00]`=COL 0x7FAD18 → `[COL+0xC]`=TD 0x817508 → TD+8 名=**`.?AVGenericList@@`** ✓；控制位：`[0x8174C8]`=0x7F9594 ✓，且 0x8174C8 实为 **CCINIClass TypeDescriptor 起点**（TD+8 名=`.?AVCCINIClass@@`，首 dword 即其 vfp 0x7F9594；GenericList TD 0x817508 与之相邻 +0x40）——书内"控制位 CCINIClass TD 0x8174C8 vfp 0x7F9594 同 walk 复现"属实。
- **5/12 划分如实**：自有帧内槽写普查（17 个 stack-object 行全查）：**恰 5 行**帧内存在 vptr store——0x77884F/0x77890C/0x778956（slot 0x38，共用 store 0x7787C0）、0x779C3D（0x779BB3）、0x779EBD（0x779E33）；**其余 12 行帧内对该槽零 dword 写**（含 reg 形态 `89 44 24 xx` 也无）——书内"5 行有帧内构造证据 / 12 行裸传"逐行核实。12 行"构造点未证，不编故事"**如实保留**，未发现把未证明行写成已证明。
- lea 邻接：17/17 行 `lea ecx,[esp+slot]` 紧邻 call（0 违例）✓。

## 5. 负命题的阳性对照 — CONFIRMED

- **caller-self = 0/88**：同一自有分类器跑五个直传宿主，caller-self 命中 **0x5276D0=4 / 0x528A10=31 / 0x5295F0=5 / 0x5283D0=11 / 0x528F00=0，总 51**——与书 §4.3 "4+31+5+11+0=51（0x528A10 高达 31）"逐值全中。检测器能看见该形态 ⇒ SMALL 宿主 0/88 是有检测能力在场的真结果。
- **global-load = 0（跨 7 SMALL）**：同检测器五直传宿主命中 **164/90/118/3/2**，与 R-061 冻结 E-hist（119+45 / 80+10 / 95+23 / 3 / 2）逐值全等 ✓。另以 strict 变体（任一 ecx 写者截停）复算 hist，五宿主仍全等——结论对该启发式不敏感。
- R-061 侧负命题 `D-2C-absent-527f20` 的阳性对照=注入式 killer（往 0x527F20 窗口注入 `mov esi,0xB7882C` 即红），本轮套件复跑 EXACT 在案。

## 6. 诚实账 — CONFIRMED（无 UNKNOWN 静默升格）

逐条核对（行号引 `r061_witness_this.md`/`r062_upward_trace.md`）：

- R-061 §3"转参=UNKNOWN…**保留 UNKNOWN，不外推**"（L76）；§4 一一对应未闭合/冷块身份未展开/0x528220 thunk 再上跳 UNKNOWN/"不宣称任何可改写点；未真机"（L86-92）；R-062 §5"实例归属仍是 UNKNOWN…17+1 是类型命名不是实例身份"（L92-95）。**均如实保留**。
- **BSS 未读如实**：自有段表核实 `0xB7882C/0xB78830` 落 `.data`（VA 0x812000..0xB79BE4）但 fileoff 0x77882C **超出 raw 界 0x47E000** → 盘上确不可读（书"现值不可读（BSS）"属实）。
- **工厂件→见证连线未证**：书 L78"其结果流向未见直写任何 [G+8]（K4 实测空）⇒…未证，不连"；R-062 §2 推论段明确"机制推论（不升格为结论）…实例归属账不变（UNKNOWN 保留）"。
- **caller-self 51 行未展开**：R-062 §5 明记"超出本件 7-SMALL 范围，登记不穷尽"。
- **六全局 [+8] 构造器清零旁证**（本轮自有普查）：全镜像 `mov [imm32],reg` 直写命中 GLOBAL+8 者**恰 6 站**（0x40DFBE→0x887188、0x40E06E→0x887210、0x40E11E→0x887130、0x40E1CE→0x887060、0x40E27E→0x8870C8、0x49B39E→0x89F520），全在书 L80-81 所指清零簇内；各簇首 `53 33 db`=push ebx;xor ebx,ebx ⇒ **ebx=0 → [+8] 初值恒 NULL 成立**；`c7 05` imm 形态对 G+8 直写=0 站。（注：书列 12 址为 [G+4]/[G+8] 成对站，+8 位是每对第二址，语义一致。）

## 7. R-061 推翻案（R-059 §2③）抽验 — CONFIRMED（4/4，超出抽 1）

自有引擎四 spill 址全查：

```
0x5275CC bytes=8bf1 'mov esi,ecx'  below-head(0x5276D0)=True  in-reach(0x527750 站)=False
0x527B97 bytes=8bf1                 below-head(0x527CC0)=True  in-reach(0x527D5B 站)=False
0x528DF2 bytes=8bf1                 below-head(0x528F00)=True  in-reach(0x528F97 站)=False
0x52A623 bytes=8bf1                 below-head(0x52A760)=True  in-reach(0x52A7DE 站)=False
```

`0x5275CC` 实字节确为 `8bf1` 且位于对齐闭包外——R-059"线性窗跨函数污染、4 个 `mov esi,ecx` 实为前驱函数尾段"的推翻有**字节+可达性双重支撑**；R-059 探针 `8bce/8bf1` 记混的纠正（`8bf1`=mov esi,ecx）与 capstone 解读一致。

## 8. 出入与红项清单

| # | 级别 | 内容 |
|:--|:--|:--|
| 红-1 | **红项（措辞，工件级数字无误）** | R-062 书 §2 标题"0x528C00 的**三分之一** this 是 caller 栈上 GenericList 临时件"：实测 17 stack-object / 67 总 caller = **25.4%（约 1/4）**。正文数字（17 行、67 caller）正确，仅标题比例夸大。建议升格办理时顺手勘误为"约四分之一"。 |
| 题-1 | 题面勘误 | 复核任务书写 `out/_r061_freeze.json`，盘面实件为 `out/_r061_freeze5.json`（哈希 `6330e5de…` 对上；证据书 §5 与套件内名称一致）——任务书笔误，非工件缺陷。 |
| 观察-1 | 非缺陷 | R-062 清单件内 `round=1` 与书 §3"round-2 校准"表述不一致：溯源为 round-2 校准**复用 round-1 脚本**（`out/_calib_r062_mut1.py` L201 以常量 `round:1` 写清单）就地修复后重跑，`_r062_mut_calib2.txt` 内嵌 JSON 与冻结清单逐字节全等——字段名与轮次语义错位，数据链无恙。 |
| 观察-2 | 非缺陷 | R-062 §1 表把 param-slot 语义表述为"该帧对 X 零写入 ⇒ X 是**入向 cdecl 参数槽**"——从"零写入"到"入向参数"含一步推断（理论上 callee 经引用写未排除）；本轮 55 帧审计未发现 `lea` 取址反证，且书内已用"身份不命名/UNKNOWN"兜底，判可接受。 |
| 自记-1 | 复核员自记 | 本轮我方探针先后两次 bug（`fo()` 误以 RVA 比 VA 致 `rd()` 读错节；vptr 切片 `[6:14]` 应为 `[8:16]`），均已修正重跑；首跑的 133 条 RAWBYTE"假红"与 0 行"构造证据"皆为我方缺陷所致，**非工件问题**，如实登记以保证透明。 |

## 9. 总判定

- **R-061（re_atlas/evidence/r061_witness_this.md + 门禁 194 断言 + 冻结套件 194 例）：维持冻结候选所载全部断言成立，建议升格。**
  仍缺项：① 异族通道复核在本轮仍以"同族降级"替代（通道登记在案；若章程把 out-of-family 作硬条件，则该项仍开）；② 真机/运行期行为（BSS 现值、命中缓存实际填充序列）不在静态范围，书内亦未宣称。
- **R-062（re_atlas/evidence/r062_upward_trace.md + 门禁 126 断言 + 冻结套件 112 例）：维持冻结候选所载全部断言成立，建议升格。**
  仍缺项：① 同上异族通道项；② 12 裸传行构造点、51 行 caller-self 再上行、param-slot"零写入⇒入参"的寄存器间接写路径——书内均已如实登记为未证/不穷尽，不构成升格障碍；③ 红-1 标题比例措辞建议随升格一并勘误（不影响数据）。

## 10. 本轮实测落点汇总（供 Leader 核对）

- 门禁：R-061 `== 194/194 PASS ==` EXIT=0；R-062 `== 126/126 PASS ==` EXIT=0。
- 套件：R-061 194/194 exact、EXIT=0；R-062 112/112 exact、EXIT=0（均 splice+full 双路、uncovered/phantom=0）。
- 冻结链：套件字面量↔清单 194+112 三字段全等；run1↔清单全等；校准输出↔清单逐字节全等；`--dump`↔CHAIN 88 行全等。
- 自有引擎：13 宿主边界/计数全中；88 行分类与字节全中；GenericList 5/12 划分与三窗字节+RTTI 全中；阳性对照 51 行与 164/90/118/3/2 全中；推翻案 4/4 成立；六全局 G+8 直写普查 6 站+ebx 清零成立；BSS 不可读成立。

## 11. 局限

1. **同族降级**：异族通道不可用，本轮为同模型家族全新上下文 fresh-eyes；"通道异族性"意义上的 out-of-family 仍未满足，是否据此升格由发起线章程裁定。
2. **静态复核**：未真机、未运行游戏；运行期值（BSS、缓存填充）不可判，书内亦未宣称。
3. 变异套件复跑为全量双路（非抽样）；但我方未对每例的"红集预期"另行独立重推——预期真源仍为冻结清单（其与校准输出/套件字面量/run1 的四点全等已由 §1.3 闭合）。
4. 自有边界引擎与门禁同属"线性对齐扫描"域：若存在仅由非对齐字节序列进入的第三形态入口（如冷区之外的垫片），该方法域可能同盲；本轮以冷入口 `0x5293E3` 样本+前向 BFS 交叉验证覆盖了已声明的形态，未穷举全部 6,719 头的前向验证。
5. param-slot 的"入向参数"语义残差：帧内零写入+零 `lea` 取址仍不能排除 callee 经 `mov reg,esp` 派生指针写入的极端形态（本轮未发现任何此类形态，55 帧零命中）。

## 12. 探针与捕获件清单

`re_atlas/tools/_crev_recon.py`（对账）· `re_atlas/tools/_crev_engine.py`（自有引擎）——仅此两个临时脚本；门禁/套件输出经控制台/系统临时目录捕获，未落工作区；生产文件零改动（全部哈希已于文首/文中读回）。

---

## 13. OOF 勘误补记（2026-10-29，Leader 依异族复核 r061_r062_oof_review_20261029.md 红-2/红-3/红-4 代录）

- 红-2：§1 代码块中 `G61_EXIT=0`/`G62_EXIT=0` 非脚本输出行，系复核时 shell `$?` 记录——表述级更正，
  不影响 EXIT=0 判定本身。
- 红-3：§3「55 帧 lea 取址审计 0/55」的探针 `_crev_engine.py:430/434` `startswith("[esp")` 对 capstone
  渲染 `eax, [esp + 0x38]` 恒假（Leader 已独立复现）——该处为恒真式空转；异族复核员以逐指令 esp 追踪
  （含未弹出 push、callee ret imm16 清理）正确重算，address-taken 命中确为 0，**结论碰巧为真**，
  param-slot 判定不受影响；本条如实登记探针缺陷。
- 红-4：§0 表中 `mutate_r061_gate.py` 哈希「无宣称」不实——LEDGER.md:6619 有记
  `89a7956f…4cc4e3`（本轮 Leader 实测同值）。
- 本报告 §9「建议升格」已获异族对账级复核支持并办理，见 LEDGER 升格收口段。
# R-061/R-062 独立复核报告（RE-ATLAS 线 C 线 · 冻结候选升格前复核 · 2026-10-28）

- 复核员：RE-ATLAS C 线独立复核员（全新上下文；**同族降级**——原定异族 qfmodel 通道持续网络故障不可用，本轮按 R-061 先例降级同族会话模型新上下文执行，已登记台账；独立性=全新上下文+亲自取证，未复用任何前轮探针/脚本/结论）。
- 纪律执行：镜像只读、未运行游戏；本轮新写入仅 2 个文件——本报告 + `re_atlas/tools/_crev_recon.py`、`re_atlas/tools/_crev_engine.py`（`_crev_` 前缀临时脚本）；门禁/变异套件/证据书/冻结清单/LEDGER/STATUS/INDEX/`gamemd.exe` 全程未触碰。
- 工具链：Python 3.12.10 + capstone 5.0.7；PE 段表自算：ImageBase=0x400000，ENTRY=0x7CD80F，.text=[0x401000,0x7E1000)（raw off=0x1000，size=0x3E0000），与门禁同界。

---

## 0. 复核范围与证据版本（哈希自验，全部本人读回）

| 文件 | 宣称值 | 本轮实测 | 判定 |
|:--|:--|:--|:--|
| `ra2youli/gamemd.exe` | `73201cc0…f67476` | 同 | ✓（`ra2bench/gamemd.exe` 同哈希，两副本一致） |
| `re_atlas/tools/r061_witness_this_contract.py` | `3080309a…1ebfc` | 同 | ✓ |
| `re_atlas/tools/r062_upward_trace_contract.py` | `611ca4d4…1dff`（R-062 书 §1 宣称） | 同 | ✓ |
| `re_atlas/tools/mutate_r061_gate.py` | （无宣称） | `89a7956f…4cc4e3` | 登记 |
| `re_atlas/tools/mutate_r062_gate.py` | `1e8d600de6f096ee…`（R-062 书 §3 宣称） | 同 | ✓ |
| `out/_r061_freeze5.json` | `6330e5de…ca8`（书内 §5 宣称） | 同 | ✓（**任务书写作 `out/_r061_freeze.json`，盘面实件为 `_r061_freeze5.json`——任务书文件名笔误**，证据书与套件内名称/哈希一致） |
| `out/_r062_freeze.json` | `1e4e0ba0…881ab214` 前缀 | `1e4e0ba0b42c…1488f1d4360914881ab214` | ✓ |
| `out/_r061_freeze_run1.txt` | 前缀 `8deb04a4` | `8deb04a4ffe3…` | ✓ |
| `out/_r062_freeze_run1.txt` | 前缀 `a366c932` | `a366c932ba88…` | ✓ |
| `re_atlas/evidence/r061_witness_this.md` | （本轮实测登记） | `a9258862…c453c93` | 登记 |
| `re_atlas/evidence/r062_upward_trace.md` | （本轮实测登记） | `bd37de71…8323b` | 登记 |

清单内嵌守卫：`_r061_freeze5.json`/`_r062_freeze.json` 件内 `gate_sha256`/`image_sha256` 与盘上门禁/镜像逐字一致（`_crev_recon.py` 实测）。

---

## 1. 复跑：门禁与变异套件 — CONFIRMED

### 1.1 门禁全量复跑（本人执行）

```
$ python re_atlas/tools/r061_witness_this_contract.py
  PASS 194 / FAIL 0；末行：== 194/194 PASS ==；G61_EXIT=0
$ python re_atlas/tools/r062_upward_trace_contract.py
  PASS 126 / FAIL 0；末行：== 126/126 PASS ==；G62_EXIT=0
```
R-062 控制标签逐行 PASS：`U-ctl-*` global-load 164/3/90/2/118、`U-vptrstore-*` 三站、`U-rtti-name`（'.?AVGenericList@@'）、`U-rtti-ctl`（vfp 0x7F9594）、`U-lea-adj`（17）、`U-p1f-*` 五钉、`U-noverdict-drift`。

### 1.2 变异套件全量复跑（本人执行，两套件均全量双路、未抽样）

```
$ python re_atlas/tools/mutate_r061_gate.py     # 194 例 × splice+full 双路，全量
  baseline 194/194 PASS
  …（194 行逐例 EXACT，含红集打印；全程零 SURVIVED/EXC/MISMATCH）
  == FREEZE-SUITE TALLY ==
  cases=194 exact=194 survived=0 exc=0 splice-mismatch=0 full-mismatch=0
  labels=194 covered-by-literals=194 uncovered=0 phantom-expectations=0
  == 194/194 cases exact-killed (freeze-candidate, pending independent review) ==
  MUT61_EXIT=0
$ python re_atlas/tools/mutate_r062_gate.py     # 112 例 × splice+full 双路，全量
  baseline 126/126 PASS
  …（112 行逐例 EXACT；全程零 SURVIVED/EXC/MISMATCH）
  == R-062 FREEZE-SUITE TALLY ==
  cases=112 exact=112 survived=0 exc=0 splice-mismatch=0 full-mismatch=0
  labels=126 covered-by-literals=126 uncovered=0 phantom-expectations=0
  == 112/112 cases exact-killed (pending independent review) ==
  MUT62_EXIT=0
```

两套件运行期间 STALE 三哈希守卫通过（gate/image/manifest 与冻结值一致方才执行）；套件为只读执行（打印至 stdout，不落盘）。逐例红集打印与冻结字面量的全等另经 §1.3 三字段对账独立确认。

### 1.3 冻结链三字段对账（`_crev_recon.py`，**全量**而非抽 20）

- 套件 `CASES` 字面量（AST 提取，未执行套件）↔ 冻结清单 (case, mut, red)：**194/194 与 112/112 三字段全等，problems=0**。
- `out/_r06{1,2}_freeze_run1.txt` ↔ 清单：case 集全等、EXACT 计数 194/112 全中、tally 六字段全等、`EXIT=0` 在场；R-061 run1 打印红集 ↔ 清单 red **194/194** 逐例全等。
- 溯源闭合：`out/_r061_mut_calib5.txt` / `out/_r062_mut_calib2.txt` 内嵌 `JSON_MANIFEST` 与冻结清单**逐字节全等**（R-062 侧排除 `round` 字段，见 §9 观察-3）。
- `python re_atlas/tools/r062_upward_trace_contract.py --dump`（EXIT=0）输出 88 行与件内 `CHAIN` 字面量**键集全等、逐行 (verdict, chain) 全等**——"CHAIN 88 行冻结字面量由 --dump 机器生成"声明成立。

## 2. 函数边界与调用点独立重导 — CONFIRMED（13/13 全查，超出抽 3 要求）

`_crev_engine.py` 自有引擎（自写 PE 解析、线性解码 **1,394,120** 条对齐指令、**6,719** 个对齐 E8 头、自写 pred 图（jcc 双边/jmp 仅 taken/ret 断边）、自写反向 BFS；**不 import 门禁模块**）：

- **13/13 宿主**：`reach(site) ∩ E8头集 == {host}` 全部单例成立；caller 计数 **757/2/5/7/1/306/650/67/5/3/0/651/3** 与书 §1 表逐值全中。被抽验三点：
  - `0x5283D0`：heads-in-reach={0x5283d0}，cnt=**306** ✓，头签名 `83ec0c33c053` ✓；
  - `0x5276D0`：heads-in-reach={0x5276d0}，cnt=**757** ✓，头签名 `83ec0c33c053` ✓；
  - 冷入口 `0x5293E3`：E8 头集=∅、cnt=**0** ✓；冷头 `0x529394` 字节=`33c03bf00f84` ✓；全镜像 `jmp→0x529394` **仅 `0x52949C` 一处** ✓；`0x529394 ∈ reach(0x5293E3)`（尾跳入边活）✓；冷块**不**在 `0x529160` 站点 reach 内（书"0x529160 闭包不含它"）✓。
- 交叉验证（前向 BFS，调用边不跟随）：三宿主 `site ∈ fwd(host)` 均真，地址相邻头**零泄漏**。

## 3. 88 caller 分类：完整性/互斥/求和/字节 — CONFIRMED

自有分类器（自写 ret 框定 + 寄存器链回溯，同文档语义、异实现）：

- **求和与互斥**：verdict 直方图 = {param-slot 54, stack-object 17, local-slot 1, param1-forward 3, unknown-reg 12, unknown-thunk 1}，**sum=88**；逐 caller 单一 verdict（互斥由构造保证）；walked 集合 == CHAIN 键集合（**完整性**，无多无漏）。
- **88/88 行** verdict 与链字节序列同 `CHAIN` 冻结字面量**全等**（mismatches=0）；并对**全部 88 行**做了"自有导出写者地址 → 盘上原始字节 == 冻结链 hex"三方核对（`rd()` 直读文件），**0 差**——超出抽 10 行要求。
- **param1-forward 3 行（0x68A754/0x68A772/0x68A790）定性**：五钉独立全中——F 头 `0x689E90` 前 10 字节=`558bec83e4f883ec3453`、F 唯一 E8 caller=[0x687853]、`8b7d08`@0x689E9C（caller 帧 `mov edi,[ebp+8]`＝arg1）、G 帧 `8b7c2418`@0x687744、F 帧 `[esp+0x18]` 写者=0。定性"caller 第一参数原样转发"成立；书内明记"身份仍不命名/UNKNOWN 保留"，**无过度**。
- **unknown-reg 12 行**：自有扫描同判"链死在入向 callee-saved（帧内无写者）"；书内"再上一跳未穷尽＝UNKNOWN 保留"——**无不足**（未把可继续上行的行写成定论）。
- **param-slot 过度认定审计**：55 行（param-slot 54 + local-slot 1）帧内对 verdict 槽的 `lea`（取址传引用）命中 **0/55**——本轮未发现"零写入但实为被 callee 经引用写"的反证形态。（残余局限见 §11。）

## 4. GenericList 构造证据 — CONFIRMED（1 处标题级措辞红项，见 §8）

- **三窗 8 字节钉**（盘上直读）：`0x7787C0`=`c7442438041b7e00`、`0x779BB3`=`c7442424041b7e00`、`0x779E33`=`c7442424041b7e00`——`mov dword ptr [esp+X], 0x7E1B04` 形态全中 ✓。
- **自有 RTTI 链 walk**：`[0x7E1B00]`=COL 0x7FAD18 → `[COL+0xC]`=TD 0x817508 → TD+8 名=**`.?AVGenericList@@`** ✓；控制位：`[0x8174C8]`=0x7F9594 ✓，且 0x8174C8 实为 **CCINIClass TypeDescriptor 起点**（TD+8 名=`.?AVCCINIClass@@`，首 dword 即其 vfp 0x7F9594；GenericList TD 0x817508 与之相邻 +0x40）——书内"控制位 CCINIClass TD 0x8174C8 vfp 0x7F9594 同 walk 复现"属实。
- **5/12 划分如实**：自有帧内槽写普查（17 个 stack-object 行全查）：**恰 5 行**帧内存在 vptr store——0x77884F/0x77890C/0x778956（slot 0x38，共用 store 0x7787C0）、0x779C3D（0x779BB3）、0x779EBD（0x779E33）；**其余 12 行帧内对该槽零 dword 写**（含 reg 形态 `89 44 24 xx` 也无）——书内"5 行有帧内构造证据 / 12 行裸传"逐行核实。12 行"构造点未证，不编故事"**如实保留**，未发现把未证明行写成已证明。
- lea 邻接：17/17 行 `lea ecx,[esp+slot]` 紧邻 call（0 违例）✓。

## 5. 负命题的阳性对照 — CONFIRMED

- **caller-self = 0/88**：同一自有分类器跑五个直传宿主，caller-self 命中 **0x5276D0=4 / 0x528A10=31 / 0x5295F0=5 / 0x5283D0=11 / 0x528F00=0，总 51**——与书 §4.3 "4+31+5+11+0=51（0x528A10 高达 31）"逐值全中。检测器能看见该形态 ⇒ SMALL 宿主 0/88 是有检测能力在场的真结果。
- **global-load = 0（跨 7 SMALL）**：同检测器五直传宿主命中 **164/90/118/3/2**，与 R-061 冻结 E-hist（119+45 / 80+10 / 95+23 / 3 / 2）逐值全等 ✓。另以 strict 变体（任一 ecx 写者截停）复算 hist，五宿主仍全等——结论对该启发式不敏感。
- R-061 侧负命题 `D-2C-absent-527f20` 的阳性对照=注入式 killer（往 0x527F20 窗口注入 `mov esi,0xB7882C` 即红），本轮套件复跑 EXACT 在案。

## 6. 诚实账 — CONFIRMED（无 UNKNOWN 静默升格）

逐条核对（行号引 `r061_witness_this.md`/`r062_upward_trace.md`）：

- R-061 §3"转参=UNKNOWN…**保留 UNKNOWN，不外推**"（L76）；§4 一一对应未闭合/冷块身份未展开/0x528220 thunk 再上跳 UNKNOWN/"不宣称任何可改写点；未真机"（L86-92）；R-062 §5"实例归属仍是 UNKNOWN…17+1 是类型命名不是实例身份"（L92-95）。**均如实保留**。
- **BSS 未读如实**：自有段表核实 `0xB7882C/0xB78830` 落 `.data`（VA 0x812000..0xB79BE4）但 fileoff 0x77882C **超出 raw 界 0x47E000** → 盘上确不可读（书"现值不可读（BSS）"属实）。
- **工厂件→见证连线未证**：书 L78"其结果流向未见直写任何 [G+8]（K4 实测空）⇒…未证，不连"；R-062 §2 推论段明确"机制推论（不升格为结论）…实例归属账不变（UNKNOWN 保留）"。
- **caller-self 51 行未展开**：R-062 §5 明记"超出本件 7-SMALL 范围，登记不穷尽"。
- **六全局 [+8] 构造器清零旁证**（本轮自有普查）：全镜像 `mov [imm32],reg` 直写命中 GLOBAL+8 者**恰 6 站**（0x40DFBE→0x887188、0x40E06E→0x887210、0x40E11E→0x887130、0x40E1CE→0x887060、0x40E27E→0x8870C8、0x49B39E→0x89F520），全在书 L80-81 所指清零簇内；各簇首 `53 33 db`=push ebx;xor ebx,ebx ⇒ **ebx=0 → [+8] 初值恒 NULL 成立**；`c7 05` imm 形态对 G+8 直写=0 站。（注：书列 12 址为 [G+4]/[G+8] 成对站，+8 位是每对第二址，语义一致。）

## 7. R-061 推翻案（R-059 §2③）抽验 — CONFIRMED（4/4，超出抽 1）

自有引擎四 spill 址全查：

```
0x5275CC bytes=8bf1 'mov esi,ecx'  below-head(0x5276D0)=True  in-reach(0x527750 站)=False
0x527B97 bytes=8bf1                 below-head(0x527CC0)=True  in-reach(0x527D5B 站)=False
0x528DF2 bytes=8bf1                 below-head(0x528F00)=True  in-reach(0x528F97 站)=False
0x52A623 bytes=8bf1                 below-head(0x52A760)=True  in-reach(0x52A7DE 站)=False
```

`0x5275CC` 实字节确为 `8bf1` 且位于对齐闭包外——R-059"线性窗跨函数污染、4 个 `mov esi,ecx` 实为前驱函数尾段"的推翻有**字节+可达性双重支撑**；R-059 探针 `8bce/8bf1` 记混的纠正（`8bf1`=mov esi,ecx）与 capstone 解读一致。

## 8. 出入与红项清单

| # | 级别 | 内容 |
|:--|:--|:--|
| 红-1 | **红项（措辞，工件级数字无误）** | R-062 书 §2 标题"0x528C00 的**三分之一** this 是 caller 栈上 GenericList 临时件"：实测 17 stack-object / 67 总 caller = **25.4%（约 1/4）**。正文数字（17 行、67 caller）正确，仅标题比例夸大。建议升格办理时顺手勘误为"约四分之一"。 |
| 题-1 | 题面勘误 | 复核任务书写 `out/_r061_freeze.json`，盘面实件为 `out/_r061_freeze5.json`（哈希 `6330e5de…` 对上；证据书 §5 与套件内名称一致）——任务书笔误，非工件缺陷。 |
| 观察-1 | 非缺陷 | R-062 清单件内 `round=1` 与书 §3"round-2 校准"表述不一致：溯源为 round-2 校准**复用 round-1 脚本**（`out/_calib_r062_mut1.py` L201 以常量 `round:1` 写清单）就地修复后重跑，`_r062_mut_calib2.txt` 内嵌 JSON 与冻结清单逐字节全等——字段名与轮次语义错位，数据链无恙。 |
| 观察-2 | 非缺陷 | R-062 §1 表把 param-slot 语义表述为"该帧对 X 零写入 ⇒ X 是**入向 cdecl 参数槽**"——从"零写入"到"入向参数"含一步推断（理论上 callee 经引用写未排除）；本轮 55 帧审计未发现 `lea` 取址反证，且书内已用"身份不命名/UNKNOWN"兜底，判可接受。 |
| 自记-1 | 复核员自记 | 本轮我方探针先后两次 bug（`fo()` 误以 RVA 比 VA 致 `rd()` 读错节；vptr 切片 `[6:14]` 应为 `[8:16]`），均已修正重跑；首跑的 133 条 RAWBYTE"假红"与 0 行"构造证据"皆为我方缺陷所致，**非工件问题**，如实登记以保证透明。 |

## 9. 总判定

- **R-061（re_atlas/evidence/r061_witness_this.md + 门禁 194 断言 + 冻结套件 194 例）：维持冻结候选所载全部断言成立，建议升格。**
  仍缺项：① 异族通道复核在本轮仍以"同族降级"替代（通道登记在案；若章程把 out-of-family 作硬条件，则该项仍开）；② 真机/运行期行为（BSS 现值、命中缓存实际填充序列）不在静态范围，书内亦未宣称。
- **R-062（re_atlas/evidence/r062_upward_trace.md + 门禁 126 断言 + 冻结套件 112 例）：维持冻结候选所载全部断言成立，建议升格。**
  仍缺项：① 同上异族通道项；② 12 裸传行构造点、51 行 caller-self 再上行、param-slot"零写入⇒入参"的寄存器间接写路径——书内均已如实登记为未证/不穷尽，不构成升格障碍；③ 红-1 标题比例措辞建议随升格一并勘误（不影响数据）。

## 10. 本轮实测落点汇总（供 Leader 核对）

- 门禁：R-061 `== 194/194 PASS ==` EXIT=0；R-062 `== 126/126 PASS ==` EXIT=0。
- 套件：R-061 194/194 exact、EXIT=0；R-062 112/112 exact、EXIT=0（均 splice+full 双路、uncovered/phantom=0）。
- 冻结链：套件字面量↔清单 194+112 三字段全等；run1↔清单全等；校准输出↔清单逐字节全等；`--dump`↔CHAIN 88 行全等。
- 自有引擎：13 宿主边界/计数全中；88 行分类与字节全中；GenericList 5/12 划分与三窗字节+RTTI 全中；阳性对照 51 行与 164/90/118/3/2 全中；推翻案 4/4 成立；六全局 G+8 直写普查 6 站+ebx 清零成立；BSS 不可读成立。

## 11. 局限

1. **同族降级**：异族通道不可用，本轮为同模型家族全新上下文 fresh-eyes；"通道异族性"意义上的 out-of-family 仍未满足，是否据此升格由发起线章程裁定。
2. **静态复核**：未真机、未运行游戏；运行期值（BSS、缓存填充）不可判，书内亦未宣称。
3. 变异套件复跑为全量双路（非抽样）；但我方未对每例的"红集预期"另行独立重推——预期真源仍为冻结清单（其与校准输出/套件字面量/run1 的四点全等已由 §1.3 闭合）。
4. 自有边界引擎与门禁同属"线性对齐扫描"域：若存在仅由非对齐字节序列进入的第三形态入口（如冷区之外的垫片），该方法域可能同盲；本轮以冷入口 `0x5293E3` 样本+前向 BFS 交叉验证覆盖了已声明的形态，未穷举全部 6,719 头的前向验证。
5. param-slot 的"入向参数"语义残差：帧内零写入+零 `lea` 取址仍不能排除 callee 经 `mov reg,esp` 派生指针写入的极端形态（本轮未发现任何此类形态，55 帧零命中）。

## 12. 探针与捕获件清单

`re_atlas/tools/_crev_recon.py`（对账）· `re_atlas/tools/_crev_engine.py`（自有引擎）——仅此两个临时脚本；门禁/套件输出经控制台/系统临时目录捕获，未落工作区；生产文件零改动（全部哈希已于文首/文中读回）。

---

## 13. OOF 勘误补记（2026-10-29，Leader 依异族复核 r061_r062_oof_review_20261029.md 红-2/红-3/红-4 代录）

- 红-2：§1 代码块中 `G61_EXIT=0`/`G62_EXIT=0` 非脚本输出行，系复核时 shell `$?` 记录——表述级更正，
  不影响 EXIT=0 判定本身。
- 红-3：§3「55 帧 lea 取址审计 0/55」的探针 `_crev_engine.py:430/434` `startswith("[esp")` 对 capstone
  渲染 `eax, [esp + 0x38]` 恒假（Leader 已独立复现）——该处为恒真式空转；异族复核员以逐指令 esp 追踪
  （含未弹出 push、callee ret imm16 清理）正确重算，address-taken 命中确为 0，**结论碰巧为真**，
  param-slot 判定不受影响；本条如实登记探针缺陷。
- 红-4：§0 表中 `mutate_r061_gate.py` 哈希「无宣称」不实——LEDGER.md:6619 有记
  `89a7956f…4cc4e3`（本轮 Leader 实测同值）。
- 本报告 §9「建议升格」已获异族对账级复核支持并办理，见 LEDGER 升格收口段。

---

## 14. 判据局限限定注（2026-10-30，Leader 依 R-064 裁定书代录·台账 §471）

§4「GenericList 构造证据 — CONFIRMED」的复现对象=**字节与『同字面槽』判据下的 5/12 划分**，
非物理槽配对——R-064 仲裁（r064_rtti_naming_adjudication.md §3）以 esp-D 归一化判定 witness 槽
实为 INIClass stamp（错位恒 0xC），「GenericList 栈件」定名被推翻；本报告字节级结论（三窗 8 字节、
RTTI 链名）仍真。判据局限已由 R-064 更正。
