# SEMFIX-SLOTS PROGRESS（最终）

- 卡号 SEMFIX-SLOTS；写域仅 SEMFIX_SLOTS\；COVERAGE\、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli\ 未动；未 git commit、未建 venv、未 pip install。
- 目标：`ra2youli\gamemd.exe` 只读，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，4,825,360 B，ImageBase 0x400000；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile。
- 核盘：COVERAGE/coverage.tsv（表头逗号、数据 TAB 8 列），筛 col4 含「槽语义未证」∧col5==`[已证]`∧col2!=S22 → **实际 36 行**（S09 15 / S03 8 / S10 7 / S08 6），与卡面非 S22 36 行一致。复跑：`work/step1_filter.py`。
- 复算方法：`work/step1_filter.py` 得行表 → `work/disasm.py` 逐行反汇编（EVIDENCE/disasm_<entry>.txt，skipdata=True）→ `work/skeleton.py`+`work/focus.py` 控流 → `work/body.py` 抽函数体 → 与 `work/make_delta.py` 内 CONTRACT 表对齐 → `work/make_delta.py` 出 delta（name 逐字节照抄，校验 36/36 PASS，grade 仅 [已证]）。
- **核心数字：实际处理 36 行；补语义 36 / 应降级 0。** 判据：36 行的 ③b 档位均已在各自审计裁决中入账（S08_KPROVED2 / S03_C4 / S03_C5 / S09_KPROVED / S09_KPROVED2 / S09_KPROVED3 / S10_KPROVED2），本卡逐行从 exe 字节复验锚点成立，无一行 grade↔语义不可证据化，故不触发降级。
- 应降级行：**无**。自检查的是「语义是否已证」而非「是否以 [静态推断] 开头」（R14_COMMON §8.6 条4）；36 行 delta 语义均含 ③b 档+锚，槽语义未证串已全部消除。
- 边际披露：006C9890/00631CC0/004E2690/004AAD30 的 ③b① 依 D-42 细则#1（≥3 互斥闸动作各异），非跳表；沿用已入账档位，敏感性见 UNKNOWNS.md。
- 随机抽 3 行可独立复算字节锚（file off = VA−0x400000 经 pefile 节表映射，本镜像 .text 起处 VA−fileoff=0x400000）：
  1. `0045A680 +0x54` = `8b5482fc`(`mov edx,[edx+eax*4-4]`) `+0x58`=`895487fc`(`mov [edi+eax*4-4],edx`) → file off `0x5A6D4` 起 `8b5482fc895487fc`（实测逐字节一致）。
  2. `004DB690 +0x11A` = `81ff02400080`(`cmp edi,0x80004002`) `+0x120`=`7406`(`je`) → file off `0xDB7AA` 起 `81ff024000807406`（实测一致）。
  3. `004D7170 +0x12A` = `8a9022010000`(`mov dl,[eax+0x122]`)、`+0x136`=`888822010000`(`mov [eax+0x122],dl`) → file off `0xD729A` 起 `8a9022010000fec24783ff0888902201`（实测一致）。
- 逐行处置（entry: 子系统 槽 → 档位/判定；全部「补语义」）：
  1 0045A680:S08 slot2→③b④ 深拷贝循环 | 2 0045A730:S08 slot4→③b②+④ 查找/-1哨兵 | 3 004A9840:S09 slot41→③b② -1哨兵 | 4 004A9DD0:S09 slot38→③b④ 双层8项循环 | 5 004AA050:S09 slot39→③b④ 双层8项循环 | 6 004AAD30:S09 slot49→③b①细则#1 7闸7helper | 7 004AAE90:S09 slot46→③b① 4界跳表 | 8 004ACE70:S09 slot32→③b④ RNG写回循环
  9 004D24A0:S08 slot6→③b④ 0x10步循环 | 10 004D2510:S08 slot5→③b④ 多源枚举 | 11 004D27D0:S08 slot3→③b② E_POINTER | 12 004D2810:S08 slot13→③b③ 14字段布局断言 | 13 004D7170:S10 slot54→③b④ +0x122计数写回 | 14 004D74E0:S10 slot81→③b① 13体跳表 | 15 004D7D50:S10 slot80→③b① 11体跳表 | 16 004D9960:S10 slot10→③b④ 左移写
  17 004DB3C0:S10 slot5→③b④ count/Items写 | 18 004DB690:S10 slot6→③b② E_NOINTERFACE | 19 004DF040:S10 slot330→③b④ 栈累加best | 20 004E2690:S09 slot27→③b①细则#1 字节/字双字形源 | 21 00552490:S03 LCW slot2→③b④ 解压I/O循环 | 22 00557730:S09 List slot42→③b④ 移除+左移 | 23 0055C7C0:S03 LZO slot2→③b④ 解压I/O循环 | 24 005BDF70:S09 Mouse slot30→③b④ 释放循环
  25 00631CC0:S03 FilePipe slot3→③b①细则#1 双向换绑 | 26 0063FB20:S09 Power slot16→③b④ 4段绘制循环 | 27 0063FEA0:S09 Power slot10→③b② -1字段哨兵 | 28 0065CAC0:S03 RawFile slot2→③b② 释放+清标志 | 29 0065CB50:S03 RawFile slot7→③b①+② mode三路 | 30 0065CCE0:S03 RawFile slot9→③b④ 打开I/O循环 | 31 0065D150:S03 CDFile slot3→③b② bool返回 | 32 006A5310:S09 Sidebar slot8→③b④ 4标志过滤循环
  33 006A5840:S09 Sidebar slot53→③b④ 单元布局循环 | 34 006A7780:S09 Sidebar slot10→③b④ 0x3c步循环 | 35 006C9890:S03 FileStraw slot1→③b①细则#1 5闸换绑 | 36 006D0680:S09 Tab slot10→③b①+④ 命令switch+循环
- 交付：PROGRESS.md、coverage_delta.tsv（36 行 6 列）、UNKNOWNS.md、DISAGREE.md、EVIDENCE\（36×disasm + INDEX/SKELETONS/FOCUS）、work\（8 脚本）。
