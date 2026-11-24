# PATCH-D35 · PROGRESS

卡号 PATCH-D35｜目录 `lead\next_re_20261117_r14\PATCH_D35\`｜2026-11-19｜真机锁 PATCH-D35（收尾释放）

## 1 洞的复算（独立从 exe 字节；脚本 work/recalc_cave.py）
- VA→偏移：`VA 0x7DF781 − ImageBase 0x400000 = RVA 0x3DF781`；`.text` 节 `VA=0x1000, RawPtr=0x1000, VSize=0x3DF38D, RawSize=0x3E0000`；`0x3DF781 ∈ .text` ⇒ 文件偏移 `0x1000+(0x3DF781−0x1000)=0x3DF781`。
- 63 B 内容：**全 `0xCC`，63/63，无例外**。maximal int3 run `[0x3DF781,0x3DF7C0)` 长度恰 63；前字节 `0x7DF780=0xC3(ret)`，后 `0x7DF7C0=0x55(push ebp)` 新函数序言。
- 函数区间包含判定（atlas 12,916，`[entry,entry+size)`，纪律 17 不用 `entry_at_or_before`）：**CONTAINING=NONE**，洞不在任何已知函数体内；前函数 `0x7DF640+243→0x7DF733`、后 `0x7DF7C0+242→0x7DF8B2`。
- **洞大小(63B)/内容(全int3)/边界与裁决 & VERDICT ★C 逐字相符 ⇒ 继续打补丁。**

## 2 打补丁（只打卡目录副本）
- 复制 `ra2youli\gamemd.exe`→`work\gamemd_patched.exe`，复制前后 SHA 实测相同 `73201CC0…F67476`。
- 写入 13B 共享桩（`85 c9 74 05 e9 a6 4f f4 ff 83 c4 04 c3`）+ 19B 块守卫（`a1 e0 71 88 00 85 c0 74 05 e9 2b e1 ee ff e9 37 e1 ee ff`）= 32B 于洞内 `[0x7DF781,0x7DF7A0)`，余 31B 保留 int3。
- 字节 diff（work/gen_diff_evidence.py → EVIDENCE/byte_diff.tsv）：全文件差异 **32** 字节，偏移 `0x3DF781..0x3DF7A0` 全部落在洞内；**洞外差异 = 0**。
- 副本 SHA-256 = `4EBC5195203140F4CECD0E9BE0DEA74A69A8388A5B2BC0D5651FF4BBA2C593BB`。
- **未做站点侧接线**（卡面"洞外 0 变化"铁规禁止）——洞内桩无调用者；此为授权边界内最大部署，见 DISAGREE #1 / UNKNOWNS #1。

## 3 有界真机冒烟（8 处，副本 work\run\gamemd.exe 启动）
- 副本能启动：窗口标题 "Yuri's Revenge"，证明进入游戏；资源复制到卡目录 run\（非原目录）。
- 8 处挑选依据：从 26 可达候选中取 static-ref + 冲突跳转 0 + CFG 路径最短者：`006D1632(11)/006D09FA(18)/00640427(31)/006D059B(38)/006D0634(39)/006D1293(46)/006D0940(47)/006D1308(50)`。
- 每处独立启动副本 + GUI 操作尝试覆盖宿主功能，判崩/不崩：**8/8 未崩**；except.txt 全部未新增/未变（26272 B，sha `6907F395…91094`）；无崩溃地址；rc=0 或存活（rc=0 为正常退出，非崩溃）。逐处见 SMOKE_TABLE.tsv / EVIDENCE/smoke_*.json。
- **限定**：常规 GUI 未把 `[0x887368]`/`[0x8871E0]` 置 NULL，且桩未接线 ⇒ "不崩"**不证明 NULL 路径安全**，仅表示"已观测到常规操作未崩、except 未新增"。

## 4 覆盖率
- **已冒烟 8 处 / 26 可达候选 = 30.8%；对 30 处 P1 = 26.7%；不宣称全覆盖。**
- 其余 18 可达 + 4 零静态引用 + `0x6CD8CD` 未冒烟，仅报覆盖率。

## 5 收尾复验
- 原 `ra2youli\gamemd.exe` SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` —— **未变**。
- 原目录 `gamemd.exe/except.txt/RA2MD.INI/BATTLEMD.INI` 指纹与开工基线逐字比对：**VIOLATIONS=NONE**（except.txt 26272 B 未变）。
- run 目录 except.txt 亦未变；无残留 gamemd 进程（count=0）。
- LIVE_LOCK：`PATCH-D35` → `RELEASED by PATCH-D35`。

## 6 一句话结论
**证据不足（洞已验证可零位移写入且洞外 0 变化、副本可正常启动、8 处冒烟未崩，但因卡面"洞外 0 变化"禁止站点侧接线使桩无调用者、且冒烟未真正触发 NULL，无法证明补丁可部署防崩）**——依据：EVIDENCE/byte_diff.tsv 洞外差异 0；SMOKE_TABLE.tsv 8/8 未崩但 except 未新增；DISAGREE #1 / UNKNOWNS #1-3。
