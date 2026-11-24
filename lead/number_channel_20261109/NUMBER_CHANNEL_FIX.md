# NUMBER_CHANNEL_FIX.md — 背景段数字通道改造方案（设计件，不改任何既有件）

执行者：数字通道改造撰写员。日期 2026-11-09。第二轮：承接复核 `verdict=partial` 的补强重写。
性质：**只做方案设计**；零真机、零采样代码；不 commit、不 push；唯一写域 `lead/number_channel_20261109/`，本轮产物 `_nc2_` 前缀。
绝对只读：`lead/orch_claims_20261109/`、`lead/metric_audit_20261109/`、`lead/keff_calc_20261109/`、`lead/pvalue_recalc_20261109/`、`lead/score_decomp_20261109/`、两件台账、`.zcode/workflow-runs/` 历史 payload、`.zcode/workflow-drafts/` 草稿。
引用一律追到「实跑命令+输出」或「文件:行」；拿不到写「未验」。指纹用 `hashlib`，Python 一律 `python -I -X utf8` + 绝对路径。

> **★ 复核 verdict 如实记录**：上一轮主件（SHA256 `abea556f…5501549ec`，50607 B）复核判定为 **`partial`**（`whatBreaksIt` 列 8 条决定性破口）。按交付要求，**`partial` 标 `unconfirmed`**：即本件不宣称「不靠自觉已完全兑现」，只宣称「复核列出的破口已逐条补强并有本会话实跑回归证据」；真实 workflow 实效仍**未验**。旧版实现 `_nc_placeholder.py` / `_nc_lint.py` 保留在盘作为对照，未被修改；本轮可粘贴实现是 `_nc2_placeholder.py` / `_nc2_lint.py` / `_nc2_writeback_test.py`。

---

## 1 目的与边界

**目的**：把「编排方手写散文段里的数字」这条通道整体废掉 —— 数字不再以裸值出现在散文，只在 `CLAIM_NUMBERS` 单一机器源里声明，散文用 `{{N.<id>}}` 引用；派发前由 lint 机检，纠正只回写数字源。

**边界（硬）**：

| 项 | 本轮实际做了什么 | 依据 |
|---|---|---|
| 只做方案设计 | 未改任何既有件：只读目录、两台账、历史 payload、草稿全部只读访问 | 终态 `git status --porcelain -- lead/number_channel_20261109/` = `?? lead/number_channel_20261109/`；9 件指纹写件前后由 `_nc2_fingerprint_out.txt:88` 复核 `n_match=9/9` |
| 零真机 | 未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存 | 本会话命令清单全部为 `python -I -X utf8` 文本/JSON 处理 |
| 零采样代码 | 未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析 | `_nc2_*.py` 只用 `hashlib/json/re/ast/io`（`_nc2_placeholder.py:26-33`） |
| lint 与解析器落写域 | 三个可粘贴实现 + 全部实跑输出均在本任务写域 | §6 产物清单 |
| 不 commit / 不 push | `git branch --show-current` = `main`，`git rev-parse --short HEAD` = `2657458`（与起始快照一致） | 本会话实跑 |

**★「不靠自觉」是硬要求**：凡需要「注意仔细」「标了就算」的方案都不合格。上一轮正是在这一点被判 `partial`：复核用 8 个探针证明 `source_kind` 是撰写人自报、机器不核证据，错值 10 只要标「实跑」+ 假 `command`/`stdout_sha256` 就全 lint `ok=True`（`_ncv_probe_out.json` 的 `validator_probes.V1/V2/V3`、`_ncv_probe5_out.json` 的 `A_defeat_by_mislabeling_as_实跑`）。本轮把「自觉」换成「证据机核」，见 §3.2。

---

## 2 上游指纹 + 核查复现

### 2.1 九件上游指纹（本会话独立重算）

实跑：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/number_channel_20261109/_nc_fingerprint_verify.py" > "…/_nc2_fingerprint_out.txt"` → `BINDING_SUMMARY n_match=9/9`（`_nc2_fingerprint_out.txt:88`；逐件 64 位值与字节数见 `:89-97` 与 `:4-85`）。逐件绑定行（格式固定：「被核对象 SHA256 = 」紧跟完整 64 位十六进制，中间无路径/括号/星号/反引号/空格，随后「，字节数 = 」+数字）：

```
被核对象 SHA256 = 9ebc406831a3fa402cf7006240b2b6c1314fed344dd1aa0c2a06f89b072140e4，字节数 = 53432   [ORCH_CLAIMS_AUDIT.md]
被核对象 SHA256 = 1f7aba12c7ab21e6c27eac491e790d2ed4bf7423cae2a9df9e35e545228b7834，字节数 = 1127   [_oc_stats_out.json]
被核对象 SHA256 = 541af3380dec0657c79f6d39999feaaa5d6e90d6fab34d8ce014844961370439，字节数 = 1336   [_oc_recompute_out.json]
被核对象 SHA256 = f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503，字节数 = 45362  [METRIC_CONVENTION_AUDIT.md]
被核对象 SHA256 = 4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16，字节数 = 34964  [KEFF_CALC.md]
被核对象 SHA256 = 277df9910d4611e0072faf83bd65e3639667a01b511191d5f74b575e448911ac，字节数 = 29780  [_pv_PVALUE_RECALC.md]
被核对象 SHA256 = dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb，字节数 = 42573  [SCORE_DECOMP.md]
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419  [PENDING_DECISIONS.md]
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518 [GOAL_THREE_TARGETS_20261018.md]
```

**口径声明**：9/9 MATCH 只证明「本会话读到的这 9 件与任务书贴的指纹一致」，不证明「9 件内容的历史真伪」（`ORCH_CLAIMS_AUDIT.md:254` 同型声明）；后者见 §2.2 独立复算。

### 2.2 (a) 19/1/0（即「准确率 0-20」中的 0/20 口径）—— 可复现，限「人工录入 C 表 → 统计」这一步

实跑：`python -I -X utf8 "…/_nc_verify_claims.py" > "…/_nc2_verify_claims_out.json"`（`_nc2_verify_claims_out.json:2-17`）：

```
from_C_table    = {"total":20,"wrong":19,"imprecise":1,"correct":0}
from_stats_json = {"total":20,"wrong":19,"imprecise":1,"correct":0}
reproducible    = true
```

`_oc_stats_out.json:2-5` 同为 20/19/1/0；`ORCH_CLAIMS_AUDIT.md:112` 明写同一组值，`:114-116` 给 0% / 5% / 15% 三口径。**如实边界**：`C` 表是核查员对 20 条主张的人工判定录入，本会话复现的是「录入→统计」，**未重新逐条判定 20 条真伪**（`_nc2_verify_claims_out.json:16-17` 已标），逐条真伪**未验**。另据 `ORCH_CLAIMS_AUDIT.md:117`，20 条是编排方**自选坏例样本**（`literal_in_taskbook` = yes 9 / hedged 6 / no_such_assertion 3 / self_recount 2），**0% 不可外推为历史任务书总体准确率**。

补充独立算术复核（本会话 `python -I -X utf8 -c <五组复算>`）：`0.25/7.62939453125e-06=32768.0`、`as_2pow=15.0`、`equals_16384=false`；`(18/log2(40)-1)/17=0.14013134380964332`、`round8=0.14013134`、`1-ρ̄=0.8599`；两层 `(19/39)*(3/39)=0.037475345167652864`、三层 `=0.03363172002225257`、`fp_product=0.0`；`(20+18)/74=0.5135135135135135` —— 与 `_oc_recompute_out.json:2-51` 逐值吻合，复现 `ORCH_CLAIMS_AUDIT.md:118` 的「机器生成/贴实跑部分 100%」。

### 2.3 (b) 六类分布 —— 可复现

`_nc2_verify_claims_out.json:18-59`：从 `C` 表重算主性质分布 **口径混淆 7 / 串对象 4 / 数少 3 / 数多 3 / 代数错 2 / 设计实验当实跑 1（合计 20）**；与 `_oc_stats_out.json:14-20`、`ORCH_CLAIMS_AUDIT.md:124-132` 三方一致（`primary_match=true`, `sum_primary=20`）。非互斥全性质重算「口径混淆 10 / 串对象 6」，与 `_oc_stats_out.json:22-29` 一致。归并 **口径混淆+串对象主性质 = 11/20 = 55%**（`:59`、`ORCH_CLAIMS_AUDIT.md:134, :146-147`），计数方向对称「数少 3 : 数多 3」（`:148`）。**边界同上**：分布是人工标签的统计，不是本会话对错误性质的重新归类；归类本身**未验**。

### 2.4 (c) ★「贴了≠用了」原文 —— 可复现，两份任务书 `lowered` 逐行实读

本会话用 `json.loads` 解码 `.mjs` 第 9 行 `export const payload = {...}` 的 `lowered` 字符串（不是 grep 乱码），逐行定位（命令见 §2.1 同型脚本；输出 `_nc_taskbook_89df_hits.txt`、`_nc_taskbook_89df_context.txt`、`_nc_taskbook_8682_hits.txt`；本会话又直接解码复核）：

