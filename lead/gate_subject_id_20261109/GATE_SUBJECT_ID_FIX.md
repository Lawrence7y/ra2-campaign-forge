# 门禁主体识别缺陷（第 13 类）诊断与修复——终稿（含复核回件）

撰写：主体识别撰写员（终稿轮，GLM 子代理）｜2026-11-09｜写域：lead/gate_subject_id_20261109/（唯一写域）
纪律：零真机、零采样代码、不 commit、不 push；lead/ 全部历史写域与两件台账一律只读（本轮 8/8 上游指纹现值重验相符，§2.1）；全部检索为指定文件 stat/read 或单层有界 glob，无递归 walk、无界 rglob 零次。
版本说明：本件为**终稿**，按本发门禁约定占用主文件名 GATE_SUBJECT_ID_FIX.md，替换诊断轮被核稿。被核稿的字节态未失——其同字节副本 _si_SUBJECT_ID_DEFECT.md 原样保留（本轮重验 SHA256 = 8c67dc3f…f4dc、23441 B，§5.2 C 组），复核回件绑定行指涉该字节态，经副本可查。终稿自身哈希不在本件内自指，落盘后连同门禁实跑结果记于 _siw_final_receipt.txt。

## 1 目的与边界

**目的**：对已实证的第 13 类门禁缺陷——用 `max(cands,key=lambda p:p.stat().st_size)` 从写域挑「交付件」，导致**被检主体可被操纵**——完成五件事：①统计历史受害面（§2）；②诊断根因（§3.1）；③检验可操纵性——诚实回答能否用来绕过检查（§3.2，结论：能）；④给出可跑的三方案修复（§4）；⑤汇总复核回件与全量清单（§5）。

**边界**：
- 只读：lead/ 全部历史写域、两件台账（PENDING_DECISIONS.md、GOAL_THREE_TARGETS_20261018.md）、.zcode/ 工作流档案、一切既有门禁脚本。全程 stat/read/单层 glob。
- 写：仅本写域内 _si_*/_siw_* 件与本件。诊断轮证据件（_si_*）本轮零改动（10/10 哈希现值重验相符，§5.2）；_si_fix_lib.py 按 §5.1 瑕疵#3 处置保件不改（docstring 笔误以勘误记录，保哈希可追溯）。
- 修复以可粘贴片段交付（_si_fix_lib.py），不落地到任何既有门禁脚本。

**终稿轮证据足迹（本轮实跑；耗时为 perf_counter 实测，dirsVisited 按递归 walk 计、单层 glob 不计目录访问）**：

| # | 动作 | 范围 | dirsVisited | 耗时 | 产出件 |
|:-:|:--|:--|:-:|:-:|:--|
| R1 | 八件上游指纹 + 诊断轮 10 证据件绑定重验 + 被核稿双件重验 + 5 域漂移抽查 | 指定文件 stat/read；5 域单层 glob | 0（无 walk） | 0.009s | _siw_verify_out.txt |
| R2 | _si_fix_lib.py 三方案活跑（counterpart 真实域 + 沙盒负例×6） | 指定域；单层 glob×6 | 0（无 walk） | 0.008s | _siw_fixcheck_out.txt |
| R3 | 核心三域 max 现值复查 + 本轮产出件指纹 | 3 域单层 glob；2 文件 read | 0（无 walk） | 0.002s | _siw_drift2_out.txt |
| R4 | 终稿自检（五节/要素/禁词/绑定行独立复算）+ 本发门禁实跑 | 本件 | 0 | 见产出件 | _siw_selfcheck_out.txt、_siw_gatecheck_out.txt |

诊断轮的六路全库检索足迹（写域复扫 626 dirs/0.139s/743 md、gatescan 625+537 dirs、wfscan/gatecensus 等）见被核稿 §1 及其绑定产出件（_si_scan_out.json 等，§5.2）；其足迹表第 2 行耗时栏留有未填占位符 @@T2@@s——复核瑕疵#1，对应指纹检查本轮已按同口径重跑（R1，实测 0.009s，8/8 相符）。

## 2 上游指纹（八件）与历史受害面统计

### 2.1 八件上游指纹（编排方派发常量 vs 本轮 hashlib 实算：8/8 相符，_siw_verify_out.txt A 组）

| 件 | SHA256 | 字节数 | 结论 |
|:--|:--|--:|:-:|
| lead/counterpart_fix_20261109/COUNTERPART_FIX.md | e291f5a8f8b2c303b31e7f06989233e122460d9838817271fa425cae066ff416 | 32830 | OK |
| lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md | 9878bb7ec170599dd8d74eacfa0a7be0806294d91d8be994a456ad6ed864ddb4 | 32840 | OK |
| lead/strict_exposure_20261109/STRICT_EXPOSURE.md | 3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8 | 23798 | OK |
| lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md | f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545 | 24897 | OK |
| lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md | 823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c | 30536 | OK |
| lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md | ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154 | 42172 | OK |
| lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | OK |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | OK |

