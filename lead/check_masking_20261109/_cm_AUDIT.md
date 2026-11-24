# 坏输入注入审计回件 — check_d27 / check_d29 / check_d30

日期 2026-11-09 · 角色：坏输入注入审计员 · 零真机 / 零采样代码 / 绝对只读被审件 / 不 commit 不 push
唯一写域 `lead/check_masking_20261109/`，产出前缀 `_cm_`。

## 绑定行（被核对象 = 三件自检脚本各自独立指纹）

被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926

（上三行依次对应 check_d27.py / check_d29.py / check_d30.py；完整命令与输出见 §0、`_cm_injection_out.txt:6-9,155-158`。）

---

## §0 定位与结构核查

### (a) 三件的写域、大小、当前指纹（独立核对编排方）

实跑命令（本次，repo root）：

```
python -I -X utf8 -c "
import hashlib, os
rels = ['lead/d27_ruling_20261106/check_d27.py','lead/d29_ruling_20261106/check_d29.py','lead/d30_ruling_20261106/check_d30.py']
for r in rels:
    p = os.path.abspath(r); b = open(p,'rb').read()
    print(r); print('  bytes =', len(b)); print('  sha256 =', hashlib.sha256(b).hexdigest())
"
```

输出原文：

```
lead/d27_ruling_20261106/check_d27.py
  bytes = 3764
  sha256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c
lead/d29_ruling_20261106/check_d29.py
  bytes = 3906
  sha256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14
lead/d30_ruling_20261106/check_d30.py
  bytes = 3926
  sha256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd
```

三件都各自位于 `lead/dNN_ruling_20261106/`（裁决域），与编排方给出的 16 位前缀 `3b769d7c64c27251… / 2a50b09adff555db… / 6cb737963fc62a0e…` 一致。三件在 `lead/PENDING_DECISIONS.md:92,105,129` 被登记为「门禁 check_dNN.py 实跑 exit=0」，即它们的 PASS 是台账的承重证据。

四个背景指纹也独立核对通过（实跑 `python -I -X utf8 -c` 对候选集算 hashlib）：

```
MATCH goal bytes= 759518 sha256= 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede   lead\GOAL_THREE_TARGETS_20261018.md
MATCH head bytes= 52419 sha256= 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7   lead\PENDING_DECISIONS.md
MATCH maskDoc bytes= 45536 sha256= 2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f   lead\masking_effect_20261109\MASKING_EFFECT_AUDIT.md
MATCH meRep bytes= 33313 sha256= 7fb133c682e08af29b3de58bdd58819312a1d3036a07d7c5eb5ec0be5bf347ac   lead\masking_effect_20261109\_me_REPORT.md
```

### (b) 逐件结构：有无 SELF_TEST 汇总行？用 any()/all()/min() 哪一种？

实跑命令：

```
for f in lead/d27_ruling_20261106/check_d27.py lead/d29_ruling_20261106/check_d29.py lead/d30_ruling_20261106/check_d30.py; do echo "--- $f ---"; grep -n -E "SELF_TEST|any\(|all\(|min\(|max\(|sys\.exit|SystemExit|return [012]|PASS|FAIL" "$f"; done
```

输出原文（即编排方给的「三件自检结构抽取 = {}」的真实填充；编排方那一行是空对象，本会话独立补齐）：

```
--- lead/d27_ruling_20261106/check_d27.py ---
58:            print(f"FAIL [1] 文件缺失或不是普通文件: {path.as_posix()}")
59:        return 2
86:        if not any(keyword in body for body in bodies.get(title, [])
90:    count = len(REFERENCE.findall(ruling))
98:            print(f"FAIL {error}")
99:        return 1
100:    print(f"PASS: D-27 八项机械检查通过；裁决书引用 {count} 处")
101:    return 0
107:    sys.exit(main())
--- lead/d29_ruling_20261106/check_d29.py ---
83:                all(word in body for word in words) if require_all
84:                else any(word in body for word in words)
87:            if not any(matches):
90:        citations = re.findall(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+", ruling)
100:        print("FAIL (missing files)")
101:        return 2
103:        print("FAIL (content)")
104:        return 1
105:    print("PASS")
106:    return 0
110:    raise SystemExit(main())
--- lead/d30_ruling_20261106/check_d30.py ---
83:                all(word in body for word in words) if require_all
84:                else any(word in body for word in words)
87:            if not any(matches):
90:        citations = re.findall(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+", ruling)
100:        print("FAIL (missing files)")
101:        return 2
103:        print("FAIL (content)")
104:        return 1
105:    print("PASS")
106:    return 0
110:    raise SystemExit(main())
```

结论（三件一致）：

- **没有 `SELF_TEST` 汇总行**，也没有 `min()`。汇总就是末行 `print("PASS")`（d29/d30 `:105`）或 `print("PASS: …")`（d27 `:100`）+ `return 0` / `sys.exit(main())`。编排方的空 `{}` 不是「无结构」，而是三件都没有字面 `SELF_TEST` 记号；本任务用「PASS 行」当等价汇总位。
- **有 `any()`**：
  - d27 `check_d27.py:86-88`：`if not any(keyword in body for body in bodies.get(title, []) for keyword in keywords)` —— 词表 `keywords` 与 body 双重存在量词；第 6 项词表 `("外推","卡顿不存在")`（`:84`），第 4/5 项为单元素 `("循环论证",)` / `("本次不授权",)`（`:82-83`）。
  - d29 `check_d29.py:82-87`：内层 `all(...) if require_all else any(...)`，外层再 `if not any(matches)`。`require_all=False` 项是 `(4, "冲突是否成立", ("互斥","前提"))`（`:76`）；`require_all=True` 项是 `(5,"授权边界",("本次不授权",))` 与 `(6,"未背书",("口径 B","外推","191"))`（`:77-78`）。
  - d30 `check_d30.py:82-87`：与 d29 同构；`require_all=False` 项是 `(4,"三档权衡的实质",("93.98","误报率"))`（`:76`）；`True` 项为 `(5,("本次不授权",))`、`(6,("外推","栈采样"))`（`:77-78`）。
- **有 `all()`**：只在 d29/d30 的 `require_all=True` 分支；d27 没有。

### (c) 逐输入可归因 vs. k 输入压成 1 bit

三件都是「**逐项 append 到 errors/failures，末行压成单一 PASS/FAIL 布尔**」：

