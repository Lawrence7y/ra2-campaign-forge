# S09-KPROVED8 · PROGRESS（卡号 S09-KPROVED8）

开工 2026-11-20T00:16+08:00。目标 `ra2youli\gamemd.exe` SHA-256 前缀 73201CC0/后缀 F67476（现场全值 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`），ImageBase 0x400000，全程只读。Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未建 venv/未 pip install/未 git commit。写域仅 `S09_KPROVED8\` 与 `_ghidra\S09_KPROVED8\`；未改 COVERAGE/台账/R14_COMMON/任何 `_audit\`。判据：§8.6 六条 + D-40/41/42/43 + §8.7 九条 + §8.8；只认 ③b，D-44 解封条件=第4列语义不含「未证」。

## 0. 结论：8 行全部四环齐全（四环齐全数 = **8 / 8**），delta 行数 = 8 = 自报行数

| entry | name | ③b 档位（入口相对锚） | ② 持有表(slot) | ④ 见证 |
|---|---|---|---|---|
| 004888B0 | ColorListClass::slot43 | ②+④ -1哨兵 + 数组左移有界循环(+0x11/+0x38/+0x43) | 1表 vt7E5054/43 | livevt 构造器写 4887D7/488803/488F13 |
| 00488910 | ColorListClass::slot42 | ②+④ -1哨兵 + 数组左移有界循环(+0x05/+0x2E/+0x3A) | 1表 vt7E5054/42 | livevt 同上 |
| 00488980 | ColorListClass::slot50 | ① 五路跳表 cmp eax,4/ja + jmp[0x488EC0](+0x1B4/+0x1BD) | 1表 vt7E5054/50 | livevt 同上 |
| 006539D0 | RTacticalClass_RadarClass::slot31 | ①+② 二路映射跳表 + call639DA0返-1哨兵(+0x2E3/+0x2FE) | 1表 vt7F02BC/31 | livevt 构造器写 65288E |
| 006D0A20 | MouseClass::slot16 | ④ 多段有界循环：标志扫描/对象清理/数组左移(+0x61/+0x334/+0x3F5) | 3表同slot16→归基类级 | livevt 7E1964 四处ctor写 |
| 00565AA0 | MouseClass::slot22 | ④ 有界清零循环 mov[eax*4-4],0 + cmp Count/jl(+0x43/+0x4A/+0x58) | 8表同slot22→归基类级 | livevt 7E1964 ctor写 |
| 00771900 | Anim_Voices_WorldDominationTour::slot2 | ② 语音计时器 -1哨兵双闸 + elapsed/duration 两可证伪终点(+0x06/+0x0F/+0x25) | 1表 vt7F7354/2 | livevt ctor写 771831/771874/771890/771A33 |
| 0049FB40 | CounterClass::slot3 | ④ 有界清零循环 mov[esi+eax*4-4],0 + cmp Count/jl(+0x08/+0x10/+0x17) | 1表 vt7E5C54/3 | livevt 构造器写 49F9C1/49FBF9 |

② 链全部现场读通：每 entry 枚举全部持有表，`[vt-4]=COL → [COL+0xC]=TD → TD+8 内联名串` 逐表核，`vt[slot]==entry` 全 True，无 fail-closed；类名读不到即拒（本卡 0 例）。多表同 slot（006D0A20/00565AA0）按错源⑯归基类级、name 栏保留 coverage 现值。④ 全部走 D-43(A) 宽读法活 vt（构造器装表 + vt[slot]==entry + 写点在行外 + site 不共用，不要求真实派发点）；全 .text skipdata 线性扫描 1,392,592 指令 / 68,253 E8，本 8 行均 0 direct 命中，故只用 livevt。逐行反汇编/站点/RTTI 全量见 `EVIDENCE/ROW_*.txt`（不截断）。

## 1. 核心数字（供审计复算）

- **四环齐全数 = 8/8**；**delta 行数 = 8**（= 自报，判据7 通过）。
- **S09 现态（atlas W130 ∩ coverage 大写 entry，自己从 coverage.tsv 重算）**：n=**1051**，named_L=**681**，named_S(R14)=**681**（64.80%，门槛 946 不达标），proved=**106/1051**（10.09%，门槛 526）。另 proved_strict=**89**（8.47%）。复算 `work/core_stats.py` → `core_numbers.json`。
- **③b 基率**（S09 [静态推断] 池 N=**592**，池内随机取 8 行，seed **20261119**，**2000** 次，行采样口径）：strict K=**33**（5.57%），期望 8×33/592=**0.4459**，实测均值 **0.4415**，分布 {0:1260,1:612,2:113,3:15}；loose K=**88**（14.86%），期望 **1.1892**，实测均值 **1.1845**，分布 {0:536,1:798,2:470,3:162,4:26,5:7,6:1}。复算 `work/base_rate.py` → `EVIDENCE/baseline_3b.json`。
  - 操作化 strict：T1 有界跳表(目标全在体内) ∨ T2 cmp -1/HRESULT→jcc 且 ≥2 出口 ∨ T4 回边+边界 cmp+窗内非栈写。loose：strict ∨ 任意 scale 间接jmp ∨ 任意 cmp -1→jcc ∨ 任意回边带 cmp ∨ ≥3闸且≥3异名直调。`K=N·p` 与 `8×均值` 是恒等式（判据3），不作校验；本 8 行全在 strict K 集内（见 `work/pool_3b_flags.tsv`）。
- A 集合 S09 has4_strict∧has2_rtti 池剩余 51 行（已扣排除集），本卡取 8 行定向挑硬 ③b，8/8 命中远超基线 ~0.45，源于定向非随机。

## 2. 两处跳表逐路可核（③b①）

- 00488980：表 0x488EC0 五路 → 488A44/488AC0/488B9F/488C83/488E37，全部 in_body∩in_text（`EVIDENCE/JUMPTABLE_00488980.txt`）。
- 006539D0：字节映射表 0x653F04[0..0x47] 仅 2 个派发 id{0,1} → 表 0x653EFC 两项 653CC0/653CBA，全 in_body（`EVIDENCE/JUMPTABLE_006539D0.txt`）。

## 3. 复算与纪律自检

- 脚本全在 `work\`（core_stats/s09lib8/screen/screen2/detail/livevt/pattern_scan/verify_jumptables/base_rate/final_verify），只读目标、可复跑。全表 RTTI 实测 1214 表/14044 槽（与审计基准一致，未受害于错源①）。
- ④ 站点用函数区间包含判归属，不用 entry_at_or_before；不采「最近E8/E9」「最大函数=热点」「无调用者=死代码」启发式。
- 排除集合成：七张 S09_KPROVED delta 全部 entry + SEMFIX_SLOTS2/3 的 S09 行 + 卡面黑名 00654320/0069DEB0 = 52 个唯一 entry（`work/exclusion_set.tsv`）；本 8 行均不在排除集。
- 第4列全部写出 ③b 整体合同（类名+槽位+子系统描述保留盘上前半句，占位替换为档位+一句话+入口相对锚+关键指令），禁词扫描 0 命中。未抄其它卡 work 代码；仅交本卡目录产物。
