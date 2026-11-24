# PATCH-D35R · PROGRESS（≤70 行）

卡号 PATCH-D35R｜目录 `lead\next_re_20261117_r14\PATCH_D35R\`｜2026-11-20｜真机锁 PATCH-D35R（收尾释放）

## 1 复用上一张 + 站点复算
- 读 PATCH_D35 的 PROGRESS/PATCH_REPORT/SMOKE_TABLE/byte_diff/UNKNOWNS/DISAGREE：确认 63B int3 洞 `[0x7DF781,0x7DF7C0)` 与 13B 共享桩 + 19B 块守卫逻辑；上一张因「洞外 0 变化」未接线、桩无调用者 ⇒ 本卡只补站点侧接线。
- 从 PATCH_MAP.tsv + CANDIDATES.md 复算 8 站点（指令边界、原 `E8 rel32 call 0x724730`、前一条 `mov ecx,[0x887368]` 无 NULL 守卫）：0x6D1632 / 0x6D09FA / 0x640427 / 0x6D059B / 0x6D0634 / 0x6D1293 / 0x6D0940 / 0x4A8B75（末者替换上一张 0x6D1308，因其菜单 GUI 不可达；0x4A8B75 为 PATCH_MAP 首行、reach=True）。
- 站点用 `E8 rel32`（保留 call 操作码）改指向洞内桩：卡面「E9 或等效」的等效形式；`E9` 会破坏桩尾 `ret 4` 依赖的返回地址（见 DISAGREE #1）。

## 2 打补丁（只打副本，EVIDENCE/hashes.txt）
- 原 exe SHA `73201CC0…F67476` 开工/收尾两次实测一致、未变；副本 `work\gamemd_r2.exe` SHA `36A87577…C7F4`（run 目录同名 exe 同 SHA）。
- 洞内写入 30B 桩（test ecx/jz/tail-jmp/add esp,4/ret + 只读观测副作用）+ 19B 块守卫（逻辑同上一张）；余 14B 保留 int3。桩的观测副作用写 `.data` 零填充 `0x9F5000/0x9F5004`（文件中无字节，0 条代码引用，安全填充）。
- 8 站点各写 `E8 rel32 → 0x7DF781`。全文件逐字节 diff：差异 **73 B** = 洞内 49 B + 站点 24 B；**越界差异 0**。

## 3 diff 集合证明（EVIDENCE/byte_diff_full.tsv）
- 允许集合 = 洞 `[0x3DF781,0x3DF7C0)` ∪ 8 站点 `[site_off,site_off+5)`；逐差异行标注 CAVE/SITE，`outside_allowed_set_diff_count=0`。差异集合 ⊆ 允许集合，且洞内、站点内差异真实存在 ⇒ 恰为 {洞}∪{8站点}。无越界。

## 4 有界真机冒烟（8 站点，SMOKE_TABLE_R2.tsv）
- 副本从 `work\run\` 启动；最小启动集 11 MB（临时硬链接 16 大 mix 使游戏到达 "Yuri's Revenge" 主菜单，收尾全删）。
- 桩执行证据办法：桩内 `inc [0x9F5004]` 计数 + `mov [0x9F5000],retaddr`；进程外 `ReadProcessMemory`（VM_READ）只读采样，无 WriteProcessMemory/注入/断点。
- 逐站点结果（崩/不崩 + 桩是否确认执行）：
  - 0x6D1632：不崩；**无法证明桩被执行**（未捕获 ret 0x6D1637；in-game sidebar 未到达）。
  - 0x6D09FA：不崩；**无法证明桩被执行**（未捕获 ret 0x6D09FF）。
  - 0x640427：不崩；**无法证明桩被执行（最终 build）**（中间 build 曾见 0x64042C，非最终 build 不计）。
  - 0x6D059B：不崩；**无法证明桩被执行**（未捕获 ret 0x6D05A0）。
  - 0x6D0634：不崩；**无法证明桩被执行**（未捕获 ret 0x6D0639）。
  - 0x6D1293：不崩；**无法证明桩被执行**（未捕获 ret 0x6D1298）。
  - 0x6D0940：不崩；**无法证明桩被执行**（未捕获 ret 0x6D0945）。
  - 0x4A8B75：不崩；**桩执行已确认**：`hit_count 0→2`、`last_ret=0x4A8B7A`(=站点+5)，641 次连续只读采样，证据 EVIDENCE/smoke_r2_diag_sites.json。
- except.txt 全程 26272 B / sha `6907F395…91094` 未变；无崩溃地址；进程由本卡关闭。

## 5 覆盖率
- 已接线 8 站点；桩执行已确认 **1/8 = 12.5%**；其余 7 站点已冒烟但证据不足。其余 22 个 P1 候选 + 块站点未接线未冒烟；不宣称全覆盖。

## 6 收尾复验
- 原 `ra2youli\gamemd.exe` SHA `73201CC0…F67476` 未变；16 个大 mix SHA 逐文件未变；原/副本 except.txt 未变；gamemd 残留进程 count=0；run 目录清理回 11.07 MB；LIVE_LOCK `PATCH-D35R` → `RELEASED by PATCH-D35R`。

## 7 一句话结论
**不能证明补丁防崩**——依据：站点接线与严格 diff 已验证（73B 差异全在 {洞}∪{8站点}、越界 0），且仅 1/8 站点（0x4A8B75）经只读 counter 取得「桩确实执行」证据（hit_count 0→2、last_ret=0x4A8B7A）；其余 7 站点无法证明桩执行、NULL 路径未被真机触发，故「未崩」不构成 NULL 防护证据，按铁规不得外推为防崩。
