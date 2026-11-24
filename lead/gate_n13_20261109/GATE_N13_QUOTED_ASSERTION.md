# GATE_N13_QUOTED_ASSERTION.md — N13 / R13 谓词：引用/否定/清单语境下的完成词不算断言

> 唯一写域 `lead/gate_n13_20261109/`。零真机、零采样代码；只做静态文本、正则、`hashlib` 指纹。不 commit、不 push。
> 本件为**第二轮修订稿**：承接复核 `verdict = partial`（④ 5/5 新负样本漏网、⑦ 真删文件不产出生效 FAIL），两项缺陷已实跑修复并在 §4/§6 逐条回判。
> 复核结论按铁律如实登记：原轮 **partial**；因本件未经复核方重签，**partial 标 unconfirmed**（见 §6.1）。

## 1 目的与边界

**目的**：把旧朴素字面门禁 `for bad in ['已入账','已追加','已生效']: if bad in t: P.append(...)` 换成语境谓词，使其同时做到：

- **放过** A 检索动作 / B 小节标题·表头列名·目录清单 / C 否定式三类语境；
- **抓住** 三类语境之外的 **D 真断言**（含同句混用、表格数据行、词表拆分裂缝、A/B 标记劫持）。

**只做** A/B 两类新谓词 + 朴素门禁 → 谓词化门禁的迁移配方。**不做的**：

| 不做 | 依据 / 边界 |
|:--|:--|
| 不改草案正文、不改两件台账 | 铁律：`lead/ledger_bound_20261109/`、`lead/ledger_appendix_20261108/` 绝对只读；收尾指纹见 §6.3 |
| 不改历史 payload | `.zcode/workflow-runs/` 全部 mjs 绝对只读，只 Read；旧门禁复现用写域内重建脚本 `_n13v_hist_gate_replay*.py` |
| **不重写 R10 的 C 类** | `lead/gate_fp7_20261108/_g7_predicates.py:78-111` `r10_context`、`:113-130` `r10_scan` 已实现 `negation` / `quote_mention` 豁免；`:134-148` `r12_scan` 已实现双重否定守卫。N13 只消费 R10 的 `kind`，并加「否定必须落在 token 自己的微段内」的局部性守卫（§5.2 如实说明这是补缝，不是整体重做） |
| 不放宽判据 | 复核指出「豁免外溢」后，第二轮把豁免从**整行/整子句**收窄到**逐 token 微段**；负样本 18 → 26 条，正样本仍 16 条全放过（§4） |

**必现四类定义**：A = 检索动作（`grep`/清点/核查/`有没有…？`/`grep=0`/`0 命中`）；B = 小节标题 `#`/表头列名 `| … 已入账? |`/目录清单 `§1 总览 / §2 …`；C = 否定式（`不宣告…已生效`、`不得写成「本笔已生效」`）；D = 真断言（`本笔已于 §605 入账`、`已生效，可应用母本`）。

## 2 上游指纹（七件）+ 三处误报逐行语境判类表

### 2.1 七件指纹（本会话实算）

命令（本会话实跑，`python -I -X utf8 -c`，绝对路径 + `hashlib`）：

```
python -I -X utf8 -c "import hashlib,os; B='D:/Project/ra2-campaign-forge/'; fs=[...七件...]; [(lambda p,f: print(f, (hashlib.sha256(open(p,'rb').read()).hexdigest(), os.path.getsize(p)) if os.path.isfile(p) else ('MISSING',0)))(B+f,f) for f in fs]"
```

输出（与编排方【编排方指纹】逐位一致）：

| 件 | SHA256 | 字节数 |
|:--|:--|--:|
| `lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md` | `47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70` | 70587 |
| `lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md` | `7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43` | 60272 |
| `lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md` | `724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e` | 45719 |
| `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 |
| `lead/r9r12_20261109/_g9_gate.py` | **MISSING** | 0 |
| `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

