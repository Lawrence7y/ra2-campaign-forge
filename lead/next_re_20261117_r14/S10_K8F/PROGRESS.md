# S10-K8F PROGRESS（≤40 行）
修正卡：读 S10_K8 与 _audit/VERDICT.md（PARTIAL），只写 S10_K8F；K8、COVERAGE/、目标 exe 未写。成稿 2026-11-18T04:50+08。
目标 ra2youli/gamemd.exe SHA-256 73201CC0...F67476 / 4825360B；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；无 Ghidra。
基线复算：coverage.tsv SHA C4805489...CAF43 / 3652533B / mtime 04:05:20.480290+08；S10 528 行、∩atlas 526、表外 2；[已证] 92/526=17.4905%，named(S) 52，门槛 263，差 171。
## 四处缺陷修正
1a. 独立复核 work/reverify_semantics_k8f.py（原始字节+反汇编）：0041BA90 吞请求精确条件为 cur∈{4,26,27,30,31} ∧ [this+0x294]==0 ∧ id∉{4,26,27,30,31}；内层 idx0→0041BAD3(call)，idx1/越界→0041BADE(吞)。三行 id=1/2/15 均在集合外，[已证] 不虚高。
1b. 005B35E0 早退第 4 条为 cur==id ∧ queued∈{id,-1}（queued=[this+0xB4]），不是 queued!=-1；cur=0x1E 跳过清 [this+0x6D2]。delta 六行只改语义列，并补齐行5/6 的 cur=30 分支；entry/name/grade/evidence 均未动。
2. 重生成 EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt：纠正“inner index 0→41BADE”反写，改为 inner idx0→41BAD3→005B35E0；六个 #anchor 保留。
3. S22 结算改为 54→55/4851=1.1338%，named 4→6；006B6FA0 不在 atlas，故不计入 atlas 分母、proved 或 named；不在 atlas 的行不计入 atlas 分母统计。
4. 补生成 EVIDENCE/S22_BASELINE_K8.txt（atlas_n=4851、proved=54、named=4、SIM 55/6、时点与脚本路径），来源 work/s22_baseline.py。
## 结算与校验
S10 模拟：proved 92→99/526=18.8213%，named(S) 52→59，门槛剩差 164；004E0E80 若 D-37 改归 S22，S10 应回退为 98。
S22 按盘上归属不动：proved 54→55/4851=1.1338%，named 4→6；006B6EA0 +1 proved/+1 named，006B6C90 仅改名 +1 named，006B6FA0 表外不计。
校验：10 行/9 列、entry 与 name 唯一、name 无 +0x 偏移、证据路径全存在、0 placeholder；name_kind symbolic=4/behavioral=6；EVIDENCE/DELTA_VALIDATE.txt。
证据：BASELINE_RECOMPUTE_K8.txt、QUEUE_DISPATCH_AND_FALSE_KILLS.txt、SPAWNMANAGER_CTORS.txt、OWNERSHIP_004E0E80.txt、S22_BASELINE_K8.txt；复算脚本见 work/。
## 归属（不自行改判）
SpawnManagerClass 三构造器仍是 coverage.tsv 盘上 S22；Lead 已将“同类劈两桶 + S22 前提为假”升级为 D-37 第二类实例并请用户裁决。裁决前本卡按盘上归属 S22 交付，详见 DISAGREE.md。
