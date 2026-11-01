new-provider-3/qoder-cn:qfmodel

# R-061 独立核验报告（RE-ATLAS 线 · R-061 轮 · 冻结候选核验）

- 核验员：ZCode agent（全新上下文；**同模型家族降级**——异族通道 persona 派发失败，纪律禁绕，如实登记）
- 核验时间：2026-10-26（UTC+8 本地）
- 纪律：只读镜像；探针仅写入 `out/_review_r061_*`；本报告仅写 `re_atlas/evidence/r061_independent_review.md`；未触碰 `out/_r061_freeze_run1.txt`（后台在跑，仅记录其存在，未作证据）；未 commit；未起第二个全量套件。
- 全部哈希/字节/计数均为本人亲自读回（Python312 + capstone 5.0.7，PE 段表亲自换算：ImageBase=0x400000，.text VA=0x401000 RawPtr=0x1000 RawSize=0x3E0000，与门禁同界 [0x401000,0x7E1000)）。

---

## R1 三哈希实测 — CONFIRMED

```
$ sha256sum re_atlas/tools/r061_witness_this_contract.py out/_r061_freeze5.json ra2youli/gamemd.exe
3080309aa23e194e63601603a6527abe988502710de942995968d2bea121ebfc  r061_witness_this_contract.py   # 应值一致
6330e5de64d5edf624771ef6eb0caeb2a39cbb3191e57d0c213deb1056c03ca8  _r061_freeze5.json              # 应值一致
73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476  gamemd.exe                      # 应值一致
```
另：freeze5.json 件内 `gate_sha256`/`image_sha256` 字段与上两值逐字一致；`round=5`，`status="FREEZE-CANDIDATE (pending out-of-family independent review)"`，`tally={killed:194, survived:0, exc:0, mismatch:0, uncovered:[], labels:194, covered:194}`。

## R2 门禁全量复跑 — CONFIRMED

```
$ python re_atlas/tools/r061_witness_this_contract.py   # 工作目录 D:\Project\ra2-campaign-forge
...（194 行 PASS，A/B/C/D/E/F/G 七组）
== 194/194 PASS ==
EXIT=0
```
捕获件 `out/_review_r061_gate_rerun.txt`：`grep -c '^PASS'`=194，`grep -c '^FAIL'`=0，尾行 `== 194/194 PASS ==`，exit 0。与声称一致。

## R3 字面量对账（CASES 表 vs 冻结清单） — CONFIRMED

`out/_review_r061_r3_reconcile.py`（AST 提取 `CASES` 字面量，不执行套件），逐例比对 (case, mut{址:字节}, red 集合) 三字段：
```
cases compared: 194   problems: 0   RESULT: 194/194 MATCH
duplicate literal names: []
```
要求 194/194 三字段全等：成立，零出入。（对账时 `mutate_r061_gate.py` sha=89a7956f…，与文档§5 所述"转录落盘"时间线一致；该文件不在 R1 应值清单内，其预期红集真源=freeze5.json，已逐字节核对。）

## R4 关键逆向断言独立重导 — CONFIRMED（两处题述措辞出入，见 c/d 注记）

### R4a 站点 `mov esi,[reg+8]` 字节 — CONFIRMED（超出"任选3"，13/13 全查）
`out/_review_r061_r4_raw.py`（手工 PE 偏移 raw 读）+ `out/_review_r061_r4_closure.py`（自解码反汇编双重）：
```
site 0x527750 load@0x5276FE 8b7308 OK   decodes 'mov esi, dword ptr [ebx + 8]'
site 0x5279BD load@0x52796B 8b7508 OK   'mov esi, [ebp + 8]'
site 0x527D5B load@0x527D03 8b7508 OK
site 0x527FD1 load@0x527F78 8b7508 OK
site 0x5282A0 load@0x52824E 8b7308 OK   site 0x528450 load@0x5283FE 8b7308 OK
site 0x528AA7/CB7/F97/1F3/3E3(0x529391)/66E(0x52961C) 均 OK
site 0x52A7DE load@0x52A766 8b742420 'mov esi, dword ptr [esp + 0x20]'  # 文档已声明的栈参例外，属实
```
注：题述"站点处确为 8b7308/8b7508"——站点地址本身实为 `call 0x52B4F0`（raw 独立验证 0x527750 处 e8 位移解出目标 0x52b4f0），`mov esi,[reg+8]` 在门钉的宿主内 load 址；`0x52A7DE` 是文档明载的栈参形态例外。字节事实与文档/门禁完全一致，非工件缺陷。