`lead/r9r12_20261109/_g9_gate.py` 现盘 MISSING（与派发一致）；真正回归模块在 `lead/gate_r9r12_20261109/_g9_gate.py`，实读 `:24` 固定顺序、`:40-52` 指纹门、`:206-230` self_test，实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_r9r12_20261109/_g9_gate.py` → `"all_pass": true`。

### 2.2 三处误报：自己复跑、逐行核对，不采信派发表

命令（本会话实跑，逐行 repr 扫三件）：

```
python -I -X utf8 -c "import io; B='D:/Project/ra2-campaign-forge/'; fs=[...]; ws=['已入账','已追加','已生效']; [(lambda p,f: [print(f+':'+str(i)+' ['+w+'] '+ln.rstrip()) for i,ln in enumerate(io.open(p,encoding='utf-8'),1) for w in ws if w in ln])(B+f,f) for f in fs]"
```

输出：合订本 **7 命中** `:54 / :77 / :79 / :87 / :209 / :242 / :338`；草案 **3 命中** `:28 / :174 / :275`；`已追加` 两件 **0 命中**。逐字原文与派发【三处误报原文】一致；附录草案另有 `:146 / :177 / :194`（均为 C 否定式，不在本次被扫两件内，如实登记）。历史 payload `.zcode/workflow-runs/dwfrun-5876dbf3-36f9-4f9c-8ec3-8a7fefb07395.mjs` 的 `ASK_ANALYST` 背景语逐字为「· :28 / :275 …；· :54 / :77 / :79 / :87 / :338 …；· :174 / :209 / :242 …」——所谓「三处」实为**三组共 10 处**。

实读确认：`LEDGER_BOUND_VOLUME.md:87` 是表头，下一行 `:88` = `|:--:|:--:|:--|:--|--:|:--|` 分隔行，`:89` 才是数据行 `| 1 | §605 | … | 否（grep 0 命中） |`；`:209 / :242 / :174` 的「不宣告 N-4 正式绑定已生效」落在行尾加粗否定分句，全文 439 字符逐字读过后才判 C。

### 2.3 逐处判类表（A/B/C/D + 现有 R10 会判成哪一类）

「R10 实判」= 本会话 `g7.r10_scan(该行, [该词])` 与全文 `g7.r10_scan(text, WORDS)` 双跑的 `kind`（源码 `_g7_predicates.py:78-130`）。命令 `python -I -X utf8 -c "<逐行+全文 r10_scan>"` 输出全文 kinds = `{assertion:5, negation:2}` / `{assertion:2, negation:1}`，与本表逐格一致。

| 件:行 | 词 | 原句要点 | 判类 | 依据 | R10 实判 | 需否新规则 |
|:--|:--|:--|:--:|:--|:--|:--|
| 草案 :28 | 已入账 | `### 1(c) 有没有已入账的？` | **A/B** | `###` 小节标题 + 「有没有…的？」问句，无主语谓语 | `assertion` → 误报 | 要（R13 A/B） |
| 草案 :275 | 已入账 | `1(c) 已入账 grep=0` | **A/B** | 一页纸总览目录枚举 + `grep=0` 检索结果，非句子 | `assertion` → 误报 | 要（R13 A/B） |
| 合订 :54 | 已入账 | `## 2 · … + 已入账 grep 结果` | **B**（A 亦覆盖） | `##` 小节标题，完成词是「检索结果」名词短语的定语 | `assertion` → 误报 | 要（R13 B） |
| 合订 :77 | 已入账 | `### 2.2 待入账清点 + 已入账 grep 结果` | **B** | `###` 小节标题 | `assertion` → 误报 | 要（R13 B） |
| 合订 :79 | 已入账 | `**已入账核查实跑命令**：` | **A** | 核查动作的冒号标签，「已入账」是被核查的对象 | `assertion` → 误报 | 要（R13 A） |
| 合订 :87 | 已入账 | `\| … \| 草案件字节 \| 已入账? \|` | **B** | 表头列名（下一行 `:88` 为分隔行），列名带 `?` 问询 | `assertion` → 误报 | 要（R13 B） |
| 合订 :338 | 已入账 | `§1 总览 / §2 … 已入账 grep / §3 …` | **B**（A 亦覆盖） | 目录/结构枚举（§ 串 + 章节名），非句子 | `assertion` → 误报 | 要（R13 B） |
| 合订 :209 | 已生效 | `…本节登记不宣告 N-4 正式绑定已生效）。` | **C** | 「不宣告」直接否定完成词，R10 回看窗 24 字符内命中 `不` | `negation`（R10 已覆盖）→ 正确放过 | 不要 |
| 合订 :242 | 已生效 | 同款加粗否定分句 | **C** | 同上 | `negation`（R10 已覆盖）→ 正确放过 | 不要 |
| 草案 :174 | 已生效 | 与 :242 同款逐字引文 | **C** | 同上 | `negation`（R10 已覆盖）→ 正确放过 | 不要 |

**汇总**：10 处命中 = **A/B 7 + C 3 + D 0**。R10 对 C 类 3 处全部正确豁免；对 A/B 7 处全部误判 `assertion`（会 FAIL）。**没有 D 类被判成 C**。

## 3 实现

### 3.1 R13 谓词完整可粘贴片段

以下为**完整可粘贴片段**，逐字即写域 `_n13_pasteable.py`（8,122 B）；生产模块为 `_n13_predicates.py`（16,649 B，同一算法 + `r13_scan` 明细入口 + 文件尾迁移注释）。本会话实跑验证：粘贴片段正样本 16/16 放过、负样本 26/26 抓住、三真件 D=0（命令与输出见 §4.4）。

```python
# -*- coding: utf-8 -*-
# R13 谓词完整可粘贴片段（A 检索动作 / B 小节标题·表头·目录 / C 交 R10 / D 默认 FAIL）
# 用法：把本段整段粘进门禁脚本，按 §3 的迁移配方调用 r13_assertions(t, WORDS, r10_scan, r12_scan)
import re

WORDS = ('已入账', '已追加', '已生效')
_LEAD = re.compile(r"^\s*(?:[-*+>]\s+|\d+[.)]\s+|[①-⑳]\s*)*\s*")
_SEG = "。！？；\n，,、：:|+/（）()【】<>*#=`"   # 微段边界（含冒号/斜杠/竖线）
_HEAD = re.compile(r"^#{1,6}\s")
_TROW = re.compile(r"^\|.*\|\s*$")
_TSEP = re.compile(r"^\|[\s:|-]+\|\s*$")
_TOC = re.compile(r"(?:§|一页纸总览|总览|1\([a-c]\)|目录|大纲|结构|五节|五章|章节)")
# A/B 标记只允许在 token 之后的同一微段内（或「有没有/是否」在 token 之前）
_AFTER = re.compile(r"grep|检索|搜索|查找|清点|核查|核对|实跑命令|核查动作|结果|=0\b|"
                    r"0\s*(?:逐字)?命中|否（grep|[？?]|清单|总览|目录|结构|五节|五章|章节")
_ASK = re.compile(r"有没有|是否|查有无|查是否")
_ASKTAIL = re.compile(r"[？?]|的\s*$")
# 结构性前缀（剥净后仍有字 = 主语 ⇒ D）
_STRUCT = re.compile(r"\s+|#{1,6}\s*|\d+\s*|[（(][a-zA-Z0-9]+[）)]\s*|[①-⑳]\s*"
                     r"|[·•\-+*|/>“”‘’`_=「」『』【】\[\]{}〈〉§]+\s*"
                     r"|有没有|是否|查有无|查是否|(?:一|二|三|四|五|六|七|八|九|十)、"
                     r"|上游指纹|待入账清点|一页纸总览|总览|目录|大纲|结构|五节|五章|章节|清单")
_NEG = re.compile(r"不宣告|不得不|并非不|并不是不|不是不|不得|不能|不可|并未|亦非|"
                  r"未见|未验|未核|未确认|否决|排除|禁止|请勿|无越权|没有不")
