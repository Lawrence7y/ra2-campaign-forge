# D13B_DESIGN_REVIEW.md · 独立设计复核件（四项专项，逐项全量、未抽样）

**复核员**：D-13b 设计复核员（新上下文，独立复核）。**日期**：2026-11-06。
**被核对象（题给【待复核】五件）**：`lead/d13b_design_20261106/D13B_DESIGN.md`、`BUDGET_MODEL.json`、`_state_machine.py`、`_test_state_machine.py`、`_test_out.txt`。
**唯一写域**：`lead/d13b_design_20261106/review/D13B_DESIGN_REVIEW.md`（本次新建 `review/` 目录只用于写本件 + 跑测临时文件，重跑临时文件已删）。母本五件一字未改；只读域一字未改；零真机、零采样、不 commit / 不 push；Python 全部 `python -I -X utf8` + 绝对路径。
**纪律**：不写报告/摘要外的文件；所有判定均引「文件:行」或本会话实跑输出；未跑的不宣称通过。

---

## 0 复核结论（机器可读字段）

```
subjectSha256: 17de49554d71925079c47db19fed915d4c1656e304f6a7c8623cff0523f47ae7
subjectBytes: 40374
checkedEveryRow: true
noSamplingCode: true
budgetSelfConsistent: true
coversUnverified: true
```

**四项专项判定**：专项 1 反扫描 **PASS（0 命中）**／专项 2 预算自洽 **PASS（152.50 == 152.50，meetsMedian=false 与 152.50 ≥ 129.93 一致）**／专项 3 未验诚实 **PASS（四项全覆盖；无估算冒充实测、无 [待论证指标] 冒充已达成）**／专项 4 不复制原缺陷 **PASS（写成保守预算，不是语义真值）**。
**单测亲自重跑**：`PASS=43 FAIL=0`，与存档 `_test_out.txt` 逐字节一致（§6）。
**issues**：1 条低危出处核对提示（段① 间隔数未能按同一 97 窗集合精确复现，见 §8），不翻转任何一项判定。

**指纹口径说明（沿用本仓既有复核件惯例）**：`subjectSha256` / `subjectBytes` 取**主交付件 `D13B_DESIGN.md`** 实算值（先例：`lead/b2b_design_20261106/review/B2B_DESIGN_REVIEW.md:13-14`、`:205`，两个被核对象时只取主文书、其余指纹另列对照表）。五件逐件指纹与按题给顺序拼接的复合指纹全部列于 §1，任一解释口径均可对照。

---

## 1 前置：五件指纹实算（双工具交叉核对）

实跑命令 1（`sha256sum` + `wc -c`，Git Bash）：

```
for f in D13B_DESIGN.md BUDGET_MODEL.json _state_machine.py _test_state_machine.py _test_out.txt; do wc -c "lead/d13b_design_20261106/$f"; sha256sum "lead/d13b_design_20261106/$f"; done
```

实跑命令 2（`python -I -X utf8` + `hashlib`，绝对路径，交叉核对）：

```
python -I -X utf8 - <<'PY'
import hashlib
base = 'D:/Project/ra2-campaign-forge/lead/d13b_design_20261106/'
files = ['D13B_DESIGN.md','BUDGET_MODEL.json','_state_machine.py','_test_state_machine.py','_test_out.txt']
blob = b''
for f in files:
    d = open(base+f,'rb').read(); blob += d
    print(f, hashlib.sha256(d).hexdigest(), len(d), len(d.splitlines()))
print('COMPOSITE', hashlib.sha256(blob).hexdigest(), len(blob))
PY
```

两命令结果逐位一致：

