# H5_GOVERNANCE_FIX.md — H5 管辖关系修复【补丁设计交付件】

**撰写日期**：2026-11-09　**唯一写域**：`lead/h5_governance_20261109/`　**被核对象**：`lead/gate_v1v2_20261109/_v12_rule.py`
**复核 verdict = partial**（编排方【复核】字段原文；见 §6.1）。按交付要求，凡 refuted 或 partial 的结论一律标 **unconfirmed**：本设计的「修复完成 / 可落地」结论标 **unconfirmed**，不作完成式概括。

---

## 1 目的与边界

**目的**：只交付 H5（`H5_否定禁止管辖`）的 `prohibit_U` 管辖关系补丁**设计**与改前改后对照，由所有者决定是否落地。要求同时做到：(a) 放过真正的否定管辖，如「不宣告 N-4 已生效」；(b) 不再放过「不得…不得」相距、`不得不` 这类非管辖或双重否定。两边都要有样本。

**边界（铁律）**：

- **不改 `_v12_rule.py`、不改任何既有件**。四处替换只以「可粘贴片段 + 精确锚点」形式给出；修后副本 `_h5_v12_patched.py`（写域内新件，17,352 B）仅供回归，不是落地。
- **绝对只读**：`lead/gate_v1v2_20261109/` 全部件（含 `_v12_rule.py`）、`lead/v12_impact_20261109/` 全部件、`lead/gate_n13_20261109/`、`lead/gate_fp7_20261108/_g7_predicates.py`、`lead/gate_pipeline_20261109/`、两件台账，一律不修改、不追加、不覆盖。会话末实跑复核见 §6.6。
- 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；不 commit、不 push。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`；引用追到「实跑命令+输出」或「文件:行」，拿不到写「未验」。

**改前 / 改后一行对照**（供所有者决定是否落地；数字均来自本会话实跑 §5）：

| 项 | 改前（`_v12_rule.py:116` + `:135`） | 改后（本设计四处替换 + `h5_govern`） |
|:--|:--|:--|
| 判据 | `prohibit_U = any(k in U_bare for k in PROHIBIT)`：U 内有禁止词即豁免，不分前后 | `gov = h5_govern(pre, post)`：G1 前向 + G2 同微句 + G3 辖域路径 + G4 引证屏蔽 + G5 非双重否定 |
| 编排方九条 | 4 对 / 5 错（4 漏 1 误拦） | 9 对 / 0 错（`_h5_regress_out.txt:2-10`） |
| 自建 44 条（正样本 18 / 负样本 26） | correct=28 / fp=7 / fn=9 | correct=44 / fp=0 / fn=0 |
| 复核自构边界 10 条 | — | **5/10**（`_h5v_full.py` 实跑，§5.5）→ partial |
| 32 域 26 处 | 26 V1 | 26 V1，changed=0；`baseline_fp_mismatch=0` |
| 2 处确凿回退 | 2/2 放过 | 2/2 抓住（§5.4） |
| 真否定管辖 | `TRUE_NEG` 被误拦 | `TRUE_NEG` 放过（形状 b 桥接） |
| 生产门禁 | 不可插 | **仍不可插**（§6.3） |

**本件不声称修复完成**：编排方复核给出 partial，决定性失败在「铁律两边同时做到」这一项（§5.5、§6.1），故下列所有「修后」数字只在**指定样本集内**成立，外推能力 **unconfirmed**。

---

## 2 上游指纹（八件）+ 九条样本实跑

### 2.1 八件上游指纹（本会话实跑）

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5v_fp.py`
输出首行：`SECRET_P resolved = lead\gate_n13_20261109\_n13_predicates.py is_file = True`（占位 `lead/gate_n13_20261109/_n13_predicates.py` 由运行环境解析为真实件）；末行：`ALL_MATCH = True count = 8`。八行逐件 `match=True`：

| # | 件 | SHA256 | 字节数 |
|--:|:--|:--|--:|
| 1 | `lead/gate_v1v2_20261109/_v12_rule.py` | `15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0` | 9148 |
| 2 | `lead/v12_impact_20261109/_vi_REPORT.md` | `9375f37c0ecc81851944fa5383679ce0f02090b2bce6156a5f31396140bdc085` | 32956 |
| 3 | `lead/v12_impact_20261109/_vi_probe_out.json` | `7fd90337383038a21698beec865147257e3e99d6e3be33babf76b5763c65aeec` | 52341 |
| 4 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 |
| 5 | `lead/gate_n13_20261109/_n13_predicates.py` | `e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079` | 16649 |
| 6 | `lead/gate_pipeline_20261109/_gp_pipeline.py` | `25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7` | 15811 |
| 7 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 8 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

会话末第二次实跑（`python -I -X utf8 -c "<hashlib 逐件 read_bytes>"`）七件 `sha_ok=True`，只读域 mtime 仍为会话前（`_v12_rule.py` 12:17:39、`_g7_predicates.py` 00:44:32），`__pycache__` 字节码时间戳仍 12:18:26 / 00:45:10（脚本全设 `sys.dont_write_bytecode=True`）。