### R4b 自实现后向闭包（ret 不跨 / jmp 只走 taken / jcc 两路） — CONFIRMED
自有 pred 图 + BFS（`out/_review_r061_r4_closure.py`，独立解码 1,394,120 条对齐指令、6719 个 E8 目标，未引用门禁 `breach`）：
```
13/13 站点中 12 个：closure(site) ∩ E8头集 == {声称宿主}（单例，非空）
  例：0x527750→{0x5276d0}  0x5279BD→{0x527920}  0x52966E→{0x5295f0}  0x52A7DE→{0x52a760} ...
唯一例外 0x5293E3：E8 头集=∅ —— 与文档 §1"冷头 0x529394 非 E8 目标、入边=0x52949C 的 jmp"独立复现一致：
  raw 扫描：E8→0x529394 计数=0；E9→0x529394 仅 ['0x52949c']；0x529394 ∈ closure(0x5293E3)=True；
  冷头字节 @0x529394 = 33c03bf00f84（与 COLD_HEAD_BYTES 钉值一致）。
门禁对该例的断言形态=可达性+字节钉（非单例E8），与我的实测吻合。
各站点 cache-load 址均 ∈ 自有闭包（load 可达站点：True×13）。
```

### R4c 0x5283D0 宿主 RA2MD-only — CONFIRMED（题述"push"应为"mov ecx,imm32"，措辞出入，工件无恙）
```
[own] 对齐 caller 总数 = 306                     # 与 E-cnt-5283d0 钉值一致
[own] 同块 `mov ecx,0x8870c0`(b9 c0 70 88 00) + call 0x5283D0 的 caller 恰 3 个：
      0x5FA9C8 / 0x5FAA28 / 0x5FAA9D
  阳性上下文（raw hex）：caller 0x5FA9C8 ctx: ...68b4308300 e803daf2ff，
      mov ecx 址=0x5FA9B3（b9 c0 70 88 00 实测 @0x5FA9B3..B8=b9c070880088）
题述"直查 push 0x8870c0 + call"：`68 c0 70 88 00` 全镜像仅 6 处（0x698446..0x6991F4），
均非 caller 上下文（后续字节 8d，非 call）→ 直查 push 得 0，直查 mov ecx 得 3。
判定=题面把 ecx 装载的编码形态写错；文档/门禁记载正确（hist 读的就是 mov ecx）。
```

### R4d 工厂 0x52CB90 两调用点 — CONFIRMED（push 为 imm8 短形态 6A 58，非 68 58 00 00 00；文档/门禁记载为真）
```
@0x52CBFB (7B) = 6a58 e815c22900  → push 0x58; call rel32 → 目标 0x7C8E17
@0x52CCDB (7B) = 6a58 e835c12900  → push 0x58; call @0x52CCDD → 目标 0x7C8E17（与 F1 同一 operator new；
      rel32=0x0029c135 @0x52CCE2 独立解出，修正首跑探针位移读取偏移后的复测值）
（题述字面 68 58 00 00 00 不出现；6A 58 语义=push 0x58，call 紧随其后——实质断言成立）
附带独立复核：F3 @0x52CC36= c706f41a7e00（vptr 0x7E1AF4）；F4 工厂 caller 用两种独立方法数：
  raw E8 位移扫描=[0x52c605,0x52df25,0x52e0c4,0x685609] 与自有对齐流 caller 集完全一致，count=4。
```