| 文件 | SHA256 | 字节 | 行（splitlines） |
|:--|:--|--:|--:|
| `D13B_DESIGN.md` | `17de49554d71925079c47db19fed915d4c1656e304f6a7c8623cff0523f47ae7` | 40374 | 306 |
| `BUDGET_MODEL.json` | `db5b8eb5456283fa0aca043127e878d4902f094ad6ee75645bf0376a3358bf66` | 6862 | 35 |
| `_state_machine.py` | `b1ff8c67167553b218b489928daee442525d11c6b79fc172f4db903dadd9a600` | 23834 | 415 |
| `_test_state_machine.py` | `d7fb6f55c07d5cb0cf983b0b1f920407b91ad122a7d1afece95cfea879e92d66` | 14509 | 273 |
| `_test_out.txt` | `4d9f220f64cc79a0c9d4a7a1e672f2023399a21fd6e09baa2c23e497bc3a6f62` | 5135 | 69 |
| **复合（按上列顺序拼接 5 件）** | `0c8e9689018f0e4d3272c9bd5869356b7180d6a68f210d3530d360abecaca227` | 90714 | — |

`_state_machine.py` 415 行与 `_test_state_machine.py:96-99` 断言、`_test_out.txt:10`（`lines=415`）一致。`_test_out.txt` 69 行，末行 `PASS=43 FAIL=0`（`:69`）与 `D13B_DESIGN.md:167` 引用一致。

---

## 2 专项 1 · 反扫描（11 关键词 × 2 文件，全量、未抽样）

**题给关键词全集**：`ctypes` / `OpenProcess` / `ReadProcessMemory` / `WriteProcessMemory` / `VirtualAllocEx` / `CreateRemoteThread` / `SetWindowsHook` / `MiniDump` / `SuspendThread` / `StackWalk` / `TerminateProcess`（与 `TASK.md:144-146` 专项 A、`D13B_DESIGN.md:237` 所列一致；`SetWindowsHook` 为前缀，可同时覆盖 `SetWindowsHookEx`；`MiniDump` 为前缀，可同时覆盖 `MiniDumpWriteDump`）。

实跑命令 3（每文件逐关键词 grep）：

```
grep -niE 'ctypes|OpenProcess|ReadProcessMemory|WriteProcessMemory|VirtualAllocEx|CreateRemoteThread|SetWindowsHook|MiniDump|SuspendThread|StackWalk|TerminateProcess' _state_machine.py _test_state_machine.py
for f in _state_machine.py _test_state_machine.py; do grep -ciE '<同一关键词集>' "$f"; done
```

输出：`grep exit=1`（零命中，无任何行列打印）；`_state_machine.py hits=0`；`_test_state_machine.py hits=0`。

实跑命令 4（Python 逐关键词 × 逐文件矩阵，大小写敏感 + 不敏感双模式，绝对路径、`-I -X utf8`）：

```
python -I -X utf8 - <<'PY'  # 读两文件全文，对 11 关键词逐一做 in 判定，ci 与 cs 各一次
... 输出 11 行矩阵 ...
PY
```

输出（节选与合计）：

```
keyword                _state_machine _test_state   (case-insensitive + case-sensitive substring)
ctypes                 ci=False cs=False  ci=False cs=False
OpenProcess            ci=False cs=False  ci=False cs=False
ReadProcessMemory      ci=False cs=False  ci=False cs=False
WriteProcessMemory     ci=False cs=False  ci=False cs=False
VirtualAllocEx         ci=False cs=False  ci=False cs=False
CreateRemoteThread     ci=False cs=False  ci=False cs=False
SetWindowsHook         ci=False cs=False  ci=False cs=False
MiniDump               ci=False cs=False  ci=False cs=False
SuspendThread          ci=False cs=False  ci=False cs=False
StackWalk              ci=False cs=False  ci=False cs=False
TerminateProcess       ci=False cs=False  ci=False cs=False
TOTAL HITS (all keywords x both files x both modes) = 0
```

额外（超出题给最小集的自查，实跑命令 5）：

```
grep -nE '\b(exec|eval|compile|__import__|open\(|ctypes|winreg|msvcrt|mmap)\b|^[[:space:]]*(import|from) ' _state_machine.py _test_state_machine.py
grep -niE 'win32|psutil|subprocess|os\.system|hook|inject|dump|suspend|RemoteThread|VirtualAlloc|kernel32|user32|LoadLibrary|GetProcAddress' _state_machine.py _test_state_machine.py
```