| 件 | 逐项累积 | 汇总 | 判定 |
|---|---|---|---|
| d27 | `errors.append(...)` ×8 项（`:58,67,70,74,79,88,92,94`） | `if errors: … return 1` / `print("PASS") return 0`（`:96-101`） | 每个检查项各自 append 一条错误文本 → **结构上逐检查项可归因**；但单个检查项内部的 k 个词被 `any()` 并成 1 bit |
| d29 | `failures.append(...)`（`:62,65,70,74,89,92,95`） | `if missing/failures … / print("PASS")`（`:97-106`） | 同上 |
| d30 | 与 d29 逐行同构 | 同上 | 同上 |

关键区分：**「逐检查项可归因」≠「逐输入可归因」**。
- 8 个机械检查（缺文件 / q1 / 标题 / [4] / [5] / [6] / 引用数 / selfBias）确实是逐项报错，报 FAIL 时会打印 `[4] …` / `[6] …` 这样的编号，这部分**是**逐项可归因的（本次 `_cm_injection_out.txt:57,113-115,123-124` 实证）。
- 但每个 `require_all=False` 检查项内部把 k≥2 个词用 `any()` 合成一个布尔：`covered = ∃w ∈ words: w in body`，然后只 append 一条「须包含 A 或 B」。**哪个词死了、哪个词活着，输出里完全没有**。这就是 k→1 bit 的有损压缩，与 `_rs_carrier_scan.py:229` 的 `any(n in txt …)`、`:343` `ok &= good`、`:346` `SELF_TEST = PASS` 同一形态（`lead/refsync_scope_20261109/_rs_carrier_scan.py:229,324-349` 本次直读）。
- `require_all=True` 分支内层是 `all(word in body …)`：删任一必需词都会让该项 FAIL，故对「词是否存活」是**敏感**的（本次 `and_kill_1` / `neg_ctrl_all` 实证，见 §1）。但它同样**不打印每个词的存活状态**，只是「整项 FAIL」。所以它是「逐项敏感、逐词不可见」。

依据：`check_d27.py:86-88`、`:96-101`；`check_d29.py:82-89`、`:97-106`；`check_d30.py:82-89`、`:97-106`；审计 `MASKING_EFFECT_AUDIT.md:331-335` 的抽象（本次直读 `:329-345`）。

### (d) 有没有哪一件其实已经是逐输入检查？

**逐检查项：有，三件都是**（errors/failures 列表逐项 append，FAIL 时逐条打印）。
**逐输入（词级）：没有，三件都不是**。三件各有一个 `require_all=False` 的 OR 词表（d27 `("外推","卡顿不存在")`、d29 `("互斥","前提")`、d30 `("93.98","误报率")`），全部是「任一词命中即过」。所以**没有一件能排除在同类风险之外**；三件都在 HIGH 名单里，与审计 `MASKING_EFFECT_AUDIT.md:309-311` 的直读判断一致。如实说：审计标的「HIGH 同类」成立，但成立的**位置**是词表 OR 项，不是整个脚本的所有检查项——`require_all=True` 项与缺文件/引用数/selfBias 项并不属于这个缺陷。

---

## §1 逐件注入坏输入（本任务核心）

### 注入方式（不改源文件一个字节）

驱动：`lead/check_masking_20261109/_cm_inject.py`（本写域新建，非被审件）。每个场景在写域内 `_cm_tmp/<tag>/<slug>/` 建全新沙箱，把 gate 脚本 + 两份输入文档**逐字节复制**进去，只对副本做替换，然后 `subprocess` 以 `cwd=沙箱` 跑 `<沙箱>/check_dNN.py`。
- d29/d30 用 `Path(__file__).resolve().parent`（`check_d29.py:50`、`check_d30.py:50`），副本同目录即命中。
- d27 用**CWD 相对** `DIRECTORY = Path("lead/d27_ruling_20261106")`（`check_d27.py:8`），故其沙箱内另建同名子目录放文档副本。第一次驱动漏了这点，6 个 d27 场景全给 `EXIT=2 / 文件缺失`，是**无效运行、已作废并重跑**，不作为结论依据。
- 哨兵：`TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`（保证零命中，与背景材料同串）。
- 两族注入：
  - **A 族（文档侧）**：把某个词从裁决书副本中删掉（换成哨兵），兄弟词保持存活 → 「一个输入失效、其它输入正常」。
  - **B 族（脚本侧参数/临时副本等价）**：把脚本副本里词表的一个字面量换成哨兵，其余 7 项检查一字不动 → `_rs_carrier_scan.py`「坏 needle」的抽象等价物。

实跑命令（本次，repo root）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cm_inject.py" > "D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cm_run_console.txt" 2>&1; echo "DRIVER_EXIT=$?"
```

输出（console 尾部）：

```
injected scenarios = 19
injected scenarios still EXIT=0 (PASS) = 14
DONE

[written] D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_injection_out.txt
DRIVER_EXIT=0
```

全量逐场景命令 + 输出原文见 `lead/check_masking_20261109/_cm_injection_out.txt:1-186`。基线（repo root 原样三件，未注入）也实跑过：

```
=== BASELINE d27 ===  PASS: D-27 八项机械检查通过；裁决书引用 71 处   EXIT=0
=== BASELINE d29 ===  PASS   EXIT=0
=== BASELINE d30 ===  PASS   EXIT=0
```

### (a)(b)(c) 三件逐件结果

#### check_d27 — 注入后**仍 PASS**

A 族（文档侧，杀 `未背书` 小节 OR 词表中的一个词）：

注入 1 —— 杀 `外推`，兄弟 `卡顿不存在` 存活（`_cm_injection_out.txt:20-25`）：

```
[d27] A: kill '外推' in 未背书, sibling '卡顿不存在' alive
  DOC RULING_D27.md: '外推' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x1; occurrences 3 -> 2; bytes 17658 -> 17686
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\a_kill_1\check_d27.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\a_kill_1
  EXIT = 0
  | PASS: D-27 八项机械检查通过；裁决书引用 71 处
```

注入 2 —— 杀 `卡顿不存在`，兄弟 `外推` 存活（`_cm_injection_out.txt:27-33`）：

```
[d27] A: kill '卡顿不存在' in 未背书, sibling '外推' alive
  DOC RULING_D27.md: '卡顿不存在' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x1; occurrences 1 -> 0; bytes 17658 -> 17677
  CMD = C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -I -X utf8 D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\a_kill_2\check_d27.py
  CWD = D:\Project\ra2-campaign-forge\lead\check_masking_20261109\_cm_tmp\d27\a_kill_2
  EXIT = 0
  | PASS: D-27 八项机械检查通过；裁决书引用 71 处
