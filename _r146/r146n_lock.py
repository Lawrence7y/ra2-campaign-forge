#!/usr/bin/env python3
import io, os, re, json, hashlib, time, sys
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
LOCK = '/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
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
    ck('幂等：旧文本 != 新文本 [' + tag + ']', old_text != new_text)
    ck('写入前 sha 匹配 [' + tag + ']', sha(old_text) == old_sha, sha(old_text)[:16])
    ck('写入前 CR 匹配 [' + tag + ']', old_text.count('\r') == old_cr, old_text.count('\r'))
    ck('追加型：旧内容是新内容前缀 [' + tag + ']', new_text.startswith(old_text))
    backup(path, tag)
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
rc_now = read(os.path.join(BASE, 'R14_COMMON.md'))
size151 = sec_bytes(rc_now, 151); floor151 = size151 - 21
ck('§2.151 已落盘且字节数 > 8000', size151 > 8000, size151)
print('  size151=%d floor151=%d' % (size151, floor151))

# ---- 4 LEAD_LOCK OE ----
lk0 = read(LOCK)
ck('LEAD_LOCK 旧 CR == 137（只钉 CR，不钉死 sha）', lk0.count('\r') == 137, lk0.count('\r'))
ck('LEAD_LOCK 尚无 OE1（幂等前提）', 'OE1.' not in lk0)
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
lk_back = write_checked(LOCK, lk0, lk_new, sha(lk0), 137, 137, 'lock_oe')
ck('回读含 OE1', 'OE1.' in lk_back and 'OE8.' in lk_back)


json.dump({'fails': FAILS, 'size151': size151, 'floor151': floor151}, open('/home/t628/projects/ra2-campaign-forge/_r146/r146n_lock.json','w'), indent=1)
print('=== FAILS %d ===' % len(FAILS)); print(FAILS)
sys.exit(1 if FAILS else 0)
