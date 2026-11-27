# 卡 r164_e1_exec · a2_sites.json 全件规则独立复算（只读）

角色：exec（执行员）。模型：work/cn:hy4flash-free。预算 8 分钟。只读，禁止修改任何文件。
**不要读 _r164/ 目录里的任何文件**（保持实现独立）。

## 背景（一句话）
lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json（17,624,355 B）是一个
两段 JSON：calls 段（目标地址 -> 调用站点列表）与 bounds 段（地址列表）。
主会话声称已把它**整件复原成一段确定规则**，请你独立复算这条声称。

## 请独立测量（全部自己写代码，不要 import 仓库里任何脚本）
仓库根 = /home/t628/projects/ra2-campaign-forge；二进制 = ra2bench/gamemd.exe。
可用 python3 + pefile + capstone（capstone 用 Cs(CS_ARCH_X86, CS_MODE_32)，并设 md.skipdata = True）。

1. 文件尺寸与分段
   - 文件总字节数；sha256。
   - 常量 MARK = 由右花括号、逗号、空格、双引号 bounds 双引号、冒号、空格、左方括号 组成的 14 字节串。
     量它在文件中出现几次、第一次的起始偏移。
   - 以该偏移 +1 为界把文件切成两段，量两段各自字节数，并断言两段字节数之和等于文件总字节数。

2. bounds 段
   - 解析出条数、是否无重复、最大值。
   - 自行扫 .text（blob 取 VirtualAddress 起、长度取 Misc_VirtualSize / VirtualSize），
     skipdata=True，一次扫完（**必须整段一次扫，禁止按 64KB 分块**，分块会在块边界重切出伪起点）。
   - 判断：bounds 序列与扫描得到的起点序列**是否逐位相等（条数、顺序、值全同）**。

3. calls 段
   - 解析出键数、键值对总数。
   - 判断：键集合是否等于「扫描中助记符为 call 且操作数以 0x 开头的目标地址」集合。
   - 判断三件事是否同时成立：
     a) 文件里键的**顺序**等于这些目标在扫描中**首次出现**的顺序；
     b) 每个键内站点列表的顺序等于扫描顺序（不是排序）；
     c) 每个键内站点集合与扫描结果逐键相等。

4. 序列化
   - 用 python json.dumps 以默认分隔符（ensure_ascii=False）序列化 {"calls": <解析出的 calls>}，
     量其字节长度，并判断去掉末尾一个右花括号后是否与文件前 913,238 字节逐字节相同。
   - 量 bounds 数组段字节数，判断它是否恰等于 12 × bounds 条数。

5. 一条具体站点
   - 站点地址 0x74836A：读该处 5 字节，验证是否为 E8 且 rel32 目标是否为 0x7C8B3D（32 位环绕）。
   - 判断该站点是否在 bounds 序列里；若不在，找出它落在哪一条 skip 块的内部（起点/长度/位移）。
   - 打开 lead/next_re_20261117_r14/C01_census/EVIDENCE/callgraph.json，判断里面是否**存在**
     src=0x748360 且 site=0x74836A 的条目。

## 交付格式（硬要求）
- **一次命令输出全部证据**：把上面全部测量写成**一条** bash 命令（python3 内联即可）跑完，把输出原文贴回。
- 结论分 5 小节，每节一句话 + 数字。没量到的写「未量」，不要推断。
- 最后一行 SELFCHECK：写出你做了什么反控（例如把 bounds 首元素 +4 后等式是否必失败；
  或把 capstone 的 blob 换成 SizeOfRawData 长度后起点数变成多少），并给实测值。
