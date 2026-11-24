# MERGED_MERGE_CONTRACT.md — 接入合并契约（③）+ 机读件计数口径（④）方案件

> **本件只出方案，不落地任何改动。** ③（接入点 `lead/r11_f2_fix_20261109/_f2_r11plus.py:303-305` 的合并契约）
> 与 ④（机读件 `lead/r11_f2_fix_20261109/_f2_compare_out.json` 的计数口径）均属**模板所有者裁决范围**：
> ④ 尤其是「口径分歧属于需要裁决的事项，不是可以自行拍板的实现细节」，本件只给选项、给后果、给推荐，**不替所有者决定**。
> 铁律遵循：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码
> （无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；绝对只读五个只读域与两件台账；
> 唯一写域 = `lead/merged_contract_20261109/`；不 commit、不 push；Python 一律 `python -I -X utf8`（部分加 `-B`）
> + 绝对路径；指纹用 `hashlib`。本会话**绝不改** `_f2_r11plus.py`、`_f2_compare.py`、`_f2_compare_out.json` 或任何既有件；
> 改动全部以「改前改后逐字对照」给出。
>
> **编排方材料**：本任务的【编排方指纹】【接入点与机读件】【方案】【复核】【交付】五段全部为派发输入，本件据此展开并逐项复核。
> **上轮方案件**：`lead/merged_contract_20261109/_mk_CONTRACT_DESIGN.md`（56237 B，本会话实算 sha256=a968a17d096b49ab0b8e5941ff1bfbb57eeae68da727820c4cc8807cfa112432）、
> 复核输出 `_mkv_fp_out.txt`、`_mkv_consumers_out.txt`、`_mkv_edge_out.txt` 为既有只读输入，本会话实读、不修改。

---

## 1 目的与边界

**目的**：交付一份可被所有者逐项裁决的**合并契约 / 计数口径方案件**，含 ① 改前改后逐字片段；② 计数口径 ≥2 方案对照；
③ 逐个消费者影响面；④ ③④ 与 ①② 的依赖顺序；⑤ 复核回件 verdict 与未改/未验声明。

**边界（逐条）**：

| 项 | 界定 | 依据 |
|:--|:--|:--|
| 只出方案不落地 | 本写域产出 `.md` 与 4 个 `_mm_*` 探针；`_mk_r11plus_candidate.py` 是上轮写域内的**改后候选副本**（编译 OK、非原件），本会话只装载它做对跑，绝不覆盖 `_f2_r11plus.py` | 本任务【铁律】；`_mk_build_candidate.py:2-7` |
| ③④ 属裁决范围 | ④ 的 `plus_match` 是否含 merged、`plus_path`/`plus_match` 是否废弃、键名/schema_version/`results[]` 分类键/`_f2v_run_out.json` 是否同步、指纹锁重基线，**全部标注「须所有者裁决」**；本件通篇只给候选与选项、不作拍板式概括（同类复核的禁用词 grep 命中 0，见 §4(d)） | 本任务【铁律】★ 机读件口径分歧；`_mk_CONTRACT_DESIGN.md:456,458,623-628` |
| ①② 不在本会话改动 | ① = `_f2v_verify9.py` 三形态分支补丁、② = `_g9_gate.py` `match=True and not path` 缺口补丁，上轮只出设计未落地；本会话实读 `_f2v_verify9.py:24` 仍 `Path(src.get("verified_path") or src.get("path"))`、`_g9_gate.py:160` 仍 `r11_verdict = "FAIL" if r11_problems else "PASS"` | 本会话 `grep -n 'Path(src.get\|r11_verdict = "FAIL" if r11_problems' ...`（见 §6 命令表）；`_mk_CONTRACT_DESIGN.md:27-33` |
| 只读域 | `lead/r11_f2_fix_20261109/`、`lead/r33e_merge_20261109/`、`lead/gate_r9r12_20261109/`、`lead/merged_safety_20261109/`、`lead/merged_consumer_audit_20261109/`、两件台账，一律不得修改/追加/覆盖 | 本任务【铁律】★ 绝对只读 |
| 引用口径 | 每条结论追到「实跑命令+输出」或「文件:行」；未跑到、拿不到的写「未验」，不补造 | 本任务 Standard |

**术语**：`unique` = 同文档联查唯一命中（单一对象回验）；`merged` = J4 等价类（副本群，`tier=SAMEDOC_LINK_EQ`）；
`multi` = ≥2 命中但未满足 J4 三条件（放弃采集）；`zero` / `invalid_hex` = 无命中 / hex 非法。
`link_triple` 三态指 `unique / multi(含 merged 改判) / zero` 的判定族；④ 的**三态**指计数维度
`{single_path（单一回验）, merged_eq（副本群匹配）, none（无锚）}`（§3(c)、§4(a)）。

---

## 2 上游指纹（十一件）+ ③ 现状 + ④ 现状

### 2.1 十一件上游指纹（本会话实算）

命令（EXIT=0，输出 `_mm_fp_out.txt`，24 行）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mm_fp.py > D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mm_fp_out.txt
```

`_mm_fp.py` 用 `hashlib.sha256(open(p,"rb").read()).hexdigest()` 对 11 件全字节实算，`ALL_MATCH = True COUNT = 11`，
与【编排方指纹】11 项全等；`_mkv_fp_out.txt:2-13` 另为上轮复核件同口径 11 行 `MATCH` + `ALL_MATCH = True COUNT = 11`（本会话实读）。
逐件严格格式绑定行（格式：`被核对象 SHA256 = <64hex>，字节数 = <n>`，中间无路径/括号/星号/反引号/空格）：

被核对象 SHA256 = 83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75，字节数 = 15723
被核对象 SHA256 = 12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106，字节数 = 4821
被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958
被核对象 SHA256 = 23c5eebb77b43e9e187be6b4736fe1f0b3f5d8eb7f46a9ee2f8af1bbbce53514，字节数 = 2189
被核对象 SHA256 = 1eb22164c78330e825d053f665934e9ef1e4eba14e2b101c884de68a91aad701，字节数 = 1564
被核对象 SHA256 = 625704697e412c30a278c616cf8be594b8b870a2734df2219aa0607aa74a19bd，字节数 = 8579
被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481
被核对象 SHA256 = 8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367，字节数 = 33762
被核对象 SHA256 = bc5eb5d0d13e1fbe8a67451141476c7f077ec49e0d8e9a6bbab34bc569110c44，字节数 = 34299
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

> 件序对应：`_f2_r11plus.py` / `_f2_compare.py` / `_f2_compare_out.json` / `_f2w_checks.py` / `_f2w_extract.py` /
> `_f2_selftest.py` / `_re_linked.py` / `_mc_AUDIT.md` / `_ms_DESIGN.md` / `lead/PENDING_DECISIONS.md` /
> `lead/GOAL_THREE_TARGETS_20261018.md`（逐件对应关系见 `_mm_fp_out.txt` 的 `MATCH` 行）。

### 2.2 ③ 现状：else 分支逐行（`_f2_r11plus.py:298-306` 实读）

本会话 `Read` 原件全文，`:298-306` 逐字（`_mk_probe_out.txt:16-24` 同，本会话实读该输出文件）：

```python
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

- 触发 `:303-305` 的条件 = `path is None`（无 T1，`:201`）且 `t2_spans/t2n_cands/t3_cands` 三者全空
  （四级采集 `:164-194`、`:249-253` 全落空；`:298-302` 的 `elif` 未进）。
- `rec` 骨架在 `:196-197`：`{"declared": declared, "path": path(None), "match": None, "citation": citation}`，
  本分支另带 `:266` 写入的 `tried`（空列表）。`:304` 把 `tier` 置 `None`；`:305` 是**唯一产出**：一条 R3-3b warning；
  **problems 不动、不调任何模块、不回验、不改 `match`**；`:306` 收口，`:310` 返回 `(problems, warnings, bindings)`。
- 现盘 30 件中此分支走 **10 条绑定行**：`_mk_probe_out.txt:77-78` 实记 `plus tier 分布 ={'T2N':2, None:10, 'T3':1, 'T2':5, 'T1':1}`、
  `tier=None（:303-305 else 分支）条数 = 10`；`_mk_CONTRACT_DESIGN.md:70-72` 记分布在 5 件。

### 2.3 ③ 现状：link 家族计数（独立复核 + 口径分歧如实登记）

命令（本会话实跑，输出 `_mm_probe_out.txt` §PROB 与 `_mkv_consumers_out.txt` §H 可互证）：
上轮 `python -I -X utf8 .../_mk_probe.py` 的 `_mk_probe_out.txt:27-34` 给出整文件字面计数：