输出仅 3 行，全部为白名单/说明：
- `_test_state_machine.py:26` `import importlib.util`（仅按绝对路径加载同目录状态机，`:29-33` 为 `spec_from_file_location`；非系统接口、非采样 API）；
- `_test_state_machine.py:36` `open(_SM_PATH, encoding="utf-8").read()`（只读文本内省，`:35` 注释明示「不执行、不注入」）；
- `_test_state_machine.py:14` 文档字符串「无 `exec` / `eval` / `compile`」（陈述，非调用）。

`_state_machine.py` **无任何 import/from 语句**（全文 415 行，`:2`、`:10` 自述「零 import / 零系统接口」；`_test_out.txt:10` 断言 PASS）。两文件均无 `exec(` / `eval(` / `compile(` 调用，无「单测包装实际采样 API 调用」形态。

⇒ **noSamplingCode = true**（11 × 2 × 2 = 44 个判定格逐格核过，零命中）。

---

## 3 专项 2 · 预算自洽（自己加，不引用交付件的自算结果）

实跑命令 6（独立重算，绝对路径、`-I -X utf8`）：

```
python -I -X utf8 - <<'PY'
import json
bm = json.load(open('D:/Project/ra2-campaign-forge/lead/d13b_design_20261106/BUDGET_MODEL.json', encoding='utf-8'))
segs = bm['segments']; s = 0.0
for x in segs:
    print('  %-18s ms=%8.4f  offlineVerifiable=%s' % (x['seg'], x['ms'], x.get('offlineVerifiable')))
    s += x['ms']
print('SUM of segments   = %.4f' % s)
print('totalMs (declared)= %.4f' % bm['totalMs'])
print('sum == totalMs    = %s' % (abs(s - bm['totalMs']) < 1e-9))
print('zero/neg segments = %d' % sum(1 for x in segs if x['ms'] <= 0))
print('meetsMedian(decl) = %s' % bm['meetsMedian'])
print('152.50 < 129.93   = %s' % (s < 129.93))
print('gap (sum-129.93)  = %.4f' % (s - 129.93))
print('meetsMedian consistent with fact = %s' % (bm['meetsMedian'] == (bm['totalMs'] < 129.93)))
PY
```

输出（完整）：

```
segments count = 4
  event_onset        ms=  2.5000  offlineVerifiable=False
  threshold_accum    ms=100.0000  offlineVerifiable=True
  poll_dispatch      ms= 48.0000  offlineVerifiable=False
  capture_exec       ms=  2.0000  offlineVerifiable=False
SUM of segments   = 152.5000
totalMs (declared)= 152.5000
sum == totalMs    = True
zero/neg segments = 0
meetsMedian(decl) = False
152.50 < 129.93   = False
gap (sum-129.93)  = 22.5700
meetsMedian consistent with fact = True
```

逐段核对（`BUDGET_MODEL.json` 行号）：① `event_onset` 2.5（`:6`）② `threshold_accum` 100.0（`:13`）③ `poll_dispatch` 48.0（`:20`）④ `capture_exec` 2.0（`:27`）。
**自己加**：`2.50 + 100.00 + 48.00 + 2.00 = 152.50`，与 `totalMs = 152.5`（`:32`）相等；无 0 / 负段（遵 `TASK.md:87`）。
**与 129.93 比较**：`152.50 ≥ 129.93`，超出 `22.57ms` ⇒ `meetsMedian=false`（`:33`）与事实**一致**；`D13B_DESIGN.md:14`、`:38`、`:57-61`、`:74`、`:302` 均如实写「达不到 / 在当前假设下达不到」，`gapToMedian`（`BUDGET_MODEL.json:34`）亦为 `22.57ms`，无一处把 `152.50` 写成 `< 129.93` 或 `meetsMedian=true`。
口径纪律：`129.93ms` 被明确限定为 1681 个保留标签事件的中位、与 1737 个 full97 全部候选不得直接对照（`BUDGET_MODEL.json:34`；`D13B_DESIGN.md:59`；题给铁律 7）。
另外独立复现了 §2/§3 引用的 `STALL_EVENTS.json` 分桶（实跑命令 7，`python -I -X utf8`，只读 `utf-8-sig`）：`total=1737 true=1681 false=56`、`min=100.00 median=129.93 max=566.96`、`>=1000ms(true)=0`、`100-200=1520 200-500=158 500-1000=3`、`durs>=152.50 = 503 (29.923%)`、`100-200 & d>=152.5 = 342 (22.50%)`，与 `D13B_DESIGN.md:93-96`、`:220-227` 所载逐位一致 ⇒ 「本次实跑」措辞有据。

