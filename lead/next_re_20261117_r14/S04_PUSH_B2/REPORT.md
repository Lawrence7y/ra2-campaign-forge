# S04-PUSH — B2 批次（攻 S04 的 proved 增量，候选第 19–36 行）

> 状态：**DONE**。执行纪律已守：先建目录、先写骨架、逐行核完立即落盘 EVIDENCE 与 delta 行。
> 卡片：`lead\next_re_20261117_r14\_cards\S04-PUSH.md`（全文 76 行读完）
> 本批：B2 = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S04` 的 73 行按 entry 升序取第 **19–36** 个（1-based，含两端），共 18 行。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B2\`（卡片中的 S04_PUSH_B1 一律替换为本目录名）

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`；Python 3.12.10 / capstone 5.0.7（skipdata=True）/ pefile 2024.8.26
- gamemd.exe 现场复算 SHA-256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（一致）
- ImageBase 实测 `0x400000`，`.text` VirtualAddress `0x1000`、VirtualSize `0x7DF38D` ⇒ `.text=[0x401000,0x7E038D)`（一致）
- 全镜像扫描规模：1,392,592 条指令 / 68,253 个 E8@指令边界 / 6,728 distinct direct 目标（与 SURVEY_RING24 卡 §33 基准逐格一致 ⇒ 扫描完备，符合错源 ㉖ 自洽要求）

## 筛选命令（写进报告）
候选来源 `SURVEY_3B2\hits_detail.tsv`（只当线索）。筛选脚本落盘 `work/filter_b2.py`：
```python
import csv
SRC = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
rows = []
with open(SRC, encoding="utf-8") as fh:
    for row in csv.DictReader(fh, delimiter="\t"):
        if row["subsystem"] == "S04":
            rows.append(row)
rows.sort(key=lambda x: int(x["entry"], 16))
b2 = rows[18:36]   # 第 19–36 行（1-based 含两端）= 0-based [18,36)
```
结果：S04 共 **73** 行；B2 = 第 19–36 行共 **18** 行，entry 依次：
`00523C90 00523D00 00525430 00525A60 00526B10 00533D20 005E6520 005FA620 006418B0 00641B00 00641EE0 00644890 00645820 0067A090 0067A110 0067A190 0067A210 0067A290`。

## 判定口径（严格，宁严不宽；余量仅 6 行）
1. **①入口**：entry 在 `.text` 内、函数边界自洽（atlas size + 自写 CFG extent）。
2. **②类身份**：RTTI 名（`COL+0xC→TD+8` 内联名串）/ 虚表归属 / 构造链；**取不到写 `未取得` 并判该行不成立**。
3. **③整体合同**：**只认 ③b**。③b②=可伪证错误码/返回约定且调用方真拿它分支；③b①=跳转表每条路径可单独验证；③b③=内存形状断言（D-42 门槛 ≥2 张 vt 写 或 ≥10 字段布局断言）；③b④=完整循环 I/O 带 **per-iteration 边界检查** 且循环体内有非栈写。禁 ③a；禁「被调用者内部的写」当循环内非栈写；禁模板假句。
4. **④使用见证**：真实调用者或活虚表派发（构造器装活表、`vt[slot]==entry`、site 不共用、非 atexit 析构表），**direct-only 不足**。
5. **D-40 新禁则**：② 与 ④ 必须来自两条**独立**证据链；**同一虚表槽不能既证明类身份又证明被使用**。
6. 三陷阱主动排查：`eax` 覆写；多路同一 call（仅参数不同）；模板假句。
7. 每行必须有自身地址锚，禁止整批共用 reason；类名取不到写 `未取得`，不许编。

## 本批 18 行总表（entry / ① / ② / ③ / ④ / ②-④独立 / 裁定 / 是否产出）