_QUOTE = re.compile(r"「[^」]{0,120}」|“[^”]{0,120}”|\"[^\"]{0,120}\"")
_BAN = re.compile(r"不得|不能|不可|禁止|请勿")
_POSTAIL = re.compile(r"(?:已|现|正式)(?:生效|入账|追加)\s*[，,、；;]?\s*"
                      r"(?:可应用|可改|放行|具备|无需|照此|即)")
_CONTRAST = re.compile(r"(?:但|但是|然而|而|且|另外|另|同时|并)\s*[^，。；\n]{0,24}?(?:已入账|已追加|已生效)")
_SUBJ = (r"(?:本笔|本件|该笔|该件|此笔|此件|该条|本条|此条|本节|母本|台账|本候选|本回件|"
         r"本交付件|本项|该项|此项|本草案|该草案|第\s*[一二三四五六七八九十\d]+\s*笔|笔\s*\d+|N-?\d+)")
_SPLIT = re.compile(r"(?:" + _SUBJ + r")\s*(?:已|现|正式|业已|现已|现正式)\s*"
                    r"(?:于\s*§\s*\d+\s*|至\s*台账\S{0,8}\s*|经\s*)?(?:入账|追加|生效)")


def _body(line):
    m = _LEAD.match(line)
    return (line[m.end():], m.end()) if m else (line, 0)


def _seg_of(s, a, b):
    lo, hi = 0, len(s)
    for ch in _SEG:
        j = s.rfind(ch, 0, a)
        if j + 1 > lo:
            lo = j + 1
        j = s.find(ch, a)
        if j != -1 and j < hi:
            hi = j
    return s[lo:hi], a - lo, b - lo


def _subject(pre):
    return bool(_STRUCT.sub("", pre).strip())


def _header(lines, i):
    body, _ = _body(lines[i])
    if not _TROW.match(body):
        return False, False
    nxt, _ = _body(lines[i + 1]) if i + 1 < len(lines) else ("", 0)
    if _TSEP.match(nxt) or re.search(r"[?？]|是否", body):
        return True, True
    return False, True


def _toc(body):
    if not _TOC.search(body) or "。" in body or "；" in body:
        return False
    return bool(re.search(r"§\d+|/\s|\+\s|\|\s|[（(][a-zA-Z0-9]+[）)]", body) or "总览" in body)


def _split_lines(text):
    out = {}
    for li, line in enumerate(text.splitlines(), 1):
        for m in _SPLIT.finditer(line):
            seg, _, _ = _seg_of(line, m.start(), m.end())
            if _NEG.search(seg):
                continue
            if any(q.start() <= m.start() and m.end() <= q.end()
                   for q in _QUOTE.finditer(line)):
                continue
            out.setdefault(li, []).append(m.group(0).strip())
    return out


def _line_positive(body, occ, splits):
    for tok, a, b in occ:
        seg, ra, _ = _seg_of(body, a, b)
        if _NEG.search(seg[:ra]):
            continue
        if _subject(seg[:ra]) or _CONTRAST.search(seg):
            return True
    for m in _POSTAIL.finditer(body):
        seg, _, _ = _seg_of(body, m.start(), m.end())
        if not _NEG.search(seg):
            return True
    return bool(splits)


def r13_assertions(t, tokens=WORDS, r10_scan=None, r12_scan=None):
    """返回 (problems, details)；problems 只含 D 类。C 类必须 R10 同意才豁免。"""
    L = t.splitlines()
    hdr = [_header(L, i) for i in range(len(L))]
    r10, r12 = {}, set()
    if r10_scan:
        for h in r10_scan(t, list(tokens))[2]:
            r10[(h["token"], h["pos"])] = h["kind"]
    if r12_scan:
        for h in r12_scan(t, list(tokens))[1]:
            r12.add((h["token"], h["pos"]))
    splits = _split_lines(t)
    problems, details, base = [], [], 0
    for li, line in enumerate(L):
        body, off = _body(line)
        occ = [(tok, m.start(), m.end()) for tok in tokens
               for m in re.finditer(re.escape(tok), body)]
        if not occ and li + 1 not in splits:
            base += len(line) + 1
            continue
        mixed = _line_positive(body, occ, splits.get(li + 1, []))
        bstruct = _HEAD.match(body) or hdr[li][0] or (_toc(body) and not hdr[li][1])
        for tok, a, b in occ:
            pos = base + off + a
            seg, ra, rb = _seg_of(body, a, b)
            pre, suf = seg[:ra], seg[rb:]
            kind, rule, degraded = "D", "", False
            if mixed:
                rule = "同句混用：行内另有肯定断言"
            elif (tok, pos) in r12:
                rule = "R12 双重否定构式=肯定"
            else:
                neg = bool(_NEG.search(pre)) or bool(
                    any(q.start() <= a and b <= q.end() for q in _QUOTE.finditer(body))
                    and _BAN.search(_QUOTE.sub(" ", body)))
                k = r10.get((tok, pos)) if r10_scan else None
                if neg and k in ("negation", "quote_mention"):
                    kind, rule = "C", "C 否定式（R10 " + k + " 已覆盖）"
                elif neg and r10_scan is None:
                    rule, degraded = "降级：无 R10，C 类不自行豁免 → 默认 FAIL", True
                elif neg:
                    rule = "R10 " + str(k) + "：微段否定不采纳 → 默认 FAIL"
                elif _subject(pre):
                    rule = "D 真断言：微段内 token 前有主语"
                else:
                    hit = _AFTER.search(suf)
                    ask = _ASK.search(pre) and _ASKTAIL.search(seg)
                    if hit or ask:
                        kind, rule = ("B" if bstruct else "A"), (
                            ("B 小节标题/表头/目录：" if bstruct else "A 检索动作：")
                            + repr((hit or _ASK.search(pre)).group(0)))
                    else:
                        rule, degraded = "默认 FAIL：微段内无 A/B 标记且无直接否定", (r10_scan is None)
            details.append({"token": tok, "pos": pos, "line": li + 1,
                            "quote": line.strip(), "kind": kind, "exempt": kind in ("A", "B", "C"),
                            "rule": rule, "r10_kind": r10.get((tok, pos)), "degraded": degraded})
            if kind == "D":
                problems.append("越权断言 %s（N13 D 类，L%d：%s）" % (tok, li + 1, rule))
        base += len(line) + 1
    for li, hits in splits.items():
        for h in hits:
            details.append({"token": h, "pos": -1, "line": li, "quote": L[li - 1].strip(),
                            "kind": "D", "exempt": False, "rule": "词表拆分裂缝：主语+完成动词",
                            "r10_kind": None, "degraded": False})
            problems.append("越权断言 %s（N13 D 类·词表拆分裂缝，L%d：主语+完成动词）" % (h, li))
    return problems, details