```

B 族（脚本副本词表换成坏针，`_cm_injection_out.txt:35-49`）：

```
[d27] B: script tuple -> ('外推', SENTINEL)
  SCRIPT check_d27.py: '"卡顿不存在"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3764 -> 3783; sha256 3b769d7c64c27251 -> f404f58783ab4da0
  CMD = ...\_cm_tmp\d27\b_kill_2\check_d27.py
  EXIT = 0
  | PASS: D-27 八项机械检查通过；裁决书引用 71 处

[d27] B: script tuple -> (SENTINEL, '卡顿不存在')
  SCRIPT check_d27.py: '"外推"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3764 -> 3792; sha256 3b769d7c64c27251 -> e7284d28098e72e7
  CMD = ...\_cm_tmp\d27\b_kill_1\check_d27.py
  EXIT = 0
  | PASS: D-27 八项机械检查通过；裁决书引用 71 处
```

★ 完整命令与输出原文（独立复跑，非驱动内嵌；`B: ('外推', SENTINEL)` 场景）：

```
$ python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cm_tmp/d27/b_kill_2/check_d27.py   (cwd=…/_cm_tmp/d27/b_kill_2)
PASS: D-27 八项机械检查通过；裁决书引用 71 处
EXIT=0
```

对照负控（证明驱动能出 FAIL，`_cm_injection_out.txt:52-57`）：杀掉单元素词表的 `循环论证` →

```
[d27] NEG-CONTROL: kill sole keyword '循环论证' of check [4]
  DOC RULING_D27.md: '循环论证' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x1; occurrences 1 -> 0; bytes 17658 -> 17680
  CMD = ...\_cm_tmp\d27\neg_ctrl\check_d27.py
  EXIT = 1
  | FAIL [4] 新证据是否成立小节正文须包含: 循环论证
```

⇒ **d27 是同族缺陷的第二个实证**（第一是 `_rs_carrier_scan.py`）：坏掉一根词针，八项机械检查照报「通过」，且引用计数仍是 71（输出完全不变，连可察觉的漂移都没有）。

#### check_d29 — 注入后**仍 PASS**

A 族（`_cm_injection_out.txt:68-81`）：

```
[d29] A: kill '前提' in 冲突是否成立, sibling '互斥' alive
  DOC RULING_D29.md: '前提' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x1; occurrences 2 -> 1; bytes 12258 -> 12286
  CMD = ...\_cm_tmp\d29\a_kill_1\check_d29.py
  EXIT = 0
  | PASS

[d29] A: kill ALL '互斥' in 冲突是否成立, sibling '前提' alive
  DOC RULING_D29.md: '互斥' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x99; occurrences 5 -> 0; bytes 12258 -> 12398
  CMD = ...\_cm_tmp\d29\a_kill_2\check_d29.py
  EXIT = 0
  | PASS
```

（第二例把全文 5 处 `互斥` 全杀光，只剩 `前提` 一根活针，仍 PASS —— 与 `_rs_carrier_scan.py` 单 N2 一根 6/6 PASS 完全同构。）

B 族（`_cm_injection_out.txt:84-97`）：

```
[d29] B: script tuple -> ('互斥', SENTINEL)
  SCRIPT check_d29.py: '"前提"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3906 -> 3934; sha256 2a50b09adff555db -> 2399e95a43eaafa4
  CMD = ...\_cm_tmp\d29\b_kill_2\check_d29.py
  EXIT = 0
  | PASS

[d29] B: script tuple -> (SENTINEL, '前提')
  SCRIPT check_d29.py: '"互斥"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3906 -> 3934; sha256 2a50b09adff555db -> 1648224881829853
  CMD = ...\_cm_tmp\d29\b_kill_1\check_d29.py
  EXIT = 0
  | PASS
```

★ 完整命令与输出原文（独立复跑）：

```
$ python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cm_tmp/d29/b_kill_2/check_d29.py   (cwd=…/_cm_tmp/d29/b_kill_2)
PASS
EXIT=0
```

对照负控 / AND 侧（`_cm_injection_out.txt:108-124`）：

```
[d29] NEG-CONTROL(all): kill ALL '191' -> AND-path must FAIL
  DOC RULING_D29.md: '191' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x99; occurrences 9 -> 0; bytes 12258 -> 12537
  EXIT = 1
  | [3] RULING_D29.md: missing section: :191 的适用边界
  | [6] Section 未背书: body must contain 口径 B AND 外推 AND 191
  | FAIL (content)

[d29] AND-extra: kill ALL '外推' (one of 3 required words)
  EXIT = 1
  | [6] Section 未背书: body must contain 口径 B AND 外推 AND 191
  | FAIL (content)
```

⇒ d29 的 `require_all=True`（AND）项**能**抓死词，但 `require_all=False`（OR）项抓不到；整体仍报 PASS 的坏输入场景共 5 个（含一个「只杀第 1 处 `191` 而正文仍有 8 处」的弱负控，如实标为「词未真正死、不算注入成功」，`_cm_injection_out.txt:100-105`）。

#### check_d30 — 注入后**仍 PASS**

A 族（`_cm_injection_out.txt:135-148`）：

```
[d30] A: kill ALL '93.98' in 三档权衡的实质, sibling '误报率' alive
  DOC RULING_D30.md: '93.98' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x99; occurrences 3 -> 0; bytes 13197 -> 13284
  CMD = ...\_cm_tmp\d30\a_kill_1\check_d30.py
  EXIT = 0
  | PASS

[d30] A: kill ALL '误报率' in 三档权衡的实质, sibling '93.98' alive
  DOC RULING_D30.md: '误报率' -> 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ' x99; occurrences 3 -> 0; bytes 13197 -> 13272
  CMD = ...\_cm_tmp\d30\a_kill_2\check_d30.py
  EXIT = 0
  | PASS
```

B 族（`_cm_injection_out.txt:151-164`）：

```
[d30] B: script tuple -> ('93.98', SENTINEL)
  SCRIPT check_d30.py: '"误报率"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3926 -> 3951; sha256 6cb737963fc62a0e -> b1670537e12a6d7c
  CMD = ...\_cm_tmp\d30\b_kill_2\check_d30.py
  EXIT = 0
  | PASS