> 图例：①入口 / ②类身份(RTTI名·虚表归属·构造链) / ③整体合同(③b) / ④使用见证 / 任一环 FAIL ⇒ 不进 delta。余量仅 6 行 ⇒ 拿不准判 FAIL。

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④独立 | 裁定 | 产出 |
|---|---|---|---|---|---|---|---|---|---|
| 19 | 00523C90 | sub_00523C90 | ✓ | 未取得(refs0/slot0；构造链无) | ✗(stricmp 分支/③a) | direct-only(7) | n/a | **③不成立+②未取得** | 否 |
| 20 | 00523D00 | sub_00523D00 | ✓ | 未取得(refs0/slot0；构造链无) | ✓形(branch)但②缺 | direct 1 | n/a | **②未取得** | 否 |
| 21 | 00525430 | sub_00525430 | ✓ | ✓构造链 TypeList&lt;int&gt;(VT 7E4DD8) | ✗(③b②br0/16；③b③1vt+6字段<门槛；③b④无上界检查) | direct 16 | n/a | **③不成立** | 否 |
| 22 | 00525A60 | sub_00525A60 | ✓ | 未取得(vt写栈/局部非this) | ✗(模板假句/br0) | direct-only(3) | n/a | **②未取得+③模板假句** | 否 |
| 23 | 00526B10 | sub_00526B10 | ✓ | 未取得(refs0/slot0；this为栈局部无vt归属) | ✓强(③b②NULL哨兵,br15/16) | direct 16(真实) | n/a | **②未取得**(③强但不救②) | 否 |
| 24 | 00533D20 | sub_00533D20 | ✓ | 未取得(vt写栈临时,this字段0) | ✗(INI读取分支/br0) | direct-only(3) | n/a | **②未取得** | 否 |
| 25 | 005E6520 | sub_005E6520 | ✓ | 未取得(ecx为int索引;vt写栈) | ✗(INI解析分支/br1) | direct 22 | n/a | **②未取得** | 否 |
| 26 | 005FA620 | sub_005FA620 | ✓ | 未取得(refs0/slot0；构造链无) | 内部分支 | direct 1 | n/a | **②未取得** | 否 |
| 27 | 006418B0 | sub_006418B0 | ✓ | 未取得(vt写栈Pipe/BufferPipe) | ✗(管道分支/br0) | direct 2 | n/a | **②未取得** | 否 |
| 28 | 00641B00 | sub_00641B00 | ✓ | 未取得(vt写栈Straw/BufferStraw) | ✗(br0) | direct 1 | n/a | **②未取得** | 否 |
| 29 | 00641EE0 | sub_00641EE0 | ✓ | 未取得(vt写栈CCINI/Straw) | ✗(br0) | direct 3 | n/a | **②未取得** | 否 |
| 30 | 00644890 | sub_00644890 | ✓ | 未取得(refs0/slot0；拷贝赋值壳) | 弱(br2/17) | direct 17 | n/a | **②未取得** | 否 |
| 31 | 00645820 | sub_00645820 | ✓ | 未取得(refs0/slot0；构造链无) | 内部分支(br0) | direct 1 | n/a | **②未取得** | 否 |
| 32 | 0067A090 | sub_0067A090 | ✓ | 未取得(拷贝赋值壳,无vt归属) | ✗(new分配模板句/br0) | direct 42 | n/a | **②未取得+③模板假句** | 否 |
| 33 | 0067A110 | sub_0067A110 | ✓ | 未取得(同族拷贝赋值壳) | ✗(new分配模板句/br0) | direct 5 | n/a | **②未取得+③模板假句** | 否 |
| 34 | 0067A190 | sub_0067A190 | ✓ | 未取得(同族拷贝赋值壳) | ✗(new分配模板句/br0) | direct 1 | n/a | **②未取得+③模板假句** | 否 |
| 35 | 0067A210 | sub_0067A210 | ✓ | 未取得(同族拷贝赋值壳) | ✗(new分配模板句/br0) | direct 1 | n/a | **②未取得+③模板假句** | 否 |
| 36 | 0067A290 | sub_0067A290 | ✓ | 未取得(同族拷贝赋值壳) | ✗(new分配模板句/br0) | direct 6 | n/a | **②未取得+③模板假句** | 否 |

