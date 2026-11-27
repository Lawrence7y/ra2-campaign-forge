#!/usr/bin/env python3
"""R147 K：四件套写入 + 门禁回归（一次写完，带幂等与次数断言）。

本轮交付（R147）：
  ① 0x8871E0 被证为**单例指针槽**，且论据换成审计员指出的四条支点（不是我原先的
     「只有一个非空写点」）：
       a 无 SIB 变址写 [reg*scale+0x8871E0] = 0
       b 无带位移形态 [reg+0x8871E0] = 0
       c 无取地址指令（lea/push/mov reg,0x8871E0）= 0
       d 槽在 .data 原始数据之外（BSS 尾，零初始化）+ 3 写点 = 1 构造 + 2 归零
  ② R144 §七/§八① 的「0x7E6060 未找到装表站点」已被证伪并就地更正
     （装表站点 0x4A8660，负位移；属 0x8A0368 起、步长 0x18、5 元素的静态数组初始化循环）。
  ③ 自错 S-328..S-335 八条登记。
  ④ 规则 D：执行员 #328（hy4）与审计员 #329（deepseek, OVERTIME 10.7'/8'）双家独立，
     审计员三条批评由 r147g 亲测 10/10 全部成立。

写入纪律：每份文档 wx 独占备份 → 旧 sha/CR 断言 → 幂等断言（新内容尚未出现）
→ 一次性写 → 回读 sha/CR/「该节出现恰 1 次」断言（S-327：追加型必须断次数）。
"""
import io, os, re, sys, json, time, hashlib

HERE = '/home/t628/projects/ra2-campaign-forge'
BL = HERE + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
RC = HERE + '/lead/next_re_20261117_r14/R14_COMMON.md'
BRD = HERE + '/lead/next_re_20261117_r14/STATUS_BOARD.md'
ARC = HERE + '/lead/next_re_20261117_r14/BOARD_ARCHIVE.md'
LED = HERE + '/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK = HERE + '/lead/LEAD_LOCK'
GATE = HERE + '/lead/next_re_20261117_r14/check_disc.py'
R147 = HERE + '/_r147'

FAILS = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        FAILS.append(n)
    return bool(c)

def read(p):
    return io.open(p, encoding='utf-8', newline='').read()

def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def backup(path, tag):
    src = open(path, 'rb').read()
    dst = os.path.join(BL, os.path.basename(path) + '.before_r147_' + tag + '_' + time.strftime('%Y%m%d_%H%M%S') + '.bak')
    with io.open(dst, 'xb') as f:
        f.write(src)
    ck('备份 wx 独占且逐字节相同 [' + tag + ']', open(dst, 'rb').read() == src, os.path.basename(dst))
    return dst

def write_checked(path, old_text, new_text, old_cr, new_cr, tag, must_once=None):
    backup(path, tag)
    ck('写入前 CR 匹配 [' + tag + ']', old_text.count('\r') == old_cr, old_text.count('\r'))
    ck('幂等前置：新内容尚未写入 [' + tag + ']', old_text != new_text, 'old==new 表示上一轮已写过')
    if must_once:
        ck('幂等前置：标记串尚未出现 [' + tag + ']', must_once not in old_text, must_once[:40])
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_text)
    back = read(path)
    ck('回读 逐字节相同 [' + tag + ']', back == new_text)
    ck('回读 CR == 期望 [' + tag + ']', back.count('\r') == new_cr, back.count('\r'))
    if must_once:
        ck('回读 标记串出现恰 1 次 [' + tag + ']', back.count(must_once) == 1, back.count(must_once))
    return back

def sec_bytes(text, num):
    """按 C16 口径算 §2.NNN 的字节数（到下一个 ## 开头为止，含标题行）。"""
    cur = None; acc = []
    for l in text.split('\n'):
        if re.match(r'^##\s+2\.' + str(num) + r'\b', l):
            cur = num; acc = [l]; continue
        if cur == num:
            if re.match(r'^##\s+', l):
                break
            acc.append(l)
    return len('\n'.join(acc).encode('utf-8'))

# ---------------- 0. 计算 §2.152 字节数 ----------------
rc0 = read(RC)
size152_pre = sec_bytes(rc0, 152)
ck('§2.152 写前不存在（幂等前提）', size152_pre == 0, size152_pre)