[d30] B: script tuple -> (SENTINEL, '误报率')
  SCRIPT check_d30.py: '"93.98"' -> '"TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"'; occurrences 1 -> 0; bytes 3926 -> 3955; sha256 6cb737963fc62a0e -> 132685366f014171
  CMD = ...\_cm_tmp\d30\b_kill_1\check_d30.py
  EXIT = 0
  | PASS
```

★ 完整命令与输出原文（独立复跑）：

```
$ python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cm_tmp/d30/b_kill_2/check_d30.py   (cwd=…/_cm_tmp/d30/b_kill_2)
PASS
EXIT=0
```

对照负控 / AND 侧（`_cm_injection_out.txt:167-183`）：

```
[d30] NEG-CONTROL(all): kill ALL '栈采样' -> AND-path must FAIL
  EXIT = 1
  | [6] Section 未背书: body must contain 外推 AND 栈采样
  | FAIL (content)

[d30] AND-extra: kill ALL '外推' (one of 2 required words)
  EXIT = 1
  | [6] Section 未背书: body must contain 外推 AND 栈采样
  | FAIL (content)
```

### (d) 有没有比 _rs_carrier_scan.py 强的？

**没有一件在「坏输入仍 PASS」这一点上更强**。三件的 OR 项与 `_rs_carrier_scan.py` 同样压成 1 bit（本次 §1 三件 B 族全部 `EXIT=0`）。

但必须如实说出一处**局部更强**：d29/d30 的 `require_all=True` 分支是 `all(...)`（`check_d29.py:83`、`check_d30.py:83`），删掉任一词就会 FAIL（本次 `and_kill_1` / `neg_ctrl_all` 实证 `EXIT=1` 并打印 `AND` 词表），d27 的单元素词表项（[4]/[5]）同理（`neg_ctrl` 实证 `EXIT=1`）。这是「**逐项独立 append 到 failures**」带来的：一个 OR 项被掩蔽不会影响另一个 AND 项被抓到。而 `_rs_carrier_scan.py` 是把 6 条负控全塞进**同一个** `ok &= good`（`:343`），`SELF_TEST` 只有一根布尔。所以严格讲：三件是「8 个 1-bit 检查并列」，`_rs_carrier_scan.py` 是「1 个 1-bit 自检」；三件的粒度更好，但**目标 OR 项本身没有任何改进**，坏词依旧不可见。审计 `MASKING_EFFECT_AUDIT.md:343` 的「OR 改逐项报告」正对这一处。

### 第四件（计数用），本次独立复现

`_rs_carrier_scan.py` 声明「script NEVER writes a file」（`:7`，本次直读），且 `--needle` 为 `action="append"`（`:194`），故参数层坏针注入不违反只读铁律。实跑：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" --needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ" > "D:/Project/ra2-campaign-forge/lead/check_masking_20261109/_cm_rs_broken_out.txt" 2>&1; echo "EXIT=$?"
```

输出（`_cm_rs_broken_out.txt:8,10,40438-40445`）：

```
EXIT=0
needles = ['不能定位当年错误步骤', 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ']
scanned files = 6030 ; carrier occurrences = 8998 ; distinct files = 222
=== E. NEGATIVE-CONTROL SELF-TEST (R6) ===
  PASS  ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:123 want=ASSERTION        got=ASSERTION
  PASS  ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:25 want=ASSERTION        got=ASSERTION
  PASS  ledger_bound_20261109/LEDGER_BOUND_VOLUME.md:196 want=ASSERTION        got=ASSERTION
  PASS  ledger_bound_20261109/_lb_BOUND_VOLUME.md:129 want=ASSERTION        got=ASSERTION
  PASS  s604_verdict_entry_20261109/_ve_DRAFT_S609.md:22 want=REFUTING_QUOTE   got=REFUTING_QUOTE
  PASS  ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:215 want=ASSERTION        got=ASSERTION
SELF_TEST = PASS
```

（注意：`scanned files=6030 / carrier occurrences=8998` 与背景材料给的 `638 / 84` 不同 —— 那是当时语料；本次 `--root` 默认值指向更宽的树。这不影响结论：`SELF_TEST = PASS` 与 6/6 负控在坏针下依旧。此项如实登记为口径差，不冒充复现同一数字。）

---

## §2 共有缺陷模式

### (a) 四件中确有「k 输入压成 1 bit」的件数：**4 / 4**

| # | 对象 | 压缩点 | 本次实证 |
|---|---|---|---|
| 1 | `check_d27.py` | `:86-88` `any(keyword … for … for keyword in keywords)`，OR 词表 `("外推","卡顿不存在")` | B 族 2/2 `EXIT=0 PASS`，A 族 2/2 `EXIT=0 PASS` |
| 2 | `check_d29.py` | `:84` `any(word …)` + `:87` `if not any(matches)` 双层 OR，词表 `("互斥","前提")` | B 族 2/2、A 族 2/2 `EXIT=0 PASS` |
| 3 | `check_d30.py` | 同 d29，词表 `("93.98","误报率")` | B 族 2/2、A 族 2/2 `EXIT=0 PASS` |
| 4 | `_rs_carrier_scan.py` | `:229` `any(n in txt …)` / `:165` `min(pos)` / `:343` `ok &= good` / `:346` 单 `SELF_TEST` | 本次 `--needle …哨兵` → `EXIT=0 / SELF_TEST = PASS / 6/6` |

数字：**4 件**。限定语：四件的 OR/并集项都是 1 bit；d29/d30 另有 `all()` 的 AND 项、d27 另有 6 个单输入项，这些**不**属于该缺陷，但也没能阻止整体 PASS。

### (b) 抽象描述（便于以后识别）

> 设一个自检有 k≥2 个同类输入（needle / pattern / keyword / token / case），内部用**存在量词**合成：`covered(x) = ∃i: match(input_i, x)`；随后把这 k 个输入的存活情况压成**一个布尔**（`ok &= good` / `if not any(...)` / `print("PASS")`）。
> 于是 `PASS` 的可达世界里必然包含「`input_1` 完全失效、但每个样本都被某个 `input_{j≠1}` 命中」，与「k 根全正常」**观测等价**。
> 缺陷不在 `match` 实现，而在**从 k 个输入到 1 bit 的有损压缩**：待证命题是 ∀i 有效，观测量只有 ∃i 命中，且不保留 `i` 的溯源（`hits=[…]`）。
> 判据式（抄 `MASKING_EFFECT_AUDIT.md:331-335` 并本次直读复核）：`DISTINGUISHABLE_PASS = AND_k( per_input_SELF_TEST_k )`；`EXCLUSIVE / HITSET / MASKED_LINES` 只作诊断，不替代 `AND_k`（审计 `:160-176,335` 的复核 `partial` 教训）。