```

**★ 复核 ④ 的修法（本轮核心，不放宽判据）**：旧版把 A/B/C 豁免发在**整行/整子句**上，凡行内出现 `grep`、`未验`、`§` 就把该行所有命中豁免掉，且 `r13_assertions:344-346` 把 A/B/C 豁免行整体跳过 `_SPLIT_ASSERT`，于是 `未验：本笔已入账`、`grep 结果：此笔已入账`、`§2 清单 / 此笔已入账 / §3 依赖` 等成族漏判。第二轮改为：

1. `_SEG` 微段边界含 `: / | + （ ） * # = ` 等，使「`grep 结果：`」「`未验：`」「`/ 此笔已入账 /`」各自独立成段（`_n13_pasteable.py:8`、`:41-50`）；
2. A/B 标记**只允许在 token 之后的同一微段内**（`:13-15`、`:146-151`）；「有没有/是否」问句只在 token **之前**且段尾有 `？` 时生效；
3. `_subject(pre)` 不再依赖封闭主语词表：剥掉结构性前缀后**仍有任意文字即视为主语** ⇒ D（`:18-22`、`:53-54`、`:143-144`），故 `此笔`、`该条`、`第 5 笔`（带空格）、`§605` 一律抓住；
4. C 豁免要求 `_NEG` **显式否定短语落在 token 自己的微段内**且 **R10 同意**（`:23-24`、`:137-142`），「`未验：`」在上一微段不再一键废掉整行；
5. `_SPLIT_ASSERT` 逐行补 D，**不再跳过任何 A/B/C 行**（`:160-165`）；三真件实测 `split_hits=0`。

### 3.2 朴素门禁 → R10+R12+R13 词表化流程：迁移配方改前改后对照

**改前 3 行**（既有朴素字面门禁；实读 `lead/gate_doc_name_fix_20261109/_dnv_sandbox36/ledger_appendix_20261108/_dnv_gate.py:14-15`，同形见历史 payload `dwfrun-614dbceb-b7e1-4dbb-b811-41d148f56a9a.mjs` 的 `GATE_CODE`）：

```python
for bad in ['已入账','已追加','已生效']:
 if bad in t: P.append('含越权断言 '+bad)
```

**改后**（5 条语句，粘贴块 10 行；`N13` / `G7` 为调用方已有的两个绝对路径）：

```python
try:
 import importlib.util as _u, pathlib as _p
 if not (_p.Path(N13).is_file() and _p.Path(G7).is_file()): raise ImportError('谓词模块缺失')
 _s=_u.spec_from_file_location('_n13',str(N13));_m=_u.module_from_spec(_s);_s.loader.exec_module(_m)
 _g=_u.spec_from_file_location('_g7',str(G7));_g7=_u.module_from_spec(_g);_g.loader.exec_module(_g7)
 for _p in _m.r13_assertions(t,['已入账','已追加','已生效'],r10_scan=_g7.r10_scan,r12_scan=_g7.r12_scan)[0]: P.append(_p)
except (ImportError, OSError, AttributeError):
 for bad in ['已入账','已追加','已生效']:
  if bad in t: P.append('含越权断言 '+bad)   # 降级：字面全拦，绝不静默 PASS
```

**★ 复核 ⑦ 的修法**：旧配方 `except ImportError` 抓不到 `spec.loader.exec_module` 在**真删文件**时抛的 `FileNotFoundError`（`OSError` 子类），门禁无 JSON 输出直接崩。本轮加 `Path(...).is_file()` 预检 + `except (ImportError, OSError, AttributeError)`。实测 `_n13v_migration.py` 的 `M1 / M1b / M2`（真把 `_n13_predicates.py` 改名到写域内、以及把 G7 指向不存在文件）全部返回 `{"ok": false, "problems": ["含越权断言 已入账", "含越权断言 已生效"]}`，`N13V_MIGRATION_ALL_PASS = True`（§4.4）。「改后 5 行」指 **5 条语句**（try / import / 预检 / 两次加载 / for / except / 降级共 10 行粘贴块），复核指出原稿「改后 5 行」是行数口径瑕疵，此处更正。

**接口不变**：仍读同一个 `t`、仍 append 到同一个 `P`、仍输出 `ok = not P` 的 `{ok:bool, problems:list}`；问题串仍为 `含越权断言 <token>` 家族（改后由谓词生成 `越权断言 <token>（N13 D 类…）`）。`_n13_migration_check.py` U1 实跑「三形态均返回 {ok:bool, problems:list}」。

### 3.3 判别顺序、边界处理、拿不准默认 FAIL

**判别顺序**（逐处命中，粒度 = 一个 token 的一次出现）：

```
⓪ 行级同句混用：本行另有肯定完成断言（主语+完成词 / 「但…已入账」/ 可应用型 / 拆分形态）→ 全行 D
① 该命中在 R12 double_neg 集合 → D（双重否定=肯定）
② 微段内显式直接否定 且 R10 kind ∈ {negation, quote_mention} → C（放过）；R10 不同意 / 无 R10 → D
③ 微段内 token 前有非结构性名词（主语）→ D（真断言）
④ 微段内 token 之后有 A/B 标记，或 token 之前是「有没有/是否…？」问句 → B（若本行是 # 标题/表头/目录）或 A
⑤ 其余（裸完成词、拿不准、无 R10、R10 未同意）→ D（默认 FAIL）
⑥ 逐行补「主语 + 完成动词」拆分形态 → D（不再跳过 A/B/C 行）
```

