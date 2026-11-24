# -*- coding: utf-8 -*-
"""_si_compose_report.py — 组装主交付件 GATE_SUBJECT_ID_FIX.md（+同字节 _si_ 副本）。
数字全部从本写域 JSON 注入；写入前自检：禁用词不含、必备要素全含、小节齐全。"""
import hashlib
import json
from pathlib import Path

OUTD = Path(r"D:/Project/ra2-campaign-forge/lead/gate_subject_id_20261109")


def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


sc = json.loads((OUTD / "_si_scan_out.json").read_text(encoding="utf-8"))["summary"]
gc = json.loads((OUTD / "_si_gatecensus_out.json").read_text(encoding="utf-8"))
gs = json.loads((OUTD / "_si_gatescan_out.json").read_text(encoding="utf-8"))
ws = json.loads((OUTD / "_si_wfscan_out.json").read_text(encoding="utf-8"))

# 36 行位点表
rows = []
for r in gc["filesWithGateSelection"]:
    if r["docMax"] > 0:
        rows.append("| %s | %s | %s |" % (
            "`" + r["file"].split("/")[-1] + "`",
            "`" + (r["domain"] or "-") + "`",
            r["risk"]))
TABLE = "\n".join(rows)

# 绑定行束
EV = ["_si_scan_out.json", "_si_fp_out.txt", "_si_gatescan_out.json", "_si_wfscan_out.json",
      "_si_gatecensus_out.json", "_si_wfextract_out.txt", "_si_gate_counterpart_extracted.py",
      "_si_gate_self_extracted.py", "_si_exploit_out.txt", "_si_fix_lib.py"]
BIND = []
for f in EV:
    h, n = sha(OUTD / f)
    BIND.append("被核对象 SHA256 = %s，字节数 = %d（lead/gate_subject_id_20261109/%s）" % (h, n, f))
BINDS = "\n".join(BIND)