### R4e R-059 病根复证 — CONFIRMED（阴性命题带阳性对照）
自有闭包引擎（R4b 同引擎）：
```
spill 址  0x5275CC:8bf1 'mov esi,ecx'  below-head=True  in-closure(0x527750)=False  cache-load-in-closure=True
spill 址  0x527B97:8bf1  ...           in-closure(0x527d5b)=False   （0x527B97<0x527CC0）
spill 址  0x528DF2:8bf1  ...           in-closure(0x528f97)=False
spill 址  0x52A623:8bf1  ...           in-closure(0x52a7de)=False   （0x52A623<0x52A760）
阳性对照（内存副本 bytearray，不落盘）：把 0x5275CC 覆为 jmp 0x527750 后，
  spill ∈ closure(0x527750) 翻为 True；基线为 False ⇒ "无路径进入站点"是图事实、非恒真。
  ⇒ => negative claim is graph-backed, not vacuous: True
```

### R4f 冻结变异抽测（A 类 + E 类各 1，双路） — CONFIRMED
`out/_review_r061_r4f.py`（期望只读 freeze5.json；门禁 import 复用 build 机器，闭包/计数判定已由 R4b/e 自有引擎旁证）：
```
baseline red-set: []（全绿）
case A-527750        mut={0x5279e8:64,0x5279e9:fd,0x5279ea:ff,0x5279eb:ff}
  frozen exp=['A-527750']  splice=['A-527750']  full=['A-527750']  MATCH-EXACT: True
case Eh-5283d0-g8870c0 mut={0x5fa9b4:0xc1}
  frozen exp=['E-hist-5283d0']  splice=同  full=同  MATCH-EXACT: True
反证控制：A-cold 真红集=['A-cold-5293e3','A-sig-529394'] ≠ 故意错配的期望['A-527750'] → 期望比对非恒真。
补测：对 Eh-5283d0 改用另一翻法（同址 0x5fa9b4 翻成 0x90=nop 而非字面的 0xc1），splice/full 均只红
  ['E-hist-5283d0']，与冻结红集相同——说明该断言读的确实是 ecx 全局值装载本身（两种破坏方式殊途同归），
  且冻结期望并未过拟合到"仅 opcode 翻 c1"这一字节形态（登记为观察，非缺陷）。
```

## R5 套件源码层核验 — CONFIRMED（守卫全部活体演示，未起全量）

`re_atlas/tools/mutate_r061_gate.py` 源码逐项 + `out/_review_r061_r5/` 沙盒演示（gate/manifest 的**副本**扰动，生产件未动）：
| 要求 | 源码位 | 活体演示 |
|---|---|---|
| STALE 三哈希守卫 exit 3 | L52-63（gate/image/manifest 依序） | 扰动 gate 副本字节→`STALE: gate bytes…` exit **3**；扰动 manifest 副本→`STALE: out/_r061_freeze5.json changed…` exit **3**（秒级返回，不进全量） |
| 基线非全绿 exit 2 | L298-302 | 在 gate 副本里翻一处 HEAD_SIG 钉值→`BASELINE NOT GREEN (193/194) -- abort (ruling 3)` exit **2** |
| 每例双路 splice+full+精确红集==字面量 | L307-326（`red_sp!=exp`/`red_fu!=exp` 分账 mismatch_sp/fu） | R4f 两例双路实测吻合 |
| survived/mismatch/exc 分账 | L305/311-326/338-342 | 源码读回成立 |
| G-79 尾段双向对账，uncovered∨phantom⇒exit 1 | L331-351（`unc`、`phantom`、`ok and …`） | 我用自有标签集独立复算：gate 194 标签 vs CASES 字面量覆盖 → uncovered=[] phantom=[]（双向零差） |
| splice 增量路径真实性 | `build()` L290-292（re-sync 失败回退全量） | 随机 12 例+定向 8 例共 20 例 `_splice` 全部 resync 成功（无静默回退），增量路径非虚设 |
恒真/不读字节扫描：全部 `ok(...)` 判据为精确 `==`（字节 hex、整数计数、集合相等），无 `>=`/存在性阈值；hist/kinds 用"同块、call/ret/jump 截断、40B 窗"有界回溯（启发式但被逐例字节 killer 覆盖）。**形态弱点登记（非缺陷）**：① B4 为"site 前 12B 窗内任一指名列"式定位，未钉死地址——round-5 校准逐例单字节即红，实测无可满足邻字节；② `hist_global`/`kinds` 取窗内**首个** ecx 写者（首中即停），同块双写场景未钉语义，冻结集未含此类场景。