R12 必须接在 R10 **之后**：`_g7_predicates.py:123-129` 对 `double_neg` 两分支都不进（静默），`lead/gate_r9r12_20261109/_g9_gate.py:24` 固定顺序 R9→R10→R12→R11 同一理由。完整链见 §5.3。

**边界处理**：

- **同句混用**（任务第二步(c) 点名）：`_line_positive`（`_n13_pasteable.py:87-98`）逐微段扫主语+完成词、`_CONTRAST`（但/且…已入账）、`_POSTAIL`（已生效，可应用）、拆分形态；只要一处肯定，**该行所有豁免作废**。`不宣告 X 已生效，但 Y 已入账` → D（补 R10 `CLAUSE_BREAK = "。！？；\n"` 不含逗号的裂缝，`_g7_predicates.py:71`）。
- **行首缩进 / 列表符号 / 表格竖线**：`_body` 剥 `_LEAD`（`- * + >` / `1.` / `①`）；`_header` 用下一行 `|:--|` 分隔行或 `?`/`是否` 判表头，**数据行不豁免**（N12/N13/F04 实测抓）。
- **表头合法但数据行内断言**：`| 笔 | 状态 | 已入账? |` + 分隔行 + `| 1 | 本笔已入账 | 是 |` → 表头 B、数据行 D。
- **拿不准默认 FAIL**：`grep 结果：已入账`（裸完成词在 A 标记之后的新微段内、无主语、无结果数字）→ D；`未验：本笔已入账` → D；无 `r10_scan` 时 C 类不自行豁免、一律 `degraded=True` 判 D（实跑合订本 `no R10 kinds={'B': 3, 'A': 2, 'D': 2}`，有 R10 时 `{'B': 3, 'A': 2, 'C': 2}`）。**拿不准默认 FAIL 只覆盖「命中词表但语境拿不准」**，不覆盖词表外/跨行（§5.4）。
- **词表拆分裂缝**（补强，不放宽）：`本笔已于 §605 入账` 不含字面三词，用 `_SPLIT` 补 D；三真件 `split_hits = 0 / 0 / 0` 实跑。

### 3.4 新误报族探针

`_n13_new_fp_probe.py` 13 条（9 条把 A/B 表面标记粘到真断言上 + 4 条真件对照），实跑 **`反例探针：13/13 符合期望；不符 0`**。已修掉的族：`grep 结果：已生效，可应用母本`（F03，A 标记劫持）、`有没有已入账的？有，本笔已于 §605 入账`（F05）、`本笔已入账 0 命中不得写成未入账`（F09，`0 命中` 反向劫持）、`§2 … / §3 本笔已生效，可应用母本`（F07）。

## 4 正负样本集与回归

### 4.1 正样本 16 条（应当放过，覆盖 A/B/C）

样本定义在 `_n13_regression.py:46-82`。真件逐字 10 条 + 构造 6 条：

| id | 文本要点 | 期望 | 实判 |
|:--|:--|:--:|:--:|
| P01 | 草案 :28 `### 1(c) 有没有已入账的？` | A/B | B |
| P02 | 草案 :275 `一、一页纸总览 … 1(c) 已入账 grep=0 …` | A/B | B |
| P03 | 合订 :54 `## 2 … 已入账 grep 结果` | B | B |
| P04 | 合订 :77 `### 2.2 … 已入账 grep 结果` | B | B |
| P05 | 合订 :79 `**已入账核查实跑命令**：` | A | A |
| P06 | 合订 :87-88 表头 + 分隔行 | B | B |
| P07 | 合订 :338 § 结构枚举截取 | B | B |
| P08 | 合订 :209 `不宣告 N-4 正式绑定已生效` | C | C |
| P09 | 合订 :242 尾段否定分句 | C | C |
| P10 | 草案 :174 同款否定分句 | C | C |
| P11 | 缩进 + `-` + `有没有已追加的？grep … = 0 命中` | A | A |
| P12 | 表头 `已生效?` + 数据行 `否（grep 0 命中）` | A/B | B |
| P13 | `**不得写成「本笔已生效」**；本件只登记。` | C | C |
| P14 | 缩进 + `*` + `已入账 grep 结果：0 逐字命中` | A | A |
| P15 | `### 3 已追加 grep 结果（清单）` | B | B |
| P16 | `§2 上游指纹 + 已入账 grep 结果 / §3 冲突` | B | B |

**放过有样本证明**：`正样本小计：放过 16 / 误拦 0 / 合计 16`。

### 4.2 负样本 26 条（应当抓住，覆盖 D 类）

样本定义在 `_n13_regression.py:85-113`。原 18 条 + 复核 ④ 的 8 条样本外真断言：