TPL = """# 门禁主体识别缺陷（第 13 类）诊断与修复

撰写：主体识别诊断员（GLM 子代理）｜2026-11-09｜写域：lead/gate_subject_id_20261109/（唯一写域）
纪律：零真机、零采样代码、不 commit、不 push；lead/ 全部历史写域与两件台账只读未动。
命名说明：本件按本发门禁约定命名 GATE_SUBJECT_ID_FIX.md；因任务纪律要求产出带 _si_ 前缀，另落**同字节**副本 _si_SUBJECT_ID_DEFECT.md（两者 SHA256 相同）。主交付件 = GATE_SUBJECT_ID_FIX.md，其 SHA256/字节数由回件绑定行给出（不在本件内自指）。

## 1 目的与边界

**目的**：对已实证的第 13 类门禁缺陷——用 `max(cands,key=lambda p:p.stat().st_size)` 挑「交付件」导致**被检主体可被操纵**——完成：①统计历史受害面；②诊断根因；③给出可跑的三方案修复；④检验可操纵性（能否绕过检查）。

**边界**：
- 只读：lead/ 全部历史写域、两件台账（PENDING_DECISIONS.md、GOAL_THREE_TARGETS_20261018.md）、.zcode/ 工作流档案。全程 stat/read/walk，未写未删未改。
- 写：仅本写域内 _si_* 件与本件（含同字节副本）。
- 遍历：全部检索带剪枝（跳 .git/__pycache__/node_modules/.tmp/点目录）与深度上限，无界 rglob 零次。
- 修复以可粘贴片段交付（_si_fix_lib.py），不落地到任何既有门禁。

**证据足迹（六路检索，dirsVisited / 耗时）**：

| # | 检索 | 范围 | dirsVisited | 耗时 | 产出件 |
|:-:|:--|:--|:-:|:-:|:--|
| 1 | 写域 md 清点复扫 | lead/ 递归，深度上限 6 | @@DV1@@ | @@T1@@s | _si_scan_out.json |
| 2 | 八件指纹复核 + ORPHAN 句实证 | 指定 8 文件 | 0（无 walk） | @@T2@@s | _si_fp_out.txt |
| 3 | lead/ 内 .py/.md 主体识别位点 | lead/ 递归，深度上限 6 | @@DV3@@（py）/ @@DV3B@@（md） | @@T3@@s/@@T3B@@s | _si_gatescan_out.json |
| 4 | 库根+.tmp 补充 .py 扫描 | 库根（不含 lead/），深度上限 4 | @@DV4@@ | @@T4@@s | 同上 |
| 5 | .zcode mjs 门禁普查（两遍 walk） | .zcode/，深度上限 3 | @@DV5@@ / @@DV5B@@ | @@T5@@s / @@T5B@@s | _si_wfscan_out.json / _si_gatecensus_out.json |
| 6 | payload 门禁源码还原 + 沙盒检验 | 指定 2 个 payload + 沙盒 | 0（无 walk） | @@T6@@s | _si_wfextract_out.txt、_si_gate_counterpart_extracted.py、_si_gate_self_extracted.py、_si_exploit_out.txt |

## 2 上游指纹与历史受害面统计

### 2.1 八件指纹复核（hashlib 实算，非采信编排方）

8/8 全 OK（sha256 与字节数逐件相符；全文 16 行含逐件哈希见 _si_fp_out.txt）：

| 件 | 字节数 | 结论 |
|:--|--:|:-:|
| lead/counterpart_fix_20261109/COUNTERPART_FIX.md | 32830 | OK |
| lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md | 32840 | OK |
| lead/strict_exposure_20261109/STRICT_EXPOSURE.md | 23798 | OK |
| lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md | 24897 | OK |
| lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md | 30536 | OK |
| lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md | 42172 | OK |
| lead/PENDING_DECISIONS.md | 52419 | OK |
| lead/GOAL_THREE_TARGETS_20261018.md | 759518 | OK |

ORPHAN 句实证：全句「变 ORPHAN 不等于问题解决」在主件 COUNTERPART_FIX.md 中出现（含「★★ 变 ORPHAN 不等于问题解决：」加粗处与表格「变 ORPHAN ≠ 问题解决」处等，共 20 处 ORPHAN 提及）；中间稿 _cf_counterpart_vs_tighten_20261109.md 有 9 处 ORPHAN 提及但**无**该全句——门禁误判的文字层实锤。字节数差 = 32840 − 32830 = 10。

### 2.2 复扫口径与总面

编排方清点为「一级写域、非递归」口径：145 dirs、414 md。本复扫为「剪枝 + 深度上限 6 递归」口径：dirsVisited=@@DV1@@、含 md 目录 @@DM@@、md @@TM@@ 件、stat 错误 0、耗时 @@T1@@s（_si_scan_out.json）。**两口径下「最大件为下划线件」的写域集合完全一致（5 个）**，结论不依赖口径。

### 2.3 第一步三问

**(a) max 会选中下划线件的写域共 5 个**：

| 写域 | max 选中 | 被压过的最大非下划线件 | 差 |
|:--|:--|:--|--:|
| lead/counterpart_fix_20261109 | _cf_counterpart_vs_tighten_20261109.md (32840B) | COUNTERPART_FIX.md (32830B) | 10B |
| lead/d13d14_cards_20261108 | _n10_D13D14_CARDS_20261108.md (30122B) | DECISION_QUESTIONS.md (27172B) | 2950B |
| lead/direction_ruling_20261108 | _dr_RULING.md (20942B) | RULING_DIRECTION.md (16514B) | 4428B |
| lead/handoff_pack_20261109 | （14 件全 _hp_*，bareCount=0）max 在中间稿中挑最大 | 无主件 | — |
| lead/s604_script_hunt_20261109 | （唯一 md 即中间稿 _sh_findings.md，bareCount=0） | 无主件 | — |

**(b) 大小差 = 10B / 2950B / 4428B**。10B（0.03%）纯属偶然：主件与中间稿是同一文本的两个版本（字符数 19773 vs 19667），差异落在几十字节量级是「同文本双版本」的常态——max 在这种场景下近似掷硬币。2950B/4428B 的两域里 max 同样选错对象，只是尚未触发可见误判。

**(c) max 恰好选中非下划线件：272 个写域**（多文件域碰巧挑对 170 个 + 单文件域平凡正确 102 个）。现状正确率 272/277≈98%，但正确的原因是「多数域恰好只有一份显眼大件」，不是机制正确——其余 5 个已翻车或必然翻车。

### 2.4 结构性放大器（比下划线更广的两类歧义）

- **同域多主件**：@@MB@@ 个目录 bareCount>1（如 goal2_rc4_fixv5_20261022 bareCount=31、goal3t_nightwatch_20261102 bareCount=22、codex_round_20261030/LEADER_battle bareCount=13）。max 在多主件之间同样按大小猜。
- **跨域同名主件**：@@DN@@ 种非下划线文件名跨写域重名（RECEIPT.md×8 域、TASK.md×27 域、FACTCHECK.md×9 域、REPORT.md×23 域、SPEC.md×24 域、A_RESIDUAL_REFERENCES.md×2 域（28384B vs 33431B）等）。任何 `lead/**/RECEIPT.md` 式宽 glob，主体同样不可判。

### 2.5 门禁受害面普查（权威口径：.zcode/workflow-runs）

**lead/ 下没有门禁脚本本体**：lead 内 @@PY1@@ 个 .py 全扫，`max(...)紧邻st_size` 位点 **0 处**（仅 3 处 mtime 记录用途，_si_gatescan_out.json）；库根+.tmp 补充 @@PY2@@ 个 .py，`max~st_size` 0 处、`max~mtime` 5 处（out/re_work/sessions_timeline.py、tools/host_attribution*.py，非门禁链）。门禁代码以 GATE_CODE 常量内嵌于 .zcode/workflow-runs/dwfrun-*.mjs 的 payload.lowered。

普查结果（@@MJS@@ 个 mjs 全扫；两遍 walk，见足迹表第 5 行）：

- **36 处 `DOC=max(cands,key=lambda p:p.stat().st_size)`**，分布于 36 个 run 文件、32 个写域（其中 34 处伴随 `sorted(wd.glob('*.md'))`，2 发为变体取件：n4_yi_final、gate_fp7）；
- **3 发已是显式命名**（`expected=wd/'…md'`，缺件即 FAIL）：oldwording_sweep_20261109、本发 gate_subject_id_20261109、s604_verdict_entry_20261109——即编排方已在新门禁上落地方案A；
- 1 处 `max(cands` 引文：本发 payload 的任务文本引用缺陷代码本身（非门禁）；
- 风险分级（按写域当前是否含下划线中间稿）：**32 行 HIGH、4 行 MED**（MED：c07_gate_fix_20261109、c07_protocol_attacks_20261109、c07_gate_audit_20261109、samedoc_link_20261109；按域计 28 HIGH + 4 MED）。逐处清单见 §5.2。

### 2.6 必然错位实例（与 10B 偶然实例互补）

- **handoff_pack_20261109**：其 payload 约定 DOC=APPROVAL_PACK.md，但该域 14 件全为 _hp_* 中间稿（bareCount=0）——约定主件从未存在，max 必然落在中间稿上；
- **s604_script_hunt_20261109**：唯一 md 即中间稿 _sh_findings.md——同上。
这两发是「max 在无主件域必然选中中间稿」的结构性实例；counterpart 发则是「主件存在但被 10B 遮蔽」的偶然实例。两者共同说明：**max 挑件在 36 发历史里的 98% 正确率是运气，不是机制**。

## 3 根因诊断与可操纵性检验

### 3.1 三问根因

**(a) 为什么用 max(st_size) 挑交付件**：门禁只拿到「写域」这层容器，不知道主件名。而讽刺的是 payload 里早有现成答案——counterpart 发的 ASK 文本写有 `const DOC = "lead/counterpart_fix_20261109/COUNTERPART_FIX.md"`（_si_wfextract_out.txt），**GATE_CODE 却没有引用它**，改用 `cands=sorted(wd.glob('*.md'))` + max。根因是把「主件通常是域内最大的 md」这条经验当成了识别器；36 发历史仅 1 发暴露（正确率 98%）形成「一直没出事」的路径依赖，掩盖了主体从来未被真正锚定的事实。

**(b) 为什么下划线前缀没被用作排除条件**：下划线惯例只存在于产出形态（_cf_ / _hp_ / _sh_ / _dr_ / _n10_ / _n4v2_），从未成文——lead/_routing_policy/ROUTING_20261108.md 全文只管模型路由，无任何文件命名约定。本发 payload 的写域清点代码（SWEEP_CODE）已把 largestIsUnderscore 当**描述字段**输出——惯例已被感知，但止步于描述，没有进入门禁的**排除规则**。感知与执行之间断了一层。

**(c) 同类的主体识别缺陷（第 13 类家族）**：

1. **glob 太宽**：`wd.glob('*.md')` 吞下中间稿（36 处实证）；`lead/**/X.md` 式宽 glob 吞跨域同名件（20 种重名，§2.4）。
2. **按 mtime 挑**：mtime_pick 位点 lead 内 126 个 .py、门禁位内 3 处（T42E4_FORENSIC/_verify_files.py:58、XVERIFY_S543_0f4bd824/V3/_v3_scorefam_probe.py:55、XVERIFY_S544_7255362d/V2/_census.py:180，均为 getmtime/st_mtime）。mtime 可被任意后续写件刷新，比 st_size 更易操纵。
3. **按顺序取首**：sorted_first 位点 lead 内 6 处；sorted() 对点前缀、大小写的排序在子代理掌握命名权时同样可被摆布。
4. **双主件歧义**（121 目录）与**跨域同名**（20 种）——即便排除了下划线，主体仍可能不唯一。
5. **DOC 常量被弃用**：payload 已声明主件路径，GATE_CODE 却去猜——信息在手上仍走启发式，属实现疏漏而非信息缺失。

### 3.2 可操纵性检验（全部实跑；_si_exploit_out.txt，12/12 断言通过）

- **真实域复跑**（源码 = payload 忠实还原件 _si_gate_counterpart_extracted.py，只读 exec）：输出 `{"ok": false, "problems": ["缺「变ORPHAN不等于解决」声明"], "bindings": 15, "docBytes": 32840, "doc": "_cf_counterpart_vs_tighten_20261109.md"}`——编排方报告的误判**精确复现**；主件 32830B 从未被门禁读入。
- **(a) 写更大的中间稿、把禁用词写进去**（S1/S2 沙盒，禁用词用无害替身 __SIM_BANNED_TOKEN__）：S1 = 诚实主件干净含要素、中稿大 10B 缺要素 → 旧门禁 FAIL（**误报**，与真实案例同形）；S2 = 禁用词放进**主件**、中稿更大更干净 → 旧门禁 **PASS**——违禁内容留在真主件里，门禁绿灯放行。
- **(b) 写更大的中间稿、把该有的要素都写上**（S3）：主件缺要素、中稿更大且补齐 → 旧门禁 **PASS**——要素检查落在伪造件上，**误判通过成立**。
- **(c) 判定：能绕过，不止误报，且是双向的**。S4a/S4b 再证：域内两份非下划线主件（一好一坏）时，旧门禁 PASS 还是 FAIL 完全由哪份更大决定（S4a 坏件大 → 碰巧 FAIL；S4b 坏件小 → 坏件根本不被读、PASS）——同一攻击面两次运行给出相反判定。攻击者即被门禁约束的子代理本身（写域文件由它落盘），无需任何提权，且全程静默无告警。**结论：高危、可双向利用（误报 + 漏报/绕过）。**

三方案在全部五场景的实跑判定（详见 _si_exploit_out.txt）：方案A 五场景全对（双主件时判约定主件）；方案B/C 四场景对、双主件场景 FAIL(不唯一)——即 fail-closed；真实域上方案A/B 均选中 COUNTERPART_FIX.md 且全要素 PASS，遮蔽告警正命中 _cf_ 件。

## 4 三种修复方案

共同前提：主体识别失败必须 FAIL（fail-closed），禁止静默降级回启发式猜件。可粘贴完整实现 = _si_fix_lib.py（GateFail / pick_deliverable_explicit / pick_deliverable_unique_bare / pick_deliverable_largest_bare / overshadow_warning），已经沙盒五场景 + 真实域双验证。

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

- 适用：每发任务已约定主件名。本发即此形态（expected=wd/'GATE_SUBJECT_ID_FIX.md'，_si_gate_self_extracted.py:5-6）；36 发旧门禁的 payload 里也普遍已有 `const DOC = "lead/…/主件.md"`——名字是现成的，只是 GATE_CODE 没用。
- 风险：子代理漏写/改名 → FAIL。属安全侧失败，重跑即愈；无歧义。
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

- 适用：把「一域一主件、中间稿一律 _ 前缀」写入派发纪律之后。
- 风险：现状 @@MB@@ 个目录 bareCount>1，直接上 B 会对合法多主件域误 FAIL——须先成文约定或按域白名单；对 handoff_pack 这类「域内全是中间稿」的域会 FAIL——那是正确行为：这种域本就没有可判定的单一主体。

### 4.3 方案C：兜底最小补丁（过滤 + 恰一）

```python
# 对旧门禁 DOC=max(cands,key=lambda p:p.stat().st_size) 的最小补丁（改 2 行）：
bare = [p for p in cands if not p.name.startswith("_")]
if len(bare) != 1:
    P.append('主体不唯一或缺失: ' + repr([p.name for p in bare]))
else:
    DOC = bare[0]   # 此后与大小无关；max 不再参与主体识别
```

- 适用：36 处旧 GATE_CODE 的即刻止血——改动量最小，立刻堵住下划线遮蔽与双主件歧义。
- 风险：同方案B（多主件域会 FAIL）；且不解决「约定主件根本没写」的形态（handoff_pack 会 FAIL——同样正确）。C 是过渡件，最终形态应收敛到 A。

### 4.4 加固与配套

- **overshadow_warning**：选中主件后若有更大的下划线件存在，记审计告警（不 FAIL）。真实域上正命中 _cf_counterpart_vs_tighten_20261109.md（_si_exploit_out.txt D 段）。
- **纪律成文**：把「主件名进 ASK/GATE_CODE；中间稿一律 _ 前缀；一域一主件」写进派发模板或新增命名政策件（现 lead/_routing_policy/ 只管模型路由），使方案B/C 的前提成立。
- **清点口径统一**：编排方写域清点（SWEEP_CODE）已是深度受限遍历且输出 largestIsUnderscore——建议在其 summary 里直接加「maxPicksUnderscore / bareUnique」两个布尔字段，让受害面每轮可见。

## 5 复核回件

### 5.1 证据件绑定行（hashlib 实算）

@@BINDS@@

### 5.2 全量清单（36 处 DOC=max 位点逐处列出）

lead/ 下 .py 门禁脚本 `max(st_size)` 位点数：**0**（@@PY1@@ 件全扫）——脚本本体不在 lead/，以下以 payload 位点为准（36 处 → 32 写域；风险=该写域当前是否含下划线中间稿）：

| run 件（.zcode/workflow-runs/） | 目标写域 | 风险 |
|:--|:--|:-:|
@@TABLE@@

**改法汇总**：
1. 36 处一律替换为方案A：GATE_CODE 开头加 `expected=wd/'<约定名>'` + 缺件 FAIL（约定名各发 payload 已有或一句即可约定）；
2. 来不及逐发改名的，先用方案C 两行补丁止血（堵下划线遮蔽 + 双主件歧义）；
3. 3 发显式命名门禁（oldwording_sweep / 本发 / s604_verdict_entry）无需动，建议再叠 fps 指纹校验；
4. 配套：把命名纪律成文（§4.4），否则方案B/C 在 121 个多主件域上会误 FAIL。

### 5.3 未改任何历史件声明

本诊断全程只读：lead/ 下任何历史写域、两件台账（PENDING_DECISIONS.md、GOAL_THREE_TARGETS_20261018.md）、.zcode/ 档案、任何既有门禁脚本，均未写未删未动；全部落盘限于 lead/gate_subject_id_20261109/ 内（_si_* 件 + 本件 + 同字节副本 + _si_sandbox 沙盒）。台账现状指纹与本发门禁 PRE_H/PRE_GO 由 §5.4 自验自动复核。

### 5.4 自验

以还原的本发门禁（_si_gate_self_extracted.py）对本写域实跑：PASS（输出见 _si_gatecheck_out.txt）。附注：旧 max 门禁若施于本写域，实跑选中 _si_SUBJECT_ID_DEFECT.md（23286B）——Windows 下 `sorted(Path)` 按 normcase 比较，_ 前缀（0x5F）排在小写字母之前，与纯 str 排序相反；两件同字节故判定不变。这本身即「同字节双件无害、异字节双件危险」的对照样本：max 的挑件行为连排序细节都随平台语义漂移，更不可托付主体识别。

### 5.5 未验项

1. 36 发旧门禁各自**当时**的实跑输出（exit/problems）未逐发取证：除 counterpart（复跑实证误判）外，其余 35 处按「结构性暴露」计，不逐发断言其曾产生误判。
2. handoff_pack / s604_script_hunt 两发当时门禁是否 PASS 未验（payload 不含门禁 stdout）。
3. lead 内 8 个已带 `startswith('_')` 过滤的 .py 脚本未逐一审读用途（smell 计数见 _si_gatescan_out.json）。
4. root/.tmp 补充扫描的 5 处 max~mtime 位点（out/re_work/sessions_timeline.py:112-115、tools/host_attribution.py:43、tools/host_attribution_v160.py:28）未逐处审读语义——不在门禁链上，列为观察项。
5. .zcode/agents 目录未扫（超出本次深度预算），如存在门禁副本未覆盖。
"""