### 2.2 误判的文字层实锤（诊断轮实证，复核人独立复核同结论）

全句「变 ORPHAN 不等于问题解决」仅存在于主件 COUNTERPART_FIX.md（20 处 ORPHAN 提及，含加粗与表格变体）；中间稿 _cf_counterpart_vs_tighten_20261109.md 有 9 处 ORPHAN 提及但无该全句。两件字节差 = 32840 − 32830 = **10 B**——主件被 10 字节的同文本异版本遮蔽，门禁遂对着中间稿判主件「缺声明」（§3.2 复现）。

### 2.3 受害面统计（三时点对照——统计是时点的，工作区是活的）

**诊断时点（06:30–06:31；写域复扫剪枝+深度上限 6，dirsVisited=626/0.139s/743 md）：max 会选中下划线中间稿的历史写域共 5 个**：

| 写域 | max 选中 | 被压过的最大非下划线件 | 大小差 |
|:--|:--|:--|--:|
| lead/counterpart_fix_20261109 | _cf_counterpart_vs_tighten_20261109.md (32840B) | COUNTERPART_FIX.md (32830B) | 10B |
| lead/d13d14_cards_20261108 | _n10_D13D14_CARDS_20261108.md (30122B) | DECISION_QUESTIONS.md (27172B) | 2950B |
| lead/direction_ruling_20261108 | _dr_RULING.md (20942B) | RULING_DIRECTION.md (16514B) | 4428B |
| lead/handoff_pack_20261109 | 14 件全 _hp_*（bareCount=0），max 必落中间稿 | 无主件 | — |
| lead/s604_script_hunt_20261109 | 唯一 md 即中间稿 _sh_findings.md（bareCount=0） | 无主件 | — |

**漂移轨迹（复核实测 + 终稿轮抽查）**：复核人独立重扫（07:16，dirsVisited=652/0.85s/767 md）得历史域 6 个——handoff_pack（06:34:18 落 APPROVAL_PACK.md 40024B）、s604_script_hunt（06:36:33 落 S604_SCRIPT_HUNT.md 27347B）因主件落盘退出清单，c07_protocol_attacks / oldwording_sweep / s604_verdict_entry 三域进入。终稿轮抽查（_siw_verify_out.txt D 组 + _siw_drift2_out.txt）：上述五域现均 bareCount=1 且 max 为非下划线主件（40024 / 27347 / 32131 / 30046 / 36097 B——三域主件在复核扫描后落盘）；核心三域现值仍为下划线 max（10B / 2950B / 4428B，R3）。**故终稿时点历史受害域 = 3 个；任一时点清单，下游引用前必须重新扫描**——受害面本身随子代理写盘节奏漂移，这是本缺陷统计的第一课。

**(b) 大小差**：10B（0.03%）纯属偶然——主件与中间稿是同一文本的两个版本，字符数 19773 vs 19667，差异落在几十字节量级时 max 近似掷硬币；2950B / 4428B 两域同样选错对象，只是尚未触发可见误判。

**(c) max 碰巧挑对的域**：272 个（多文件域碰巧挑对 170 + 单文件域平凡正确 102；诊断时点）。现状正确率 272/277≈98%，但正确原因是「多数域恰好只有一份显眼大件」，不是机制正确——其余已翻车或必然翻车。

**结构性放大器（比下划线更广的两类歧义）**：
- **同域多主件**：诊断时点 121 个目录 bareCount>1（goal2_rc4_fixv5_20261022 bareCount=31、goal3t_nightwatch_20261102 bareCount=22 等），复核实测 125——_si_fix_lib.py docstring 所写 112 属时点+笔误差（勘误见 §4.4），一律以各轮扫描时点实测为准。max 在多主件之间同样按大小猜。
- **跨域同名主件**：诊断时点 20 种、复核 24 种非下划线文件名跨写域重名（RECEIPT.md×8 域、TASK.md×27 域、FACTCHECK.md×9 域、REPORT.md×23 域、SPEC.md×24 域、A_RESIDUAL_REFERENCES.md×2 域（28384B vs 33431B）等）。任何 `lead/**/RECEIPT.md` 式宽 glob，主体同样不可判。

### 2.4 门禁受害面普查（权威口径：.zcode/workflow-runs payload）