| 符号 | 原件 `_f2_r11plus.py` 计数 | 命中行 | 编排方 `linkFamily` | 结论 |
|:--|--:|:--|--:|:--|
| `link_triple` | **0** | — | 0 | 全等 |
| `_re_linked` | **0** | — | 0 | 全等 |
| `samedoc` | **0** | — | 0 | 全等 |
| `verified_path` | **2** | `:238`、`:270` | 0 | **不一致，见下** |
| `recomputed` | 2 | `:237`、`:271` | （未给） | 补充 |

`_mc_AUDIT.md:170` 的正则族（`link_triple|_re_linked|samedoc|\bsl_link\b|import .*link|\blink\(`）
命中 **0 行**（`_mk_probe_out.txt:32`）；装载语句只有 `:45-48` 四个标准库 import 与
`:70` `spec_from_file_location("_g7_predicates_f2plus", ...)` / `:72` `exec_module`（`:34` 列出）。

> **★ 口径分歧（如实登记，不替所有者裁决）**：【接入点与机读件】派发 `linkFamily.verified_path = 0`，
> 但本会话 `Read` 原件 `:238`（`rec.update({"recomputed": sha, "bytes": size, "verified_path": str(hit)})`，T1 命中）
> 与 `:270`（`"verified_path": verified["path"]`，T2/T2N/T3 any-match-wins 命中）确有 2 次字面。
> 二者都是**本文件自有的单对象回验键**，不是 link 家族引用；`MERGED_CONSUMER_AUDIT.md:80` 亦记
> 「`verified_path` 是缺席断言须加限定」。若派发值 0 意为「link 家族 0 引用」，结论成立（三个真 link 符号全 0）；
> 若意为「文件里无该字面」，则与 `:238/:270` 冲突。**本件按实读取 2，标注分歧，不替所有者裁决。**

### 2.4 ④ 现状：`totals` 语义（`_f2_compare.py:35-36,65-71,73-74,100-101`）

本会话 `Read _f2_compare.py` 全文与 `_f2_compare_out.json`（经 `_mm_probe.py` 解析）。命令：

```
python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mm_probe.py > .../\_mm_probe_out.txt
```

输出 §CMP：`stored = {"bindings":19,"orig_match":0,"orig_path":1,"orig_problems":24,"plus_match":9,"plus_path":9,"plus_problems":23}`、
`recomputed =`（同上）、`EQUALS = True`、`plus_path_set == plus_match_set : True`、
`plus_path tier分布 = ['T1','T2','T2N','T3']`。即 **7 键与 `results[]` 独立重算 7/7 全等**
（`_mk_probe_out.txt:73-74`、`_mkv_consumers_out.txt:159-165` 同，本会话实读）。

| 键 | 现值 | 聚合表达式（代码行） | 语义 |
|:--|--:|:--|:--|
| `bindings` | 19 | `:65` `+= len(o_bind)` | 30 件清单绑定行总条数（`:44` 断言原/增必等） |
| `orig_path` | 1 | `:66` `sum(1 for b in o_bind if b["path"])` | 原版 `r11_scan` 采到显式路径的绑定行数 |
| `plus_path` | 9 | `:67` `sum(1 for b in n_bind if b.get("path"))` | 增强版采到**单一 path** 的绑定行数（T1/T2/T2N/T3） |
| `orig_match` | 0 | `:68` `sum(... b["match"] is True)` | 原版判 `match=True` 的条数 |
| `plus_match` | 9 | `:69` `sum(... b.get("match") is True)` | 增强版判 `match=True` 的条数 |
| `orig_problems` | 24 | `:70` `+= len(o_prob)` | 原版 problem 总数 |
| `plus_problems` | 23 | `:71` `+= len(n_prob)` | 增强版 problem 总数 |

`:73-74` 打印、`:100-101` `OUT.write_text(json.dumps({"totals": tot, "results": results}, ...))` 落盘整件。

**能否区分 merged / unique？——不能。** 缺一个维度：**「匹配的性质 / 单对象主张是否成立」**。

- `:69` 只数 `match is True`，而 `_re_linked.py:306-308` 明确 merged 的 `match=True` 仅指
  「声明 hex 与全体成员现盘重算逐位一致」、**不指向任何单一对象**；两种事实被压进同一计数。
- `:67` 只数 `b.get("path")` 真值，无法表达「有 `members` 但无 `path`」这第三态；merged 表现为
  `plus_match +1` 而 `plus_path +0`，与「失配但也有 0 path」在 totals 里不可分辨。
- 现盘 `plus_match` 的 9 行与 `plus_path` 的 9 行**集合完全相同**（`EQUALS`/`set equal = True`，
  tier 同为 `T1/T2/T2N/T3`）——这是**巧合性恒等**，代码里没有任何一处表达「match = 单一回验」。
  `MERGED_MIN_SAFETY_PATCH.md:280` 的 `totals={"plus_path":0,"plus_match":1}`（U1 单条手工喂入）
  与本会话 30 件投影 `(9,9)→(17,18)`（§5(b)）口径不同、不互相冒充。

**`results[]` schema（实读 `_mm_probe_out.txt` §CMP）**：
`result_keys = ['file','orig','orig_overall','other_predicates_fail','plus','plus_overall']`；
`plus_keys = ['bindings','problems','verdict','warnings']`（**4 键，无汇总/分类字段**）；
`plus.bindings 全量键集 = ['alt','bytes','citation','declared','match','path','recomputed','suffix_stripped','tier','tried','verified_path']`；
`含 merged 字段 = {'members': False, 'decl_lines': False, 'samedoc_link': False}`。
`bindings` 是自由 dict 列表（`:59` 直接塞 `n_bind`，不过滤键）——**结构上「能装」，语义上「现在没有」**；
`verdict` 只由 `problems` 推出（`:60`），故 merged（`problems=[]`）在 `plus.verdict` 里被记成 `"PASS"`。
warning 文本里「未做单一对象主张 / 禁止由 merged 推导任何授权结论」（`_re_linked.py:282-289`）
是唯一人工线索，**不可机读、不可计数**。第二件带 `totals` 的机读件 =
`lead/r11_f2_fix_20261109/_f2v_run_out.json`（`_mm_probe_out.txt` §RUN：9 键
`{"bindings":19,"orig_collected":1,"orig_match":0,"orig_problems":24,"orig_warnings":18,"plus_collected":9,"plus_match":9,"plus_problems":23,"plus_warnings":11}`），
由 `_f2v_run.py:25,60-72` 写出，键名不同、口径同形 —— ④ 的影响面不止 `_f2_compare_out.json`。

---

## 3 接入合并契约（③）：改前改后逐字 + 五项要求 + 三形态 rec + 下游行为变化

### 3(a) 逐字改前改后（三处一起构成 ③；A/B 为只读装载前置，C 为接入点本体）

完整可编译副本 = 写域 `_mk_r11plus_candidate.py`（`_mk_build_candidate.py:117-128` 由原件一次字符串替换生成；
本会话实跑 `BEFORE_C count = 1`、`CANDIDATE_COMPILE=OK`，输出见 §6 命令表）。**逐字片段如下，绝不写回原件。**

**A. 常量区（`_f2_r11plus.py:52-55`）**

```python
# 改前（逐字）
G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743

_g7_cache = None
```

```python
# 改后（候选逐字）
G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743

# ---- R3-3e / J4 同文档联查模块（只读原件；指纹护栏同 load_g7 纪律） ----
RE_LINKED_PATH = REPO_ROOT / "lead" / "r33e_merge_20261109" / "_re_linked.py"
RE_SHA256_EXPECTED = "7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52"
RE_BYTES_EXPECTED = 19481

_g7_cache = None
_re_cache = None
```

**B. 装载函数（`_f2_r11plus.py:72-77` 处插入；沿用 `:58-74 load_g7` 的 hashlib 指纹门 + `spec_from_file_location` 只读装载）**

```python
# 改前（逐字）
    spec.loader.exec_module(mod)
    _g7_cache = mod
    return _g7_cache


# ---- 剥行号后缀（F2-b）----------------------------------------------------
```

```python
# 改后（候选逐字）
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

**C. 接入点本体（`_f2_r11plus.py:303-306`）—— 改前 / 改后逐字**

```python
# 改前（逐字，原件 :303-306）
            else:
                rec["tier"] = None
                warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
        bindings.append(rec)
```

```python
# 改后（候选逐字，_mk_r11plus_candidate.py:328-364；本会话 compile OK）
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

