# 接入合并契约（③）+ 机读件计数口径（④）裁决方案

> **只出方案，不改任何件。** 本件落在唯一写域 `lead/merged_contract_20261109/`，前缀 `_mk_`。
> 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；
> 零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；
> 不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。
>
> **复核回件绑定行**（本会话 `python -I -X utf8` + `hashlib` 对原件全字节实算，11/11 与编排方派发值全等，见 `_mk_probe_out.txt` §1）：
>
> 被核对象 SHA256 = 83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75，字节数 = 15723
> 被核对象 SHA256 = 12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106，字节数 = 4821
> 被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958
> 被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481
> 被核对象 SHA256 = 8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367，字节数 = 33762
> 被核对象 SHA256 = bc5eb5d0d13e1fbe8a67451141476c7f077ec49e0d8e9a6bbab34bc569110c44，字节数 = 34299
> 被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
> 被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
>
> 可复核命令与输出：`_mk_probe.py` / `_mk_probe_out.txt`（101 行，EXIT=0）、
> `_mk_build_candidate.py`（构造 ③ 候选副本，compile OK）、`_mk_project.py` / `_mk_project_out.txt`（30 件投影，EXIT=0）。
> 候选副本 `_mk_r11plus_candidate.py` 仅作改后片段的编译/投影验证，**绝不覆盖 `_f2_r11plus.py`**。

---

## 0 边界与术语

- ① = `_f2v_verify9.py` 三形态分支补丁（上轮已设计，`MERGED_MIN_SAFETY_PATCH.md` §3）；
- ② = `_g9_gate.py` `match=True and not path` 缺口补丁（上轮已设计，同件 §4）；
- ③ = 接入点 `_f2_r11plus.py:303-305` 的合并契约（本任务给方案）；
- ④ = 机读件 `_f2_compare_out.json` 的计数口径（本任务给**裁决选项**）。
- ①② 只出设计未落地：本会话实读 `_f2v_verify9.py:24` 仍为 `Path(src.get("verified_path") or src.get("path"))`、
  `_g9_gate.py:160` 仍为 `r11_verdict = "FAIL" if r11_problems else "PASS"`（`_mk_probe_out.txt` §7 与逐件实读）。
- ③ ④ **都不在本会话改动范围内**，本件只给改前改后对照与选项，由模板所有者决定。

**口径分歧（如实登记，不冒充一致）**：上轮 `MERGED_MIN_SAFETY_PATCH.md:292` 说审计最小安全集是「1–3 代码必做 + 5–6 治理必做 = 5 条」（`MERGED_CONSUMER_AUDIT.md:181-188`），同件 `:294` 另给「4 项 + 1 治理」的内部归并。本件不裁这个数字，只按任务书处理 ③④。

---

## 1 第一步：核实 ③ 的现状

### 1(a) 当前 else 分支逐行做了什么

`_f2_r11plus.py:298-306` 实读逐字（`_mk_probe_out.txt` §2；原件 `:298-306`）：

```
298 |             elif t2_spans or t2n_cands or t3_cands:
299 |                 rec["match"] = False
300 |                 rec["tier"] = "T2/T2N/T3"
301 |                 warnings.append("采集到候选锚但均不在盘：%s（R11+/F2，仅警告）"
302 |                                 % ", ".join((t2_spans + t2n_cands + t3_cands)[:4]))
303 |             else:
304 |                 rec["tier"] = None
305 |                 warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
306 |         bindings.append(rec)
```

逐行语义（本任务只关心 `:303-305` 的 `else`）：

| 行 | 动作 | 说明 |
|---:|:--|:--|
| 298-302 | `elif` 分支 | T2/T2N/T3 采到候选但都不在盘 → `match=False`、`tier="T2/T2N/T3"`、一条「仅警告」。**不属本任务接入点**（`MERGED_CONSUMER_AUDIT.md:183` 也只点 `:303-305`） |
| 303 | `else:` | 触发条件 = `path is None`（无 T1）且 `t2_spans/t2n_cands/t3_cands` 三者全空，即四级采集全落空（`_f2_r11plus.py:201,249-253`） |
| 304 | `rec["tier"] = None` | 把证据强度标为「无」。`rec` 的骨架在 `:196-197`：`{"declared", "path"=None, "match"=None, "citation"}`；此分支还带 `:266` 写入的 `tried`（空列表） |
| 305 | `warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")` | 唯一的产出：**一条 warning**。`problems` 不动（不增不减），不调任何模块，不回验、不改 `match` |
| 306 | `bindings.append(rec)` | 收口，返回契约 `(problems, warnings, bindings)`（`:310`） |

即：**当前 else 分支是纯「人工锚定」占位**：`tier=None`、`match` 保持 `None`、`path` 保持 `None`、
`problems` 不变、只加一条 R3-3b warning。它不装载也不调用任何 link 家族模块。

现盘 30 件中该分支走到 **10 条绑定行**（`_mk_probe_out.txt` §6：`plus tier` 分布 `None:10`，
分布在 5 件：`A_RESIDUAL_REFERENCES.md`1、`INTEGRATION_REPORT.md`1、
`_integ_INTEGRATION_REPORT.md`1、`B_EXECUTION_SPEC.md`5、`_n4_SPEC_N4_B2B_MATRIX.md`2）。

### 1(b) link 家族引用计数（独立复核）

命令（`_mk_probe.py` §3，输出 `_mk_probe_out.txt` §3）：
`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mk_probe.py`

| 符号 | 本会话整文件字面计数 | 命中行 | 编排方派发值 | 结论 |
|:--|--:|:--|--:|:--|
| `link_triple` | **0** | — | 0 | 全等 |
| `_re_linked` | **0** | — | 0 | 全等 |
| `samedoc` | **0** | — | 0 | 全等 |
| `verified_path` | **2** | `:238`、`:270` | 0 | **不一致，见下** |
| `recomputed` | 2 | `:237`、`:271` | （未给） | 补充 |

`_mc_AUDIT.md:170` 的 grep 家族 pattern
（`link_triple|_re_linked|samedoc|\bsl_link\b|import .*link|\blink\(`）在本文件命中 **0 行**，
与 `_mc_AUDIT.md:171` 记的 `NO_MATCH` 一致。装载语句只有 `:45-48` 四个标准库 import
与 `:70,72` 的 `spec_from_file_location("_g7_predicates_f2plus", ...)` / `exec_module`
（`_mk_probe_out.txt` §3；`_mc_AUDIT.md:173-174` 同）。

**★ 必须如实指出的口径分歧**：编排方派发的 `linkFamily` 四个键为
`{link_triple:0, _re_linked:0, samedoc:0, verified_path:0}`，但本会话 `hashlib` 复核件
`_f2_r11plus.py` 内 `verified_path` 字面出现 **2 次**，在 `:238`
（`rec.update({"recomputed": sha, "bytes": size, "verified_path": str(hit)})`，T1 命中）
与 `:270`（`"verified_path": verified["path"]`，T2/T2N/T3 any-match-wins 命中）。
`recomputed` 同理 2 次（`:237`、`:271`）。两者都是**本文件自己的单对象回验键**，
不是 link 家族引用。审计 `MERGED_CONSUMER_AUDIT.md:173` 已记「④ `verified_path` 是缺席断言须加限定」，
与本会话实读一致。若派发值 0 意为「link 家族 0 引用」，结论仍成立（三个真 link 符号确实全 0）；
若意为「文件里没有 `verified_path` 字面」，则与 `:238/:270` 冲突。**本件按实读取 2，并标注分歧，不替所有者裁决。**

### 1(c) `link_triple` 返回三元组 `(problems, warnings, rec)` 每一项怎么处置

实跑依据：`_re_linked.py:303-331` 定义 + 本会话对 6 个 fixture 的 `link_triple` 实跑
（`_mk_probe_out.txt` §5）。以 `Ffull_merged/doc.md` 为例，返回 `tuple` 长 3：