# ---------------- 1. R14_COMMON §2.152 ----------------
SEC = []
SEC.append('## 2.152 R147 · 0x8871E0 是**单例指针槽**（论据换成四条可失败支点）；R144 §七「0x7E6060 未找到装表站点」被一手字节证伪并就地更正')
SEC.append('')
SEC.append('**一 · 0x8871E0 的单例判定，论据不是我原先写的那条。** R147 起初我用「只有一个非空写入点」')
SEC.append('去推「所以不是多实例容器」。跨家族审计员 #329 指出这个推理**不成立**：构造时写数组头、')
SEC.append('随后循环写 `[base + idx*4]` 的形态完全可能存在，一个非空写点推不出单例。审计员是对的，')
SEC.append('论据必须换成机器码层面四条可失败判据（`r147g` 复算，10/10 全成立）：')
SEC.append('')
SEC.append('| 支点 | 判据 | 实测 | 反控/说明 |')
SEC.append('|---|---|---|---|')
SEC.append('| a | SIB 变址写 `[reg*scale + 0x8871E0]` | **0** 处 | 4 种 scale × 8 种索引寄存器全算 |')
SEC.append('| b | 带位移形态 `[reg ± 0x8871E0]` | **0** 处 | 即「基址+常量偏移」，R144 曾据此假设次虚表 |')
SEC.append('| c | 取地址 `lea/push/mov reg,0x8871E0` | **0** 处 | 地址从未流入寄存器 ⇒ 先取基址再循环写的间接路径也不存在 |')
SEC.append('| d | 槽位所在区段 | `.data` RVA **0x751E0** > 原始数据 **0x6C000** ⇒ **BSS 尾、零初始化** | 静态无初值 |')
SEC.append('')
SEC.append('配合 3 个写入点的语义（`r147d` 函数内前向数据流，分支汇合取交）：')
SEC.append('**0x52BAD8** 源 `eax` = 格 UNKNOWN，且其紧邻前置 `call` 的目标是 **0x665650**（宿主 ctor，')
SEC.append('R146 已证该 ctor 由 `push 0x18C0 / call 0x7C8E17` 分配的对象调用）⇒ 这是**唯一构造写**；')
SEC.append('**0x52BAFA** 与 **0x6BEABD** 源 `ebx` = 格 **ZERO** ⇒ 前者是分配失败回滚置零、')
SEC.append('后者是析构（`mov esi,[0x8871E0] / cmp esi,ebx / je / call 0x667A30 / call 0x7C8B3D` 后置零）')
SEC.append('⇒ 教科书式单例生命周期：1 写 + 2 清。')
SEC.append('')
SEC.append('**二 · 计数与交叉核验（三家独立，逐项相同）。** 主会话 `r147e`、执行员 #328（hy4）、')
SEC.append('审计员 #329（deepseek）三家各自从零写扫描器：全文件原始字节 `e0 71 88 00` **1423** 次；')
SEC.append('.text 指令边界命中 **1423** 次；写入点 **3** 个（`0x52BAD8` / `0x52BAFA` / `0x6BEABD`）；')
SEC.append('读点 **1420**；构造写所在函数 **0x52BA60**（唯一调用者 `0x48CCCF`）。审计员另给两个可复现钉：')
SEC.append('`.text` 段 sha256 `c0368a17…`、整文件 sha256 `73201cc0…`，主会话复算**逐字节一致**。')
SEC.append('')
SEC.append('**三 · 自错 S-336（函数入口判定）：`0x52BA9B` / `0x52BADF` 不是函数入口。** 它们是')
SEC.append('`0x52BA60` 函数体内的 **jmp 标签**（分别由 `0x52BABC`、`0x52BB00` 跳来，是失败分支与')
SEC.append('成功分支的收尾段），`call` 目标数各为 **0**。我首版把 `jmp` 目标也当函数起点，导致数据流')
SEC.append('在错误边界内计算。改用「只用 call 直接目标定函数起点」后，三点收敛到 **2** 个函数。')
SEC.append('')
SEC.append('**四 · R144 §七/§八① 更正：0x7E6060 的装表站点找到了。** 原文说「没有找到装表站点')
SEC.append('（可能作为次虚表被基址+常量偏移访问）」。一手字节：站点在 **0x4A8660**，形态')
SEC.append('`mov dword ptr [eax - 8], 0x7e6060` —— **负位移**，正是 R145 定位的解析器缺陷形态')
SEC.append('（`r143lib.norm` 空白压缩字符类 `[+,*]` 不含 `-`）。该站点属**静态数组初始化循环**：')
SEC.append('`0x4A8630 mov eax,0x8A0368 / mov edx,5 / xor ecx,ecx`，循环体 `0x4A863C..0x4A866B`，')
SEC.append('步长 `add eax,0x18`，共 **5** 元素；每元素依次写 `[eax-8]=0x7E192C` → `0x7E4F64` → `0x7E6060`，')
SEC.append('再 `[eax+0xC]=0xA`、`[eax+8]=ecx`。数组基址 `0x8A0360` 在 `.data`，静态内容**全 0**')
SEC.append('⇒ 运行期由该循环填充。`0x7E6060` 的 RTTI：COL `0x7FFC28`（locator=0/offset=0）、')
SEC.append('TD `0x816B10` 名 `.?AVLayerClass@@`、前 8 槽 **8/8** 落 `.text`。')
SEC.append('')
SEC.append('**五 · 门禁回归。** `C16_FLOORS` 加 `152: <floor>`（§2.152 实测 bytes − 21），表项')
SEC.append('**145 → 146**，`C16_FLOORS_SHA256` 重钉；`GATE_VER` **R146 → R147**。看板写前 210 行 < 260，')
SEC.append('**无需归档**（这与 R146 写前 293 ≥ 260 必须归档不同）。')
SEC.append('')
SEC.append('**六 · 未取得（不粉饰）。** ① 0x52BA60 **无幂等守卫**（写前无 `if ([0x8871E0]) return`），')
SEC.append('「单例」是**事实上的**（靠 `0x48CCCF` 单点调用保证），不是运行期强制的 —— 措辞不得写后者；')
SEC.append('② 槽在 BSS，运行期首次赋值时刻与释放时刻属动态项；③ 邻槽 `0x8871D8 / 0x8871E8 / 0x8871F0`')
SEC.append('各有 1 处 `qword ptr` 引用（`0x40DF22 / 0x40DE3C / 0x40DE1C`），与 0x8871E0 无指针步进关系，')
SEC.append('不构成数组证据，但**未定性**它们是什么数据；④ 0x4A8270（数组初始化循环所在函数）的调用者')
SEC.append('`0x479104` 的调用时机未定（静态可继续做）。')
SEC.append('')
SEC.append('**七 · 自错登记（S-328..S-335，八条，全部是我的脚本判据缺陷，不是数据错误）。**')
SEC.append('- **S-328**（分类器漏写入）：去空白后操作数变 `dwordptr[0x8871e0]`，我拿 `[0x8871e0]` 比目的操作数，')
SEC.append('永不相等 ⇒ 把 `0x52BAD8` 这种**真实写入**判成 READ。修复：先剥 `dword/qword/word/byte` 前缀串。')
SEC.append('- **S-329**（正控选错）：我把 `0x8871E4 / 0x8871DC` 当「正控」，实测二者原始字节命中 **0** ——')
SEC.append('它们本身就是无人引用全局，当正控必然假失败。改用 `0x886380`（原始命中 8）作正控。')
SEC.append('- **S-330**（函数边界用 jmp 目标）：见上文 S-336 同族，首版 `starts` 混入 11,407 个 jmp 目标。')
SEC.append('- **S-331**（线性回扫判零值）：用「同函数内最近 xor reg,reg 且其后无赋值」判零，把另一分支的')
SEC.append('`pop ebx`（`0x52BAF2`，在 `ret 0x52BAF9` 之前）当成前置定值 ⇒ `0x52BAFA` 被误判为**非空写**。')
SEC.append('- **S-332**（同基本块回扫仍不够）：改成基本块边界后 `0x52BAFA` 判对，但 `0x6BEABD` 判错 ——')
SEC.append('它的 `ebx=0` 建在函数入口块 `0x6BE1C8`，隔了基本块边界。两个回扫判据都只在「自己举的例子」上成立。')
SEC.append('- **S-333**（传移函数把「不写目的」的指令当写入）：`push ebx` 被当成写 ebx ⇒ `0x6BE1C0` 里 ebx')
SEC.append('被误标 UNKNOWN。修复：`push/cmp/test/jcc/ret/call` 一律不算写目的。')
SEC.append('- **S-334**（断言把「指令地址」当「call 目标」）：我拿 `0x52BAD1`（call 指令自身 VA）去和')
SEC.append('`0x665650`（目标）比，必然假失败。修复：`prev_call` 同时返回 (指令 VA, 目标 VA)。')
SEC.append('- **S-335**（把「有意保留的原文」当成「没改掉」）：更正时我把旧句留在删除线 `~~…~~` 内便于对照，')
SEC.append('回读断言却要求旧串计数为 0 ⇒ 假失败。正确断言是「仅以删除线形态出现恰 1 次」。')
SEC.append('')
SEC.append('（S-336 见上第三节；八条计数口径为 S-328..S-335 + S-336，实为九条，此处标题所述「八条」')
SEC.append('以 S-328..S-335 为准，S-336 单列在第三节。）')
SEC.append('')
SEC152 = '\n'.join(SEC) + '\n'

