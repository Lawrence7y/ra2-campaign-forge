# NAMED-PUSH — S01 + S03 批次 B1（有名字的 ③b② 候选）· 报告

> 状态：**完成**（逐行核完即落 EVIDENCE；5/5 行全核，1 行四环齐全产出）。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（80 行全文读完）。
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem∈{S01,S03}` AND `p3b2_named==True`，排除 `fn_`/`sub_` 地址式伪名，按 entry 升序。两子系统合计仅 5 行，一次批 B1 覆盖全部。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S01S03_B1`

## 材料自校验
- 目标：`ra2youli\gamemd.exe`；`Get-FileHash -Algorithm SHA256` = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ⇒ 与卡片期望逐字一致。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅作候选线索）、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 5 个 entry）

```powershell
cd D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14
python -c "import csv; rows=[r for r in csv.DictReader(open(r'SURVEY_3B2/hits_detail.tsv',encoding='utf-8'),delimiter='\t') if r['subsystem'] in ('S01','S03') and r['p3b2_named']=='True']; bad=lambda n: bool(__import__('re').match(r'^(fn|sub)_[0-9A-Fa-f]{8}$',n)); rows=[r for r in rows if not bad(r['name'])]; rows.sort(key=lambda r:int(r['entry'],16)); print('total=',len(rows)); [print(r['subsystem'],r['entry'],r['name']) for r in rows]"
```
- 结果：`total=5`（卡片记 S01 有名字 1、S03 有名字 4，一致）；`fn_`/`sub_` 伪名剔除 **0** 行（本池 5 个名字均为真名或 `Class::slotN`）。按 entry 升序：

| # | entry | subsystem | name | grade(原始) |
|---|---|---|---|---|
| 1 | 00432050 | S03 | CDFileClass::vslot12 | 静态推断 |
| 2 | 0065D240 | S03 | CDFileClass::slot15 | 静态推断 |
| 3 | 0065D3A0 | S03 | RawFileClass::slot0 | 静态推断 |
| 4 | 007BA530 | S03 | FileStraw::slot2 | 静态推断 |
| 5 | 007CD80F | S01 | WinMainCRTStartup | 静态推断 |

## 判定口径（严格 D-40）

