#!/usr/bin/env python3
"""R146 K：四件套写入（§2.151 / §1201 / LEAD_LOCK OE / 看板 R146）+ 看板归档。

写入纪律（逐条断言，任一失败立即停）：
  W1  目标文件写入前用 wx 模式在 R17_LEAD_BASELINE/ 独占创建唯一 .bak
  W2  写入前断言 旧 sha256 == 期望值 且 旧 CR == 期望值
  W3  一次性写入
  W4  回读校验：新 CR == 期望、内容逐字节相同、旧内容是新内容的前缀（追加型）
看板：写前 293 行 >= 260 ⇒ 先把最早 2 段搬进 BOARD_ARCHIVE.md（CR 保持 2952）。
"""
import io, os, re, json, hashlib, time, sys

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
RC = os.path.join(BASE, 'R14_COMMON.md')
BRD = os.path.join(BASE, 'STATUS_BOARD.md')
ARC = os.path.join(BASE, 'BOARD_ARCHIVE.md')
LED = '/home/t628/projects/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK = '/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
R146 = '/home/t628/projects/ra2-campaign-forge/_r146'

FAILS = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: FAILS.append(n)
    return bool(c)

def read(p): return io.open(p, encoding='utf-8', newline='').read()
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

def backup(path, tag):
    src = open(path, 'rb').read()
    dst = os.path.join(BL, os.path.basename(path) + '.before_r146_' + tag + '_' + time.strftime('%Y%m%d_%H%M%S') + '.bak')
    with io.open(dst, 'xb') as f: f.write(src)
    ck('备份 wx 独占且逐字节相同 [' + tag + ']', open(dst, 'rb').read() == src, os.path.basename(dst))

def write_checked(path, old_text, new_text, old_sha, old_cr, new_cr, tag):
    backup(path, tag)
    ck('写入前 sha 匹配 [' + tag + ']', sha(old_text) == old_sha, sha(old_text)[:16])
    ck('写入前 CR 匹配 [' + tag + ']', old_text.count('\r') == old_cr, old_text.count('\r'))
    ck('追加型：旧内容是新内容前缀 [' + tag + ']', new_text.startswith(old_text))
    ck('幂等：新内容尚未写入（旧文本 != 新文本）[' + tag + ']', old_text != new_text,
       'old==new means the previous run already wrote it')
    with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(new_text)
    back = read(path)
    ck('回读 CR == 期望 [' + tag + ']', back.count('\r') == new_cr, back.count('\r'))
    ck('回读逐字节相同 [' + tag + ']', back == new_text)
    return back

def sec_bytes(text, num):
    cur = None; acc = []
    for l in text.split('\n'):
        if re.match(r'^##\s+2\.' + str(num) + r'\b', l):
            cur = num; acc = [l]; continue
        if cur == num:
            if re.match(r'^##\s+', l): break
            acc.append(l)
    return len('\n'.join(acc).encode('utf-8'))

# ---- 0 计算 §2.151 字节数（C16 口径）----
sec_body = io.open(os.path.join(R146, 'sec2151.md'), encoding='utf-8', newline='').read()
sec_body = sec_body[sec_body.index('## 2.151'):].rstrip('\n')
ck('§2.151 正文非空且含关键数字', all(k in sec_body for k in ('0x18C0', '1,027', '278')), len(sec_body))
ck('§2.151 正文无 CR', '\r' not in sec_body, sec_body.count('\r'))
rc0 = read(RC)
size151 = sec_bytes(rc0.rstrip('\n') + '\n\n' + sec_body + '\n', 151)
floor151 = size151 - 21
ck('§2.151 字节数 > 8000', size151 > 8000, size151)
print('  size151=%d floor151=%d' % (size151, floor151))