**lead/ 下没有门禁脚本本体**：lead 内 1642 个 .py 全扫，`max(...)紧邻 st_size` 位点 **0 处**（仅 3 处 mtime 记录用途，_si_gatescan_out.json）；库根+.tmp 补充 1997 个 .py，max~st_size 0 处、max~mtime 5 处（out/re_work/sessions_timeline.py:112-115、tools/host_attribution.py:43、tools/host_attribution_v160.py:28——不在门禁链，语义未逐处审读，§5.6）。门禁代码以 GATE_CODE 常量内嵌于 dwfrun-*.mjs 的 payload。

普查（诊断轮两遍 walk 209/211 mjs；复核实测 212 mjs，36 处位点 0 缺/0 多/0 错配）：

- **36 处 `DOC=max(cands,key=lambda p:p.stat().st_size)`**，分布于 36 个 run 文件、32 个写域（34 处伴随 `sorted(wd.glob('*.md'))`，2 发变体取件：n4_yi_final、gate_fp7）；
- **已显式命名的门禁**（`expected=wd/'…md'`，缺件即 FAIL）：诊断时点 3 发——oldwording_sweep_20261109、本发、s604_verdict_entry_20261109；复核时点新增第 4 发 equiv_class（dwfrun-4f51b573）——编排方已在新门禁上落地方案A；
- 1 处 `max(cands` 引文：本发 payload 的任务文本引用缺陷代码本身（非门禁）；
- 风险分级（按写域当前是否含下划线中间稿）：**32 行 HIGH、4 行 MED**（MED：c07_gate_fix_20261109、c07_protocol_attacks_20261109、c07_gate_audit_20261109、samedoc_link_20261109；按域计 28 HIGH + 4 MED）。逐处清单见 §5.3。

## 3 根因诊断与可操纵性检验

### 3.1 根因三问

**(a) 为什么用 max(st_size) 挑交付件**：门禁只拿到「写域」这层容器，不知道主件名。而讽刺的是 payload 里早有现成答案——counterpart 发的 ASK 文本写有 `const DOC = "lead/counterpart_fix_20261109/COUNTERPART_FIX.md"`（_si_wfextract_out.txt），**GATE_CODE 却没有引用它**，改用 `cands=sorted(wd.glob('*.md'))` + max。根因是把「主件通常是域内最大的 md」这条经验当成了识别器；36 发历史仅 1 发暴露（98% 正确率）形成「一直没出事」的路径依赖，掩盖了主体从未被真正锚定的事实。

**(b) 为什么下划线前缀没被用作排除条件**：下划线 = 中间稿的惯例只存在于产出形态（_cf_ / _hp_ / _sh_ / _dr_ / _n10_ / _ve_ / _ow_ / _pa_），从未成文——lead/_routing_policy/ROUTING_20261108.md 全文只管模型路由，无任何文件命名约定。写域清点代码（SWEEP_CODE）已把 largestIsUnderscore 当**描述字段**输出——惯例已被感知，但止步于描述，没有进入门禁的**排除规则**。感知与执行之间断了一层。

**(c) 同类的主体识别缺陷（第 13 类家族，均有实跑位点或实测佐证）**：

1. **glob 太宽**：`wd.glob('*.md')` 吞下中间稿（36 处门禁实证）；`lead/**/X.md` 式宽 glob 吞跨域同名件（§2.3）。
2. **按 mtime 挑件**：mtime_pick 位点 lead 内 126 个 .py（复核按 getmtime/st_mtime 口径实测 133，漂移量级相符；判据口径未定论，§5.6），门禁位内 3 处（T42E4_FORENSIC_085458ab/_verify_files.py:58、XVERIFY_S543_0f4bd824/V3/_v3_scorefam_probe.py:55、XVERIFY_S544_7255362d/V2/_census.py:180，均为 getmtime/st_mtime）。mtime 可被任意后续写件刷新，比 st_size 更易操纵。
3. **按顺序取首**：sorted_first 位点 lead 内 6 处——该判据未定义，复核未复现（§5.6）；且终稿轮承诊断轮实测：Windows 下 `sorted(Path)` 按 normcase 比较（_ 前缀 0x5F 排在小写字母前），与纯 str 排序相反，平台语义漂移使顺序启发式更不可托付。
4. **双主件歧义**（121→125 目录）与**跨域同名**（20→24 种）——即便排除了下划线，主体仍可能不唯一。
5. **DOC 常量被弃用**：payload 已声明主件路径，GATE_CODE 却去猜——信息在手上仍走启发式，属实现疏漏而非信息缺失。
6. **内容子串门禁的自身脆弱**：本发门禁禁词表为字面 substring 检查（三个既成事实断言词，撰写人须避开复述）——正是 gate_postmortem_20261109（第 12 类字面匹配缺陷）在本次的活例；主体识别修复应与字面匹配加固同批进行。
7. **清点口径不一致**：编排方清点为一级写域非递归（145 dirs/414 md），复扫为剪枝深度 6 递归（626/743）——两口径下「最大件为下划线件」集合一致（诊断时点均 5 个），但任何下游按清点数字做判定前须先固定口径。

