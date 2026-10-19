# QC213P2 探针扩展补丁 · 独立核验判定书

- 核验员：探针补丁核验员（subagent，独立通道/独立模型，与实现者不同）
- 日期：2026-10-19
- 被核目录：`lead\qc161_patch_QC213P2_20261019\`
- 被核件：`qc151_trip_qc213p2.py`（399,508 B）、`QC213P2_FIX.md`（12,803 B）、`RECEIPT.md`（6,677 B）
- live 母件（只读）：`lead\qc151_u0400_trip\qc151_trip.py`（381,363 B）
- 判读规格：`spawnfix9_freeze_20261019\WIPE_TRIGGER_ANALYSIS.md` §2.3/§5.1 + 「附：关键地址速查」
- 架构参照：`qc161_patch_QC213_20261018\QC213_FIX.md`
- 附加独立取证：`lead\qc161_u0400_trip\_src_variant_800x600_csf\gamemd.exe`（4,825,360 B，与 WIPE_TRIGGER_ANALYSIS.md §0 参照件同路径；本核验员未复测其 sha256，只按 WIPE 报告自述的 ImageBase 0x400000 做指令字节复核）

**总判定：CONFIRMED（7/7 核验点通过；3 条不影响判定的诚实申报类观察项见 §8）**

---

## §1 核验点 ① 锚与实物

| 件 | 命令 | 实测 sha256 | 字节 | LF | CR |
|---|---|---|---|---|---|
| live 母件 | `sha256sum …\qc151_u0400_trip\qc151_trip.py` | `37c1d4351cdf7033306a76892fcc19d2f7e182176e0205e1e67cadfa01470ad0` | 381,363 | 6,967 | 0 |
| 补丁副本 | `sha256sum …\qc151_trip_qc213p2.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 | 7,291 | 0 |

- 卡面锚 `37c1d435…` **实测命中**；副本 sha256 与 RECEIPT §2 / FIX 头部**逐字符一致**。
- 起跑前/收工后各测一次 live，两次同为 `37c1d435…` ⇒ **live 零改动**（补丁副本制成立）。

**结论：PASS。**

---

## §2 核验点 ② 反向重建

### 2.1 全文件差分（difflib，autojunk=False，行级）

```
opcodes: [('equal',0,3262,0,3262), ('insert',3262,3262,3262,3548),
          ('equal',3262,6623,3548,6909), ('insert',6623,6623,6909,6927),
          ('equal',6623,6671,6927,6975), ('insert',6671,6671,6975,6995),
          ('equal',6671,6968,6995,7292)]
ADDED_LINES=324  REMOVED_LINES=0  equal_lines=6968  (len差=324=增-删)
```

- 仅 **3 条 insert**，无 `replace`/`delete` ⇒ 既有行**零改动**、**324 纯增 / 0 删**（与 RECEIPT §3 / FIX §3 声称一致）。
- 三块定位：probe 锚 3262 行后（副本 3263-3548，含哨兵共 286 行 / 净内容 284 行）；arm 锚 6623 行后（副本 6910-6927，18/16）；finalize 锚 6671 行后（副本 6976-6995，20/18）。哨兵行本身计入块内，故 286+18+20=324 与 ADDED_LINES 吻合。

### 2.2 哨兵整块删除 ⇒ 逐字节还原

删三块（含 `# >>> QC213P2-BEGIN …` 与 `# <<< QC213P2-END …` 行）后重组：

```
rebuilt lines 6968 / live lines 6968      LINE-LEVEL MATCH True
rebuilt bytes 381363 / live bytes 381363  BYTE-IDENTICAL True
rebuilt sha 37c1d4351cdf7033306a76892fcc19d2f7e182176e0205e1e67cadfa01470ad0  sha-match True
```

**结论：PASS。**「删三块 QC213P2 ⇒ 逐字节还原 37c1d435」由本核验员独立复现，非转录。

---

## §3 核验点 ③ 探针语义对规格

### 3.1 VA→file_off 逐项对表（一律 VA−0x400000）