对 d27/d29/d30 的具体化：`k=2` 的词表 OR；对 `_rs_carrier_scan.py`：`k=2` 的 needle 并集 + 6 条负控单布尔。

### (c) ★ 30 秒最小判据

拿到任何自检脚本，按序做 4 步（每步都是 `grep` 级，不用跑全库）：

1. **找输入表**（5 秒）：`grep -n -E "needle|keywords|words|TOKENS|REQUIRED|PATTERN|--[a-z-]+" <script>` —— 有没有长度 ≥2 的字面量元组 / `action="append"` / 可重复 CLI flag？有 → 记 k，进第 2 步；没有 → 不是本类。
2. **找量词**（10 秒）：`grep -n -E "any\(|all\(|min\(|\|=|&=" <script>` —— 只要出现 `any(...)` 把多个输入并成一个布尔，或 `ok &= ...` / `min(...)` 丢掉 argmin，就标红。`all()` 对本类**不**红（它逐项敏感），但仍不打印逐词存活状态。
3. **找汇总出口**（10 秒）：`grep -n -E "SELF_TEST|PASS|FAIL|return 0|sys.exit" <script>` —— 若输出只有**一行** PASS/FAIL（或 `SELF_TEST = X` 一根布尔），且没有 `for i, inp in enumerate(inputs): print(i, …)` 之类的逐输入行，即「k→1 bit」成立。
4. **一针验证**（5 秒，可选但决定性）：把**一根**输入换成保证零命中的哨兵（脚本副本 / CLI 参数层，绝不改源），重跑。`EXIT` 仍 0 / 仍 `PASS` ⇒ 确诊；变 FAIL ⇒ 该件有 `AND_k` 或 `all()` 兜住，不是本类。

判据一句话：**「多输入表 + `any()`/`ok&=`/`min()` + 单行 PASS 出口」三项齐 ⇒ 本类；坏针注入仍 PASS ⇒ 实证。**
本次四件全部三项齐（三 gate：`:81-88/:76-89` + `:100/:105`；扫描器 `:165/:229/:343/:346`），且全部经第 4 步实证仍 PASS。

### (d) 修复优先级

**第一优先：`_rs_carrier_scan.py`**（最该先修）。理由（均有本次或审计内证据）：
- 它是四件里**唯一已被当作交付口径证据**写进修复登记的一件：审计 `MASKING_EFFECT_AUDIT.md:109-110,381`（本次直读 `:98-110,375-386`）指出 `REFSYNC_SCOPE_FIX.md:251` 把 `SELF_TEST = PASS` 当作「载体扫描口径已修正、6 条负控都覆盖」的交付证据，判为 **high 且不可信**；`_nn_REPORT.md:402` 自认下一轮才发现。
- 它的压缩最彻底：6 条负控 → 1 个 `ok`（`:343`），连「哪个负控挂了」都要靠逐行文本才看得见；还叠加 `:165` `min(pos)` 的**反向掩蔽**（审计 `:148`：加一根 needle 能把 PASS 变 FAIL，role 不单调），是四件里唯一有位置依赖风险的。
- 修复方案已被复核确认可用（审计 `:172-195` 的甲'/乙'/丙' 四场景矩阵 `ALL_SCENARIOS_MATCH_EXPECTATION = True`），可直接落地。

**第二优先：`check_d27.py`** —— 它的 OR 词表在 `未背书` 小节，而 `未背书` 是裁决书的「诚实账/授权边界」承重段；且 d27 的输出带「八项机械检查通过；引用 71 处」，措辞最像「全项已验」，最易被误读为逐项可归因（本次 `a_kill_2` 杀光 `卡顿不存在` 后输出**一字不变**）。此外 d27 用 CWD 相对路径（`:8`），换目录就 EXIT=2，属额外脆弱性（本次第一次驱动踩到）。

**第三/第四：`check_d29.py` ≈ `check_d30.py`** —— 两件逐行同构（`:76-89`、`:97-106`），改动可一次套用两份；它们比 d27 多一层 `all()` 兜底，但 OR 项同样中招。三件都在 `lead/PENDING_DECISIONS.md:92,105,129` 挂着「门禁 exit=0」的台账登记，故**三件都该修**，只是先后按「承重程度 + 压缩彻底度」排。

---

## §3 一次性修复方案

### (a) 三套方案能否一套通吃四件？

**能，但只有「甲'（逐输入独立跑自检 + `AND_k`）」能通吃，且必须按审计 §4.1 的修正版，不能用撰写人原版乙/丙。**

审计给的判据（本次直读 `MASKING_EFFECT_AUDIT.md:156-195`）：
- `:160` 复核人实跑证明撰写人原方案乙/丙（含「推荐」的丙）在「交付的双针掩蔽 PASS」上仍报 `COVERAGE_GATE=PASS`，`PLAN_C` 的 `PER_NEEDLE_SELFTEST` 是**误称**（只由语料独占行数推出，从不跑自检）→ 三方案「均能区分」不成立，verdict=partial。
- `:172` **唯一被复核确认能抓的核心 = 甲（逐 needle 独立跑自检 + `AND_k`）**。
- `:176` 修正版统一 GATE：`AGGREGATE = AND_k( REAL per-input self-test )`，`HITSET / MASKED_LINES / EXCLUSIVE / EXCLUSIVE_CONTROLS` 一律只报告、不门禁；`PER_NEEDLE_SELFTEST` 必须来自真实 k 次运行。
- `:186-195` 四场景矩阵 S1–S4 全中（甲'/乙'/丙' 均 FAIL/FAIL/PASS/FAIL，`ALL_SCENARIOS_MATCH_EXPECTATION = True`）。

甲' 为什么能通吃四件：它是**外部外壳**，不要求被审脚本有 `SELF_TEST` 字样、不要求它们是 CLI 多输入、也不依赖 `min(pos)`。对四件分别定义「单输入运行」即可：
- `_rs_carrier_scan.py`：`for n in needles: 跑 --needle n`，要求 `EXIT=0 ∧ 6 条负控逐条匹配 WANT`（审计 `:176` 已如此）。
- `check_d27/29/30.py`：`for w in OR词表: 用只含 w 的词表跑一次该检查项`（脚本副本/参数层，或等价地在同一脚本内把 `any()` 换成逐词循环），要求该项 `EXIT=0`；`AGGREGATE = AND_k`。
- 本次 §1 的 B 族注入正是甲' 的 S4 场景：把一根换成哨兵，单跑必 FAIL（`_cm_injection_out.txt:37,45,85,93,152,160` 的 `occurrences 1 -> 0`），`AND_k` 就会把整体判 FAIL —— 而现行四件全放过了。