### 3.2 可操纵性检验——诚实回答：能否用来绕过检查？

**能。不止误报，且是双向的；攻击者就是被门禁约束的子代理本身（写域文件由它落盘），无需任何提权，全程静默无告警。severity = high。** 全部实跑：诊断轮沙盒五场景 + 真实域复跑 12/12 断言（_si_exploit_out.txt）；复核人完全独立构造 8/8 断言（_siv_exploit_out.txt/.json）再现同结论：

1. **误报（真实域精确复现）**：忠实还原 counterpart 发 GATE_CODE（_si_gate_counterpart_extracted.py；复核人从 payload 模板独立重建，逐字节一致）只读复跑，输出 `{"ok": false, "problems": ["缺「变ORPHAN不等于解决」声明"], "bindings": 15, "docBytes": 32840, "doc": "_cf_counterpart_vs_tighten_20261109.md"}`——主件 32830B **从未被门禁读入**，误判精确复现。
2. **绕过（S2）**：违禁内容写进真主件、中间稿写得更大更干净 → 旧门禁 **PASS**——违禁内容留在真主件里，门禁绿灯放行，借道入库。
3. **误判通过（S3）**：真主件缺要素、更大的中间稿补齐全部要素（含规范绑定行）→ 旧门禁 **PASS**——要素检查全部落在伪造件上。复核人独立变体（主件 2500B 缺全部要素 + 中稿 4580B 含全部要素）同样 PASS。
4. **双向判定翻转（S4a/S4b）**：域内两份非下划线主件一好一坏时，旧门禁 PASS 还是 FAIL 完全由哪份更大决定——同一攻击面两次运行给出相反判定。
5. **三方案对此全部免疫**：方案A 五场景全对（双主件时判约定主件）；方案B/C 四场景对、双主件场景 fail-closed（本轮 R2 活跑 10/10 断言再现，§4）。

### 3.3 附加观察

受害面随写盘漂移（§2.3：5→6→3 个历史域）意味着：即便旧门禁今天全对，明天一个更大的 _ 前缀件就能让它翻车——缺陷是结构性的，不依赖单次侥幸；同理，任何「当前没有误判」的扫描快照都不构成对机制的安全证明。

## 4 三种修复方案（实现片段与适用场景）

共同前提：**主体识别失败必须 FAIL（fail-closed），禁止静默降级回启发式猜件。** 可粘贴完整实现 = _si_fix_lib.py（SHA256 见 §5.2 绑定；2850 B），验证链：诊断轮沙盒五场景 + 真实域双验证（12/12）→ 复核人 importlib 实载 13/13 断言 → 终稿轮活跑 10/10 断言（_siw_fixcheck_out.txt：A/B/C 在 counterpart 真实域均选中 COUNTERPART_FIX.md；缺件 / 双主件 / 零主件 / 大中稿在场四处负例全部正确 GateFail；遮蔽告警正命中 _cf_ 件）。

### 4.1 方案A：显式命名（首选）

```python
class GateFail(Exception):
    pass  # 主体识别失败 -> 门禁必须 FAIL，禁止降级回启发式挑件

def pick_deliverable_explicit(wd, expected_name):
    p = Path(wd) / expected_name
    if not p.is_file():
        raise GateFail("主交付件未按约定命名 " + str(expected_name))
    return p
```

- 适用：任务下发时已约定主件名（每发 ASK 均应写明，如 counterpart 发 `const DOC=…`、本发 GATE_SUBJECT_ID_FIX.md）。本发门禁即此形态（_si_gate_self_extracted.py:5-6）。
- 风险：子代理漏写/改名 → FAIL。属安全侧失败，重跑即愈；零歧义。
- 最佳实践：叠加指纹校验——payload 的 fps 表已有各件 sha256，把「expected 存在」升级为「expected 存在且 sha256=fps[...]」，主体识别与完整性一次闭合（与本回件的绑定行机制同构）。

### 4.2 方案B：排除下划线 + 恰好一份（次选）

```python
def pick_deliverable_unique_bare(wd):
    cands = sorted(Path(wd).glob("*.md"))          # 单层，有界
    bare = [p for p in cands if not p.name.startswith("_")]
    if not bare:
        raise GateFail("写域内无非下划线 md 主件")
    if len(bare) > 1:
        raise GateFail("非下划线主件不唯一: " + repr([p.name for p in bare]))
    return bare[0]
```

