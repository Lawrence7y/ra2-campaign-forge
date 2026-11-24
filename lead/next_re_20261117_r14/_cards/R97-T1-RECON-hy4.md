# R97-T1 独立复算：864 / 851 / 763 三数之争的逐站对账（hy4 执行员）

## 0 硬约束（先读，违反即作废）
- 只读 live 的 gamemd.exe 与 _r93 下已有文件。禁止写 lead/ 下任何文件，禁止改 _r93 下任何文件。
- 唯一可写目录：/home/t628/projects/ra2-campaign-forge/_r97/_exec/
- 严禁直接执行 _r93/_audit/analyze.py。该脚本把自己的产物写回 _r93/_audit/counts.json，
  会覆盖上一轮原件（主会话已犯过这个错一次）。要复用它的函数，请复制一份到 _exec/ 并把
  OUT 常量改到 _exec/ 下再跑。
- 产物上限 20 MB。卡面与产物不得出现反引号。

## 1 背景（你必须自己核实，不要照抄我的结论）
gamemd.exe 里 call DWORD PTR [reg+0x48] 站点共 929 个。命题是：调用点的 this（ecx 的值）
与 vt（reg 指向对象的第一个 dword）相等。R92 主会话实现得 851；R93 主会话改进实现得 864；
R93 跨家族审计员（_r93/_audit/analyze.py）得 851（它的 counts.json 写 variantA_no_call_break
HIT_total 851 = HIT_CONCRETE 7 + HIT_ANCHED 844）。

我已实测两件事，请你独立验证或推翻：
  A1. 现在盘上的 _r93/_audit/analyze.py 直接跑，矩阵四格是
      callbrk+clobber 852 / callbrk+noclobber 852 / nocallbrk+clobber 763 / nocallbrk+noclobber 851。
      也就是说 851 只在 nocallbrk 且 noclobber 这一格出现，而该脚本自己的 payload 把
      primary 定义为 nocallbrk+clobber（=763）。请你自己跑出来核对这四格数字。
  A2. 旧 counts.json（31,563 B 之前是 30,654 B）的 schema 与现在 analyze.py 写出的 schema 不同
      （旧的是 variantA_no_call_break / variantB_with_call_break 键，新脚本写 matrix_2x2 等键），
      且旧文件 mtime 早于 analyze.py 的 mtime。请用 stat 核对 mtime 先后，并说明这意味着什么。

## 2 你要独立做的事
### 任务 1：复现四格
把 analyze.py 复制到 _exec/aud_copy.py，只改 OUT 指向 _exec/，跑出四格 HIT 数与类别分解，
与上面的 A1 数字逐一对账（相等就写相等，不等就写你的数）。

### 任务 2：逐站对账 864 与两套 auditor 口径
主会话的 864 站在 _r93/expr_r93.json 的 rows（字段 verdict，HIT/HIT_ABS/HIT_ANCH 都算命中）。
请你自己写脚本（不要 import expr_r93.py，自己读 _r93/expr_r93.json 的 rows 即可）：
  B1. 导出 callbrk+noclobber 口径下 auditor 判命中、而主会话 864 里没有的站点（应为 0 个），
      以及主会话有、auditor 没有的站点，打印全部地址。
  B2. 对 noclobber 口径，主会话独有站点应为 13 个；对 clobber 口径应为 101 个。
      若你的数字不同，直接报你的数字并给出你的实现口径说明。

### 任务 3：两个缺陷假设的独立检验
假设 D1：analyze.py 的 parse_addr 对无方括号的绝对内存操作数（例如 mov edx,DWORD PTR ds:0x87f7e8）
返回 ('c', disp)，于是 step() 把它当成立即数而不是读内存，vt 丢掉了一层 load。
假设 D2：judge() 在两边的值都是同一个不透明原子（同锚）时返回 UNDET；主会话判 HIT_ANCH。
请分别只开一个开关、两个都开，各跑一遍，报 2x2x2 共 8 格的 HIT 数（三轴：callbrk 块界 /
call clobber / 两个缺陷修不修）。要求：两个都修后，四格（两种块界 x 两种 clobber）是否都等于 864，
且站点集合与主会话 864 的集合完全相同（差集两向都为 0）。若不等，报残差地址。

### 任务 4：正反控（必须做，否则整卡作废）
  C1. 正控：D1 的字节级证据。打印 0x6933b1 附近 12 条指令，指出哪一条是绝对内存读，
      并打印 analyze.py 的 parse_addr 对该操作数串的返回值（应是 ('c', 8910824)）。
  C2. 反控：同一个不透明原子必须被判相等、两个不同的不透明原子必须判不等。
      自己构造最小用例（不需要真镜像）证明修后的判据不会把任意两个 opaque 都算成相等。
  C3. 反控：只修 D1 或只修 D2 都不能到 864。报这两个数。

## 3 产物
- _r97/_exec/recon_hy4.py（你的脚本，带断言，跑完打印 PASS/FAIL 计数）
- _r97/_exec/recon_hy4.log（完整输出）
- _r97/_exec/VERDICT.md（结论：四格数字、13 与 101 的逐站表、8 格表、正反控结果、
  你认为主会话哪条说法错、错在哪）
- 每个数字都要有你自己的实测出处（脚本里哪一行打印的），不许只抄我的数。