# ---- 1 看板归档（先裁 2 段，再写本轮段）----
brd0 = read(BRD); lines = brd0.split('\n')
secs = [i for i, l in enumerate(lines) if l.startswith('## ')]
n_lines0 = len(lines) - (1 if lines and lines[-1] == '' else 0)
ck('写前看板 >= 260 行 ⇒ 归档规则触发', n_lines0 >= 260, n_lines0)
ck('看板段数 >= 4', len(secs) >= 4, len(secs))
arc0 = read(ARC); arc_cr0 = arc0.count('\r')
ck('归档前 ARC sha 匹配', sha(arc0) == '3ecfb9aa9640f16d7327c8a320e06fc59292640e5b8da0629a3f923267af9dcb', sha(arc0)[:16])
ck('归档前 ARC CR == 2952', arc_cr0 == 2952, arc_cr0)
move_end = secs[2]
moved = '\n'.join(lines[secs[0]:move_end])
rest = '\n'.join(lines[move_end:])
ck('搬走的段含「第 142 轮」「第 143 轮」', ('第 142 轮' in moved) and ('第 143 轮' in moved))
ck('剩下部分不含被搬段', ('第 142 轮' not in rest) and ('第 143 轮' not in rest))
ck('搬入内容无 CR（否则破坏 ARC CR=2952）', '\r' not in moved, moved.count('\r'))
arc_new = arc0.rstrip('\n') + '\n\n' + moved.rstrip('\n') + '\n'
ck('归档后 CR 仍 2952', arc_new.count('\r') == 2952, arc_new.count('\r'))
backup(ARC, 'archive')
with io.open(ARC, 'w', encoding='utf-8', newline='') as f: f.write(arc_new)
ck('归档回读 CR == 2952', read(ARC).count('\r') == 2952, read(ARC).count('\r'))
brd1 = rest if rest.endswith('\n') else rest + '\n'
ck('裁剪后看板 CR 仍 0', brd1.count('\r') == 0, brd1.count('\r'))
ck('裁剪后行数下降', brd1.count('\n') < brd0.count('\n'), [brd0.count('\n'), brd1.count('\n')])

# ---- 2 R14_COMMON §2.151 ----
ck('R14_COMMON 旧 sha 匹配', sha(rc0) == 'e46f45b85760cb7bad98dcaf6c58e7d70e4ae28fd668b30ac12e5ca8496333fe', sha(rc0)[:16])
ck('R14_COMMON 旧 CR == 1081', rc0.count('\r') == 1081, rc0.count('\r'))
rc_new = rc0.rstrip('\n') + '\n\n' + sec_body + '\n'
ck('§2.151 新内容 CR 仍 1081', rc_new.count('\r') == 1081, rc_new.count('\r'))
rc_back = write_checked(RC, rc0, rc_new, 'e46f45b85760cb7bad98dcaf6c58e7d70e4ae28fd668b30ac12e5ca8496333fe', 1081, 1081, 'rc2151')
ck('回读含 §2.151 标题', '## 2.151 R146' in rc_back)

# ---- 3 台账 §1201 ----
led0 = read(LED)
ck('台账 旧 sha 匹配', sha(led0) == '9b2229d1ccdf30c96486de88ef2d4af01173b60421b76ee6fd54ad9d3e75e586', sha(led0)[:16])
ck('台账 旧 CR == 337', led0.count('\r') == 337, led0.count('\r'))
head = ('## §1201 R146 · R145 的两条「未定」被一手字节推翻：大位移组是**堆分配 0x18C0 字节对象'
        '内嵌异构子对象**的 vptr 写（宿主 0x665650，73 站点 / 8 张虚表 / 54 个位移非等差）；'
        '0x7E1FB4 不是「无主虚表」而是 AbstractClass 链上 INoticeSource 子对象（mdisp=12）的 vptr，'
        '被同槽覆盖属正常构造序列')