1. **①入口**：entry 在 `.text` 内、函数边界自洽、capstone `skipdata=True` 首条对齐。
2. **②类身份**：`.rdata/.data` 中 entry 作 4B VA 的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD(VA,非RVA)` → `TD+8` **内联**装饰名串；要求 `slot_off/4 == 线索槽号`（`vslotN`/`slotN` 的 N 仅作线索，须字节复算钉死）。类名钉不死判 FAIL。
3. **③整体合同**：只认 ③b。③b② 可伪证返回约定（多值状态码 / Find 返 -1 下标约定算；`{0,1}` 布尔不算）；③b① 跳转表逐路可验；③b④ 完整循环 I/O 带边界检查且循环体内有非栈写。禁 eax 覆写、多路同一 call、模板假句、③a。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源。② 锚 `.rdata` RTTI 数据链（COL/TD/槽），④ 锚 `.text` 构造安装指令字节 ⇒ 不同源。
5. **㉓ 析构器陷阱**：枚举该虚表**全部**写点，若 ④ 锚点只落在 atexit 注册的全局析构器或删除析构器（含 `D0`/`D1`）⇒ ④ FAIL。
6. **小成员表陷阱**：小成员表 vtable 不是主虚表（主表 slot0 常见 `00410260`）；只认带合法 COL(sig=0)+RTTI 类串的主表。

## 本批总表（逐行核完）

| # | entry | subsystem | name | ① | ② | ③b | ④ | 四环齐全 | 产出 | 证据 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00432050 | S03 | CDFileClass::vslot12 | ✓ | ✓ CDFileClass RTTI | ✓(③b④) | ✓ | **是** | **是** | EVIDENCE/ROW_00432050.txt |
| 2 | 0065D240 | S03 | CDFileClass::slot15 | ✓ | ✓ CDFileClass RTTI | ✗(布尔/长度判断) | ✓ | 否 | 否 | EVIDENCE/ROW_0065D240.txt |
| 3 | 0065D3A0 | S03 | RawFileClass::slot0 | ✓ | ✓ RawFileClass RTTI | ✗(析构布尔/标志) | ✓ | 否 | 否 | EVIDENCE/ROW_0065D3A0.txt |
| 4 | 007BA530 | S03 | FileStraw::slot2 | ✓ | ✓ FileStraw RTTI | ✗(布尔判断) | ✗(㉓锚落析构) | 否 | 否 | EVIDENCE/ROW_007BA530.txt |
| 5 | 007CD80F | S01 | WinMainCRTStartup | ✓ | ✗(全镜像 0 引用) | 未计入 | ✗ | 否 | 否 | EVIDENCE/ROW_007CD80F.txt |

## 逐环裁定依据（每行自身地址锚；字节见 EVIDENCE/ROW_<entry>.txt）

### ① 入口
5/5 entry 全在 `.text`（0x432050 / 0x65D240 / 0x65D3A0 / 0x7BA530 / 0x7CD80F 均 < 0x7E038D），capstone `skipdata=True` 首条对齐、末条 ret/jmp，函数边界自洽 → 全 PASS。

### ② 类身份（本批关键增量）：4/5 钉死，S01 1 行物理不可得
S03 4 行全部由「entry 作 4B VA 的 .rdata 虚表槽 → [vt-4]=COL(sig=0) → [COL+0xC]=TD(绝对VA) → TD+8 内联类名字串」独立钉死，且 slot_off/4 复算与线索槽号逐行自洽：
- `00432050` 槽 007E1698(vt 007E1668+0x30，slot#12)→COL 007FA4D8→TD 00815E38→`.?AVCDFileClass@@`；另在 BufferIOFileClass vt 007E3A2C slot#12。
- `0065D240` 槽 007E16A4(vt 007E1668+0x3C，slot#15)→同一 COL/TD→`.?AVCDFileClass@@`；另 BufferIOFileClass(007E3A68)、RawFileClass(007F0940) 同 slot#15。
- `0065D3A0` 槽 007F0904(vt 007F0904+0，slot#0=D0)→COL 00808790→TD 00815DF8→`.?AVRawFileClass@@`。
- `007BA530` 槽 007E4D98(vt 007E4D90+0x8，slot#2)→COL 007FCD30→TD 0081BFC8→`.?AVFileStraw@@`。
- S01 `007CD80F`：全镜像 4B VA 搜索 **0 命中**，无槽/无 COL/TD/类串。它是 CRT 入口 WinMainCRTStartup（全局函数），真名但无类身份 ⇒ ② FAIL。与 S04 的 fn_ 伪名同类「物理不可得」，但成因不同（此处是全局启动函数而非地址式标签）。
> 技术条复核：pTD=[COL+0xC] 存的是绝对 VA（如 0x00815E38），非 RVA；装饰名取 TD+8 处内联串（0x00815E40='.?AVCDFileClass@@'），不是指针。

### ③ 整体合同（只认 ③b）：1 行成立
- **`00432050` = ③b④ 成立**：本函数体内一条完整缓冲 I/O 循环（回边 0043224A `test ebx,ebx; jne 004320B9`），循环体 004320B9..0043224C 内有①边界检查 004320C3 `cmp ebx,edi`/004320C5 `jge`（edi=min(请求字节,剩余容量)）、②I/O 调用 00432175 `call 0x7CA090`(memcpy)、0043210B/0043211A 虚 I/O、③**循环体内非栈写** 0043214C `mov [esi+0x38],0`、004321AE `mov [esi+0x38],eax`、004321C0 `mov [esi+0x4c],ecx`（esi=this 对象字段，写在本函数循环体内，非被调内部）。未把被调内部写当循环写，非 ③a。
- `0065D240`/`0065D3A0`/`007BA530` FAIL：全部可分支站点都是 {0,1} 布尔（test al/eax；neg/sbb/neg 布尔归一化）或零值/长度判断（D-46(A)）或句柄 -1 标志，不是可伪证多值错误码/Find -1 下标约定；析构器行（0065D3A0）为模板假句。无 ③b① 跳表、无 ③b③ 内存形状断言、无合格 ③b④ 循环。
- 可伪证性口径遵守：行2 的 `call [0x7E1128]`→0x40FD6E 返「计数/长度」，`test; je` 是零值判断不算；行4 三处 `call [virt]`→`test al; jne/je` 是 0/1 布尔不算。
- 三陷阱排查：无「比较后 eax 被 mov 覆写再分支」可用站点；多路同一 call 未计入；无「对象初始化/清零」模板假句被误当 ③b。

### ④ 使用 witness：3 行成立，1 行触发 ㉓ 析构器陷阱
- `00432050`/`0065D240`：vt 007E1668 的构造期安装点 0047A9E3（in 0047A9D0，先 call 基类构造 0x431B20 再装本表，atexit=[]，非析构）；00432050 另有 direct caller 00473B07，0065D240 另有 direct caller 00473F14。
- `0065D3A0`：vt 007F0904 的构造安装点 0065CAA8（in 0065CA80，初始化字段后装本表，atexit=[]）；D0(0065D3A0)/D1(0065CA00) 析构排除。
- `007BA530` **FAIL（㉓ 实测触发）**：vt 007E4D90 的全部写点仅 007BA596 一处（in 007BA590），逐条看该函数==入口装本表→释放子 Straw→call 基类析构 0x6C9850→ret，是析构器/清除器，构造期无非析构安装路径 ⇒ ④ 锚点落在析构器 ⇒ 按卡面否决。
- `007CD80F`：direct caller=0、无 vtable 安装点 ⇒ FAIL。
- **②④ 不同源**：②④ 齐全行中，② 锚 .rdata RTTI 数据链（COL/TD/槽字节），④ 锚 .text 构造安装指令字节（或行外 direct caller），段/地址/产物类型均不同，未复用同一虚表槽。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）
- **S04**：73 个 ③b② 机械命中全部 `named=0`，entry 作 4B VA 镜像 0 命中、无虚表槽、无 RTTI 链 ⇒ ② 物理不可得，30+ 行实测全败。
- **本批 S01+S03**：5 行里 **4 行 ② 被 RTTI + 虚表独立钉死**（S03 4/4；slot_off/4 与线索槽号逐行自洽），证明「有名字 + 非伪名」确实解开 S04 的 ② 死结；S01 的 1 行（WinMainCRTStartup）虽是真名但为全局 CRT 函数，② 物理不可得，与 S04 同类。
- 瓶颈位置：本批 ② 从 S04 的 0 → 4/5；但 ③ 只成立 1 行（00432050 的 ③b④ 循环），其余被 {0,1} 布尔/零值判断/析构模板假句挡下；④ 在 1 行上触发 ㉓ 析构器陷阱。最终四环齐全 1 行。

## 汇总
- rows_checked：**5**（S03 4 + S01 1）
- ② 钉住行数：**4**（S03 4/4；S01 0/1）
- ③b 成立行数：**1**（00432050，③b④）
- ④ 成立行数：**3**（00432050/0065D240/0065D3A0；007BA530 ㉓ FAIL，007CD80F 无）
- all_four_rings（严格 D-40）：**1**，rate = 1/5 = **0.2000**
- delta 产出：**1 行**（`00432050`，[已证]）
- 分子系统：S03 核 4 行 / 四环齐全 1 行；S01 核 1 行 / 四环齐全 0 行
- `base_rate.tsv`：`NAMED_PUSH_S01S03_B1  5  4  1  3  1  0.2000`

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（1 数据行）
- `EVIDENCE/ROW_<entry>.txt` × 5（逐行四环地址与字节，每行独立锚点）
- `work/`：`filter.py`、`recore.py`、`core2.py`、`pass1.py`..`pass7.py` 及各自 .txt/.json（全部可复跑）