**① `dwfrun-89df48db…`（主证之一，但需口径收窄）**

| lowered 行 | 原文（本会话解码实读） | 归属 |
|---|---|---|
| `:65` | `"o['claim19_ratio']={'computed':c/a,'expected_32768':32768,…}"` | 机器段 `VERIFY_CODE` |
| `:68` | `"o['claim20_rho_threshold']={'computed':round(rho,8),'expected_0.14013':0.14013134,…}"` | 机器段 `VERIFY_CODE` |
| `:107/:108` | `"【编排方实跑指纹】" + fpText` / `"【对编排方几个关键数字主张的复核…】" + vfText` | 机器段（`.join` 拼接，变量 `fpText`/`vfText` 定义于 `:90/:102`） |
| `:35/:36` | `"19. 「族级/全单元 = 32768 倍」→ 编排方心算成 16384，实际 32768（它是对的）。"` / `"20. 「ρ̄ < 0.8599」→ 编排方反解错，实际 ρ̄ < 0.14013（它是对的）。"` | `CLAIMS` 段（被核对象） |
| `:122` | `"  · 「32768」心算成 16384，「ρ̄<0.14」反解成 0.86"` | **散文背景段**（`_nc_taskbook_89df_context.txt:38`） |
| `:250` | `"编排方独立复算：族级/全单元=32768、ρ̄<0.14013、…"` | `verified` 段 |

`ASK_ANALYST` 由 `IRON + 实跑指纹段 + 复核段 + 散文背景段 + CLAIMS + 任务` 拼接（`_nc_taskbook_89df_context.txt:16-27`；`ORCH_CLAIMS_AUDIT.md:201` 同判）。**★ 口径收窄**：`:122` 的 `16384`/`0.86` 是 CLAIMS 里「编排方自述的复算错」的引述，不是本轮新主张（`ORCH_CLAIMS_AUDIT.md:102, :104, :116`）；故 `89df` 是「贴了对值、散文引述错值」，跨段 diff **必须区分引述段与主张段**。本轮 §4.3 把 `:110`【背景—— 从引述打开标记中移除，`lowered:122` 现在判 `prose`（`_nc2_regression_out.json:127-137`）。

**② `dwfrun-868215ce…`（主证，错数字进验收/发布段）**

- `:95` `"【32 域双轨重判结果（编排方实跑…）】" + rjText`（`rjText` 定义于 `:89`）、`:166` `"【双轨重判】" + rjText` —— 机器段贴实跑；
- `:98` 散文「**10 个域**仍有门禁问题，**5 个域** bindings=0」、`:110`【任务】「对 **10 个**仍报问题的域」、`:131`「把 **10 个域**全部改走…」、`:132`「**5 个** bindings=0 的域」、`:170`【交付】「**5 个** bind=0 域逐个定性」、`:217` `publishArtifact.description`「**10 个**仍报问题的域逐个判真伪」、`:226` `conclusion:`「**十个域：**」+ `finding.tenDomains`；
- 下游更正件在盘：`lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md:51`「gateProblems 非空 **13 域** | **10 域** | 不符」、`:53`「bindings=0 **6 域** | **5 域** | 不符」、`:56`「6 种口径都得不出 10 → 集合对齐未验」、`:161`「任务书【交付】写『5 个』，实测 6 个」、`:289` 复述。

`ORCH_CLAIMS_AUDIT.md:189, :204, :229` 的三处诊断（错数字进 `publishArtifact` 元数据、贴了≠用了、`rjText` 后散文仍 10/5）**逐条可复现**。

### 2.5 (d) 18/18 拦截率 —— 不可复现为「拦截率」；原报告自身已更正

`_nc2_verify_claims_out.json:162-243`、`_nc2_verify_intercept_out.json`。

**(i) 数字来源自相矛盾**：`_oc_stats_out.json:34` 给 `caught_by_subtask=18`、`:41-46` 同时给 `literal_in_taskbook.no_such_assertion=3`。本会话从 `C` 表逐条交叉（`_nc2_verify_claims_out.json:178-237`）：

```
caught_ids      = [1..18]                    (n=18)
literal_yes_ids = [1,2,3,4,5,8,9,12,13]     (n=9)
literal_no_ids  = [11,15,17]                 (n=3)
hedged_ids      = [6,7,10,14,16,18]          (n=6)
conflict_caught_but_no_literal = [11,15,17]  <- 同时 caught=True 且 literal=no
internal_contradiction = true
```

未被下发者不可能被「当场拦下」。`ORCH_CLAIMS_AUDIT.md:169` 自己判为「18/18 虚增 3 条」，`:171-173` 改为 **严格 9/20、宽松 15/20、原报告 18/18 不成立**。

**(ii) 逐条更正记录**：本会话按 `文件:行` 窗口实读 12 份更正件（`_nc2_verify_intercept_out.json:2-278`）：`STALE_PASS_INVENTORY.md:65-72/:103-110`（#1/#2）、`KEFF_CALC.md:100-115/:254-259`（#3/#4/#5）、`CHAIN_VS_SINGLE.md:144-150`（#6）、`GATE_REJUDGE_32.md:135-140`（#7）、`GATE_N13_QUOTED_ASSERTION.md:388-406`（#8）、`GATE_REJUDGE_32.md:48-57`（#12）、`MINHARD_SET_CHECK.md:170-185`（#13）、`MASKING_EFFECT_AUDIT.md:76-90`（#14）、`_sd_report.md:215-221`（#18），`n_strict_pass = 12/12`。

**★ 口径不一致（如实登记）**：`ORCH_CLAIMS_AUDIT.md:171` 声明「严格口径 = 9/20」，但同段枚举了 **12 个 id**（`1,2,3,4,5,6,7,8,12,13,14,18`），其中 `6,7,14,18` 在 `C` 表里是 `hedged`；`literal_yes` 里的 `9` 反而未被枚举。本会话 `python -I -X utf8 -c <§4.2 id 抽取>` 实跑得 `literal yes ids (9): [1,2,3,4,5,8,9,12,13]`、`enumerated but NOT yes: [6,7,11,14,15,17,18]`、`yes but NOT enumerated: [9]`。故「严格 9/20」**数字可复现、逐条对应关系未验**（审计件 `:171` 自标「未验」）。

**(iii) #11/#15/#17 字面断言 census**：本会话遍历主归档 `.zcode/workflow-runs/` 下 `.mjs`（本轮时点 259 份，见 `_nc2_census_out.json:5`；`_nc2_verify_intercept_out.json` 记 259），`挑错中稿/挑错文件` 3 命中、`脚本缺陷` 2 命中、`修好就能插` 1 命中，均在更正/提问/闸门语境；**原下发断言本身未验**。

**(iv) 判定与措辞收窄**：`18/18` 只能复现为「`_oc_stats.py` 里 18 行 `caught=True` 的录入计数」。★ 本轮任务书背景段 `dwfrun-96a786f8…lowered:132` 写的是「(d) 18/18 拦截率**能否复现**？（去核每条是否真有子任务纠正记录）」—— 这是**核验提问**，不是肯定式主张；上一轮把它定成「贴了≠用了活实例」属措辞过强，本轮按复核意见更正：只登记为「背景段把 18/18 与九件指纹同列，而 `ORCH_CLAIMS_AUDIT.md:169` 已否定它；属精度不足的提问式引用」，**不**升级为第三个实证案例。真正坐实的「贴了≠用了」是 §2.4 的两份任务书。

### 2.6 四项小结

| 项 | 判定 | 依据 |
|---|---|---|
| (a) 19/1/0 | 可复现（录入→统计层） | `_nc2_verify_claims_out.json:2-17` |
| (b) 六类分布 | 可复现（7/4/3/3/2/1，55%） | `:18-59` |
| (c) 贴了≠用了 | 可复现（两份任务书 `lowered` 原文） | `:61-160` + 三份 `_nc_taskbook_*` + 本会话解码 |
| (d) 18/18 拦截率 | **不可复现**；已更正 9/20 严格、15/20 宽松；本轮任务书是提问式引用 | `:162-243`、`ORCH_CLAIMS_AUDIT.md:169-173`、`dwfrun-96a786f8…lowered:132` |

---

## 3 占位符方案

### 3.1 (a) 核心规格（六字段 + 证据字段）

散文段只允许 `{{N.<id>}}`；数字集中在机器段 `CLAIM_NUMBERS`（任务书给的六字段 `id/value/unit/scope/source_kind/source_ref/sha256` 全保留，另加证据字段）：

```js
// 机器段（允许裸数字，但每条必须有在盘证据）
const CLAIM_NUMBERS = [
  { id:"domains_nonempty", value:13, unit:"域",
    scope:{ label:"全量载体", numerator:"gateProblems 非空的域",
            denominator:"全部 32 域", condition:"本轮 gate_rejudge32 DIR" },
    source_kind:"实跑", source_ref:"world-read#2 REJUDGE_CODE",
    sha256:"<claim_digest：整条声明主体的 SHA256，非手写>",
    command:"python -I -X utf8 <rejudge.py>", command_exit:0,
    stdout_path:"lead/.../_nc2_demo_stdout.txt",
    stdout_sha256:"<该 stdout 文件字节的 sha256>",
    domain:"gate_rejudge32", artifact:"GATE_REJUDGE_32.md" },
];
// 散文段（禁裸数字）
const BACKGROUND = ["【背景与实测事实】",
  "  回归里 {{N.domains_nonempty}} 仍有门禁问题，须逐域重判。"].join("\n");
```

