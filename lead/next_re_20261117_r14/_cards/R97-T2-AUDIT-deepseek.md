# R97-T2 跨家族审计：三个数字 851 / 864 / 763 谁在说什么（deepseek 审计）

## 0 硬约束
- 只读。唯一可写目录：/home/t628/projects/ra2-campaign-forge/_r97/_audit/
- 绝对不要执行 _r93/_audit/analyze.py（它会覆写 _r93/_audit/counts.json）。要跑就复制到 _audit/ 改 OUT。
- 产物上限 20 MB，不得写 lead/ 下任何文件。卡面与产物不得出现反引号。
- 你的结论会被主会话逐条用脚本复算；不要为了让结论好看而省略反例。

## 1 命题与三个候选值
gamemd.exe 中 call DWORD PTR [reg+0x48] 共 929 站。命题：调用点 ecx 的值 == reg 所指向
对象的第 0 个 dword。候选命中数：
  - 851：R92 主会话（_r93/REPORT.md 记 V1）
  - 864：R93 主会话（_r93/expr_r93.json，hit=864 = hit_concrete 169 + hit_anchored 695）
  - 851：R93 跨家族审计员（_r93/_audit/counts.json 的 variantA_no_call_break.HIT_total）
  - 763：同一审计脚本在它自己 payload 里声明为 primary 的那一格（nocallbrk + clobber）

## 2 审计目标（只审这四件事，别扩大）
### T2-A 现盘可复现性
1. 用 stat 报 _r93/_audit/counts.json 与 _r93/_audit/analyze.py 两个文件的 mtime、size。
2. 读现盘 counts.json，列出它的顶层键。判断这个 schema 是 analyze.py 当前源码写出的 schema
   还是别的版本的 schema（依据是源码里 json.dump 的 payload 字典字面量）。
3. 结论：现盘 counts.json 与现盘 analyze.py 是不是同一次运行的一对？给出判据。

### T2-B 「851」这个数的口径归属
4. 把 analyze.py 复制到你的目录，只改 OUT。分别跑 2x2 四格（块界 callbrk/nocallbrk x
   call clobber/clobber off），报四格 HIT 数。
5. 结论：851 只出现在哪一格？analyze.py 自己在 payload 里把哪一格叫 primary？
   两者是否一致？若不一致，这是不是一个「引用者会引错数」的结构性缺陷？

### T2-C 主会话 864 的可质疑处（你来挑，别顺着我）
6. _r93/expr_r93.py 的 judge 把「this 是不透明量但两侧锚完全相同」判成 HIT_ANCH 并计入命中。
   独立评估：这个判据在什么情况下会给出假阳？给至少一个具体机制（要能落到某类指令形态），
   并说明它是否在本镜像里真实发生（能落到地址就落地址，落不到就说不确定）。
7. _r93/expr_r93.py 的 HIT_ABS 只有 1 站（0x6933b1）。审计员的 judge 把它判 MISS，因为
   analyze.py 的 parse_addr 对无方括号的绝对内存操作数返回常量而非读内存。请你独立判断：
   0x6933b1 这条 call 的 ecx 与 edx 是否真的相等（要读字节、要写清依据）。这是判断题，
   不要因为我上面这么写就跟着写。

### T2-D 数字之外
8. 两个实现的站点集合是不是同一批 929 个地址？如果不是，差几个、差哪些。
9. 你认为「≥ 851 站满足 vt == [this]」这个三方交集结论是否成立？成立就给下界推导，
   不成立就指出哪一方的数不能进交集。

## 3 产物
_r97/_audit/AUDIT97.md（结论 + 每条的实测出处）、_r97/_audit/*.log、_r97/_audit/*.py。
每条结论后面必须写「依据：<命令或脚本输出行>」。
