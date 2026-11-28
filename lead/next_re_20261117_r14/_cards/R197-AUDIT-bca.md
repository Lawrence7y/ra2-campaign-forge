# 卡 R197 审计（deepseek）：只读复核 BCA 相邻递增判据的三条主张

## 角色与边界
只读审计。**不得写任何文件，不得修改任何文件**，不得运行 gamemd.exe。只允许读到 stdout。
全部静态取证。一条命令跑完全部复核（单个 python 脚本，直接打印结果）。预算 8 分钟，回合数 <= 12。
PE 映射用 /home/t628/projects/ra2-campaign-forge/_r185/pe185.py：
   import sys; sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185'); import pe185 as P
   P.RAW（整个文件字节）/ P.B[段名]（含 lo 虚拟起点 / rawptr 文件偏移 / rawsize）/ P.dw(va) / P.where(va) / P.cstr(va,n)
镜像基址 0x400000。不需要 capstone，本卡只读数据结构。

## 数据结构的定义（这是被测对象，照此实现即可）
COL 为 24 字节，判据：dword +0 在 {0,1,2}、+8 == 0、+12 指向 .data（TypeDescriptor）、+16 指向 .rdata（ClassHierarchyDescriptor）。
  扫 .rdata 与 .data 两段，按 dword 步进，5 个 dword 同时满足即认作 COL。
  TypeDescriptor 的类名在 td+8，读取时**上限必须给 400**（给 80 会截断长模板类名）。
CHD 为 16 字节：+8 是元素个数 n（正整数），+12 是 BCA 数组指针。BCA 数组是 n 个 4 字节元素，每元素是一个 BCD 地址。
BCD 为 24 字节：+4 是 ncb，+8 是有符号 mdisp。

## 三条待复核主张（逐条独立复算，给数）
A1 【基数】不同 CHD 地址 = 954；BCD 槽位总数 = 2615；不同 BCD 地址 = 1002；COL 个数 = 1214。
   若你的数不同，逐个列出差异地址。
A2 【相邻差值三分】对每张 CHD 的 BCA 数组按顺序算相邻差 diff = bcd[i+1] - bcd[i]（有符号）：
   全部相邻对 = 1661，其中 diff < 0 有 1480、diff == 0 有 0、diff > 0 有 181。
A3 【核心判据】统计每个 BCD 地址的全局引用计数 ref（它出现在多少张 CHD 的 BCA 数组里）。
   称 ref == 1 的为「私有 BCD」，ref > 1 的为「共享 BCD」。
   主张 A3a：全部 1661 个相邻对中，两端都是私有 BCD 的对只有 21 个，且这 21 个的 diff **全部**等于 -24。
   主张 A3b：全部 688 个 diff != -24 的对里，两端都是私有 BCD 的对个数为 **0**。
   主张 A3c：私有 BCD 共 698 个、共享 BCD 共 304 个；落在共享 BCD 上的槽位共 1917 个。

## 你还要独立回答的两问
Q4 【A3 的鉴别力】如果 A3b 成立只是因为「私有对本来就几乎没有」，那这条判据就没有解释力。
   请给出：全部 1661 个相邻对里，两端都是私有的只有 21 个，占 21/1661。再给「至少一端是共享」的对数。
   然后判断：A3b 是否能被「688 个异常全部分布在有共享端点的对里」解释，还是仅仅因为样本稀疏。给数说明。
Q5 【反向检验】构造一个**必须掉下来**的检验：把每张 CHD 的 BCA 数组用固定种子随机打乱 200 次，
   统计打乱后 diff == -24 的对数均值，以及 diff > 0 的对数均值。若打乱后 -24 的均值仍接近 973，
   说明 -24 是判据自带的性质而非数据性质（则 A3a 无意义）；若大幅下降，说明 -24 是真结构。

## 输出格式
直接在 stdout 打印，每问一段，形如：
  A1: CHD=... slots=... uniq=... COL=... | 与主张一致/不一致(差异...)
  A2: total=... dec=... eq=... inc=...
  A3a: private_pairs=... of which diff==-24: ...
  A3b: neq24=... pp_in_neq24=...
  A3c: priv=... shared=... shared_slots=...
  Q4: ...
  Q5: ...
最后一行写 ASSERTS=<断言数> FAILS=<失败数>。
只报你实测的数。**若你的数与主张不一致，直接报你的数并标注不一致，不要为了对齐而调整判据。** 严禁预估。
