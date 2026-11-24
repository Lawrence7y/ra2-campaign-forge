#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w6.py —— 补 R14_COMMON §2.112.8（自错）/ §2.112.9（收口）

E-w6：§2.112 初稿只有 2.112.1..2.112.7，缺了 §2.111 体例里必有的「自错」与「收口」两节；
根因是我照着「业务结论」写段，没有先对齐上一节的小节骨架（2.111 有 11 个小节，含 2.111.6 自错、
2.111.10 写盘后复核、2.111.11 可复用判据）。

收口数字以九个 JSON 的 checks 数组直读为准：7+8+14+8+16+14+15+10+7 = 99，FAIL 0。
自错条数按条清点 = 14（E-x1..E-x4 / E-y1..E-y3 / E-z1..E-z2 / E-w1..E-w5）。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')
P = 'lead/next_re_20261117_r14/R14_COMMON.md'
SEG = '_r108/seg_rc_2112.md'

ADD = '''
### 2.112.8 自错 14 处（全部由断言当场抓住，不隐去、不洗白）

| 编号 | 内容 | 抓法 |
|---|---|---|
| E-x1 | `r108c` 的 `owner_in` 用严格 `>` 判 S，「S 本身即窗口内最大 E 成员」时返回 None，13 张 R107-OWNER 被误记「拿不到 owner」 | A1 断言直接 FAIL |
| E-x2 | 「排他性」判据在随机窗口上发火率 **100%**（HB 密度 1/235 B）⇒ 无鉴别力 | R1 反控报 400/400，按无鉴别力降级为自检 |
| E-x3 | `ret` 前缀 `0x67` 未处理（全段 2 处 0x7dcc34 / 0x7dcc58，实为数据区 `67 cb 7d 00`）⇒ `set` 排序 TypeError 崩在负控 | Q2a 负控直接抛异常 |
| E-x4 | IMMPTR v2 把**内存操作数 displacement** 当立即数（`0x71f2be add byte ptr [eax+0x71ef01],dl`），0x71f328 被错改判成 0x71ef01 | 剥方括号后恢复 0x71e940，A2 断言 FAIL 抓出 |
| E-y1 | `r108e` 帧常量探测深度不足（前 6 条无 `sub esp` 就记 None）⇒ 0x58bda4 两侧同为 None 被误判「相同」 | K2b 断言 FAIL |
| E-y2 | 口径「从 O 线性解码，首条 ret 早于 H ⇒ 到不了 H」把正确 owner 判负（0x417fe0 第 25 条即 `0x418030 ret`，`0x418031` 仍是同一函数） | Q4a 断言 FAIL 47/387 |
| E-y3 | 口径「jmp/jcc BFS 不可达 ⇒ 不是本函数」不成立：CFG 不跟跳转表边（`jmp *0x418d58(,%eax,4)`） | 抽查 0x418345 证伪 |
| E-z1 | `r108g` C1 断言「6,719 个 call 目标全部是指令起点」实测 6,692，**27 个不是** | C1 FAIL → `r108h` 定量 |
| E-z2 | 遇 `and esp,-8` 即返回，把 0x4ffdd0 的帧记成对齐修饰而漏掉其 `sub esp,0x70` | A3 断言 FAIL |
| E-w1 | 收口断言总数首稿写 **105**（真值 99）、`a` 抄成 6（真值 7），凭记忆累加未直读 JSON | 写盘后直读九个 JSON 的 checks 长度抓出 |
| E-w2 | 修数脚本用「自错 8 处…」当替换锚点，该串先在 R107 的 EI6 出现 ⇒ **改错了 R107 的段** | 复核 LEAD_LOCK 两处标题发现 |
| E-w3 | 「自错几处」按**行**数而不是按**条**数（台账体例把 E-y2/E-y3 并成一行）⇒ 先写 8、后写 9 | 逐码清点后改 14 |
| E-w4 | 备份文件名只含 basename + 时间戳，同一文件两处改动落在同一秒 ⇒ `O_EXCL` 第二次 EEXIST 崩掉半个作业 | `fix_w2.py` 抛 FileExistsError |
| E-w5 | `fix_w34.py` 的 JOBS 表给 lock/台账两支只挂了一条插入文本，而同脚本断言要求三条齐备 ⇒ FAIL 4 | 断言抓住（断言对、表错） |

### 2.112.9 收口

九个带断言机制脚本合计 **99 项断言 FAIL 0**（a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7；
数字由各脚本 JSON 的 checks 数组直读累加，不凭记忆）。`check_disc.py` **exit 0**；五项 CR 全绿
（1081 / 137 / 337 / 0 / 2952，字节 896,329 / 680,774 / 4,901,826 / 35,327 / 863,251）；
看板开局 300 行 = 上限 ⇒ 先归档第 101/102/103 三段到 BOARD_ARCHIVE（逐字搬，missing=0，归档 CR 保持 2952），
写入后看板 254 行 ≤ 300；收口前 `ps` 核对无 `r108*` 孤儿进程。
'''

fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

t = io.open(P, encoding='utf-8', newline='').read()
ck('R14_COMMON 尚无 2.112.8', '### 2.112.8' not in t)
ck('R14_COMMON 尚无 2.112.9', '### 2.112.9' not in t)
old_b = io.open(P, 'rb').read()
ck('CR 前置 1081', old_b.count(b'\r\n') == 1081, old_b.count(b'\r\n'))
ck('追加体全 LF', '\r' not in ADD)
new = t + ADD
ck('新文件含 2.112.8 与 2.112.9', '### 2.112.8' in new and '### 2.112.9' in new)
bl = os.path.join(BASE, 'R14_COMMON.md.before_R108_EW6_%s.bak' % TS)
fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
try:
    os.write(fd, old_b)
finally:
    os.close(fd)
ck('备份独占同哈希', hashlib.sha256(io.open(bl, 'rb').read()).digest()
   == hashlib.sha256(old_b).digest(), os.path.basename(bl))
with io.open(P, 'wb') as f:
    f.write(new.encode('utf-8'))
back = io.open(P, 'rb').read()
ck('回读逐字节一致', back == new.encode('utf-8'))
ck('CR 保持 1081', back.count(b'\r\n') == 1081, back.count(b'\r\n'))
# 段文件同步（保持可复跑一致）
s = io.open(SEG, encoding='utf-8', newline='').read()
ck('段文件尚无 2.112.8', '### 2.112.8' not in s)
with io.open(SEG, 'wb') as f:
    f.write((s + ADD).encode('utf-8'))
ck('段文件回读含 2.112.9', '### 2.112.9' in io.open(SEG, encoding='utf-8', newline='').read())
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