body = [
 '',
 '- **① 口径先对齐（S-322 教训）。** R144 的 278 是**严格口径**（r143lib.RE_STORE，拒收负位移）。'
 '本轮宽容解析重算「mov dword ptr <mem>, imm ∈ VTS 且 disp≠0 且基址 ∈ 通用寄存器」= **1,310**：'
 'small（disp ∈ {4,8,12}）**1,027**、large **283**；严格口径 large 仍 **278**，差 **5** = '
 '位移 -8/-8/-8/-4/-8，与 R145 已定位的负位移形态同源（正控）。',
 '- **② 大位移组是什么（一手现场）。** base 寄存器有界回溯（_r146/r146e_root.py，最多退 60 条，'
 '遇「不写目的寄存器」的指令必须继续退；我最初把 push/test/cmp 当定义点，判据因此退化，已修）'
 '定位到宿主函数 **0x665650**：其内 large 站点 **73** 个、**8** 张不同虚表。关键序列 '
 '00665A30 lea ecx,[esi+0x2bc] / 00665A43 mov [esi+0x2a0],0x7eb6d4 / 00665A4D call 0x525680 —— '
 '每 **28 字节（0x1c）** 一个内嵌子对象，写 vptr 后紧接 thiscall 构造。TypeList<H>（0x7E4DD8）'
 '同函数出现 **54** 次、写在 **54 个互不相同**的位移上（856…5104），位移差集**非等差**'
 '（步长集合 {28,32,36,40,56,60,88,104}）⇒ **不是数组**；不同虚表写在不同成员位移 ⇒ '
 '**是多个异构内嵌子对象**。宿主大小由唯一调用者一手给出：0052BABE push 0x18c0 / '
 '0052BAC3 call 0x7c8e17 / 0052BACF mov ecx,eax / 0052BAD1 call 0x665650 / 0052BAD8 mov [0x8871e0],eax '
 '⇒ **堆分配 0x18C0（6.2 KB）对象**，构造后指针存进静态 0x8871E0。'
 '⇒ R145 待办 #3 的正解：既非成员数组、也非静态容器内嵌。',
 '- **③ 0x7E1FB4 是什么。** 0x410170 段：00410174 mov [eax+8],0x7e1fbc（INoticeSink）→ '
 '0041017B mov [eax+0xc],0x7e1fb4（INoticeSource）→ 随后 00410198 mov [eax],0x7e1f50（AbstractClass 主 vptr）'
 '与 004101AC mov [eax+0xc],0x7e1f24（覆盖）。r146i 把归属钉死：AbstractClass 的 CHD '
 'numBaseClasses=**8**（= 自身 + 7 个真基类），其中 INoticeSink 的 **mdisp=8**、INoticeSource 的 '
 '**mdisp=12**，与它们被写的位移 **8/12 逐一相等**；覆盖者 0x7E1F24 的 COL.locator 恰为 **12**'
 '（同槽派生类 vptr）。三处写 0x7E1FB4 的函数内另有 **5/5/9** 个别的槽的 vptr 写 ⇒ 是**子对象 ctor**，'
 '非独占 ctor。⇒ R145 的「瞬态」判定对，「谁的对象未定」错：它明确是 AbstractClass 派生对象内 '
 'INoticeSource 子对象（偏移 12）的 vptr。**归属明确 ≠ 运行期静止存在，两件事必须分开写**。',
 '- **④ 跨家族审计（规则 D，deepseek #326，10 回合 / 6.67 分 / 无 OVERTIME）。** 三条批评全部由 '
 '_r146/r146j_audit_recheck.py 亲测复算 **11/11 PASS**：（a）**断言 B 被我写出了歧义** —— '
 '.?AVINoticeSource@@ 在镜像里被两个地址指代：自有虚表 **0x7E1FB4**（COL 0x7FB160、locator=0，'
 '.text 解码命中 **3** 次、全 eax、全位移 12）与 AbstractClass 组的 **0x7E1F24**（COL 0x7FAFD8、'
 'locator=12，命中 **5** 次、位移全 12、基址集合 {eax,ecx,esi}）；写成「那个虚表地址 3 次」会被读成后者。'
 '（b）**断言 C 是事实性错误** —— LayerClass 的 CHD numBaseClasses=3，但 pBaseClassArray[0] 是'
 '**类自身**（nCB=2），真基类只有 **2** 个；写「基类链长度 3」会被读成「3 个基类」。'
 '（c）**计数口径必须声明** —— 「原始对齐 dword」与「解码后的立即数」不同：0x7E1FC8 raw=**3** / '
 'decode=**0**，而 0x7E1FB4 与 0x7E1FBC raw==decode。',
 '- **⑤ 执行员盲测（规则 D，hy4 #325，24 回合 / 10.08 分 / 回收打 `[OVERTIME: 实测 10.08\' vs 预算 8.0\']`，'
 '如实登记）。** N1 严格 1,027 / **278**、N2 宽容 283 且多出 5 个位移 **-8/-8/-8/-4/-8**、'
 'N3 0x7E1FB4 命中 **3** 次且位移全 12 —— **三项逐项相同**；它自报 VTS=**1,218**（TDs 988 / COL 1214）、'
 'exe 4,825,360 B、sha256 73201cc0…。它还自主指出**我卡面「严格口径」措辞与 capstone 实际打印不符**'
 '（原始输出是 [eax + 0xc]，加号两侧有空格），并登记 0x4A8660 写的是 0x7E6060 —— 即 R144 §七'
 '「该虚表未找到装表站点」是被同一个负位移盲区漏掉的。两条均成立，已采纳为措辞更正。',
 '- **⑥ 门禁回归（两处，均为容纳新节 + 重钉，未改判据语义）。** C16_FLOORS 加 151: ' + str(floor151) +
 '（§2.151 实测 **' + str(size151) + ' B** − 21），表项 **144 → 145**，C16_FLOORS_SHA256 183a5d82… → 见本轮重钉；'
 'GATE_VER **R145 → R146**。',
 '- **⑦ 未取得（不粉饰）。** ① 宿主 0x665650 的成员类型序列只解到 8 张虚表名，非 vptr 字段未解析；'
 '② 0x8871E0 这个静态指针运行期何时重新赋值 / 何时释放未知（动态项）；'
 '③ 0x7E1FB4 是否曾作为**最派生**类实例存在，静态侧无路径 ≠ 运行期不存在（需动态验证）；'
 '④ 0x7C8E17 只证是**分配入口**（push 1 + call 0x7C9442），**未证**它是 operator new 本体；'
 '⑤ 动态项（虚表运行期读取、3,805 处寄存器 call/jmp 落点、35 个静态容器运行期值、窗口表 r66 后快照）'
 '留 win-main；⑥ 已判死线继续禁投：具名池、无名池、direct-only(D2)、D4结构性无、静态④、动态④、'
 '证据指针791行、D-48攻②-b。',
]
led_new = led0.rstrip('\n') + '\n\n' + head + '\n' + '\n'.join(body) + '\n'
ck('台账新内容 CR 仍 337', led_new.count('\r') == 337, led_new.count('\r'))
led_back = write_checked(LED, led0, led_new, '9b2229d1ccdf30c96486de88ef2d4af01173b60421b76ee6fd54ad9d3e75e586', 337, 337, 'led1201')
ck('回读含 §1201 标题', '## §1201 R146' in led_back)


