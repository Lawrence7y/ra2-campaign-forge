# R-061 · 2026-10-26 — 见证 `this` 调用图上行（C26-04 主任务）

对象：`gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（只读）。
全部常量由 `out/_probe_r061*.py` 机器转储先行（G-65）。门禁
`tools/r061_witness_this_contract.py` **194/194 PASS**；变异 round-5 已跑毕、套件已转录（见 §5；全量复跑与独立复核在途）。

## 0. ★ 被推翻项（章程 §8 逐条列）

**R-059 §2③ 的三分归类不成立**：「13 近端站点 esi 首写者 = 4×`mov esi,ecx`（跨过程）
/ 7×`[esi+0x10]`（容器链自遍历）/ 2×栈参」。

- **根因**：R-059 探针用 `call_va − 0x200` 的**线性窗口**找「首个 esi 写者」。本区
  **零 nop 填充**（R-058 §6.1 自己就警告过），窗口越过函数边界，读到的是**上一个函数
  序言**的 `mov esi,ecx`（this 保存进 esi 的惯用序言）。四处「`mov esi,ecx`」写者
  `0x5275CC / 0x527B97 / 0x528DF2 / 0x52A623` 全部位于各自宿主的**分支图头地址之下**
  （C-spill 断言把这一点钉成字节+可达性双重证据：那四处确实写着 `mov esi,ecx`
  （`8bf1`——R-059 探针还把 `8bce`/`8bf1` 的 mnem/op 对应记混，本线复核纠正），
  且分支图上**无路径**进入见证站点）。
- **正确分类**（分支图定界后）：**13/13** 站点进 twin 前的 `esi` 都来自
  **`mov esi,[reg+8]` 缓存加载**（`8b7308` / `8b7508`；唯一例外 host `0x52A760` 的
  esi 来自栈参 `[esp+0x20]`——宿主自己的 arg1，随后 `[ebp+8]` 路在 call-site 0x689E90
  的形参转链再上一跳未证 ⇒ 记 UNKNOWN）。
- **未受影响**：R-059 的 G-79 首轮对账、恒真式两处改写（C6/D2）、`0x7E1AF4` 析构表
  定谳；R-058 全部结论；「13 近端站点」集合本身（NEAR 表与孪生不对称 F 组）——
  本件只是**重读同一 13 站**并纠正其 this 通道分类。

## 1. 宿主边界（分支图闭包，非首ret非nop）

方法：头候选 = 对齐 E8 call 目标 ∪ PE 入口；对 `[site−0x4000, site]` 每个候选做
前向闭包（jcc taken/fallthrough、`jmp` 仅 taken、`ret` 无续边），**包含判定** = 站点∈闭包；
A 组断言用**反向 pred 可达 ∩ E8 头集 == {host}**（比前向闭包更严：任何别处的 5 字节
`E9` jmp 重定位进窗口都会红——M 组实测如此）。

| 站点 | 宿主（唯一） | 宿主 6 字节序言 | 对齐调用者 |
|:--|:--|:--|--:|
| 0x527750 | 0x5276D0 | `83ec0c33c053` | 757 |
| 0x5279BD | 0x527920 | `81ecac010000` | 2 |
| 0x527D5B | 0x527CC0 | `83ec64538d44` | 5 |
| 0x527FD1 | 0x527F20 | `83ec7853558b` | 7 |
| 0x5282A0 | 0x528220 | `83ec0c33c053` | 1 |
| 0x528450 | 0x5283D0 | `83ec0c33c053` | 306 |
| 0x528AA7 | 0x528A10 | `83ec0c33c053` | 650 |
| 0x528CB7 | 0x528C00 | `81ec18040000` | 67 |
| 0x528F97 | 0x528F00 | `b814500000e8` | 5 |
| 0x5291F3 | 0x529160 | `81ec14040000` | 3 |
| 0x5293E3 | **0x529394（冷）** | `33c03bf00f84` | **0**（入边=0x52949C 的 `jmp`） |
| 0x52966E | 0x5295F0 | `83ec0c33c053` | 651 |
| 0x52A7DE | 0x52A760 | `83ec10535556` | 3 |

- `0x5293E3` 多入口冷块（0x529394 非对齐头、被 0x52949C 尾跳入、`0x529160` 闭包不含它）。
  C26-04「不能在首ret或无NOP处凭直觉断边界」的实例：**冷区** 0x529350 起一段的
  真实入口就是这种 E9 落点。诚实登记，不并入常规档。
- 十三宿主共享**同一形状**（+0x10 命中缓存 cmp/fill 对、`add esi,0x2c` 重基址、
  twin-A 调用、`mov [reg+8]` 自缓存回填）⇒ CCINIClass 访问器家族（H-045/H-046）。

## 2. 见证协议（13 站统一）

```
mov esi, [reg+8]        ; 缓存的 CCINIClass*（唯一例外 0x52A760：esi=arg1）
mov ecx, [esi+0x30]     ; 容器元素数（0x527FD1 走 helper 路，无此 mov）
add esi, 0x2C           ; 重基址：esi := &容器头
[查 [esi+0x10] 命中缓存：cmp [ecx],eax @site-0xb（0x527d5b 在 site-0xe；
 0x527fd1 用 call 0x52B4D0 helper），未命中则]