| 项 | 实跑值 | 接入时怎么处置 | 依据 |
|:--|:--|:--|:--|
| `problems` | `[]`（6 个 fixture 全 `[]`） | **丢弃 / 断言为 `[]`**，绝不 `problems.extend(...)`，绝不把 warning 升级成 problem | `_re_linked.py:47`、`:174`、`:177-179`、`:305`、`:330`；`_re_NOTES.md:28,68` |
| `warnings` | `list[str]`，merged 为 1 条（含「未做单一对象主张（path=None）」「禁止由 merged 推导任何授权结论」），另可追加 `declared_but_mismatched` 的「同文档联查辅助」条目 | **只并 `warnings`**（`warnings.extend`）；且须遵守 `MERGED_CONSUMER_AUDIT.md:183`「保留原 R3-3b warning 或替换为 merged warning，二选一须显式、不得两者都丢」 | `_re_linked.py:282-289`（merged warning 文本）、`:330-331`；`MERGED_CONSUMER_AUDIT.md:183`；`_mc_AUDIT.md:204` |
| `rec` | merged 时 7 键：`declared / path(None) / match(True) / tier(SAMEDOC_LINK_EQ) / samedoc_link / members / decl_lines`；**不含** `verified_path/recomputed/bytes` | **选择性合并进本分支已有的 `rec`**（骨架见 `:196-197`），不是整条替换：`tier`/`match`/`path`/`samedoc_link`/`members`/`decl_lines` 并入；**不覆盖 `rec["declared"]`**（见下）；**不写单对象三键** | `_re_linked.py:310-313`（骨架）、`:320-329`（merged 分支）、`:306-308`（match 语义） |

**`_re_linked.py:47`「problems 恒为 `[]`」是设计纪律，不是巧合。** 四条独立证据：

1. **声明面**：`:47` docstring「★ 一律 warning 级：任何分支都不产出 problem（problems 恒为空列表，merged 亦然）」；
   `:174` `link()` docstring「problems 恒为 `[]`（联查永不升级 problem）」；`:305` `link_triple` docstring 重复一次。
2. **代码面**：本会话 grep `problems.append|problems.extend|out["problems"]=|["problems"]+`
   在 `_re_linked.py` **命中 0 处**（`_mk_probe_out.txt` §4）；唯一初始化是 `:177` `out = {"scope": ..., "problems": [], ...}`，
   唯一出口是 `:330` `return r["problems"], [r["warning"]] + (...), rec`。即结构上不可能非空。
3. **治理面**：`_re_NOTES.md:28`「problems 恒为 `[]`——merged 仍是 warning 级，不升级 problem」、
   `:68`「联查恒不产 problem，只需把返回 warnings 并入 r11 的 warnings」；
   `R33E_MERGE.md:16` 同；`SAMEDOC_LINK.md:21` 记原版同纪律。
4. **实跑面**：6 个 fixture（unique / merged / multi / zero / invalid_hex / 纯等同词反例）`problems` 全 `[]`（`_mk_probe_out.txt` §5）。

**为什么这条纪律对接入方是硬约束**：`r11_scan_plus` 的 `problems` 直接决定
`_f2_compare.py:58,60` 的 `verdict`（`FAIL if problems else PASS`）与 `_g9_gate.py:160` 的 `r11_verdict`。
若把 merged warning 塞进 `problems`，合法 warning 会被判 FAIL（违反「一律 warning 级」）；
反之若依赖「`problems` 非空才算回验」，merged 恒空 ⇒ 零单一锚定被静默放过（这正是 ② 补的缺口）。

**★ 一个易漏的契约陷阱（本会话实读发现）**：`_re_linked.py:180,185` 把 `out["binding_hex"]` 写成
`binding_hex.strip().lower()`，`link_triple` 的 `rec["declared"]` 取自它（`:310`）。
若接入时整条 `rec = lk_rec` 覆盖，且绑定行 hex 含大写字母，`_f2_compare.py:45-46`
的 `[b["declared"] for b in o_bind] == [b["declared"] for b in n_bind]` 会 `AssertionError`。
现盘 19 条 `declared` 实测全小写（本会话对 `_f2_compare_out.json` 统计 `uppercase-containing = 0`），
故当下不触发，但属**契约级隐患**：改后片段必须显式保留原 `rec["declared"]`，不得用 `lk_rec["declared"]` 覆盖。
本会话候选副本已按此写，30/30 断言投影通过（`_mk_project_out.txt` §A）。

---

## 2 第二步：③ 的合并契约（改前改后 + 论证 + 形态表 + 下游影响）

满足审计 `MERGED_CONSUMER_AUDIT.md:183-185` 与 `_mc_AUDIT.md:202-204` 的五项：
**显式 `tier=SAMEDOC_LINK_EQ`；不写 `verified_path/recomputed/bytes`；`problems` 恒 `[]`；只并 warnings；
`members/decl_lines` 全列**（外加 `:183` 要求的 `samedoc_link`、`path=None`、`match=True`）。

### 2(a) 改前片段（逐字，`_f2_r11plus.py:303-305`）

```python
            else:
                rec["tier"] = None
                warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
```

（同段上下文 `:298-306` 已在 §1(a) 逐字给出。）

### 2(b) 改后片段（候选，逐字）

下面 3 处一起构成 ③；**A/B 是装载前置，C 是接入点本体**。完整可编译件 = 写域
`_mk_r11plus_candidate.py`（`_mk_build_candidate.py` 由原件一次字符串替换生成，
3 个 BEFORE 各 `count=1`、`compile=OK`、原件指纹未变）。

**A. 常量区改前 → 改后**（`_f2_r11plus.py:52-55`）

```python
# 改前
G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743

_g7_cache = None
```

```python
# 改后
G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743

# ---- R3-3e / J4 同文档联查模块（只读原件；指纹护栏同 load_g7 纪律） ----
RE_LINKED_PATH = REPO_ROOT / "lead" / "r33e_merge_20261109" / "_re_linked.py"
RE_SHA256_EXPECTED = "7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52"
RE_BYTES_EXPECTED = 19481

_g7_cache = None
_re_cache = None
```

**B. 装载函数改前 → 改后**（`_f2_r11plus.py:72-77` 处插入；沿用 `:58-74` `load_g7` 的指纹门纪律）

```python
# 改前
    spec.loader.exec_module(mod)
    _g7_cache = mod
    return _g7_cache


# ---- 剥行号后缀（F2-b）----------------------------------------------------
```

```python
# 改后
    spec.loader.exec_module(mod)
    _g7_cache = mod
    return _g7_cache


def load_re():
    """只读加载 _re_linked.py link_triple；先验指纹，失配拒绝运行。结果缓存。"""
    global _re_cache
    if _re_cache is not None:
        return _re_cache
    raw = RE_LINKED_PATH.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != RE_SHA256_EXPECTED or len(raw) != RE_BYTES_EXPECTED:
        raise RuntimeError(
            "联查模块指纹失配：%s = %s/%d ≠ 声明 %s/%d —— 拒绝运行"
            % (RE_LINKED_PATH, sha, len(raw), RE_SHA256_EXPECTED, RE_BYTES_EXPECTED)
        )
    spec = importlib.util.spec_from_file_location("_re_linked_f2plus", RE_LINKED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _re_cache = mod
    return _re_cache


# ---- 剥行号后缀（F2-b）----------------------------------------------------
```

**C. 接入点改前 → 改后**（`_f2_r11plus.py:303-306`）

```python
# 改前（逐字）
            else:
                rec["tier"] = None
                warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
        bindings.append(rec)
```

