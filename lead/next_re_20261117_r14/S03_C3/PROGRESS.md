补齐 7 行 ③（0065CAC0 / 004324B0 / 00552490 / 006C9890 / 00631CC0 / 0065D150 / 00431E80）

# S03-C3 进度记录
- 卡号 S03-C3；执行员 agent-57；写域仅 S03_C3/ 与 _ghidra/S03-C3/（本卡只用前者）。
- 目标 ra2youli/gamemd.exe 只读（SHA-256 73201CC0…7476）；python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26；未建 venv、未 pip install、未 import 他卡 work 代码。
- 必读已核：R14_COMMON §8 错源 ⑲⑳㉑㉒（+㉓–㉖）/§8.4/§8.5；PENDING D-40（`lead/PENDING_DECISIONS.md:540`）；本卡 CARD.md 正文。

## ① 核心结果
- **补齐③行数 = 7/7**；每行重写语义栏、盘上 name 一字不动；grade `[静态推断]→[已证]`（① 入口 + ② RTTI + ③ 整体合同 + ④ direct call 四环齐）。
- 每行 ③（带指令偏移）/② 链/④ 站点全文：`EVIDENCE/THREE_RING_CONTRACTS.md`；`coverage_delta.tsv` 8 列。

## ② ⑨ 停机核验（盘上 coverage.tsv 实算）
- coverage.tsv 18,431 数据行；S03 纯 coverage 196 = `[已证]`18/`[静态推断]`110/`[未证]`68；atlas∩S03 194 = 18/108/68。
- 7 行盘上值逐字复核：subsystem=S03、grade=`[静态推断]`、name 与卡面表完全一致（⑨ 通过）。

## ③ ⑲ 自检 + 扫描覆盖（错源 ㉖）
- capstone 5.0.7：`hasattr(op,"index")=False`；`op.mem.index` 无 index 返 **0**，`is None=False`。
- `.text` 按 VirtualSize 全扫 0x401000..0x7E038D：**1,392,592 指令 / 68,253 E8@边界 / raw E8 81,715**，与卡面基准逐字一致；扫到 SizeOfRawData 会多 1,594 条零填充，未扫。
- 48 个 direct 站点（3+1+10+9+10+11+4=48）逐字节复核 100% OK；evidence: `EVIDENCE/rtti_sites_verified.json`（48 站点）与 `EVIDENCE/scan_scale_verified.json`。

## ④ ② RTTI 类属（字节实读，fail-closed 全过）
- 7 行 `[vt-4]=COL → [COL+0xC]=TD → TD+8 内联串` 全部读出，`vt[slot]==entry` 全成立；7 行 liveness 全 `live`。
- 00631CC0 为三链共享实现（SHAPipe/FilePipe/BufferPipe），盘上名 FilePipe::slot3 由 `.?AVFilePipe@@`@vt 007E4DA0 slot3 直接支撑，名字不动。

## ⑤ ④ 使用见证（direct call，全 OK）
- 判据：E8@指令边界 + site+5+rel32==entry + caller 在 `[entry,entry+size)` 外（非自环）；逐站点字节见 `EVIDENCE/rtti_sites_verified.json`。
- 站点数：0065CAC0 3 / 004324B0 1 / 00552490 10 / 006C9890 9 / 00631CC0 10 / 0065D150 11 / 00431E80 4。004324B0 的站点 caller 00473BA0 为 `[已证]`。

## ⑥ 随机基线（同子系统内随机取同样多行）
- 从 S03 的 108 行 `[静态推断]` 随机取 7 行、判据=①②④（direct+RTTI）：基率 31/108=28.70%，E[7]=2.01，10 seed 实测 mean 2.3。
- 从 S03 全部 194 行 atlas∩coverage 随机取 7 行：基率 36/194=18.56%，E[7]=1.30，10 seed mean 1.1。
- ③ 在盘上补前 0/194（四环不齐）⇒ 同判据补前 E[7]=0；本卡 7 行是 S03-CRITERION 审计预选集，非随机抽样。
- **未按**「随机 VA 命中 target」算（那是地址算术 0.166%，对语义零信息）；`EVIDENCE/random_baseline.json`。

## ⑦ ⑱ 按 entry 查全库冲突（只报不改名）
- 命中 15：台账 §35765 行的「7 行待补③」清单（7 条）、coverage.tsv 自身 7 行、台账 §20586 行把 006C9890 记在 `File_Stream_Crypto` 表（D-37 归属分歧，见 DISAGREE.md）。docs/re/ 与 re_atlas/kb/ 内 0 命中。

## ⑧ 严禁项自查
- 未以 direct call 单独升 grade（每行齐 ①②③④）；未用 atexit 析构器表；未做槽号匹配/slot-baseline；未用 P=R=100%/恰命中 N 自证；未写进程内存/硬件断点。

## ⑨ 交付
- `PROGRESS.md` / `UNKNOWNS.md` / `DISAGREE.md` / `coverage_delta.tsv` / `EVIDENCE/` / `work/`。
