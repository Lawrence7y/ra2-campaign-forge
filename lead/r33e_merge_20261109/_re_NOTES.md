# _re_NOTES.md — J4 并入版（R3-3e 候选）使用约束与纪律

**日期**：2026-11-09　**撰写**：J4 并入员（独立上下文）
**并入实现**：`lead/r33e_merge_20261109/_re_linked.py`（新件，本写域）

被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481

（上行 = 本会话 hashlib 对 `_re_linked.py` 全字节实算的复核回件绑定行；命令 = `python -I -X utf8 -c` 读全文件算 sha256/len。本件此后若再改动不影响该绑定行所指对象。）

**被并入原件**：`lead/samedoc_link_20261109/_sl_link.py`（只读，本任务全程零改动）
**判据来源**：`lead/equiv_class_20261109/_eq_criteria.md` §5.1（伪代码）+ `_eq_proto.py:50-92`（原型实跑）
**回归证据**：`_re_struct_diff_out.json`（结构白名单）、`_re_run10_out.json`（十条双跑逐条比对）、`_re_j4_out.json`（四类 J4 案例 + 正反控制）

---

## 1 merged 是什么（一句话）

`verdict="merged"` = 「同文档内存在溯源声明背书的逐字节同值副本群」——multi 分支的后验精化，
只在三条件**同时**满足时出现，否则维持 multi 原样（输出与原实现逐字节一致）：

- (i) 行 L 命中封闭集 `DECL_RE = /复制自|复制为|COPY_IDENTICAL\s*=\s*True/`（**禁扩**——
  刻意排除「逐字节同一/相同」等纯等同词，Q4_RELATION.md:85/:168 真实反例：纯等同词会把
  「不同趟次证据件恰好同哈希」的发现性表述误当复制声明）；
- (ii) ≥2 个 multi 成员的锚定 token 行号含 L（行号取自 anchors 记录，每 token 至多前 4 行，同原实现）；
- (iii) 各命中行覆盖成员的并集 == 全体 multi 成员（**全或无**，不部分合并）。

unique / zero / invalid_hex 一律不介入（unique 不因等价类降级；zero 无类可并）。
problems 恒为 `[]`——merged 仍是 warning 级，不升级 problem。

## 2 三条纪律的落地位置（缺一不可）

### (a) path=None，不做单一对象主张 —— 体现处
1. `link()`：merged 时 `out["reverify"]` **恒为 None**（unique 才有 reverify 单对象回验）；
   J4 块不写任何 `path=`/`verified_path=` 单对象字段（`_re_linked.py` J4 块注释「★ merged 三纪律」）。
2. `link_triple()`：merged rec 的 `rec["path"]` 保持初始 None，**不写**
   `verified_path` / `recomputed` / `bytes`（unique 专属字段）；回归断言
   `triple_t3_merged_shape` 已验证（`_re_run10_out.json` assertions）。
3. 单对象信息的唯一去处 = `members` 列表（见 (c)）。

### (b) 禁止从 merged 推导授权结论 —— 写在四处
1. `_re_linked.py` 模块 docstring【merged 三纪律 2】；
2. `_re_linked.py` J4 并入块注释（link() 内）；
3. `_re_linked.py` `link_triple()` merged 分支注释；
4. merged 的 `warning` 文本本身（每个 merged 输出都自带这句）：
   「未做单一对象主张（path=None），角色归属留人工判定，禁止由 merged 推导任何授权结论」。
**语义**：merged ≠ 放行 ≠ 锚定；隔离副本集成通过 ≠ 母本可写（RULING_D25:26，
`_integ_INTEGRATION_REPORT.md:59` 实读在案）。内容层无假 MATCH 风险（hash 同即字节同），
风险全在角色层——角色/授权主张只许人工从 members 自行辨认，禁止自动化消费。

### (c) members 全列 —— 格式
```json
"members": [{"path": "<现盘解析绝对路径>", "sha": "<64 位小写 hex 全量>", "bytes": <int>}, ...]
```
- 两处同形：`out["eq"]["members"]` 与 `link_triple` 的 `rec["members"]`；
- 取**全量** matches，不做 `max_detail` 截断（anchors 仍按原实现截断显示，members 不截）；
- merged 的 `decl_lines`（行号列表）与 `eq.decl_hits[].text`（声明行原文，strip 后全量）同记，
  供人工实读声明行原文（判据 §5.3-1）。

## 3 若接入 r11_scan_plus 需要适配什么