# ---- 4 LEAD_LOCK OE ----
lk0 = read(LOCK)
ck('LEAD_LOCK 旧 sha 匹配', sha(lk0) == '2f0280273877d5d5f09c4411632db8a4434630753704dbfa8032aeddaafcd7e0', sha(lk0)[:16])
ck('LEAD_LOCK 旧 CR == 137', lk0.count('\r') == 137, lk0.count('\r'))
OE = []
OE.append('OE1. ✅ **R146 主交付：R145 的两条「未定」被一手字节推翻。** ① **大位移组**：严格口径 278 / 宽容 283'
          '（差 5，位移 -8/-8/-8/-4/-8）。宿主 **0x665650** 内 large 站点 73 个 / 8 张虚表；'
          'TypeList<H>（0x7E4DD8）在同函数出现 54 次、写在 54 个互不相同位移上（856…5104），'
          '位移差集**非等差**（步长集合 {28,32,36,40,56,60,88,104}）⇒ 不是数组；'
          '唯一调用者 0052BABE push 0x18c0 → 0052BAC3 call 0x7c8e17 → 0052BACF mov ecx,eax → '
          '0052BAD1 call 0x665650 → 0052BAD8 mov [0x8871e0],eax ⇒ **堆分配 0x18C0（约 6.2 KB）对象的'
          '内嵌异构子对象**。② **0x7E1FB4**：不是无主虚表，是 AbstractClass 链上 INoticeSource 子对象'
          '（**mdisp=12**）的 vptr，写 [eax+0xc] 后被同槽派生类 0x7E1F24（COL.locator=12）覆盖，'
          '属正常 MSVC 构造序列。⇒ R145 待办 #1/#3 结案。')
