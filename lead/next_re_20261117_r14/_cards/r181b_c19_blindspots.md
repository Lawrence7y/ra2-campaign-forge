# r181b 只读复核卡：在主门禁里加一条「事实层联动」断言 C19 的盲区盘点

## 背景（主会话已实测，可独立复算但不必推翻）

root = /home/t628/projects/ra2-campaign-forge

- 主门禁 lead/next_re_20261117_r14/check_disc.py（1059 行 / 57837 B）对 _r160/facts_floors.py
  与 FACT_INDEX_CURRENT.md 的引用次数实测各 0。
- 事实层门禁 _r160/facts_floors.py（478 行 / 26147 B）有 D0..D10 十条判据。
- 串门 _r161/gate_runner.py 有 G1/G2/G3 三组，G3 d/e/f/g 做交叉一致性复算。
- 台账 lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv 133310 B，
  sha256 28423e7928d8414216b6a09f8ea56ef60d484dbd121cf9e5d673ffc3bc45db46。

## 主会话拟做的改动（待你审，不要动手改）

在 check_disc.py 里新增 C19「事实层联动」，判据四条：
  (a) _r160/facts_floors.py 存在，且其源码里 CUR_SHA256 字面量 == 现盘 V563/FACT_INDEX.tsv 的 sha256；
  (b) facts_floors.py 里 TOTAL_BYTES 字面量 == 现盘该文件字节数；
  (c) check_disc.py 自身源码里嵌入的 facts_floors.py 的 sha256 常量 == 现盘 facts_floors.py 的 sha256；
  (d) FACT_INDEX_CURRENT.md 里的 sha256 字段 == 现盘该文件 sha256。
反向控制：改动上述任一目标盘上文件（改一个字节）必须使 check_disc exit 1。

## 你要回答的五个问题（只读，不写任何文件）

Q1 (a)(b) 与 gate_runner 的 G3d/G3e 判据是否实质重复？若重复，C19 的独立价值在哪里？给出你的判断依据。

Q2 (c) 引入「check_disc 里嵌入 facts_floors.py 的 sha256」会不会造成一个新的假 FAIL 面 ——
   即每次改 facts_floors.py 都必须同步改 check_disc.py？若要，代价是几处？请按现盘代码实测给出。

Q3 (d) 与 facts_floors 的 D10 判据 (B) 相比，(d) 少覆盖了什么？（提示：D10 有两条独立事实 + 一条冗余，
   你的任务是判断 (d) 究竟等价于哪一条，以及「指针说 133310 但现盘是 133311」这类漂移由谁抓。）

Q4 四条判据里有没有「恒真」的？逐条判定，并指出任何一条在什么现实工况下会永远通过（永远通过子项是
   check_disc 的历史缺陷类型 C7b/C11b/C18 反复抓的东西）。

Q5 有无第五、第六个更该放进主门禁、且成本更低的联动点？给出至多两条，每条一句话说明它抓什么现实失效。

## 交付格式

- 报告写入 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/_r181/r181b_audit.md
- 正文 25 行以内，逐条 Q1..Q5，每条给「成立 / 部分成立 / 不成立」+ 依据（文件:行号）。
- 严禁修改任何生产文件；严禁写 pycache；严禁派生子代理。