> **warning 二选一（如实说明）**：`_re_linked.py:298` 的 zero warning 文本前缀已含 R3-3b 原句，
> 故 `warnings.extend(lk_warn)` 在 zero 分支等价于「保留原 warning 并追加联查说明」；unique/merged/multi
> 用联查结论 warning 替换之。若所有者要求 zero 分支**逐字不变**，须改为按 `samedoc_link["verdict"]`
> 显式分支（`zero` 保留 `:305` 一行、其余 `extend(lk_warn)`）——**本件给选项不替决定**。
> 契约级陷阱：`_re_linked.py:180,185` 把 `binding_hex` 写成 `lower()`，`link_triple` 的 `rec["declared"]`
> 取自它（`:310`）；若整条 `rec = lk_rec` 覆盖且绑定 hex 含大写，会破 `_f2_compare.py:45-46` 的
> `declared` 序列断言。现盘 19 条 `declared` 实测全小写（`_mk_CONTRACT_DESIGN.md:135-136`），当下不触发，
> 但改后片段必须**显式保留原 `rec["declared"]`**（上面已如此写）。

### 3(b) 五项要求逐条对应（`MERGED_CONSUMER_AUDIT.md:183-185`、`_mc_AUDIT.md:202-207`）

| # | 要求 | 改后片段落实点 | 实证 |
|--:|:--|:--|:--|
| 1 | 显式 `tier=SAMEDOC_LINK_EQ` | `rec["tier"] = lk_rec.get("tier")`；`_re_linked.py:311-312,326` 映射 | 30 件投影产出 1 条 `tier='SAMEDOC_LINK_EQ'`（`_mm_project_out.txt` §B） |
| 2 | **不写** `verified_path/recomputed/bytes` | 只有 `elif ... "SAMEDOC_LINK" and path is not None`（unique）才写三键；merged 分支注释「★ 故意不写」 | `_mk_r11plus_candidate.py:349-361` 实读；`_mm_project_out.txt` §B `missing single-obj keys = {'verified_path': True, 'recomputed': True, 'bytes': True}` |
| 3 | `problems` 恒 `[]` | `assert lk_prob == [], "同文档联查不得产 problem（纪律）"`；**丢弃** `lk_prob`，绝无 `problems.extend` | `_mk_r11plus_candidate.py:337`；`_re_linked.py:47,174,177,305,330`；本会话 `_mm_probe_out.txt` §PROB `write-statements count = 0 []`、`:177` 唯一初始化、`:330` 唯一出口 |
| 4 | 只并 warnings | `warnings.extend(lk_warn)`；zero 含原 R3-3b 原句，其余用联查结论替换，二选一显式 | `_re_linked.py:282-289,298,330-331`；`MERGED_CONSUMER_AUDIT.md:183` |
| 5 | `members/decl_lines` **全列**（+ `samedoc_link`、`path=None`、`match=True`） | merged 分支 `rec["members"]=lk_rec["members"]`、`rec["decl_lines"]=...`；`rec["path"]=lk_rec.get("path")` 恒 None；`rec["match"]=lk_rec.get("match")` | `_re_linked.py:34-36`（纪律三）、`:276-281`（全量 `matches`，无 `max_detail` 截断）、`:320-329`；投影 `members_n=2 decl_lines=[13]`（`_mm_project_out.txt` §B） |

**「不写三键」的纪律论证（不是遗漏）**：

1. **纪律一原文** `_re_linked.py:26-29`：「merged rec 恒不写 path / verified_path / recomputed / bytes 等单对象字段……
   merged 是『副本群』形态，不指向任何单一对象」；`:254-256`、`:322-325` 再重复。
2. **代码面**：`:310-313` 骨架 `path=None`；`:314-319` 仅 unique 写三键；`:320-329` merged **只**写
   `tier/match/members/decl_lines`；`out["reverify"]` 恒 None（`:28-29`、`:178`）。
3. **语义面**：`:306-308` `match=True` 仅指「声明 hex 与全体成员现盘重算逐位一致」。若写 `verified_path`
   或 `recomputed`，等于把「群体的哈希」伪装成「某一个文件的哈希」；`_f2v_verify9.py:24-29` 会据此
   `Path(...).read_bytes()` 并比 `src["bytes"]`，**凭空制造单一锚对象** —— 正是纪律二
   （禁止由 merged 推导授权结论，`:30-33`、`RULING_D25:26`）要防的。
4. **`members` 是合法替代**：纪律三 `:34-36` 要求逐成员全列 `{path, sha, bytes}`；本会话投影的
   `members` 为 2 条（`qc151_trip.isolated.py` / `qc151_trip.candidate_lf.py`，各 412759 B，sha 全 64 位，
   `_mm_project_out.txt` §B）。信息在别处且更完整。
5. **实跑佐证**：`_mk_probe_out.txt:45-48` merged fixture `has verified_path/recomputed/bytes = False/False/False`、
   `reverify=None`；`MERGED_MIN_SAFETY_PATCH.md:280-285` U1-U6 把该缺席当作缺陷成因。
   ⇒ 这三键缺席是**可断言的正向契约**（宜有 `assert "verified_path" not in rec` 回归），不是待补字段。

### 3(c) 接入后 `rec` 三形态对照表（unique / merged / multi，附 zero）

依据：`_mk_probe_out.txt:41-64` 六 fixture `link_triple` 实跑 + 本会话 `_mm_project_out.txt` §B 30 件投影的 merged rec。
「接入后 rec」= `:196-197` 骨架（`citation/tried`）叠加 3(a)-C 的合并结果。

| 键 | **unique**（`Pu_unique_with_decl`） | **merged**（`Ffull_merged` / 30 件投影） | **multi**（`Fp1_decl_covers_one` / `Fd_equiv_words`） | 附：zero / invalid_hex |
|:--|:--|:--|:--|:--|
| `declared` | 原绑定行 hex（**保留原值，不采用 `lk_rec` 的 lower 版**） | 同左 | 同左 | 同左 |
| `citation` / `tried` | 原值（`:163,197` / `:266` 空列表） | 原值 | 原值 | 原值 |
| `tier` | `"SAMEDOC_LINK"` | **`"SAMEDOC_LINK_EQ"`** | `"SAMEDOC_LINK"` | `None` |
| `match` | `True` | **`True`**（仅指全体成员逐位一致） | `None` | `None` |
| `path` | 单一现盘路径（str） | **`None`** | `None` | `None` |
| `verified_path` | 单一现盘路径（str） | **不写（键缺席）** | 不写 | 不写 |
| `recomputed` | 64 hex | **不写（键缺席）** | 不写 | 不写 |
| `bytes` | int | **不写（键缺席）** | 不写 | 不写 |
| `members` | 不写 | **全列**（每条 `{path, sha, bytes}`，无截断） | 不写 | 不写 |
| `decl_lines` | 不写 | **全列**（fixture `[4]` / 30 件投影 `[13]`） | 不写 | 不写 |
| `samedoc_link` | `link()` 完整 out（`verdict=unique`，`reverify` 非空） | 完整 out（`verdict=merged`，含 `eq.members/decl_hits`，`reverify=None`） | 完整 out（`verdict=multi`，`reverify=None`） | `verdict=zero`，`reverify=None` |
| `problems`（函数级） | 不变 | **不变（恒不增）** | 不变 | 不变 |
| `warnings`（函数级） | 联查结论 warning（替换 R3-3b） | merged warning + 可能 1 条「同文档联查辅助」 | 联查多命中 warning | 保留 R3-3b 原文 + 联查零命中说明 + 辅助 |

**`None` vs 键缺席**（对消费者致命）：merged 的 `path=None`、`samedoc_link.reverify=None`；
multi 的 `path=None/match=None/reverify=None`；而 `verified_path/recomputed/bytes` 是 `not in rec`。
`.get("bytes","-")` 返回 `"-"`（`_f2w_extract.py:33`），`src["bytes"]` 直接 `KeyError`（`_f2v_verify9.py:29`）。

### 3(d) 下游行为变化逐件列（消费者影响面，含复核回件补正）

**量化投影（本会话实跑，命令见 §6；输出 `_mm_project_out.txt` §A-C）**：只做 ③、`_f2_compare.py` 与 ④ 完全不动、
用候选副本替换 `r11_scan_plus` 重跑 30 件：

- 变化 **5/30 件、10/19 条绑定行**；新 tier 分布 `{None:1, SAMEDOC_LINK:8, SAMEDOC_LINK_EQ:1}`；
- `totals` `BEFORE=(plus_path 9, plus_match 9)` → `AFTER=(plus_path 17, plus_match 18)`，
  `bindings/orig_*/plus_problems` 不变；`warnings 11→14`；`plus_problems 恒 23`；
- `_f2_compare.py:44-50` 三条断言投影 **30/30 通过**；
- 真实产出 1 条 merged rec：`lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md`
  （`tier=SAMEDOC_LINK_EQ`、`path=None`、`match=True`、`members_n=2`、`decl_lines=[13]`）。

**逐件清单**（读 JSON 4 件 / 直调 plus 7 件 / 门禁 1 件 / 指纹锁与登记面）：