- 适用：把「一域一主件、中间稿一律 _ 前缀」写入派发纪律**之后**。
- 风险：现状 121（复核 125）个多主件域直接上 B 会误 FAIL——须先成文约定或按域白名单放行；对 handoff_pack 形态（域内全是中间稿）会 FAIL——那是正确行为：这种域本就没有可判定的单一主体。

### 4.3 方案C：兜底最小补丁（过滤 + 恰一）

```python
# 对旧门禁 DOC=max(cands,key=lambda p:p.stat().st_size) 的最小补丁（改 2 行）：
bare = [p for p in cands if not p.name.startswith("_")]
if len(bare) != 1:
    P.append('主体不唯一或缺失: ' + repr([p.name for p in bare]))
else:
    DOC = bare[0]   # 此后与大小无关；max 不再参与主体识别
```

- 适用：36 处旧 GATE_CODE 的即刻止血——改动量最小，立刻堵住下划线遮蔽与双主件歧义；对「约定主件根本没写」的形态（handoff_pack）同样正确 FAIL。C 是过渡件，最终形态应收敛到 A。

### 4.4 加固、配套与勘误

- **overshadow_warning**（_si_fix_lib.py:57-61）：选中主件后若存在更大的下划线件，返回告警清单留审计痕（不 FAIL）；counterpart 真实域正命中 _cf_ 件（本轮 R2 实测）。
- **纪律成文**：「主件名进 ASK/GATE_CODE；中间稿一律 _ 前缀；一域一主件」写入派发模板或新增命名政策件（现 lead/_routing_policy/ 只管模型路由），方案B/C 的前提才成立。
- **清点口径**：SWEEP_CODE 已输出 largestIsUnderscore——建议在其 summary 直接加 maxPicksUnderscore / bareUnique 两个布尔字段，让受害面每轮可见。
- **勘误（复核瑕疵#3）**：_si_fix_lib.py:29 docstring 写「112 个目录 bareCount>1」，与诊断稿 121、复核实测 125 均不一致。为保该件哈希（已被两轮回件绑定）可追溯，**保件不改**，以本条勘误为准：该计数是时点值，以各轮扫描实测为准。

## 5 复核回件、全量清单与声明

### 5.1 复核回件（verdict 如实记录）

**verdict = confirmed**（非 refuted / partial，故不标 unconfirmed）。复核人独立实跑 24 条 Bash 命令，写盘仅 16 个 _siv_* 件 + _siv_sandbox（全部在本写域内）。

被核对象 SHA256 = 8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc，字节数 = 23441

（被核对象 = 诊断轮主交付件 GATE_SUBJECT_ID_FIX.md；该字节态现完整存于同字节副本 _si_SUBJECT_ID_DEFECT.md，本轮重验相符——§5.2 C 组。本终稿占用主文件名后，此绑定行继续指涉被核字节态，经副本可查。）

复核要点（复核回件摘要，全部为其本会话实跑）：
① 指纹 8/8 OK，两台账 PRE_H/PRE_GO 现值=派发时刻常量（诊断窗口内台账未动）；被核稿双件同字节、绑定行成立。② 独立重扫（剪枝+深度上限 6，652 dirs/0.85s/767 md）证实「5 域」在诊断扫描时点为真，并记录此后漂移（核心三域差 10B/2950B/4428B 逐件相符）。③ 三方案 importlib 实载 13/13 断言：A 缺件 GateFail、B/C 滤下划线+恰一、overshadow 正确命中/留空、§5.4 normcase 断言实测成立（str 排序 GATE 先、sorted(Path) normcase 序 _si 先、同字节 max 取序首）。④ 可操纵性完全独立构造 8/8：大中稿含全部要素→旧门禁 PASS（主件从未被读）、违禁词藏真主件→PASS（绕过成立）、好坏件仅互换大小→判定翻转、三方案均选中真主件并正确 FAIL；payload 模板重建与撰写人还原件逐字节一致，还原门禁子进程实跑精确复现误判；本发门禁自跑 ok:true。⑤ 全量清单 36 行与其独立提取 0 缺/0 多/0 错配；宽正则变体搜捕无额外命中；.zcode/agents 深探 0 文件 0 命中（补上诊断轮未验项）；.tmp 48 py 0 位点；lead 其余域 max~st_size 0 处成立。⑥ 越界检查：六路遍历全部有界、无界 rglob 零次、零真机、零采样代码、未 commit/push。