```python
# 改后（候选，_mk_r11plus_candidate.py，compile OK）
            else:
                # ===== R3-3e / J4 接入点：同文档指纹-路径联查 =====
                # 前置：T1/T2/T2N/T3 全部落空才到此（:298-302 的 elif 不进本分支）。
                # _re_linked.py 只读；load_re() 先验指纹，零真机、零采样代码。
                RE = load_re()
                lk_prob, lk_warn, lk_rec = RE.link_triple(
                    text, doc_dir, declared, bytes_decl, root)
                # 纪律：problems 恒为 []（联查一律 warning 级，不升级 problem）
                #       ⇒ 丢弃 lk_prob，只并 warnings；problems 原样不动。
                assert lk_prob == [], "同文档联查不得产 problem（纪律）"
                # warning 二选一须显式：zero ⇒ lk_warn 内含原 R3-3b 原文；
                # merged / unique / multi ⇒ 用联查自己的结论 warning 替换之。
                # 二者必居其一，绝不双丢。
                warnings.extend(lk_warn)
                # rec 合并：保留 declared/citation/tried/alt 等原有键，
                # ★ 不覆盖 rec["declared"]（link_triple 的 binding_hex 已 lower()，
                #   直接覆盖会破坏 _f2_compare.py:45-46 的 declared 序列断言）。
                rec["tier"] = lk_rec.get("tier")
                rec["match"] = lk_rec.get("match")
                rec["path"] = lk_rec.get("path")
                rec["samedoc_link"] = lk_rec.get("samedoc_link")
                if lk_rec.get("tier") == "SAMEDOC_LINK_EQ":
                    # merged：副本群，全列 members / decl_lines（纪律三）
                    rec["members"] = lk_rec["members"]
                    rec["decl_lines"] = lk_rec["decl_lines"]
                    # ★ 故意不写 verified_path / recomputed / bytes：
                    #   纪律一「不做单一对象主张」——merged 无单一锚对象，
                    #   match=True 仅指声明 hex 与全体成员重算逐位一致。
                elif lk_rec.get("tier") == "SAMEDOC_LINK" and \
                        lk_rec.get("path") is not None:
                    # unique：单一对象回验成立，link_triple 已给单对象三键
                    rec["verified_path"] = lk_rec["verified_path"]
                    rec["recomputed"] = lk_rec["recomputed"]
                    rec["bytes"] = lk_rec["bytes"]
                # multi / zero / invalid_hex：path=None、match=None，
                #   不写任何单对象三键、不写 members/decl_lines。
        bindings.append(rec)
```

**warning 二选一的落实方式（如实说明）**：`_re_linked.py:298` 的 zero warning 文本里
已含「绑定行缺显式路径，需人工锚定（R11/R3-3b）」原句（前缀完全一致），
故 `warnings.extend(lk_warn)` 在 zero 分支等价于「保留原 warning（并追加联查说明）」；
unique/merged/multi 分支则用联查结论 warning **替换**之。候选实测：30 件 warnings 总数
`11 → 14`，变化 5 件，`A_RESIDUAL_REFERENCES.md` 1→3、`_integ_INTEGRATION_REPORT.md` 1→2、
`INTEGRATION_REPORT.md` 1→1（改文本）、`B_EXECUTION_SPEC.md` 5→5（改文本）、
`_n4_SPEC_N4_B2B_MATRIX.md` 2→2（改文本），逐件明细见本会话实跑输出。
**若所有者要求「zero 分支逐字不变」，须改为按 verdict 显式分支**（`if lk_rec["samedoc_link"]["verdict"]=="zero": 保留原 :305 一行 else: extend(lk_warn)`），本件给选项不替决定。

### 2(c) 为什么「不写 `verified_path/recomputed/bytes`」是纪律而不是遗漏

- **纪律一的原文**：`_re_linked.py:26-29`【merged 三纪律】第 1 条
  「path=None 不做单一对象主张：link_triple 的 merged rec 恒不写 path / verified_path /
  recomputed / bytes 等单对象字段（rec["path"] 保持 None）；link() 输出的 out["reverify"]
  恒为 None。merged 是「副本群」形态，不指向任何单一对象。」
- **代码证据**：`:310-313` 造骨架 `path=None`；`:314-319` 只有 `unique` 分支才写
  `verified_path/recomputed/bytes`；`:320-329` 的 merged 分支**只**写
  `tier/match/members/decl_lines`。`:254-256` J4 块注释、`:322-325` 再重复一遍。
- **语义证据**：`:306-308` 明写 `match=True` 仅指「声明 hex 与全体成员现盘重算逐位一致」，
  **不指向任何单一对象**。若写了 `verified_path` 或 `recomputed`，等于把一个「群体的哈希」
  伪装成「某一个文件的哈希」；消费方（如 `_f2v_verify9.py:24-29`）会据此 `Path(...).read_bytes()`
  并比 `src["bytes"]`，从而**凭空制造一个单一锚对象**——正是纪律二
  （禁止由 merged 推导授权结论，`:30-33`、`RULING_D25:26`、
  `_integ_INTEGRATION_REPORT.md:59` 实读在案）要防的。
- **`members` 是这三键的合法替代**：`:34-36` 纪律三要求逐成员全列
  `{path, sha, bytes}`；本会话实跑 merged rec 的 `members` 为 2 条
  （`qc151_trip.isolated.py` / `qc151_trip.candidate_lf.py`，各 412759 B，sha 全 64 位，
  `_mk_project_out.txt` §B）。所以「没有单对象三键」不是信息缺失，而是**信息在别处且更完整**。
- **实跑佐证**：本会话 `link_triple` merged 输出 `has verified_path/recomputed/bytes = False/False/False`、
  `samedoc_link.reverify = None`（`_mk_probe_out.txt` §5）；`MERGED_MIN_SAFETY_PATCH.md:74-77`
  A3 亦记「MISSING KEY … True」三行，并把它当作缺陷 1 的成因（不是遗漏，是设计）。

结论：这三键的缺席是**可断言的正向契约**（`assert "verified_path" not in rec` 应进回归），
不是待补的字段；任何「顺手补上」都会把 merged 降级成 unique 语义，破坏 J4 三条件与授权纪律。

### 2(d) 接入后 `rec` 形态对照表（unique / merged / multi）

依据：本会话 `link_triple` 6 fixture 实跑（`_mk_probe_out.txt` §5）+
30 件投影的 merged rec（`_mk_project_out.txt` §B）。「接入后 rec」= `:196-197` 骨架
（`citation`、`tried` 等）叠加 2(b)-C 的合并结果。

| 键 | **unique**（`Pu_unique_with_decl`） | **merged**（`Ffull_merged` / 30 件投影） | **multi**（`Fp1_decl_covers_one` / `Fd_equiv_words`） | 附：zero / invalid_hex |
|:--|:--|:--|:--|:--|
| `declared` | 原绑定行 hex（**保留原值，不采用 `lk_rec` 的 lower 版**） | 同左 | 同左 | 同左 |
| `citation` | 原值（`:163,197`） | 原值 | 原值 | 原值 |
| `tried` | 原值（`:266`，本分支为 `[]`） | 原值 `[]` | 原值 `[]` | 原值 `[]` |
| `tier` | `"SAMEDOC_LINK"` | **`"SAMEDOC_LINK_EQ"`** | `"SAMEDOC_LINK"` | `None` |
| `match` | `True` | **`True`**（仅指全体成员逐位一致） | `None` | `None` |
| `path` | 单一现盘路径（str） | **`None`** | `None` | `None` |
| `verified_path` | 单一现盘路径（str） | **不写（键缺席）** | 不写（键缺席） | 不写 |
| `recomputed` | 64 hex | **不写（键缺席）** | 不写 | 不写 |
| `bytes` | int | **不写（键缺席）** | 不写 | 不写 |
| `members` | 不写 | **全列**（每条 `{path, sha, bytes}`，无截断） | 不写 | 不写 |
| `decl_lines` | 不写 | **全列**（如 `[4]` / 30 件投影 `[13]`） | 不写 | 不写 |
| `samedoc_link` | `link()` 的完整 out（`verdict=unique`，`reverify` 非空） | 完整 out（`verdict=merged`，含 `eq.members/decl_hits`，`reverify=None`） | 完整 out（`verdict=multi`，`reverify=None`） | `verdict=zero`，`reverify=None` |
| `problems`（函数级） | 不变 | **不变（恒不增）** | 不变 | 不变 |
| `warnings`（函数级） | 联查结论 warning（替换 R3-3b） | merged warning + 可能 1 条「同文档联查辅助」（`declared_but_mismatched`） | 联查多命中 warning | 保留 R3-3b 原文 + 联查零命中说明 + 辅助 |