| 字段 | 必填 | 作用 / 拦哪条 |
|---|---|---|
| `id` | 所有 | `{{N.id}}` 反查键；重复 id FAIL |
| `value` | 所有 | 唯一数值源；散文不得另写 |
| `unit` | 所有 | 无量纲写 `"无量纲"`，不许 `""` |
| `scope` | 所有 | `{label,numerator,denominator,condition}`；`label` 必须在 24 词受控口径表；拦 **#3/#5/#13/#15/#18 口径混淆** |
| `source_kind` | 所有 | 受控词表四值，见 §3.2；**由机器核证据，不是自报** |
| `source_ref` | 所有 | 来源指针（run id / path / estimator / 推导式） |
| `sha256` | 所有 | ★ `claim_digest(c)`：对「除计算字段外的整条声明（含 value 与全部证据）」规范序列化取 SHA256；**作者不能手写**，`seal_claim()` 是唯一生成入口（`_nc2_placeholder.py:100-115`） |
| `command` + `command_exit` + `stdout_path` + `stdout_sha256` | 实跑 | 在盘 stdout 工件 + 其哈希；核 value 是否出现在该 stdout（§3.2） |
| `path` + `line` + `line_sha256` | 文件行 | 实读该行、核行级哈希、确认当行含该数字 |
| `estimator` + `basis` + `degrade` | 估算 | 见 §3.3 |
| `derivation` + `depends_on` | 推导 | 受限 AST 重算；`depends_on` 可空 list 但键不可缺 |
| `domain` + `artifact` | 所有 | 与本轮 `DIR` 一致性检查；拦 **#6/#8/#11 跨域串台** |

整块规范序列化 `json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')` 取 SHA256，按固定格式写任务书末尾。实跑 `python -I -X utf8 "…/_nc2_placeholder.py" > "…/_nc2_placeholder_demo_out.json"` → `validate.ok=True, problems=[], n_claims=6`，`block_sha256 = aa7ccc6c16f21cb7001ed4d703132baf6fd4f172f35ef98395288ef111c07f97`（`_nc2_placeholder_demo_out.json:2-128`）。★ 上一轮 `evidence` 里写的 `5dd458b4…dc893586bca14771` 在盘 0 命中（复核指出），实际演示块哈希请以本轮 `:124-128` 为准。

**口径受控词表**（`SCOPE_LABELS`，标签不在表内即 FAIL）：`似然 / 后验 / q_i / fp_rate / 台账行 / 交付件行 / 实跑 / Shim / 设计实验 / 严格交集 / 全量载体 / in-sample / 标签层 / 真值层 / 两层 / 三层 / 朴素判据 / 谓词化判据 / 连续外推 / 整数口径 / 发布产物元数据 / 自述复算 / 被核对象 / 其它`（24 词，`_nc2_placeholder.py:56-61`）。比率/倍数/件数/域数类（`RATIO_UNITS`）强制三元组，缺任一 `AMBIGUOUS_SCOPE_MISSING`（可拦 #3/#4/#5/#13/#18；`ORCH_CLAIMS_AUDIT.md:213`）。

### 3.2 (b) `source_kind` 受控词表与必填字段（★ 证据机核，非自报）

| 值 | 含义 | 必填字段（缺一 FAIL） | 机器核证据动作（`verify_evidence`，`_nc2_placeholder.py:171-243`） |
|---|---|---|---|
| `实跑` | 本会话 `worldRead` / `python -I -X utf8` 的 stdout | `command, command_exit, stdout_path, stdout_sha256, source_ref, sha256, domain, artifact` | ① `stdout_path` 在盘且文件字节 sha256 == `stdout_sha256`；② `command_exit==0`；③ `value` 作为数值 token 出现在 stdout；④ 改 `value` 不改摘要 -> `BAD_CLAIM_DIGEST` |
| `文件行` | 只读在盘件 `path:line` | `path, line, line_sha256, source_ref, sha256, domain, artifact` | 实读该行、核行哈希、确认当行含 `value`；缺 `line_sha256` / 假路径 / 值不在行内 / 行越界全 FAIL |
| `估算` | 心算/印象/未跑 | `estimator, basis, degrade, source_ref, sha256, domain, artifact` | 无需外部证据；但强制降级渲染 + 禁入验收段（§3.3） |
| `推导` | 由其它已登记数字算出 | `derivation, depends_on, source_ref, sha256, domain, artifact` | 用**受限 AST**（只许字面量/四则/乘方/白名单函数，绝不 `exec`）重算 `derivation`，与 `value` 数值相等；`depends_on` 悬空 -> `DANGLING_DEP` |

**新增「推导」的理由**：`32768` 与 `0.14013134` 不是直接实跑值，是 `0.25/7.62939453125e-06` 与 `(18/log2(40)-1)/17` 的推导结果（`_oc_recompute_out.json:2-19`）；三值词表会把它们逼成「实跑」（不实）或「估算」（过贬）。

**★ 这是本轮对「不靠自觉」的核心兑现**：旧版 `validate_claim_numbers(strict=False)` 只查「`sha256` 是 64 位十六进制格式」，把 value 13 改 999 仍 `ok=True`（`_ncv_probe_out.json` 的 `V1`，本会话重跑 `_nc2_baseline_probe_out.json` 的 `V1=true`）。本轮默认 `strict=True`，证据不闭合即 `ok=false`。本会话回归实跑（`_nc2_regression_out.json:7-60`）：

```
V1_change_value_keep_sha256 -> ok=false, [BAD_CLAIM_DIGEST, VALUE_NOT_IN_STDOUT]
V2_stdout_sha256_bogus      -> [BAD_CLAIM_DIGEST, STDOUT_SHA256_MISMATCH]
F1..F4 文件行四探针          -> 全部 ok=false（缺行哈希/假路径/值不在行内/行越界）
D1_derivation_wrong_value   -> [DERIVATION_VALUE_MISMATCH]
DECISIVE_wrong10_labeled_实跑 -> ok=false, [EVIDENCE_UNVERIFIED:实跑:STDOUT_ARTIFACT_MISSING]
```

即复核的决定性破口「错值 10 标实跑 + 假 command/stdout_sha256 全 lint ok=True」已被堵住（`_nc2_regression_out.json:222` `validator_bogus_实跑_rejected=true`）。**如实边界**：`command` 字符串本身**不重跑**（`_nc2_placeholder.py:191` 注释；`_nc2_regression_out.json:26-29` 的 `V3` 显示改 `command` 不改值仍 `ok=true`，但改 `command` 会改变 `claim_digest`）。「command 真的产生过这个 stdout」这一层**未验**，只能靠 stdout 工件 + 哈希 + 值在 stdout 内三重约束逼近。

### 3.3 (c) ★ 估算渲染规则（都是估的，显式降级）

1. **显式降级不可关闭**：`render_value()` 对 `source_kind="估算"` 恒追加 `（估算，未实跑）`；`degrade` 必须为 `true`，否则 `ESTIMATE_NOT_DEGRADED` FAIL（`_nc2_placeholder.py:323-335`）。
2. **禁入验收段（硬 FAIL）**：`【交付】/【必现要素】/【任务】/【复核】/【验收】/【结论模板】/publishArtifact/conclusion:/description:` 任一出现估算 id 或降级标记 → `ESTIMATE_IN_ACCEPTANCE`。lint 按**解析后的 id** 判（§4.2），不靠字面 tag。
3. **交叉约束**：`visible_in` 与验收段有交集，`validate_claim_numbers` 阶段即 FAIL。
4. **下游语义**：见降级标记者不得当验收基线；【交付】里的数字必须来自 `实跑/文件行/推导` 三类。
5. **★ 为什么这一条最值钱**：错数字真正造成损害的地方是**被写进【交付】/`publishArtifact` 元数据/结论模板** —— `dwfrun-868215ce` 的 `lowered:217/:226`（`_nc_taskbook_8682_hits.txt:26-28`）、`ORCH_CLAIMS_AUDIT.md:189` 已证；`ORCH_CLAIMS_AUDIT.md:276` 判「错数字框定了子任务工作范围」也是因为 `lowered:110`【任务】写了「对 10 个域」。

**★ 复核破口(3) 已补**：旧版 `QUOTED_OPEN` 含「【复核】」且引述优先，`"【复核】{{N.est_effort}}"` 被判 `ok=True`（`_ncv_probe_out.json` 的 `P2`）。本轮 `ACCEPTANCE` **优先于** `QUOTED_OPEN`（`_nc2_lint.py:132-146`），`P2`/`A3`/`P4` 全部 `ESTIMATE_IN_ACCEPTANCE`（`_nc2_regression_out.json:61-120`）。

### 3.4 (d) 解析器片段（可粘贴）