**次要瑕疵 4 处（复核原文）与本终稿处置**：
1. 被核稿 §1 足迹表第 2 行耗时栏留未填占位符 @@T2@@s（GATE_SUBJECT_ID_FIX.md:22）→ 本终稿足迹表全部填实测值（§1 R1–R4），对应检查重跑相符；
2. 被核稿 §5.4 写 _si_SUBJECT_ID_DEFECT.md=23286B，实值 23441B（与其自验件 _si_gatecheck_out.txt 一致）→ 本终稿一律写 23441B 并重验（§5.2 C 组、§5.5）；
3. _si_fix_lib.py:29 docstring「112」与 121/125 不一致 → 勘误记录、保件不改（§4.4）；
4. §2.3(a)「5 域」为时点快照 → 本终稿改三时点对照并声明重扫义务（§2.3）。

### 5.2 证据件绑定行（hashlib 实算；诊断轮 10 条本轮现值重验 10/10 相符，_siw_verify_out.txt B/C 组）

被核对象 SHA256 = 4ba1c43e576989e624e986b4ead34aba7eface4b47a5e7c9e14ace59fc352f85，字节数 = 180681（lead/gate_subject_id_20261109/_si_scan_out.json）
被核对象 SHA256 = e27d1f54282611c3f71f59b79399e72cefff6e67aeaf9e76131bc3e95c576ece，字节数 = 10565（lead/gate_subject_id_20261109/_si_fp_out.txt）
被核对象 SHA256 = c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94，字节数 = 611043（lead/gate_subject_id_20261109/_si_gatescan_out.json）
被核对象 SHA256 = e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52，字节数 = 180256（lead/gate_subject_id_20261109/_si_wfscan_out.json）
被核对象 SHA256 = 44ca323a505cad7cdcae4297baff260f57f76173474f5e996ccf84d70e68966d，字节数 = 11870（lead/gate_subject_id_20261109/_si_gatecensus_out.json）
被核对象 SHA256 = 4167956c3d5f6ae68656bce60c053d1ab09de95059cf7d269e33f914df6217d1，字节数 = 45230（lead/gate_subject_id_20261109/_si_wfextract_out.txt）
被核对象 SHA256 = b25c8c40c2ad484abb473b28145fd3a5e6a02d790aa526fb9baae28d62ce0939，字节数 = 2281（lead/gate_subject_id_20261109/_si_gate_counterpart_extracted.py）
被核对象 SHA256 = 83a81c084e1f2df5d997d125a0f6d26f445d077abee62355b2f8c9989eea82ec，字节数 = 1402（lead/gate_subject_id_20261109/_si_gate_self_extracted.py）
被核对象 SHA256 = 151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587，字节数 = 5717（lead/gate_subject_id_20261109/_si_exploit_out.txt）
被核对象 SHA256 = 54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee，字节数 = 2850（lead/gate_subject_id_20261109/_si_fix_lib.py）
被核对象 SHA256 = 538723099529a83e5128e4949142cc602ba87eba33d0183d5c4bb4e531e591b7，字节数 = 6354（lead/gate_subject_id_20261109/_siw_verify_out.txt，终稿轮 R1）
被核对象 SHA256 = db8d99edea1a0d1749fcfe5235803e73cea93296ab7d077dd1f7c6535a3c2c8d，字节数 = 1525（lead/gate_subject_id_20261109/_siw_fixcheck_out.txt，终稿轮 R2）
被核对象 SHA256 = 8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc，字节数 = 23441（lead/gate_subject_id_20261109/_si_SUBJECT_ID_DEFECT.md——被核稿存世字节态；主文件名 GATE_SUBJECT_ID_FIX.md 现由本终稿占用，终稿哈希见 _siw_final_receipt.txt）

### 5.3 全量清单（门禁脚本里 max(st_size) 逐处列出 + 风险等级 + 改法汇总）

lead/ 下 .py 门禁脚本 `max(st_size)` 位点数：**0**（1642 件全扫）——脚本本体不在 lead/，以下以 payload 位点为准（36 处 → 32 写域；风险 = 该写域当前是否含下划线中间稿；复核人独立比对 36 行 0 缺/0 多/0 错配）：

