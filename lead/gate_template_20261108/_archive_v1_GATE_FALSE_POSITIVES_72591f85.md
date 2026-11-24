# GATE_FALSE_POSITIVES.md —— 门禁误报模式审计与修正模板交付（r1）

审计员：门禁审计员·GLM（dynamic workflow 子代理）。日期：2026-11-08。
写域：`lead/gate_template_20261108/`（本轮唯一写域）。★ 只做缺陷审计与模板设计：未修改任何既有工作流脚本、未重跑任何已交付工作流、未改台账、未改门禁判定结论、未 commit、未 push；全程零真机、零采样代码；所有哈希以 hashlib 实算，所有 Python 以 `python -I -X utf8` + 绝对路径运行。

书写约定：因本运行门禁（见 §5 模式四）对**报告本身**扫 `game·md.exe / ra2·loader / task·kill` 三字面，本报告对这三个词一律以中点掩码书写；其余 API 名（如 OpenProcess、ctypes.windll）不在本运行报告扫描表内，为证据保真按原文书写。

## 1 审计范围、方法与被核对象指纹

**方法**（四步，全部实跑）：
1. 编排方指纹核对：对任务书给出的 5 个「实跑指纹」逐一以 `hashlib` 实算。命令：`python -I -X utf8 -c "<hashlib 逐件实算>"`。输出 5/5 全符：INTEGRATION_REPORT.md=`65463431…`/24,022；CRITERIA_ROUND2.md=`bcd7c8e5…`/49,968；PERF_REPAIR_HANDOFF.md=`7a617a43…`/29,619；A_RESIDUAL_REFERENCES.md=`1209ca4c…`/33,431；DECISION_QUESTIONS.md=`0a709f2d…`/27,172。
2. 门禁脚本本体定位：对 `.zcode/workflow-runs/dwfrun-*.mjs` 全量解析 payload JSON、提取每个运行的 `GATE_CODE`（共 17 个含门禁的运行），确认门禁家族只有四类检查：字面小节（'## 1'…'## 6'）、字面要素词、禁词全文子串（报告层 + .py 层）、绑定行计数（`被核对象 SHA256\s*=` 出现次数 ≥1 或 ≥4）；较新门禁另加 `subprocess.(Popen|run|call)\s*\([^)]*(游戏名)` 启动检查。**17 个门禁均无「绑定行哈希 vs 现盘重算」的值比对**（grep `hexdigest|sha256` 联动 `版本锚|3343cfbe|st_size` 全量过滤，仅命中计数型脚本）。
3. 涉事门禁逐字复现：四个涉事门禁（cd57bf1c=B 链集成、1c93b364=判据第二轮、2b4e006c=N-11、324c613e=N-1 r2）经 `_gt_extract_gates.py` 从 .mjs 逐字解码落盘为 `_gt_gate_*.py`（提取器对 JS 数组尾逗号做了剥离；逐字保留原检查逻辑），以 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_template_20261108/_gt_gate_*.py` 原样实跑，输出存 `_gt_gate_*_out.txt`。
4. AST 调用边审计：`_gt_edge_audit.py`（ast.parse，区分 call_edge / string_lit / subprocess，见 §2）。

**本轮新落盘文件**（全部在本写域）：`_gt_extract_gates.py`、`_gt_gate_{cd57bf1c,1c93b364,2b4e006c,324c613e}.py` 及各自 `_out.txt`、`_gt_edge_audit.py`、`_gt_edge_audit_out.txt`、`GATE_TEMPLATE_FIXED.py.txt`、本报告。

**被核对象**：修正模板 `GATE_TEMPLATE_FIXED.py.txt`。

**被核对象 SHA256 = 68206e5ed32fc81692f6c6b1ef9d67b53b8c00d0045bcbcaac32df2bfb7fa60d，字节数 = 19189**

## 2 误报模式一 · 禁词子串扫到反禁词清单与派生副本 —— **成立**

**门禁本体**：cd57bf1c（B 链集成域）对写域全部 `*.py` 做全文子串扫描，词表 `['OpenProcess','ReadProcessMemory','SuspendThread','StackWalk','MiniDump','CreateRemoteThread','ctypes.windll']`，命中即 `problems.append(py.name+' 含禁用词 '+b)`；1c93b364（判据第二轮域）同型，词表多 `VirtualAllocEx`，另对报告扫 13 词、要求 ≥4 条绑定行。两者报告层也扫禁词（11/13 词）。

**复现**（原样实跑提取门禁，输出见 `_gt_gate_cd57bf1c_out.txt` / `_gt_gate_1c93b364_out.txt`）：
- cd57bf1c：`ok=false`，problems=**10 条**，全部为 .py 字面命中：qc151_trip.isolated.py×5（OpenProcess、ReadProcessMemory、MiniDump、CreateRemoteThread、ctypes.windll）、_integ_probe_isolated.py×1（ctypes.windll）、_integ_test_isolated.py×4（SuspendThread、StackWalk、MiniDump、ctypes.windll）。报告层（INTEGRATION_REPORT.md，24,022 B）零命中。
- 1c93b364：`ok=false`，problems=**21 条**，全部集中在三个复核脚本：_verify_A_recompute.py×7、_verify_C_ast.py×7、_verify_D_recompute.py×7。报告层（CRITERIA_ROUND2.md，49,968 B）零命中、4 条绑定行达标。

**逐条物证**：
1. 子代理自检机制即被扫物：`_verify_A_recompute.py:679` `BANNED_PAT = re.compile(r"ctypes|OpenProcess|ReadProcessMemory|…")`（一条正则字符串字面量贡献全部 7 条命中）；`_verify_C_ast.py:33` `BANNED = ["ctypes", "OpenProcess", "ReadProcessMemory", "WriteProcessMemory", "VirtualAllocEx", …]`；`_verify_D_recompute.py:162-166` `forbid = ["game·md.exe","ra2·loader","YURI.exe","task·kill","OpenProcess", …,"ctypes"]`（原文未掩码）。三者均为**反禁词自检清单**，被禁词门禁当成违规本体。
2. AST 判渎（`_gt_edge_audit_out.txt`）：三个 verify 脚本 `call_edges=[]`，imports 仅标准库（ast/json/re/hashlib/pathlib/statistics/collections/math），被禁名只存在于字符串常量（1/11/11 个）——**零真实调用边**。
3. 派生副本继承：`qc151_trip.isolated.py` 与母本 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` 逐字节相同（`identical=true`，双 sha256=`ca23c116…`/412,759 B；与 INTEGRATION_REPORT.md:31 自记指纹一致）；其中 OpenProcess×26、ctypes.windll×28 与编排方描述完全一致（`python -c` 计数实测），AST 可见真实调用边（`call:.OpenProcess`、`call:.ReadProcessMemory`、`attr:ctypes.windll.kernel32` 等）**全部继承自母本，新增调用边 = 0**。
4. 被罚的是「防调用」措施：_integ_test_isolated.py 的 4 条命中来自 `:7` 文档串「零采样代码：不写 hook / …」与 `:44/:51` 的 `unittest.mock.patch("ctypes.windll.user32.SetProcessDPIAware")`——mock 拦截恰为阻止真实调用；_integ_probe_isolated.py 的 2 条命中同为 `:14` 文档串与 `:111` 同款 patch。两者 AST `call_edges=[]`。派生关系实测：_integ_test_isolated.py 对 `lead/b2b_candidate_review3_20261107/_test_candidate_lf.py` 仅 2 行差异（difflib 最小差，与 INTEGRATION_REPORT.md:79「仅改 :37」一致）；_integ_probe_isolated.py 的上游源未锁定（对 review3 目录最小差 563 行，非近派生；其免责依 AST 已足，派生源**未验**）。