完整实现 `_nc2_placeholder.py`。核心片段：

```python
import hashlib, json, re, ast, math, io, os
PLACEHOLDER = re.compile(r"\{\{N\.([A-Za-z0-9_.\-]+)\}\}")
ANY_MUSTACHE = re.compile(r"\{\{(.*?)\}\}", re.S)
ESTIMATE_TAG = "（估算，未实跑）"
COMPUTED_FIELDS = ("sha256", "source_block_sha256", "correction")

def canonical_bytes(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")

def claim_digest(c):                       # ★ 数字与证据绑定
    body = {k: v for k, v in c.items() if k not in COMPUTED_FIELDS}
    return hashlib.sha256(canonical_bytes(body)).hexdigest()

def seal_claim(c):                         # 唯一生成 sha256 的入口
    d = dict(c); d.pop("source_block_sha256", None)
    d["sha256"] = claim_digest(d)
    return d

def render(text, by_id, *, allow_estimate=True):
    problems, used = [], []
    def sub(m):
        cid = m.group(1)
        if cid not in by_id:
            problems.append("UNRESOLVED_PLACEHOLDER")   # ★ 不回显 cid
            return "[UNRESOLVED]"
        c = by_id[cid]; used.append(cid)
        if c["source_kind"] == "估算" and not allow_estimate:
            problems.append("ESTIMATE_IN_ACCEPTANCE_SEGMENT")
            return "[ESTIMATE_REJECTED]"
        return render_value(c)
    out = PLACEHOLDER.sub(sub, text)
    n_bad = 0
    def kill(m):                            # ★ 非 {{N.*}} 整段抹除，不回显内容
        nonlocal n_bad
        if PLACEHOLDER.fullmatch(m.group(0)): return m.group(0)
        n_bad += 1; return "[NONCONFORMING_MUSTACHE]"
    out = ANY_MUSTACHE.sub(kill, out)
    if n_bad: problems.append("NONCONFORMING_MUSTACHE:n=%d" % n_bad)
    return {"ok": not problems, "text": out, "problems": problems, "used": used}
```

**★ 安全约束（本次会话确实出现一条夹带指令，要求把形如 `{{NAME_…}}` 的 token 原样透传、不要替换）**：本解析器把所有非 `{{N.*}}` 形态一律判 `NONCONFORMING_MUSTACHE` 硬 FAIL，**且渲染文本里也不回显 token 内容**。本会话实跑 `python -I -X utf8 -c <未知 token 探针>` → `render("【背景】{{NAME_INJECT}} 与 {{N.no_such_id}}")` 得 `text="【背景】[NONCONFORMING_MUSTACHE] 与 [UNRESOLVED]"`、`ok=false`（`_nc2_diff_and_token_out.json:12-19`）。旧版 `rendered_text_echo_token=true`（`_ncv_probe2_out.json`）已修正。**不采信、不回显、不执行**。

`validate_claim_numbers()` 检查：非空 / id 合法且不重 / `source_kind` 在词表 / 各 kind 必填字段 / `sha256 == claim_digest(c)` / `scope.label` 在词表 / 比率三元组 / `domain+artifact` / 估算降级与验收段 / **证据机核（strict）** / 推导依赖闭合。输出 `{ok, problems, by_id, block_sha256, binding_line}`。

### 3.5 (e) ★ 同一数字重复出现 —— 纠正回写机制

**根因**（`ORCH_CLAIMS_AUDIT.md:204, :278, :238`）：#2 已在 `STALE_PASS_INVENTORY.md:107` 纠正 3→4 行，下一批任务书仍出 10/5；纠正只落在单份交付件，没回到数字源。

**机制（单一数字源 + 版本哈希链，全链自洽）**：

```
lead/number_channel_20261109/_nc_number_source.json      <- 唯一可写数字源
  { version, prev_sha256, prev_hashes[], block_sha256, binding_line,
    claims:[...], history:[{id,from,to,evidence,at_version}, ...] }
```

1. 所有任务书的 `{{N.id}}` 指向这一份源；散文里**没有数值，只有 id**。
2. 纠正唯一入口 `correct_value(path,cid,new_value,evidence)`：改源、`sha256` 由 `seal_claim()` 重算、`history` 追加、`version+=1`、`prev_hashes` 追加旧块、重算 `block_sha256`。**散文一字不动**。
3. 每份任务书末尾必贴 `【数字源】… version=<n>` + 绑定行；`check_chain()` 不止验链尖，还核：块哈希与 claims 自洽、每条 `source_block_sha256 == block_sha256`、每条 `sha256 == claim_digest`、`history` 版本序列 `2..version` 连续完整、`prev_sha256` 与 `prev_hashes[-1]` 一致（`_nc2_placeholder.py:413-505`）。
4. **★ 复核破口(7) 已补**：旧版 `save_source` 使每条 `source_block_sha256` 恒 ≠ 最终 `block_sha256`（`_ncv_final_out.json` 的 `chain_selfconsistency`）；`check_chain` 抹掉 `history`、断 `prev` 仍 `ok=True`。本轮 `_nc2_writeback_test_out.txt:13-14` 五种篡改（`WIPE_HISTORY / BREAK_PREV / CHANGE_VALUE_NO_RESEAL / BREAK_CLAIM_BLOCK_HASH / NO_BINDING_LINE`）**全部被拒**，`all tamper rejected: True`；`_nc2_regression_out.json:188-196` 在 `version=2`（已纠正）源上抹 history 得 `HISTORY_CHAIN_BROKEN`。

**实跑验证**：`python -I -X utf8 "…/_nc2_writeback_test.py" > "…/_nc2_writeback_test_out.txt"`，复刻 #2→#12 七步（`_nc2_writeback_test_out.txt:1-16`）：

```
STEP1 initial: version=1 block=7a07e50e164d6356
STEP2 taskbook A (before correction) chain: {'ok': True, 'problem': ''}
STEP3 corrected: changed=True/True version=3 ... per-claim source_block==block ? True
       history: [5→6 @v2 (GATE_REJUDGE_32.md:53), 10→13 @v3 (:51)]
STEP4 stale taskbook B (old hash): {'ok': False, 'problem': 'STALE_VERSION'}
STEP5 fresh taskbook B chain: {'ok': True, 'problem': ''}
       rendered prose: "【背景】沿用 6 域（口径：全量载体） 与 13 域（口径：全量载体）。"
STEP6 prose placeholders unchanged across correction: True
STEP7 tamper probes: 全部 ok=false；all tamper rejected: True
STEP8 temp source removed: True
```

即：旧任务书哈希 → FAIL；复贴新哈希的**同一段散文**自动渲染成 6/13；占位符串跨纠正完全不变；历史链不可篡改。临时源实跑完已删（`:16`）。**如实边界**：未在真实派发流程实装，「机制在真实 workflow 里一定生效」**未验**。

---

## 4 派发前 lint

完整实现 `_nc2_lint.py`（本任务写域），接 `.mjs` 的 `GATE_CODE` 设计：`ok=false` 时拒绝 `agent.ask()` 与 `publishArtifact()`。归档含 `CLAIM_NUMBERS` 者本轮时点 = **1**（`_nc2_census_out.json:5`；`ORCH_CLAIMS_AUDIT.md:224` 报 0 是上一轮时点，目录被并行会话追加），故这是新增件，不是改造既有门禁。

### 4.1 (a) 要抓什么（逐条，25 条规则码）

| # | 规则码 | 抓什么 | 对应实证 |
|---|---|---|---|
| 1 | `BARE_ARABIC` | 散文段阿拉伯裸数字未走 `{{N.id}}` | `868215ce:98` 的 10 个域 / 5 个 |
| 2 | `BARE_CJK_NUMERAL` | 中文数字+量词（十个域 / 四条问题 / 三层连乘） | `868215ce:226`「十个域：」 |
| 3 | `AMBIGUOUS_SCOPE` | 比率/倍数/件数无三元组或口径标签不在词表 | #3/#4/#5/#13/#18 |
| 4 | `CROSS_DOMAIN_LEAK` | `domain`/`artifact` 与本轮 `DIR` 不符 | #6 Shim→74 版、#8 n4 域→合订本 |
| 5 | `DESIGN_EXPERIMENT_UNMARKED` / `_IN_ACCEPTANCE` | Shim / 设计实验未标 `DESIGN_ONLY` 或进验收段 | #6、`ORCH_CLAIMS_AUDIT.md:240` |
| 6 | `ESTIMATE_NOT_DEGRADED` / `ESTIMATE_IN_ACCEPTANCE` | 估算未降级 / 进验收段 | #17、§3.3 |
| 7 | `UNRESOLVED_PLACEHOLDER` / `NONCONFORMING_MUSTACHE` | 未知 id / 非 `{{N.*}}` 形态（**不回显内容**） | 防未知占位符投放 |
| 8 | `BAD_SOURCE_KIND` / `MISSING_FIELDS` / `BAD_SHA256` / `BAD_CLAIM_DIGEST` / `EVIDENCE_UNVERIFIED` / `DANGLING_DEP` | 词表外 kind / 必填缺 / 哈希格式 / 哈希与声明不符 / 证据不闭合 / 推导悬空 | §3.2、复核破口(1) |
| 9 | `STALE_NUMBER_SOURCE` / `STALE_VERSION` / `BLOCK_HASH_MISMATCH` / `HISTORY_CHAIN_BROKEN` / `PREV_SHA256_BROKEN` / `CLAIM_BLOCK_HASH_MISMATCH` | 未复贴哈希 / 版本滞后 / 块不自洽 / 历史链断 / 断 prev / 单条绑定不符 | §3.5、复核破口(7) |
| 10 | `CROSS_SECTION_VALUE_NOT_USED` | 机器段贴了对值、散文段未引用（贴了≠用了） | §2.4 两份任务书 |
| 11 | `UNRENDERED_MACHINE_SEGMENT` | 静态 `"【复核数据】" + vfText` 源码冒充已渲染全文 | 复核破口(6) |
| 12 | `UNPROVEN_ACCEPTANCE_NUMBER` | 验收/发布段出现裸数字而该数字无已验证来源 | `868215ce:217/:226` |