### (b) 差异在哪（若不能朴素一套通吃）

甲' 的**原则**能通吃，但**适配器不能一行通吃**，差异有 4 点：

1. **输入来源不同**：`_rs_carrier_scan.py` 的输入是 CLI `--needle`（`:194` `action="append"`，参数层可注入）；三个 gate 的输入是**源码内硬编码字面量元组**（`check_d27.py:81-85`、`check_d29.py:75-79`、`check_d30.py:75-79`），且脚本本身不接受任何 CLI 参数。→ 三 gate 若坚持「不改被审脚本」，只能在**临时副本**里替换字面量（本次 `_cm_inject.py` 的 B 族就是这个适配器）；若要内嵌修复，则必须改源码（本任务铁律禁止，留给后续轮次）。
2. **k 的语义不同**：扫描器 k=2 是「同一判定函数的并列 needle」，且 `min(pos)` 让角色非单调（审计 `:148,335`）；三 gate 的 k=2 是「同一小节的 OR 关键词」，与位置无关，没有反向掩蔽。→ `HITSET`/`EXCLUSIVE` 诊断量对扫描器有意义，对三 gate 基本无意义；三 gate 只需要「逐词命中数」。
3. **汇总出口不同**：扫描器有字面 `SELF_TEST = PASS/FAIL`（`:346`）且 `return 0 if ok else 1`（`:349`）；三 gate 只有 `print("PASS")` + `return 0`（`:100-101` / `:105-106`），FAIL 时是 `errors/failures` 列表逐条打印。→ 外壳解析规则不同：一个抓 `SELF_TEST` 行，一个抓 `EXIT` + 逐条 `[n]` 行。
4. **AND 项的处理**：d29/d30 已有 `require_all=True` 的 `all()` 项（`:83`），单跑一个词时会天然 FAIL（本次 `and_kill_1` 实证），所以「逐词独立跑整个脚本」对 AND 项会**误伤**。→ 甲' 的门禁必须**只针对 OR 项**（`require_all=False` 的那一项）做 `AND_k`，AND 项保持原样整项跑；否则 k=1 时平凡失败（与审计 `:195` S3 `EXCLUSIVE_CONTROLS=[0,0]` 却该 PASS 的教训同类）。这是三 gate 独有、`_rs_carrier_scan.py` 没有的差异。

结论：**甲' 是唯一通吃的门禁原则（本次直读审计 `:172,176,339-343`）；乙（独占负控）/丙（命中溯源台账）只能当诊断层**。原版乙/丙已被复核 `partial` 否掉（`:160`），修正版乙'/丙'（`:181-182`）虽有 `AND_k` 但改动量大且仍带输出破坏，不是「一次性最小修复」。

### (c) ★ 通用「坏针注入自检」补丁模板（可粘贴）

下面模板是**外部外壳**，不改被审脚本一个字节；`run_once` / `mutate_input_i` 按脚本形态替换即可。它同时适用于 CLI 多输入（扫描器）与硬编码字面量（三 gate，走临时副本）。

```python
# bad_input_selftest.py —— 通用「坏针注入自检」外壳甲'（零侵入）
# 用法：python -I -X utf8 bad_input_selftest.py
# 只依赖：被审脚本的「单输入运行」能给出可解析的 PASS/FAIL + 逐条 want/got。
import hashlib, shutil, subprocess, sys, tempfile
from pathlib import Path

SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"   # 保证零命中

def run_once(inputs, workdir):
    """返回 (exit, lines)。按脚本形态二选一实现：
       (a) CLI 多输入：cmd = [sys.executable,'-I','-X','utf8',SCRIPT]
                       + sum([['--needle', x] for x in inputs], [])
       (b) 硬编码词表：在 workdir 建脚本副本，把词表字面量替换为 inputs，再跑副本
       禁止写回源文件；所有写入限制在 workdir。"""
    raise NotImplementedError

def parse(lines):
    """按脚本形态返回 (aggregate_pass, controls)：
       扫描器：aggregate = 'SELF_TEST = PASS' in lines
               controls  = 6 行 'PASS … want=… got=…' 逐条比对 WANT 表
       三 gate：aggregate = (exit == 0)
               controls  = 目标检查项 [n] 未出现在 failures 中
       逐条 want/got 必须逐行比对，不能只看总布尔。"""
    raise NotImplementedError

def real_per_input_selftest(inputs, workdir):
    """甲' 核心：每根输入单独跑未修改被审脚本，AND_k 才给 PASS。
       HITSET / EXCLUSIVE / MASKED_LINES 只打印，不参与门禁。"""
    per = []
    for i, x in enumerate(inputs):
        rc, lines = run_once([x], workdir)          # 单输入，不是并集
        ok, controls = parse(lines)
        per.append(ok and rc == 0 and all(controls))
        print(f"  input[{i}] = {x!r}: SELF_TEST={'PASS' if per[-1] else 'FAIL'}"
              f" controls={sum(controls)}/{len(controls)}")
    return all(per)                                  # AGGREGATE = AND_k

def bad_needle_injection(inputs, workdir):
    """坏针注入：依次把第 i 根换成哨兵，要求 AGGREGATE 变 FAIL。
       这是本次四件全部通不过、补丁必须通过的判据。"""
    results = []
    for i in range(len(inputs)):
        broken = list(inputs)
        broken[i] = SENTINEL
        rc, lines = run_once(broken, workdir)
        ok, _ = parse(lines)
        # 关键：不能只信 aggregate（它正是被掩蔽的那个布尔）
        caught = (rc != 0) or (not ok)
        results.append(caught)
        print(f"  broken[{i}] -> {SENTINEL}: caught={caught}  (rc={rc})")
    return all(results)                              # 每根坏针都必须被抓

def main():
    inputs = [...]            # 填：needles / OR 词表；k>=2
    with tempfile.TemporaryDirectory() as workdir:
        base_rc, base_lines = run_once(inputs, workdir)
        base_ok, _ = parse(base_lines)
        agg   = real_per_input_selftest(inputs, workdir)
        inj   = bad_needle_injection(inputs, workdir)
        print(f"BASE_PASS={base_ok}  AND_k={agg}  BAD_NEEDLE_CAUGHT={inj}")
        verdict = base_ok and agg and inj
        print("DISTINGUISHABLE_PASS =", verdict)
        return 0 if verdict else 1

if __name__ == "__main__":
    sys.exit(main())
```