**哪些为 `None`**：merged 的 `path=None`、`samedoc_link.reverify=None`；
multi 的 `path=None/match=None/reverify=None`；zero 的 `tier=None` 且 `path=None/match=None`。
**哪些键缺席**（不是 `None`，是 `not in rec`）：merged / multi / zero 的
`verified_path/recomputed/bytes/members/decl_lines`（除 merged 有 `members/decl_lines`）。
这个区别对消费者是致命的：`.get("bytes","-")` 返回 `"-"`（`_f2w_extract.py:33`），
而 `src["bytes"]` 直接 `KeyError`（`_f2v_verify9.py:29`）。

### 2(e) 这一改动会改变哪些下游行为（逐个列，不只说「6 件」）

先给**本会话实跑的量化投影**（`_mk_project.py` / `_mk_project_out.txt` §A，30 件全量，非假设）：
只做 ③、`_f2_compare.py` 与 ④ 完全不动、用候选副本替换 `r11_scan_plus` 重跑 30 件：

- 变化 **5/30 件、10/19 条绑定行**；新 tier 分布 `{None:1, SAMEDOC_LINK:8, SAMEDOC_LINK_EQ:1}`；
- `totals` 投影 `BEFORE = {bindings:19, orig_path:1, plus_path:9, orig_match:0, plus_match:9, orig_problems:24, plus_problems:23}`
  → `AFTER = {…, plus_path:17, plus_match:18, …}`（**`plus_path` 9→17、`plus_match` 9→18**，
  `bindings/orig_*/plus_problems` 不变）；
- `warnings` 总数 `11 → 14`；`plus_problems` 恒 `23`（纪律成立）；
- `_f2_compare.py:44-50` 三条断言投影 **30/30 通过**（`declared` 序列不漂移、原 T1 path 不丢）；
- 30 件里真实产出 **1 条 merged rec**：`lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md`
  （`tier=SAMEDOC_LINK_EQ`、`path=None`、`match=True`、`members_n=2`、`decl_lines=[13]`）。

> ★ 上轮 `MERGED_MIN_SAFETY_PATCH.md:280` 的 `totals={"plus_path":0,"plus_match":1}` 是
> **单条 merged rec 的手工喂入**（U1），本件是 30 件真实接入投影。两者口径不同、不互相冒充：
> 单条 `(0,1)` 说明「merged 使 plus_match 增 1 而 plus_path 不增」，30 件 `(9→17, 9→18)`
> 说明另有 8 条 unique 同时抬高两个计数。计数口径裁决必须同时覆盖**这两类变化**。

**逐件下游清单**（「读 JSON」4 件 / 「直调 plus」7 件 / 门禁 1 件 / 报告与指纹锁 3 类）：

| # | 消费者 | 实读位置 | 读什么 | ③ 接入后的行为 |
|--:|:--|:--|:--|:--|
| 1 | `_f2_compare.py`（写者 + :67/69 计数 + :73-74 打印 + :100 落盘） | `:35-36,66-71,73-74,100-101` | 聚合 `totals`；`plus_path`/`plus_match` | **`totals` 变 `(17,18)`**；`:73-74` 控制台汇总变；`:100` 写出的 `_f2_compare_out.json` 全件字节变；`results[].plus.bindings` 里 10 条 rec 形状变（新增 `samedoc_link/members/decl_lines` 键）。**这就是 ④ 的落点** |
| 2 | `_f2w_checks.py`（读 JSON） | `:14,26-38` | `results[].plus.bindings` 的 `match`/`recomputed`/`bytes` | merged 条 `sha_ok=False`（`(b.get("recomputed") or "").lower()` 为空），`n_ok` 少计 1；unique 8 条因候选写了 `recomputed` 反而变「逐字一致」→ 报告数字从 9 变 17，**语义混杂**（`_mk_project_out.txt` C2） |
| 3 | `_f2w_extract.py`（读 JSON） | `:12-13,26-33` | `verified_path/recomputed/bytes/path/match/tier` | merged 条 `verified='' recomputed='' bytes='-'` 静默空白（C3）；unique 8 条出现新 `tier=SAMEDOC_LINK` 与现盘重算值；19 条逐条表整体变 |
| 4 | `_f2w_pass.py`（读 JSON） | `:6-7,10-24` | `orig/plus` 的 `problems/warnings/verdict` 与 `match` 计数 | `plus match` 由 9 变 18；`warnings` 计数 11→14；`R11 PASS` 件数不变（`problems` 恒 23）；merged 被计入「已回验」统计（C4） |
| 5 | `_f2w_final.py`（读 JSON） | `:30-34` | 只数 `len(orig/plus["warnings"])` | **正常但数字变**：`orig_warnings` 不变、`plus_warnings` 11→14；不读单对象键，不崩（C10） |
| 6 | `_f2v_verify9.py`（直调） | `:19-36` | `verified_path/path/bytes` 直接下标 | **崩**（① 未落地时）：`Path(None)` → `TypeError`，绕过则 `src["bytes"]` → `KeyError`（C1，`_mcv_empirical.py` trial A/A2/A3 亦证） |
| 7 | `_f2_selftest.py`（直调） | `:105-111`（另 `:64,75,117,126,130,141` 调 plus） | `:110` `nb[0].get("verified_path","").endswith("_f2_r11plus.py")` | S4 断言返回 `False`、断言失败（C8）；且 30 件自扫用例会随新 tier 变化 |
| 8 | `_f2v_final.py`（直调） | `:24,50,51-59` | `collected=sum(path)`、`match` 计数、开放 `tiers` dict | `collected=9→17`、`match=9→18`、`tiers` 新增 `SAMEDOC_LINK_EQ`/`SAMEDOC_LINK`；开放 dict 不崩但统计混杂（C6） |
| 9 | `_f2v_run.py`（直调 + 自己写第二件 `totals`） | `:35,48-52,60-72` | `plus_paths/plus_match/plus_tiers` 列表 + `_f2v_run_out.json` 的 9 键 `totals` | `plus_paths` 出现 `None`、`plus_match` 出现 `True`；**`_f2v_run_out.json` 是第二件带 `totals` 的机读件**（`{orig_collected,plus_collected,orig_match,plus_match,…,plus_warnings}`），同样会漂移 → ④ 的影响面不止 `_f2_compare_out.json`（C7） |
| 10 | `_f2w_dogfood.py`（直调） | `:20-33` | `collected`/`match`/开放 `tiers` | 同 #8；`plus warnings` 打印变（C6） |
| 11 | `_f2v_edge.py`（直调） | `:36,43,48,77` | `.get("tier")/match/suffix_stripped` 打印 + problems/warnings | **正常**：不假设单对象 path，用 `.get`；但其 fixture 用例的期望输出文本会随 warning 变化（`MERGED_CONSUMER_AUDIT.md:130` B11 判「正常」） |
| 12 | `_g9_gate.py`（门禁，当前**不可达**） | `:155-167` | `g7.r11_scan`（原版）→ `reverified/n_match/r11_verdict` | 当下 merged 不流入（`:155` 实读为 `g7.r11_scan`，`_mk_probe_out.txt` §7）；**若将来改接 plus**：`reverified=17`/`match_true=18`/`problems=[]` ⇒ 旧 `:160` 仍 PASS，1 条零单一锚定 merged 被静默放过（C9，② 未落地时） |
| 13 | `_f2_repro.py` / `_f2v_context.py` / `_g9v_verify.py` 等 7 件原版 `r11_scan` 组 | `_f2_repro.py:46`、`_f2v_context.py:24`、`_mc_AUDIT.md:186` | 原版 rec | **不受 ③ 影响**（不调 plus），但 `_f2w_extract.py:12` 把 `_f2_repro_out.json` 与 compare JSON `zip` 对齐，行数/顺序不变故不崩 |
| 14 | 3 件指纹锁脚本 | `lead/f2d_rootcause_20261109/_f2d_fpcheck.py:11`、`_f2dw_fpcheck.py:21-22`、`_f2dv_fpcheck.py:26-27` | 硬编码 `148ea8d6…/44958` | 一旦 `_f2_compare.py:100` 重写 JSON（无论选甲/乙/丙），三件全部 `MISMATCH/DRIFT`；`R11_F2_COVERAGE_FIX.md:47` 与 `_f2_F2_PATCH_REPORT.md:140-141` 的指纹登记同样失效 |
| 15 | 报告/台账层 | `R11_F2_COVERAGE_FIX.md:47,92`、`_f2_F2_PATCH_REPORT.md:79,140-141`、`F2D_ROOT_CAUSE.md:41` | 引用 9/9/19/24/23 等数字与指纹 | 数字与指纹引用需同步登记；两件台账本任务绝对只读（`PENDING_DECISIONS.md`、`GOAL_THREE_TARGETS_20261018.md` 实读无 merged/计数口径裁决条目） |

