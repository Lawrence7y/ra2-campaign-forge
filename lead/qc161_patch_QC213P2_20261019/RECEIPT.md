# QC213P2 构建回执（RECEIPT）

- 日期：2026-10-19
- 构建员：探针补丁构建员（subagent，非真机执行者）
- 交付目录：`lead\qc161_patch_QC213P2_20261019\`
- 制式：**补丁副本制**（live 文件零改动）

---

## 1. 锚（起跑前 / 收工后各实测一次）

| 时点 | 文件 | sha256 | 字节 | LF | CR |
|---|---|---|---|---|---|
| 起跑前 | `lead\qc151_u0400_trip\qc151_trip.py` | `37c1d4351cdf7033306a76892fcc19d2f7e182176e0205e1e67cadfa01470ad0` | 381,363 | 6,967 | 0 |
| 收工后 | 同上 | `37c1d4351cdf7033306a76892fcc19d2f7e182176e0205e1e67cadfa01470ad0` | 381,363 | 6,967 | 0 |

- 卡面声明锚前 8 位 = `37c1d435` ⇒ **实测命中，未 STOP**。
- 收工后复测相同 ⇒ **live 文件零改动**（本次唯一写入 = 交付目录三件）。

命令（两次相同）：
```
python -c "import hashlib;d=open(r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py','rb').read();print(hashlib.sha256(d).hexdigest(),len(d),d.count(b'\n'),d.count(b'\r'))"
```
输出（起跑前）：`37c1d4351cdf7033306a76892fcc19d2f7e182176e0205e1e67cadfa01470ad0 381363 6967 0`
输出（收工后）：同上，逐字段相同。

## 2. 产物 sha

| 件 | sha256 | 字节 | LF | CR |
|---|---|---|---|---|
| `qc151_trip_qc213p2.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 | 7,291 | 0 |
| `QC213P2_FIX.md` | `ac2f4ba340fce5447d2998b51726b986711f50a5f351ff0b11426a560a150232` | 12,803 | 179 | 0 |
| `RECEIPT.md` | 本文件（自哈希不内嵌，见 §6 复算命令） | — | — | — |

## 3. hunk 清单

| hunk | 补丁副本行区间 | 行数 | 插入点（锚行号，1-based） | 内容 |
|---|---|---|---|---|
| A | 3263-3548 | 286 | 锚 3262 之后（`# <<< QC213-END probe` 之后） | `# >>> QC213P2-BEGIN probe … # <<< QC213P2-END probe` |
| B | 6910-6927 | 18 | 锚 6623 之后（`# <<< QC213-END arm` 之后） | `# >>> QC213P2-BEGIN arm … # <<< QC213P2-END arm` |
| C | 6976-6995 | 20 | 锚 6671 之后（`# <<< QC213-END finalize` 之后） | `# >>> QC213P2-BEGIN finalize … # <<< QC213P2-END finalize` |

- 全文件 `difflib` 差分：`ADDED_LINES=324`、`REMOVED_LINES=0`（286+18+20=324）；`get_opcodes` 仅三条 `insert`，无 `replace`/`delete`。
- **反向重建**：按哨兵整块删除三块 ⇒ 381,363 B / `37c1d435…` / **MATCH True**（逐字节还原）。

## 4. 自测记录（均在 `%TEMP%`，零落仓库）

| # | 项 | 命令 | 结果 |
|---|---|---|---|
| ① | `py_compile` | `py_compile.compile(patch, cfile=%TEMP%\qc213p2_final_*\x.pyc, doraise=True)` | **PASS**（pyc 390,463 B） |
| ② | `argparse --help` 冒烟 | `subprocess.run([sys.executable, patch, '--help'], cwd=%TEMP%, env=PYTHONDONTWRITEBYTECODE=1)` | **PASS**（rc=0；stdout 与锚 `--help` **逐字节相同**；stderr 仅行号不同：锚 6856/5901/5896 → 补丁 7179/6186/6181，因插入行导致） |
| ③ | importlib exec + 常量 | `importlib.util.spec_from_file_location(...).exec_module` | **PASS**（阶梯 64 帧 / 丢弃 138；`on=False`；地址与 file_off 逐项等于 FIX §1.1） |
| ④ | 反向重建 | 哨兵整块删除 + sha256 | **PASS**（`37c1d435…` MATCH True） |
| ⑤ | 合成地址空间回放（P1/P2/P3/P5/P4） | `%TEMP%` 内 exec 真模块 + 猴子补丁 `_rpm_u32_qc213p2_base` | **PASS 22/22** |
| ⑥ | 闩锁/早闩/冻结/错误帽/off 直通 | 同上 | **PASS**（5 场景，见 §5） |
| ⑦ | 禁止面扫描 | 三块内子串计数 | **PASS**（`WriteProcessMemory`/`VirtualProtectEx`/`VirtualAllocEx`/`CreateRemoteThread`/`time.sleep`/`keybd_event`/`SendInput`/`mouse_event`/`SetWindowsHookEx`/`WriteFile`/`OpenProcess`/`CloseHandle` 全为 **0**） |

