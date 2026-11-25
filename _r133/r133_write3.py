#!/usr/bin/env python3
# R133: append ledger §1187, LEAD_LOCK LM, and STATUS_BOARD round entry.
# Three files, three independent edits, each under backup -> write -> readback.
# All must stay LF-pure where they already are (ledger CR keeps 337, lock CR keeps 137,
# board CR stays 0). Verified AFTER all three writes, per S-217.
import io, hashlib, os, time, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
BAK = os.path.join(ROOT, 'R17_LEAD_BASELINE')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(ROOT, 'lead/next_re_20261117_r14/STATUS_BOARD.md')
ts = time.strftime('%H%M%S')

def backup(p, b, tag):
    bp = os.path.join(BAK, os.path.basename(p) + '.before_R133_%s_%s.bak' % (tag, ts))
    fd = os.open(bp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    os.write(fd, b); os.close(fd)
    assert open(bp, 'rb').read() == b, bp
    print('  backup ->', os.path.basename(bp))

LEDGER = """
## §1187 R133：修 C7 三个死分支（钉普查而非造产物），主会话独立复算 R132 两条承重结论

- **基准**：R14_COMMON §2.136 (CR=1081) | 台账 §1186 (CR=337) | LEAD_LOCK LL (CR=137) | 看板 208 行 (CR=0) | 归档 CR=2952
- **门禁真修第五处**：C7 的 exists / bytes= / none 三个分支在 31 行里各覆盖 0 行（R132 实测，R133 r133g 复测仍 0/0/0，8/8 PASS；r133h 证注入一行对应形态会把计数 0 推到 1，即钉有分辨力）。修法**不为不可达形态硬造产物**——那会制造一条只为过门禁而存在的行；改为新增 **C7b**：把整张形态普查 `24/3/4/0/0/0` 显式钉住，漂移即 FAIL。
- **正反控 13/13 PASS（r133j2）**：PC1 未改副本 exit 0；PC2 六键全打印；PC3 C7 结果行也带普查；三个 NC 各把一条 grep 行改成 exists / bytes=999 / none，三次都 exit 1 且报 drifted；NC4 删掉零值播种行后零值键报 vanished（exit 1）；NC5 表与钉同时改动后 C7b 不再报漂移（可重钉，非不可过的死闸）；RES1/RES2 证注入一行 none 把计数 0 推到 1。真实树前后 sha 相同。
- **控制脚本自身两次方法事故，如实记**。第一次 r133j 用 copytree 复制整个 R14（811 MB，其中 R17_LEAD_BASELINE 独 766 MB 而门禁一字节不读），六次复制写进 tmpfs 约 4.8 GB，撞自己 600 秒 timeout（exit 143），**一个断言都没跑出来**——这不是对门禁的判决，是控制脚本缺陷，故重跑不改写结论。第二次改为按实测文件集暂存，但手写清单漏了 place_r87.py（门禁第 74 行 import），每个暂存副本都在 import 阶段失败、13 项全报 FAIL 而原因与 C7b 无关。最终改为现场用 io.open/builtins.open 探针推导文件集，并补 R14 顶层全部 .py（importlib 走 _io.open_code，绕过两个探针）。教训与 S-216 同族：**控制失败的第一次读数必须先归因到控制本身。**
- **用实验而非读代码判定审计分歧**。hy4 称 C7b 的 exists/bytes=/none 三键是惰性键（播种后恒 0==0，不可能触发）。我直接把钉住的 exists 从 0 改成 1 而表不动：门禁 exit 1 并打印「C7b shape census drifted: exists=0 but pinned 1」。**三键决策相关，hy4 此条错。**
- **但 hy4 另一条对，且是我代码注释里的错**。我原注释写「播种是让 exists=0 可检查的原因」。hy4 指出不播种时 loop1 仍能经 C7_SHAPE_PIN.get(k) != measured 抓到新出现的一行，故播种不是「可检查」的原因；播种真正修的是相反的 bug——不播种时 loop2 会把三个零值形态报成 vanished，即在健康表上伪造三条失败。复算确认后改注释（本轮第二次改门禁，只改事实错误陈述，不改逻辑），改后 exit 0、控制套件仍 13/13。
- **主会话独立复算 R132 两条承重结论，22/22 PASS**。自写 PE 解析、GUID 格式化与逐字节比较，不复用 _r133 代码：两处差异确为 0x4e 与 0x70（均 c0/b0），且都是 push imm32 的立即数字节 0（操作码 0x68 在 +0x4d / +0x6f，差 1）；指针差 1 字节而所指 GUID 差 15 字节，两事同真；0x817bc0 = IID_IUnknown {00000000-0000-0000-C000-000000000046}、0x817bb0 = {070F3290-9841-11D1-B709-00A024DDAFD1}，相距恰 0x10，同在 .data。反控：读 0x817bd0 得不同串、大小端给出不同串。
- **分支结构独立复算 22/22 PASS**。两实例各 136 字节 / 56 条指令 / 末条 ret 0xc；test al,0x14 在 +0x14、je 在 +0x16，目标 A=0x6bee1a / B=0x41c2ba；该目标在体内恰被 1 条分支指向（就是那条 je），其前一字节结束于 ret 0xc（无直落）；else 臂恰 1 条 call 且为 [0x7e15fc]，不含 0x7e1600；if 臂含 0x7e1600，故 OleRun 在活臂。
- **arg3 在 15 个调用点全为 7，主会话独立解出**。第一版把「最近三条 push」取反（拿成最远三条），得一堆 GUID 指针当 arg3；第二版犯元组索引错（t[1] 是 size 不是 mnemonic），walk 全空——两条都在反控里当场暴露（S-224/S-225）。修正后 15/15 都是 7，且 arg3 所在地址与 hy4 独立解出的 15 个地址**逐个相同**，两家方法不同，是强互证。
- **规则 D 如实记**。deepseek task 278 **failed 加 error_max_turns**（61 回合 / 6.87 分钟 / 预算 8.0），result 为空、未落报告，故 deepseek 侧本轮无外部输入。hy4 task 279 succeeded（27 回合 / 3.47 分钟）。hy4 每条结论由主会话复算：C1-C6、C8、C9、C11a、C11c 一致；C7/C10 的「仅窄口径成立」确认（if 臂实为 4 条 call 而非 1 条，原卡表述过宽）；C11b 的 DISAGREE 成立且是**我的卡写错**（用 0x817bc0 做大小端反控，其 Data1/Data2/Data3 全零故两种端序同形，应改用 0x817bb0）；G1 实验判定为 hy4 错；G2 为 hy4 对、我注释错；G3 为 hy4 对且是实质漏洞；G4 机制成立但后果不成立（实测暂存副本与真实树 15 条 NOTE 逐行相同、exit 码相同）。
- **未修，如实记**：hy4 的 G3 漏洞本轮只证实不修——普查只看第 6 列首个 token，改第 5 列产品路径则普查不变而 C7 实际检查对象已变。修法不能往普查里加计数（同一维度），需把第 5 列纳入钉住对象，涉及重钉 C14 整表指纹与 C13，属单独流程。
- **自错六条**：S-224 大小端反控用退化输入（0x817bc0 三字段全零）、且 arg3 取成最远三条 push；S-225 元组索引 t[1] 当 mnemonic 用（实为 size），walk 全空；S-226 控制脚本 copytree 811 MB 撞自己 timeout，exit 143 而零断言——把控制缺陷当成被测对象结论；S-227 手写文件集漏 place_r87.py，13 项全假 FAIL；S-228 无锚 'pinned (\\d+)' 正则匹配到 C15 的 pinned 100 而非 C16 的 pinned 131，NC4 假 FAIL；S-229 在 cd 后的相对路径下写 heredoc，脚本落到错误目录、文件根本不存在。
- **收口**：控制 13/13 + 7/7、主会话复算 22/22 + 22/22 + 15/15 地址互证、hy4 结论复算 17/17。门禁改动三处：新增 C7b 普查钉、修正播种注释的事实错误、GATE_VER R132 -> R133 并同步 DISC_RECHECK 第 20 行；新增 2.137 后按半量规则重钉 C16（正文实测 6319 B 取 3159，条目 130 -> 131，摘要 d533653e -> 97195da8）。终态 check_disc.py exit 0、C10 ok(R133)、C7 live-checks 31、C16 pinned 131 / unpinned 0 / hollow 0 / missing 0、五项 CR 1081/137/337/0/2952 全绿；看板 208 行未到 260 阈值，不归档。
"""

LOCK = "LM. R133 主攻 R132 未取得项 ⑤「门禁 C7 三个死分支未修」。修法与前三处门禁修法同向：不为不可达分支硬造产物，而是把「它们确实覆盖 0 行」这一事实本身钉住。\n"

BOARD = """
## 第 128 轮（R133）

**一 · 修 C7 三个死分支，方向是不造产物而钉普查。** R132 实测 C7 的 exists / bytes= / none 三个分支在 31 行里各覆盖 0 行，R133 复测仍 0/0/0。为它们硬造一条产物，只会造出一条只为过门禁而存在的行。改为新增 C7b：把整张形态普查 24/3/4/0/0/0 显式钉住，漂移即 FAIL，逼下一个人先裁定再改数据。

**二 · 正反控 13/13。** 三个 NC 各把一条 grep 行改成 exists / bytes=999 / none，三次都 exit 1 且报 drifted；NC4 删掉零值播种行后零值键报 vanished；NC5 表与钉同时改动后 C7b 不再报漂移（证明可重钉、不是不可过的死闸）；RES2 注入一行 none 把计数 0 推到 1（钉有分辨力）。真实树前后 sha 相同。

**三 · 控制脚本自己坏了两次，如实记。** 第一次 copytree 整个 811 MB 的 R14（其中 766 MB 门禁一字节不读）写进 tmpfs，撞自己 600 秒 timeout，exit 143，零断言跑出——这不是对门禁的判决，是控制缺陷，故重跑而不改写结论。第二次手写文件集漏了 place_r87.py（门禁第 74 行 import），每个暂存副本都死在 import 阶段、13 项全假 FAIL。最终改成现场探针推导文件集 + 补 R14 顶层全部 .py。

**四 · 审计分歧用实验判决，不用读代码判决。** hy4 称 C7b 的三个零值键是惰性键。我直接把钉住的 exists 从 0 改成 1 而表不动：门禁 exit 1 并打印 drifted。三键决策相关，hy4 此条错。

**五 · 但 hy4 另一条对，且是我注释里的错。** 我写「播种是让 exists=0 可检查的原因」。实际不播种时 loop1 仍能抓到新出现的一行；播种真正修的是相反 bug——不播种时 loop2 会把三个零值形态报成 vanished，在健康表上伪造三条失败。复算后改了注释，只改事实陈述不改逻辑。

**六 · 主会话独立复算 R132 两条承重结论，22/22。** 自写 PE 解析与 GUID 格式化：两处差异 0x4e 与 0x70 均为 push imm32 的立即数字节 0；指针差 1 字节而 GUID 差 15 字节，两事同真；0x817bc0 是 IID_IUnknown、0x817bb0 是 {070F3290-...}，相距恰 0x10。

**七 · 分支结构独立复算 22/22。** 两实例各 136 字节 / 56 条指令 / ret 0xc；else 入口在体内恰被 1 条分支指向且直前是 ret（无直落）；else 臂恰 1 条 call = [0x7e15fc] 且不含 0x7e1600；if 臂含 0x7e1600，故 OleRun 在活臂。

**八 · arg3 15/15 全为 7。** 我前两版各有解析错（取成最远三条 push；元组索引 t[1] 当 mnemonic），都在反控里当场暴露。修正后 15/15 为 7，且 arg3 地址与 hy4 独立解出的 15 个地址逐个相同。

**九 · 规则 D。** deepseek task 278 failed 加 error_max_turns（61 回合 / 6.87 分钟），result 为空，故 deepseek 侧无外部输入，本轮不写「已过两家族审计」。hy4 task 279 succeeded（27 回合）。其每条结论由主会话复算：C11b 的 DISAGREE 成立且是我卡写错（大端反控用了退化的 0x817bc0）；G3 成立，是实质漏洞；G4 机制成立后果不成立。

**十 · 未修。** hy4 的 G3：普查只看第 6 列首 token，改第 5 列产品路径则普查不变而 C7 实际检查对象已变。修法需把第 5 列纳入钉住对象，牵动 C14 整表指纹与 C13，属单独流程。

**十一 · 收口。** 控制 13/13 + 7/7、主会话复算 22/22 + 22/22 + 15/15、hy4 复算 17/17。门禁改三处（新增 C7b、改注释事实错、GATE_VER R132->R133 并同步第 20 行），新增 2.137 后按半量规则重钉 C16（6319 B 取 3159，130 -> 131 条，摘要 d533653e -> 97195da8）。终态 exit 0、C10 ok(R133)、C16 pinned 131 / unpinned 0；五项 CR 1081/137/337/0/2952 全绿；看板 208 行未到 260 阈值，不归档。
"""

for p, sec, tag, cr_expected in ((LED, LEDGER, 'ledger', 337), (LCK, LOCK, 'lock', 137), (BRD, BOARD, 'board', 0)):
    b0 = open(p, 'rb').read()
    print('%s: sha=%s bytes=%d CR=%d' % (os.path.basename(p), hashlib.sha256(b0).hexdigest()[:16], len(b0), b0.count(b'\r')))
    assert b0.count(b'\r') == cr_expected, (p, b0.count(b'\r'), cr_expected)
    assert '\r' not in sec, 'appended text must be LF-only'
    backup(p, b0, tag)
    add = sec.encode('utf-8')
    # ensure the previous content ends with a newline so the append is well formed
    prefix = b'' if b0.endswith(b'\n') else b'\n'
    b1 = b0 + prefix + add
    assert b1.count(b'\r') == cr_expected, (p, b1.count(b'\r'))
    with open(p, 'wb') as f:
        f.write(b1)
    b2 = open(p, 'rb').read()
    assert b2 == b1, 'readback mismatch ' + p
    print('  -> sha=%s bytes=%d CR=%d' % (hashlib.sha256(b2).hexdigest()[:16], len(b2), b2.count(b'\r')))

# verify AFTER all three writes (S-217)
print('\n=== verify all three ===')
print('ledger §1187 present:', b'\xc2\xa71187' in open(LED,'rb').read() or '§1187'.encode() in open(LED,'rb').read())
print('lock LM present     :', b'\nLM. ' in open(LCK,'rb').read())
print('board R133 present  :', '第 128 轮（R133）'.encode() in open(BRD,'rb').read())
print('board lines         :', sum(1 for _ in io.open(BRD, encoding='utf-8')))