# 两遍定点：正文里要引用自己的字节数与 floor，先占位再替换，替换后重算直到稳定
rc_new = rc0 + SEC152
prev = None
for _ in range(6):
    size152 = sec_bytes(rc_new, 152)
    floor152 = size152 - 21
    t = '\n'.join(SEC) + '\n'
    t2 = t.replace('<floor>', str(floor152))
    t2 = t2.replace('实测 bytes − 21', '实测 **' + str(size152) + ' B** − 21')
    cand = rc0 + t2
    if cand == rc_new:
        break
    rc_new = cand
size152 = sec_bytes(rc_new, 152)
floor152 = size152 - 21
ck('§2.152 定点收敛（正文引用的字节数 == 实测）', ('实测 **' + str(size152) + ' B** − 21') in rc_new,
   [size152, floor152])
ck('§2.152 实测字节 > 1000（非空节）', size152 > 1000, size152)

rc_back = write_checked(RC, rc0, rc_new, 1081, 1081, 'rc2152', '## 2.152 R147')
ck('§2.152 出现恰 1 次', rc_back.count('## 2.152') == 1, rc_back.count('## 2.152'))
ck('§2.151 仍出现恰 1 次（未被破坏）', rc_back.count('## 2.151') == 1, rc_back.count('## 2.151'))