| # | 消费者 | 实读位置 | ③ 接入后行为 | 证据 |
|--:|:--|:--|:--|:--|
| 1 | `_f2_compare.py`（写者 + 计数 + 打印 + 落盘） | `:35-36,65-71,73-74,100-101` | `totals` 变 `(17,18)`；`:100` 重写 `_f2_compare_out.json` 全件字节变；`results[].plus.bindings` 里 10 条 rec 形状变（新增 `samedoc_link/members/decl_lines`）。**这就是 ④ 的落点** | 本会话 `Read`；`_mm_project_out.txt` §A |
| 2 | `_f2w_checks.py`（读 JSON） | `:14,26-38` | merged 条 `sha_ok=False`（`(b.get("recomputed") or "").lower()` 为空），`n_ok` 少计 1；unique 8 条因候选写了 `recomputed` 反而「逐字一致」→ 9 变 17，**语义混杂** | `_mm_project_out.txt` C2；本会话 `Read` |
| 3 | `_f2w_extract.py`（读 JSON） | `:12-13,24-33` | merged 条 `verified='' recomputed='' bytes='-'` 静默空白；unique 8 条出现新 `tier=SAMEDOC_LINK` 与现盘重算值；19 条逐条表整体变（与 `_f2_repro_out.json` `zip` 行数/顺序不变故不崩） | `_mm_project_out.txt` C3；本会话实读 `rows_n=19` |
| 4 | `_f2w_pass.py`（读 JSON） | `:6-7,10-25` | `plus match` 9→18；`warnings` 11→14；`R11 PASS` 件数不变（`problems` 恒 23）；merged 被计入「已回验」统计 | `_mm_project_out.txt` C4 |
| 5 | `_f2w_final.py`（读 JSON） | `:30-34` | **正常但数字变**：`orig_warnings` 不变、`plus_warnings` 11→14；不读单对象键，不崩 | `_mm_project_out.txt` C10 |
| 6 | `_f2v_verify9.py`（直调） | `:19-36` | **崩（① 未落地时）**：`Path(None)` → `TypeError`；绕过则 `src["bytes"]` → `KeyError` | `_mm_project_out.txt` C1；`MERGED_CONSUMER_AUDIT.md:120` |
| 7 | `_f2_selftest.py`（直调） | `:60,105-111`（另 `:64,75,117,126,130,141` 调 plus） | **★ 复核补正：S4 不受 ③ 影响**（见下）；`:60` `sha_of(F2PLUS)` 动态取值不硬编码指纹；S6（`:141` 只比 `len(n_p)>len(o_p)`）因 `problems` 恒 23 不触发 | 本会话 `_mm_probe_out.txt` §S4 对跑；`_mkv_*` 复核 ⑤(c) |
| 8 | `_f2v_final.py`（直调） | `:50-59` | `collected=9→17`、`match=9→18`、开放 `tiers` dict 新增两类；不崩但统计混杂 | `_mm_project_out.txt` C6；本会话 `Read :45-59` |
| 9 | `_f2v_run.py`（直调 + 写第二件 totals） | `:25,35,48-52,60-72` | `plus_paths` 出现 `None`、`plus_match` 出现 `True`；**`_f2v_run_out.json` 9 键 totals 同步漂移** → ④ 影响面不止 compare JSON | `_mm_project_out.txt` C7；`_mm_probe_out.txt` §RUN |
| 10 | `_f2w_dogfood.py`（直调） | `:20-33` | 同 #8；`plus warnings` 打印变 | `_mm_project_out.txt` C6 |
| 11 | `_f2v_edge.py`（直调） | `:36-39,48-51,77-84` | **正常**：不假设单对象 path，用 `.get` 打印；fixture 期望输出文本会随 warning 变化 | `MERGED_CONSUMER_AUDIT.md:130` B11；本会话 `grep` |
| 12 | `_g9_gate.py`（门禁，当前**不可达**） | `:155-167` | 当下 merged 不流入（`:155` 实读 `g7.r11_scan`，`_mk_probe_out.txt:95`）；**若将来改接 plus**：`reverified=17/match_true=18/problems=[]` ⇒ 旧 `:160` 仍 PASS，1 条零单一锚定 merged 被静默放过（② 未落地时） | 本会话 `Read :150-167`；`_mm_project_out.txt` C9 |
| 13 | `_f2_repro.py` / `_f2v_context.py` / `_g9v_verify.py` 等原版 `r11_scan` 组 | `_mc_AUDIT.md:186`、`MERGED_CONSUMER_AUDIT.md:132-135` | **不受 ③ 影响**（不调 plus），行数/顺序不变故 `_f2w_extract.py:24` 的 `zip` 不崩 | 审计表 B12/B13/B15/B16 |
| 14 | **compare_out 指纹锁 3 件** | `f2d_rootcause_20261109/_f2d_fpcheck.py:11`、`_f2dw_fpcheck.py:22`、`_f2dv_fpcheck.py:27` | 一旦 `:100` 重写 JSON（甲/乙/丙皆然）→ `MISMATCH/DRIFT` | 本会话 `grep -n '148ea8d6'` 实跑 |
| 15 | **r11plus 指纹锁 ≥8 件（复核回件补正，上轮方案件漏列）** | `_eqv_fp.py:38`、`_f2v_fp.py:16`、`_re_fp_check.py:24`、`_rev_core.py:35`、`_slw_hashes.py:38`、`_mcv_fp.py:13`，及 #14 的 3 件同时锁 r11plus | ③ 会改 `_f2_r11plus.py`（接入方重算登记，`_mk_CONTRACT_DESIGN.md:699` 自述）→ 这些硬编码 `83f8217f…/15723` 的件全部 `BASELINE_MISMATCH/MISMATCH/DRIFT` | 本会话 `grep -rIln --include='*.py' '83f8217f' lead/` 实得 **19 件**，其中 PROD/AUDIT **8 件**（其余为沙箱/上轮审计/写域探针），见 `_mm_probe_out.txt` §FP；判定点 `_eqv_fp.py:69`、`_rev_core.py:49-55`、`_slw_hashes.py:29` |
| 16 | **`_ow_raw_hits.json` fileMeta 快照（复核回件补正，上轮方案件漏列）** | `oldwording_sweep_20261109/_ow_sweep.py:66` → `_ow_raw_hits.json:15229-15279` | 该 JSON 的 `fileMeta` 实存四件快照：`_f2_compare_out.json`(148ea8…/44958)、`_f2_compare.py`(12e55a…/4821)、`_f2_r11plus.py`(83f821…/15723)、`_f2v_run_out.json`(a62ee13e…/25200) → ④/③ 重写后 stale | 本会话 `_mm_probe_out.txt` §OW 实读四件 `{'sha256','bytes'}`；`grep -n '148ea8d6\|83f8217f\|12e55acf'` 命中 `:15259/:15263/:15279` |
| 17 | 报告/台账登记面 | `R11_F2_COVERAGE_FIX.md:47`、`_f2_F2_PATCH_REPORT.md:141`、`F2D_ROOT_CAUSE.md:41`；两件台账 | 数字（9/9/19/24/23）与指纹引用需同步登记；两件台账本任务绝对只读。本会话 `grep -c 'SAMEDOC_LINK_EQ\|counting_policy\|plus_match_by_kind'` = `1 / 2`（实为别的主题行，非 ③④ 裁决条目），`grep -n '计数口径'` 命中 `:289` / `:6385` / `:9361` 均与 ④ 无关 ⇒ **现无 ③④ 裁决登记** | 本会话两条 `grep` 实跑（§6 命令表） |

> **★ 复核回件 ⑤(c) 的 S4 误判，本会话独立复跑确认并更正**：上轮 `_mk_CONTRACT_DESIGN.md:373`
> 与 `:672` 断言「`_f2_selftest.py` S4 断言返回 `False`、断言失败（C8）」。
> 但 `_f2_selftest.py:106-107` 的 S4 文本带两个反引号 T2 锚（`_f2_repro.py` 与 `_f2_r11plus.py`），
> 走的是 `:250-272` 的 T2 any-match-wins 分支，**根本到不了 `:303-305` 的 else**。
> 本会话 `_mm_probe.py` 用该原用例对跑原件与候选，输出 §S4：
> `ORIG tier='T2' match=True verified=.../_f2_r11plus.py ... S4_assert=True reached_303_305_else=False` /
> `CAND tier='T2' ... S4_assert=True reached_303_305_else=False`（两版 `changed=False`）。
> `_mk_project_out.txt:25` 的 `C8 = False` 是把 §B 单条 merged rec 手工喂进 `:110` 表达式
> （`_mk_project.py:105-106` 实读 `M.get("verified_path","").endswith(...)`），**不是真实 S4 路径**。
> ⇒ 本件把 #7 更正为「S4 不受 ③ 影响；C8 仅对单条 merged rec 表达式成立」。