---

## 3 第三步：核实 ④ 的现状

### 3(a) `totals` 现在有哪几个计数、各自语义

`_f2_compare.py:35-36` 定义 7 键，`:65-71` 逐件累加，`:73-74` 打印，`:100` 落盘。
本会话实读 `_f2_compare_out.json` 的 `totals` 并**由 `results[]` 独立重算，7/7 全等**
（`_mk_probe_out.txt` §6 `RECOMPUTED_EQUALS_STORED = True`）：

| 键 | 现值 | 聚合表达式（代码行） | 语义 |
|:--|--:|:--|:--|
| `bindings` | 19 | `:65` `+= len(o_bind)` | 30 件清单里绑定行总条数（原版/增强版条数受 `:44` 断言约束必等） |
| `orig_path` | 1 | `:66` `sum(1 for b in o_bind if b["path"])` | 原版 r11_scan 采到显式路径的绑定行数 |
| `plus_path` | 9 | `:67` `sum(1 for b in n_bind if b.get("path"))` | 增强版采到**单一 path** 的绑定行数（T1/T2/T2N/T3 命中） |
| `orig_match` | 0 | `:68` `sum(... b["match"] is True)` | 原版判 `match=True` 的绑定行数 |
| `plus_match` | 9 | `:69` `sum(... b.get("match") is True)` | 增强版判 `match=True` 的绑定行数 |
| `orig_problems` | 24 | `:70` `+= len(o_prob)` | 原版 problem 总数 |
| `plus_problems` | 23 | `:71` `+= len(n_prob)` | 增强版 problem 总数 |

**重要语义事实（本会话实跑）**：现盘 `plus_match` 的 9 行与 `plus_path` 的 9 行
**集合完全相同**（`set equal = True`，tier 分布 `T1/T2/T2N/T3`）。也就是说，
**在当前产物里 `plus_match == plus_path` 是巧合性恒等**，代码里没有任何一处表达
「match 是否等于单一回验」。这正是审计 `MERGED_CONSUMER_AUDIT.md:184` 说的
「B3/B6/B7/B8/B9/B10 的 `match`/`path` 计数口径须显式区分」的根源。
③ 接入后这个恒等立刻被打破：投影 `plus_path=17 / plus_match=18`（差 1 = 那条 merged）。

### 3(b) 这组计数能不能区分「merged 匹配（无单一对象）」与「unique 单一回验」？

**不能。** 缺一个维度：**「匹配的性质 / 单对象主张是否成立」**。

- `plus_match` 只数 `match is True`，而 `_re_linked.py:306-308` 明确 merged 的 `match=True`
  「仅指声明 hex 与全体成员现盘重算逐位一致、不指向任何单一对象」。两种完全不同的事实
  被压进同一个计数。
- `plus_path` 只数 `b.get("path")` 真值，无法表达「有 `members` 但无 `path`」这第三种形态；
  于是 merged 表现为 `plus_match +1` 而 `plus_path +0`，与「失配但也有 0 path」在 totals 里不可分辨。
- 现盘 7 键里没有 `tier` 维度、没有 `members` 维度、没有 `merged` 维度，也没有
  `plus_match_no_path` / `plus_merged` 之类补键。
- `results[].plus.bindings` 里虽可逐条看到 `tier`（**:82** 的控制台表打印了 `tier`），
  但 `totals` 是**无条件的扁平累加**，且 4 个 JSON 读者（§2(e) #2-#5）实读**都不触碰 `totals`**
  （`_mk_probe_out.txt` §7 `totals=False` 四件），它们各自从 `results[]` 重算自己的口径 —— 所以
  「改 totals」本身**并不会自动修好报告层**；④ 必须按 `MERGED_MIN_SAFETY_PATCH.md:304`
  的复核 ⑥ 结论，**JSON 读者与直调者两路分别裁决**，不能按单点收敛。

缺的维度可表述为三态之一：`{single_path（单一回验）, merged_eq（副本群匹配）, none（无锚）}`，
或更保守地保留现键、只补一个「`match=True` 且 `path` 为空」的计数。

### 3(c) `results[]` 每条的 `orig`/`plus` 子结构里有没有能承载 merged 信息的字段？

实读（`_mk_probe_out.txt` §6）：

- 顶层 `result_keys = ["file","other_predicates_fail","orig","plus","orig_overall","plus_overall"]`；
- `orig` / `plus` 各 4 键：`["problems","warnings","bindings","verdict"]`；
- `plus.bindings` 全量键集（19 条并集）= `alt, bytes, citation, declared, match, path,
  recomputed, suffix_stripped, tier, tried, verified_path`；
  **含 merged 字段 = `{members:False, decl_lines:False, samedoc_link:False, SAMEDOC_LINK_EQ:False}`**。

结论：**结构上「能装」，语义上「现在没有」**。

- `bindings` 是自由 dict 列表（`_f2_compare.py:59` 直接把 `n_bind` 塞进去，不做键过滤），
  所以 ③ 一旦接入，`members/decl_lines/samedoc_link` 与 `tier="SAMEDOC_LINK_EQ"`
  **会自动流进 JSON，无需改 schema**——本会话 30 件投影确认 `_f2_compare.py:44-50`
  断言 30/30 仍过。
- 但 `orig`/`plus` 这 4 个子键里**没有任何汇总/分类字段**：没有 `merged_count`、
  没有 `tier_counts`、没有 `match_kind`。`verdict` 只由 `problems` 推出（`:60`），
  因此 merged（`problems=[]`）在 `plus.verdict` 里被记成 `"PASS"`，与真正单一回验的 PASS 不可区分。
- `warnings` 是 `list[str]`，merged warning 文本里带「未做单一对象主张」「禁止由 merged 推导任何授权结论」，
  是**唯一**能人工辨认 merged 的载体，但不可机读、不可计数。
- 若 ④ 选「在 `results[]` 里加分类字段」，属于**结构扩展**（新键），与「只改 `totals`」
  的兼容性不同，见 §4 各方案。

---

## 4 第四步：④ 的口径裁决方案（★ 此项须模板所有者裁决）

**本件只给选项与后果，不替所有者决定。** 三个方案都默认「③ 已按 §2 接入」。
共同前提（不属裁决、但必须随方案落地）：`MERGED_CONSUMER_AUDIT.md:184` 要求
B3/B6/B7/B8/B9/B10 显式区分「merged 匹配 ≠ 单一回验」，且 `MERGED_MIN_SAFETY_PATCH.md:304`
复核 ⑥ 已证「两路消费面须分别裁决」——**任何只改 `totals` 的方案都不覆盖直调者那一路**，
这一点在三个方案里都必须额外声明。

### 4(a) 三个方案

#### 方案甲：`totals` 新增键，既有键语义不变（additive）

改动形态（`_f2_compare.py:35-36` 与 `:65-71`）：

```python
# 改前
tot = {"bindings": 0, "orig_path": 0, "plus_path": 0, "orig_match": 0,
       "plus_match": 0, "orig_problems": 0, "plus_problems": 0}
...
tot["plus_match"] += sum(1 for b in n_bind if b.get("match") is True)
```

```python
# 改后（甲）
tot = {"bindings": 0, "orig_path": 0, "plus_path": 0, "orig_match": 0,
       "plus_match": 0, "orig_problems": 0, "plus_problems": 0,
       "plus_merged_match": 0, "plus_match_no_path": 0,
       "plus_samedoc_unique": 0}          # 键名仅示例，由所有者定
...
tot["plus_match"] += sum(1 for b in n_bind if b.get("match") is True)
tot["plus_merged_match"] += sum(1 for b in n_bind
                                if b.get("tier") == "SAMEDOC_LINK_EQ")
tot["plus_match_no_path"] += sum(1 for b in n_bind
                                 if b.get("match") is True and not b.get("path"))
tot["plus_samedoc_unique"] += sum(1 for b in n_bind
                                  if b.get("tier") == "SAMEDOC_LINK"
                                  and b.get("path"))
```

