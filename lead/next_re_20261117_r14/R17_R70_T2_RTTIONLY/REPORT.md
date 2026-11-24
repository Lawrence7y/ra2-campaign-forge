Q1 | rtti_names.tsv=988 行 ; names.tsv=988 是否同一 988: 是(差异=0，两者归一化裸名集合完全相等：rtti独有0、names独有0)
Q2 | 规则=<大小写不敏感；coverage.tsv第4列按Class后缀正则抽429个token；对RTTI侧988个TD逐个判——coverage token 精确裸名 / token去开头P·A·V前缀后裸名 / 模板基名(?$X@…→X) 三类任一命中即算"有coverage对应项"，从RTTI侧直接累加无对应者，不写988减> ; RTTI_ONLY=383 ; 与383: 一致
Q3 | 规则=<口径S规则之上加：coverage token 的 X_Y ↔ RTTI 非模板复合TD 的 X@Y 整token大小写不敏感精确匹配(命中6个token/6个TD)，禁止丢段取基名> ; RTTI_ONLY=377 ; 与377: 一致
Q4 | 正控 BOTH: 我的实现=397 / 权威表 397 ; C 口径 BOTH=403 / 403 | 同口径: 是
OVERALL | 383(S)/377(C) 经三种独立数法(RTTI侧纯bare名逐个判、tdVA逐个判、权威cv减法)一致复现，且BOTH正控397/403与权威reconcile_final.tsv的S_bucket/C_bucket列吻合，两数可作为直接计数引用，不再仅是988-605/611的推导值。

## 复算脚本

脚本名：`recount.py`（本目录 `lead\next_re_20261117_r14\R17_R70_T2_RTTIONLY\recount.py`），输出 `recount_out.txt`。
关键命令：

```
python D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R70_T2_RTTIONLY\recount.py
```

脚本完全独立实现，不 import 权威 work.py；只读源文件，产物只写本目录。

## 数字溯源（文件 + 总行/数据行 + 过滤条件 + 脚本名）

| 数字 | 文件 | 总行/数据行 | 过滤条件 | 脚本名 |
|---|---|---|---|---|
| rtti_names.tsv=988 | R17_R19_RTTI_XCHECK\rtti_names.tsv | 989/988 | 跳表头，非空数据行，取 bare_class 列 | recount.py |
| names.tsv=988 且同一988 | R17_R13_NAME_TABLE\names.tsv | 989/988 | 跳表头，非空数据行；name 列去 .?AV/.?AU/.?AW 前缀与尾部 @@ 归一化后与 rtti bare 集合比较(相等,差0) | recount.py |
| coverage token=429 | COVERAGE\coverage.tsv | 18499/18498 | 第4列 one_line_semantics，Class后缀正则抽取、每行去重 | recount.py |
| S: BOTH=397/COVERAGE_ONLY=32 | R17_R24_RECON_FINAL\reconcile_final.tsv | 430/429 | 按 S_bucket 列取值(BOTH/COVERAGE_ONLY 为桶名，非文本grep) | recount.py |
| C: BOTH=403/COVERAGE_ONLY=26 | R17_R24_RECON_FINAL\reconcile_final.tsv | 430/429 | 按 C_bucket 列取值 | recount.py |
| S: RTTI_ONLY=383 | R17_R19_RTTI_XCHECK\rtti_names.tsv + COVERAGE\coverage.tsv | 988 + 18498 | RTTI侧988 TD逐个判；A减法=383 / B逐个判(tdVA in cv)=383 / C纯bare名逐个判=383，三法一致 | recount.py |
| C: RTTI_ONLY=377 | 同上 | 988 + 18498 | 口径S加X_Y↔X@Y整token匹配；A=377 / B=377 / C=377，三法一致 | recount.py |

## 独立性与正控说明

- 权威表 R17_R24_RECON_FINAL 的 RTTI_ONLY 由 `988 - |被coverage命中的TD集合cv|` 得出（S: cv=605→383；C: cv=611→377），是减法推导。
- 本卡换的独立路径：从 RTTI 侧 988 个 TD 出发逐个判"是否存在 coverage 对应项"，直接累加无对应者（数法C，完全不构造cv、不写减法）；另用 tdVA 逐个判（数法B）交叉。S/C 均得 383/377，与减法一致。
- 边界诊断：exact∩prefix=0、exact∩模板基名=0、exact∩compound=0，证明"RTTI侧逐个判"与权威token侧resolve完全等价，不存在优先级重叠导致的口径差。
- Q4 正控：我的token侧实现给出 BOTH=397(S)/403(C)、COVERAGE_ONLY=32(S)/26(C)，与权威 reconcile_final.tsv 的 S_bucket/C_bucket 列逐项吻合，同口径成立。
- 机制分布(我的实现)与权威一致：S=exact209+prefix186+template_base2；C 再加 compound6。