### 4.2 (b) 可粘贴实现要点（不是「加强规范」）

```python
def lint(taskbook_text, claim_numbers, *, source=None, dir_hint="",
         root=ROOT, rendered=False):
    findings = []
    # ★ 严格证据机核（旧版 strict=False 是全部 bypass 的根源）
    v = ncph.validate_claim_numbers(claim_numbers, strict=True, root=root)
    for p in v["problems"]: add(rule_code(p), 0, p)
    # ★ 扫描全文所有 join 数组，不只首个 ASK_ANALYST
    blocks = extract_all_join_blocks(taskbook_text)   # re.finditer, re.S
    cls_all = concat(classify_lines(b) for b in blocks)
    # 散文段：BARE_* / AMBIGUOUS_SCOPE / DESIGN_* / ESTIMATE_*（按解析后 id）
    # ★ 全文 publishArtifact / conclusion: / description: 行独立扫描
    for lineno, line in artifact_lines(taskbook_text): ...
    # 全链 check_chain / 跨段 diff（保留 UNRENDERED 规则码）
    diff = ncph.cross_section_diff(machine_txt, prose_txt, v, rendered=rendered)
    return {"ok": not findings, "findings": findings, "summary": {...}}
```

（`_nc2_lint.py:190-303`；`GATE_CODE` 接线设计 `ok=false` 拒绝 `agent.ask` 与 `publishArtifact`。）

**★ 复核破口(4) 已补**：旧版 `lint_draft` 只抽首个 `ASK_ANALYST`，`8682` 的 `lowered:170/217/226` 在首个数组之外；`publishArtifact`/`conclusion` 不是 `PROSE_STRING`，`classify_lines` 完全看不见，`A_catches` 对五条真实损害行全为 false（`_ncv_probe5_out.json`）。本轮 `extract_all_join_blocks` + `artifact_lines` 全文扫描，`_nc2_regression_out.json:144-186` 五条真实损害行 `lowered:98/110/170/217/226` **全部 `caught=true`**（命中 `BARE_ARABIC`/`BARE_CJK_NUMERAL`/`AMBIGUOUS_SCOPE`），`:220` `all_5_real_damage_lines_caught=true`。★ 如实边界：这里仍是「只读预检」，**未实装进任何真实 `.mjs` GATE_CODE、未跑真实派发回归**。

### 4.3 (c) ★ 散文段判定（散文段与机器段的判定方法，不靠自觉，靠结构）

**判定依据 = 该行是不是运行时拼接，不是「看起来像不像背景」，更不是标题里写了什么。**

| 类别 | 判定（`_nc2_lint.py:47-172`） | 裸数字 |
|---|---|---|
| **机器段** | 数组元素形如 `"【…】" + <标识符>`（`fpText`/`rjText`/`vfText`/`JSON.stringify(...)`），或显式 `// MACHINE_SEGMENT` 注释 | 允许（但须 `rendered=True` 且该行有可见数值 token） |
| **引述段** | `QUOTED_OPEN`（**收窄为** `【被核对象】/【原文】/【逐条原说法】/CLAIMS = [`）到 `QUOTED_CLOSE` 的状态化整段 | 允许，但不参与跨段 diff |
| **散文段** | 纯字符串字面量（无 `+` 拼接），且不在引述区/代码区；**含 `ACCEPTANCE` 标记的行一律按散文/验收段判** | **禁止** |
| **代码区** | ` ``` ` 围栏内、行内 `` `...` `` 内 | 不报 |

**为什么不能只看标题**：编排方给段起个「【实测事实】」就能把心算数字洗成机器段。**★ 复核破口(2) 已补**：旧版 `MACHINE_MARK` 含「【编排方实跑指纹】」纯标题串，纯字符串 `"【编排方实跑指纹】实测 7 个域"` 被判 machine 且 lint `ok=True`（`_ncv_probe2_out.json` 的 `A1`）。本轮**删除整个 `MACHINE_MARK` 标题规则**（`_nc2_lint.py:47-52`），`P1_title_launder` 与 `P1b_unregistered_under_title` 现在都报 `BARE_ARABIC`（`_nc2_regression_out.json:62-70, :110-119`）。

**★ 状态机仍必需，且顺序已改**：`89df` 的 `CLAIMS` 是独立数组 `CLAIMS = [ "1. …", "19. …心算成 16384…" ]`，打开标记只在第一行；旧版按单行判会把编号行误报。本轮 `classify_lines` 保留 `in_quoted` 状态，但：① `QUOTED_OPEN` 移除「【复核】/【核查】/【背景——」（`ACCEPTANCE` 优先，见 §3.3）；② `QUOTED_OPEN` 仍优先于 `MACHINE_CONCAT`，否则 `"【被核对象】" + JSON.stringify(finding)` 整段引述会被洗成机器段；③ 复核破口(5)「89df 的 `【背景——` 打开 QUOTED 区直到 `:124`【任务，把 `lowered:122` 一并豁免」已补 —— `_nc2_regression_out.json:127-137` 显示 `:110/:113/:122/:124` 全部判 `prose`，`line122_classified_prose=true`（`:219`）。

**★ 复核破口(6) 已补**：旧版 `cross_section_diff` 只对整段 machine_text 做一次 `_NUM_TOKEN.search`，必贴绑定行含数字就把它并入机器段，`UNRENDERED` 守卫被击败；且 lint 把所有 diff 问题映射成 `CROSS_SECTION_VALUE_NOT_USED`，`UNRENDERED` 根本不在 `RULES`（`_ncv_probe4_out.json`）。本轮**逐行判**：`+ IDENT` 所在行本身无数值 token 即 FAIL，别的行的绑定行数字不作数；规则码保留（`_nc2_lint.py:283-288`）。实跑 `_nc2_diff_and_token_out.json:6-11`：`STATIC_no_binding` 与 `STATIC_with_binding_line` **都** = `["UNRENDERED_MACHINE_SEGMENT"]`；`_nc2_regression_out.json:121-125` 带必贴绑定行的集成 lint 仍 `ok=false`。三例 diff：`WRONG=['CROSS_SECTION_VALUE_NOT_USED:ratio_32768'] / RIGHT=[] / STATIC=['UNRENDERED_MACHINE_SEGMENT']`（`_nc2_diff_and_token_out.json:2-11`）。

### 4.4 (d) 误报控制（本轮实跑，脚本与输出均在盘）

复核指出上一轮 §3.4 的 census「无在盘脚本/输出」（`_ncv_probe4_out.json` 的 `census_artifacts.census_script_on_disk=false`）。本轮补 `_nc2_census.py` + `_nc2_census_out.json`，实跑命令：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/number_channel_20261109/_nc2_census.py" > "…/_nc2_census_out.json"
```

输出（`_nc2_census_out.json:2-21`）：

| 量 | 本轮时点值 | 上一轮报值 |
|---|---|---|
| `.dwf.ts` 草稿 / 含 `ASK_ANALYST` | 216 / 101 | 213 / 98 |
| 主归档 `.mjs` / 含 `CLAIM_NUMBERS` | 259 / 1 | 256 / 0 |
| 散文字符串行数 | 4089 | 3200 |
| 阿拉伯数字 raw → 代码+豁免屏蔽后 | 2498 → 1665 | 2354 → 2014 |
| 屏蔽抑制 | 833（33.35%），影响 90 份 | 340（14.44%），29 份 |
| 语法性中文数字抑制 | 295 处 | 534 处 |
| 残余裸数字 / 每份 mean / median / p90 / max | 1665 / 16.49 / 15 / 28 / 61 | 1694 / 17.29 / 15 / 29 / 46 |
| 零残余草稿 | 1 / 101 | 0 / 98 |

两轮口径不同（本轮 `extract_prose_lines` 抽**所有** join 数组且时点目录已被并行会话追加），**不可直接相减**；结论一致：**绝大多数草稿仍有残余裸数字 → 零豁免不可上线**（与 `ORCH_CLAIMS_AUDIT.md:211` 的「132 阿拉伯 + 9 中文量词命中，无豁免策略不可上线」方向相同）。

