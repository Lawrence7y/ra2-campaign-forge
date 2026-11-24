D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe	sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R33-SLOT107-DISPATCH 报告

## 范围与边界

- 纯静态只读；未建进程、未调试、未启动 gamemd；未改 R12/R28 目录；产物只写本目录。
- 入口集独立重建：RTTI 槽值 6692（RTTI {'vtables': 1214, 'slots': 14044, 'td': 988, 'col': 1214, 'rdata_bytes': 200704, 'data_bytes': 442368}）+ E8 目标 68807 + padding 15067 + 构造器 9，总计 19301；未用 C3/C2 字节扫入口。
- 反汇编 68 个函数、7117 条指令、23691 字节；每函数上限 200 条。

## Q1

等距抽样 12 条，成立 12，不成立 0；基础可信集命中 8 条，其余由严格解码锚定；未触发停手阈值。

| site | new_host | 在基础可信集 | 严格解码ret在site后 | fn_end | 范围内 | 判定 | 依据 |
|---|---|---|---|---|---|---|---|
| 0x415B8F | 0x415B10 | True | True | 0x415C54 | True | OK | trusted_set=True; strict_decode=True; prefix_insns=40 |
| 0x43F678 | 0x43F658 | False | True | 0x43F9A6 | True | OK | trusted_set=False; strict_decode=True; prefix_insns=14 |
| 0x44F1D8 | 0x44F195 | False | True | 0x44F1F6 | True | OK | trusted_set=False; strict_decode=True; prefix_insns=24 |
| 0x44F577 | 0x44F3B7 | False | True | 0x44F5B5 | True | OK | trusted_set=False; strict_decode=True; prefix_insns=133 |
| 0x487B9F | 0x487A10 | True | True | 0x487C0F | True | OK | trusted_set=True; strict_decode=True; prefix_insns=130 |
| 0x4CBE7B | 0x4CBC40 | True | True | 0x4CBEBD | True | OK | trusted_set=True; strict_decode=True; prefix_insns=165 |
| 0x50D8BF | 0x50D6D0 | True | True | 0x50D9B1 | True | OK | trusted_set=True; strict_decode=True; prefix_insns=140 |
| 0x51DD54 | 0x51DBD0 | True | True | 0x51DEFD | True | OK | trusted_set=True; strict_decode=True; prefix_insns=119 |
| 0x5F4F3C | 0x5F4EC0 | True | True | 0x5F521C | True | OK | trusted_set=True; strict_decode=True; prefix_insns=42 |
| 0x6EB35A | 0x6EB1F4 | True | True | 0x6EB37A | True | OK | trusted_set=True; strict_decode=True; prefix_insns=118 |
| 0x737404 | 0x73737E | False | True | 0x737427 | True | OK | trusted_set=False; strict_decode=True; prefix_insns=37 |
| 0x75F902 | 0x75F8B0 | True | True | 0x75F96B | True | OK | trusted_set=True; strict_decode=True; prefix_insns=29 |

## Q2

分布：(a):0, (b):0, (c):24, (d):57, (e):5。容器遍历类 (b) 共 0 条；全量见 sites86.tsv。

## Q3

从 (b) 类按 scaled/loop 排序抽查 0 点；检查 [obj+0x520]/[obj+0x408]/[obj+0x74] 和同 host 的 0x124+0x1AC 双派发。候选 0 个。

| site | host | base_reg | 容器证据 | 特征偏移 | 派发偏移 | scaled | 双派发 | 判定 |
|---|---|---|---|---|---|---:|---|---|

## Q4

经容器遍历路径亦未取得 0x449440 的调用方。

只证存在至少一个或未发现，不证唯一，不证运行期真的执行到；不改变 ②-b 的 [静态推断] 收口（D-53(A)，§2.9 + §2.10 的 (a′) 不可拆）。

## 产物

REPORT.md、sites86.tsv、candidates.tsv、work.py。