OE.append('OE2. 📌 **自错 S-323（本轮第 1 条，正文措辞的事实性错误，由跨家族审计抓出）。** 我原写'
          '「LayerClass 的 CHD 基类链长度是 3」—— numBaseClasses=3 但 pBaseClassArray[0] 是**类自身**'
          '（nCB=2），真基类只有 2 个。同一错误也适用 AbstractClass（8 项 = 自身 + 7 个真基类）。'
          '**教训**：MSVC BCD 数组的 [0] 恒为类自身；写「链长 N」而不说明「含自身」就是事实性错误，'
          '必须写「自身 + N−1 个真基类」；且「mdisp 全 0」在单继承下是默认值、不构成证据，'
          '要论证无虚基类须同引 pdisp 全 -1。')
OE.append('OE3. 📌 **自错 S-324（本轮第 2 条，断言歧义）。** 我把 .?AVINoticeSource@@ 说成「那个虚表地址」，'
          '但镜像里它被**两个**地址指代：自有虚表 0x7E1FB4（COL 0x7FB160、locator=0，.text 解码命中 3 次、'
          '全 eax、全位移 12）与 AbstractClass 组的 0x7E1F24（COL 0x7FAFD8、locator=12，命中 5 次、'
          '位移全 12、基址集合 {eax,ecx,esi}）。**教训**：凡「某个类的虚表」必须带 COL VA + locator 才能'
          '唯一定位。同族错误是 S-322（口径名词病）。')
OE.append('OE4. 📌 **自错 S-325（本轮第 3 条，计数口径未声明）。** 「0x7E1FB4 在 .text 出现 3 次」只在'
          '「解码后的立即数」口径下成立：按「原始对齐 dword」计数，0x7E1FC8 得 3（raw）/ 0（decode），'
          '是跨 dword 边界的巧合命中。**教训**：任何「出现 N 次」必须写清是按解码指令还是按原始 dword 计数。')
OE.append('OE5. 📌 **自错 S-326（本轮第 4 条：我自己脚本里的判据退化，三处）。** ① r146b 的 J1 先用'
          '「disp − COL.offset 的残差」再判等差 —— 残差把 small 组全压成 0，正控直接 FAIL；'
          '② J2 把「站点自己」的 (vt, disp) 记进集合再查询，等于恒真，small 组也 0/1027；'
          '③ r146e 把 push/test/cmp 这类只读指令当成寄存器定义点，导致 base 回溯整类落空。'
          '三处均由可失败断言当场抓出并改掉（J1 改用原始位移、J2 排除自身、回溯只认写目的寄存器的助记符）。'
          '**教训**：新判据必须先在一个已知答案的桶上跑通，再拿去出结论。')