---

## 4 机读件计数口径裁决方案（④）：多方案对照 + 消费者影响 + 向后兼容 + 推荐（须所有者裁决）

> **★ 本节全部内容属「须模板所有者裁决」，本件只给选项与后果，不替所有者决定。**
> 共同前提（不属裁决但须随方案落地）：`MERGED_CONSUMER_AUDIT.md:184` 要求 B3/B6/B7/B8/B9/B10
> 显式区分「merged 匹配 ≠ 单一回验」；`MERGED_MIN_SAFETY_PATCH.md:304` 复核 ⑥ 已证「JSON 读者与直调者两路消费面须分别裁决」。
> **任何只改 `totals` 的方案都不覆盖直调者那一路**，三方案皆须额外声明。

### 4(a) ≥2 方案对照（三方案，均给出逐字改前改后 + 30 件投影）

**共同改前（`_f2_compare.py:35-36`、`:65-71`）**：

```python
# 改前（逐字）
tot = {"bindings": 0, "orig_path": 0, "plus_path": 0, "orig_match": 0,
       "plus_match": 0, "orig_problems": 0, "plus_problems": 0}
...
tot["bindings"] += len(o_bind)
tot["orig_path"] += sum(1 for b in o_bind if b["path"])
tot["plus_path"] += sum(1 for b in n_bind if b.get("path"))
tot["orig_match"] += sum(1 for b in o_bind if b["match"] is True)
tot["plus_match"] += sum(1 for b in n_bind if b.get("match") is True)
tot["orig_problems"] += len(o_prob)
tot["plus_problems"] += len(n_prob)
```

#### 方案甲：`totals` 新增键，既有 7 键语义不变（additive）

```python
# 改后（甲，候选；键名仅示例，由所有者定）
tot = {"bindings": 0, "orig_path": 0, "plus_path": 0, "orig_match": 0,
       "plus_match": 0, "orig_problems": 0, "plus_problems": 0,
       "plus_merged_match": 0, "plus_match_no_path": 0,
       "plus_samedoc_unique": 0}
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

- 旧 7 键**逐字不重定义**：`plus_match` 仍含 merged，`plus_path` 仍只数单一 path。
- 30 件投影（按候选 rec 推算，**非实跑该方案**）：`plus_path=17, plus_match=18,
  plus_merged_match=1, plus_match_no_path=1, plus_samedoc_unique=8`；`17+1=18` 恒等式可回归。
- 优：改动最小、旧键零重定义。缺：**旧键误导性保留**（只读 `plus_match` 的旧消费者仍把 merged 当单一回验）；
  `plus_match_no_path` 与 `plus_merged_match` 重叠需文档说明；报告层仍需逐件改。

#### 方案乙：`totals` 拆**三态**，既有键废弃/重定义（breaking）

```python
# 改后（乙，候选）
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

- `plus_path` / `plus_match` **废弃或重定义**（二择一必须写进判定书，本件不拍板）。
- 优：三态互斥且完备，`match=True` 不再被误当单一回验（直接满足 `MERGED_CONSUMER_AUDIT.md:184`）。
- 缺：**破坏面最大**：`:67,69` 两表达式被删/重定义；同名不同义最危险；历史 JSON 与新 JSON 不可互读（4(c)）。

#### 方案丙（推荐候选，非决定）：保留 7 键 + 正交 `tier` 分组 + 分类键 + `schema_version`（additive + 自描述）