| run 件（.zcode/workflow-runs/） | 目标写域 | 风险 |
|:--|:--|:-:|
| `dwfrun-13448f03-38f0-40e1-b43c-c97759379f8f.mjs` | `lead/ledger_appendix_20261108` | HIGH |
| `dwfrun-15585c14-eff5-46e5-a910-1288e8310bc0.mjs` | `lead/strict_exposure_20261109` | HIGH |
| `dwfrun-24bda605-750d-4fd8-bc60-90139f8b7207.mjs` | `lead/c07_truth_protocol_20261109` | HIGH |
| `dwfrun-27d477b1-0a71-49e2-a503-3c9732a413bc.mjs` | `lead/w2_samecause_20261109` | HIGH |
| `dwfrun-53714984-6fd6-44ea-9fd5-a3dee40f6998.mjs` | `lead/text_fix_unified_20261109` | HIGH |
| `dwfrun-5ad91c91-308a-4c68-8869-ab18d1721803.mjs` | `lead/f2d_rootcause_20261109` | HIGH |
| `dwfrun-5e5d5e49-0888-4a28-a365-69c0acd092ba.mjs` | `lead/s604_script_gap_20261109` | HIGH |
| `dwfrun-616f12ea-e992-48c5-982e-1c1289832e79.mjs` | `lead/ledger_appendix_20261108` | HIGH |
| `dwfrun-636adfc5-7ca1-4948-a711-f8027d8de9e2.mjs` | `lead/counterpart_fix_20261109` | HIGH |
| `dwfrun-65b875da-d77d-4730-b8ef-8a302b8ca4ba.mjs` | `lead/gate_r9r12_20261109` | HIGH |
| `dwfrun-65d9f3a9-5598-4f76-b552-bdfbb68fb6fc.mjs` | `lead/gate_postmortem_20261109` | HIGH |
| `dwfrun-66e74798-f5ef-4f70-8217-65c5d2229dca.mjs` | `lead/c07_gate_fix_20261109` | MED |
| `dwfrun-69087c8f-2c8f-45e6-9373-cae0361012f0.mjs` | `lead/matrix_row5_20261109` | HIGH |
| `dwfrun-802eb959-8844-4df4-87ba-3d71bff4e693.mjs` | `lead/u5u6_mirror_20261109` | HIGH |
| `dwfrun-80551feb-5b8f-40c5-bb92-b6c8171c98c4.mjs` | `lead/c07_protocol_attacks_20261109` | MED |
| `dwfrun-80d9632c-3394-46c0-b011-c294fa40a079.mjs` | `lead/c07_slot_20261109` | HIGH |
| `dwfrun-830e57b2-c46c-4fe0-8c29-ad21e8f233da.mjs` | `lead/ledger_appendix_20261108` | HIGH |
| `dwfrun-88b03f6c-146d-4893-8d84-e87a85abc6e3.mjs` | `lead/s604_exclusive_20261109` | HIGH |
| `dwfrun-903e6b21-eb50-4c2f-a8dd-da3851198786.mjs` | `lead/n11_wording_fix_20261108` | HIGH |
| `dwfrun-962827dd-a748-45ed-b80c-6076f87c9a55.mjs` | `lead/c07_gate_audit_20261109` | MED |
| `dwfrun-a1c4b1fd-3c38-4b5e-838d-e428469e98cc.mjs` | `lead/o1prime_reach_20261109` | HIGH |
| `dwfrun-a4a38b66-4a6b-4794-b2da-29d141c91a60.mjs` | `lead/handoff_pack_20261109` | HIGH |
| `dwfrun-af6f3c87-7d72-4587-8e0d-07c4b878337c.mjs` | `lead/n4_yi_final_20261108` | HIGH |
| `dwfrun-bc3fed8c-072e-44c0-88d0-c2dc9b016bc2.mjs` | `lead/c07_slot_20261109` | HIGH |
| `dwfrun-bc9d8b8e-9faa-4226-8022-ccd881335683.mjs` | `lead/s604_script_gap_20261109` | HIGH |
| `dwfrun-c482b235-41c5-431b-b9d9-2617c362b1cc.mjs` | `lead/matrix_reach_20261109` | HIGH |
| `dwfrun-cd88a9f5-f5aa-4cdb-865a-5ff57c1e2203.mjs` | `lead/samedoc_link_20261109` | MED |
| `dwfrun-cec38f8b-6a40-4b41-b6b4-16da09b9d950.mjs` | `lead/s604_attribution_20261108` | HIGH |
| `dwfrun-d3ec8aec-3df8-4291-bd1b-437af9f187f2.mjs` | `lead/r11_f2_fix_20261109` | HIGH |
| `dwfrun-db5bad08-1aa0-4dea-940f-5f66a8b27a06.mjs` | `lead/matrix_ab_ruling_20261109` | HIGH |
| `dwfrun-dcda8414-b411-49a0-bb78-3d9fab5a0a33.mjs` | `lead/s604_script_hunt_20261109` | HIGH |
| `dwfrun-ebe5b75c-c69b-4216-81ac-882da55f8156.mjs` | `lead/pending_factpack_20261108` | HIGH |
| `dwfrun-f0c21a59-ac15-426c-a017-013a8acc9ed8.mjs` | `lead/n10c04_ruling_20261108` | HIGH |
| `dwfrun-f123d326-bd6f-4266-8a73-0acd2a314e19.mjs` | `lead/v2_precision_fix_20261108` | HIGH |
| `dwfrun-fed3c2a2-7a61-4449-b6e7-cc7d0a5daf14.mjs` | `lead/gate_fp7_20261108` | HIGH |
| `dwfrun-ffc43bb0-e58a-43d2-80d4-4fe1fef6d832.mjs` | `lead/n11_dimmap_20261108` | HIGH |