⇒ **budgetSelfConsistent = true**（4/4 段、合计、中位数比较、零负段逐项核过）。

---

## 4 专项 3 · 未验诚实（§4 四项覆盖 + 全文标记纪律）

**§4 存在性**：`D13B_DESIGN.md:256` 为 `## 4 未验`（实跑 `grep -n '^## 4 未验'`，另核 `## 1`~`## 5` 五节齐备于 `:28/:78/:144/:256/:284`，合 `TASK.md:157`）。

**四项逐行覆盖**（`D13B_DESIGN.md:260-265` 表格 4 行，逐行打开）：

| # | 未验项 | 行 | 原文命中 |
|:--|:--|:--|:--|
| 1 | **系统时延**（系统调度 / 轮询 / 中断到发出捕获指令的真实耗时；被测线程实际响应；目标线程精准定位） | `:262` | 「无法产生任何真实在线时延样本」「③=48ms 只是 :190 名义值的工程拆分 **[估算]**」 |
| 2 | **扰动**（采样动作引入的额外停顿、GC / 分页影响、对帧率的影响、无死锁） | `:263` | 「完全未验」「<10ms 只是『基于物理尺度的设计要求』」「不得为此产生真机扰动样本」 |
| 3 | **资源释放**（`100ms` 零残留、句柄与内存映射释放时序、`rc=0`） | `:264` | 「无 `rc` 可观测、无释放时序可测」「模型不背书」 |
| 4 | **栈**（真实调用栈格式、符号可解析性、函数归因、在线抓取 `≤2ms`） | `:265` | 「未采集任何进程内部指令地址（EIP/RIP）或函数栈」「离线能否解析本身 **[未验]**」 |

实跑命令 8（`sed -n '256,281p'` + 逐词 grep）：`系统时延=2`、`扰动=3`、`资源释放=3`、`栈=3`（均在 §4 正文内，非零）。扩展清单 `:269-278` 逐项标 **[未验]**；`:280` 明确「一律未跑、未验、不补造」。`_state_machine.py:108-115` 的 `UNVERIFIED` 六项同样含系统调度时延 / 扰动 / 资源释放 / 真实栈（`_test_out.txt:14` 断言 `items=6` 且四词均命中，PASS）。

**全文「把估算写成实测」排查**（逐行打开，未抽样）：

- 实跑命令 9：`grep -n '实测' D13B_DESIGN.md BUDGET_MODEL.json _state_machine.py _test_state_machine.py _test_out.txt` —— 命中 16 处，逐处判定**无一处把估算冒充实测**：
  - 否定式限定：`BUDGET_MODEL.json:26`「这是设计指标**不是实测**」；`D13B_DESIGN.md:37`「设计指标，非实测」；`:85`「**非实测**捕获成功率」；`:302`「是设计指标 / 工程估算，**不是实测**」；`_state_machine.py:101`「[估算] 设计选择（**非实测**）」。
  - 未验/未来条件式：`D13B_DESIGN.md:15`「缺的是**未授权的真机实测**」；`:68`「须有真机实测证明真实运行上界成立」；`:70`「须实测不引入额外增长」；`:306`「缺的是……真机实测」；`BUDGET_MODEL.json:34`「须有真机实测证明」「须实测不引入额外增长」；`_test_state_machine.py:220` / `_test_out.txt:53`「实测覆盖 **[未验]**」；`D13B_DESIGN.md:250`「实测覆盖 [未验]」。
  - 既有离线语料内合法度量：`D13B_DESIGN.md:101`「附……窗间间隔实测值」（离线样本内数值，§2 场景二所载 `121.54ms` 等，非系统时延实测）；`:24`「不自行重算，只引用」明示既有事实口径。