| 量 | 代码常量 | VA | 速查表/出处 | file_off | 对表 |
|---|---|---|---|---|---|
| RulesClass | `QC213P2_RULES_VA`（副本 3296 行） | `0x008871E0` | 速查「RulesClass」 | `0x004871E0` | MATCH |
| RulesClass+0x8E8 | 常量 `QC213P2_RULES_ARR8E8_OFF=0x8E8`（3297 行） | `0x008872C8`（速查表显式行） | 速查「RulesClass+0x8E8」 | `0x004872C8` | 见 §8-① |
| ShortGame 全局 | `QC213P2_SHORTGAME_VA`（3300 行） | `0x00A8B262` | 速查「ShortGame 全局」 | `0x0068B262` | MATCH |
| SessionClass | `QC213P2_SESSION_VA`（3301 行） | `0x00A8B230` | 速查「SessionClass」 | `0x0068B230` | MATCH |
| SessionClass+0x14B6 | 常量 `0x14B6`（3302 行） | `0x00A8C6E6` | 报告 §1.2（0x52D1F5 拷贝源） | `0x0068C6E6` | MATCH |
| HouseClass Items | `QC213P2_HOUSE_ITEMS_VA`（3304 行） | `0x00A8022C` | 既有 QC213 §1.1 | `0x0068022C` | MATCH |
| HouseClass Count | `QC213P2_HOUSE_COUNT_VA`（3305 行） | `0x00A80238` | 既有 QC213 §1.1 | `0x00680238` | MATCH |
| CurrentFrame | `MEASURE_CURRENT_FRAME_VA`（母件 2860 行，未改） | `0x00A8ED84` | 速查「frame 计数器」 | `0x0068ED84` | MATCH |

### 3.2 指令级复核（gamemd.exe 字节，file_off = VA−0x400000）

| VA | 指令 | 文件字节 | MATCH |
|---|---|---|---|
| `0x4F8EAC` | `mov eax,[esi+0x34]` | `8B 46 34` | ✓ |
| `0x4F8EAF` | `mov cl,[eax+0x1a6]` | `8A 88 A6 01 00 00` | ✓ |
| `0x4F8EBD` | `mov al,[0xa8b262]` | `A0 62 B2 A8 00` | ✓ |
| `0x4F8F4C` | `mov edx,[0x8871e0]` | `8B 15 E0 71 88 00` | ✓ |
| `0x4F8F54` | `mov eax,[edx+0x8e8]` | `8B 82 E8 08 00 00` | ✓ |
| `0x4F8F5A` | `mov eax,[eax+8]` | `8B 40 08` | ✓ |
| `0x4F8F61` | `mov ecx,[eax+0xdf8]` | `8B 88 F8 0D 00 00` | ✓ |
| `0x4F8F68` | `lea ecx,[esi+0x5550]` | `8D 8E 50 55 00 00` | ✓ |
| `0x4FC16C` | `mov edx,[0xa8b230]` | `8B 15 30 B2 A8 00` | ✓ |
| `0x4FC172` | `mov eax,[edx]` | `8B 02` | ✓ |
| `0x4FC174` | `test ah,8` | `F6 C4 08` | ✓ |
| `0x52D1F5` | `mov byte [0xa8b262],cl` | `88 0D 62 B2 A8 00` | ✓ |

⇒ P1/P2/P3/P5 的**偏移链与速查表/反汇编逐指令一致**；`list@0x5550` 的 `+0x4`(Array)/`+0x8`(上限)/`+0x10`(Count) 与 WIPE §1.4（`0x49FB60` 取 `[ecx+0x10]`、`0x49FAE0` 按 `[list+0x8]` 边界取 `[list+0x4][idx]`）一致。

### 3.3 P3 对齐修法正确性（0x00A8B262 校验）