## 逐行裁定依据（摘要；完整四环地址与字节见 `EVIDENCE/ROW_<entry>.txt`）
- **② 环是全批系统性败因**：18/18 行的 entry 在全部数据段作为 dword 出现次数 = 0（`work/slot_check2.json`，用 `witness_core.find_dword_refs + resolve_slot` 与自建 `build_index.entry2slots` 两套独立实现复算一致）⇒ RTTI 名与虚表归属一律「未取得」。按卡片「取不到就写未取得，并判该行不成立」直接否决。
- **构造链通道逐行核查**（`work/ctor_deep_*.txt` / `work/ctorchain_*.txt`）：7 行体内确有可解析 RTTI 的 vt 立即数写入，但逐一核对写目标——
  - `00525430`：唯一 `to_this=True`（+0xEE/+0x16B `mov [esi],0x7E4DD8`，esi=ecx=this，RTTI `.?AV?$TypeList@H@@`）⇒ 构造链可定类 `TypeList<int>`，② 成立；但其 ③ 三型全败（详见下行）。
  - `00525A60`/`00533D20`/`005E6520`/`006418B0`/`00641B00`/`00641EE0`：vt 写全部落在 `[esp+..]` 栈临时或其它局部对象，`this+字段写`=0，构造链不能给本函数定类名 ⇒ ② 未取得。
  - 其余 10 行函数体 0 处写已知 vt，构造链无。
- **00525430 的 ③ 三型全败**（本批最接近的行，单独说明）：③b② 的 `call@0x52545C→test@0x525461→je@0x525463` 是 stricmp 分支，调用方 0/16 分支其返回（构造器无返回契约被消费）；③b③ 只 1 张 distinct vt（同值写 3 次）+6 个 this 字段，低于 D-42「≥2 vt 或 ≥10 字段」门槛；③b④ 回边 `jne@0x52550B→0x5254A0` 体内 `mov [ecx+eax*4],edi` 有非栈写，但 `cmp ecx,ebx/jle@0x5254A2` 测的是 `[esp+0x20]` 而非写索引上界，缺 per-iteration 边界检查。⇒ 不成立。
- **③b② 最强行 00526B10**（NULL 哨兵 + 15/16 调用方分支）仍因 ② 未取得（this=ebp 为调用方栈局部，本函数不自写 vt、不虚派发 ebp）被否决——严格执行「任一环 FAIL 即否决」，不因单环强而放宽。
- **0067A090–0067A290 五连族**：121 字节同构拷贝赋值壳，`call new@0x67A0B3→test@0x67A0BE→je@0x67A0C0` 是分配失败分支，语义属「对象初始化」模板假句，且 0 调用方分支其返回 ⇒ ③ 不成立；② 亦未取得。命中卡片「模板假句」与「多路同一 call」双陷阱。

## 汇总
- 核完行数：**18/18**
- 四环齐全（严格 D-40）行数：**0**
- 产出 delta 行数：**0**（`S04_delta.tsv` 仅表头）
- 系统败因：18/18 ② 环 RTTI 名/虚表归属未取得；构造链仅 1 行可定类但该行 ③ 三型全败。
- 结论：本批 18 行无一对 S04 proved 有可辩护增量；余量 6 行全部保留给后续批次，不虚报。

## 输出清单
- `S04_delta.tsv`（仅表头；0 数据行）
- `EVIDENCE/ROW_<entry>.txt` × 18（每行四环地址与字节 + 逐行裁定）
- `REPORT.md`（本文件）、`PROGRESS.md`（每 5 行追加）、`base_rate.tsv`
- `work/`（筛选/取证/复算脚本与中间产物：filter_b2.py、build_index.py、dump_rows.py、analyze_callers.py、ctorchain.py、slot_check2.py、ctor_deep.py、make_facts.py、gen_evidence.py、index.json、dump_*.txt、facts_final.tsv 等）