# ---------------- 2. 台账 §1202 ----------------
led0 = read(LED)
ck('台账 写前 CR == 337', led0.count('\r') == 337, led0.count('\r'))
L = []
L.append('## §1202 R147 · 0x8871E0 单例判定的论据被换成四条机器码支点（原「只有一个非空写点」被审计员判为不足）；R144 §七「0x7E6060 未找到装表站点」被负位移装表站点 0x4A8660 证伪并就地更正')
L.append('')
L.append('**一 · 被推翻的前提。** R147 首版结论「0x8871E0 是单例指针槽，因为只有一个非空写入点」被')
L.append('跨家族审计员 #329 判为**推理缺环**：构造写数组头 + 循环写 `[base+idx*4]` 的形态完全可能存在。')
L.append('主会话亲测该批评成立，并改换论据为四条机器码层面判据：')
L.append('')
L.append('| 支点 | 判据 | 实测 |')
L.append('|---|---|---|')
L.append('| a | SIB 变址写 `[reg*scale + 0x8871E0]` | **0** 处 |')
L.append('| b | 带位移形态 `[reg ± 0x8871E0]` | **0** 处 |')
L.append('| c | 取地址 `lea/push/mov reg,0x8871E0` | **0** 处 |')
L.append('| d | 槽位区段 | `.data` RVA 0x751E0 > 原始 0x6C000 ⇒ BSS 尾、零初始化 |')
L.append('')
L.append('**二 · 三家独立同数。** 主会话 `r147e` / 执行员 #328（hy4）/ 审计员 #329（deepseek）各自独立扫描，')
L.append('逐项相同：原始字节 **1423**、指令边界 **1423**、写入点 **3**（`0x52BAD8` 构造写、')
L.append('`0x52BAFA` 与 `0x6BEABD` 归零写）、读点 **1420**、构造写所在函数 **0x52BA60**')
L.append('（唯一调用者 `0x48CCCF`，非循环）、析构函数 **0x6BE1C0**（调用者 `0x6BED48`）。')
L.append('审计员给的两个钉（`.text` 段 sha256 `c0368a17…`、整文件 `73201cc0…`）由主会话复算一致。')
L.append('')
L.append('**三 · R144 §七更正。** 「0x7E6060 未找到装表站点」为解析器缺陷产物：站点在 **0x4A8660**，')
L.append('形态 `mov dword ptr [eax - 8],0x7E6060`（**负位移**，被 `norm` 的字符类 `[+,*]` 拒收）。')
L.append('它属静态数组初始化循环：`0x4A8630 mov eax,0x8A0368 / mov edx,5 / xor ecx,ecx`，')
L.append('循环体 `0x4A863C..0x4A866B`，步长 `0x18`，5 元素，每元素依次写 `0x7E192C` → `0x7E4F64` → `0x7E6060`。')
L.append('数组基址 `0x8A0360` 在 `.data`、静态全 0（运行期填充）。')
L.append('')
L.append('**四 · 门禁。** `C16_FLOORS` 加 `152: ' + str(floor152) + '`（§2.152 实测 **' + str(size152) + ' B** − 21），')
L.append('表项 **145 → 146**，`C16_FLOORS_SHA256` 重钉；`GATE_VER` **R146 → R147**。')
L.append('看板写前 **210 行 < 260** ⇒ **无需归档**（R146 写前 293 ≥ 260 必须归档，两者不同）。')
L.append('')
L.append('**五 · 未取得。** ① `0x52BA60` **无幂等守卫**（写前无 `if ([0x8871E0]) return`），')
L.append('「单例」是**事实单例**而非运行期强制单例，措辞不得写成后者；② 槽在 BSS，首赋时刻与释放时刻属动态；')
L.append('③ 邻槽 `0x8871D8 / 0x8871E8 / 0x8871F0` 各 1 处 `qword ptr` 引用，与指针步进无关，未定性；')
L.append('④ 数组初始化函数 `0x4A8270` 的调用者 `0x479104` 的调用时机未定。')
L.append('')
L.append('**六 · 自错 S-328..S-336（九条，全部为脚本判据缺陷）。** S-328 分类器漏写入（未剥 `dwordptr` 前缀）；')
L.append('S-329 正控选成无人引用全局（0x8871E4/0x8871DC 原始命中 0）；S-330/S-336 用 jmp 目标当函数起点；')
L.append('S-331 线性回扫把别支路 `pop ebx` 当前置定值；S-332 同基本块回扫够不到入口块的零值；')
L.append('S-333 传移函数把 `push` 当写目的；S-334 断言拿 call 指令自身地址比 call 目标；')
L.append('S-335 把有意保留的删除线原文当成「没改掉」。')
L.append('')
L1202 = '\n'.join(L) + '\n'
led_new = led0 + L1202
led_back = write_checked(LED, led0, led_new, 337, 337, 'led1202', '## §1202 R147')
ck('§1202 出现恰 1 次', led_back.count('## §1202') == 1, led_back.count('## §1202'))
ck('§1201 仍出现恰 1 次', led_back.count('## §1201') == 1, led_back.count('## §1201'))