- 既有 7 键**逐字不重定义**：`plus_match` 仍含 merged（现状语义 = 「判 match=True 的条数」），
  `plus_path` 仍只数单一 path。
- 30 件投影（未实跑该方案，按候选 rec 推算）：`plus_path=17, plus_match=18,
  plus_merged_match=1, plus_match_no_path=1, plus_samedoc_unique=8`；
  `17 + 1 = 18` 成立，形成可机读的恒等式断言。
- 优点：改动最小、旧键零重定义、恒等式可回归。
- 缺点：**旧键的误导性保留**——只读 `plus_match` 的旧消费者仍把 merged 当单一回验；
  `plus_match_no_path` 与 `plus_merged_match` 有重叠需文档说明；报告层（#2-#5、#8-#10）
  仍需逐件改才能不一致。

#### 方案乙：`totals` 拆三态，既有键废弃或重定义（breaking）

```python
# 改后（乙）
tot = {"bindings": 0, "orig_path": 0, "orig_match": 0,
       "orig_problems": 0, "plus_problems": 0,
       "plus_by_kind": {"single_path": 0, "merged_eq": 0, "none": 0},
       "plus_match_total": 0}
...
for b in n_bind:
    if b.get("tier") == "SAMEDOC_LINK_EQ":
        tot["plus_by_kind"]["merged_eq"] += 1
    elif b.get("path") and b.get("match") is True:
        tot["plus_by_kind"]["single_path"] += 1
    else:
        tot["plus_by_kind"]["none"] += 1
```

- `plus_path` / `plus_match` **废弃**（或重定义为 `single_path` / `single_path+merged_eq`，
  两者择一必须写进判定书）。
- 优点：语义最干净，三态互斥且完备，`match=True` 不再被误当单一回验；
  直接满足 `MERGED_CONSUMER_AUDIT.md:184`。
- 缺点：**破坏面最大**：任何按名取 `plus_path`/`plus_match` 的旧代码/报告/`_f2v_run_out.json`
  口径都要跟着改；`_f2_compare.py:67,69` 两个表达式被删；历史 JSON 与新 JSON 不可互读（见 4(c)）。

#### 方案丙（推荐候选）：`totals` 保留 7 键 + 新增正交 `tier` 分组 + `schema_version`（additive + 自描述）

```python
# 改后（丙）
tot = {"bindings": 0, "orig_path": 0, "plus_path": 0, "orig_match": 0,
       "plus_match": 0, "orig_problems": 0, "plus_problems": 0,
       "plus_tier_counts": {},                 # 开放 dict：tier -> 条数
       "plus_match_by_kind": {"single_path": 0, "merged_eq": 0},
       "schema_version": 2}
...
for b in n_bind:
    t = b.get("tier") or "NONE"
    tot["plus_tier_counts"][t] = tot["plus_tier_counts"].get(t, 0) + 1
    if b.get("match") is True:
        k = "merged_eq" if b.get("tier") == "SAMEDOC_LINK_EQ" else "single_path"
        tot["plus_match_by_kind"][k] += 1
```

同时**在 `results[].plus` 加一个机读分类键**（如 `"match_kind": "single_path"|"merged_eq"|"none"`
或 `"merged_count": n`），让 4 个 JSON 读者不必靠 warning 文本人肉分辨；
并在文件顶层加 `"schema_version": 2` 与 `"counting_policy": "<裁决书编号>"`。

- 30 件投影（按候选 rec 推算）：`plus_tier_counts = {T1:1,T2:5,T2N:2,T3:1,
  SAMEDOC_LINK:8, SAMEDOC_LINK_EQ:1, NONE:1}`；`plus_match_by_kind={single_path:17, merged_eq:1}`；
  与 `plus_path=17`、`plus_match=18` 自洽。
- 优点：既有 7 键零重定义（旧读者不破）、新增键正交可回归、开放 `tier` dict 不会因未来新 tier 再改 schema、
  `schema_version` 让新旧 JSON 可判别、`results[]` 的分类键直接服务报告层两路。
- 缺点：改动面比甲大；`results[]` 加键属结构扩展，需明确「旧代码忽略未知键」的兼容约定。

### 4(b) 每个方案对既有消费者的影响（谁读 `totals`？谁读 `plus_path/plus_match`？会不会破）

**先给本会话查清的事实（`_mk_probe_out.txt` §7 + 全仓 grep）**：

- **读 `_f2_compare_out.json` 的 `totals` 的件 = 0 件**。写者只有 `_f2_compare.py:100`；
  4 个读者 `_f2w_checks.py:14`、`_f2w_extract.py:13`、`_f2w_pass.py:6`、`_f2w_final.py:31`
  实读**都只取 `cmp_["results"]`**，四件源码里**不出现 `totals` 字样**
  （`_mk_probe_out.txt` §7 `totals=False` 四件）。全仓另两处 `d["totals"]`
  （`goal3_mimosa_tools_review_20261022/_summarize.py:14`、
  `qc161_u0400_trip/_census_d07_gate36.py:86`）读的是**别的 JSON**（mimosa findings），与本机读件无关。
  `_ms_tight.py:201,210` 的 `written["totals"]` 是上轮自造单条 merged 的探针，非生产读者。
- **读 `plus_path`/`plus_match` 语义的件 = 两类**：
  (i) `_f2_compare.py:67,69` 自己（写者，也 `:73-74` 打印）；
  (ii) **不读 totals、但按同口径从 `results[]` 重算**的 8 件：
  `_f2w_pass.py:17`、`_f2w_checks.py:28-29`、`_f2w_extract.py:31-33`、
  `_f2v_final.py:54`、`_f2w_dogfood.py:26`、`_f2v_run.py:62,64`、
  `_f2_compare.py:67,69`、`_f2v_verify9.py:21`（`:21` 是 `match is True` 门禁）；
  另有 `_f2v_run.py:71` 写第二件 `totals`（9 键，键名不同：`plus_collected/plus_match/…`）。
- **按名硬编码 `_f2_compare_out.json` 指纹的件 = 3 件**（`f2d_rootcause_20261109/_f2d_fpcheck.py:11`、
  `_f2dw_fpcheck.py:21-22`、`_f2dv_fpcheck.py:26-27`，值 `148ea8d6…/44958`），
  加 2 份报告登记（`R11_F2_COVERAGE_FIX.md:47`、`_f2_F2_PATCH_REPORT.md:140-141`、
  `F2D_ROOT_CAUSE.md:41`）。

| 消费者 | 甲 | 乙 | 丙 |
|:--|:--|:--|:--|
| 4 个 JSON 读者（#2-#5） | **不破**（不读 totals、`.get` 容忍新键）；但报告数字仍按 `results[]` 旧口径混杂 → **静默误读不修** | **不破**（同上，因不读 totals）；若它们将来改读 totals 才会破 | **不破**；且新 `results[].plus.match_kind` 让它们**有机读依据**去修 |
| `_f2_compare.py:67,69,73-74,100` | 改累加（+3 键）；`:73-74` 打印变 | 删/重定义 2 键，改动最大 | 改累加（+3 键 + 开放 dict）；`:73-74` 打印变 |
| `_f2v_run.py` 的 `_f2v_run_out.json` | 键名不同，**不受影响但口径不一致**（第二件机读件仍 `plus_collected=17/plus_match=18` 无 merged 维度）；须单独裁决 | 同左；若统一三态须同改 | 同左；建议同步加 `plus_match_by_kind` |
| 8 件直调/重算者（#6-#11、#2-#4） | **不破，但静默误读仍在**（这正是 §5(b) 传导链）；须按 `MERGED_CONSUMER_AUDIT.md:184` 逐件加分支 | 不破（它们不读 totals），但语义仍混杂 → 逐件加分支同样不可省 | 不破；分类键可直接被它们引用 |
| `_g9_gate.py`（当前不可达） | 无关（不读 JSON） | 无关 | 无关；② 独立处理 `match=True and not path` |
| 3 件指纹锁脚本 + 3 份报告登记 | **破**：JSON 字节变 → `MISMATCH/DRIFT` | **破**（同上，且更严重） | **破**（同上） |
| 台账两件（绝对只读） | 需登记裁决，不改 | 需登记裁决，不改 | 需登记裁决，不改 |