接入点：`_f2_r11plus.py:303-305` 的 else 分支（T1/T2/T2N/T3 全落空、现产 R3-3b 警告处）。
在该分支调用 `link_triple(text, doc_dir, declared, bytes_decl, root)` 并合并 rec。适配清单：
1. **tier 枚举扩展**：新值 `SAMEDOC_LINK_EQ`（merged 专用）。下游若对 tier 值集封闭
   （None/T1/T2/T2N/T3/SAMEDOC_LINK），必须显式加分支；`tier=SAMEDOC_LINK_EQ` 且
   `path=None` 是合法组合，不得当异常。
2. **path=None 形态适配**：merged 的 rec 无 `verified_path`/`recomputed`/`bytes`——
   消费方若假设「match=True ⇒ 有单一 path」会 KeyError/误读；必须走 members。
3. **problems 契约不变**：联查恒不产 problem，只需把返回 warnings 并入 r11 的 warnings。
4. **hash 重算复用（可选）**：link() 内部自读盘算 sha256；r11 已有 `recompute` 闭包，
   如要避免重复 IO 需给 link() 加 recompute 注入参数——语义不变，纯优化。
5. **merged 事件逐次记档**（判据 §5.2）：每次 merged 落 run 机读件
   `{binding_hex, bytes_decl, members, decl_lines, decl_text}`——等价类是联查时刻快照
   （TOCTOU 同限），事后审计需要当时成员与声明行。
6. **判定书登记**（判据 §5.2）：J4 是对 SAMEDOC_LINK.md:20 ★4「唯一命中才采」的显式修订
   （multi 不再无条件放弃，改「声明解析 → merged｜multi」），并入台账时必须写明修订关系，
   不能无声替换。

## 4 禁止事项（继承 + 新增）

- 声明词组封闭集禁扩（漏词 = 漏闭合，安全方向；扩词 = 误并风险，判据 §7-6）；
- 禁止改 `lead/samedoc_link_20261109/_sl_link.py` 及本任务列明的全部只读件；
- 禁止从 merged 输出推导角色/授权结论，禁止自动化消费 rec.path（merged 时恒 None）；
- 零真机、零采样代码；本写域件不 commit、不 push。

## 5 回归证据索引（全部本会话实跑，命令见各件 docstring）

| 件 | 内容 | 结论 |
|:--|:--|:--|
| `_re_fp_check.py` → stdout | 10 件只读基线指纹 | ALL_MATCH（与编排方实跑指纹逐一对账） |
| `_re_struct_diff.py` → `_re_struct_diff_out.json` | 原件 vs 并入版 difflib 白名单核验 | STRUCT_OK：11 hunk 全在白名单 |
| `_re_run10_diff.py` → `_re_run10_out.json` | 十条真件原/并双跑 + 附加对照 + invalid_hex | 20/20 断言过；unique 8=8、zero 1=1 不变；唯一变化 = 条3 multi→merged；12 行输出逐字节全等 |
| `_re_j4_cases.py` → `_re_j4_out.json` | 四类案例 + 正反控制 | 19/19 断言过 |
| `_re_parity_extra.py` → `_re_parity_extra_out.json` | 补充回归 14 案：unique/zero/invalid_hex 带声明行不介入、15 成员 members 全列（anchors 仅 12）、Q4 multi 的 triple 契约、原 `_sl_selftest.py` 8 个调用面双跑 | 21/21 断言过；unique 6/6 与 zero 3/3 输出全等；唯一变化 = 15 成员夹具 multi→merged |

补充回归命令：`python -I -B -X utf8 D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_parity_extra.py`
（首次实跑 20/21——历史 selftest 实为 9 项含 `(a)0` 前置检查，断言常数写 8 致失败；改为 9 后复跑 21/21。两次输出均如实记录：首次 FAIL 项为脚本自身断言常数错误，非并入版行为异常。）

## 6 交付件指纹（本会话 hashlib 实算）

| 件 | SHA256 | 字节数 |
|:--|:--|--:|
| `_re_linked.py` | `7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52` | 19481 |
| `_re_parity_extra.py` | `3bea1ab0760d5c46bfc94f76e7f1d97ae35bfd3354497b2dbaaf27e7195cd4e5` | 13512 |
| `_re_parity_extra_out.json` | `18906e18359a22b2c1f63d168be6c3c138ef9402adc2e14bdee29220ace0969d` | 12768 |

（其余交付件指纹见本会话实跑 stdout；本件不写自嵌哈希。）
