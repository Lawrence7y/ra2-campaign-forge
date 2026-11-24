# S13-PUSH PROGRESS

时间基准（本机 Asia/Shanghai）：2026-11-20。

## 执行纪律
- 先算账面再取证；每核完一行立刻落盘；每 5 行追加进度到本文件。
- 不修改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账；只写 S13_PUSH\。

## 进度
- [x] 读完卡片 S13-PUSH.md（2026-11-20）
- [x] 第一步：账面自算完成并落盘 `LEDGER.txt` + `work/ledger.json`
  - n=240；named_L=216 / named_S(R14)=216 / named_strict=108
  - proved=100 / proved_strict=99
  - 门槛：named ceil(0.9*240)=216（恰好达标，零余量）；proved ceil(0.5*240)=120
  - 差距：named_S(R14)=0；proved=20；proved_strict=21
  - 结论：named_S(R14) 已达门槛 ⇒ 按卡片条件第四步（named 不够时同时攻 named）本卡不强制触发；本卡主攻 proved。
  - coverage.tsv sha256 = FA5637DF6C87F0327C91770FF8E478378ACDDB1E3C5E6F157B033DE11AFC3836
  - function_atlas.tsv sha256 = 4527079B8E1556F0F34BC2C16068DDAEF7681EE2B6A5E1F2AADC61A73653DB69
- [x] 材料自校验：gamemd.exe SHA256=73201CC0...F67476；capstone 5.0.7 / pefile 2024.8.26；.text=[0x401000,0x7E038D)
- [x] 第二步基础率：池=140（S13 atlas 且 [静态推断]115+[未证]25）；通道A(③b②)机械命中=13(rate 0.0929)，通道B(③b①跳转表)=0，union=13；落 base_rate.tsv
- [x] 第三步逐行取证（13 个 A 命中全核完，每核完即落 EVIDENCE/ROW_<entry>.txt）：
  - eax 覆写陷阱剔除 4 行（004251F0/00438A90/006294D0/0070FEE0）
  - ③b② 真形态 9 行；其中无虚表槽/仅 direct 3 行（0062AC30/006FD460/00708080）环④不合格
  - 四环（本卡字面）齐全 6 行入选 delta：004684E0 00629FD0 0075E0C0 0075E2C0 00772CD0 00772EB0
  - ⚠ 这 6 行环④与环②共用 vtable 槽，D-40 严格口径（S13_KPROVED2/S13_K12/SURVEY_RING24）判 FAIL：争议已在每行 EVIDENCE 与 REPORT 明确标记
- [x] 第四步 named：named_S(R14)=216=门槛 ⇒ 按卡片触发条件不必攻；产出空 S13_named_delta.tsv（仅表头）
- [x] 写 REPORT.md / base_rate.tsv / 两个 delta.tsv（全部落盘）
- [x] 最终答复：账面 n=240/named216/proved100/strict99；基础率 A 13/140→去陷阱9→四环字面6→D40严格0，B 0；delta 6 行；按本卡字面口径 100→106 仍差 14，按 D-40 严格口径仍差 20；两口径均不能达标