- 实跑命令 10：`grep -nE '实测|已达成|已验证|已通过|已闭合|保证|证明|背书.*通过|完全.*验证|真实.*实测' D13B_DESIGN.md` —— 全部 21 行逐处核过：`:5`/`:13`/`:302`/`:306` 的「已实跑闭合 / 已交付」均限定为**纯逻辑模型自洽、预算自洽、反扫描、分桶复算**（本会话已独立复现，见 §3、§6），并紧跟「不是真实系统表现」「不验证真实运行上界、不保证 rc=0」；`:293`「**不可保证**」；`:300`「本文不背书」；`:5`「不背书未执行的门禁/单测/核验已通过」。无一处把 `[估算]` / `[待论证指标]` 升格为实测或已达成。
- 实跑命令 11：`grep -nE '待论证指标.{0,20}(已达成|已验证|已通过|保证达成|已闭合)' <五件>` —— 仅 2 命中：`D13B_DESIGN.md:286`（转述 D-27 原文「**不得写成**『已达成』或『保证』」）、`:288`（「无一个写成已达成/保证」），均为**纪律陈述**而非达成宣称。§5（`:284-302`）九个指标逐行定位 `[待论证指标]`，「本文中的状态」列一律「未达成、未验证 / 不可保证 / 不背书」。
- 标记计数（实跑命令 12，`grep -o` 计数）：`D13B_DESIGN.md` 内 `[估算]`=14、`[待论证指标]`=33、`[未验]`=39、`[保守停止预算]`=2。`BUDGET_MODEL.json` ①③④ 三段 `offlineVerifiable=false`（`:8/:22/:29`），`label`/`basis` 均带 `[估算]`/`[待论证指标]` 且明写「真实…[未验]」。

⇒ **coversUnverified = true**（四项全覆盖；无估算冒充实测、无 `[待论证指标]` 冒充已达成）。

---

## 5 专项 4 · 不复制原缺陷（「未观察到恢复 = 结束」写成什么？）

**结论：写成 `[保守停止预算]`，不是语义真值 ⇒ 不记 issues。** 逐处代码证据（全部实读 `_state_machine.py`）：

| 位置 | 事实 |
|:--|:--|
| `:36-38` | 模块头明确点名旧缺陷 `_stall_probe.py:211-224`「未观察到恢复即判终局冻结」，并规定「本模型『未观察到恢复』一律 UNKNOWN；只有 `stall_recovered`（正向证据）才写 RECOVERED，且绝不写终局语义真值」「语义取值集合里根本不存在『结束 / 终局』这一项」 |
| `:60-68` | `SEMANTIC_VALUES = (SEM_UNKNOWN, SEM_RECOVERED, SEM_ANOMALY_REWIND, SEM_BUDGET_ONLY)`（`:68`）——**无结束/终局取值**；`:63`「UNKNOWN 是……『未观察到恢复 / 缺窗』的唯一诚实输出」 |
| `:54` / `:66` | `ST_DISARMED_BUDGET` 注「**[保守停止预算]** 命中后的少采态，非语义真值」；`SEM_BUDGET_ONLY` 注「保守停止预算命中，仍非语义真值」 |
| `:92-94` | `PARAM_BASIS["budget_stop_ms"]` = `[保守停止预算][待论证指标]`「只可作保守停止预算，不得当结束态真值；停止只会少采，不会把长停误判为不存在」 |
| `:260-267`（分支 5） | `KIND_WINDOW_END`（整窗无推进）→ `WINDOW_END_CARRIED` / `SEM_UNKNOWN`，`open_stalls` **保持打开**、携带到后续窗，不无条件判 false、不 `continue`（对治 `:169-189`） |
| `:269-274`（分支 6） | `KIND_WINDOW_GAP`（缺窗 / 未观察到恢复）→ `WINDOW_GAP_UNKNOWN` / `SEM_UNKNOWN`，注释「未观察到恢复不等于结束」，`open_stalls` 保持打开 |
| `:331-340`（分支 9b） | `dur >= budget_stop_ms` → `DISARMED_BUDGET` / `BUDGET_STOP_CONSERVATIVE` / `SEM_BUDGET_ONLY`，`extra` 附 `{"note": "[保守停止预算] 非语义真值"}`；注释「只少采，不断言长停不存在，不产生结束态语义状态」 |
| `:191-207`（`_enter_window`） | 换窗只归零窗内配额，`seen` / `open_stalls` **保留**；`DISARMED_BUDGET -> ARMED` 回退并注明「先前停滞语义仍 UNKNOWN，不改写为结束态真值」 |
| `:245-258`（分支 4） | 唯一能写 `RECOVERED` 的是正向证据 `KIND_RECOVERED`；且解除保守停止预算 |
| `:235-243`（分支 3） | `ST_EXITED` 只能由**显式** `KIND_TERMINATE` 进入（`:79` 注「不是由『未观察到恢复』推断」），且注「观测会话终态，不是对局结束态真值」；`:100` / `:408` 把 `exit_budget_ms` 标 `[待论证指标][未验]`、`exit_budget_verified=False` |