| id | 文本 | 覆盖点 |
|:--|:--|:--|
| N01 | `本笔已于 §605 入账。` | 编排方真断言形（拆分裂缝） |
| N02 | `已生效，可应用母本。` | 编排方真断言形 |
| N03 | `本笔已于 §607 入账，第五节另计。` | 被登记笔 + § 定位 |
| N04 | `本节已生效，可应用母本` | 主语=本节 |
| N05 | `该笔已追加至台账尾部。` | 主语=该笔 |
| N06 | `第 5 笔已入账。` | 主语=第 N 笔（带空格） |
| N07 | `不宣告 X 已生效，但 Y 已入账` | ★ 同句混用（任务第二步(c) 点名） |
| N08 | `不宣告 N-4 正式绑定已生效，但本笔已于 §605 入账` | ★ 同句混用 + § 定位 |
| N09–N11 | 缩进 / `-` / `*` 列表符 + 情态修饰 | 行首装饰 |
| N12 | `\| 1 \| §605 \| 本笔已入账 \| 是 \|` | ★ 表格数据行内断言（表头不豁免数据行） |
| N13 | `\| 2 \| §606 \| 该笔已生效，可应用母本 \| 备注入账 \|` | 表格单元格 + 可应用 |
| N14–N17 | 时间副词 / 括注 / 母本 / 台账 | 谓语变体 |
| N18 | `本笔已入账 0 命中不得写成未入账` | A 结果标记劫持反向对照 |
| **N19** | `未验：本笔已入账` | ★ 复核 V1：前置标签不得一键废行级守卫 |
| **N20** | `grep 结果：第 5 笔已入账` | ★ 复核 V2：A 标记 + 带空格主语 |
| **N21** | `§2 清单 / 此笔已入账 / §3 依赖` | ★ 复核 V3：B 目录行内主语断言 |
| **N22** | `未验：§605 已入账` | ★ 复核 V4 |
| **N23** | `grep 结果：此笔已入账` | ★ 复核 V5：非词表主语「此笔」 |
| **N24** | `grep 结果：已入账` | 复核 X1：裸完成词拿不准 → 默认 FAIL |
| **N25** | `未验：第 605 节已入账` | 复核 X2 |
| **N26** | `已入账核查清单：该条已追加` | 复核 X3：A 标签 + 另一微段断言 |

**抓住有样本证明**：`负样本小计：抓住 26 / 漏网 0 / 合计 26`。复核探针重跑：`_n13v_final_probe.py` → `PART 1 正式 5 条漏网 = []`、`PART 1 全部漏网 = []`；`_n13v_negatives.py` → `正式 5 条：抓住 5 / 漏网 0`、`全部漏网 = []`、`N13V_NEW_NEG_ALL_CAUGHT = True`。**判据未放宽**：正样本数量仍 16、真件仍 0 D，只把豁免从整行收窄到微段。

### 4.3 真件 0 命中 D 类 + 旧门禁四条问题逐条重判