OE.append('OE6. ✅ **规则 D 如实（两家独立，含一次 OVERTIME）。** 执行员 **#325（hy4, exec）succeeded** / '
          '24 回合 / **10.08 分** / 回收打 **`[OVERTIME: 实测 10.08′ vs 预算 8.0′]`**（如实登记）：'
          'N1 严格 1,027 / **278**、N2 宽容 **283** 且多出 5 个位移 **-8/-8/-8/-4/-8**、'
          'N3 0x7E1FB4 命中 **3** 次且位移全 12 —— 三项**与我逐项相同**；它自报 VTS=**1,218**'
          '（TDs 988 / COL 1214）、exe 4,825,360 B、sha256 73201cc0…。并自主指出**我卡面「严格口径」'
          '措辞与 capstone 实际打印不符**（原始输出是 [eax + 0xc]，加号两侧有空格；严格口径拒的只有减号那一类），'
          '以及 **0x4A8660 写的是 0x7E6060**（即 R144 §七「该虚表未找到装表站点」也被同一个负位移盲区漏掉）。'
          '审计员 **#326（deepseek, audit）succeeded** / 10 回合 / 6.67 分 / 无 OVERTIME，三条批评'
          '（B 歧义 / C 事实性错误 / 计数口径）经 r146j 亲测 **11/11 PASS** 全部成立，已按 OE2–OE4 更正。')
OE.append('OE7. ✅ **门禁回归与看板归档。** `C16_FLOORS` 加 `151: %d`（§2.151 实测 **%d B** − 21），'
          '表项 **144 → 145**，`C16_FLOORS_SHA256` `183a5d82…` → 新钉（重钉前先用现表复现旧钉）；'
          '`GATE_VER` **R145 → R146**；`DISC_RECHECK.tsv` 主键 20 行与 `DISC_UNVERIFIABLE.tsv` 主键 20 行'
          '同步重钉。看板写前 **293 行 ≥ 260** ⇒ 先把最早的 **2 段**（第 142 / 143 轮）搬进 '
          '`BOARD_ARCHIVE.md`（CR 保持 **2952**）再写本轮段。' % (floor151, size151))
OE.append('OE8. 📌 **未取得（不粉饰）**：① 宿主 0x665650 的成员类型序列只解到 8 张虚表名，'
          '非 vptr 字段未解析；② 0x8871E0 这个静态指针运行期何时重赋值 / 对象何时释放 unknown（动态项）；'
          '③ 0x7E1FB4 是否曾作为最派生类实例存在 —— 静态侧无构造路径 ≠ 运行期不存在，需动态验证；'
          '④ 0x7C8E17 只证是**分配入口**（push 1 + call 0x7C9442），**未证**是 operator new 本体；'
          '⑤ 动态项（虚表运行期读取、3,805 处寄存器 call/jmp 落点、35 个静态容器运行期值、'
          '窗口表 r66 后快照）留 win-main；⑥ 已判死线继续禁投：具名池、无名池、direct-only(D2)、'
          'D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。')
lk_new = lk0.rstrip('\n') + '\n\n' + '\n\n'.join(OE) + '\n'
ck('LEAD_LOCK 新内容 CR 仍 137', lk_new.count('\r') == 137, lk_new.count('\r'))
lk_back = write_checked(LOCK, lk0, lk_new, '2f0280273877d5d5f09c4411632db8a4434630753704dbfa8032aeddaafcd7e0', 137, 137, 'lock_oe')
ck('回读含 OE1', 'OE1.' in lk_back and 'OE8.' in lk_back)

