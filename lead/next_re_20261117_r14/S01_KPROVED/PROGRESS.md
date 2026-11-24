**升了 0 行 / 最多 0 行（目标 21 行；严格 D-42 ③b + D-41(A) 口径下 S01 proved 不可达）**
# S01-KPROVED · PROGRESS

卡号 S01-KPROVED｜开工 2026-11-18 18:1x +08:00｜目标 ra2youli\gamemd.exe 只读（SHA256 73201CC0…F67476）｜写域仅本目录 + _ghidra\S01-KPROVED｜Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26，未建 venv、未 pip install。
骨架在开工 10 分钟内落地（18:1x）。已读 R14_COMMON §8.4/§8.5/§8.6 + 本卡 CARD.md + PENDING_DECISIONS D-40/41/42 原文。

## ⑨ 停机核验（盘上重算，atlas∩coverage）
S01：n=53、proved=6、[静态推断]=8、[未证]=39、named(L)=11 → 门槛 27，差 **21**，与卡面一致。
coverage.tsv 全表 18,431 行；E8 全镜像 1,392,592 指令 / 68,253 E8@边界（与卡面基准逐字吻合）/ 81,715 raw E8。

## 结论：0 行可升（逐环）
最小环集 = ①入口 + ②类属/身份 + ③b 合同 + ④使用见证，任一缺不升。47 个未证行逐行判据见 `EVIDENCE/per_row_verdict.tsv`：
- **② 环是硬瓶颈**：47 行中仅 2 行有 vtable/RTTI 形态（00554400、00643E80，均 slot0），另仅 0069AE90 有 YRpp 地址绑定；其余 44 行无 RTTI、无 YRpp 绑定 → ② 直接失败（自由函数/静态成员/CRT，D-41(A) 物理不可用 RTTI）。
- 00554400 / 00643E80：② RTTI 可成立，但 **③ 仅 ③a**（16 指令 2 守卫 1 虚调的薄消息处理；3 指令 `mov [ecx+4],arg; ret 4` 纯 setter）→ 不满足 ③b，不升。
- 0069AE90（唯一 YRpp 绑定，Game::SetProgress 候选）：③b 有 4 路跳表(0x69B15C)+完整 Sleep 定时循环，④ 有 60 个边界核实 direct call；**但 ② 严格不成立**——
  · YRpp 原文是 `JMP_STD(0x69AE90)`，非卡面要求的 `CALL(0x…)/JMP_THIS(0x…)`；
  · `SET_REG32(ECX,0xA8B238)` 的 imm 不在函数体内（在包装器），体内只把 ECX 当指针保存；体内出现的 0xA8ED6B/0xAC4F58/0xA8B230 是跨类通用全局（ArmageddonMode/ProgressScreenClass::Instance/ScenarioClass::Instance），非 Game 类声明成员/偏移/常量，无「逐项吻合」；
  · 属单点吻合，D-42 细则 3 明确拒绝；与通过的 0053AF40（3 个类静态成员全用上）/00595740（11×偏移+常量）不同。
  ⇒ ② 走不通 → 不升（D-41 裁决前默认 (A)）。
- ④ 单独一律不作升格依据（D-40 已作废该判据，M32 回退 53 行）。

## 随机基线 / 差分（本子系统内随机取同样多行）
unproven 池 n=47：weak（仅④ direct call@指令边界）=40（85.1%）；strong（④+③b 机械筛）=25（53.2%）；**weak\strong 差集=15 行**。
随机基线（seed 20261118，200 抽×5 seed，不重复）：weak 期望 34.04 / 实测均值 34.07；strong 期望 13.30 / 实测 13.39；full（④+③b+有效②）期望 0 / 实测 0。
② 通道基率：YRpp 绑定 1/47=2.1%（且该 1 行严格不过）；RTTI/vtable 2 行且均 ③a。=> ③b 机械筛判别力弱，真正卡口是 ②。

## 自证 / 交付
- ⑲：capstone 5.0.7 无 op.index，mem 无 index 返 0（int）——全程不按 index is None 过滤。
- ⑱：按 entry 扫全库 6 位/8 位写法，5,247 文件，命中均为地址级枚举（S08_K1/sweep.json、S09_F1/entries.txt），无命名归属冲突；有 2 处 subsystem 提及（0048C8B0/0055D360）系已证行、不属本卡改动。详见 `EVIDENCE/conflict18.txt`。
- name 未动、subsystem 未动；coverage_delta.tsv 仅表头（0 数据行）。
- 并入后 S01 proved 仍 6/53 = 11.32%（门槛 27），未达标、不可达。
- EVIDENCE/：per_row_verdict.tsv、scan_main.json/txt、baseline_final.txt、conflict18.txt、VERIFY_69AE90.txt、ANALYSIS_0069AE90.txt；work/：扫描与判据脚本。
