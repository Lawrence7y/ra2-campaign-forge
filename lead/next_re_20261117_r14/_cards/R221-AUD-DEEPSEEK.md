# R221-AUD 只读跨家族复核（deepseek 审计员）

## 角色
只读审计员。绝对不要修改任何项目文件，只做独立复算并给 PASS/FAIL 与差异。
工作目录 /home/t628/projects/ra2-campaign-forge 。可用 python3 + capstone。自己的脚本写到 /tmp/ 下。

## 环境要点（必须照做）
- 只读模块：sys.path.insert(0,"/home/t628/projects/ra2-campaign-forge"); import _r185.pe185 as P
  P.RAW 全文件字节；P.r2o(va) 文件偏移；P.B[".text"] 段信息；P.SECS 段表。
- capstone：md.skipdata=True，逐字节 resync：每步对 RAW[pos:pos+16] 调 md.disasm_lite 取第一条，pos += 长度，解不出 pos += 1。
  不要固定 64KB 切块重启，不要开 detail=True 整段 disasm。
- 每条都要实跑数字，禁止照抄本卡数字后声称一致。

## 待复核（每项给实测值 + PASS/FAIL）

1. 段表：.text lo=0x401000 rawptr=0x1000 rawsize=0x3e0000；.rdata lo=0x7e1000；.data lo=0x812000 rawsize=0x6c000。
   因此 0x8758e4 属 .data（0x812000..0x87e000），不在 .rdata。给 PASS/FAIL。

2. 零间隙衔接四条（每条 True/False）：
   0x8759b4+5696==0x876ff4；0x876ff4+3360==0x877d14；0x879b30+5696==0x87b170；0x87b170+3360==0x87be90。

3. 逐字节同一性：0x8759b4 与 0x879b30 各 5696 B 相同；0x876ff4 与 0x87b170 各 3360 B 相同；
   0x8758c4 与 0x8758d4 各 16 B 相同（内容为 8 个 16 位字：前 4 个是 0xFFFF，后 4 个是 2,4,6,8）。
   并给出 3360 B 块（state+两抖动表）的 sha256 前 16 位。

4. 索引表 0x8758c4 起 8 个 16 位字按有符号 = (-1,-1,-1,-1,2,4,6,8)。给 PASS/FAIL。

5. 律 D（差分表 0x879b30，1424 个 int32，index = 16*m+n，m=0..88，n=0..15）：
   s = IMA[m]，d = (s>>3) + (s if (n&7)&4 else 0) + ((s>>1) if (n&7)&2 else 0) + ((s>>2) if (n&7)&1 else 0)；
   期望 = -d（n>=8 时）否则 +d。请自己按 IMA ADPCM 规范生成 89 项 step table（首项 7，末项 32767）或用 0x8758e4 处实表。
   给命中数/1424。主会话实测 1424/1424。

6. 律 S（状态表 0x87b170，1424 个 uint16，同样 16 个一记录）：
   期望 = 32 * clamp(m + ADJ[n&7], 0, 88)，ADJ = (-1,-1,-1,-1,2,4,6,8)。给命中数/1424。主会话实测 1424/1424。
   同一律在副本 0x876ff4 上给命中数（主会话实测 1424/1424）。
   给出该表 1424 字的 min / max / 是否全部为 32 的倍数（主会话实测 min=0 / max=2816 / True）。

7. 反控（主会话实测值，请独立复算）：
   K1 律 S 基址右移 2（0x87b172 起读）命中 564/1424；
   K2 按每记录 8 字（stride 8 words）模型命中 12；
   K3 clamp 上界改 87 命中 1376；
   K4 律 D 符号判据 n>=8 改 n>=7 后的命中数（本卡不给期望，请报实测）；
   K5 律 D 的 n 改成 n&15 后的命中数（请报实测）。

8. 步长表 0x8758e4 起 89 个 16 位字与标准 IMA ADPCM step table 逐项相同（89/89）。给命中数与末日项（末项 32767）。

9. 引用计数（.text 逐字节 resync 全扫），给条数与位点前 6 个（主会话实测值）：
   0x8758c4 = 3（mov ax,word ptr [ecx+0x8758c4]：0x7c639b/0x7c649f/0x7c65be）；
   0x8758d4 = 0；0x8758e4 = 3；0x8759b4 = 0；0x876ff4 = 8（mov dx,word ptr [edx+0x876ff4]）；
   0x879b30 = 24（add eax,dword ptr [edx*2+0x879b30]）；0x87b170 = 24（mov dx,word ptr [edx+0x87b170]）；
   0x87bc90 = 21（or dl,byte ptr [ebx+0x87bc90]）；0x87bd90 = 24（or dl,byte ptr [ebx+0x87bd90]）。
   请特别复核 0x87bc90 与 0x87bd90 的 21 与 24 是否属实（两表相邻 256 B，容易串位）。

10. 两张抖动表：A = 0x87bc90 起 256 B 视为 16x16，A[r][c]==2*c 对全部 256 项成立；
    B = 0x87bd90 起 256 B，B[r][c]==2*r 对全部 256 项成立；B 等于 A 的转置；A 不等于 B。逐项给 PASS/FAIL。

11. 跳转表：0x7c7758 起 8 个 dword = (0x7c75c1,0x7c7694,0x7c76ac,0x7c76c4,0x7c76e0,0x7c76f8,0x7c771c,0x7c7740)；
    0x7c7778 起 4 个 dword = (0x7c73e2,0x7c73f8,0x7c7408,0x7c7418)。给 PASS/FAIL。

## 输出
一条命令或两三条命令产出全部结果，不要逐条命令试探。每条：编号 | 实测值 | 是否与卡片一致 | 不一致时给你的值与差异原因。
最后单列 "你发现的口径问题"（例如表被误归到错段、记录跨度算错、相邻表串位）。