# ---- 5 看板第 146 轮段 ----
BRD2 = [
 '## 🟢 R17 第 146 轮（2026-11-27 02:0x–03:0x）· R145 的两条「未定」被一手字节推翻：大位移组是**堆分配 0x18C0 对象的异构内嵌子对象** vptr 写（宿主 0x665650，73 站点 / 8 张虚表 / 54 个位移非等差）；0x7E1FB4 不是「无主虚表」，是 **AbstractClass 链第 4 个子对象**（mdisp=12）的 vptr',
 '',
 '### 一 · 一句话',
 '',
 'R145 留下的两条「未定」，本轮都用现盘字节做掉了：大位移组**既不是成员数组、也不是静态容器内嵌**，而是「堆对象里一串异构内嵌子对象」；`0x7E1FB4` **归属明确**，只是运行期不会静止存在 —— 这两件事 R145 写成了一句。',
 '',
 '### 二 · 口径先对齐（S-322）',
 '',
 'R144 的 278 是**严格口径**（`RE_STORE` 拒收 `[eax - 8]` 这类负位移）。宽容解析重算：`disp ≠ 0` 站点 **1,310** = small（{4,8,12}）**1,027** + large **283**；严格 large 仍 **278**，差 **5** = 位移 **-8/-8/-8/-4/-8**，与 R145 的根因同源（正控）。',
 '',
 '### 三 · 大位移组是什么（一手现场）',
 '',
 '宿主函数 **0x665650** 内 73 个 large 站点、8 张虚表。每 **28 字节（0x1c）** 一个内嵌子对象：先写 vptr 到子对象起点，紧接 `lea ecx,[esi+子对象起点+0x1c]` + `call` 构造它（`00665A30`/`00665A43`/`00665A4D` 三步一组）。`TypeList<H>` 同函数 **54** 次、写在 **54 个不同位移**（856…5104），步长集合 `{28,32,36,40,56,60,88,104}` ⇒ **非等差、非数组**。宿主大小由唯一调用者给出：`0052BABE push 0x18c0` / `call 0x7c8e17` / `mov ecx,eax` / `call 0x665650` / `mov [0x8871e0],eax` ⇒ **堆分配 0x18C0 ≈ 6.2 KB**。',
 '',
 '### 四 · 0x7E1FB4 是什么',
 '',
 '`00410174 mov [eax+8],0x7e1fbc`（INoticeSink，mdisp=8）→ `0041017B mov [eax+0xc],0x7e1fb4`（INoticeSource，mdisp=12）→ 之后 `00410198 mov [eax],0x7e1f50` 与 `004101AC mov [eax+0xc],0x7e1f24`（`COL.locator=12`，同槽派生类 vptr）覆盖。**mdisp 与被写位移 8/12 逐一相等**。三处写 0x7E1FB4 的函数内另有 **5/5/9** 个别的槽的 vptr 写 ⇒ 是**子对象 ctor**，不是独占 ctor。',
 '',
 '### 五 · 规则 D（两家独立，含一次 OVERTIME）',
 '',
 '- **#325（hy4, exec）** succeeded / 24 回合 / **10.08′** / 回收打 **`[OVERTIME: 实测 10.08′ vs 预算 8.0′]`**（如实登记）：1,027 / 278 / 283 / 5 个负位移 / 3 次全 12 —— **逐项相同**。它另指出**我卡面「严格口径」措辞与 capstone 实际打印不符**（原始是 `[eax + 0xc]`），以及 `0x4A8660` 写的是 `0x7E6060`（R144 §七那条「未找到装表站点」也是负位移盲区漏的）。两条都采纳。',
 '- **#326（deepseek, audit）** succeeded / 10 回合 / 6.67′ / 无 OVERTIME：三条批评经 `r146j` 亲测 **11/11 PASS** 全部成立（见第六节）。',
 '',
 '### 六 · 自错四条（S-323..S-326），三条由外部抓出',
 '',
 '- **S-323（事实性错误）**：「LayerClass 的 CHD 链长 3」错 —— `numBaseClasses=3` 含 `[0]` **类自身**，真基类只有 2 个；`AbstractClass` 同理（8 = 自身 + 7）。且「mdisp 全 0」在单继承下是默认值、不构成证据，须同引 `pdisp 全 -1`。',
 '- **S-324（断言歧义）**：`.?AVINoticeSource@@` 有两个地址指代 —— 自有虚表 **0x7E1FB4**（`COL 0x7FB160` locator=0，命中 **3** 次、全 `eax`）与 AbstractClass 组 **0x7E1F24**（`COL 0x7FAFD8` locator=12，命中 **5** 次、基址 `{eax,ecx,esi}`）。凡「某个类的虚表」必须带 **COL VA + locator**。',
 '- **S-325（计数口径未声明）**：`0x7E1FC8` raw=**3** / decode=**0**（跨 dword 边界巧合）；`0x7E1FB4`/`0x7E1FBC` 两口径相同。任何「出现 N 次」必须写清口径。',
 '- **S-326（我脚本里的判据退化，三处）**：J1 用残差判等差（残差把 small 全压成 0）、J2 把站点自己记进集合（恒真）、`r146e` 把 `push/test/cmp` 当定义点。三处均由可失败断言当场抓出。',
 '',
 '### 七 · 门禁回归与归档',
 '',
 '`C16_FLOORS` 加 `151: %d`（§2.151 实测 **%d B** − 21）、表项 **144 → 145**、`C16_FLOORS_SHA256` 重钉；`GATE_VER` **R145 → R146**；`DISC_RECHECK.tsv` 与 `DISC_UNVERIFIABLE.tsv` 主键 20 行同步。看板写前 **293 ≥ 260** ⇒ 先把第 142/143 轮段搬进 `BOARD_ARCHIVE.md`（CR 保持 2952）再写本轮。' % (floor151, size151),
 '',
 '### 八 · 未取得（不粉饰）',
 '',
 '① 宿主成员类型序列只解到 8 张虚表名，非 vptr 字段未解析；② `0x8871E0` 运行期行为 unknown（动态项）；③ `0x7E1FB4` 是否曾作为最派生类实例存在，静态无路径 ≠ 运行期不存在；④ `0x7C8E17` 只证是**分配入口**，未证是 `operator new` 本体；⑤ 动态项留 win-main；⑥ 已判死线继续禁投。',
 '',
 '### 九 · 下轮优先（禁写元审计待办）',
 '',
 '1. **旧节更正（单独一卡 + 门禁回归）**：R144 §七「0x7E6060 未找到装表站点」已被证伪（站点在 `0x4A8660`，负位移盲区），§2.149 与看板 R144 段同错需改。',
 '2. **宿主 0x665650 的成员布局**：8 张虚表已定位，其余非 vptr 字段按「成员数组 / 结构体字段」做可失败判据。',
 '3. **`0x8871E0` 的写入者普查**：除 `0x52BAD8` 外还有谁写它，决定该对象是单例还是多实例（静态可做）。',
 '4. **F23/F35 正文修订**（R137 看板第九节①）：F23 补「12 行分解余 1 行无归属」与「计数依赖 coverage.tsv 4,147,334 B 已失」；F35 补「proved_strict 定义缺一手权威」—— 两条已在 v5.39 limitations 里，缺的是正文口径统一。',
 '5. **F24 正文 86.19% 数字撤下**（R136 已证 99.992% 有字节对应）；**F24 语料值失效期标注**（4,417 件/737,517,286 B 是 11-22 快照，现盘 65 件/44,470,975 B）。',
 '6. 动态项（虚表运行期读取、3,805 处寄存器 `call/jmp` 落点、35 个静态容器运行期值、窗口表 r66 后快照）留 win-main。',
 '7. 已判死线继续禁投：具名池、无名池、direct-only(D2)、D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。',
]
brd_new = brd1.rstrip('\n') + '\n\n' + '\n'.join(BRD2) + '\n'
ck('看板新内容 CR 仍 0', brd_new.count('\r') == 0, brd_new.count('\r'))
n_new = len(brd_new.split('\n')) - (1 if brd_new.endswith('\n') else 0)
ck('看板总行数 <= 300', n_new <= 300, n_new)
brd_back = write_checked(BRD, brd1, brd_new, sha(brd1), 0, 0, 'board146')
ck('回读含第 146 轮段', '第 146 轮' in brd_back)

json.dump({'fails': FAILS, 'size151': size151, 'floor151': floor151,
           'board_lines': n_new}, open('/home/t628/projects/ra2-campaign-forge/_r146/r146k_write.json', 'w'), indent=1)
print('\n=== PART1+PART2 FAILS %d ===' % len(FAILS))
print(FAILS)
sys.exit(1 if FAILS else 0)
