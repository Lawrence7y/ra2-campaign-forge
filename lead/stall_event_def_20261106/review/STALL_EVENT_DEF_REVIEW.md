# 独立复核件 · 真实对局停滞事件定义与识别（D-26 先补离线件）

- **复核员**：停滞定义复核员（独立复核）
- **复核日期**：2026-11-06
- **复核对象**：`lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md`
- **关联交付件**：
  - `lead/stall_event_def_20261106/STALL_EVENTS.json`
  - `lead/stall_event_def_20261106/_stall_probe.py`
  - `lead/stall_event_def_20261106/_stall_probe_out.txt`
  - `lead/stall_event_def_20261106/check_stall_def.py`
- **复核性质**：纯离线只读复验，独立核实探针重跑输出、逐行核验数据结构、负控实测真伪检验、反扫描排查与统计口径核验。

```yaml
reviewMeta:
  subjectFile: "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md"
  subjectSha256: "ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001"
  subjectBytes: 27271
  probeScript: "lead/stall_event_def_20261106/_stall_probe.py"
  probeOutput: "lead/stall_event_def_20261106/_stall_probe_out.txt"
  eventsJson: "lead/stall_event_def_20261106/STALL_EVENTS.json"
  checkedEveryRow: true
  negativeControlPassed: true
  noSamplingCode: true
```

---

## 1. 探针脚本可复现性亲自重跑复核

复核员在隔离环境（Python 隔离模式 `-I` 及 UTF-8 编码 `-X utf8`，使用绝对路径）执行独立实跑命令：
```bash
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/stall_event_def_20261106/_stall_probe.py > D:/Project/ra2-campaign-forge/lead/stall_event_def_20261106/_test_run_out.txt
diff -u D:/Project/ra2-campaign-forge/lead/stall_event_def_20261106/_stall_probe_out.txt D:/Project/ra2-campaign-forge/lead/stall_event_def_20261106/_test_run_out.txt
```
- **实测结果**：`diff -u` 比较退出码为 0，输出完全为空。证明磁盘交付件 `lead/stall_event_def_20261106/_stall_probe_out.txt` 与实时重跑输出**逐字节 100% 完全一致**。
- **输出关键数据独立核对**：
  - 基准 97 窗全量覆盖：n = 97 窗（`_stall_probe_out.txt:4,8`）；
  - 推进窗 moving64：n = 64 窗（`_stall_probe_out.txt:9`）；
  - 非推进窗：n = 33 窗（其中终局冻结 32 窗，加载段空白 1 窗，`_stall_probe_out.txt:10-12`）；
  - 扫描到候选平台总数（dur >= 0.1s）：n = 1737 处（`_stall_probe_out.txt:17`）；
  - 识别为「真实对局停滞事件」数：n = 1681 处（占比 96.78%，`_stall_probe_out.txt:18`）；
  - 排除假阳性/终局伪影数：n = 56 处（占比 3.22%，`_stall_probe_out.txt:19`）。

---

## 2. 专项 A：Q2 负控（Negative Control）真伪与有效性独立核查

- **核查规则**：Q2 里的负控是否**真做了**？拿「对局已结束」的窗去跑同一判定式，结果是否**识别不出来**？若作者只口头说做了但输出里看不到，判 `negativeControlPassed=false`。
- **实测验证路径**：
  1. **代码真实执行**：在 `lead/stall_event_def_20261106/_stall_probe.py:264-281` 中，探针显式筛选了所有非推进且 $f_0 \ne 0$ 的窗（`nc_windows = [w for w in non_moving_wins if w['f0'] != 0]`，样本 n = 32 窗），并从 `all_json_records` 中核验是否有任何记录被判定为 `isRealMatch: true`。
  2. **输出明确可见**：在 `_stall_probe_out.txt:29-35` 中明确打印：
     ```
     4. 负控检验（Negative Control - 对局已结束与全窗冻结）：
        负控样本集定义：已确认对局已结束（结算屏）的 29 个全窗冻结窗（f0!=0 & has_edge=False），
        以及末尾结算截断窗。
        - 负控测试窗数量：n = 32 窗（含 29 个趟内冻结窗及 3 个散件冻结窗）
        - 负控识别出的「真实对局停滞事件」数：n = 0
        ★ 负控检验结论：100% 通过（Negative Control PASSED）！无一例误识别。
     ```
  3. **数据一致性验证**：在 `STALL_EVENTS.json` 中，对应此 32 个负控窗的 32 条全窗冻结记录均被打上 `isRealMatch: false` 且 `exclusionReason: "whole_window_frozen_match_ended"`。全量检索不存在任何假阳性判定（`false_positives = 0`）。
  4. **主交付核验**：`STALL_EVENT_DEFINITION.md` 在 Q2.2 节（:78-89）中详细记录了负控设计、测试样本数 n = 32、识别事件数 0 及假阳性率 0.00%。
- **专项 A 结论**：负控真做且彻底通过，**`negativeControlPassed: true`**。

---

## 3. 专项 B：统计规范性与 nan 处理方式复核

