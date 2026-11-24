# R17-R66 调度卡：直接调用漏点 (0x007C8B3D, 0x0074836A) 根因验证 + sweep.installs 口径裁定

## 目标与规则约束
- 工作目录：D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14
- 严格遵守：§2.8 A/B/C（正反控、单源降级、第三方裁决）、§2.12 D/E/F（审计须复算、函数体窗口须到首个 ret 且带正控、字符串断言须完整窗口）、§2.13（锚落点）、§2.30 纪律 30（集合比对前先统一表示并打印归一化前后命中数）。
- 严格遵守写入纪律：所有被修改文件先在 R17_LEAD_BASELINE 用 wx 独占备份（唯一时间戳名）-> 断言旧 sha256 与 CR 不变量 -> 一次性写入 -> 回读校验。
- CR 不变量（改完必须保持不变）：
  - R14_COMMON.md: CR=1081
  - lead/LEAD_LOCK: CR=137
  - lead/GOAL_THREE_TARGETS_20261018.md: CR=337
  - STATUS_BOARD.md: CR=0 且总行数 <= 300（本轮必须先归档再追加！）
  - BOARD_ARCHIVE.md: CR=2952

## 本轮实测任务（产物放 _r66/）
1. 在 _r66/ 编写并运行 verify_r66.py：
   - 对 ra2youli/gamemd.exe 中 VA 0x007C8B00..0x007C8B70（含目标点 0x007C8B3D）与目标函数 0x00748350..0x00748390 做 capstone x86-32 反汇编（带正控 0x0040100A -> 0x00407100），并读取 PE 段表确认 0x007C8B3D 所在节区（如 .text / .rdata / .data / .rsrc 或函数边界归属）。
   - 比对 a2_sites.json、scan_mine.json、e8_sites_audit.json、sweep.json 四个文件中的调用点集合，查明 (0x007C8B3D, 0x0074836A) 在哪几份中出现/缺失，并给出归一化前后对照及根因结论（不许猜，必须用真实字节与脚本输出证成）。
   - 对 S08_KPROVED2/_audit/EVIDENCE/sweep.json 的 installs（6,226 条 / 序列化 248,114 B）抽取代表条目到 gamemd.exe 原始字节做双控核验，并裁定其是否已在 F24 磁盘体量（sweep.json 总字节 1,631,944 B）内或需否另计。
2. 先归档看板再追加：
   - 因 STATUS_BOARD.md 当前为 298 行（上限 300），先将 R17 第 57 轮和第 58 轮段落逐字归档至 BOARD_ARCHIVE.md（保持 BOARD_ARCHIVE CR=2952，STATUS_BOARD CR=0），确认归档后看板行数 <= 270。
3. 四件套落盘（所有数字先实测再填，禁止预估）：
   - 追加 R14_COMMON.md 的 §2.72（全 LF，CR=1081）
   - 追加台账 lead/GOAL_THREE_TARGETS_20261018.md 的 §1121（保持 CR=337）
   - 追加 lead/LEAD_LOCK 的 CU 段（保持 CR=137）
   - 追加 STATUS_BOARD.md 的第 66 轮记录（全 LF，CR=0，总行数 <= 300）
4. 最后实测并打印五项 CR 不变量 + 看板总行数，全部通过方可结束。