- 代码（副本 3387-3388 行）：`_qc213p2_u8(handle, QC213P2_SHORTGAME_VA & ~3, QC213P2_SHORTGAME_VA & 3)`。
- `0x262 & 3 = 2` ⇒ 基址 `0x00A8B260`、取 **byte2**，即读 dword@`0x00A8B260` 后 `(v>>16)&0xFF`。**与卡面要求逐字一致。**
- 修法必要性独立复算：若不传 `&~3`，`_qc213p2_u8` 内部仍会对 `0x00A8B262` 做 `&~3` → 落到 `0x00A8B260` 且 `off&3=0` → 取 byte0（错位）。**RECEIPT §6.2 的诚实申报（初版错位→修正）成立。**
- 同族对齐点：`def1F5`(0x1F5&3=1)、`isHuman1EC`(0x1EC&3=0)、`ht1A6`(0x1A6&3=2)、`Session+0x14B6`(0x14B6&3=2) 全部经 `_qc213p2_u8` 统一对齐取字节，无第二处裸基址。

**结论：PASS。**（RulesClass+0x8E8 的速查表行自洽性问题见 §8-①，属规格书笔误，不影响本补丁读法正确性。）

---

## §4 核验点 ④ 架构合规

| 项 | 证据 | 判定 |
|---|---|---|
| `--measure`+NAV OK 门控 | arm 块（副本 6911 行）`if getattr(args,"measure",0) and _nav_verdict=="OK":` —— 与 QC213 arm（6902 行）逐字同构 | PASS |
| 无新增 CLI 开关 | 三块内 `add_argument` 计数 0；`--help` 输出与锚逐字节相同（见 §6） | PASS |
| 错误帽 | `QC213P2_ERR_CAP=3`；`_qc213p2_err`（3343-3352 行）达帽置 `done=True`。合成回放：6 个阶梯帧全坏 ⇒ error 行**恰 3** + `done=True` | PASS |
| off 直通零行为差异 | 3534-3535 行 `if not _QC213P2_PROBE["on"]: return _rpm_u32_qc213p2_base(handle, va)`；实测 off 时返回值 42 原样、锚调用恰 1 次、零 rec 行；off 时契约外异常**照锚语义传播** | PASS |
| readings 键=实际帧号 6 位零填 | `tag = f"p{frame:06d}_qc213p2"`（3360 行）；回放首帧 7 ⇒ 键 `p000007_qc213p2_kind`（非 `p000010_`），证实用实际帧号 | PASS |
| QC213 三点闩锁未破坏 | `QC213_LATCH_FRAMES` 实测仍 `(300,600,1800)`；P2 块内无 `_QC213_PROBE["latch_frames"]` 赋值；`_QC213P2_PROBE` 为独立 dict（`is not _QC213_PROBE`）；`--probe-frames` 仍只作用于 QC213（6931-6933 行未被改） | PASS |
| P4 独立阶梯设计 | `QC213P2_LADDER_SRC=(10,)+tuple(range(250,451))` → 去重升序 202 帧 → `_qc213p2_ladder_effective` 截 64 帧 = `(10,250…312)`，`DROPPED=138`；早闩/逐帧档/冻结三档分立，`latched` 字典去重 | PASS |

**结论：PASS。**

---

## §5 核验点 ⑤ 禁止面

三块内（probe 3263-3548 / arm 6910-6927 / finalize 6976-6995）子串计数：

```
WriteProcessMemory / VirtualProtectEx / VirtualAllocEx / CreateRemoteThread /
NtWriteVirtualMemory / RtlMoveMemory / memcpy / memset / time.sleep / Sleep /
keybd_event / SendInput / mouse_event / SetWindowsHookEx / WriteFile / OpenProcess /
CloseHandle / CreateProcess / WinExec / ShellExecute / subprocess / os.system /
socket / urllib / requests / http.client / ctypes / winreg / urlopen / popen /
SetWindowPos / WriteConsole / print(
⇒ 三块全部命中计数 = 0
```

- 块内 `time.` 仅 1 处：`time.monotonic()`（3484 行，冻结看门，**非 sleep**）。
- 块内 `import`/`from` 语句 **0** 条。
- 全部读数经 `_rpm_u32_qc213p2_base`（=QC213 包装=锚 `_rpm_u32`，锚 = `ReadProcessMemory` 只读，母件 2905-2921 行）与 `_qc213p2_u8`（3337-3340 行，对齐取字节）⇒ **全块只读 RPM**，零写入/零注入/零新句柄/零网络。
- rec 组名仅 `QC213P2`（21 处）与 `MEASURE`（2 处），未污染既有组。