```python
# 改后（丙，候选）
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

同时在 `results[].plus` 加机读分类键（如 `"match_kind": "single_path"|"merged_eq"|"none"`），
文件顶层加 `"counting_policy": "<裁决书编号>"`（顶层 `schema_version` 是否同步由所有者定）。

- 30 件投影（推算）：`plus_tier_counts = {T1:1,T2:5,T2N:2,T3:1,SAMEDOC_LINK:8,SAMEDOC_LINK_EQ:1,NONE:1}`；
  `plus_match_by_kind={single_path:17, merged_eq:1}`；与 `plus_path=17`、`plus_match=18` 自洽。
- 优：旧 7 键零重定义（旧读者不破）、开放 `tier` dict 不因未来新 tier 再改 schema、
  恒等式 `plus_path == plus_match_by_kind["single_path"]`、`plus_match == single_path + merged_eq` 可回归、
  `results[]` 分类键服务两路。缺：改动面比甲大；`results[]` 加键属结构扩展，需「旧代码忽略未知键」约定。

**对照总表**：

| 维度 | 甲 | 乙 | 丙（推荐候选） |
|:--|:--|:--|:--|
| 旧 7 键 | 逐字保留、语义不变 | 废弃或重定义（同名不同义） | 逐字保留、语义不变 |
| 新增维度 | 3 个补键（`plus_merged_match` 等） | **三态** `plus_by_kind{single_path,merged_eq,none}` | `plus_tier_counts` + `plus_match_by_kind` + `schema_version` + `results[].plus` 分类键 |
| `plus_match` 含 merged | 是 | 否（或重定义） | 是 |
| 能否区分 merged/unique | 能（补键） | 能（三态） | 能（互斥二态 + 恒等式） |
| 改 `:100` 重写整件 | 是 | 是 | 是 |
| 结构扩展 `results[]` | 否 | 否 | 是 |

### 4(b) 每方案对既有消费者的影响（谁读 `totals`？谁读 `plus_path/plus_match`？会不会破）

**本会话查清的事实**：

- **读 `_f2_compare_out.json` 的 `totals` 的件 = 0**。写者只有 `_f2_compare.py:100`；
  4 个读者 `_f2w_checks.py:14`、`_f2w_extract.py:13`、`_f2w_pass.py:6`、`_f2w_final.py:31`
  实读**都不出现 `totals` 字样、只取 `cmp_["results"]`**（`_mm_probe_out.txt` §JSONREAD 四行
  `totals_lit=False d_results=True`；`_mkv_consumers_out.txt:72-76` 同）。
  全仓 `d["totals"]` 仅 5 个 `.py`（`_mkv_consumers_out.txt:4-19`）：2 个读别件 mimosa findings
  （`goal3_mimosa_tools_review_20261022/_summarize.py:14`、`qc161_u0400_trip/_census_d07_gate36.py:86`），
  另 3 个是写域探针/上轮探针（`_mk_probe.py:121,136`、`_mkv_consumers.py:89,124,140,142`、`_ms_tight.py:201,210`）。
- **按 `plus_path`/`plus_match` 同口径自算的 8 件**（`_mkv_consumers_out.txt:21-71` §B）：
  `_f2_compare.py:35,36,67,69,81`、`_f2v_run.py:25,51,62,64`、`_f2w_extract.py:29`，
  加 `_f2w_checks.py:28-29`、`_f2w_pass.py:17`、`_f2v_final.py:54`、`_f2w_dogfood.py:26`、
  `_f2v_verify9.py:21`、`_mc_empirical.py` / `_ms_probe.py` / `_ms_tight.py` / `_msv_check.py`（上轮探针）。
  7 件直调 `r11_scan_plus` 见 `_mk_probe_out.txt:86-93`；`_g9_gate.py:155` 仍 `g7.r11_scan`（`:95`）。
- **硬编码指纹/登记面（含复核补正）**：compare_out 锁 3 件（#14）、r11plus 锁 PROD/AUDIT 8 件（#15）、
  `_ow_raw_hits.json` fileMeta 四件快照（#16）、3 份报告登记（#17）。**三方案皆然**。

| 消费者 | 甲 | 乙 | 丙 |
|:--|:--|:--|:--|
| 4 个 JSON 读者（#2–#5） | **不破**（不读 totals、忽略未知键）；报告数字仍按 `results[]` 旧口径混杂 → **静默误读不修** | **不破**（同上）；若将来改读 totals 才会破 | **不破**；新 `results[].plus.match_kind` 给它们**机读依据**去修 |
| `_f2_compare.py:67,69,73-74,100` | 改累加（+3 键） | 删/重定义 2 键，改动最大 | 改累加（+3 键 + 开放 dict） |
| `_f2v_run.py` 的 `_f2v_run_out.json`（9 键） | 键名不同，**不受影响但口径不一致**（仍 `plus_collected=17/plus_match=18` 无 merged 维度）；须单独裁决 | 同左；若统一三态须同改 | 同左；建议同步加 `plus_match_by_kind` |
| 8 件直调/重算者（#6–#11、#2–#4） | **不破，但静默误读仍在**（§5(b) 传导链）；须按 `MERGED_CONSUMER_AUDIT.md:184` 逐件加分支 | 不破，语义仍混杂 → 逐件加分支同样不可省 | 不破；分类键可直接被它们引用 |
| `_g9_gate.py`（当前不可达） | 无关（不读 JSON） | 无关 | 无关；② 独立处理 `match=True and not path` |
| compare_out 锁 3 + r11plus 锁 ≥8 + `_ow_raw_hits.json` + 3 份报告 | **破**：JSON/源码字节变 → `MISMATCH/DRIFT/stale` | **破**（同上，且更严重） | **破**（同上） |
| 两件台账（绝对只读） | 需登记裁决，不改 | 需登记裁决，不改 | 需登记裁决，不改 |

**共同结论**：三方案**没有任何一个**会因「totals 键变化」直接弄崩 4 个 JSON 读者（它们根本不读 totals）；
三者**都会**弄崩 compare_out 3 件指纹锁（`:100` 必然重写整件），且 ③ 另会弄崩 r11plus ≥8 件指纹锁
与 `_ow_raw_hits.json` 快照。差别只在「旧键误导性是否消除」与「报告层是否有可机读的分类依据」。
**只改 totals 不覆盖直调者一路**（复核 ⑥），#15/#16 两类漏项须一并纳入裁决范围。

### 4(c) 向后兼容性

| | 旧 json 被新代码读 | 新 json 被旧代码读 |
|:--|:--|:--|
| **甲** | **能读**：新代码若 `tot.get("plus_merged_match", 0)` 则旧 JSON 缺键取默认 0；若**断言键存在**则旧 JSON 失败（须显式降级分支） | **能读**：4 个旧读者不读 totals、忽略未知键；`results[]` 结构不变 ⇒ 不崩。只是旧读者不知道 merged 存在，继续静默误读 |
| **乙** | **不能读（除非写兼容层）**：旧 JSON 无 `plus_by_kind`，且 `plus_path/plus_match` 被废弃/重定义 ⇒ **同名不同义最危险（静默错值，不报错）** | **不能读（若旧代码按名取键）**：`KeyError: 'plus_match'`；本会话查实 4 个读者不取，故实盘不崩，但未来按名取的读者会崩；`results[]` 未变 ⇒ 旧读者仍可跑 |
| **丙** | **能读**：`schema_version` 缺省视为 1，新代码走旧口径；`plus_tier_counts`/`plus_match_by_kind` 用 `.get(..., {})` 兜底 | **能读**：既有 7 键逐字保留、语义不变；新增键被旧代码忽略；`results[].plus` 新键被 `.get` 读者忽略 ⇒ 不崩 |

> 补充：上述为**基于源码实读的结构推断**，本会话**未跑**真实新旧 JSON 双向兼容回放（标「未验」，§6）。
> 「旧 json → 新代码」在三方案里还另面临 `:100` 重写后的指纹锁问题，与 schema 兼容是两件事，须分别登记。

### 4(d) 推荐与理由 + 明确标注须所有者裁决

**推荐候选 = 方案丙**（推荐 ≠ 决定），理由（基于本会话实读/实跑）：

1. 既有 7 键零重定义 ⇒ compare_out 指纹锁之外**零代码破坏**（4(b) 表）；
2. `plus_tier_counts` 是开放 dict，不会因未来新 tier 再改 schema（`_mc_AUDIT.md:202-203`「现盘无封闭白名单」）；
3. `plus_match_by_kind` 给出 `single_path`/`merged_eq` 互斥二态 + 恒等式
   `plus_path == plus_match_by_kind["single_path"]`、`plus_match == single_path + merged_eq`，
   可写成回归断言，直接回答 2.4 缺的维度；
4. `schema_version` + `counting_policy` 让 4(c) 两向兼容可机读判别，避免乙的同名不同义静默错值；
5. `results[].plus` 分类键是**唯一能同时服务两路消费面**的落点（`MERGED_MIN_SAFETY_PATCH.md:304` 复核 ⑥），
   甲/乙只动 totals，报告层 8 件仍无依据可修。

**★ 此项须模板所有者裁决。本件不拍板的点（逐项列出）**：

- (a) `plus_match` 是否允许继续含 merged（甲/丙 含、乙 不含）；
- (b) `plus_path` / `plus_match` 是否废弃（乙）；
- (c) 键名、`schema_version` 起点、`results[]` 加哪个分类键、`_f2v_run_out.json` 是否同步、
  compare_out 3 件 + r11plus ≥8 件指纹锁 + `_ow_raw_hits.json` + 3 份报告登记如何重基线；
- (d) 「最小安全集 5 条」vs「4 项+1 治理」的数字口径（`_mk_CONTRACT_DESIGN.md:35`、`MERGED_MIN_SAFETY_PATCH.md:292-294`），
  本件不裁；以及 `linkFamily.verified_path=0` vs 实读 2（§2.3）。

上轮禁用词正则由【复核】⑦ 记载为 `grep -nE ... _mk_CONTRACT_DESIGN.md` 命中 0（本会话实读【复核】材料，
未重跑该条）；本件经同一正则用 `python -I -X utf8 -B -c` 实跑 `FORBIDDEN_HITS = 0`，
并以 `grep -nE` 同口径实跑 `GREP_EXIT=1`（§6.3 命令表 #9）；
全篇一律用「候选 / 选项 / 推荐候选 / 须所有者裁决」表述。

---

## 5 ③④ 与 ①② 的先后依赖：三情形 + 落地顺序与每步验证

### 5(a) 只做 ①②（当前状态：合规，功能未上线）

- `R33E_MERGE.md:17`「本报告不自行上线」、`SAMEDOC_LINK.md:22`「是否接入由编排方裁决」、
  `MERGED_CONSUMER_AUDIT.md:193`「暂不接入是合规现状」；
- 本会话实读 `_f2_r11plus.py:303-305` 仍 `tier=None` + R3-3b warning、link 家族 3 符号全 0（§2.2/2.3）；
  `_g9_gate.py:155` 仍 `g7.r11_scan`；`_f2v_verify9.py:24` 仍单对象 `Path(...)`（§1 命令表）。生产链不产、不收 merged
  （`MERGED_CONSUMER_AUDIT.md:142-144` severity=medium 的前提）。
- ①② 是「未来接入面」的预防性补丁：上轮记载 30 件 `0/30` 漂移、`COUNTEREXAMPLE_OK`
  （`MERGED_MIN_SAFETY_PATCH.md:315-316`），**本会话未复跑**，标未验（§6）。
- **但**：`MERGED_CONSUMER_AUDIT.md:181` 最小安全集是 5 条、`MERGED_MIN_SAFETY_PATCH.md:292` 明示
  「两处不是接入的最小安全集」；只做 ①② ⇒ ③ 空置 ⇒ merged 根本没接进来（`:306`），
  ④ 未裁 ⇒ 机读件仍是「`plus_match == plus_path` 巧合恒等」。owner/SOP/sink 缺口（`:190-194`）仍缺。

### 5(b) 加做 ③ 未做 ④：具体传导链（30 件真实投影，非单条手工喂入）

本会话 `_mm_project_out.txt` §A-C 实跑（命令见 §6），逐字摘录：

```
③ 接入（候选副本，_f2_compare.py 与 ④ 完全不动）
  ↓ 30 件中 10 条 else 绑定行走联查：8 unique + 1 merged + 1 zero
  ↓ 5/30 件 plus.bindings 形状变（新 tier / members / decl_lines / samedoc_link）
  ↓ problems 恒 23（纪律）→ plus.verdict 全不变 → 门禁与 verdict 层看不出异常
  ↓ warnings 11→14；_f2_compare.py:44-50 断言 30/30 仍过（不报警）
  ↓ _f2_compare.py:67/69 照旧无条件累加 → totals: plus_path 9→17, plus_match 9→18
  ↓ _f2_compare.py:100 重写 _f2_compare_out.json（整件字节变）
     ├─ compare_out 3 件指纹锁 + r11plus ≥8 件指纹锁 → MISMATCH/DRIFT
     ├─ _ow_raw_hits.json fileMeta + 3 份报告登记 → stale
     └─ 4 个 JSON 读者（不读 totals，只取 results[]）：
         ├─ _f2w_checks.py:29   merged 条 sha_ok=False → n_ok 少计 1（C2）
         ├─ _f2w_extract.py:26-33 verified='' recomputed='' bytes='-' 静默空白（C3）
         ├─ _f2w_pass.py:17     plus match 9→18，merged 混入「已回验」（C4）
         └─ _f2w_final.py:31-33 plus_warnings 11→14（正常，数字变；C10）
  ↓ 直调者一路（不经 JSON，④ 改 totals 完全够不着）：
     ├─ _f2v_verify9.py:24/29  → TypeError / KeyError（① 未落地时；C1）
     ├─ _f2_selftest.py S4      → ★ 不受影响（T2 锚先行，本会话 §S4 对跑修正）
     ├─ _f2v_final.py:54-58 / _f2w_dogfood.py:25-30 → collected=17 match=18 tiers 新增两类（C6）
     ├─ _f2v_run.py:48-52,71   → plus_paths=[...,None] plus_match=[...,True]，且 9 键 totals 漂移（C7）
     └─ _f2v_edge.py           → 正常（.get 打印）
  ↓ 门禁（若将来改接 plus，② 未落地时）：reverified=17 match_true=18 problems=[] ⇒ 旧 :160 PASS（C9）
  ⇒ 1 条「零单一对象锚定」的 merged 被静默计成已回验；报告层两路同时静默错；
    totals 里 plus_match(18) ≠ plus_path(17) 却无任何键解释这 1 的差额。
