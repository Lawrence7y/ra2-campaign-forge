# 任务 A：把五笔待入账草案（§605–§609）并入主台账

仓库：D:\Project\ra2-campaign-forge（Windows / PowerShell）。你是受限执行方，只按本任务书写盘。

铁律：
1) 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 attach、不读活进程内存，不写 hook / 采样 / MiniDump / SuspendThread / StackWalk 代码。
2) 只读边界：除写域外一律只读；禁止 git commit / push / reset / checkout；不得覆盖或删除既有件（要备份就备份到写域内）。
3) python 一律：python -I -X utf8 <绝对路径>；指纹用 hashlib 实算，禁止手写估计。
4) 每个数字追到「实跑命令+输出」或「文件:行」；拿不到就写「未验」，不补造。
5) 报告必须含「边界与未验」一节。
6) 收尾回执：改了哪些文件、跑了哪些命令、结论一句话、遗留未验项。

## 输入（只读）
- lead\ledger_bound_20261109\LEDGER_BOUND_VOLUME.md ← 主输入（5 笔草案正文、编号、依赖、冲突登记）
- lead\ledger_appendix_20261108\_la_SUMMARY.md 与 _la_draft1..4*.md ← 单件草案，可作逐字校对源
- 目标台账：lead\GOAL_THREE_TARGETS_20261018.md（约 9,758 行 / 759,518 B；基线 sha256=2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede）

## 写域
① lead\GOAL_THREE_TARGETS_20261018.md 的**文件末尾追加**（append-only，一个既有字节都不许改）；② 新建 lead\re_ledger_apply_20261111\（脚本、日志、回执、备份）。

## 步骤
1) 读合订本，取 5 笔草案的**逐字正文**与规定顺序/依赖/冲突处置。
2) 正文逐字照抄（不许改写/压缩/调措辞），编号保持 §605–§609；按合订本要求给 §609 加 unconfirmed 标记。
3) 用写域内的 python 脚本做**二进制末尾追加**（不要全文重写）：先算 before sha256/字节数，追加后再算 after。
4) 自检四条，逐条实测并贴输出：
   a. after 文件前 before_bytes 个字节的 sha256 == before 全文件 sha256（证明旧内容未动）；
   b. §605…§609 每个在全文恰好出现 1 次（grep 计数）；
   c. 追加段起止行号与追加字节数；
   d. UTF-8 读回成功，行数 = 旧行数 + 追加行数。
5) 若某笔与台账现状冲突（引用不存在的 § 号、与 §604 口径矛盾），**跳过该笔**并照实登记，其余照常入账，不得自行改写草案。

## 交付（写域内）
- APPLY_RECEIPT.md：逐笔状态表（已入账/跳过+原因）、before/after 指纹、追加行号、四条自检实跑输出、冲突与处置、「未做」清单（未改 PENDING_DECISIONS、未 commit、未 push、未动其它文件）。
- _apply.py / _verify.py 与其 stdout 落盘。
- GOAL_before.md 备份副本。