**未做**：真机趟（卡面明确不做）。P1-P5 真机读数未验证。

## 5. 合成回放明细（可复核口径）

- P1 解引链：`rules=0x30000000 → arr=0x12340000 → elem1=0x12350000 → idx=3`；h1 `[list+0x4][3]=5`、`Count=22` ⇒ 7/7 PASS。
- P2：h0=0 / h1=0 / h2=1 / h3=1 ⇒ 4/4 PASS。
- P3：glob=0 / sess=0 / equal=True ⇒ 3/3 PASS。
- P5：byte1=0x08 / bit=0x08 / set=True ⇒ 3/3 PASS。
- P4：h1 `x2F0=0` / `c5574=242` / `c5588=92` / `def1F5=0` / `meta_count=4` ⇒ 5/5 PASS。
- 闩锁：帧序 `7,10,249,250,251,252,252,300,450` ⇒ `early` 于 f7；`latched={10,250,251,252,300}`；252 重拍不重采；313（非阶梯）零行。
- 冻结：帧钟不变 5 s ⇒ `frozen_final` + `done=True`。
- 错误帽：`count=100` 连续 5 拍 ⇒ error 行**恰 3** + `done=True`。
- off 直通：返回值 42 原样、锚调用 1 次、零快照。

## 6. 诚实申报与遗留风险

1. **P4 阶梯帽截断（设计取舍，非缺陷但影响覆盖面）**：`QC213P2_LADDER_SRC = (10,) + range(250,451)` 共 202 帧，超 `QC213P2_LADDER_CAP=64` ⇒ 实际生效 `(10, 250…312)`，**f313-f450 不采**，`ladder_dropped=138`。卡面要求「>64 帧窗自动截断并记 note」⇒ 已按要求实现并留痕。若真机趟需覆盖到 f450，须改常量（`QC213P2_LADDER_SRC` 收窄或 `QC213P2_LADDER_CAP` 调高），**本补丁未擅改**，请在跑前确认。
2. **P3 对齐读取修正**：初版全局 ShortGame 读基址未对齐（会读 `0x00A8B260` byte0）；合成回放 FAIL 后改为 `VA & ~3` + `VA & 3` 移位。已重拼并全绿。如实记录。
3. **P1 第 4/5 级依赖前级**：`Arr8E8[1]==NULL` 时 `p1_idx_df8` 与 `p1_c5550_idx` 均落 `null`（不可测，不写 0）——这与 §5.1 预测「NULL 或计数 0」兼容，但**无法用本探针区分**「NULL」与「计数 0」两种情形下的同一结论；区分靠 `p1_elem1_null`。
4. **未新增 CLI 开关**：阶梯只能改常量（`QC213P2_LADDER_SRC`/`_CAP`），不能命令行给；这是刻意的（镜像 QC213 门控、避免新增旗标面）。
5. **QC213 原探针不覆写**：`QC213_LATCH_FRAMES` 仍 `(300,600,1800)`；`--probe-frames` 仍只作用 QC213。两套探针同帧并行，readings 键前缀可区分。
6. **真机未验**：本件只证明 instrument 正确（读法/哨兵/键名/去重/收口），不预设 P1-P5 真机数值。

## 7. 复算命令（复核用）

```
python -c "import hashlib;p=r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_patch_QC213P2_20261019\qc151_trip_qc213p2.py';d=open(p,'rb').read();print(hashlib.sha256(d).hexdigest(),len(d),d.count(b'\n'),d.count(b'\r'))"
python -c "import hashlib;p=r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_patch_QC213P2_20261019\RECEIPT.md';d=open(p,'rb').read();print(hashlib.sha256(d).hexdigest(),len(d))"
```