**结论：PASS。**

---

## §6 核验点 ⑥ 冒烟复跑

| 项 | 命令 | 结果 |
|---|---|---|
| py_compile（副本） | `py_compile.compile(patch, cfile=%TEMP%\…\patch_x.pyc, doraise=True)` | **PASS**，pyc 390,463 B（与 RECEIPT §4① 声称的 390,463 B 一致） |
| py_compile（母件对照） | 同命令 | PASS，pyc 375,937 B |
| `argparse --help` | `subprocess.run([sys.executable, <src>, '--help'], cwd=%TEMP%, env=PYTHONDONTWRITEBYTECODE=1)` | rc 均 0；**stdout 4391 B 逐字节相同**（sha256 均 `18e4518bdf9937377c9ef03f7bc1e21536324bc7f7adef92a4f9ba3fb5d545db`）；`--measure`/`--probe-frames` 均在 |
| stderr | 同上 | 仅行号不同（母件 6856/5901/5896 → 副本 7180/6187/6182）；剥离行号与脚本路径后**逐字节相同** ⇒ 差异纯由插入行导致 |
| importlib exec + 常量 | `spec_from_file_location(...).exec_module(mod)` | 模块级常量全数落地：`LADDER_CAP=64`、`LADDER_SRC` 202 帧、`LADDER` 64 帧 `(10,250…312)`、`LADDER_DROPPED=138`、`ERR_CAP=3`、`FREEZE_S=2.0`、`on=False`、`QC213_LATCH_FRAMES=(300,600,1800)`、`MEASURE_CURRENT_FRAME_VA=0x00A8ED84`；地址/file_off 逐项等于 §1.1 表 |

### 6.1 合成地址空间回放（exec 真模块 + 猴子补丁 `_rpm_u32_qc213p2_base` 注入内存）

帧序 `7,10,249,250,251,252,252,300,450,313`，合成 4 屋（h0=Player/isHuman、h1=Computer、h2/h3=Neutral/Special），P1 链 `rules=0x30000000 → arr=0x12340000 → elem1=0x12350000 → idx=3`，`list@0x5550` cap=4/count=22、`[Array+4*3]=5`：

| 组 | 断言 | 结果 |
|---|---|---|
| A P1 | rules/arr8e8/elem1/elem1_null=False/idx_df8=3 | 5/5 PASS |
| B P1 | h0 c5550_count=22、h0 idx=1、h1 idx=5、h0 ge_cap=False | 4/4 PASS |
| C P2 | h0=0、h1=0、h2=1、h3=1 | 4/4 PASS |
| D P3 | glob=0、sess=0、equal=True | 3/3 PASS |
| E P5 | byte1=0x08、bit=0x08、set=True | 3/3 PASS |
| F P4 | h1 x2F0=0/c5574=242/c5588=92/def1F5=1/meta_count=4/h0 isHuman=1/h1 isHuman=0/h0 id30=0 | 8/8 PASS |
| G 键名 | `p000007_…_kind='early'`、`p000250_…_kind='latch250'` | 2/2 PASS |
| H 闩锁 | snapshots=[early@7, latch10/250/251/252/300]；latched={10,250,251,252,300}；latched_n=5；f252 仅 1 次；f450/f313/f249 零行；零 error 行 | 6/6 PASS |
| 场景 | idx≥cap ⇒ ge_cap=True 且 idx=0（0x49FAE0 扩容清零语义） | PASS |
| 场景 | Arr8E8[1]==0 ⇒ idx_df8/c5550_idx/ge_cap 全 `null`（不可测不写 0）、c5550_count 仍采 22 | PASS |
| 场景 | 冻结：帧钟 +1.9s 不触发、+2.5s ⇒ `frozen_final` + `done=True` | PASS |
| 场景 | 错误帽：6 个阶梯帧连续坏 ⇒ error 行**恰 3** + `done=True`、零快照 | PASS |
| 场景 | off 直通：返回值 42 原样、锚调用 1 次、零 rec 行；off 时异常照锚语义传播 | PASS |
| 场景 | on + 契约外异常：返回 None、`err=RuntimeError(...)`、`done=True`、记 `probe_error{kind:"exception"}` | PASS |

