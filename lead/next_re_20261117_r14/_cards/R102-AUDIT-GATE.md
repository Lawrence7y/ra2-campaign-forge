R102 审计卡 · 门禁加严是否真的加严了（找主会话的错）

## 你的任务

主会话本轮对 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py
做了一次「纯加严」改动。你的任务是**证伪它**：找出它不是加严、或者加严得不够、或者引入了
新的假判据的地方。你的价值在于抓错，不在于确认。

## 主会话声称做了什么（这就是要审的对象）

C1 新增 C12 检查：把 DISC_UNVERIFIABLE.tsv（冻结档，12 行）的第 4 列「校验式」**真跑一遍**，
   并要求：冻结 id 必须在 DISC_RECHECK 里以「有」开头、理由非空、冻结时刻严格 ISO8601(+HH:MM)。
   理由：此前门禁只读冻结档第 1 列（id）+ sha256 钉整档，第 4 列校验式从不执行。

C2 把 C6MAX 接线：此前 --c6max=N 被 argparse 解析但全脚本无人读取（AST Load=0），
   docstring 却写「超阈值即 FAIL」。现在 cross > C6MAX 就 FAIL。

C3 GATE_VER 从 R87 抬到 R102，并同步 DISC_RECHECK.tsv 第 20 行校验式里的字面版本号
   （因为 C7 会真跑那一行、C10 会比对注册值）。

C4 输出横幅从硬编码的「--- check_disc.py (R49) ---」改成由 GATE_VER 派生。

主会话还声称：这些改动今天全绿，所以不改变 exit 0；并给出 25 项前提断言 + 17 项沙箱控制组。

## 你要具体查的六点

A1 拿去真跑：现在真门禁是否仍 exit 0？python3 check_disc.py 输出里 C12 / C6 threshold /
   横幅 / C10 四处的实际文本各是什么？逐字抄。

A2 C12 是否**能被触发**？自己造沙箱（/tmp 下，symlink 真树 + 只复制三个可变态）把冻结档某行的
   第 4 列改成必不命中的正则，同步改 FREEZE_SHA256 常量，看是否 FAIL。再做一个反向：
   同样坏档但用「改前的门禁」（备份在 R17_LEAD_BASELINE/R102.before_check_disc_C12_*.bak）
   是否 exit 0 —— 若 exit 0，则证明 C12 确实新增了鉴别力，而不是本来就会被别处抓到。

A3 C12 有没有**误判风险**？重点看：它复用了 C7 的 run_expr。若冻结档某行的校验式写成
   exists（存在式） 类或 bytes=N 类（而非 grep=），run_expr 的分支是否都仍然正确？把 run_expr 的
   四个分支逐条对着冻结档现有 12 行过一遍，有几行走哪个分支？

A4 C6MAX 接线有没有把**默认行为**改掉？默认 120、实测 cross=9。若将来 cross 增长到 121，
   门禁会 FAIL —— 这是加严还是可能误伤？给出你的判断与理由（不要只说「可能」）。

A5 有没有**新的假旋钮**留下？用 AST 扫 check_disc.py 里所有模块级名字，列出「被赋值但
   Load 次数为 0」的常量。逐个判断：它是死代码、还是文档承诺但没实现（后者更糟）。

A6 一致性：docstring 顶部（第 1-21 行）对检查项的描述，与改后代码的实际行为是否一致？
   尤其 C1..C11 的措辞。逐条列出「文档说了但代码没做」或「代码做了但文档没写」的项。

## 硬要求

- 不要读 _r102 目录下的任何脚本（那是被测方的实现细节，读了会锚定）。你可以读被改的文件本身
  与它的备份，可以读 DISC_RECHECK.tsv / DISC_UNVERIFIABLE.tsv / recheck_verify.py / place_r87.py。
- 每个结论都要有可复跑命令 + 实际输出。禁止「应该」「大概」。
- 明确区分「我实测到的」与「我推断的」。推断必须标 [推断]。
- 产物写到 lead/next_re_20261117_r14/_r102_audit/ 下（新建），命名 AUDIT102.md + 脚本 + json。
- AUDIT102.md 末尾给一节「我认为主会话最可能错在哪」，最多三条，每条给复现步骤。

## 边界

- 只读真树，只写 /tmp 与你自己的产物目录。严禁修改 check_disc.py / DISC_RECHECK.tsv /
  DISC_UNVERIFIABLE.tsv 的真身。
- 不要碰 LEAD_LOCK / R14_COMMON / GOAL_THREE_TARGETS / STATUS_BOARD。
- 不要分析 harness / server.py / re_guardian / re-tool 源码。