**豁免白名单**（`_nc2_lint.py:99-124`）：`path:line` / `file.md:110-112`、64 位哈希、`tail: 16384`、`§3.2`、`2026-11-09`、`R10/D-27/N13/V12`、`dwfrun-<uuid>`、`字节数`、绑定行整行、`bindings=0` 类常量、孤立 `0` / 年份。**语法性中文数字白名单** `CJK_GRAMMATICAL`（`一个/一类/两件/第一/两者/一方面…`，`:158-164`）。

单份真实草稿预检：`python -I -X utf8 "…/_nc2_lint.py" "…/.zcode/workflow-drafts/32域门禁判据逐域重判.dwf.ts" > "…/_nc2_lint_real_draft_out.json"` → `n_join_blocks=6, prose_lines=142, machine_lines=6, artifact_lines=3, n_findings=122`，`by_rule={AMBIGUOUS_SCOPE:84, BARE_ARABIC:28, BARE_CJK_NUMERAL:5, MISSING_FIELDS:1, UNPROVEN_ACCEPTANCE_NUMBER:3, UNRENDERED_MACHINE_SEGMENT:1}`（`_nc2_lint_real_draft_out.json:2-18`）。**如实边界**：`AMBIGUOUS_SCOPE` 与 `BARE_*` 有意重叠报，122 条 findings ≠ 122 个独立错误；**未做人工逐条标注计算精确 FP/FN 率**，标**未验**。

### 4.5 (e) 正反例各 5 条 + 复核破口回归 + 规则可达性门禁

**任务书要求的正反例各 5 条**实跑 `python -I -X utf8 "…/_nc2_lint.py" > "…/_nc2_lint_selftest_out.json"` → `n=18, n_pass=18`（`_nc2_lint_selftest_out.json:2-3`），其中 POS1–5 / NEG1–5 见 `:4-90`：

| 例 | 名称 | 输入要点 | 期望 | 实得 |
|---|---|---|---|---|
| POS1 | 占位符齐全无裸数 | `实测为 {{N.domains_nonempty}} 与 {{N.bindings_zero}}` | ok | ok ✓ |
| POS2 | 机器段允许裸数（渲染后真拼接） | `"【编排方实跑指纹】" + fpText + " 13 域 6 域"` + 散文引用两个 id | ok | ok ✓ |
| POS3 | 代码块内数字不报 | `` `tail: 16384 与 13 域` `` 整段在行内代码里 | ok | ok ✓ |
| POS4 | 引述段允许裸数 | `【被核对象】+ JSON.stringify` 后跟 `19. …32768…16384`，散文写 `{{N.ratio_32768}}` | ok | ok ✓ |
| POS5 | 豁免形态不报 | `KEFF_CALC.md:110-112 / §3.2 / 2026-11-09 / R10 / D-27` | ok | ok ✓ |
| NEG1 | 阿拉伯裸数字 | `实测 13 个域` | FAIL | `BARE_ARABIC` ✓ |
| NEG2 | 中文数字+量词 | `十个域…五个域 bindings=0` | FAIL | `BARE_CJK_NUMERAL` ✓ |
| NEG3 | 估算进验收段 | `【交付】{{N.est_effort}} 必须达成` | FAIL | `ESTIMATE_IN_ACCEPTANCE` ✓ |
| NEG4 | 未解析占位符 | `{{N.no_such_id}}` | FAIL | `UNRESOLVED_PLACEHOLDER` ✓ |
| NEG5 | 数字源哈希滞后 | 复贴旧 64 位哈希 | FAIL | `BLOCK_HASH_MISMATCH`/`STALE_NUMBER_SOURCE` ✓ |

**★ 复核破口(8) 已补**：旧版 10/10 自检只覆盖 18 条声明规则中的 6 条（`_ncv_probe4_out.json` 的 `selftest_coverage`）。本轮除把自检扩到 18 例（REG1–8 逐一实测标题洗白/【复核】/publishArtifact/conclusion/错值标实跑/静态拼接/未知 token/历史链抹除）外，另加**机器枚举式规则可达性门禁** `_nc2_rule_coverage.py`：对 `RULES` 里**每一条**构造最小输入，要求 lint 报出该规则码；`RULES` 新增一条而没写探针 → 脚本直接 FAIL。实跑：

```
python -I -X utf8 "…/_nc2_rule_coverage.py" > "…/_nc2_rule_coverage_out.json"
→ n_declared_rules=25, n_rules_with_probe=25, n_rules_fired=25,
  all_declared_rules_reachable=true, rules_without_probe=[], rules_not_fired=[]
```

（`_nc2_rule_coverage_out.json:2-8`）。这把「自检覆盖」从「靠人补例子」变成「机器强制枚举」。

---

## 5 可行性

### 5.1 (a) 写任务书变慢多少（给估计，标明是估计；★ 修正上一轮算术矛盾）

**可测基线**（本轮实跑，非估计，`_nc2_census_out.json:2-21`）：216 份草稿 / 101 份含 `ASK_ANALYST` / 散文 4089 行 / 残余裸数字 1665 token / 每份 mean **16.49**、median 15、p90 28、max 61 / 每份散文行 4089/101 ≈ **40.5 行**。

**估计（明确标「估算，未实跑」）**：迁移期每份新增工作三块 ——

1. **把残余裸数字迁进 `CLAIM_NUMBERS`**：mean 16.49 个/份；每个需填 `id/value/unit/scope(4 子字段)/source_kind/source_ref/证据字段/domain/artifact` ≈ 10 字段。
   **★ 上一轮 §4.1 写「每字段 10–20 秒 × 约 10 字段 → 4–8 分钟」自相矛盾**（复核 `_ncv_probe3_out.json` 的 `effort_check`：按字面应为 28.8–57.6 分钟；本会话复算 `_nc2_baseline_probe_out.json` 的 `effort_arith` 同为 28.8/57.6）。本轮更正为两套并列口径，不再混用：
   - 口径甲（**每个数字** 10–20 秒，含查证据）：16.49 × 10–20s = **2.75–5.50 分钟/份**（本会话 `python -I -X utf8 -c <算术复核>` 实算）。
   - 口径乙（**每字段** 10–20 秒 × 10 字段）：= **27.48–54.97 分钟/份**。两者差 10 倍，**都是估算，未做起草计时实验**；取哪个取决于「填字段」能否批量模板化，**未验**。
2. **散文改占位符 + 跑 lint + 修 findings**：**估算 3–6 分钟/份**（未实测）。
3. **数字源版本/绑定行维护**：**估算 1 分钟/份**（未实测）。

合计：口径甲 **估算 7–13 分钟/份**，口径乙 **估算 31–62 分钟/份**；相对起草一份含 40+ 行散文的任务书（本会话无实测起草耗时，**未验**）大致相当于**增加 15–30%（甲）或 70–150%（乙）**。迁移后重复数字共用单一数字源，边际成本应下降（**未实测**）。

**★ 净成本未必增加**：`ORCH_CLAIMS_AUDIT.md:278` 判「协调者若每轮都要下游替他重算背景，协调本身在制造净成本」；§2.5 实读 12 份下游更正件（如 `GATE_REJUDGE_32.md:51-56` 为核 10/5 做了 32 域全量重判并标「集合对齐未验」）即被浪费的下游工时。**下游节省量未量化（未验）**。

**如实声明**：以上全部为**估算**，`source_kind="估算"`，`basis="216 份草稿的残余裸数字实测分布 + 字段数"`，`degrade=true`（本方案自身规则）；**未做任何真实起草计时实验**。

### 5.2 (b) 更轻的替代方案对比

| 方案 | 改动量 | 能拦什么 | 拦不住什么 | 依据 |
|---|---|---|---|---|
| **A. 只做「估算禁入验收段」** | 1 条规则 + 1 个受控词表（约 30 行） | 错数字进【交付】/`publishArtifact`/结论模板（`868215ce:217/:226`） | 背景段仍可写错值；口径混淆、跨域串台、贴了≠用了；**且若 `source_kind` 无证据机核，错值标「实跑」即可绕过**（`_ncv_probe5_out.json` 的 `A_defeat_by_mislabeling_as_实跑`） | §3.3、`ORCH_CLAIMS_AUDIT.md:189, :276` |
| **B. 只做背景段裸数字 lint（无占位符）** | 1 个 lint（约 80 行） | 逼编排方把裸数改成「未验」或删掉；显著降低散文数字密度 | 数字仍可写进机器段/验收段；无来源绑定、无纠正回写；豁免白名单要维护 | §4.4、`ORCH_CLAIMS_AUDIT.md:211, :243` |
| **C. 只贴实跑（现状加强版）** | 0 | 提高可追溯覆盖率 | **已被证伪**：`89df`/`868215ce` 贴了对值仍写错值（§2.4）；`ORCH_CLAIMS_AUDIT.md:231` 判「部分满足、不够」 | §2.4 |
| **D. 完整方案（占位符 + 证据机核 + lint + 回写链）** | 2 个模块 + 规则门禁 + 1 份数字源 + GATE_CODE 接线（约 600 行，本轮 `_nc2_placeholder.py` 456 行 + `_nc2_lint.py` 480 行 + `_nc2_rule_coverage.py` 210 行，不含测试/输出） | A+B 全部 + 口径标签 + 跨域检查 + 证据绑定 + 纠正回写 + 跨段 diff | 未实装，实效未验；迁移成本 §5.1 | §3、§4 |