`BUDGET_MODEL.json:34` 与 `D13B_DESIGN.md:21`、`:74`、`:88`、`:108`、`:140`、`:299` 同口径：所有 `semantic_truth_written` 恒 `False`，`>1s` 仅 `budget_disarm_conservative`。合成反例由 `_test_out.txt:54-58`、`:61-63` 的 8 条断言 PASS 佐证（§6 已亲自重跑）。

---

## 6 单测亲自重跑（隔离模式 + UTF-8；核存档真实性与 FAIL=0）

实跑命令 13（`-I -X utf8`、绝对路径、stdout 重定向到 `review/` 内临时文件；临时文件跑完已删）：

```
mkdir -p review
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/d13b_design_20261106/_test_state_machine.py" > review/_rerun_tmp.txt 2>review/_rerun_err.tmp
cat review/_rerun_err.tmp
cmp -s _test_out.txt review/_rerun_tmp.txt
diff -u _test_out.txt review/_rerun_tmp.txt
grep -n 'PASS=' review/_rerun_tmp.txt | tail -1
grep -c '\[FAIL\]' review/_rerun_tmp.txt
grep -c '\[PASS\]' review/_rerun_tmp.txt
wc -c _test_out.txt review/_rerun_tmp.txt
```

输出（完整）：

```
review dir created
python exit=0
=== stderr (should be empty) ===            [空]
=== byte-identical cmp (rerun vs archived) ===
cmp exit=0 (0 = byte identical)
=== diff ===
diff exit=0 (0 = no difference)
=== PASS/FAIL line ===
69:PASS=43 FAIL=0
=== [FAIL] count ===
0
=== [PASS] count ===
43
=== sizes ===
 5135 _test_out.txt
 5135 review/_rerun_tmp.txt
10270 total
temp cleaned
```

⇒ `_test_out.txt` 是**真实输出**：重跑与存档 `cmp exit=0` / `diff exit=0` 逐字节一致（均 5135 B）；`PASS=43 FAIL=0`（`:69`）、`[FAIL]` 计数 **0**、`[PASS]` 计数 43；`stderr` 为空、退出码 0。`_test_out.txt:3` 记录的命令 `python -I -X utf8 D:/.../_test_state_machine.py` 与本次实际执行一致。

---

## 7 checkedEveryRow 的依据（逐项全量，未抽样）