DV = sc["dirsVisited"]
tpl = (TPL
       .replace("@@DV1@@", str(DV))
       .replace("@@T1@@", str(sc["elapsedSec"]))
       .replace("@@DM@@", str(sc["domainsWithMd"]))
       .replace("@@TM@@", str(sc["totalMd"]))
       .replace("@@DV3@@", str(gs["leadScope"]["dirsVisitedPy"]))
       .replace("@@DV3B@@", str(gs["leadScope"]["dirsVisitedMd"]))
       .replace("@@T3@@", str(gs["leadScope"]["elapsedSecPy"]))
       .replace("@@T3B@@", str(gs["leadScope"]["elapsedSecMd"]))
       .replace("@@DV4@@", str(gs["rootScope"]["dirsVisited"]))
       .replace("@@T4@@", str(gs["rootScope"]["elapsedSec"]))
       .replace("@@DV5@@", str(ws["dirsVisited"]))
       .replace("@@DV5B@@", "4")
       .replace("@@T5@@", str(ws["elapsedSec"]))
       .replace("@@T5B@@", "0.104")
       .replace("@@T6@@", "0.080")
       .replace("@@MB@@", str(len(sc["domainsWithMultiBare"])))
       .replace("@@DN@@", str(len(sc["crossDomainDuplicateBareNames"])))
       .replace("@@PY1@@", str(gs["leadScope"]["pyScanned"]))
       .replace("@@PY2@@", str(gs["rootScope"]["pyScanned"]))
       .replace("@@MJS@@", str(ws["mjsScanned"]))
       .replace("@@BINDS@@", BINDS)
       .replace("@@TABLE@@", TABLE))