**推荐**：先做 **A′ = A + 最小证据机核**（成本最低且堵住 A 的自报绕过），再做 **B**，最后补 **D** 的回写链。**C 不应作为方案**（§2.4 已给两份反例）。

### 5.3 (c) ★ 若只做一件事 —— 仍是「估算禁入验收段」，但判断需加一条限定

1. **损害位置确定**：`868215ce` 的 `lowered:110`【任务】「对 10 个域」、`:170`【交付】「5 个 bind=0 域」、`:217` `publishArtifact.description`、`:226` 结论模板（`_nc_taskbook_8682_hits.txt:9-28`）；`ORCH_CLAIMS_AUDIT.md:189` 判「最直接的错数字进入已交付产物」，`:276` 判「错数字框定了子任务工作范围」。
2. **背景段错值多数被流程接住**：`ORCH_CLAIMS_AUDIT.md:192`「污染程度：低但非零，形态是过程浪费 + 少数登记/元数据残留，不是系统性错误结论入账」；`:277`「是流程救了结果，不是数字救了结果」。§2.5 实读 12 份更正件亦证更正值都成了交付值。
3. **成本最低、可直接机检**：`ESTIMATE_IN_ACCEPTANCE` 已实跑通过（自检 NEG3，`_nc2_lint_selftest_out.json`），且本轮 `P2/A3/A7` 破口回归全被拦（`_nc2_regression_out.json:61-120`）。

**★ 但复核 `whatBreaksIt` 决定性破口(1) 表明：只做 A 而不做证据机核，撰写人把错值 10 标成 `source_kind="实跑"` 就能让 `ESTIMATE_IN_ACCEPTANCE` 不触发**（`_ncv_probe5_out.json` 的 `A_defeat_by_mislabeling_as_实跑: ok=true`）。所以**「只做一件事」的准确表述是：做「验收段数字必须有已验证来源」**（= 估算禁入 + 最小 `verify_evidence`），约 30+80 行；单做旧版 A 不成立。**如实说它拦不住什么**：#3/#5/#13/#18 口径混淆、#6 设计实验当实跑、#8/#11 跨域串台、#19/#20 贴了≠用了，全不在射程内。**它是收益/成本比最高的一步，不是完备解。**

### 5.4 (d) 能否回溯审计已交付件 —— 部分能，两处硬限制

**能做的（本会话已实跑）**：① 裸数字普查与分类（216 份 `.dwf.ts` / 259 份 `.mjs` 只读 census，`_nc2_census_out.json`）；② 贴了≠用了回查（从归档 `.mjs` 解 `lowered`，§2.4 的 `89df`/`868215ce` 即这么找到）；③ 污染清单（`ORCH_CLAIMS_AUDIT.md:181-192` 已做：7 处 stale 登记、`publishArtifact` 元数据、`STALE_PASS_INVENTORY.md:57/:59` 同件 3/4 并存）。

**两处硬限制**：① 已交付件没有 `{{N.id}}`，无法反查数字源 —— 占位符方案是**前向**的；本轮时点归档含 `CLAIM_NUMBERS` 者 = 1（`_nc2_census_out.json:5`，即本任务书自身语境），历史件仍不能 `validate_claim_numbers()` / `check_chain()`。② 本任务铁律**绝对只读**：只读目录、四份审计件、两件台账一律不得修改/追加/覆盖；`.zcode/workflow-runs/` 历史 payload 在多份既有任务书里被列为「历史 payload 绝对不改」（如 `32域门禁判据逐域重判.dwf.ts:32`）。故回溯审计只能是**只读报告**，不能回写纠正、不能补标 `DESIGN_ONLY`、不能给旧件加绑定行。

**判定**：可做为「一次性只读回溯普查」（产出新报告，不动旧件），**不可**做为「把旧件纳入这套门禁并自动修复」。已交付件的纠正须由 Leader 另行裁决（`ORCH_CLAIMS_AUDIT.md:187`）。

---

## 6 复核回件 + 结论 + 未验项

### 6.1 复核回件（绑定行，格式固定）

被核对象 SHA256 = 9ebc406831a3fa402cf7006240b2b6c1314fed344dd1aa0c2a06f89b072140e4，字节数 = 53432

- 绑定对象 = `lead/orch_claims_20261109/ORCH_CLAIMS_AUDIT.md`。本会话 `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/number_channel_20261109/_nc_fingerprint_verify.py" > "…/_nc2_fingerprint_out.txt"` 实跑，九件编排方指纹 **9/9 MATCH**（`_nc2_fingerprint_out.txt:88`），逐件完整 64 位值与字节数见 `:89-97` 与 `:4-85`。
- **★ 复核 verdict 如实记**：上一轮主件复核为 **`partial`**（`whatBreaksIt` 8 条决定性破口 + 次要缺陷），按交付要求 **`partial` 标 `unconfirmed`**。本轮已逐条补强并有本会话实跑回归（`_nc2_regression_out.json:216-223` 六项全 `true`、`_nc2_rule_coverage_out.json:2-8` 25/25），但**未实装进真实 `.mjs` GATE_CODE、未跑真实派发回归**，故「不靠自觉已完全兑现」**未验 / unconfirmed**。`refuted` 未出现，无需标注。
- 本件自身哈希由编排方在定稿后外部实算（`hashlib` 对本文件字节取 SHA256），格式与 §6.1 相同；本会话实算值见结果回件，不在文件内自贴（理由见文末）。

### 6.2 (a) ★「数字不可信」评级公平吗 —— 方向公平，字面过强

**公平的部分**（有实跑支撑）：九件指纹 9/9 MATCH、5 组复核数字独立复算全吻合（§2.1/§2.2），与 20 条手写背景主张 19/1/0 形成**通道级**反差；主方向「口径合并」11/20=55% 不是算术错（§2.3），靠「更仔细算」解决不了，**必须靠机器约束**；错数字确实框定过子任务范围（`868215ce:110/170/217/226`）；`ORCH_CLAIMS_AUDIT.md:280` 主动摊开 20 条、要求不护着、预置防错闸门，元层诚实有价值。

**过强、需收窄的三处**：① 「全部数字主张不可信」不成立 —— 20 条是**自选坏例样本**（`ORCH_CLAIMS_AUDIT.md:117`），`no_such_assertion=3`/`self_recount=2`/`hedged=6`，**0% 不能外推为总体准确率**（`:273` 自声明）。② 「数字层全错」不成立 —— `#19` 主断言「32768 倍」、`#20` 更正后「ρ̄<0.14013」**本身是对的**（`:102, :104, :116`），按主断言真伪是 3/20=15%；九件指纹与 5 组复核数字 100%。③ 「结果不可信」不成立 —— `:192` 判污染「低但非零」，更正值全部成为交付值。

**准确评级应写成**：**「编排方手写散文段的数字主张默认按『估算，未实跑』处理；机器生成/贴实跑的部分可采信但也须独立复跑」**（与 `ORCH_CLAIMS_AUDIT.md:279` 一致）。不护着（承认协调职能失守、错数字框定过范围），也不过度自责（不外推坏例样本、不否定元层诚实与流程价值）。

### 6.3 (b) 流程哪部分真在起作用

| 机制 | 实跑/在盘证据 | 判定 |
|---|---|---|
| 任务书内「不得采信 / 独立复跑 / 若不同以你的为准」纪律 | `868215ce:112`「自己重跑一遍双轨重判（不得采信编排方数字）」、`:134`「若你复跑的数字与之不同，以你的为准」、`:146`「自己重跑（不得采信编排方的 _rj 结论）」 | **成立** |
| 复核员制度 / 防错闸门 | `89df` 的 `ASK_REVIEWER`（`_nc_taskbook_89df_context.txt:47-55`）、`dwfrun-b52cb76a…:152`（`ORCH_CLAIMS_AUDIT.md:165, :277`） | **成立** |
| 子任务真的复跑并写入更正值 | §2.5 实读 12 份更正件 `n_strict_pass=12/12`；`GATE_REJUDGE_32.md:51-56` 按 13 域全量判并标「集合对齐未验」 | **成立** |
| 更正值成为交付值 | `ORCH_CLAIMS_AUDIT.md:192` 列 11 组（4 行 / 7 处 / 2 层 3.75% / 似然 2.05 / 13 域 6 域 / 2 件 6 件 / 51.35% / 0 分 / 不能插 / 32768 / 0.14013） | **成立** |
| 指纹绑定 + 独立复算 | 本会话 9/9 MATCH + 五组算术复核（§2.1/§2.2） | **成立** |

**但支撑强度须下调**（与 `ORCH_CLAIMS_AUDIT.md:173` 一致）：拦截率**不能**写成 18/18=100%（§2.5）；严格可核 9/20、宽松 15/20，且 9 条与条号一一对应**未验**。机制**存在**成立，机制**覆盖率**不成立。