```

对应 `MERGED_MIN_SAFETY_PATCH.md:307`「只修 1+2+3 不修 4：JSON 读者与直调者两路报告仍静默错」
与 `:280-285` U1-U6；本件把它从「单条手工喂入」升级为 **30 件真实投影**，并补出
unique 8 条的 `(9→17, 9→18)`、`_f2v_run_out.json` 第二机读件、以及复核回件指出的 #15/#16 两类漏项。

### 5(c) 四项全做（①② + ③ + ④）：落地顺序与每步验证

依 `MERGED_MIN_SAFETY_PATCH.md:310-322` / `_mk_CONTRACT_DESIGN.md:685-699`，顺序 = 「先裁决、再修消费面、最后才动接入点代码」：

| 序 | 做什么 | 为什么 | 每步验证（本会话已跑 / 未验如实标注） |
|--:|:--|:--|:--|
| 0 | **④ 口径裁决 + 接入与否裁决**（不改代码）：所有者定甲/乙/丙、`plus_match` 语义、键名/`schema_version`/`results[]` 分类键、`_f2v_run_out.json` 是否同步、compare_out 3 + r11plus ≥8 指纹锁 + `_ow_raw_hits.json` + 3 份报告重基线方式；台账登记 `SAMEDOC_LINK.md:20` ★4 显式修订与 owner/SOP | ④ 是口径裁决不是实现细节；`MERGED_CONSUMER_AUDIT.md:190-194` 要求先补 owner/触发 SOP；两件台账绝对只读只登记 | 判定书成文；11 件指纹复核（本会话 `_mm_fp_out.txt` **11/11 全等，已跑**）；**本步本会话未做，未验** |
| 1 | ① `_f2v_verify9.py` 三形态分支 | 唯一实证崩点（`_mcv_empirical.py` `CRASH_COUNT=3`）；不先修则下游全量回放必崩 | 上轮记 30 件 `checked 9`/`MISMATCH=0`、compile OK（`MERGED_MIN_SAFETY_PATCH.md:315`）；**本会话未复跑**，只复核原件 `:24` 仍在，标未验 |
| 2 | ② `_g9_gate.py` `match=True and not path` 缺口（与 1 同批） | 静默放行；`match=True` 无单一 path 不得默认 PASS | 上轮记 `0/30` 漂移、`COUNTEREXAMPLE_OK`（同件 `:316`）；**本会话未复跑**，只复核 `:160` 仍在，标未验 |
| 3 | **消费面两路适配**（`MERGED_CONSUMER_AUDIT.md:184` B2/B3/B5/B6/B7/B8/B9/B10）：JSON 读者 4 件 + 直调者 7 件，统一约定 `tier=="SAMEDOC_LINK_EQ"` 走 `rec["members"]`，不取 `path/verified_path/bytes` | ④ 的裁决只有落到两路才生效（复核 ⑥） | 逐件喂本会话投影的 merged rec（`_mm_project_out.txt` §B）断言零 TypeError / 零 KeyError / 无误读计数；**本会话只跑 10 个表达式（§C）与 S4 对跑，全量 11 件回放未做、未验** |
| 4 | **④ 落地**：按 0 裁决改 `_f2_compare.py:35-71,100`（及 `_f2v_run.py:25-72` 若裁决同步），重基线 #14–#17 全部登记面 | 让机读件能区分「merged 匹配」与「unique 单一回验」 | 恒等式断言（丙）：`plus_path == plus_match_by_kind["single_path"]`、`plus_match == single_path+merged_eq`；旧 json 读新代码 / 新 json 读旧代码双向回放；`declared` 序列 30/30 不漂移（`:45-46`）；**未验** |
| 5 | **③ 落地**：按 3(a) 改 `_f2_r11plus.py`（A/B/C 三处），`_re_linked.py` 保持只读 | 前 4 步都是为它准备消费面；**最后才动代码** | 本会话已做候选副本编译与 30 件投影：`BEFORE_C count=1`、`CANDIDATE_COMPILE=OK`、30 件 `asserts 30/30`、`warnings 11→14`、`plus_problems=23`、`totals (9,9)→(17,18)`、merged rec 形状（`_mm_project_out.txt`）；**正式端到端联调、7 件形状断言回归（`_re_j4_cases.py` 19/19 等）未做、未验** |
| 6 | 门禁契约回归 + run 快照 + 判定书登记 | ② 只在「改接 plus」时生效；merged 是联查时刻快照（TOCTOU 同限，`_re_NOTES.md:72-73`） | 每次 merged 落 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`；`_g9_gate.py:157-158` 若改接 plus 须重裁 `reverified`/`n_match`；**未验** |
| 7 | 指纹护栏收尾 | ③ 会改 `_f2_r11plus.py`（接入方重算登记），只读件与两件台账不得动 | 前后各算一次 `hashlib.sha256`：本会话 11/11 全等（`_mm_fp_out.txt`）、只读域新增 `.pyc` 检查、`git status` 复核（本会话实跑，见 §6）；`git log -1` 本会话未跑，标未验 |

---

## 6 复核回件（绑定行）+ 未改任何件声明 + 未验项

### 6.1 复核回件 verdict（如实记，partial 标 unconfirmed）

任务给定【复核】：`ranCommands = 54`、`sha256Line` = `被核对象 SHA256 = 83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75，字节数 = 15723`、
**`verdict = partial`**。按交付要求「refuted 或 partial 标 unconfirmed」：
**本方案件整体结论标 `unconfirmed`**（复核 partial 未翻为 confirmed）。
复核通过项（①–④、⑥–⑧）：11 件指纹 `11/11 MATCH`、改前片段逐字与行号、口径分歧如实登记、
`problems 恒 []` 纪律、else 原文、未替所有者拍板、未越界，全部成立；
**⑤ partial 的三处实锤**（本会话独立复核，全部采纳并已补入 §3(d)）：

1. **#15 漏项**：③ 必然改 `_f2_r11plus.py`（`_mk_CONTRACT_DESIGN.md:699` 自述「接入方重算登记」），
   但上轮只列 3 件 compare_out 锁。本会话 `grep -rIln --include='*.py' '83f8217f' lead/` 实得 **19 件**，
   PROD/AUDIT **8 件**（`_mm_probe_out.txt` §FP 逐件列出），其余为沙箱/上轮审计/写域探针；
   `_f2_selftest.py:60` 用 `sha_of(F2PLUS)` 动态取值不硬编码，故不受影响。
2. **#16 漏项**：`_ow_sweep.py:66` 把 `fileMeta` 落进 `_ow_raw_hits.json`；本会话实读该 JSON，
   `fileMeta` 确有 `_f2_compare_out.json`(148ea8…/44958)、`_f2_compare.py`(12e55a…/4821)、
   `_f2_r11plus.py`(83f821…/15723)、`_f2v_run_out.json`(a62ee13e…/25200) 四件快照（`_mm_probe_out.txt` §OW）。
3. **#7 S4 误判**：上轮 `:373` / `:672` 断言「S4 断言失败」不成立。本会话 `_mm_probe.py` §S4 用
   `_f2_selftest.py:105-111` 原用例对跑原件与候选，两版 `tier='T2' ... S4_assert=True reached_303_305_else=False`；
   C8 是把单条 merged rec 手工喂进 `:110` 表达式（`_mk_project.py:105-106`），不是真实 S4 路径。
   ⇒ 本件 §3(d) #7 与 §5(b) 已更正为「S4 不受 ③ 影响」。

> 复核【如实标注的边界观察】：`lead/gate_r9r12_20261109/__pycache__/_g9_regression.cpython-312.pyc`
> （12:49:17）晚于撰写人交付 12:26；复核脚本未 import 该模块，不排除工作流并发 actor，
> 与「撰写人是否越界」无关，11 件基线指纹全等未受污染。本会话沿用该如实标注，未据此改判。

### 6.2 绑定行（严格格式，本会话实算）