## R6 诚实账抽查 — CONFIRMED

`re_atlas/evidence/r061_witness_this.md` §3/§4 grep 全查：
- §3 七转参宿主明确"**保留 UNKNOWN，不外推**"；0x52A760 arg1 再上跳"未证⇒记 UNKNOWN"；工厂件流向"未证，不连"；注册表现值"不宣称「兜底必经」"；栈上包装对象"**其类型名未证**（排后）"。
- §4：闭合缺口（一一对应未闭合）、冷块整体身份未展开、0x528220 再上跳 UNKNOWN、"不宣称任何可改写点；未真机"、"复核通过前只记冻结候选，不作定谳表述"、异族降级如实登记（§5 末段）。
- 全文未把 UNKNOWN 写成已证；"定谳"仅用于 R-059 未受影响项（G-79 首轮/恒真式两改/析构表/R-058），属既存结论沿用，非本轮升格。**未发现宣称可改写点。**
- 我另做盘上旁证：六全局 [+8] 槽与 0xB7882C/30 在 .text 之外（.data RawSize=0x6C000 界外=BSS 零填充）——"盘上不可读、运行期写"表述与文件实况相符。
- 轻微观察（不构成出入）：§3"堆栈对象"行"这些 this 是含 [+8] 槽的栈上包装对象"是**推断**（依据=栈槽无 INI vptr 盖写），件内已自带"类型名未证"限定。

---

## 总判定：**PASS**

R1–R6 全部 CONFIRMED。三工件哈希对值、门禁 194/194 绿 exit 0、字面量 194/194 全等、关键逆向断言经自有引擎（自写解码/pred 图/闭包/直方图，未引用门禁机器）独立重导成立、套件源码守卫四类扰动全部按预期红/挡、诚实账无升格。未发现需整改的工件缺陷；两处出入均为**核验题面措辞**（"push"实为 `mov ecx,imm32`；push 0x58 用 `6A 58` 短编码），文档与门禁记载本身正确。

### 本核验的局限
1. **同族降级**：异族 persona 派发失败，本核验为同模型家族的全新上下文 fresh-eyes；独立性来自上下文隔离+亲自取证，覆盖面窄于计划的异族核验（裁决 6 的"out-of-family"条件在**通道异族性**意义上仍未满足——是否升格由发起线章程裁定，本件仅如实登记）。
2. 194 例全量 killed 判定未由我端到端复跑（题面禁止第二全量实例；后台 `out/_r061_freeze_run1.txt` 仅见 46/194 行在跑，我未用作证据）。我的复跑=全量门禁（R2）+ 2 例双路冻结变异 + 20 例 splice-resync 抽样 + 4 例活体扰动演示 + 双向标签对账全量复算。
3. R4 抽测站点/宿主/案例为"任选"，未逐一穷举 13 宿主全断言（E-hist 其余 4 宿主、D-2C/D-30 全 26 址、G 组 26 断言仅经门禁全绿+抽样旁证，未独立重导计数）。
4. 运行时行为（真机、命中缓存实际填充序列、BSS 现值）不在静态核验范围，文档亦未宣称。

### 探针与捕获件清单（全部前缀合规）
`out/_review_r061_gate_rerun.txt` · `out/_review_r061_r3_reconcile.py` · `out/_review_r061_r4_raw.py` · `out/_review_r061_r4_closure.py`(+`.out`) · `out/_review_r061_r4f.py`(+`.out`) · `out/_review_r061_r5/`（gate/manifest/suite 的扰动副本与沙盒件；生产文件全程未改动，sha 已于文首/文中读回）