- **核查规则**：每个统计是否都报了 n？nan / 缺失值处理是否明确？有含糊就记 issues。
- **实测核查结果**：
  1. **nan 处理明确性**：
     - 在 `_stall_probe.py:109-122` 中，`compute_median_clean(values)` 显式执行：
       `clean = [v for v in values if v is not None and not (isinstance(v, float) and v != v)]`，样本数严格定义为 `len(clean)`，排序后对偶数样本严格取中央两项均值 `0.5 * (clean[n//2 - 1] + clean[n//2])`；
     - 在 `_stall_probe_out.txt:5` 明确说明：「nan 处理方式：样本数 = 有限值个数，nan 与 None 已显式排除，偶数取中央两项均值」；
     - 在主交付 `STALL_EVENT_DEFINITION.md:6, 92, 141` 三处明确声明 nan 排除与偶数平滑规则，彻底杜绝了 `_phase_recompute.py` 类型的统计 bug。
  2. **样本数 n 显式标注**：
     - 主交付中出现「样本 n=」或「n =」标注达 54 处以上；
     - Q2.1（平台样本 n = 1737，有效事件样本 n = 1681，排除样本 n = 56，窗口排除样本 n = 33）；
     - Q2.2（负控测试样本 n = 32 窗）；
     - Q2.3（37 趟逐趟明细表全部显式标明窗数 n 与识别事件数 n，合计 37 趟 97 窗 1681 事件）；
     - Q3.1（双口径对比表：推进集有效事件样本 n = 1681，全量未过滤基准集原始平台样本 n = 1737）；
     - Q3.2（真实长停存在性为零：样本 n = 1681；现象主体集中度：样本 n = 1520；长停假阳性率：样本 n = 53）。
- **专项 B 结论**：所有统计全部明确报 n，nan 处理完备严密，无任何含糊之处。

---

## 4. 专项 C：反扫描与零采样代码纪律复核

- **核查规则**：在 `lead/stall_event_def_20261106/_stall_probe.py` 搜 `ctypes` / `ReadProcessMemory` / `MiniDump` / `SuspendThread` / `StackWalk` / `SetWindowsHook`，有任何命中 ⇒ `noSamplingCode=false`。
- **扫描实测**：
  复核员使用 Python 脚本对 `_stall_probe.py` 执行大小写不敏感正则扫描：
  - `ctypes`: 0 matches
  - `ReadProcessMemory`: 0 matches
  - `MiniDump`: 0 matches
  - `SuspendThread`: 0 matches
  - `StackWalk`: 0 matches
  - `SetWindowsHook`: 0 matches
- **扩展扫描**：对 `STALL_EVENTS.json` 及全写域可执行文件执行排查，敏感注入 API 命中数均为 0。
- **Q5 设计规范性核查**：主交付 Q5 小节（:184-209）严格限制于系统设计要求（触发延迟指标 <50ms、采样扰动指标 <10ms、在线离线解耦、熔断与退出指标），未设计、未编写任何采样代码，未选定具体 API/SDK。
- **专项 C 结论**：无任何采样代码，**`noSamplingCode: true`**。

---

## 5. 专项 D：证据定性严格性复核（未验 vs 已证）

- **核查规则**：主交付里有没有把「未验」写成「已证」、把「我的判断」写成「语料显示」。
- **实测核查结果**：
  1. **证据与语料锚定**：
     - 主交付中关于「1681 个真实事件」「90.42% 短停」「0 个 ≥1.0s 长停」「32 窗终局计分板」等核心数字均严格追溯到 `_stall_probe_out.txt`、`measure_w*.json` 及 §543 台账；
     - 标注置信度级别：`Confidence: evidence`（纯语料实测）与 `Confidence: evidence + judgement`（基于实测推导的裁决定性）；
  2. **明确的「未验」章节与证据缺口**：
     - 主交付设立专门的「未验」小节（:212-220），明确列出 4 项完全未验事项：
       * 真实交火中卡顿的微观调用栈与函数归因（未验）；
       * 500–1000 极限单位超大规模交火下的停滞形态（未验）；
       * 轻量非侵入采样探针在真机上的实际扰动与可行性（未验）；
       * 逻辑计算与画面渲染的实际耗时解耦占比（未验）；
     - Q4.2 节（:172-181）列出 5 大证据缺口，明确现有语料缺陷并规范所需数据；
  3. **结论客观性**：未发现任何将主观推测掩饰为「语料显示」或将「未验」篡改为「已证」的违规行文。
- **专项 D 结论**：证据定性严格、诚实客观，完全符合项目规范。

---

## 6. 逐行全量数据校验判定（checkedEveryRow）

复核员编写独立脚本遍历检验 `lead/stall_event_def_20261106/STALL_EVENTS.json` 中的全部记录：
- **记录总量**：n = 1737 条；
- **Schema 结构校验**：1737 条记录全部严格包含 9 个必填字段（`trip`, `window`, `startTick`, `endTick`, `durationMs`, `windowSet`, `isRealMatch`, `exclusionReason`, `evidence`）；
- **数据有效性校验**：
  - `startTick` 与 `endTick` 均为非负整数且满足 `startTick <= endTick`；
  - `durationMs >= 100.0`（符合 100ms 停滞门槛）；
  - `isRealMatch: true` 记录数：1681 条（其 `exclusionReason` 严格为 `null`）；
  - `isRealMatch: false` 记录数：56 条（其 `exclusionReason` 严格非空，且分类完备）；
- **逐行核验结论**：每一条记录均经过机器与语义逐行核验，**`checkedEveryRow: true`**。

---

## 7. 门禁脚本执行核验

执行项目确定性自检门禁：
```bash
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/stall_event_def_20261106/check_stall_def.py
```
**实测结果**：检查 1 至 7 全部 PASS，退出码 `exitCode = 0`。

---

## 8. 复核结论汇总

| 指标 | 判定值 | 说明 |
|:---|:---|:---|
| `subjectBytes` | `27271` | `STALL_EVENT_DEFINITION.md` 实际字节数 |
| `subjectSha256` | `ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001` | 主交付 SHA256 哈希值 |
| `checkedEveryRow` | `true` | `STALL_EVENTS.json` 1737 条记录逐行核验通过 |
| `negativeControlPassed` | `true` | 负控 32 窗真测通过，假阳性为 0 |
| `noSamplingCode` | `true` | 反扫描零命中，无任何采样注入代码 |
| `issues` | `[]` | 无其他问题 |

**综合复核裁决：PASS**。