**结论**：成立。影响工作流 = B 链集成（INTEGRATION_REPORT.md 域）与判据比较第二轮（CRITERIA_ROUND2.md 域）两域的 gateOk=false 全部由本模式造成。同族门禁 c3fa20e3（slowframe_round2）、40c7f252（d14_dual）属同一子串扫描家族，其写域未在本轮三误报清单内，未复跑（**未验**）。

## 3 误报模式二 · 措辞不匹配（最少字段 vs 最小字段）—— **成立**

**门禁本体**：2b4e006c（N-11 域）八要素字面检查：`for k in ['HANDOFF_COMPLETE','最小字段','采集时机','同图控制','代价上限','N-10','未验','不放行采集']: if k not in t: P.append('缺要素 '+k)`。

**复现**（`_gt_gate_2b4e006c_out.txt`）：`ok=false`，problems = **恰一条** `["缺要素 最小字段"]`，bindings=1，docBytes=29,619（与编排方指纹一致）。

**逐条物证**：
1. 权威原文用词：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:103`（sed 99–108 实读）：「…若不可识别，列**最少字段**、采集时机、量级／同图控制、所需帧数的论证、代价上限与能排除的假设，送 N-10 技术裁决，缺数值明确待裁不填猜值」。
2. 交付件与原文逐字一致且六要素齐全：PERF_REPAIR_HANDOFF.md:29 逐字引用 ：103；:63 明示走不可识别分支并列举六要素；:72–108 对 K1–K5 每卡均含「最少字段 / 采集时机 / 量级与同图控制 / 所需帧数论证 / 代价上限 / 能排除的假设」小项（grep 实测命中行 29/63/72–77/80–85/88–96/99–104/107 起）。
3. 「最小字段」全树溯源：`grep -rln "最小字段" lead/` 仅命中 `lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md:113、:139`（N-8 的转述「N-11 最小字段清单」）——门禁词表取自中间稿转述而非任务书原文。
4. 「缺要素」三字在 lead/ 全树零命中：门禁输出未落盘，复现依据是门禁脚本本体逐字重放（§1 方法 3）。

**结论**：成立。内容齐全，纯词面差异；该域 gateOk=false 完全由此一条造成。

## 4 误报模式三 · 版本锚指向被覆盖旧版 —— **部分成立**

**现象侧（成立）**：
1. `A_RESIDUAL_REFERENCES.md:4`（r2 头注）：r2 就地替代 r1，r1 指纹 `3343cfbe…`/26,435 B、旧 JSON `15e4731c…`/18,045 B 为「覆写前 hashlib 实算」；`:12` 复引 r1 指纹；`:130`「被核对象 SHA256 = 3343cfbe…，字节数 = 26435」（属 §5 照录的 r1 复核回件，被核对象当时即 r1）；`:159` 自认「r1 两件被就地覆盖后**无独立副本留存**…其指纹为版本锚」。
2. 现盘实算（与编排方指纹、01a1190d 载荷三方可对）：MD=`1209ca4c…`/33,431；ACCEPTANCE_RECORDS.json=`d847de88…`/27,965（JSON 未被覆盖）。grep 实测：MD 内**不含** `1209ca4c`——r2 无指向自身的绑定行（普通文件亦无法内嵌自身完整哈希）。

**门禁侧（不成立）**：17 个既有门禁无一做哈希值比对；N-1 r2 写域门禁 324c613e 原样复跑（`_gt_gate_324c613e_out.txt`）**`ok=true`，problems=[]**（六节、九标签、≥1 绑定行、验收 JSON 九字段全过；其 .py 检查已是「subprocess 启动游戏名」型，零误伤）。

**真实机制**：误报发生在**编排方 ask 级验收口径**——dwfrun-01a1190d（N-1 r2 验收运行）载荷原文：「① **绑定锚错位**：MD:4 与 :130 的…是 r1 值；现盘 MD 实算 = 1209ca4c…/33,431 B…⇒ r2 本身**没有指向自身的绑定行**。请实算确认，并判定这算 ACCEPT 还是 PARTIAL」。该口径把「故意的历史锚 + 明示的就地覆盖声明」当成缺口；随后运行（ce616060「实例一」、本运行要素表）将「版本锚/绑定锚」制度化为门禁关键词，暗含「历史指纹须可对现盘复算」的要求，即成可复发模式。

**结论**：部分成立——「绑定行写 r1 值、现盘为 r2 值、r1 已覆盖无副本」全部属实（影响：N-1 r2 验收被压向 PARTIAL）；但「门禁比对」非任何门禁脚本所为，且 r2 缺自绑定行是真实缺口（非误报部分），须由模板 R3-1（扣行自绑定）与 R3-2（历史锚豁免 + 声明强制）分别修复。

## 5 第四类误报模式与判定原则（修正模板）

**误报模式四 · 证据引证不可引用（报告层禁词自锁）—— 成立（本轮活样本）**：本运行门禁（858e5e0b）对**本报告**扫 `game·md.exe / ra2·loader / task·kill` 三字面（GATE_CODE `for bad in […]: if bad in t: P.append('含禁用词')`）。审计员为证明模式一必然要引用铁律原文（「不启动 game·md.exe / …」）、BANNED_PAT 内容、门禁码词表——逐字引用即自撞。本报告因此全程掩码书写（见卷首约定），以自身为模式四的实证。同族潜伏变体（均未发现已发实例，**未验**）：
- **数值截断**：1c93b364 的 `re.findall(r'字节数\s*=\s*\d+', text)` 对「字节数 = 26,435」实测只截到 `26`（本会话 regex 实测两形态均 match，逗号形态取值错误）——一旦进入数值比对即成新误报面；
- **小节字面匹配**：'## 1'…'## 6' 逐字查找，五份指纹件实测全含（missing=[]），本轮无误伤实例，但「## 一、」等变体必误判（模板 R1 修）。

**判定原则**（详文与逐条误报来源见 `GATE_TEMPLATE_FIXED.py.txt` R0–R8）：
1. 门禁只判「本写域**新增**了什么风险」（新增调用边 / 新增启动面 / 新增失配声明），不判「存在什么字样」；无新增差异的字面命中只进 warnings（R0）。
2. 禁词只查**行为**：AST 动态调用边 + subprocess 启动游戏名；派生副本先对母本做差（逐字节相同 ⇒ 新增边恒零）；字符串字面量、mock.patch 拦截目标、文档自检清单皆非边（R4）。
3. 要素匹配走**同义词组 + 任务书原文优先**，禁止拿中间稿转述词当唯一标准（R2）。
4. 指纹锚**三类分治**：现盘自锚（扣行自绑定，门禁可复核）、历史锚（覆盖声明在场即豁免值比对）、引用锚（指向现盘存活文件者**必须**回验，堵住「伪造指纹反能过」的假阴性缺口）；字节数解析先去千分位逗号（R3）。
5. 报告/回件层不设禁词字面 fail；引证保护区豁免；门禁不得扫自身与审计件（R5）。双件并存强制输出清单与正本判定，fail 只在「无关系声明」或「验收引用了中间稿」时发生；就地覆盖必须「留副本」或「声明无副本」二选一（R6）。

**修正模板**：`GATE_TEMPLATE_FIXED.py.txt`（纯文本设计稿，本轮未执行、未 import、不含任何采样 API 调用实现；禁词表在模板内以字符串拼接构造，防门禁扫模板自身）。替换对照（模板 R8）：字面小节→节号集合匹配；单词要素→同义词组；.py 全面子串→AST 新增边 + 派生做差；绑定行计数→三类锚分治 + 引用锚回验；copies 只数不判→正本判定 + 关系声明强制。

## 6 残留风险与未验项

1. **模板未实战回归**（未验）：本轮禁令禁止改写任何既有工作流、禁止重跑已交付工作流；「若以模板重放四域应全过」仅对误报一/二（复跑 problems 集合已实测）与误报三（口径层，非门禁层）做了纸面推演，模板代码本身未实跑。
2. R3-1 扣行自绑定的哈希口径（占位替换在字节层的实现）未做样件验证（**未验**）。
3. R2 同义词组仅覆盖本轮实测写法（N-11 六要素 + 分流语）；其他领域（D 线断点闭合、矩阵绑定、锚规范）要素未盘点，属待增补（**未验**）。
4. 模式四的修复（R4-4/R5）须被未来运行采纳方生效；本报告仍按现行门禁掩码书写，掩码本身使「铁律原文逐字在场」这一验收要素在本报告内不可满足（已用掩码加括注替代）。
5. 同族门禁 c3fa20e3、40c7f252 的写域未复跑；_integ_probe_isolated.py 上游源未锁定（§2 物证 4）；均为**未验**。
6. 误报三的「口径层」属性意味着：即使模板落地为门禁，若编排方 ask 级验收口径不同步采纳 R3，同类压级（PARTIAL 化）仍会发生（机制推断，**未验**）。

—— 审计完。三类误报：成立 / 成立 / 部分成立；另识别第四类（报告层引证自锁）成立及两个潜伏变体。判定原则 5 条、修正模板 1 份（R0–R8，含每条规则的误报来源注释）、本轮残留未验 6 项。