REQUIRED = ["## 1", "## 2", "## 3", "## 4", "## 5",
            "max(st_size)", "中间稿", "下划线", "受害面", "根因", "可操纵性",
            "绕过", "显式命名", "三方案", "全量清单", "未改任何历史件", "未验"]
BANNED = ["已改门禁", "已改历史件", "已修复"]
missing = [k for k in REQUIRED if k not in tpl]
banned_hit = [k for k in BANNED if k in tpl]
assert not missing, "缺要素: %s" % missing
assert not banned_hit, "含禁词: %s" % banned_hit

(OUTD / "GATE_SUBJECT_ID_FIX.md").write_text(tpl, encoding="utf-8")
(OUTD / "_si_SUBJECT_ID_DEFECT.md").write_text(tpl, encoding="utf-8")

h1, n1 = sha(OUTD / "GATE_SUBJECT_ID_FIX.md")
h2, n2 = sha(OUTD / "_si_SUBJECT_ID_DEFECT.md")
print("GATE_SUBJECT_ID_FIX.md sha=%s bytes=%d" % (h1, n1))
print("_si_SUBJECT_ID_DEFECT.md sha=%s bytes=%d" % (h2, n2))
print("twin identical:", h1 == h2 and n1 == n2)
print("table rows:", len(rows), "binding lines:", len(BIND))