配套三 gate 的最小内嵌改法（**仅作为后续轮次的建议，本任务未执行**）：把 `check_d29.py:82-89` / `check_d30.py:82-89` 的

```python
matches = [all(...) if require_all else any(...) for body in bodies]
if not any(matches): failures.append(...)
```

改成逐词循环并打印存活状态（对应审计 `:343` 第 5 条）：

```python
for w in words:
    hit = any(w in body for body in bodies)
    print(f"  [{number}] word {w!r}: {'HIT' if hit else 'DEAD'}")
    if require_all and not hit:
        failures.append(f"[{number}] Section {title}: missing word {w!r}")
if not require_all and not any(any(w in body for body in bodies) for w in words):
    failures.append(...)   # 保留原 OR 语义，但 DEAD 词已可见
```

再叠加上面的坏针注入外壳做 `AND_k` 门禁 —— 二者缺一不可：只打印逐词状态是「可见但不门禁」，只做 `AND_k` 是「门禁但不溯源」。审计 `:339-343` 六条原则里第 1、3、4、5 条正对应这四点。

### (d) 落地成本估计

| 方案 | 行数量级 | 对既有输出的破坏性 | 依据（本次直读） |
|---|---|---|---|
| **甲' 外部外壳（推荐）** | 外壳 ~15–25 行；被审脚本 **0 行** | **完全不破坏**：每次单跑输出仍是原格式，只多一层 `AND_k` 汇总；既有 `_fix_*.txt` / 台账 `exit=0` 解析不变 | 审计 `MASKING_EFFECT_AUDIT.md:180`（本次直读 `:178-184`） |
| 逐词打印（内嵌，三 gate 专用） | 每 gate ~5–10 行（把 `any` 换 for 循环 + 一行 print） | **弱破坏**：新增 `word …: HIT/DEAD` 行；PASS 行与 FAIL 编号不变 | 类比审计 `:181` 乙'；本次三 gate `:82-89` 结构 |
| 乙'（逐针负控表） | 0 行（外部预计算）或内嵌 ~20–30 行 | **弱破坏**：新增 `PER_NEEDLE` 行，A–E 段不变 | 审计 `:181` |
| 丙'（溯源台账） | ~30–50 行 | **中等破坏**：A 段每 carrier 多 `hits=`、新增 F 段；`SELF_TEST` 语义扩为「负控全过 ∧ 逐针自检全过」，**旧 PASS 可能变 FAIL**（这正是目的） | 审计 `:182` |
| 三 gate 合计（内嵌版） | 3 × ~10 行 + 共用外壳 ~25 行 ≈ **55 行级** | 弱；但需在 3 处源码改动（本任务未做） | 本次 `check_d27.py:81-88`、`check_d29.py:75-89`、`check_d30.py:75-89` |

另需 ~10 行绑定语料/脚本指纹（`hashlib.sha256`，审计 `:345` 第 7 条），防并行写入让计数漂移被误读为「测试变好」——本次 `_rs_carrier_scan.py` 复跑得 `6030/8998`、背景材料为 `638/84`，正是这种口径差的实例，如实登记。

---

## §4 结论与边界

### (a) 三件最终定性

| 件 | 定性 | 依据 |
|---|---|---|
| `check_d27.py` | **有缺陷**（HIGH，同族） | `check_d27.py:86-88` OR 词表压 1 bit；本次 A 族 2/2 + B 族 2/2 全 `EXIT=0 PASS`，杀光 `卡顿不存在` 后输出一字不变（`_cm_injection_out.txt:20-49`） |
| `check_d29.py` | **有缺陷**（HIGH，同族） | `check_d29.py:82-89` 双层 OR；本次 A 族 2/2 + B 族 2/2 全 `EXIT=0 PASS`（`:68-97`） |
| `check_d30.py` | **有缺陷**（HIGH，同族） | `check_d30.py:82-89` 与 d29 同构；本次 A 族 2/2 + B 族 2/2 全 `EXIT=0 PASS`（`:135-164`） |

三件**都不是「无缺陷」，也都不是「判不了」**：注入执行了、输出拿到了、源指纹前后一致（见 §5）。局部如实补充：三件的 `require_all=True` / 单元素词表项 / 缺文件 / 引用数 / selfBias 项**不**属此缺陷，且本次实证能出 FAIL（`neg_ctrl`、`neg_ctrl_all`、`and_kill_1`）。

### (b) 三件都是同类缺陷说明什么

1. **不是孤例，是模板复用**：d29 与 d30 逐行同构（`:76-89`、`:97-106` 完全相同，只换词表与标题），d27 是同一模式的早期版本（`:81-88`）。加上 `_rs_carrier_scan.py` 的 `any`+`min`+单布尔，四件跨 3 个不同写域、不同作者轮次，说明「多输入并集 + 单行 PASS」是本项目**默认的自检写法**，而非某次手误。审计 `MASKING_EFFECT_AUDIT.md:296-302` 的有界扫描也给出 `B (any()/min() over multiple inputs) = 1436` 处命中（本次直读 `:286-302`）——虽是正则计数、非逐文件执行，但与本结论方向一致（如实标：未逐个实跑，标未验）。
2. **台账里的 `exit=0` 不能当「逐项已验」读**：`lead/PENDING_DECISIONS.md:92,105,129` 三处都把「门禁 exit=0」写成裁决交付的证据。本次证明这 3 个 `exit=0` 与「OR 词表里有一根死词」**观测等价**。按审计 `:110` 引用的铁律「若某处通过是被掩蔽的，即使结果碰巧正确，也必须标为不可信」，这三处登记的 PASS 应标**不可信/待重跑**，而不是「结果碰巧对就算了」。
3. **项目自检质量的系统性问题**：自检普遍只验「文档在不在/有没有某串」，不验「每个判据输入是否存活」；没有 per-input 溯源、没有坏针注入、没有语料/脚本指纹绑定。审计 `:338-345` 的 7 条原则在本项目基本都没落地。四件里 `tools/verify_kit/boundary_scan.py` 被审计判为「相对最好」（`:316`，有 per-token `HIT … token=%s` 打印），但也**没有** per-token 覆盖度门禁 —— 即全项目连「可见」都少见，更别说「门禁」。

### (c) 这条审计判不了什么（如实列）