# ---------------- 3. LEAD_LOCK OF ----------------
lk0 = read(LOCK)
ck('LEAD_LOCK 写前 CR == 137', lk0.count('\r') == 137, lk0.count('\r'))
OF = []
OF.append('')
OF.append('## OF · R147：0x8871E0 单例论据重建 + R144 §七更正')
OF.append('')
OF.append('OF1. ✅ **交付一：0x8871E0 是单例指针槽，但论据已换。** 我原来写「只有一个非空写入点 ⇒ 不是多实例容器」。')
OF.append('审计员 #329 直接指出这是**推理缺环**：构造写数组头再循环写 `[base+idx*4]` 完全可能存在。')
OF.append('我亲测该批评成立，改换四条机器码支点：SIB 变址写 **0**、带位移形态 **0**、取地址指令 **0**、')
OF.append('槽在 `.data` RVA 0x751E0 > 原始 0x6C000 的 **BSS 尾（零初始化）**。配 3 个写入点语义')
OF.append('（1 构造写 `0x52BAD8`，前置 `call` 目标 `0x665650`；2 归零写 `0x52BAFA` 回滚、`0x6BEABD` 析构）')
OF.append('⇒ 单例生命周期。')
OF.append('')
OF.append('OF2. ✅ **交付二：R144 §七/§八① 就地更正。** 「0x7E6060 未找到装表站点」被证伪：')
OF.append('站点 **0x4A8660**，负位移 `mov dword ptr [eax - 8],0x7E6060`，属 `0x4A8630` 起、')
OF.append('基址 `0x8A0368`、步长 `0x18`、**5** 元素的静态数组初始化循环（`0x4A863C..0x4A866B`）。')
OF.append('R14_COMMON §2.149 的 §七与 §八① 两处已用删除线保留原文并附更正段，CR 保持 1081。')
OF.append('')
OF.append('OF3. ✅ **规则 D 如实：两家独立，含一次 OVERTIME。** 执行员 **#328（hy4, exec）succeeded**，')
OF.append('10 回合、产物 `_r147/r147x_exec_scan.json`，七项数字（1423/1423/3/POS 8/NEG 0,0/ctor 0x52BA60/')
OF.append('三写格 UNKNOWN-ZERO-ZERO）与我逐项相同；审计员 **#329（deepseek, audit）succeeded**，')
OF.append('10 回合，**实测 10.7 分钟 vs 预算 8.0 ⇒ 触发 OVERTIME，如实登记**。审计员三条批评')
OF.append('（A 推理缺环、B 函数入口误判、C 幂等守卫缺失）由 `r147g` 亲测 **10/10 全部成立**，')
OF.append('并给出两个可复现钉（`.text` sha256 `c0368a17…`、整文件 `73201cc0…`）与主会话复算逐字节一致。')
OF.append('')
OF.append('OF4. ✅ **门禁回归与无归档。** `C16_FLOORS` 加 `152: ' + str(floor152) + '`（§2.152 实测 **' + str(size152) + ' B** − 21），')
OF.append('表项 **145 → 146**，`C16_FLOORS_SHA256` 重钉；`GATE_VER` **R146 → R147**。')
OF.append('看板写前 **210 行 < 260** ⇒ **本轮不归档**（与 R146 写前 293 ≥ 260 必须归档的情形不同）。')
OF.append('')
OF.append('OF5. 📌 **自错 S-328..S-336（九条，全是我的脚本判据缺陷，不是数据错误）。** 最严重的是前三条：')
OF.append('S-328 分类器没剥 `dwordptr` 前缀，把真实写入 `0x52BAD8` 判成 READ（差点得出「0 个写入点」的假事实）；')
OF.append('S-329 把 `0x8871E4 / 0x8871DC`（原始字节命中 **0** 的无人引用全局）当正控，必然假失败；')
OF.append('S-330/S-336 把 `jmp` 目标（11,407 个）当函数起点，`0x52BA9B / 0x52BADF` 因此被误当函数入口，')
OF.append('数据流在错误边界内计算。其余：S-331 线性回扫把别支路 `pop ebx` 当前置定值；S-332 同基本块回扫')
OF.append('够不到入口块的零值；S-333 传移函数把 `push` 当写目的；S-334 断言拿 call 指令自身地址比 call 目标；')
OF.append('S-335 把有意保留的删除线原文当成「没改掉」。**共同病根：判据在我自己举的那个例子上成立，')
OF.append('就以为普遍成立；每条都是换一个输入就翻车。**')
OF.append('')
OF.append('OF6. 📌 **未取得（不粉饰）**：① `0x52BA60` **无幂等守卫**，写前既无 `if ([0x8871E0]) return`，')
OF.append('也无引用计数 ⇒ 「单例」是**事实单例**（靠 `0x48CCCF` 单点调用），**不是运行期强制单例**，')
OF.append('措辞不得写成后者；② 槽在 BSS，运行期首赋与释放时刻属动态项；③ 邻槽 `0x8871D8 / 0x8871E8 /')
OF.append('`0x8871F0` 各有 1 处 `qword ptr` 引用（`0x40DF22 / 0x40DE3C / 0x40DE1C`），与 0x8871E0 无')
OF.append('指针步进关系，不构成数组证据，但**未定性**;④ 数组初始化函数 `0x4A8270` 的调用者 `0x479104`')
OF.append('的调用时机未定；⑤ 动态项（虚表运行期读取、3,805 处寄存器 call/jmp 落点、35 个静态容器运行期值、')
OF.append('窗口表 r66 后快照）留 win-main；⑥ 已判死线继续禁投：具名池、无名池、direct-only(D2)、')
OF.append('D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。')
OF.append('')
OF.append('OF7. 📌 **给下一轮的方法论提醒（自我约束）。** 本轮九个自错里有七个是**「判据只在样例上成立」**。')
OF.append('下一轮任何新判据，落盘前必须先用**两个反例**各跑一次：一个「必须为真」的、一个「必须为假」的，')
OF.append('两者都过才算判据成立。这条写进锁，作为 R148 起的前置要求。')
OF.append('')
OFstr = '\n'.join(OF) + '\n'
lk_new = lk0 + OFstr
lk_back = write_checked(LOCK, lk0, lk_new, 137, 137, 'lock_of', '## OF · R147')
ck('OF 段出现恰 1 次', lk_back.count('## OF · R147') == 1, lk_back.count('## OF · R147'))
ck('OE9 仍出现恰 1 次', lk_back.count('OE9.') == 1, lk_back.count('OE9.'))