被核对象 SHA256 = 83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75，字节数 = 15723
被核对象 SHA256 = 12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106，字节数 = 4821
被核对象 SHA256 = 148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1，字节数 = 44958
被核对象 SHA256 = 23c5eebb77b43e9e187be6b4736fe1f0b3f5d8eb7f46a9ee2f8af1bbbce53514，字节数 = 2189
被核对象 SHA256 = 1eb22164c78330e825d053f665934e9ef1e4eba14e2b101c884de68a91aad701，字节数 = 1564
被核对象 SHA256 = 625704697e412c30a278c616cf8be594b8b870a2734df2219aa0607aa74a19bd，字节数 = 8579
被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481
被核对象 SHA256 = 8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367，字节数 = 33762
被核对象 SHA256 = bc5eb5d0d13e1fbe8a67451141476c7f077ec49e0d8e9a6bbab34bc569110c44，字节数 = 34299
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

> 格式核验：每行 `被核对象 SHA256 = ` + 完整 64 位小写十六进制 + `，字节数 = ` + 数字；
> 格式核验：每行 `被核对象 SHA256 = ` + 完整 64 位小写十六进制 + `，字节数 = ` + 数字；
> 中间无路径、括号、星号、反引号或空格。本件共 22 条严格格式绑定行（§2.1 十一件 + 本节复核回件十一件，
> 两组各 11 条、内容相同），本会话 `python -I -X utf8 -B -c` 正则校验输出
> `STRICT_LINES = 22 MALFORMED = 0`，并以同口径 `grep -nE` 禁用词正则实跑 `GREP_EXIT=1`（命中 0），
> 见 §6.3 命令表 #9。

### 6.3 本会话实跑命令与输出（逐条可复核）

| # | 命令（`python -I -X utf8` + 绝对路径；`>` 重定向到写域） | EXIT | 关键输出 |
|--:|:--|--:|:--|
| 1 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mm_fp.py > .../_mm_fp_out.txt` | 0 | 11 行 `MATCH=True` + `ALL_MATCH = True COUNT = 11`（§2.1） |
| 2 | `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mm_probe.py > .../_mm_probe_out.txt` | 0 | §S4 `ORIG/CAND S4_assert=True reached_303_305_else=False`；§FP 19 件/PROD 8 件；§OW fileMeta 四件；§CMP `EQUALS=True`、`plus_path_set == plus_match_set : True`；§PROB `write-statements count = 0 []`；§RUN 9 键 totals（§2.4/3(b)/3(d)） |
| 3 | `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mk_project.py > .../_mm_project_out.txt` | 0 | 30 件投影 `(9,9)→(17,18)`、`5/30 件 10/19 条`、`asserts 30/30`、`warnings 11→14`、`plus_problems=23`、merged rec 形状、C1–C10（§3(c)/5(b)） |
| 4 | `python -I -X utf8 -B -c "import py_compile; py_compile.compile(.../_mk_r11plus_candidate.py, cfile=.../__pycache__/_mm_cand.pyc, doraise=True)"` | 0 | `CANDIDATE_COMPILE=OK`；另 `BEFORE_C count = 1`（§3(a)） |
| 5 | `grep -rIln --include='*.py' '83f8217f' lead/ \| wc -l` + `grep -n '148ea8d6' .../_f2d*fpcheck.py` | 0 | `19`；3 件 compare_out 锁 `:11/:22/:27` 命中（§3(d) #14/#15） |
| 6 | `grep -n 'Path(src.get\|r11_verdict = "FAIL" if r11_problems' lead/r11_f2_fix_20261109/_f2v_verify9.py lead/gate_r9r12_20261109/_g9_gate.py` | 0 | `_f2v_verify9.py:24`、`_g9_gate.py:160` 现状未落地（§1） |
| 7 | `grep -c 'SAMEDOC_LINK_EQ\|计数口径\|counting_policy\|plus_match_by_kind' lead/PENDING_DECISIONS.md lead/GOAL_THREE_TARGETS_20261018.md`；再 `grep -n '计数口径'` | 0 | `1 / 2`；命中 `:289` / `:6385` / `:9361` 均非 ③④ 裁决条目（§3(d) #17） |
| 8 | `git status --porcelain -- <5 只读域 + 2 台账 + 写域>`；末次 `python -I -X utf8 -B .../_mm_fp.py` 11 件重算；`find <5 只读域> -name '*.pyc' -newermt '2026-11-09 13:00'` | 0 | 只读域/台账仅会话开始即存在的 `MM`（2 件台账）与 `??`（5 目录）；末次 `ALL_MATCH = True COUNT = 11`；`PYC_COUNT=0`；未 commit/push（`git log -1` 未跑，标未验） |
| 9 | 末次 `python -I -X utf8 -B -c` 正则校验本件 22 条绑定行 + 禁用词族；同口径 `grep -nE` 禁用词族实跑 | 0 / grep 1 | `STRICT_LINES = 22 MALFORMED = 0`、`SECTIONS = 6`、`MISSING_TERMS = []`、`FORBIDDEN_HITS = 0`；`GREP_EXIT=1`（§6.2） |

### 6.4 未改任何件声明

- 本会话**未改** `_f2_r11plus.py`、`_f2_compare.py`、`_f2_compare_out.json`、任何既有件；
  5 个只读域与两件台账一律未修改/追加/覆盖。首末 `hashlib` 复核 11 件基线全等（`#1`、`#8`），
  `git status --porcelain` 对只读域只有会话前即存在的状态（`#8`）。
- 唯一写域 `lead/merged_contract_20261109/` 内本会话**新建 6 个文件**：本件 `MERGED_MERGE_CONTRACT.md`、
  `_mm_fp.py`、`_mm_fp_out.txt`、`_mm_probe.py`、`_mm_probe_out.txt`、`_mm_project_out.txt`
  （全部为交付件名或 `_mm_*` 前缀；末次 `python -I -X utf8 -B -c` 枚举 `NEW_FILES = 6`）。
  `__pycache__/_mm_cand.pyc` 为 `#4` 的编译产物，同在写域。
  上轮既有 `_mk_*` / `_mkv_*` 件本会话只读、未改。
- 零真机、零采样代码（探针只用 `hashlib/importlib.util/json/os/re/pathlib` 做只读装载与表达式级对跑）；
  不 commit、不 push；Python 一律 `python -I -X utf8`（部分 `-B`）+ 绝对路径；指纹用 `hashlib`。

### 6.5 未验项（如实标注，不以局部实跑冒充）

1. ③ 正式落地后端到端联调（`_f2_r11plus.py:303-305` 现盘仍空置）；本会话只跑写域候选副本与 30 件投影。
2. ①② 两处补丁本会话**未复跑**（只复核原件仍在）；上轮回归结果沿用其记载（`MERGED_MIN_SAFETY_PATCH.md:315-316`）。
3. 7 件形状断言回归（`_re_j4_cases.py` 19/19、`_re_run10_diff.py` 20/20、`_rev_core.py` 92/92 等，
   `MERGED_CONSUMER_AUDIT.md:197`）——**本会话未重跑，未验**。
4. 11 件下游消费者全量回放（本会话只跑 10 个表达式 §C + S4 对跑；`MERGED_CONSUMER_AUDIT.md:199` 要求零 TypeError/KeyError/无误读计数）——**未验**。
5. ④ 甲/乙/丙三方案**均未落地、均未跑真实新旧 JSON 双向兼容回放**；4(c) 为基于源码实读的结构推断，标「推算/未验」。
6. 门禁真正改接 plus 后的契约回归；候选 v1 的 `merged members=None` 补 SKIP 后的回归——**未验**。
7. `:100` 重写后 compare_out 3 件 + r11plus ≥8 件指纹锁、`_ow_raw_hits.json` fileMeta、3 份报告登记的重基线方式——**须所有者裁决，未验**。
8. `_f2v_run_out.json` 是否同步裁决、离线提示模式的 owner / SOP / 触发条件、run 快照落盘、判定书/台账登记——**未验**。
9. `git log -1` 未变未在本会话复跑；只读域 `__pycache__` 新增 `.pyc` 的归属（复核回件边界观察）本会话未做归因，标未验。
10. 复核 verdict = **partial**，本方案件整体标 **unconfirmed**；⑤ 的三处补正虽经本会话独立实跑确认，
    但**是否据此把复核翻为 confirmed 属编排方裁决范围**，本件不替裁决。

---

> **收束**：本件只出方案。合并契约（③）的 A/B/C 三处改前改后逐字、五项要求、`tier=SAMEDOC_LINK_EQ`、
> `不写 verified_path`、`problems 恒 []`、`members 全列`、三形态 rec 表、逐件消费者影响面均在 §3；
> 机读件 `totals` / `plus_path` / `plus_match` / **三态** / 向后兼容 / **须所有者裁决**均在 §4；
> 落地顺序与三情形在 §5；复核 partial 标 unconfirmed、绑定行、未改/未验在 §6。
> **④ 的甲/乙/丙取舍与上述所有未拍板点，须模板所有者裁决后方可落地。**