1. **判不了裁决书内容本身对不对**：只验格式/词表命中，不验 D-27/D-29/D-30 的事实与推理（三件 docstring 都自称 "format gate"，`check_d27.py:1`、`check_d29.py:1`、`check_d30.py:1`）。
2. **判不了「真实历史上是否真有死词」**：本次是**主动注入**坏词，不是发现现有词表里已有死词。三件的词在原始文档里都实际命中（本次 `python -I -X utf8 -c` 逐词计数：d27 `外推=3 / 卡顿不存在=1`、d29 `互斥=5 / 前提=2`、d30 `93.98=3 / 误报率=3`，且 section 体内各词均命中），所以**本次结果碰巧是对的**（审计 `:211` 同款措辞）。判的是「PASS 不可信」，不是「结论错了」。
3. **判不了其它未点名脚本**：审计 §5.2 表里的 `_gp_regression.py` / `_g7_predicates.py` / `_n13v_independent.py` / `_v12_rule.py` / `boundary_scan.py` / `snapshot.py` 等，本次**未注入、未实跑**，一律标未验；审计自己也在 `:404-405` 声明 `_v12_rule.py` 词表存活率与其它 HIGH/MEDIUM 脚本坏针注入未做。
4. **判不了修复后的效果**：本任务铁律「只做注入审计，不改任何被审脚本」，故 §3 的模板**未在三件上落地、未跑修复后的回归**。甲' 四场景矩阵是**审计件内**的实跑结论（`MASKING_EFFECT_AUDIT.md:186-195`，本次只直读、未复跑），不是本次的实跑。
5. **判不了 `_rs_carrier_scan.py` 的当时数字**：本次复跑 `scanned files=6030 / carrier occurrences=8998 / distinct files=222`，与背景/审计里的 `638 / 84 / 20` 不同（语料与 `--root` 口径差）；只能判「坏针仍 `SELF_TEST=PASS`」这一性质，不能冒充复现了同一组数字。
6. **判不了 d27 CWD 依赖是否算 bug**：第一次驱动的 6 个 d27 场景因 `check_d27.py:8` 的 CWD 相对路径全部 `EXIT=2`，已作废重跑；这是本次踩到的口径坑，未作为被审缺陷定性（它属于「跑法」而非「k→1 bit」）。
7. **判不了 `require_all=True` 项是否也有 1-bit 问题**：本次只证它们对「整词删光」敏感（`EXIT=1`），未证它们会打印逐词存活状态（事实上不打印）。要判「逐输入可归因」仍需逐词报告改造。

### (d) 以后写自检脚本「必做」清单

1. **列输入、报 k**：开头显式列出全部 k 个输入（needle/词表/case），打印 `k=` 与每个 `input[i]`，别让输入藏在生成器里。
2. **禁止裸 `any()` 当门禁**：`any()` 只能用于「判定」，不能直接接 `PASS`；`require_all=False` 也要逐词打印 `word …: HIT/DEAD`（审计 `:343`）。
3. **`AND_k` 真实逐输入自检**：每根单独跑一次未修改被审件，要求 `EXIT=0` + 逐条 `want/got` 全匹配；`AGGREGATE = AND_k`，`PER_INPUT_SELFTEST` 必须来自真实 k 次运行，**不得由语料独占行数推断**（审计 `:160,176` 的 `partial` 教训）。
4. **保留溯源**：每个命中记 `hits=[命中输入下标]`，把「并集覆盖」与「逐根覆盖」分开算（审计 `:341`）。
5. **坏针注入自检**：k 次把第 i 根换成保证零命中的哨兵，每次要求整体变 FAIL；抓不到就是本类缺陷（审计 `:342`、本次 §1 全部放过 = 反例）。
6. **门禁/诊断分离**：`EXCLUSIVE / EXCLUSIVE_CONTROLS / MASKED_LINES / HITSET` 只报告，绝不替代 `AND_k`（审计 `:335,340,393`）。
7. **固定语料 + 脚本指纹**：报 PASS 时绑定输入语料 SHA256 + 文件数 + 被审脚本 SHA256（用 `hashlib`），防漂移误读（审计 `:345`；本次 §0 已对三件这么做）。
8. **单调性声明**：明确「scanned 单调」不等于「role/needs_fix 单调」；凡用 `min(pos)` / `argmin` 的判定，改成每根独立求角色再按明确规则合并（审计 `:344,335`①）。
9. **别把 `exit=0` 直接写进台账当「逐项已验」**：登记时附「逐输入 PASS 表 + 指纹」，否则下一轮无法区分真通过与掩蔽通过（`lead/PENDING_DECISIONS.md:92,105,129` 是本次的反面教材）。

---

## §5 纪律自证

- **零真机 / 零采样代码**：全程只跑 `python -I -X utf8` 读文本 + `subprocess` 跑纯文本检查脚本；未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 动态内存解析。
- **绝对只读被审件**：三件脚本与 6 份输入文档、掩蔽审计域、`_rs_carrier_scan.py` 全程只读。源指纹前后一致（本次实跑 `_cm_injection_out.txt:6-9` vs `:155-158`，以及末次独立复核）：

```
3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c 3764 lead/d27_ruling_20261106/check_d27.py
2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14 3906 lead/d29_ruling_20261106/check_d29.py
6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd 3926 lead/d30_ruling_20261106/check_d30.py
```

  掩蔽域四件复核：`MASKING_EFFECT_AUDIT.md 45536 / 2f55283e…`、`_me_REPORT.md 33313 / 7fb133c6…`、`_rs_carrier_scan.py 16053 / 9ccca808…`、`GOAL_THREE_TARGETS 759518 / 2baa0de4…`、`PENDING_DECISIONS 52419 / 3765eddb…`（均本次实跑 hashlib）。
- **唯一写域**：所有新建件都在 `lead/check_masking_20261109/`：`_cm_inject.py`、`_cm_injection_out.txt`、`_cm_run_console.txt`、`_cm_rs_broken_out.txt`、`_cm_tmp/` 沙箱，以及本回件。
- **不 commit / 不 push**：未执行任何 git 写操作。
- **注入只在参数层 / 临时副本**：B 族改的是 `_cm_tmp/` 里的脚本副本，A 族改的是 `_cm_tmp/` 里的文档副本；源文件零字节改动。
- **第一次驱动作废声明**：初次运行 d27 六场景因 CWD 相对路径给 `EXIT=2 文件缺失`，是无效运行，已修正驱动重跑，结论只取 `_cm_injection_out.txt`（第二次）与末次独立复跑。