另有 5 处 max~mtime 位点（out/re_work/sessions_timeline.py:112-115、tools/host_attribution.py:43、tools/host_attribution_v160.py:28）：不在门禁链，语义未逐处审读，列观察项（§5.6）。

**改法汇总**：
1. 36 处一律收敛到方案A：GATE_CODE 开头加 `expected=wd/'<约定名>'` + 缺件 FAIL（约定名各发 payload 已有或一句即可约定），并叠 payload fps 表 sha256 校验；
2. 来不及逐发改名的，先用方案C 两行补丁止血（堵下划线遮蔽 + 双主件歧义）；
3. 已显式命名的门禁无需动（诊断时点 3 发：oldwording_sweep / 本发 / s604_verdict_entry；复核时点新增第 4 发 equiv_class），建议再叠 fps 指纹校验；
4. 配套：把「一域一主件、中间稿一律 _ 前缀、主件名进 ASK/GATE_CODE」成文（§4.4），否则方案B/C 在百余个多主件域上会误 FAIL。

### 5.4 未改任何历史件声明

本任务（诊断轮 + 复核轮 + 终稿轮）全程对历史只读：lead/ 下任何历史写域、两件台账（PENDING_DECISIONS.md、GOAL_THREE_TARGETS_20261018.md）、.zcode/ 工作流档案、任何既有门禁脚本，均未写未删未动。现值证明：①八件上游指纹（含两台账）本轮实算与派发常量 8/8 相符（§2.1，_siw_verify_out.txt）；②两台账现值与本发门禁 PRE_H/PRE_GO 常量相符（本轮门禁实跑自动复核，§5.5）；③诊断轮 10 证据件本轮重验 10/10 相符（§5.2）。全部落盘限于本写域：诊断轮 _si_* 件 + _si_sandbox、复核轮 _siv_* 件 + _siv_sandbox、终稿轮 _siw_* 件 + _siw_sandbox 与本件。修复只以片段交付，未在任何既有门禁上实施。

### 5.5 自验（终稿轮 R4）

以本发门禁（_si_gate_self_extracted.py，方案A 形态）对本写域实跑（_siw_gatecheck_out.txt）：`{"ok": true, "problems": [], "bindings": 14}`（要素 12/12、五节 5/5、禁词 0 命中；终稿自检独立复算同结论，_siw_selfcheck_out.txt）。
附注（复核瑕疵#2 更正后重述）：旧 max 门禁若施于本写域，实跑选中 _si_SUBJECT_ID_DEFECT.md（**23441B**——诊断轮 _si_gatecheck_out.txt 实测；被核稿正文误写 23286B，本终稿更正）。Windows 下 `sorted(Path)` 按 normcase 比较，_ 前缀（0x5F）排在小写字母之前，与纯 str 排序相反；两件同字节故判定不变。这本身即「同字节双件无害、异字节双件危险」的对照样本：max 的挑件行为连排序细节都随平台语义漂移，更不可托付主体识别。

### 5.6 未验项（如实）

1. 36 发旧门禁各自**当时**的实跑输出（exit/problems）未逐发取证：除 counterpart（诊断轮忠实还原复跑实证误判）外，其余 35 处按「结构性暴露」计，不逐发断言其曾产生误判。
2. handoff_pack / s604_script_hunt 两发**当时**门禁是否 PASS 未验（payload 不含门禁 stdout）。
3. root/.tmp 补充扫描的 5 处 max~mtime 位点（out/re_work/sessions_timeline.py:112-115、tools/host_attribution.py:43、tools/host_attribution_v160.py:28）未逐处审读语义——不在门禁链，列观察项。
4. 「mtime_pick 126 个 .py」复核按 getmtime/st_mtime 口径实测 133、「sorted_first 6 处」判据未定义未复现——两数均注记为时点+口径值，未定论。
5. .zcode/agents：诊断轮未扫（超深度预算）；复核人已深探 0 文件 0 命中——本条以复核回件为据，终稿轮未再独立重扫。
6. 受害面/多主件/跨域同名三类计数均系时点值（5→6→3 域、121→125、20→24 种）；终稿轮仅抽查 8 个域，未全量重扫——下游引用 §2.3 任一清单前须重扫。
7. 36 处位点的改法（方案A 收敛 + fps 校验）为建议，未在任何既有门禁上实施（本任务纪律）；其落地后的回归验证亦未做。