**共同结论**：三个方案**没有任何一个**会因「totals 键变化」直接弄崩 4 个 JSON 读者
（它们根本不读 totals）；三者**都会**弄崩 3 件指纹锁（因为 `_f2_compare.py:100` 必然重写整件）。
差别只在「旧键误导性是否消除」与「报告层是否有可机读的分类依据」。

### 4(c) 每个方案的机读件向后兼容性

| | 旧 json 被新代码读 | 新 json 被旧代码读 |
|:--|:--|:--|
| **甲** | **能读**：新代码若只 `tot.get("plus_merged_match", 0)` 则旧 JSON 缺键取默认 0；但若新代码**断言键存在**则旧 JSON 失败（须显式降级分支） | **能读**：4 个旧读者不读 totals、忽略未知键；`results[]` 结构不变 ⇒ 全部不崩。只是旧读者不知道 merged 存在，继续静默误读 |
| **乙** | **不能读（除非写兼容层）**：旧 JSON 无 `plus_by_kind`，且 `plus_path/plus_match` 被废弃/重定义，新旧同名不同义 ⇒ 最危险（静默错值，不报错） | **不能读（若旧代码按名取键）**：`KeyError: 'plus_match'`；本会话查实 4 个读者不取，故实盘不崩，但任何未来按名取的读者会崩。`results[]` 未变 ⇒ 旧读者仍可跑 |
| **丙** | **能读**：`schema_version` 缺省视为 1，新代码走旧口径；`plus_tier_counts`/`plus_match_by_kind` 用 `.get(..., {})` 兜底 | **能读**：既有 7 键逐字保留、语义不变；新增键被旧代码忽略；`results[].plus` 加的新键被 `.get` 读者忽略 ⇒ 全部不崩 |

补充：**旧 json → 新代码**在三个方案里都还面临 `_f2_compare.py:100` 重写整件后的指纹锁问题
（4(b)），这与 schema 兼容是两件事，须分别登记。

### 4(d) 推荐与理由（★ 此项须模板所有者裁决）

**推荐方案丙**，理由（全部基于本会话实读/实跑）：

1. 既有 7 键零重定义 ⇒ 3 件指纹锁之外**零代码破坏**（4(b) 表）；
2. `plus_tier_counts` 是开放 dict，不会因未来 `SAMEDOC_LINK_EQ` 之外的新 tier 再改 schema
   （`_mc_AUDIT.md:202`「现盘无封闭白名单」、审计六条第 1 条要求 tier 显式可扩展）；
3. `plus_match_by_kind` 给出 `single_path` / `merged_eq` 互斥二态 + 恒等式
   `plus_path == plus_match_by_kind["single_path"]`、`plus_match == single_path + merged_eq`，
   可写成回归断言，直接回答 3(b) 缺的维度；
4. `schema_version` + `counting_policy` 让 4(c) 两向兼容可机读判别，避免乙那种
   「同名不同义」的静默错值；
5. `results[].plus` 的分类键是**唯一能同时服务两路消费面**的落点
   （`MERGED_MIN_SAFETY_PATCH.md:304` 复核 ⑥：JSON 读者与直调者须分别裁决），
   甲/乙只动 totals，报告层 8 件仍无依据可修。

**但推荐不等于决定**：三项须所有者裁决的点本件不拍板 ——
(a) `plus_match` 是否允许继续含 merged（甲/丙 含、乙 不含）；
(b) `plus_path`/`plus_match` 是否废弃（乙）；
(c) 键名、`schema_version` 起点、`results[]` 加哪个分类键、`_f2v_run_out.json` 是否同步、
3 件指纹锁与报告登记如何重基线。
**本项明确标注「此项须模板所有者裁决」。**

---

## 5 第五步：③④ 与 ①② 的先后依赖

### 5(a) 只做 ①②（已设计），当前状态是否合规？

**合规，但功能未上线。** 依据：

- `R33E_MERGE.md:17`「本报告不自行上线」、`SAMEDOC_LINK.md:22`「是否接入由编排方裁决」、
  `MERGED_CONSUMER_AUDIT.md:193`「暂不接入是合规现状」；
- 本会话实读 `_f2_r11plus.py:303-305` 仍 `tier=None` + R3-3b warning，link 家族 3 符号全 0
  （`_mk_probe_out.txt` §2-3）；`_g9_gate.py:155` 仍 `g7.r11_scan`，`_f2v_verify9.py:24`
  仍单对象 `Path(...)`。生产链不产、不收 merged（审计 §3.5 severity=medium 的前提）。
- ①② 是「未来接入面」的**预防性补丁**：按 `MERGED_MIN_SAFETY_PATCH.md:14`，当下不崩、不放行；
  实跑 30 件回归 0/30 漂移（同件 `:238`）、反例 `COUNTEREXAMPLE_OK`（`:261`）。
- **但**：`MERGED_CONSUMER_AUDIT.md:181` 的最小安全集是 5 条，`MERGED_MIN_SAFETY_PATCH.md:292`
  明示「两处不是接入的最小安全集」；只做 ①② ⇒ ③ 空置 ⇒ merged 根本没接进来
  （同件 `:306`），④ 未裁 ⇒ 机读件口径依旧是「`plus_match == plus_path` 的巧合恒等」。
  另外 `MERGED_CONSUMER_AUDIT.md:190-194` 的操作性缺口（离线提示模式无 owner / 触发 SOP / sink）
  与第 5/6 条治理项（run 快照、判定书登记）也仍缺。

### 5(b) 加做 ③ 但没 ④，会发生什么（具体传导链）

**本会话 30 件实跑投影**（`_mk_project_out.txt` §A-C，非假设）：

```
③ 接入（候选副本，_f2_compare.py / ④ 完全不动）
  ↓ 30 件中 10 条 else 绑定行走联查：8 unique + 1 merged + 1 zero
  ↓ 5/30 件的 plus.bindings 形状变（新 tier / members / decl_lines / samedoc_link）
  ↓ problems 恒 23（纪律）→ plus.verdict 全不变 → 门禁与 verdict 层看不出异常
  ↓ warnings 11→14；_f2_compare.py:44-50 断言 30/30 仍过（不报警）
  ↓ _f2_compare.py:67/69 照旧无条件累加 → totals: plus_path 9→17, plus_match 9→18
  ↓ _f2_compare.py:100 重写 _f2_compare_out.json（整件字节变）
     ├─ 3 件指纹锁 (_f2d_fpcheck/_f2dw_fpcheck/_f2dv_fpcheck) → MISMATCH/DRIFT
     ├─ 报告登记 (R11_F2_COVERAGE_FIX.md:47 / _f2_F2_PATCH_REPORT.md:140-141 / F2D_ROOT_CAUSE.md:41) 指纹失效
     └─ 4 个 JSON 读者（不读 totals，只取 results[]）：
         ├─ _f2w_checks.py:29   merged 条 sha_ok=False（合法 match=True 被记成逐字不一致）→ n_ok 少计 1
         ├─ _f2w_extract.py:26-33 merged 条 verified='' recomputed='' bytes='-' → 19 条逐条表静默空白
         ├─ _f2w_pass.py:17     plus match 9→18，merged 混入「已回验」统计
         └─ _f2w_final.py:31-33 plus_warnings 11→14（正常，但数字变）
  ↓ 直调者一路（不经 JSON，④ 改 totals 完全够不着）：
     ├─ _f2v_verify9.py:24/29  → TypeError / KeyError（① 未落地时）
     ├─ _f2_selftest.py:110    → S4 断言 False
     ├─ _f2v_final.py:54-58 / _f2w_dogfood.py:25-30 → collected=17 match=18 tiers 新增两类
     ├─ _f2v_run.py:48-52,71   → plus_paths=[...,None] plus_match=[...,True]，且 _f2v_run_out.json 的 9 键 totals 同步漂移
     └─ _f2v_edge.py           → 正常（.get 打印）
  ↓ 门禁（若将来改接 plus，② 未落地时）：reverified=17 match_true=18 problems=[] ⇒ 旧 :160 PASS
  ⇒ 1 条「零单一对象锚定」的 merged 被静默计成已回验；报告层两路同时静默错；
    totals 里 plus_match(18) ≠ plus_path(17) 却无任何键解释这 1 的差额。
```