| 专项 | 全量范围 | 本会话实跑 |
|:--|:--|:--|
| 1 反扫描 | 11 关键词 × 2 文件 ×（大小写敏感/不敏感）= 44 格 | 命令 3、4；另加命令 5 系统接口白名单扫描（3 处命中逐处判定） |
| 2 预算 | 4 段全部、合计、与 129.93 比较、零负段、`meetsMedian` 一致性 | 命令 6；另命令 7 独立复现 `STALL_EVENTS.json` 全部分桶数字 |
| 3 未验 | §4 四行表格逐行 + `:267-280` 扩展清单 + 五件全文「实测」16 处 / 风险词 21 行 / 标记计数 4 类 | 命令 8、9、10、11、12；只读源抽查 `RULING_D27.md:12/:42/:44`、`FREEZE_ONSET_20261103.md:18/:93` 与引用一致 |
| 4 原缺陷 | `_state_machine.py` 全文 415 行的恢复/结束/终局/终态/不存在相关 30+ 处逐处打开 | `grep -nE` 全量列出行号 + 上表 10 处代码锚点逐处实读 |
| 附加 | 单测 43 条断言全量重跑、五件指纹双工具交叉核对 | 命令 13、命令 1、命令 2 |

⇒ **checkedEveryRow = true**。

---

## 8 issues（其它问题）

1. **低危·出处核对提示（不翻转判定）**：段① `BUDGET_MODEL.json:5/:7` 与 `D13B_DESIGN.md:34` 称「复算 97 个基准窗 `samples.t` 的 **1121892** 个相邻间隔」。本会话在只读域 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/**/measure_w*.json` 实跑（命令 14，`python -I -X utf8`，逐文件读 `samples['t']` 做 `zip(t,t[1:])`）：该文件树共 **104** 个 `measure_w*.json`、合计 **1125893** 个相邻间隔；取 104−7 的最小样本子集（97 文件）得 **1121893** 个，与所称 `1121892` 相差 1。**但** dt 五个分位数在 104 文件全集上逐位复现：`median=2.4960 p90=2.5750 p99=2.9260 max=488.6160 mean=1.9999`（与 `BUDGET_MODEL.json:5` 完全一致），97 文件子集上 `median=2.4960 / mean=1.9999` 亦一致、`p99` 为 `2.9270`。因无法确定作者所用「97 窗」的确切文件集合（该树内存在 `archive_T*` 归档副本），**本项记为「未能精确核对的 1 个间隔数」，不判定为错误、不判定为造假**；且该段本身已标 **[估算]** +「既有离线 harness 的采样节拍代理，不是真实在线探测的系统时延」+「真实首次观察延迟 [未验]」（`:5`、`:7`；`D13B_DESIGN.md:34`、`:262`），`2.50ms` 只作乐观下界代理，不影响 §3 自洽结论与 §4 诚实结论。

**范围说明（非问题）**：`check_d13b.py`（`TASK.md:155-165` 确定性门禁）在本会话 `ls` 下**不存在**（`D13B_DESIGN.md:252` 已如实写「本次未运行、未验证、不宣称通过」）。门禁脚本与本次四项专项无关，本复核**未运行、不宣称其通过**；本件只按题给四项专项 + 单测重跑给出判定。

---

## 9 收束

| 字段 | 值 | 依据 |
|:--|:--|:--|
| `subjectSha256` | `17de49554d71925079c47db19fed915d4c1656e304f6a7c8623cff0523f47ae7` | 命令 1/2，`D13B_DESIGN.md` 实算；五件全量另见 §1 |
| `subjectBytes` | `40374` | 命令 1/2，`D13B_DESIGN.md` 实算 |
| `checkedEveryRow` | `true` | §7；四专项逐项全量 + 单测 43 条全量重跑 |
| `noSamplingCode` | `true` | §2；11×2×2 矩阵零命中，命令 3/4/5 |
| `budgetSelfConsistent` | `true` | §3；`152.50 == 152.50`、`152.50 ≥ 129.93` 与 `meetsMedian=false` 一致，命令 6 |
| `coversUnverified` | `true` | §4；四项全覆盖、标记纪律逐行核过，命令 8-12 |
| `issues` | 1 条低危出处核对提示 | §8 |

四项专项全部 PASS，单测亲自重跑 `PASS=43 FAIL=0` 且与存档逐字节一致；无阻断问题。母本与只读域未改动，未 commit / 未 push。
