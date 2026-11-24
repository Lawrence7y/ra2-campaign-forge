# S04-PUSH B2 PROGRESS

时间基准（本机 Asia/Shanghai）：2026-11-20。

## 执行纪律
- 先建目录、先写 REPORT 骨架；每核完一行立刻落盘 `EVIDENCE/ROW_<entry>.txt` 与 delta 行；每 5 行追加进度到本文件。
- 不修改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 下产物；只写 S04_PUSH_B2\。
- entry 大写十六进制不带 0x；禁止整批共用 reason；类名取不到写 未取得；余量 6 行，宁严不宽。

## 进度
- [x] 读完卡片 S04-PUSH.md（全文 76 行）
- [x] 材料自校验：gamemd.exe SHA256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476；Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；.text=[0x401000,0x7E038D)
- [x] 筛选：S04 共 73 候选，按 entry 升序取第 19–36 行 = 18 行（work/filter_b2.py → work/b2_entries.tsv）
- [x] 建立 S04_PUSH_B2 目录 + REPORT 骨架（18 行待核表）
- [x] 全局索引构建（work/build_index.py）：RTTI 1219 vtables / 6692 entries；1,392,592 指令 / 68,253 E8（与基准一致）；livevt 401
- [x] 逐行原始证据 dump（work/dump_rows.py → work/dump_<entry>.txt × 18）

### 逐行核完（每 5 行追加）
- [x] **1–5 行**（00523C90 / 00523D00 / 00525430 / 00525A60 / 00526B10）核完并落盘：
  - 00523C90：②未取得 + ③ stricmp 分支/③a → 否
  - 00523D00：②未取得 → 否
  - 00525430：②构造链可定 TypeList&lt;int&gt;，但 ③b②/③b③/③b④ 三型全败 → 否
  - 00525A60：②未取得(vt 写栈) + ③模板假句 → 否
  - 00526B10：③b② 强(NULL 哨兵 br15/16) 但 ②未取得(this 栈局部无 vt) → 否
  - 四环齐全累计 0/5
- [x] **6–10 行**（00533D20 / 005E6520 / 005FA620 / 006418B0 / 00641B00）核完并落盘：
  - 00533D20：②未取得(vt 写栈 CCINI/CCFile) → 否
  - 005E6520：②未取得(ecx=int 索引；vt 写栈) → 否
  - 005FA620：②未取得 → 否
  - 006418B0：②未取得(vt 写栈 Pipe/BufferPipe) → 否
  - 00641B00：②未取得(vt 写栈 Straw/BufferStraw) → 否
  - 四环齐全累计 0/10
- [x] **11–15 行**（00641EE0 / 00644890 / 00645820 / 0067A090 / 0067A110）核完并落盘：
  - 00641EE0：②未取得(vt 写栈) → 否
  - 00644890：②未取得(拷贝赋值壳) → 否
  - 00645820：②未取得 → 否
  - 0067A090：②未取得 + ③ new 分配模板假句 → 否
  - 0067A110：②未取得 + ③ 模板假句 → 否
  - 四环齐全累计 0/15
- [x] **16–18 行**（0067A190 / 0067A210 / 0067A290）核完并落盘：
  - 三行均为同族 121B 拷贝赋值壳：②未取得 + ③ 模板假句 → 否
  - 四环齐全累计 0/18

## 二次自证（防假阴性）
- ② 环用两套独立实现复算 dword_refs / RTTI vt 槽：自建 `build_index.entry2slots`（1219 表/6692 entry）+ B1 `witness_core.find_dword_refs+resolve_slot` ⇒ 18/18 全 0，交叉一致（`work/slot_check2.json`）。
- RTTI 读法遵 技术⑦：`COL+0xC→TD`，TD+8 内联名串逐字符读，非指针解引用；`to_this` 判定按「ecx→esi/ebp 序言溯源」（违纪律 14/16 的坑已规避）。
- 构造链 vt 写目标逐条核对 `[esp+..]` vs `[this+off]`，避免错源 ㉓/㉔（atexit 死表、差分检验）。
- capstone 无 index 陷阱（错源 ⑲）：索引脚本按 `op.mem.index` 处理，0-index 视作无 index，自检已知阳性 call。

## 最终产出
- [x] EVIDENCE/ROW_<entry>.txt × 18（逐行地址锚，reason 各行不同）
- [x] S04_delta.tsv 仅表头（0 数据行）
- [x] base_rate.tsv（batch=B2, rows_checked=18, all_four_rings=0, rate=0.0000）
- [x] REPORT.md 完整总表
- [x] 答复：核 18 行 / 四环齐全 0 行 / 产出 S04_PUSH_B2\