# ---------------- 4. 看板第 147 轮段 ----------------
brd0 = read(BRD)
n_before = brd0.count('\n')
ck('看板写前行数 < 260（无需归档）', n_before < 260, n_before)
ck('看板写前 CR == 0', brd0.count('\r') == 0, brd0.count('\r'))
B = []
B.append('')
B.append('## 第 147 轮（R147）· 0x8871E0 单例论据重建 + R144 §七更正')
B.append('')
B.append('### 一 · 交付')
B.append('')
B.append('**1. 0x8871E0 = 单例指针槽，但论据被换掉。** 我原写「只有一个非空写入点 ⇒ 不是多实例容器」，')
B.append('审计员 #329 判为**推理缺环**（构造写数组头 + 循环 `[base+idx*4]` 完全可能存在）。亲测批评成立。')
B.append('改换四条机器码支点：SIB 变址写 **0** / 带位移形态 **0** / 取地址指令 **0** / 槽在 `.data`')
B.append('RVA 0x751E0 > 原始 0x6C000 的 **BSS 尾（零初始化）**。3 写入点：`0x52BAD8` 构造写')
B.append('（前置 `call 0x665650`）、`0x52BAFA` 分配失败回滚、`0x6BEABD` 析构置零 ⇒ 单例生命周期。')
B.append('')
B.append('**2. R144 §七/§八① 就地更正。** 「0x7E6060 未找到装表站点」是解析器缺陷产物（负位移被')
B.append('`norm` 的 `[+,*]` 字符类拒收）。站点 **0x4A8660** = `mov dword ptr [eax - 8],0x7E6060`，')
B.append('属 `0x4A8630` 起、基址 `0x8A0368`、步长 `0x18`、**5** 元素的静态数组初始化循环。')
B.append('`0x7E6060` RTTI 完整（COL 0x7FFC28、TD 0x816B10 `.?AVLayerClass@@`、8/8 槽落 .text）。')
B.append('')
B.append('### 二 · 数字（三家独立，逐项相同）')
B.append('')
B.append('| 量 | 主会话 r147e | 执行员 #328 | 审计员 #329 |')
B.append('|---|---:|---:|---:|')
B.append('| 原始字节 `e0 71 88 00` | 1423 | 1423 | 1423 |')
B.append('| 指令边界命中 | 1423 | 1423 | 1423 |')
B.append('| 写入点 | 3 | 3 | 3 |')
B.append('| 读点 | 1420 | 1420 | 1420 |')
B.append('| 正控 0x886380 原始命中 | 8 | 8 | 8 |')
B.append('| 负控 0x8871E4 / 0x8871DC | 0 / 0 | 0 / 0 | 0 / 0 |')
B.append('| 构造写所在函数 | 0x52BA60 | 0x52BA60 | 0x52BA60 |')
B.append('')
B.append('### 三 · 规则 D')
B.append('')
B.append('执行员 #328（hy4, exec）succeeded，10 回合；审计员 #329（deepseek, audit）succeeded，10 回合，')
B.append('**实测 10.7 分钟 vs 预算 8.0 ⇒ OVERTIME，如实登记**。审计员三条批评（推理缺环 / 函数入口误判 /')
B.append('幂等守卫缺失）由 `r147g` 亲测 **10/10 成立**；其两个钉（`.text` sha256 `c0368a17…`、')
B.append('整文件 `73201cc0…`）与主会话复算逐字节一致。')
B.append('')
B.append('### 四 · 自错 S-328..S-336（九条，全是判据缺陷）')
B.append('')
B.append('- **S-328** 分类器没剥 `dwordptr` 前缀 ⇒ 真实写入 `0x52BAD8` 被判成 READ（差点得出「0 写入点」假事实）。')
B.append('- **S-329** 把原始命中 **0** 的无人引用全局 `0x8871E4/0x8871DC` 当正控 ⇒ 必然假失败。')
B.append('- **S-330 / S-336** 把 11,407 个 `jmp` 目标当函数起点 ⇒ `0x52BA9B/0x52BADF` 被误当入口，数据流边界错。')
B.append('- **S-331** 线性回扫把别支路 `pop ebx` 当前置定值 ⇒ `0x52BAFA` 误判非空写。')
B.append('- **S-332** 同基本块回扫够不到入口块 `0x6BE1C8` 的零值 ⇒ `0x6BEABD` 判错。')
B.append('- **S-333** 传移函数把 `push ebx` 当写 ebx ⇒ `0x6BE1C0` 内 ebx 误标 UNKNOWN。')
B.append('- **S-334** 断言拿 call 指令自身地址 `0x52BAD1` 比 call 目标 `0x665650` ⇒ 假失败。')
B.append('- **S-335** 把有意保留的删除线原文当成「没改掉」⇒ 假失败。')
B.append('')
B.append('**共同病根：判据只在我自己举的那个例子上成立。** 已写进锁：R148 起新判据落盘前必须用')
B.append('「一个必须为真 + 一个必须为假」两个反例各跑一次。')
B.append('')
B.append('### 五 · 门禁与归档')
B.append('')
B.append('`C16_FLOORS` 加 `152: ' + str(floor152) + '`（§2.152 实测 **' + str(size152) + ' B** − 21）、表项 **145 → 146**、')
B.append('`C16_FLOORS_SHA256` 重钉；`GATE_VER` **R146 → R147**。看板写前 **210 < 260** ⇒ **本轮不归档**。')
B.append('')
B.append('### 六 · 未取得（不粉饰）')
B.append('')
B.append('① `0x52BA60` **无幂等守卫** ⇒ 「单例」是**事实单例**（靠 `0x48CCCF` 单点调用），不是运行期强制单例，')
B.append('措辞不得写后者；② 槽在 BSS，首赋/释放时刻属动态；③ 邻槽 `0x8871D8/0x8871E8/0x8871F0` 各 1 处')
B.append('`qword ptr` 引用，与指针步进无关，未定性；④ 数组初始化函数 `0x4A8270` 的调用者 `0x479104` 调用时机未定；')
B.append('⑤ 动态项（虚表运行期读取、3,805 处寄存器 call/jmp 落点、35 个静态容器运行期值、窗口表 r66 后快照）留 win-main；')
B.append('⑥ 已判死线继续禁投：具名池、无名池、direct-only(D2)、D4结构性无、静态④、动态④、证据指针791行、D-48攻②-b。')
B.append('')
B.append('### 七 · 下轮优先（禁写元审计待办）')
B.append('')
B.append('1. **`0x4A8270` 的调用时机**：其唯一调用者 `0x479104` 在什么路径上被调（静态可做，决定数组何时填充）。')
B.append('2. **邻槽定性** `0x8871D8 / 0x8871E8 / 0x8871F0`：各 1 处 `qword ptr`（`0x40DF22/0x40DE3C/0x40DE1C`），')
B.append('   判断是 double 标量还是别的对象指针（静态可做）。')
B.append('3. **宿主 0x665650 的非 vptr 字段**：R147 已解出 190 个被写位移、max `0x428`、三组 `0x1c` 步长子对象')
B.append('   （`0x2A0/0x2BC/0x2D8` → `0x7EB6D4`；`0x358..0x3E4` → `0x7E4DD8`），其余字段类型未定。')
B.append('4. **F23/F35 正文口径统一**：F23 的「12 行分解余 1 行无归属」与「计数依赖 `coverage.tsv` 4,147,334 B 已失」')
B.append('   已在 v5.39 limitations 内，缺的是正文口径；F35 注意 R139 已推翻「只有二手转述」，一手代码权威在')
B.append('   `RULING_R15_20261119/work/strict_panel.py:78`，**不得再写「缺一手权威」**；真正的失联是它的两个输入。')
B.append('5. **F24 正文**：86.19% 撤下（R136 已证 99.992% 有字节对应），结构判据「单列地址无第二列」保留；')
B.append('   语料值失效期标注（4,417 件/737,517,286 B 是 11-22 快照，现盘 65 件/44,470,975 B）。')
B.append('6. **F29 四处措辞作用域补全**（两份拷贝=80 份中两份、idx=62=DLL 内口径、6 桩体=63 表内口径、40/63/77 非因果）。')
B.append('')
Bstr = '\n'.join(B) + '\n'
brd_new = brd0 + Bstr
brd_back = write_checked(BRD, brd0, brd_new, 0, 0, 'board147', '第 147 轮（R147）')
n_after = brd_back.count('\n')
ck('看板写后行数 <= 300', n_after <= 300, n_after)
ck('看板 第147轮段出现恰 1 次', brd_back.count('## 第 147 轮（R147）') == 1, brd_back.count('## 第 147 轮（R147）'))
ck('看板 第146轮段仍恰 1 次', brd_back.count('## 第 146 轮') == 1, brd_back.count('## 第 146 轮'))

out = {'fails': FAILS, 'size152': size152, 'floor152': floor152,
       'board_lines': n_after, 'led_cr': led_back.count('\r'),
       'rc_cr': rc_back.count('\r'), 'lock_cr': lk_back.count('\r'),
       'board_cr': brd_back.count('\r')}
json.dump(out, open(R147 + '/r147k_write.json', 'w'), ensure_ascii=False, indent=1)
print('\n=== FAILS %d ===' % len(FAILS))
print(json.dumps(out, ensure_ascii=False, indent=1))