### 2.2 九条样本逐条实跑（原 `_v12_rule.py`，未落地）

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_repro9.py` → 输出 `loaded = True`，逐条 JSON 落 `_h5_repro9_out.json`。`_h5v_core.py` 独立重建后复跑 `② nine MATCH count = 9 / 9`，与编排方【九条样本】逐项一致。

口径：V1=PASS（门禁放过），V2=CATCH（门禁抓）。`review=True` 表示 `_v12_rule.py:167-170` 的 S3 fail-closed「判不了」。

| id | 文本 | token | expect | verdict | hard | override | weak | 对错 | 错在哪条规则 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| REGRESS1 | 本笔已入账 0 命中不得写成未入账 | 已入账 | 应CATCH | **V1** | `H5_否定禁止管辖` | `` | `[]` | **错（漏）** | `_v12_rule.py:116` `prohibit_U` 把 token **之后**的「不得」算作管辖；`:135-136` append H5；`:143-146` 提前 return V1。同 `V12_FULL_IMPACT.md:223` |
| REGRESS2 | 审阅不得不承认本候选已生效。 | 已生效 | 应CATCH | **V1** | `H5_否定禁止管辖` | `` | `[]` | **错（漏）** | `:116` 把 `不得不` 里的「不得」当普通禁止词；`:41-43` `PROHIBIT` 含「不得」，`ADJ_NEG_RE` 只查 2 字尾；全文无双重否定识别。同 `V12_FULL_IMPACT.md:224` |
| CTRL_OK | 本件已生效，可应用母本 | 已生效 | 应CATCH | V2 | `[]` | `` | `[]` | 对（`review=True`，S3 判不了） | 无 |
| TRUE_NEG | 本节登记不宣告 N-4 正式绑定已生效 | 已生效 | 应PASS | **V2** | `[]` | `` | `[]` | **错（误拦）** | `:115` `adj_neg` 只认 `pre[-1]` / `ADJ_NEG_RE`（`[^。；\|]{0,2}$`），十余字外的「不」不认前向管辖 → 无 H5 → `:167-170` S3 默认 V2 |
| TRAIL_NEG | 已入账不得重复登记 | 已入账 | 应CATCH | **V1** | `H5_否定禁止管辖` | `` | `[]` | **错（漏）** | 同 `:116`：禁止词在 `post` 仍豁免（后向不管辖反例） |
| LEAD_NEG | 不得写成已入账 | 已入账 | 应PASS | V1 | `H5_否定禁止管辖` | `` | `[]` | 对（理由不严谨） | `:116` 恰巧命中，靠「U 内有禁止词」而非「禁止词支配 token」 |
| DOUBLE_1 | 并非不宣告已生效 | 已生效 | 应CATCH | **V1** | `H5_否定禁止管辖` | `` | `[]` | **错（漏）** | 同 REGRESS2：`并非不` 双重否定=肯定，`:116` 一律豁免 |
| DOUBLE_2 | 不能不说本笔已入账 | 已入账 | 应CATCH | V2 | `[]` | `V2_OVERRIDE:已入账` | `[]` | 对（碰巧） | `:36` 把 `已入账` 自身列为宣称词、`:152` 命中 → V2；与双重否定无关，换 token 即漏 |
| DOUBLE_3 | 无不认为本件已生效 | 已生效 | 应CATCH | V2 | `[]` | `` | `[]` | 对（碰巧，`review=True`） | 无宣称词、无 H5 → S3 默认 V2，理由仍是「判不了」 |

合计：`A old = {'correct': 4, 'fp': 1, 'fn': 4, 'total': 9}`（`_h5_regress.py` 实跑）——**4 漏 1 误拦**。三条 `DOUBLE_*` 没有一条靠双重否定识别判对（`_v12_rule.py:29` 只有 `import re`，全文未 import R12）。

### 2.3 「不得…不得」相距（铁律点名，本会话实跑）

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5v_extra.py`，输出 `=== 『不得…不得』相距 4 条 ===`（`_h5v_extra_out.json:sep`）。修后副本 `_h5v_patched.py` 上 4/4 全对：

| id | 文本 | token | expect | old | new | 判定依据 |
|:--|:--|:--|:--|:--|:--|:--|
| S1 | 不得写成已入账，不得重复登记 | 已入账 | PASS | PASS | PASS | 前向「不得写成」真管辖，第二个「不得」在 post（G1） |
| S2 | 不得重复登记，本笔已入账不得写成未入账 | 已入账 | CATCH | PASS | CATCH | 两个「不得」相距、token 夹中间：第一个管辖「登记」，第二个在 post |
| S3 | 不得写成未入账，不得宣告本笔已入账 | 已入账 | PASS | PASS | PASS | 第二个「不得宣告」前向真管辖 |
| S4 | 已入账不得改写，也不得写成未入账 | 已入账 | CATCH | PASS | CATCH | 两处「不得」都在 post（后向禁止相距） |

---

## 3 管辖判定方法

### 3.1 管辖定义（G1–G5）

设 `U` 为 `_v12_rule.py:78-98` 切出的分析单元，`pre/post` 为 token 在 U 内的前/后缀（`_v12_rule.py:110`）。称否定/禁止算子 `n` **管辖**该 token ⟺ 同时满足：

- **G1 前向**：`n` 必须落在 `pre`；`post` 里的「不得/禁止/严禁」一律不管辖（修 REGRESS1 / TRAIL_NEG，根因 `_v12_rule.py:116` 与 `:135-136`）。
- **G2 同微句**：边界 = `_v12_rule.py:66` 的 `。！？；\n` **再加** `，,` 与 `但/然而/不过/却/只是/反之/相反/另`；取最后一个边界后的 `scope` 为实际判定前缀（修跨子句；`_g7_predicates.py:71` 的 `CLAUSE_BREAK` 不含逗号，`_h5_distance.py` C 组实证「，但」污染）。
- **G3 有辖域路径**（不是只看距离）：形状 a 紧邻（`_v12_rule.py:41-43` 的 `ADJ_NEG_CHARS`/`ADJ_NEG_RE`）；形状 b 辖域动词桥接「算子 + `[把将被让令以按照]?` + 辖域动词 + 补语 ≤24 字且补语内无第二独立主语/转折」；形状 c 全句否定辖域框「句首否定标签 + `post[:40]` 谓语否定」（只为保住现盘 `s604_script_hunt:143`「不可能/未覆盖：…未做」，`_h5_ctx26_out.json` 实读）。
- **G4 引证屏蔽**：`pre` 内完整 `「…」/『…』/\`…\`/“…”` 跨度内部置等长空格、保留开闭界符；未闭合开界符之后截断。
- **G5 非双重否定**：`scope` 内含双重否定构式 ⇒ 取消 H5 豁免并强制 CATCH；不做否定词奇偶计数（`_g7_predicates.py:74-75` 明载奇偶法会把两个独立否定短语误判成肯定）。

`H5 管辖成立` ⇒ `hard += H5_否定禁止管辖` ⇒ V1/PASS；失败 ⇒ 走 `_v12_rule.py:148-170` 原有 S1/S2/S3。

### 3.2 三种情形规则

| 情形 | 例子 | G1 | G2 | G3 路径 | 结果 |
|:--|:--|:--|:--|:--|:--|
| **前向管辖**（真否定） | `本节登记不宣告 N-4 正式绑定已生效` | ✅ | ✅ | 形状 b：`不`+`宣告`+`N-4 正式绑定` | **V1 / PASS 应豁免** |
| **前向管辖**（紧邻） | `不放行 N-5`、`不授实施权` | ✅ | ✅ | 形状 a：`pre[-1]='不'` | **V1 / PASS**（现盘 4 处，`_h5_regress_out.txt:81-85`） |
| **后向不管辖** | `已入账不得重复登记`、`本笔已入账 0 命中不得写成未入账` | ❌ 在 post | — | — | **不豁免 → V2 / CATCH** |
| **跨子句不管辖** | `不宣告 N-4 已生效，但本笔已入账`（token=已入账） | ✅ | ❌ 跨 `，但` | 重取 `scope='但本笔'`，无算子 | **V2 / CATCH** |
| **跨子句不管辖**（U 已切） | `不宣告 N-4 已生效；本笔已入账` | ✅ 全文 | ❌ 跨 U | U 内 `pre='本笔'` | **V2 / CATCH** |
| 双重否定抵消（G5） | `并非不宣告已生效` | ✅ | ✅ | 形状 b 本可成立，G5 命中 | **强制 V2 / CATCH** |

### 3.3 可粘贴片段