这正是 `MERGED_MIN_SAFETY_PATCH.md:307`「只修 1+2+3 不修 4：JSON 读者与直调者两路报告仍静默错」
与 `:280-285` U1-U6 传导链；本件把它从「单条手工喂入」升级为 **30 件真实投影**并补出
unique 8 条带来的 `(9→17, 9→18)` 与 `_f2v_run_out.json` 第二机读件。

### 5(c) 四项全做的落地顺序与每步验证

依 `MERGED_MIN_SAFETY_PATCH.md:310-322` 的接入前置条件 + 本任务 ③④ 的裁决性质，
顺序为「先裁决、再修消费面、最后才动接入点代码」：

| 序 | 做什么 | 为什么 | 每步怎么验证（本会话已跑 / 未验如实标注） |
|--:|:--|:--|:--|
| 0 | **④ 口径裁决 + 接入与否裁决**（不改代码）：所有者定甲/乙/丙、定 `plus_match` 语义、定键名/schema_version、定 `_f2v_run_out.json` 是否同步、定 3 件指纹锁重基线方式；台账登记对 `SAMEDOC_LINK.md:20` ★4 的显式修订与 owner/SOP | ④ 是口径裁决不是实现细节；`MERGED_CONSUMER_AUDIT.md:190-194` 要求先补 owner/触发 SOP；两件台账绝对只读只登记 | 判定书成文；`PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md` 指纹复核（本会话已算 11/11 全等，**未改**）；**本步本会话未做，未验** |
| 1 | ① `_f2v_verify9.py` 三形态分支 | 唯一实证崩点；不先修则下游全量回放必崩 | 上轮已实跑：30 件 `checked 9` / `MISMATCH=0`、C3 七例全 OK、compile OK（`MERGED_MIN_SAFETY_PATCH.md:188,315`）；本会话**未复跑该补丁**（只复核原件 `:24` 仍在），标未验 |
| 2 | ② `_g9_gate.py` `match=True and not path` 缺口（与 1 同批） | 静默放行；`match=True` 无单一 path 不得默认 PASS | 上轮已实跑：`0/30` 漂移、top/R11 keys 全同、self_test 全 True、`COUNTEREXAMPLE_OK`（同件 `:238,261,316`）；本会话**未复跑**，标未验 |
| 3 | **消费面两路适配**（`MERGED_CONSUMER_AUDIT.md:184` B2/B3/B5/B6/B7/B8/B9/B10）：JSON 读者 4 件 + 直调者 7 件，统一约定 `tier=="SAMEDOC_LINK_EQ"` 走 `rec["members"]`，不取 `path/verified_path/bytes` | ④ 的裁决只有落到这两路才生效（复核 ⑥） | 逐件喂本会话投影的那条 merged rec（`_mk_project_out.txt` §B）断言零 TypeError / 零 KeyError / 无误读计数；**本会话只跑了 10 个表达式（§C），全量 11 件回放未做、未验** |
| 4 | **④ 落地**：按 0 的裁决改 `_f2_compare.py:35-71,100`（及 `_f2v_run.py:25-72` 若裁决同步），重基线 3 件指纹锁与 3 份报告登记 | 让机读件能区分「merged 匹配」与「unique 单一回验」 | 恒等式断言：`plus_path == plus_match_by_kind["single_path"]`、`plus_match == single_path+merged_eq`（丙）；旧 json 读新代码 / 新 json 读旧代码双向回放；`declared` 序列 30/30 不漂移（`_f2_compare.py:45-46`）；**未验** |
| 5 | **③ 落地**：按 §2(b) 改 `_f2_r11plus.py`（A/B/C 三处），`_re_linked.py` 保持只读 | 前 4 步都是为它准备消费面；**最后才动代码** | 本会话已做候选副本编译与 30 件投影：`BEFORE_C count=1`、`compile=OK`、30 件 `asserts 30/30`、`warnings 11→14`、`plus_problems=23`、`totals (9,9)→(17,18)`、merged rec 7 键形状（`_mk_build_candidate.py` / `_mk_project_out.txt`）；**正式端到端联调、7 件形状断言回归（`_re_j4_cases.py` 19/19 等，`MERGED_CONSUMER_AUDIT.md:197` 标未验）本会话未做，未验** |
| 6 | 门禁契约回归 + run 快照 + 判定书登记 | ② 只在「改接 plus」时生效；merged 是联查时刻快照（TOCTOU 同限） | 每次 merged 落 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`；`_g9_gate.py:157-158` 若改接 plus 须重裁 `reverified`/`n_match`；**未验** |
| 7 | 指纹护栏收尾 | ③ 会改 `_f2_r11plus.py`（接入方重算登记），只读件与两件台账不得动 | 前后各算一次 `hashlib.sha256`：本会话 11/11 全等基线（`_mk_probe_out.txt` §1）、只读域 `-newermt` 新增 `.pyc` = 0（本会话实跑）、`git log -1` 未变（本会话未跑，标未验） |

---

## 6 未改任何件声明 + 未验项

- 本会话**未改** `_f2_r11plus.py`、`_f2_compare.py`、`_f2_compare_out.json` 及任何既有件；
  只读域 `lead/r11_f2_fix_20261109/`、`lead/r33e_merge_20261109/`、`lead/gate_r9r12_20261109/`、
  `lead/merged_safety_20261109/`、`lead/merged_consumer_audit_20261109/`、两件台账全部未改
  （11 件指纹 `ALL_ELEVEN_MATCH = True`，`_mk_probe_out.txt` §1；只读域 `.pyc` 新增 = 0，本会话 `find -newermt` 实跑）。
- 写域 `lead/merged_contract_20261109/` 内新建 6 件：`_mk_probe.py`、`_mk_probe_out.txt`、
  `_mk_build_candidate.py`、`_mk_r11plus_candidate.py`（改后片段的编译/投影副本，**非原件**）、
  `_mk_project.py`、`_mk_project_out.txt`、本件 `_mk_CONTRACT_DESIGN.md`。
- 零真机、零采样代码；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

**未验项（如实标注，不以局部实跑冒充）**：

1. ③ 正式落地后端到端联调（`_f2_r11plus.py:303-305` 现盘仍空置）；本件只跑写域候选副本。
2. ①② 两处补丁本会话未复跑（只复核原件仍在）；上轮回归结果沿用其记载。
3. 7 件形状断言回归（`_re_j4_cases.py` 19/19 等）——`MERGED_CONSUMER_AUDIT.md:197` 明写「本会话未重跑，标未验」，本会话同样未跑。
4. 11 件下游消费者全量回放（本会话只跑 10 个表达式 / §C）；
5. ④ 三种方案均未落地、均未跑真实新旧 JSON 双向兼容回放（4(c) 为基于源码实读的结构推断，标「推算」）；
6. 门禁真正改接 plus 后的契约回归；候选 v1 的 `merged members=None` 补 SKIP 后的回归；
7. `_f2_compare.py:100` 重写后 3 件指纹锁的重基线、`_f2v_run_out.json` 是否同步裁决；
8. 离线提示模式的 owner / SOP / 触发条件、run 快照落盘、判定书/台账登记；
9. `git log -1` 未变未在本会话复跑。

**口径分歧未替所有者裁决的三处**：(i) 编排方 `linkFamily.verified_path=0` vs 本会话实读 2（§1(b)）；
(ii) 最小安全集「5 条」vs「4 项+1 治理」（§0）；(iii) ④ 的甲/乙/丙三方案取舍（§4(d)，须模板所有者裁决）。