命令 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13_regression.py`，输出：

```
LEDGER_BOUND_VOLUME.md bytes=70587 sha256=47bb594b90e1c49c kinds={'B': 3, 'A': 2, 'C': 2} D=0 verdict=PASS(0 D)
_lb_BOUND_VOLUME.md bytes=60272 sha256=7770da46b5c684ad kinds={'B': 2, 'C': 1} D=0 verdict=PASS(0 D)
正样本 0 误拦 = True (16/16)
负样本 0 漏网 = True (26/26)
真件 0 命中 D = True
ALL_PASS = True
```

三真件（含 `LEDGER_APPENDIX_DRAFT.md`）`split_hits = 0 / 0 / 0`、`problems = 0 / 0 / 0`（本会话 `python -I -X utf8 -c "<_split_assert_lines 三件探针>"`）。

**旧门禁四条问题逐条重判（如实）**：把历史 payload `dwfrun-614dbceb…mjs` 的 `GATE_CODE` 逐字重建（写域 `_n13v_hist_gate_replay*.py`），代入三件现盘 SHA 实跑 `python -I -X utf8 D:/…/_n13v_hist_gate_replay.py`：

```
exit = 0 | stdout = {"ok": false, "problems": ["含越权断言 已入账", "含越权断言 已生效"], "bindings": 11}
谓词化门禁 problems = [] | D 类数 = 0
```

只读查 CLI 会话库 `C:/Users/Administrator/.zcode/cli/db/db.sqlite`：`part` 表 `rowid=613246` 记「门禁问题：含越权断言 已入账；含越权断言 已生效」，`rowid=613929` 记「门禁 FAIL 了，两条问题都出在我写的判据上」；`part` 表内 ≥4 条 problems 且含「已入账」的 JSON 数组 = **0**。

| 旧问题 | 现盘可复现 | 谓词化重判 | 结果 |
|:--|:--|:--|:--|
| ① `含越权断言 已入账` | 是 | 7 处 A/B 全放过（合订 :54/:77/:79/:87/:338 + 草案 :28/:275） | **消失** |
| ② `含越权断言 已生效` | 是 | 3 处 C 由 R10 `negation` 豁免（:209/:242/:174） | **消失** |
| ③ 另 2 条（背景称四条） | **否（未验）** | 现盘 0 命中、旧输出未落盘、DB 无 ≥4 条数组 | **不判，不补造条目名** |
| ④ 另 2 条（背景称四条） | **否（未验）** | 同上 | **不判** |

`bindings = 11` 等其余检查项不在本谓词职责内，未改动。

### 4.4 迁移配方与粘贴片段实跑汇总

| 命令（全部 `python -I -X utf8` + 绝对路径） | 输出要点 |
|:--|:--|
| `…/_n13_migration_check.py` | U1 接口形状一致 / U2 改前 FAIL 改后 PASS / U3 降级不静默 PASS / U4 真断言仍抓 / **U5 真删谓词模块后干净 FAIL** → `MIGRATION_ALL_PASS = True` |
| `…/_n13v_migration.py`（复核方，真移文件） | `M1 / M1b / M2` 三条删文件用例全部 `{"ok": false, "problems": [2 条]}`；`M3` 真 ImportError 降级全拦；`N13V_MIGRATION_ALL_PASS = True` |
| `…/_n13_new_fp_probe.py` | `反例探针：13/13 符合期望；不符 0` |
| `…/_n13v_final_probe.py` | 修前 `5 条全 ★PASS（5/5 漏网）`；修后 `正式 5 条漏网 = []`、`全部漏网 = []` |
| `…/_n13v_negatives.py` | 修前 `抓住 4 / 漏网 1`；修后 `抓住 5 / 漏网 0`、补充侦察 `0/10` 漏网 |
| `…/_n13v_independent.py` | 独立实现 34 条对跑，差异仅 P08/P13 两条（复核方自认其独立实现判错，撰写人 34/34 符合期望；第二轮重跑结论不变） |
| `python -I -X utf8 -c "<粘贴片段全量对跑>"` | `pasteable POS 16 / 16 bad= []`、`pasteable NEG 26 / 26 bad= []`、三真件 `D= 0 problems= 0` |
| `…/lead/gate_r9r12_20261109/_g9_gate.py` | `"all_pass": true`，U3 谓词指纹 `02c17e49…/11743 B` |

## 5 与 R9–R12 的关系 / 并入顺序 / 适用边界

### 5.1 ★ 基于源码实读：C 类是否重复、A/B 缺口是否为真

实读 `lead/gate_fp7_20261108/_g7_predicates.py`：

- `:69` `NEG_RE`、`:70` `NEG_WINDOW = 24`、`:71` `CLAUSE_BREAK = "。！？；\n"`、`:72` `SPAN_RE`（≤80 字短引证）、`:76` `DOUBLE_NEG_RE` 十式；
- `:78-111` `r10_context` 四类 `double_neg / negation / quote_mention / assertion`；`:113-130` `r10_scan` 对 `assertion` 报 problem，对 `negation`/`quote_mention` 报 warning，`double_neg` 静默交 R12；`:134-148` `r12_scan`。
- 全文词频实跑（`python -I -X utf8 -c "<源码计数>"`）：`grep / 检索 / 清点 / 核查 / 表头 / 总览 / 问句 / 有没有 / 标题` **均 0**，`目录` 仅 1 次且在注释里 ⇒ **R10 确无 A/B 能力**；R12 只管双重否定，R9 管要素包裹符（`_g9_gate.py:21-22`），R11 管绑定行（`:151-154`）。
- 全文 `r10_scan` 实跑：合订 `{assertion:5, negation:2}`、草案 `{assertion:2, negation:1}`；7 处 A/B 全 `assertion`、3 处 C 全 `negation`。

**结论**：**C 类与 R10 重复（R10 已覆盖），A/B 类缺口为真**。N13 不重写 C 类正则，只消费 `r10_map[(token,pos)]`。**如实登记两点**（复核 ⑥）：

1. 本件仍用自写 `_NEG` / `_QUOTE` / `_line_positive` 在**行层与微段层**重判否定/引证/肯定，且可在 R10 不同意时把命中覆写为 D——这是**有意的 R10 补缝**（补 `CLAUSE_BREAK` 不含逗号、以及「未验：」标签跨窗污染），故「C 类不重做」的措辞偏宽，准确说法是「C 类正则不重做，判定加局部性守卫」。
2. `r13_assertions` 在**无 `r10_scan`** 时对 C 类一律 `degraded=True` 判 D（实跑合订本 `no R10 kinds={'B': 3, 'A': 2, 'D': 2}`）。**交付实为双模块捆绑，不是单文件即可用**；生产用法必须按 §3.2 同时加载 `_g7_predicates.py`。

**R10 没能覆盖的 C 类写法（实跑反例，不重做只登记）**：

| 反例 | R10 | R12 | 结论 |
|:--|:--|:--|:--|
| `不宣告 X 已生效，但 Y 已入账` | 两命中均 `negation`，problems=0 | 0 | 逗号跨句污染；N13 `_CONTRAST` + 行级守卫补判 D |
| `亦非不宣告 N-4 正式绑定已生效` | `negation`（neg_count=2），problems=0 | 0 | 分离型双重否定，`GATE_FALSE_POSITIVE_5_6_7.md:267` 已登记 GV-L 残余；**本方案不修 R10/R12，只登记** |
| `并非不宣告已生效` | `double_neg` | problems=1 | R12 已覆盖 |

### 5.2 与既有 14 类的对应

A/B 属 `GATE_FALSE_POSITIVE_5_6_7.md:53-55` 归纳外的**检索/清单语境**；C 对应第 6/7 类（R10+R12 已消）；D 对应第 12/14 类；R9 覆盖第 5 类、R11 覆盖第 8 类。`GATE_R9R12_REGRESSION.md:207` 记 R10 自指 12 条、`:213` 记残余 6 类（第 1/2/4/9/10/11 类）——本方案不动这些残余类，`GATE_R9R12_REGRESSION.md:207` 的反引号代码跨度自指误报族被继承（§5.4）。

### 5.3 ★ 并入顺序：N13 在 R10 **之前**

**N13(A/B 微段过滤) → R10(C/D 分类) → R12(双重否定补判) → R9/R11**，理由三条：

1. R10 对 A/B 的 7 处一律返回 `assertion` 并直接 `P.append(problem)`（`_g7_predicates.py:123-124`）。若先跑 R10，误报已进 `P`，后加 N13 只能「删 problem」，破坏 `P` 只增不减的既有契约（`_dnv_gate.py:4` `P=[]` 起）。
2. `r13_assertions` 内部已按此顺序写死：先 `_split_lines` / `_line_positive`，再查 `r10[(token,pos)]`，`r12` 覆写，最后补拆分形态；调用链单向、无循环依赖。迁移配方只暴露一个函数调用，调用方无需重排。
3. R12 必须仍在 R10 **之后**：R10 对 `double_neg` 静默（`:123-129`）；`_g9_gate.py:24/:83` 固定顺序 R9→R10→R12→R11 不动。R9/R11 与词表无关，位置任意。

### 5.4 适用边界：判不了的写法如实列

| 边界 | 反例 | 本轮实判 | 说明 |
|:--|:--|:--|:--|
| **跨行断言** | `本笔\n已于 §605 入账` | 漏判 | 逐行扫描接不起主语与谓语 |
| **跨小节语义承接** | `§3 结论：前述已生效。\n§4 本笔可应用母本` | 判不了 | 谓词不读上下文；`§4` 行无完成词 |
| **同义词 / 换写** | `本笔业已录入台账／登记完毕／落账` | 漏判 | 词表只有三完成词 + `_SPLIT` 三动词 |
| **被动式无主语** | `该草案被登记入台账` | 漏判 | `被 + 动词` 无对应形态 |
| **英文完成词** | `This entry has been recorded` | 漏判 | 纯中文正则 |
| **反引号代码跨度自指** | `词表 = ['已入账','已生效']` | 误拦 | `GATE_R9R12_REGRESSION.md:207` 已登记 R10 第 1/4 类自指残余；N13 不修 R10 |
| **分离型双重否定** | `亦非不宣告 N-4 正式绑定已生效` | 漏判 | R10/R12 GV-L 残余（§5.1） |
| **超长引证跨度** | `「…>80 字符…已入账…」` | 依 R10 | `SPAN_RE` 限 ≤80（`:72`） |
| **Markdown 换行拆断** | `已入\n账` | 漏判 | 逐行 `finditer` 不跨行 |
| **表格无分隔行且无问号的表头** | `\| 笔 \| 已入账 \|` + `\| 1 \| 否 \|` | **D（误拦）** | 本会话实跑 `FAIL [('D','R10 assertion')]`；`_header` 要求分隔行或 `?`/`是否`，此形态未纳入豁免，如实登记为**判不了** |

**默认 FAIL 只覆盖「命中了词表但语境拿不准」**，不覆盖「词表外/跨行/跨小节」——后者是「没命中」而非「拿不准」，谓词不会凭空报警。封闭词表 + 逐行微段正则的固有边界，不宣称完备。

## 6 复核回件 + 未改既有件声明 + 未验项

### 6.1 复核 verdict 如实登记

被核对象 SHA256 = 47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70，字节数 = 70587

- **原轮复核 `verdict = partial`**（复核回件 §④ 5 条新负样本 5/5 漏网、§⑦ 真删文件不产出生效 FAIL；①②③⑤⑧ 通过、⑥ 有口径瑕疵）。按任务「refuted 或 partial 标 unconfirmed」：**本轮修订后 verdict = unconfirmed**——两项缺陷已在本会话实跑修复并回归（§4.2 / §4.4），但**未经复核方重签**，不得自升为 confirmed。
- **旧问题逐条回判**：
  - ④ 5 条新负样本 → 修后 `_n13v_final_probe.py` `正式 5 条漏网 = []`、`全部漏网 = []`；`_n13v_negatives.py` `5/5 抓住`、`补充侦察 0/10 漏网`；并已固化进 `_n13_regression.py` 的 N19–N26。**消失**。
  - ⑦ 真删文件 → 修后 `_n13v_migration.py` `M1/M1b/M2 全 PASS`、`N13V_MIGRATION_ALL_PASS = True`，`_n13_migration_check.py` 新增 U5 真删用例 PASS。**消失**。
  - ⑥(1)「C 类不重做」措辞偏宽 → §5.1 已改述为「C 类正则不重做、判定加局部性守卫」。**已登记**。
  - ⑥(2)「无 R10 单独用会误拦 3 处 C」→ §5.1 第 2 点如实登记为**双模块捆绑的适用边界**（设计取舍，未改）。
  - 「改后 5 行」行数口径瑕疵 → §3.2 更正为「5 条语句 / 10 行粘贴块」。**已登记**。
  - ⑤ 旧门禁只复现 2 条、另 2 条未验 → 未改变，仍如实标未验（§4.3）。

### 6.2 未改既有件声明

- **绝对只读、未改一字**：`lead/ledger_bound_20261109/`、`lead/ledger_appendix_20261108/`、`lead/gate_fp7_20261108/`、`lead/gate_r9r12_20261109/`、`.zcode/workflow-runs/` 全部 mjs、`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`。收尾指纹重算（本会话 `python -I -X utf8 -c "<hashlib 七件>"`）与 §2.1 及【编排方指纹】逐位一致；mtime 扫描 `ledger_bound_20261109 / ledger_appendix_20261108 / gate_fp7_20261108 / gate_r9r12_20261109` 近一小时新增或修改文件数 **全 0**（`.zcode/workflow-runs/` 的 3 个近期 mjs 为并发运行的 run 文件，非本会话写入，未改其内容）。
- `lead/r9r12_20261109/_g9_gate.py` 现盘 **MISSING**，未创建、未补造。
- **不 commit / 不 push**：`git -C D:/Project/ra2-campaign-forge log -1 --format="%h %s"` → `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`（本会话实跑）。
- **唯一写域** `lead/gate_n13_20261109/`：`GATE_N13_QUOTED_ASSERTION.md`（本件）、`_n13_predicates.py`（16,649 B）、`_n13_pasteable.py`（8,122 B）、`_n13_regression.py`（14,353 B）、`_n13_migration_check.py`（4,961 B）、`_n13_new_fp_probe.py`（3,423 B），以及复核方先前留下的 `_n13v_*` 探针（本会话只改了 `_n13v_migration.py` 的 `except` 与 `is_file()` 预检，用于复跑 ⑦）。
- **未发现为让门禁通过而放宽判据**：第二轮反而收紧（豁免粒度整行 → 逐 token 微段；负样本 18 → 26；真件仍 0 D；U4/U5 真断言仍抓）。

### 6.3 未验项（不补造）

1. **旧门禁「四条问题」的另 2 条**：现盘 0 命中、旧输出未落盘、DB `part` 表 ≥4 条 problems 且含「已入账」的 JSON 数组 = 0（实跑 `_n13v_hist_gate_replay.py` 与 `_n13v_final_probe.py PART 2`）。**未验**，不补造条目名。
2. **复核方独立实现 P08/P13 两处判错**：复核回件自认归责于其独立实现（不剥引证跨度），未计入本件缺陷；本会话重跑 `_n13v_independent.py` 结论不变。
3. **反引号自指、分离型双重否定、跨行/跨小节/同义词/被动式/英文等**：§5.4 已列为**判不了**，未构造完备证明，不宣称覆盖。
4. **本轮修订的 verdict**：未经复核方重签，标 **unconfirmed**（§6.1）。