全文亦见写域 `_h5_pasteable.py`（本件下方代码块由该文件 `import re` 起至 `h5_govern` 结束逐字注入，非手抄）；粘贴位置：`_v12_rule.py:107` 之后、`def classify_v12`（`:108`）**之前**。

```python
import re

# ================= 常量（沿用 _v12_rule.py:41-43 的原始口径，片段自带以便独立粘贴） =========
H5_ADJ_NEG_CHARS = "不未无非勿没禁别"
H5_ADJ_NEG_RE = re.compile(
    r"(不得|不许|禁止|严禁|切勿|不可|不|未|无|非|勿|没|禁|别)[^。；|]{0,2}$")

# ---------- 双重否定表（R12 十式 + 实测漏式 + 分离型） ----------
# R12 十式逐字取自 lead/gate_fp7_20261108/_g7_predicates.py:76 DOUBLE_NEG_RE。
# 复用语义、不复用实现：本地超集 + 管辖微句作用域（理由见 _h5_DESIGN.md 第三步 c）。
H5_R12_TEN = (
    r"不得不|并不是不|并非不|不是不|不能不|不可不|未曾不|没有不|不无|无不"
)
H5_DN_EXTRA = (
    r"亦非不|未尝不|未始不|未有不|并非没有|并非毫无|不是没有|并不否认|"
    r"不可能不|不可谓不|不敢不|不会不|未必不|未免不|岂能不|焉能不|哪能不|不为不|莫不|"
    r"非[^，,。；;]{0,4}不(?:宣告|认定|认为|承认|说|写|登|记|填)"
)
# 长式在前，避免「并不是不」被「不是不」先吃掉
H5_DOUBLE_NEG_RE = re.compile("(" + H5_R12_TEN + "|" + H5_DN_EXTRA + ")")

# ---------- 前向辖域桥接：否定/禁止算子 + 辖域动词 + ≤24 字补语 ----------
# group(1)=算子, group(2)=辖域动词, group(3)=补语（token 落在补语末端）
H5_BRIDGE_RE = re.compile(
    r"((?:不代填|未代填|不得|不许|不可能|不可|禁止|严禁|切勿|未见|"
    r"不|未|无|非|勿|没|禁|别|莫))"
    r"(?:(?:[把将被让令以按照])[^，,；;。！？\n]{0,4}?)?"
    r"((?:宣告|宣布|宣称|声称|断言|认定|认为|承认|写成|记作|记为|标为|视作|"
    r"视为|当作|判为|登记|注明|录入|表明|代填|覆盖|应用|"
    r"填|写|记|说|做|见|算|盘|交|录|签))"
    r"([^，,；;。！？\n]{0,24})$"
)

# 微句边界（U 已按 。！？；\n 切过，这里补逗号级与转折级边界）
H5_MICRO_BREAK_RE = re.compile(r"[，,；;]|但|然而|不过|却|只是|反之|相反|另")
# 补语里出现「第二个独立主语」=> 已另起一句断言，桥接作废
H5_SELF_SUBJ_RE = re.compile(
    r"(?:本笔|本件|本节|本回件|本候选|该笔|该件|此笔|台账|母本|本域|本轮|第\s*\d+\s*笔)")
H5_CONTRAST_RE = re.compile(r"(?:但|然而|不过|却|只是|反之|相反)")

# 全句否定辖域框：句首否定标签 + token 后 40 字内谓语否定
H5_FRAME_HEAD_RE = re.compile(
    r"^\s*[^\u4e00-\u9fff]{0,4}"
    r"(?:不可能|未覆盖|未见|未做|未验|未发现|未含|无越权|非断言)")
H5_FRAME_POST_RE = re.compile(r"(?:未做|未覆盖|未见|没有|无须|无需|不用|未|无|非|不可能)")

# 引证屏蔽用（完整跨度置等长空格；未闭合开界符之后截断）
_H5_QUOTE_FULL = re.compile(r"「[^」\n]*」|『[^』\n]*』|`[^`\n]*`|“[^”\n]*”")
_H5_QUOTE_OPEN = "「『`“"
_H5_QUOTE_CLOSE = "」』`”"


def _h5_mask_quotes(pre):
    """G4 引证屏蔽：把引证跨度【内部】置为等长空格，但保留开/闭界符本身，
    使「禁止填「已生效」字样」里的 `填「` 仍能接上桥接动词；
    未闭合开界符之后的整段截断（token 落在引文内时由 H2_引述占位负责）。"""
    def blank(m):
        s = m.group(0)
        return s[0] + " " * (len(s) - 2) + s[-1]
    s = _H5_QUOTE_FULL.sub(blank, pre)
    for op in _H5_QUOTE_OPEN:
        i = s.find(op)
        if i < 0:
            continue
        j = s.find("」" if op == "「" else "』" if op == "『" else op, i + 1)
        if j < 0:
            return s[:i + 1]
    return s


def _h5_last_micro(s):
    """G2 跨子句不管辖：取最后一个微句边界之后的管辖前缀。"""
    cuts = [m.end() for m in H5_MICRO_BREAK_RE.finditer(s)]
    return s[cuts[-1]:] if cuts else s


def _h5_no_second_subject(tail):
    """补语内只允许「紧贴现语动词的直接宾语」（≤2 字），再远的主语视为另起断言。"""
    return not any(m.start() > 2 for m in H5_SELF_SUBJ_RE.finditer(tail))


def h5_govern(pre, post):
    """H5 管辖判定主入口。pre/post = 分析单元 U 内 token 的前/后缀（不含 token）。

    返回 dict：
      adj_neg           紧邻否定（形状 a，沿用原语义）
      prohibit_governs  前向禁止/否定【真的管辖该 token】（形状 b/c；取代旧 prohibit_U）
      double_neg        管辖微句内双重否定=肯定（取消豁免并强制 CATCH）
      dn_hit            命中的双重否定构式
      shapes            命中的形状清单（审计可追溯）
      scope             实际参与判定的管辖前缀

    三条硬约束：G1 前向（算子只在 pre，post 里的不得/禁止一律不管辖）；
    G2 同微句（逗号/分号/转折之后重取前缀）；G3 有辖域路径（紧邻 / 桥接 / 辖域框），
    不是「只看距离」。
    """
    p = _h5_mask_quotes(pre)
    scope = _h5_last_micro(p)

    # ---- G5 双重否定：只在管辖微句内识别，不做否定词奇偶计数 ----
    dm = H5_DOUBLE_NEG_RE.search(scope)
    double_neg = bool(dm)
    dn_hit = dm.group(0) if dm else ""

    # ---- 形状 a：紧邻管辖（≤2 字） ----
    adj_neg = bool(p) and (p[-1] in H5_ADJ_NEG_CHARS
                           or bool(H5_ADJ_NEG_RE.search(p)))

    # ---- 形状 b：辖域动词桥接（长距前向管辖，≤24 字补语，无微句边界） ----
    shapes = []
    if adj_neg:
        shapes.append("a_紧邻")
    bm = H5_BRIDGE_RE.search(scope)
    bridge = False
    if bm:
        tail = bm.group(3)
        bridge = (len(tail) <= 24 and _h5_no_second_subject(tail)
                  and not H5_CONTRAST_RE.search(tail))
        if bridge:
            shapes.append("b_桥接:" + bm.group(1) + bm.group(2))

    # ---- 形状 c：全句否定辖域框（句首否定标签 + 谓语否定） ----
    frame = (bool(H5_FRAME_HEAD_RE.search(p))
             and bool(H5_FRAME_POST_RE.search(post[:40])))
    if frame:
        shapes.append("c_辖域框")

    return {"adj_neg": adj_neg,
            "prohibit_governs": bool(bridge or frame),
            "double_neg": double_neg, "dn_hit": dn_hit,
            "shapes": shapes, "scope": scope}
```

**四处精确替换**（锚点唯一性由 `_h5_patch.py` / `_h5v_core.py:53-54` 的 `assert count==1` 实跑验证）：

```python
# ① 替换 _v12_rule.py:115-116（含 :114 注释行）
    # ---- H5 补丁：管辖 = 前向 + 同微句 + 有辖域路径 + 非双重否定 ----
    gov = h5_govern(pre, post)
    adj_neg = gov["adj_neg"]
    prohibit_U = gov["prohibit_governs"]      # ← 取代 any(k in U_bare ...)
    double_neg = gov["double_neg"]

# ② 替换 _v12_rule.py:135（:136 append 行不动）
    if (adj_neg or prohibit_U or "无已填" in U) and not double_neg:
        hard.append("H5_否定禁止管辖")

# ③ 在 _v12_rule.py:143 `if hard:` 【之前】插入（放 return 之后即成死代码）
    if double_neg:
        return {"verdict": "V2", "hard": [], "weak": [],
                "override": "H5_DOUBLE_NEG:" + gov["dn_hit"],
                "unit": U, "line": line, "review_flag": False,
                "reason": "H5 双重否定=肯定：管辖前缀内含双重否定构式，完成词为真断言"}

# ④ 替换 _v12_rule.py:152
    if hit_override and not adj_neg and not prohibit_U and not double_neg:
```

`U_bare = _strip_quotes(U)`（`:112`）保留但不再用于 `prohibit_U`。修后副本 `_h5_v12_patched.py` sha256 `d21b555a0c36b68df8fc70292646cae723abedc1658a65cc9bf24a1131c3d54b` / 17,352 B；复核员独立生成的 `_h5v_patched.py` 与之 `IDENTICAL = True`（`_h5v_core.py` 实跑输出）。

### 3.4 「只查距离不够」的反例（本会话实跑）

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_distance.py` → `_h5_distance_out.txt`；复核员独立复跑 `8 条 new = 8/8`（`_h5v_extra.py` 实跑）。

| 组 | 文本 | dist | R10 | expect | old | new |
|:--|:--|--:|:--|:--|:--|:--|
| A | `不得写成未入账的本笔已入账` | 10 | negation(2) | CATCH | PASS ❌ | CATCH ✅ |
| A | `不得宣告 N-4 正式绑定已生效` | 13 | negation(1) | PASS | PASS ✅ | PASS ✅ |
| B | `不宣告 N-4 正式绑定已生效` | 12 | negation(1) | PASS | CATCH ❌ | PASS ✅ |
| B | `本笔已入账 0 命中不得写成未入账` | **−8（在后）** | assertion(0) | CATCH | PASS ❌ | CATCH ✅ |
| C | `不宣告 N-4 已生效，但本笔已入账` | 15 | negation(1) | CATCH | CATCH ✅ | CATCH ✅ |
| C | `不宣告 N-4 已生效；本笔已入账` | 14 | assertion(0) | CATCH | CATCH ✅ | CATCH ✅ |
| D | `并非不宣告已生效` | 3 | double_neg(2) | CATCH | PASS ❌ | CATCH ✅ |
| D | `不宣告已生效` | 3 | negation(1) | PASS | PASS ✅ | PASS ✅ |

三条硬结论：① **同距不同真值**（A 组 10/13 字都在 24 字窗内，一句该 CATCH 一句该 PASS）⇒ 必须 G3 辖域路径 + 补语内无第二主语；② **后向距离为负**（B 组第二句）⇒ 只有 G1 前向能挡；③ **奇偶/距离法失效**（D 组同距 3 字、neg_count 2 vs 1 真值相反，而两个独立否定短语也是 2 个否定词却非双重否定）⇒ 必须按构式识别，且 C 组显示不含逗号的 `CLAUSE_BREAK`（`_g7_predicates.py:71`）会让 `neg_count=1` 跨「，但」污染 ⇒ G2 不可省。

### 3.5 本设计的已知管辖边界失败（partial 的根因，标 unconfirmed）

复核员 `_h5v_extra.py` / `_h5v_full.py` 实跑定位（详见 §5.5）：`H5_BRIDGE_RE` 的 `[把将被让令以按照][^，,；;。！？\n]{0,4}?` filler 上限 ≤4 字，`obj_len=5..8` 全 `bridge=False`（`_h5v_extra_out.json:filler_len` 实跑「应全 PASS，实际 5/9 PASS」）；G4 引证屏蔽把 `「N-4」` 撑成 5 空格同样断裂（`_h5_pasteable.py:47,:68-88`）；G5 只在 `pre/scope` 找双重否定，分离型「非…不可」第二个否定词在 `post` 就漏；形状 a 的 `adj_neg` 用整段 `p` 而非 G2 的 `scope`（`_h5_pasteable.py:126-127`），与 `_h5_DESIGN.md §2.1` 自述的 G2 不符；形状 c 把 `post` 补语里的「未写成未入账」误当谓语否定。这些是**设计件本身的缺陷**，本交付件不隐瞒、不代为修补（修补需所有者另行授权）。

---

## 4 双重否定识别

### 4.1 R12 现有覆盖（实读）

- `_g7_predicates.py:76`：`DOUBLE_NEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")` —— **十式、纯枚举、相邻连写**。本会话 `_h5_r12_gap.py` 实跑 `DOUBLE_NEG_RE.pattern` 逐字打印、十式 `regex=True` 全 True。
- `:69-71`：`NEG_RE`、`NEG_WINDOW = 24`、`CLAUSE_BREAK = "。！？；\n"`（**不含逗号**）；`:78-111` `r10_context` 用 `dbl = bool(DOUBLE_NEG_RE.search(pre))` 给 `kind='double_neg'`，`neg_count` 只作信息；`:134-148` `r12_scan` 对 `double_neg` 重新判违规，docstring `:136-139` 明确不用奇偶计数。
- 已登记的分离型漏式 `亦非不`：`GATE_FALSE_POSITIVE_5_6_7.md:162,267,279`（GV-L）、`GATE_N13_QUOTED_ASSERTION.md:442,467`（「本方案不修 R10/R12，只登记」）、`GATE_PIPELINE_COMPOSE.md:65,216,266,272,488`（GP-A1 人工真值=真断言而全链放过）。

### 4.2 实读 `DOUBLE_NEG_RE` 找漏（本会话实跑）

命令①：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_r12_gap.py` → **19 条** `r12_problems=0` 的漏式（`_h5_r12_gap_out.json`）：`亦非不 / 未尝不 / 未始不 / 未有不 / 莫不 / 不敢不 / 不会不 / 不可能不 / 未必不 / 未免不 / 岂能不 / 焉能不 / 哪能不 / 不可谓不 / 不为不 / 并非没有 / 并非毫无 / 不是没有 / 并不否认`；对照组 `没有不承认` 被「没有不」覆盖 `dbl=True / problems=1`，8 条表内构式全 `problems=1`。

命令②：`_h5v_full.py` 独立枚举 49 条候选 → 输出 `④ R12 漏式共 39 条；R12 与 H5 超集【都】漏 = 27 条`。本会话按该脚本 `:100-116` 同一口径复算（`python -I -X utf8 -c "<读 _h5v_full_out.json + classify_v12>"`）得 `gaps_both n= 27 NEW_PASS(should CATCH) n= 17`：`何尝不 / 安能不 / 岂敢不 / 没法不 / 没法不说 / 并非未 / 并非无 / 不由得不 / 忍不住不 / 不见得不 / 不一定不 / 不是没 / 非写成已入账不可 / 非登记不可 / 非说不 / 非但不 / 没说不`。复核回件【复核】记「13 条在 NEW 上判 PASS」，与本会话复算的 17 条口径差异**未查明**，如实并列登记，不择一掩盖。分离型四条 `_h5v_full.py:119-125` 实跑 `非写成已入账不可 / 不宣告已生效不行 / 非登记已入账不可 / 不写成已入账不成` 全 `new=PASS`（应 CATCH）。

结论：撰写人 19 式属实但**不穷尽**；「补 19 式 + 一条通配」不足以覆盖分离型（第二个否定词在 `post`）与反问/能愿式。

### 4.3 复用还是自实现

**判断：不直接 `import` / 调 R12，做「语义复用 + 本地超集 + 改作用域」**。三条理由：

1. `r12_scan`（`_g7_predicates.py:134-148`）是「全局扫描词表命中 → 报 problems」的门禁谓词，内部每命中再调 `r10_context`；H5 需要给定 `(pre,post)` 的纯函数。直接复用会把 24 字窗、不含逗号的 `CLAUSE_BREAK`、`SPAN_RE` 口径带进来（§3.4 C 组实证污染）。
2. R12 表本身有 19 条实测漏式 + GV-L + 复核员 27 条「都漏」；照抄等于移植已知漏判；且 `_g7_predicates.py` 是**绝对只读**件，本任务无权改它补表。
3. `_v12_rule.py:29` 只有 `import re`、`:4` 自述「只用 re / 静态文本」、`:108-170` 契约是单文件 `classify_v12`；引入跨目录运行时依赖破坏单文件可用性与「只出补丁设计」边界。

做法：`H5_R12_TEN` 逐字保留十式（可与既有门禁对账），`H5_DN_EXTRA` 补 19 式 + 分离型通配 `非[^，,。；;]{0,4}不(?:宣告|认定|认为|承认|说|写|登|记|填)`，长式在前防「并不是不」被「不是不」先吃；识别只在 G2 的 `scope` 内做，不数奇偶。将来若所有者授权改 `_g7_predicates.py`，正确做法是回填超集再让 V12 `import`——本补丁不代做。

### 4.4 衔接片段

`h5_govern()` 第一步（见 §3.3 完整代码 `_h5_pasteable.py:117-123`）：

```python
p = _h5_mask_quotes(pre)                  # G4
scope = _h5_last_micro(p)                 # G2
dm = H5_DOUBLE_NEG_RE.search(scope)       # G5：只在管辖微句内识别
double_neg, dn_hit = bool(dm), dm.group(0) if dm else ""
```

`classify_v12` 侧：② 让 `double_neg` 取消 H5 豁免；③ 先于 `if hard:` 主动返回 V2 并带 `H5_DOUBLE_NEG:<构式>` 审计标记；④ 让 `V2_OVERRIDE` 不与 G5 冲突；三者共用同一 `gov` 对象。实跑效果（`_h5v_final.py`）：`DOUBLE_1` V1→V2（`H5_DOUBLE_NEG:并非不`）、`DOUBLE_2` 理由从 `V2_OVERRIDE:已入账` 变 `H5_DOUBLE_NEG:不能不`、`DOUBLE_3` 从 S3 默认 V2 变 `H5_DOUBLE_NEG:无不`、`REGRESS2` `不得不`→`H5_DOUBLE_NEG:不得不`。以上仅在**这四条**上验过；§4.2 的 17 条仍是漏，**unconfirmed**。

---

## 5 样本集回归

### 5.1 样本集（正样本 18 ≥15 / 负样本 26 ≥15，共 44）

定义见 `_h5_samples.py:9-64`（本会话实读）。命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_regress.py` → `_h5_regress_out.{json,txt}`；复核员 `_h5v_full.py:160-172` 独立复算得 `44 样本 old = {'correct': 28, 'fp': 7, 'fn': 9}  new = {'correct': 44, 'fp': 0, 'fn': 0}  n = 44`。

**逐条样本**（`_h5_regress_out.txt:13-56`，`old/new` 为该条判定；PASS=应豁免，CATCH=应抓）：

| id | expect | 类别 | old | new |
|:--|:--|:--|:--|:--|
| P01 | PASS | 前向桥接 | CATCH | PASS |
| P02 | PASS | 前向桥接+NP主语 | CATCH | PASS |
| P03 | PASS | 前向桥接 | CATCH | PASS |
| P04 | PASS | 前向桥接 | CATCH | PASS |
| P05 | PASS | 前向桥接 | CATCH | PASS |
| P06 | PASS | 前向桥接 | PASS | PASS |
| P07 | PASS | 前向桥接+禁止 | PASS | PASS |
| P08 | PASS | 前向桥接+禁止 | PASS | PASS |
| P09 | PASS | 前向桥接+把字 | PASS | PASS |
| P10 | PASS | 前向桥接+引证 | PASS | PASS |
| P11 | PASS | 前向桥接+不代填 | PASS | PASS |
| P12 | PASS | 前向桥接 | PASS | PASS |
| P13 | PASS | 前向桥接+长补语 | CATCH | PASS |
| P14 | PASS | 前向管辖+后置转折不管辖 | CATCH | PASS |
| P15 | PASS | 紧邻否定 | PASS | PASS |
| P16 | PASS | 紧邻否定(32域形态) | PASS | PASS |
| P17 | PASS | 紧邻否定(32域形态) | PASS | PASS |
| P18 | PASS | 全句否定辖域框(32域形态) | PASS | PASS |
| N01 | CATCH | 后向禁止 | PASS | CATCH |
| N02 | CATCH | 后向禁止 | PASS | CATCH |
| N03 | CATCH | 后向禁止 | PASS | CATCH |
| N04 | CATCH | 后向禁止 | PASS | CATCH |
| N05 | CATCH | 跨子句否定 | CATCH | CATCH |
| N06 | CATCH | 跨子句否定 | CATCH | CATCH |
| N07 | CATCH | 跨子句否定 | CATCH | CATCH |
| N08 | CATCH | 跨子句否定 | CATCH | CATCH |
| N09 | CATCH | 双重否定:R12十式 | PASS | CATCH |
| N10 | CATCH | 双重否定:R12十式 | PASS | CATCH |
| N11 | CATCH | 双重否定:R12十式 | CATCH | CATCH |
| N12 | CATCH | 双重否定:R12十式 | CATCH | CATCH |
| N13 | CATCH | 双重否定:R12十式 | CATCH | CATCH |
| N14 | CATCH | 双重否定:R12十式 | PASS | CATCH |
| N15 | CATCH | 双重否定:R12十式 | CATCH | CATCH |
| N16 | CATCH | 双重否定:R12漏式(N13 GV-L `亦非不`) | CATCH | CATCH |
| N17 | CATCH | 双重否定:R12漏式 | CATCH | CATCH |
| N18 | CATCH | 双重否定:R12漏式 | CATCH | CATCH |
| N19 | CATCH | 双重否定:R12漏式 | CATCH | CATCH |
| N20 | CATCH | 双重否定:R12漏式 | CATCH | CATCH |
| N21 | CATCH | 双重否定:R12漏式 | CATCH | CATCH |
| N22 | CATCH | token夹在否定与禁止之间 | PASS | CATCH |
| N23 | CATCH | token夹在否定与禁止之间 | CATCH | CATCH |
| N24 | CATCH | token夹在否定与禁止之间 | PASS | CATCH |
| N25 | CATCH | 纯断言(对照) | CATCH | CATCH |
| N26 | CATCH | 纯断言(对照) | CATCH | CATCH |

### 5.2 correct / fp / fn（与修复前对比）

| 尺度 | 轨 | correct | fp（应 PASS 却 CATCH） | fn（应 CATCH 却 PASS） | total |
|:--|:--|--:|--:|--:|--:|
| A 编排方九条 | 修复前 | 4 | 1 | 4 | 9 |
| A 编排方九条 | 修复后 | 9 | 0 | 0 | 9 |
| B 自建 44 条 | 修复前 | 28 | 7 | 9 | 44 |
| B 自建 44 条 | 修复后 | 44 | 0 | 0 | 44 |

实跑输出原文：`A old = {'correct': 4, 'fp': 1, 'fn': 4, 'total': 9}  A new = {'correct': 9, 'fp': 0, 'fn': 0, 'total': 9}`；`B old = {'correct': 28, 'fp': 7, 'fn': 9, 'total': 44}  B new = {'correct': 44, 'fp': 0, 'fn': 0, 'total': 44}`。修复前 16 条错判逐条：`P01/P02/P03/P04/P05/P13/P14` 由 CATCH→PASS（7 条 fp 消除）、`N01/N02/N03/N04/N09/N10/N14/N22/N24` 由 PASS→CATCH（9 条 fn 消除）。**九条逐条修后结果**见 `_h5v_final.py` 实跑 `NEW nine = 9/9`（`_h5_regress_out.txt:2-10` 同）。

### 5.3 32 域现盘 26 处重跑（有无新错）

实跑输出：`C counts = {"old_V1": 26, "new_V1": 26, "changed": 0, "baseline_fp_mismatch": 0}`；复核员 `_h5v_full.py` 独立读盘复算 `⑥ counts = {"hits": 26, "old_V1": 26, "new_V1": 26, "changed": 0, "fp_mismatch": 0}`。逐处清单见 `_h5_regress_out.txt:61-87`（26 行，8 处旧 `H5_否定禁止管辖`）。

- **verdict 层面无新错**：`changed=0`，26 处逐处 `old==new`；`baseline_fp_mismatch=0`（32 件 main 的 sha256/字节数与 baseline 全匹配）；与 `V12_FULL_IMPACT.md:94` 基线 `V12 verdict={"V1": 26}` 一致。
- **但不等于「本来对的仍对」**：26 处**无逐处人工真值标签**，`changed=0` 只证明「没引入判定变化」。`_h5v_final.py` 实跑另发现 1 处 H5 标记变化：`DIFF lead/ledger_appendix_20261108/ pos=22852 tok=已生效 H5 False->True verdict V1->V1`，并记 `gateProblems 非空处数 = 26  r10_problems>0 处数 = 10`。故「正确性」标 **未验**，只验「无变化」。

### 5.4 2 处确凿回退是否修好

`V12_FULL_IMPACT.md:223-224` 点名的两处，`_h5v_core.py` / `_h5v_final.py` 实跑：

| 反例 | 修复前 | 修复后 | 修复后理由 |
|:--|:--|:--|:--|
| `本笔已入账 0 命中不得写成未入账` | V1 / `H5_否定禁止管辖` | **V2 / CATCH** | G1 禁止词在 post ⇒ 不管辖；`V2_OVERRIDE:已入账`（`_v12_rule.py:36/:152`） |
| `审阅不得不承认本候选已生效。` | V1 / `H5_否定禁止管辖` | **V2 / CATCH** | G5 `H5_DOUBLE_NEG:不得不` 主动返回 V2 |

输出 `⑤ both fixed = True`。同时：`TRUE_NEG` 修复前 V2 误拦→修后 V1/PASS（形状 b）；`LEAD_NEG` 前后均 V1/PASS；三条 `DOUBLE_*` 全 CATCH；`TRAIL_NEG` V1→V2。**即铁律两侧在「点名样本」上都有样本且都判对**。

### 5.5 复核自构边界（partial 的决定性失败）

`_h5v_full.py:45-81` 实跑 `③ NEW = 5/10 ; 误拦(真否定被 CATCH) = ['V02', 'V03'] ; 放过(真断言被 PASS) = ['V08', 'V09', 'V10']`：

| id | 文本 | expect | old | new | 结论 |
|:--|:--|:--|:--|:--|:--|
| V01 | 不宣告 N-4 正式绑定已生效 | PASS | CATCH | PASS | ✅ 真否定管辖放过 |
| V02 | 不得把 N-4 写成已入账 | PASS | PASS | **CATCH** | ❌ 误拦真禁止管辖（filler 5 字断桥） |
| V03 | 不得把「N-4」写成已入账 | PASS | PASS | **CATCH** | ❌ 误拦（G4 空格撑断桥） |
| V04 | 不宣告 N-4 已生效，但本笔已入账 | CATCH | CATCH | CATCH | ✅ 跨微句 |
| V05 | 本笔已入账，不得改写成未入账 | CATCH | PASS | CATCH | ✅ 后向禁止 |
| V06 | 不，本笔已入账 | CATCH | CATCH | CATCH | ✅ |
| V07 | 不得写成未入账，本笔已入账 | CATCH | PASS | CATCH | ✅ |
| V08 | 非写成已入账不可 | CATCH | PASS | **PASS** | ❌ 放过分离型双重否定 |
| V09 | 没法不宣告本件已生效 | CATCH | CATCH | **PASS** | ❌ 放过能愿式双重否定 |
| V10 | 不可能/未覆盖：本笔已入账不得写成未入账 | CATCH | PASS | **PASS** | ❌ 形状 c 误豁免 |

另 `_h5v_core.py:143-186` 的 B 系列 `③ NEW correct = 3 / 8`、`NEW WRONG ids = ['B2','B5','B6','B7','B8']`，其中 `B5 不，已入账` 应 CATCH 却 PASS（`scope=''` 但仍 `adj_neg=True`）。`_h5v_extra.py` 的 8 条距离反例 `8/8`、S1–S4 `4/4` 均判对，但按铁律「两边都要有样本」，一侧失守即 partial。**故本补丁不能称为完成，标 unconfirmed。**

---

## 6 复核回件（绑定行）+ 修复后取舍建议

### 6.1 绑定行与复核 verdict

被核对象 = 分类器本体 `lead/gate_v1v2_20261109/_v12_rule.py`（本会话 `hashlib` 复算，与编排方【实跑指纹】第 1 项及 `V12_FULL_IMPACT.md:304` 一致）：

被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148

**复核 verdict = partial ⇒ 标 unconfirmed**。复核【复核】字段逐项：① 指纹 8/8 MATCH 通过；② 九条 9/9 通过、独立重建修后副本 `IDENTICAL=True`；③ 管辖判定 **partial 的决定性失败**（V02/V03 误拦真否定；V08/V09/V10/B5 放过真断言；`NEW=5/10`）；④ 19 式属实但不穷尽（复核员枚举 49 条，R12 漏 39、R12 与 H5 超集都漏 27）；⑤ 两处回退真修好；⑥ 32 域数字复现但「本来对的仍对」未验；⑦ 第五步(a) 通过；⑧ 越界通过。**本交付件如实记为 partial / unconfirmed，不改写为 confirmed。**

### 6.2 能否插生产门禁

**不能全局插入；结论标未验（可插 = 否）。** 依据：

- `V12_FULL_IMPACT.md:287` 明列四条前置条件「只对白名单 3 域启用 / 先修 H5 管辖误判与 `V2_OVERRIDE` 自指词 / S3 不再无条件 fail-closed / 补齐逐处回归门槛并先影子 N≥3 轮」，缺一即净损失；本补丁只满足第 2 条的一半（H5 在指定样本集内改善，但 §5.5 外推失败）。
- `V12_FULL_IMPACT.md:333`：「按 2/3/4，**当前 V12 在 11 条反例上全不达标 → 本评估不建议把分类器真正插入任何生产门禁**」；`:344` 总闸门：「在门槛补齐并修掉 H5 管辖误判 / `V2_OVERRIDE` 自指词之前，**不建议把分类器真正插入任何生产门禁**」。
- 本补丁**只针对 H5**，`severity=high`（对「全库直接插入」）；且原回归套件、影子 N≥3 轮本会话**未验**（§6.5）。

### 6.3 其余缺陷逐条（本补丁未修）

| # | 缺陷 | 证据（文件:行 / 实跑） | 状态 |
|--:|:--|:--|:--|
| 1 | `V2_OVERRIDE` 把禁用词自身当宣称词（`已入账` 检索/标题形态 6 处误判） | `_v12_rule.py:36,:149-156`；`V12_FULL_IMPACT.md:242-247,328` | 未修 |
| 2 | S3 无条件 fail-closed：3 处应 PASS 被误拦，P09/P10 同型句随格式抖动 | `_v12_rule.py:167-170`；`V12_FULL_IMPACT.md:230-232,289-296,327` | 未修 |
| 3 | 提前 return 抹掉 `hard/override` 双标记（`hard∧override=2`、`hard∧weak=9`） | `_v12_rule.py:143-146`；`V12_FULL_IMPACT.md:260,330` | 未修 |
| 4 | R12 侧双重否定表仍漏（19 式 + `亦非不` GV-L + 复核员 27 条「都漏」）；`_g7_predicates.py:76` 绝对只读 | `_h5_r12_gap_out.json`、`_h5v_full_out.json`；`GATE_PIPELINE_COMPOSE.md:266,488` | 仅 V12 侧部分补 |
| 5 | 词表/证据不独立：N13 C 类转发 R10 kind、R12 复用 `r10_context`，一致通过 ≠ 正确 | `GATE_PIPELINE_COMPOSE.md:63,272,499` | 未修（跨层架构） |
| 6 | 本补丁形状表是枚举/启发式：filler ≤4 字、桥接动词表、24 字上限、`SELF_SUBJ` 词表；分离型「非…不可」、反问/能愿式、跨行/被动/英文未覆盖 | `_h5_pasteable.py:44-65`；`_h5v_extra_out.json:filler_len`；`_h5v_full_out.json:gaps_both` | **部分且已实证失败**（§5.5） |
| 7 | 32 域 26 处无逐处人工真值标签，`changed=0` 不能证明本来对的仍对 | `_h5v_final.py:81-84` 实跑 | 未验 |
| 8 | 1 处 H5 标记变化（`ledger_appendix_20261108` pos=22852 `已生效` H5 False→True，verdict 仍 V1） | `_h5v_final.py` 实跑 `DIFF …` 行 | 已登记，语义后果未验 |

### 6.4 达到可插条件清单（10 条，沿用 `_h5_DESIGN.md §5.3` / `V12_FULL_IMPACT.md:324-331`）

| # | 条件 | 本会话状态 |
|--:|:--|:--|
| 1 | 指纹门槛：加载前 `hashlib` 验 `_v12_rule.py` / `_g7_predicates.py` / baseline 32 件，失配拒绝运行 | ✅ 8/8 MATCH 实跑通过（§2.1）；落地后须更新为新指纹 |
| 2 | H5 管辖门槛：2 处回退 CATCH + `TRUE_NEG`/`LEAD_NEG` PASS + 三条 `DOUBLE_*` CATCH | ✅ 点名 9/9 达标；⚠️ 复核自构 10 条仅 5/10 ⇒ **unconfirmed** |
| 3 | 样本集门槛：正≥15 + 负≥15、四类负样本齐备、correct=total / fp=0 / fn=0 | ✅ 44/44、fp=0、fn=0（自建集）；⚠️ 外部边界集 5/10 ⇒ **unconfirmed** |
| 4 | 32 域逐处对账：26 处一致、`changed=0`、无新回退 | ✅ 数字达标；⚠️ 无真值标签 ⇒ 正确性未验 |
| 5 | `V2_OVERRIDE` 自指词：6 处检索/标题形态必须 PASS | ❌ 不达标（`V12_FULL_IMPACT.md:328`） |
| 6 | S3 门槛：P09/P15/TV3:L10 三处应 PASS 必须 PASS | ❌ 不达标（`V12_FULL_IMPACT.md:327`） |
| 7 | 双标记回报：`hard∧override`(2) / `hard∧weak`(9) 输出同触可见 | ❌ 不达标（`:330`） |
| 8 | 原回归套件 `_v12_verify.py` 的 V1 22/22、V2 14/14、MIXED 4/4 须 100% | **未验**（本会话未重跑；`V12_FULL_IMPACT.md:348`） |
| 9 | 影子 N≥3 轮：连续 N 轮 `新增误报=0 且 回退=0 且 S3 误拦=0` | **未实施**（`V12_FULL_IMPACT.md:335`） |
| 10 | 双重否定统一：19 式 + `亦非不` + 27 条「都漏」回填 `_g7_predicates.py:76`（需另一写域授权） | **未实施** |

**总闸门**：1–4 在指定样本集内达标（3/4 附 unconfirmed 与未验注记），5–10 未达标 / 未验 ⇒ **可插 = 否**。

### 6.5 H5 修不好的替代方案（5 档，均不把 V1/V2 分类器插进真门禁）

1. **白名单 + 精确参数匹配（首选）**：按 `(domain, tuple(banned))` 精确匹配 3 域（`c07_slot` / `c07_truth_protocol` / `s604_script_hunt`），不在白名单**完全不调用 `classify_v12`**，保留原 R10/R12 结论；排除 `DEFAULT_TOKENS=("已入账","已追加","已生效")` 与 `ASSERT_TOKENS` 五词门禁族（`V12_FULL_IMPACT.md:314-322`）。
2. **窄补丁 + 只报 warning**：把 `:116` 改成 `prohibit_pre = any(k in pre for k in PROHIBIT)`，只修后向/跨子句，放弃长距前向；H5 只作 warning 不判 verdict，拿不准交 `NEEDS_HUMAN`。代价与语义风险最小（代价：TRUE_NEG 仍被 S3 误拦、双重否定仍漏）。
3. **回退在位 N13/R13 轨**：`V12_FULL_IMPACT.md:286` 实跑 `N13 gate correct=43/45 (FP=0,FN=2)` 优于 `V12 correct=34/45 (FP=9,FN=2)`；`GATE_PIPELINE_COMPOSE.md:414` 合成链 69/74。V12 仅留影子差分。
4. **H5 降级为审计标记**：`H5_否定禁止管辖` 不改 verdict，只写 `review_flag` / `shapes[]`，人工逐处裁决；真门禁继续走朴素字面 + R9/R11（与 `V12_FULL_IMPACT.md:296` 对 S3 的建议同构）。
5. **词表/语料层面堵口（最保守）**：交付模板禁止「完成词与禁止词同单元」写法，把 REGRESS1 类句子改写为两条分句；`GATE_PIPELINE_COMPOSE.md:499` 提醒「一致不是正确」，仍需人工抽检。

### 6.6 未验项与越界核对（如实登记）

- **未验**：`_v12_verify.py` 的 V1 22/22 / V2 14/14 / MIXED 4/4 原回归套件本会话**未重跑**；影子 N≥3 轮**未实施**；「S3 verdict 回退上一轨 + NEEDS_HUMAN」完整后果**未实测**；编排方 `v12_api` 原始脚本**未独立重放**（脚本不在本次可读件里，`V12_FULL_IMPACT.md:349`）；32 域 26 处逐处正确性**未验**；复核回件「13 条 PASS」与本会话复算 17 条的口径差异**未查明**；§3.5 的管辖边界失败**未修补**。本补丁**未插任何真门禁**，全部为影子/写域副本对照。
- **越界核对（本会话实跑 `_h5v_final.py` §⑧ 与末次 `hashlib` 复算）**：七件只读件 `sha_ok=True`、mtime 均为会话前；只读域 mtime > 2026-11-09 14:35 的文件 `count = 0`；`__pycache__` 时间戳 12:18:26 / 00:45:10 未变；`git status --porcelain -- <8 路径 + 写域>` 输出仅会话前既有 `MM lead/GOAL_THREE_TARGETS_20261018.md`、`MM lead/PENDING_DECISIONS.md` 与各 `??` 目录，写域仅 `?? lead/h5_governance_20261109/`；写域文件全部 `_h5_` / `_h5v_` 前缀（本交付件 `H5_GOVERNANCE_FIX.md` 为写域内新件，无前缀，属交付文件名要求）。未改 `_v12_rule.py` 或任何既有件，不 commit、不 push，零真机、零采样代码。

### 6.7 本会话实跑命令清单（全部 `python -I -X utf8` + 绝对路径）

| # | 命令 | 关键输出 |
|--:|:--|:--|
| 1 | `…\_h5v_fp.py` | `ALL_MATCH = True count = 8` |
| 2 | `…\_h5_repro9.py` | `loaded = True`，九条逐行 JSON |
| 3 | `…\_h5_regress.py` | `A old/new`、`B old/new`、`C counts` |
| 4 | `…\_h5_distance.py` | 8 条距离反例 |
| 5 | `…\_h5_r12_gap.py` | 十式全 True、19 条 `r12_problems=0` |
| 6 | `…\_h5v_core.py` | `② nine MATCH count = 9 / 9`、`③ NEW correct = 3 / 8`、`⑤ both fixed = True`、`IDENTICAL = True` |
| 7 | `…\_h5v_extra.py` | `8 条 new = 8/8`、S1–S4 4/4、filler `5/9 PASS` |
| 8 | `…\_h5v_full.py` | `③ NEW = 5/10`、`④ R12 漏式共 39 条；都漏 27 条`、`⑥ counts`、`44 样本 … new = {'correct': 44, 'fp': 0, 'fn': 0}` |
| 9 | `…\_h5v_final.py` | `NEW nine = 9/9`、`DIFF … H5 False->True`、越界核对 |
| 10 | `python -I -X utf8 -c "<gaps_both 复算>"` | `gaps_both n= 27 NEW_PASS(should CATCH) n= 17` |
| 11 | `python -I -X utf8 -c "<末次 hashlib/mtime>"` | 七件 `sha_ok=True`、pyc 时间戳未变 |
