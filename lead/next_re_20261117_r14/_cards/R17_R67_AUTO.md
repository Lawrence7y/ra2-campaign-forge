# R17-R67 调度卡：唯一内容体量（SHA256 内容指纹去重）全量实测

## 硬性纪律与不变量
- 工作目录：D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14
- **t628 实时内存配额**：当前 t628 可用内存 1468.0 MB，初始可开子代理上限 = 4 个（t628 上派发子代理前必须先运行 harness-mem-budget 核对实时 MAX_SUBAGENTS，严禁超限）。
- 严格遵守：§2.8 A/B/C、§2.12 D/E/F、§2.30 纪律 30；严禁预估数字，所有数值必须先落盘实测后回填。
- 写入纪律：wx 独占备份（唯一名）到 R17_LEAD_BASELINE -> 断言旧 sha256 与 CR 不变量 -> 一次性写入 -> 回读校验。
- CR 不变量：R14_COMMON=1081、LEAD_LOCK=137、台账=337、STATUS_BOARD=0（总行数 <= 300）、BOARD_ARCHIVE=2952。
- 注意：当前 STATUS_BOARD.md 为 279 行（上限 300）。本轮必须先将板上最早的 2 段（R17 第 xx 轮）按 wx 独占备份+sha256断言逐字归档到 BOARD_ARCHIVE.md（保持 BOARD_ARCHIVE CR=2952，STATUS_BOARD CR=0），确认行数 <= 265 后再追加第 67 轮。

## 本轮实测任务（产物放 _r67/）
1. 在 _r67/ 编写并运行 dedup_corpus.py：
   - 读取权威清单 R17_R101_TIER_FINAL_4417/tier_final_4417.tsv（4,417 行，sum=737,517,286 B）。
   - 对全部 4,417 个文件逐一计算 SHA256（带正控验证 4 份已知 68,253 对 calls 文件 / 字节校验），统计：
     a) 唯一 SHA256 簇数与唯一内容总字节数（即 §2.71 定义的新口径「唯一内容体量」）；
     b) 重复文件总数与重复字节总量（含 Top 15 重复簇明细）；
     c) JSON 内部等值但序列化不同的补充说明（如 a2_sites.json 的 hex calls 与十进制 calls）。
   - 将清单输出到 _r67/unique_content_4417.tsv 并回读校验行数与 sum。
2. 四件套落盘：
   - 追加 R14_COMMON.md §2.73（全 LF，CR=1081）
   - 追加台账 GOAL_THREE_TARGETS_20261018.md §1122（CR=337）
   - 追加 LEAD_LOCK CV 段（CR=137）
   - 追加 STATUS_BOARD.md 第 67 轮记录（CR=0，行数 <= 300）