mov ecx, esi ; push &key ; call 0x52B4F0
mov [esi+0x10], eax     ; 回填命中缓存（site+0xd，`894610`，13 站全同字节）
```

## 3. `this` 实例归属（本件主结论表）

`this`（=进 twin 的 ecx = 宿主入参 ecx）来源分档，caller 直方图**全为精确钉值**：

| 档 | 宿主 | 证据 |
|:--|:--|:--|
| **六全局直送** | 0x5276D0：Art 119 / RA2MD 45；0x528A10：Art 80 / RA2MD 10；0x5295F0：Art 95 / RA2MD 23；0x5283D0：RA2MD 3；0x528F00：RA2MD 2 | 同块（call/ret/jmp 前）`mov ecx,<global>` 计数=钉值（E-hist）；caller 总数=钉值（E-cnt） |
| **堆栈对象** | 0x5276D0/0x528A10/0x5295F0 各有一批 `lea ecx,[esp+N]` caller（如 0x545575→宿主函数 0x545150） | 该栈槽无 INI vptr 盖写 ⇒ 这些 this 是**含 [+8] 槽的栈上包装对象**；其类型名未证（排后） |
| **转参=UNKNOWN** | 0x527920/CC0/F20/8220/8C00/9160/A760（7 宿主）**无任何** global-direct caller；kind 直方图=钉值（E-kind），如 0x52A760 = {reg:edi:3} | 上溯一跳（caller 的 caller）后仍到寄存器形参为止的未证 ⇒ **保留 UNKNOWN**，不外推 |
| **兜底注册表** | 全 13 宿主尾段各一处 `mov esi,0xB7882C`/`0xB78830`+`mov esi,[esi]`（D-2C/D-30 逐址钉）；0x527F20 的 2C **缺失钉为负命题**（D-2C-absent 注入即红） | 注册表 dword 现值在 `.data` 零填充区（盘上不可读），值=运行期写；**不宣称**「兜底必经」 |
| **堆工厂** | 0x52CB90 两处 `new(0x58)`（0x52CBFB/0x52CCDD）+ `mov [esi],0x7E1AF4`；4 调用者 0x52C605/52DF25/52E0C4/685609 | 其结果**流向**未见直写任何 [G+8]（K4 实测空）⇒「工厂件=见证 this」**未证**，不连 |

**六全局直接写 +8 的站点**：仅全局构造器清零簇（0x40DFB8/BE、0x40E068/6E、0x40E118/1E、
0x40E1C8/CE、0x40E278/7E、0x49B398/9E，F 类钉）⇒ **六全局的 [+8] 初值恒 NULL**；
运行期由宿主内 `mov [reg+8],reg` 自缓存回填（D-fill 八站钉 + 各宿主尾段模式）。

## 4. 诚实账

1. 见证↔实例**一一对应仍未闭合**：本件闭合的是「通道分档 + 计数钉值」，
   转参宿主的最终实例=UNKNOWN（静态到形参为止，不猜）。
2. `0x5293E3` 冷多入口：宿主函数**整体身份**未展开（谁跳入它、跳入条件=0x529394 的
   `je` 语义=空缓存检查），本轮钉字节+可达性，不宣布覆盖。
3. `0x528220` 唯一 caller 0x474A5F 处 ecx 写者距 call >40B（窗口=none-in-window 钉值）：
   该 caller 是 thunk 形参转发（0x474A21 `mov esi,ecx`），**再上一跳=转参链**，UNKNOWN。
4. 不宣称任何可改写点；未真机；`0xB7882C/0xB78830` 现值不可读（BSS）。
5. **同族**新上下文独立核验已完成（`evidence/r061_independent_review.md`，总判定 PASS：
   R1–R6 全 CONFIRMED，关键断言用核验员自有 capstone+自有闭包独立重导；两处出入均题面
   措辞非工件；两处形态弱点如实登记）；**异族**复核仍开（GLM persona 派发缺档级 pin），
   未过前状态=「冻结候选」，不作定谳表述。

## 5. 门禁与变异

- 门禁 `tools/r061_witness_this_contract.py`：**194/194 PASS**，exit 0。
  计数断言 A(27)/B(51)/C(17)/D(39)/E(24)/F(10)/G(26) 全 exact-pin：无 `>=`/`in` 式
  存在性阈值（G-80 教训内建——见 r055 BLOB-before-MUT 根因）。
- 校准五轮（`out/_calib_r061_mut*.py` / `_r061_mut_calib*.txt` 全保留）：
  round-1 抓出三组「兄弟满足」缺陷（窗口 OR 断言被邻宿主字节满足：D-2C/D-30/G-trio
  ——M02/M11/M14/M24/M25/M26 存活后重写为逐址钉）；round-2 抓出 `read()` 的
  `va+k` 缺省 bug（全镜像读同址 15 次⇒`jjjjjj` 假绿形态）；round-3/4 程序化生成
  killer；**round-5**（裁决 2026-10-26 执行）：E9 供体改道断言 5 字节、hist 逐 GLOBAL
  生成、splice 增量 vs 全量重建**每例红集互验**。
- round-5 校准**已完整跑毕**（`out/_r061_mut_calib5.txt`）：基线 194/194；194 例
  killed=194 / survived=0 / exc=0 / splice-full-mismatch=0 / uncovered=0；清单已提取
  `out/_r061_freeze5.json`（15,318 B，sha256
  `6330e5de64d5edf624771ef6eb0caeb2a39cbb3191e57d0c213deb1056c03ca8`，件内自记
  status=`FREEZE-CANDIDATE (pending out-of-family independent review)`）。
- 冻结转录（**已落盘，形式=冻结候选**）：round-5 清单已**机械转录**进
  `tools/mutate_r061_gate.py`（生成器 `out/_gen_r061_freeze_lits.py` 读清单打印 CASES
  字面量表，194 例/235 字节改动/预期红集手抄进件——正式套件不现算预期，裁决 4；套件
  顶部 STALE 三哈希守卫 gate/image/manifest，任一不符 exit 3）。全量复跑
  `out/_r061_freeze_run1.txt` **已收口：194/194 exact、survived/exc/mismatch/uncovered/
  phantom 全 0、套件 EXIT=0**（输出 sha256 前缀 `8deb04a4`）。**异族通道实况**：GLM persona（`ra2-re-analyst`）
  派发报 `reasoning-level-missing`（frontmatter 缺档级 pin）；纪律禁自改 persona/禁起
  未授权 workflow 绕缓存 ⇒ 本轮独立核验降级为**同族新上下文 fresh-eyes**（如实登记
  覆盖面窄于计划）。复核结论与升格前只记「冻结候选」。

## 6. 辅任务（同轮，G-79 批 1 = R-053/054/055；批 2/3 续见 `r061_aux_batch23.md`，全口径 R-047..R-055 已收官）

- **R-053**：Z1（E8 站点精确集合）零 killer → 补 M17（站点 A call rel32 +1），
  实测红 {Z1,Z2}（Z2 窗内含该字节=跨断言足迹，预期照实测写死）；套尾加
  机器 G-79 对账 → **17/17 + 覆盖 10/10**。
- **R-054**：零 killer = A4/C2/D3/D5/D7。A4/C2/D5/D7 是**未打中字节窗**（补 M23/
  M24/M26/M27 逐址）；**D3 是负命题普查**（「dtor 内零 +0x98」）按 G-80 重写为
  正锚定：dtor 窗 disp32 **集合**钉成 `== {0,4,8,0xC,0x10}`，0x98∉集成为定理，
  M25 翻转成员即红（M19 因此红集 +D3，实测写死）。→ **27/27 + 覆盖 26/26**。
- **R-055**：**根因级发现**——门在 `BLOB=bytes(RAW)` 之后才把 MUT 应用？不：
  MUT 从未写进 RAW，raw 扫描（L26-8/I3-1/I3-2/I3-3 读 BLOB）对注入**完全隐形**
  （r053 在 hoist 前有 bake 循环，r055 没有）⇒ 修 apply-before-snapshot（零基线
  变动）；四阈值断言（`>=6/>=20×2/>=10/>20/<10/>=18`）全部**掩蔽了单字节翻转**，
  转精确钉（7/22·27·13/3·28/19）后 M18–M21 补 killer，M1/M2/M12/M13 预期按实测
  交叉红集修订。→ **20/20 + 覆盖 20/20**。
- 三套件输出（实测落位）：`evidence/r053_mutate.txt`(旧) + `evidence/r053_mutate_r061.txt`、
  `evidence/r054_gate_r061.txt` + `evidence/r054_mutate_r061.txt`、
  `evidence/r055_gate_r061.txt` + `evidence/r055_mutate_r061.txt`（均已在
  `re_atlas/evidence/`，staged 区文件；原写 `out/` 为路径误记，已纠正）。
  批 1 校准脚本 `out/_g79_recon_batch1.py`（历史件留 out/）。