合计 **35+ 项逐值断言全 PASS**（首次跑出 29 项 FAIL 系本核验员 harness 把 `(group,key)` 二元组当键查询所致，非补丁缺陷；改用按键查询后全绿——此点如实记录）。

**结论：PASS。**真机数值（P1-P5 实读）**未验证**（本卡明确不做真机趟，与 RECEIPT §4「未做」一致）。

---

## §7 核验点 ⑦ RECEIPT/FIX 自洽

| 声称 | 复算 | 判定 |
|---|---|---|
| RECEIPT §2 产物 sha/字节/LF/CR | `qc151_trip_qc213p2.py` `517889c6…`/399,508/7,291/0；`QC213P2_FIX.md` `ac2f4ba3…`/12,803/179/0 | MATCH |
| RECEIPT §1 起跑/收工锚 | 两次实测 `37c1d435…`/381,363/6,967/0 | MATCH |
| FIX §3 hunk 表 286/18/20=324 | difflib ADDED_LINES=324、REMOVED=0 | MATCH |
| FIX §1.9 `QC213_LATCH_FRAMES` 仍 `(300,600,1800)` | importlib 实测 `(300,600,1800)` | MATCH |
| 遗留风险 1（LADDER_CAP=64 截断 f313-f450） | 实测 ladder 末帧 312、dropped=138；FIX §1.6 与 RECEIPT §6.1 均明示「未擅改」「跑前确认」 | 如实 |
| 遗留风险 2（P3 对齐修正） | §3.3 独立复算确认修正必要且正确 | 如实 |
| 遗留风险 3（P1 第 4/5 级 null） | 回放 S5 实测 null 传播 | 如实 |
| 遗留风险 4（无 CLI 开关） | `--help` 逐字节同 + 块内 0 个 `add_argument` | 如实 |
| 遗留风险 5（QC213 不覆写）/6（真机未验） | §4 表 + RECEIPT §4「未做」 | 如实 |

**结论：PASS。**四条（含 P3 修正共五条）遗留风险申报与实物/复算一致，无隐瞒、无夸大。

---

## §8 观察项（不影响判定，如实记录）

1. **速查表 `RulesClass+0x8E8` 行自洽性（规格书笔误，非补丁缺陷）**：速查表该行写 VA `0x008872C8`，但 `0x008871E0 + 0x8E8 = 0x00887AC8`（差 0xE8）。gamemd.exe 内 `0x008872C8` 全 .text 仅 1 处引用（`0x0040E6E4` `fstp [0x8872c8]`，属 `0x40E6C0` 起的浮点存取函数，与败北判据无关）；`0x00887AC8` 在 .text **0 处**绝对引用。**补丁的实际读法是 `rd32(RulesClass + 0x8E8)`，与 `0x004F8F54` 的指令字节 `8B 82 E8 08 00 00`（disp32=0x000008E8）逐字节吻合 ⇒ 读法正确**；副本 3270 行注释与 FIX §1.1 表中照抄的 `0x008872C8 / 0x004872C8` 是从速查表转录的**笔误地址**（应为 `0x00887AC8 / 0x00487AC8`）。该值仅出现在注释/文档，**不出现在任何代码路径**，故不影响功能；建议下一轮在速查表与 FIX §1.1 一并更正。
2. **`0x008871E0` 是运行时地址**：PE 区段显示该 VA 落在 `.data` 虚拟区（`0x412000..0x779BE4`）**之外**（磁盘 file_off `0x4871E0` 实为 `.rsrc` 区），即 RulesClass 指针槽属运行时填充区；磁盘上读到的 `0x0080FFFF` 无意义。速查表「VA→file_off 一律 −0x400000」是**运行时映像内偏移**口径，对 RPM 读成立，对磁盘静态读不成立 —— 与探针用法无冲突（探针全部走 RPM）。
3. **首轮回放 harness 自误**：本核验员首次回放出现 29 项 FAIL，根因是自建 recorder 字典以 `(group,key)` 为键却按键查询；修正后全绿。已如实记录，未据此对补丁作任何结论。

