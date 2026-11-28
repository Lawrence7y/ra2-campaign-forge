# R220-C 取证：check_disc.py 现态复测 + 12 个永不 FAIL id 的判据来历（执行员 hy4，只读）

## 角色
只读取证员。**不要修改任何项目文件**（尤其不要改 check_disc.py 与四件套）。
你的临时脚本与报告写到 /home/t628/projects/ra2-campaign-forge/_r220/ ，文件名前缀 C_ 。
工作目录 /home/t628/projects/ra2-campaign-forge 。

## 待取证（全部实测，禁止预估）
T1. 现态复测：直接运行 python3 lead/next_re_20261117_r14/check_disc.py（如需要参数先看 --help 并用其默认口径），
    用一条命令把退出码、stdout 全量（若 >200 行则给头尾各 80 行 + 总行数）、stderr 全量一起输出。
    报告：总检查项数量、PASS 数、FAIL 数、SKIP 数，以及每个 FAIL 的 id 与文字。
T2. 12 个「永不 FAIL」id 的来历：在 check_disc.py 中找出所有检查项注册处（形如 CHECKS 列表/装饰器/函数名约定），
    给出被登记的 id 全集（排序后完整列出，是一共多少个也要说清）。
    然后判定哪些 id 的判据函数在**任何输入下都不可能返回 FAIL**，判据是：函数体里没有 raise/AssertionError/return False 分支，
    或者其比较对象是常量对常量，或者它 return 的布尔量不被上层使用。
    对每个这样的 id 输出：id、函数名、行号、判据为空的具体行、为什么恒 PASS 的一句话说明。
    特别核实 id 3 / 4 / 22 / 27 / 28 这五个（历史称「窗口表问题」）现在到底是 PASS 还是 FAIL，逐个给出现态。
T3. 找自然真实行：对 T2 里每个恒 PASS 的 id，给出「如果要把判据改成真判据，应该断言的现成数据来自哪里」——
    只允许引用仓库里已经有的事实文件（例如 out/reverse/FACT_INDEX*.tsv、C16_FLOORS、gate_runner 配置等），
    给出文件路径 + 具体行号或键名，不要自己编造期望值。找不到现成数据就写「无现成数据源」。
T4. C7 三死分支：在 check_disc.py 里找出所有形如「if ...: return PASS」而 else 分支不存在的分支，给出行号与上下文 3 行。
    C20 realpath/inode 一致性：找出该检查的实现行，说明它比较的是什么（realpath？inode？sha256？），给出实际代码行。
T5. 正反控：
    正控 —— 把 check_disc.py 复制到 /tmp/ 下，人为破坏一个已知会被检查的文件（例如把 FACT_INDEX_CURRENT 指针指向一个不存在的版本号），
    再跑该副本，确认至少有一个 id 从 PASS 变 FAIL（证明该 id 判据是活的），报告是哪个 id。
    反控 —— 不做任何破坏直接跑 /tmp 副本，报告其 PASS/FAIL 与 T1 是否完全一致（应当一致）。
    恢复：/tmp 副本改完即弃，不要动项目目录里的任何文件。

## 输出
- _r220/C_report.md：T1..T5 的实测输出与结论。
- _r220/C_result.json：{总项数, pass, fail, skip, fail_ids, never_fail_ids, c7_branches, c20_impl}
- 一句话结论：现态门禁是否真的能拦住回归；如果不能，最小可行修补点在哪一行。