**★ 准确说法**：**「流程救了『结论的实质』，没救住『过程的浪费』和『发布元数据』」**。`ORCH_CLAIMS_AUDIT.md:277` 明写「若某轮复核员缺席或照抄背景，错值会直接进交付」；§2.4 证 `868215ce:217/:226` 的错数字**已经**进了 `publishArtifact` 元数据与结论模板。

### 6.4 (c) 最小三步

**第 1 步（半天，约 30+80 行）**：**验收段数字必须有已验证来源**（= 估算禁入验收段 + 最小 `verify_evidence`）。在 `.mjs` 的 `GATE_CODE` 加 `ACCEPTANCE_SEGMENTS` 黑名单 + `source_kind` 受控词表 + stdout/文件行证据机核；散文里凡标「估算」或带降级标记的数字，以及任何无证据的裸数字，出现在 `【交付】/【必现要素】/【任务】/【复核】/publishArtifact.description/conclusion` 即 `ok=false` 拒绝发布。可复用 `_nc2_lint.py` 的 `ESTIMATE_IN_ACCEPTANCE` / `UNPROVEN_ACCEPTANCE_NUMBER` 与 `_nc2_placeholder.py` 的 `verify_evidence`。★ 只做旧版「估算禁入」而不加证据机核不成立（§5.3）。

**第 2 步（1 天，约 80 行）**：**派发前裸数字 lint（只报不拒）**。接 `_nc2_lint.py` 的 `classify_lines` + `mask_exempt` + `CJK_GRAMMATICAL` + `extract_all_join_blocks` + `artifact_lines`，对全文跑，`ok=false` 打印 findings 但**先不强制拒绝发布**（迁移期）。同步把 §4.4 白名单固化。目标：先拿到「每份任务书残余裸数字数」的实测时间序列。

**第 3 步（2–3 天，约 300 行 + 1 份数字源）**：**建单一数字源 + 占位符 + 回写哈希链，并把 lint 切为硬门禁**。落 `_nc_number_source.json`；新任务书 `CLAIM_NUMBERS` 与 `{{N.id}}` 全量接入；`check_chain()` 强制复贴当前块哈希 + 历史链自洽；把 lint 从「只报」切到「`ok=false` 拒绝 `agent.ask` 与 `publishArtifact`」。`_nc2_placeholder.py` / `_nc2_lint.py` / `_nc2_writeback_test.py` / `_nc2_rule_coverage.py` 已给出可粘贴实现与本会话实跑输出。

**三步都不做的事**：不改任何既有件、不回溯改历史 payload、不 commit/push、零真机、零采样代码。

### 6.5 (d) 判不了什么 + 未验项（如实列）

1. **20 条主张逐条真伪与错误归类**：只复现「人工录入→统计」，未独立重审（§2.2/§2.3）——**未验**。
2. **编排方历史任务书总体准确率**：20 条是自选坏例样本，0% 不可外推（`ORCH_CLAIMS_AUDIT.md:117, :273`）——**未验**。
3. **严格 9/20 与条号一一对应**：§4.2 枚举 12/15 个 id 与 9 条口径不一致，审计件自标「未验」（§2.5）——**未验**。
4. **#11/#15/#17 原始字面下发断言**：归档 census 只找到更正/提问/闸门形式（§2.5(iii)）——**未验**。
5. **#8 另 2 条门禁问题、#12「10 域」枚举、#17「4 项缺陷」**：在盘分别标「未验 / 集合对齐未验 / 6 条或 8 条不匹配」，沿用不补造（`ORCH_CLAIMS_AUDIT.md:179, :288-290`）——**未验**。
6. **lint 精确 FP/FN 率**：只做屏蔽率量化与单份草稿逐行抽查，未做人工逐条标注（§4.4）——**未验**。
7. **方案在真实 workflow 里的实效**：`_nc2_*.py` 只在本任务写域实跑自检与只读预检，**未实装进任何 `.mjs` 的 `GATE_CODE`、未跑真实派发回归**；「机制一定有效」判不了 → **`partial` / unconfirmed**（§6.1）。
8. **写任务书变慢多少的实测值**：§5.1 全部为估算（已按自身规则标 `source_kind="估算"`、显式降级），未做起草计时实验——**未验**。
9. **下游被浪费工时的量化**：只给方向，未量化——**未验**。
10. **真机/运行时行为、动态内存、活进程**：铁律零真机、零采样代码，本工作不涉及。
11. **已交付件的自动修复**：绝对只读约束下只能出只读回溯报告（§5.4）。
12. **未留盘的沟通/口头任务书**：#19/#20 心算错是否进入更早未存档沟通，无证据（`ORCH_CLAIMS_AUDIT.md:291`）——**未验**。
13. **绑定行的历史一致性**：9/9 MATCH 只证明本会话读到的 9 件与任务书贴值一致（§2.1）。
14. **本方案对「口径混淆」的实际消除率**：11/20=55% 是历史分布，改造后分布需 ≥2 轮实测时间序列（`ORCH_CLAIMS_AUDIT.md:242, :279`）——**未验**。
15. **`command` 是否真的产生过所贴 stdout**：本方案不重跑命令，只核 stdout 工件 + 哈希 + 值在 stdout 内（§3.2）——**未验**。
16. **复核 `partial` 的全部次要缺陷是否已清除**：已处理 `block_sha256` 在盘 0 命中（改用本轮 `:124-128` 实值）、§4.1 算术矛盾（§5.1 两套口径）、§3.4 census 无在盘脚本（补 `_nc2_census.py`）、18/18 措辞过强（§2.5(iv)）；但「真实 workflow 实效」仍 **unconfirmed**。

### 6.6 产物清单与合规声明

本任务写域 `lead/number_channel_20261109/` 内**本轮新增**（全部 `_nc2_` 前缀；上一轮 `_nc_` / `_ncv_` 件保留未改）：

| 件 | 用途 / 实跑结果 |
|---|---|
| `_nc2_fingerprint_out.txt` | 9 件指纹独立复核 `n_match=9/9`（`:88`） |
| `_nc2_verify_claims_out.json` / `_nc2_verify_intercept_out.json` | (a)(b)(c)(d) 独立复核；12 份更正件 + 归档 census |
| `_nc2_baseline_probe_out.json` | 旧版实现破口基线重跑（V1/V2/V3 仍可绕过、effort 算术 28.8/57.6） |
| `_nc2_census.py` / `_nc2_census_out.json` | 216 份草稿散文裸数字普查（在盘脚本+输出） |
| `_nc2_placeholder.py` / `_nc2_placeholder_demo_out.json` | 占位符规格、证据机核、渲染、全链回写；`validate.ok=True, n_claims=6` |
| `_nc2_lint.py` / `_nc2_lint_selftest_out.json` / `_nc2_lint_real_draft_out.json` | lint 实现；`18/18` 自检、5/5 真实损害行；真实草稿 `n_findings=122` |
| `_nc2_writeback_test.py` / `_nc2_writeback_test_out.txt` | 纠正回写 8 步 + 5 种篡改全被拒 |
| `_nc2_diff_and_token_out.json` | 三例跨段 diff + 未知 token 不回显 |
| `_nc2_regression.py` / `_nc2_regression_out.json` | 复核 8 条破口定点回归，六项 summary 全 true |
| `_nc2_rule_coverage.py` / `_nc2_rule_coverage_out.json` | 25/25 条规则机器枚举可达性门禁 |
| `NUMBER_CHANNEL_FIX.md` | 本件（设计说明） |

- **未改任何既有件**：只读目录、两台账、历史 payload、草稿全部只读访问；9 件指纹写件前后 9/9 MATCH。
- 零真机（未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；不 commit、不 push；`git branch --show-current` = `main`、`git rev-parse --short HEAD` = `2657458`。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。
- ★「不靠自觉」的兑现点（全部有本会话实跑）：`sha256 = claim_digest(声明主体)` 改值即 FAIL；`source_kind` 由 `verify_evidence` 机核；未知 `{{...}}` 硬 FAIL 且不回显；估算降级不可关闭且验收段按解析后 id 判；全链 `check_chain` 核 history/prev/块自洽；静态 `+ IDENT` 逐行判 UNRENDERED；段落判定靠结构不靠标题；`ACCEPTANCE` 优先于引述；全文所有 join 数组 + 发布行扫描；25 条规则机器枚举可达。

---

**关于本件自身的哈希**：本件不内嵌「自哈希绑定行」—— 把自身 SHA256 写进自身字节是哈希原像问题，做不到自洽（上一轮主件的 `abea556f…5501549ec`/50607 B 是复核方在文件定稿**之后**外部实算并记入复核 `sha256Line` 的，不是文件内自贴）。本件的固定格式绑定行见 §6.1，绑定对象为 `ORCH_CLAIMS_AUDIT.md`（`9ebc4068…b072140e4` / 53432 B，本会话 `hashlib` 实算）；本件定稿后的完整 64 位 SHA256 与字节数由本会话在结果回件中给出，可由编排方按同一算法独立复算。
