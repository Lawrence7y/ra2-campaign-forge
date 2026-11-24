# S09-KPROVED7 UNKNOWNS

本文件列出 59 个候选中 **51 个未进 delta** 的行及不成立理由。8 行四环齐全入 delta；
其余按「任一环不成立则不进 delta」处理。理由按 D-40 四环 / D-42 ③a/③b 分档 / §8.7 判据归类。

## 1. 逐行不成立理由（51 行）

| entry | name | 不成立环节与理由 |
|---|---|---|
| 0048E620 | ControlClass::slot27 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 004AAD20 | TabClass::slot44 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 004AEAD0 | TabClass::slot35 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 004E1450 | CheckListClass::slot16 | ③a：纯尾转 jmp 转发桩 |
| 004E1460 | CheckListClass::slot15 | ③a：纯尾转 jmp 转发桩 |
| 004E1480 | ControlClass::slot9 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 004E1960 | ControlClass::slot18 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 004E19A0 | CheckListClass::slot20 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 004E19D0 | CheckListClass::slot21 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 004E1A20 | ControlClass::slot25 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 004E1A40 | CheckListClass::slot26 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 004F3B10 | GraphicMenuAnimItem::slot3 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 004F42A0 | GScreenClass::slot5 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 004F42D0 | GScreenClass::slot7 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 004F42E0 | GScreenClass::slot8 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 004F4BB0 | GScreenClass::slot10 | ③b① 细则#1 不成立：多路分支汇入同一调用/动作同型（M4），非各闸动作各异 |
| 005565F0 | CheckListClass::slot8 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 005566A0 | ControlClass::slot3 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 005566D0 | ControlClass::slot5 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 00556700 | ControlClass::slot4 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 00557800 | ListClass::slot43 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 00557F40 | ColorListClass::slot46 | ③b① 细则#1 不成立：多路分支汇入同一调用/动作同型（M4），非各闸动作各异 |
| 005BDA80 | MouseClass::slot18 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 005BDAA0 | MouseClass::slot20 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 005BDF30 | MouseClass::slot5 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 005BDF50 | MouseClass::slot7 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 0063F730 | PowerClass::slot7 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 0063F7B0 | PowerClass::slot5 | ①入口形态不成立：入口为 jmp 跳板/自写CFG延伸异常（错源②），非真函数入口 |
| 0063F7C0 | PowerClass::slot53 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 0063F7E0 | PowerClass::slot50 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 006403A0 | PowerClass::slot34 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 00640450 | PowerClass::slot33 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 00652D90 | RadarClass::slot50 | ③b① 细则#1 不成立：多路分支汇入同一调用/动作同型（M4），非各闸动作各异 |
| 00652DE0 | RadarClass::slot7 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 00652E90 | RadarClass::slot53 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 00653010 | PowerClass::slot8 | ③b① 细则#1 不成立：多路分支汇入同一调用/动作同型（M4），非各闸动作各异 |
| 00653760 | MouseClass::slot51 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 00653810 | MouseClass::slot36 | ③a：setcc 返回但无关键判据/无状态转移，不构成 ③b 整体合同 |
| 00653830 | MouseClass::slot37 | ③a：setcc 返回但无关键判据/无状态转移，不构成 ③b 整体合同 |
| 00653F70 | MouseClass::slot52 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 00658770 | RadarClass::slot33 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 006922E0 | ScrollClass::slot10 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 006938C0 | MouseClass::slot35 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |
| 006A5BF0 | SidebarClass::slot50 | ③b① 细则#1 不成立：多路分支汇入同一调用/动作同型（M4），非各闸动作各异 |
| 006AC5D0 | TabClass::slot30 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 006AC5E0 | TabClass::slot31 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 006D0260 | TabClass::slot5 | ①入口形态不成立：入口为 jmp 跳板/自写CFG延伸异常（错源②），非真函数入口 |
| 006D03A0 | TabClass::slot8 | ③b① 细则#1 不成立：多路分支汇入同一调用/动作同型（M4），非各闸动作各异 |
| 006D1800 | MouseClass::slot33 | ③a：极短 getter/setter，单字段读写、无分支关键判据 |
| 00724AB0 | ToolTipManager::slot2 | ③a：清零+置默认值/线性字段维护，无关键判据 |
| 00724B80 | ToolTipManager::slot3 | ③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸 |

合计 51 行（59 候选 − 8 入选 = 51）。

## 2. 关键剔除逐条说明（细则#1 / M7 / 错源②）

- **00557F40 ColorListClass::slot46**：越界闸 + 上/下滚动两分支汇入同一虚调 `[edx+0xc0]`、仅入参不同；按 M4 与 §8.7 判据6（细则#1 判定闸，比对 0069DEB0）不算「各闸动作不同」，③b① 不成立。
- **006A5BF0 SidebarClass::slot50**：23 道旗标闸动作全同型(free+清位)；末段循环体只有 `call 0x69de70`、游标推进只在 esi 寄存器，无体内非栈写/可证伪返回码，按 M7（0045A640 TIEBREAK 理由）③b④ 不成立。
- **006D0260 TabClass::slot5**：入口是 `jmp 0x6a5000` 跳板，自写 CFG 延伸 176741 B 非本函数体；按错源②（jmp32 当真入口系统性高估）①入口形态不成立。
- **0063F7B0 PowerClass::slot5**：入口尾转 jmp，自写 CFG 延伸 79328 B，①不成立。
- **00653810/00653830 MouseClass::slot36/37**：`call→test→setne al` 纯转发桩，虽有 setcc 返回但无状态转移/关键判据，按 D-42 ③a 不升。

## 3. 口径与边界

- ③b 基率按 D-42 要求用全 103 A 行抽样（strict 0.5083 / loose 0.7464，seed 20261119，N=8，2000 次），非「②∧④入选率」、非「K=行数×均值」恒等式。
- 未改 coverage.tsv / 台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli\ / 其它卡目录 / _audit\；未真机、未 git commit、未建 venv 或 pip install。