---

## §9 逐点结论汇总

| # | 核验点 | 判定 |
|---|---|---|
| ① | 锚与实物（live 双测 37c1d435 未动；副本 517889c6） | **PASS** |
| ② | 反向重建（删三块⇒37c1d435 逐字节；324 纯增/0 删） | **PASS** |
| ③ | 探针语义对规格（P1 四级解引 + list@0x5550 按 0x49FAE0；P2 [H+0x34]+0x1A6；P3 0x00A8B262&~3+byte2 与 [Session+0x14B6] 对读；P5 byte[1]&0x08；VA→file_off −0x400000 逐项对表 + 指令级字节复核） | **PASS** |
| ④ | 架构合规（门控/错误帽=3/off 直通零差异/键=实际帧号 6 位零填/QC213 三点闍锁保留/P4 独立阶梯） | **PASS** |
| ⑤ | 禁止面（三块内 WPM/sleep/OpenProcess/网络/subprocess 等 30 类令牌全 0；全块只读 RPM） | **PASS** |
| ⑥ | 冒烟复跑（py_compile PASS + `--help` stdout 逐字节同 + 合成回放 35+ 断言全 PASS） | **PASS** |
| ⑦ | RECEIPT/FIX 自洽（四条+一条遗留风险如实） | **PASS** |

**未做 / 不可验项（如实标注）**：真机趟与 P1-P5 真机读数（本卡明确不做，`UNVERIFIABLE`）；`_nav_verdict`/`args.measure` 的真机链路只在 `--help` 与源码门控表达式层面核验，未跑真机 nav 链；`gamemd.exe` 自身 sha256 未复测（沿用 WIPE 报告自述的 ImageBase 0x400000 做指令字节复核）。

---

## §10 复算命令（复核用）

```
python -c "import hashlib;d=open(r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py','rb').read();print(hashlib.sha256(d).hexdigest(),len(d),d.count(b'\n'),d.count(b'\r'))"
python -c "import hashlib;d=open(r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_patch_QC213P2_20261019\qc151_trip_qc213p2.py','rb').read();print(hashlib.sha256(d).hexdigest(),len(d),d.count(b'\n'),d.count(b'\r'))"
python -c "import difflib;a=open(r'…\qc151_u0400_trip\qc151_trip.py',encoding='utf-8').read().split('\n');b=open(r'…\qc161_patch_QC213P2_20261019\qc151_trip_qc213p2.py',encoding='utf-8').read().split('\n');sm=difflib.SequenceMatcher(None,a,b,autojunk=False);ops=sm.get_opcodes();print(ops);print('ADD',sum(j2-j1 for t,i1,i2,j1,j2 in ops if t=='insert'),'REM',sum(i2-i1 for t,i1,i2,j1,j2 in ops if t in('delete','replace')))"
```

本核验员全程**只读**母件与补丁副本；唯一仓库内写入 = 本判定书；测试脚手架全部落在 `%TEMP%`（`qc213p2_verify_*` / `qc213p2_help_*`）。

**收工清理（如实申报）**：本核验员用 `importlib.util.spec_from_file_location(...).exec_module()` 复跑常量与合成回放时，Python 在默认字节码缓存策略下于被核目录生成了 `__pycache__\qc151_trip_qc213p2.cpython-312.pyc`（mtime 2026-10-19 23:54:39，390,463 B）——这是核验员自身脚手架的副产物，**不是实现者交付物**（交付时目录仅三件）。已 `rm -rf __pycache__` 清除，收工后被核目录恢复为四件（三件交付 + 本判定书）。母件 `lead\qc151_u0400_trip\qc151_trip.py` 收工复测仍为 `37c1d435…`/381,363 B，零改动；`lead\qc151_u0400_trip\__pycache__\qc151_trip.cpython-312.pyc` 的 mtime 为 2026-10-19 19:11:38（早于本核验员起跑），非本核验员生成，未触碰。
