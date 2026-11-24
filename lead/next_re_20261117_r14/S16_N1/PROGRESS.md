# S16-N1 · PROGRESS（最终）

卡号：S16-N1｜目标：只补 S16 真实语义名，不动 grade。产物 2026-11-18；系统 Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26（无 venv / pip）。
目标：ra2youli\gamemd.exe SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（只读）。

## 基线（盘上复算，与 CARD 一致）
n(atlas∩coverage,S16,去重)=**90**；named_L=**73**；sub_=**17**；门槛 81 ⇒ 差 8；proved=**46/90=51.11%**（已过线，未动）。
复算：coverage.tsv 按 tab 分列筛 col2==S16 ∩ function_atlas.tsv，按 entry 大写去重；name 非空且不以 sub_ 开头=named；grade 含已证=proved（work/baseline.json）。

## 结论表（8 条；3 reused_audited + 5 新真名）

| # | entry | 新名 | 通道 A（二进制，独有信息） | 通道 B（异源，独有信息） | 判定 | 证据 |
|---|---|---|---|---|---|---|
| R1 | 00539EB0 | LightningStorm::Start | 读 0xA9F9F8/FA、两次 call 0x65C7E0、写 0xA9F9CC/0xA9FACC | 审计认证 + YRpp CALL(0x539EB0)=Start | [已证] reused_audited | E01 |
| R2 | 0053AE00 | LightningStorm::AnnounceActive | Msg:LightningStormActive @0x82809C 体内引用 -> call 0x734E60 -> 0x5D3BA0 | 审计认证 + YRpp CALL(0x53AE00)=PrintMessage | [已证] reused_audited | E01 |
| R3 | 0053B410 | PsychicDominator::AnnounceActive | Msg:DominatorActive @0x8280B8 体内引用 -> 同上调用链 | 审计认证 + YRpp CALL(0x53B410)=PrintMessage | [已证] reused_audited | E01 |
| N1 | 0053A0E0 | Ion::HasDeferment | 读 Active@0xA9FAB4 / Deferment@0xA9FAB8，返 bool | YRpp SuperClass.h `CALL(0x53A0E0)` + 同名字段地址 | [静态推断] | E02 |
| N2 | 0053AE50 | PsyDom::Start | owner->0xA9FAC8、coords->0xA9FA48、Anim->0xA9FAC4、Status=1 | YRpp SuperClass.h `CALL(0x53AE50)` + 字段地址逐一 | [静态推断] | E02 |
| N3 | 006CE2C0 | TimerStruct::StartIfEmpty | cmp [ecx],-1; 写 CurrentFrame@0xA8ED84 | YRpp Doc `JMP_THIS(0x6CE2C0)` + 注释 just sets start frame | [静态推断] | E02 |
| N4 | 006CE270 | LocomotionClass::AddRef2 | ecx=**Loco, null 守卫, call [vptr+4] (COM AddRef) | YRpp LocomotionClass.h `CALL(0x6CE270)`，与 AddRef1(0x45A170) 并列 | [静态推断] | E02 |
| N5 | 006CE280 | TimerStruct::Pause | 完整字节签名全 .text 唯一(1 命中)；StartTime/TimeLeft 按 CurrentFrame 夹取回写 | YRpp GeneralStructures.h `Pause(){if(IsTicking()){TimeLeft=GetTimeLeft();StartTime=-1;}}` + 同簇 StartIfEmpty 已地址绑定 | [静态推断] | E03 |

## 给审计的核心数字
① **真实语义名新增 5 条**（N1–N5）；另 3 条 reused_audited（R1–R3）按 CARD 计入 KPI 但不重复算新发现。合并后 named = 73+8 = **81/90 = 90.0%**，恰达门槛 81（余量 0）；proved 保持 46/90。
② 每名两条通道及独有信息：见上表 A/B 列；A=镜像字节/字段/调用点，B=YRpp 源码/文档符号或审计认证；两者互不蕴含（同源的『镜像串+函数体』只算 A 一环）。
③ 误命中基线：17 条 sub_ 中 YRpp 地址绑定 7 条；随机挑 5 条期望误命中 5×7/17=**2.06**（非 reused 池 14 中 5 条 ⇒ 5×5/14=**1.79**）；PAUSE 字节签名 1/4,060,045 B，RemoveItem-by-index 18 命中故不用。复算：work/baseline_false_positive.py / baseline_yrpp_coverage.py / baseline_sigs.py；报告 EVIDENCE/E04_baseline.txt。

## 复算方法（最短）
- 字节：python work/re_tools.py dis `entry`（capstone 5.0.7，skipdata）。
- 绑定：rg -n '0x<entry>' YRpp/{SuperClass.h,LocomotionClass.h,GeneralStructures.h,Documentation/*}。
- 基线：见上方脚本；SHA-256 自检见 EVIDENCE 与开头。

## 边界与交付
- 未改 grade/COVERAGE/台账/游戏文件；未创建 venv、未 pip install、未 git commit。
- 产物：PROGRESS.md / UNKNOWNS.md / DISAGREE.md / EVIDENCE/E01–E04 / work/ / coverage_delta.tsv（8 列，8 行）。
- 一致性：所有 8 行 grade 与盘上同源（全 [静态推断]），不动 proved；N5 的 [静态推断] 不升格。
