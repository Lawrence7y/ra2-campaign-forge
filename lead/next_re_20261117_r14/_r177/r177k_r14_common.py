# -*- coding: utf-8 -*-
"""R177：R14_COMMON 追加 §2.182（全 LF、CR 保持 1081）。唯一改动 = 末尾追加。"""
import hashlib, os, sys
P = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R14_COMMON.md'
PASS = FAIL = 0
def ck(n, c, d=''):
    global PASS, FAIL
    if c: PASS += 1; print('PASS', n, d)
    else: FAIL += 1; print('FAIL', n, d)

SEC = '''
## 2.182 · R177：F35 的「引文自指」被做成**终止式**之前的定量前提（增量 = 段内字面数，不是常数 1），F29 的同一律给出**首个不动点**；F24 的 86.19% 八处逐处定性为「5 撤回 + 3 定性 + 0 裸用」

**一 · 任务单三条被盘上实况裁定.** ① R177 任务单写「F23 补『12 行分解余 1 行无归属』与『计数依赖 coverage.tsv 4,147,334 B 已失』」—— **两条都已在盘**：`_r177/r177c` 14 断言实测，「1 行无归属」在 F23 statement 1 次 / limitations 1 次、`4,147,334` 在 statement 2 次 / limitations 7 次、「已失」1/4 次；闭世界逐版扫 V530..V559，「1 行无归属」首现 **V540**、`4,147,334` 首现 **V533**；V557/V558/V559 三版四计数逐字相同（未被后轮污染）。② 任务单写「F35 补『proved_strict 定义缺一手权威』」—— **该补与正文相反**：V559 的 F35 statement 第 468 字符处逐字写「R138 那句『**缺一手权威**』**已撤回，不得再写**」，R159 段另有「一句『缺一手权威』与一句『已有一手权威』**都过强**」。按任务单字面追加会在一行内制造互斥 ⇒ **本轮不做该补充**，只登记该任务单条已过期。③ 任务单写「F29 的 6 桩体 = 63 表内口径」—— **口径方向反了**：正文的真说法是「**63 只用到 6 个桩**」，6 的**基数是 40（桩集合）不是 63（表数）**，且正文显式写「其余 34 个桩（40−6）不参与任何计数」（`_r177/r177d` 13 断言；我首版把「6 个不同桩体不在 limitations」写反，实测 3 次 ⇒ S-643，当场被断言抓出）。

**二 · 自指律的定量形式（跨家族审计员 #420 提出，主会话复算采纳）.** R174-R2 段原本的写法带一个隐含假设：「每追加一段，计数 +1」。逐版实测推翻它：F35.limitations 的「同血缘克隆 / 不是独立实现」增量是 **V553→V554 +0/+2、V554→V555 +3/+2、V555→V556 +1/+1、V556→V559 +0/+0**，即**增量 = 该新增段自身的字面出现数**，不是常数（`_r177/r177f` 22 断言 0 FAIL）。**段身份必须按段头建索引**（到「】」为止）：用「全文等值」当段身份会把「被改动一个标点的旧段」误判成新增段 —— 首版据此得出 V554 新增段字面 (1,4) ≠ 增量 (0,2) 三断言全红，逐段 diff 后真相是旧段只多了一个 `**`（S-642）。**这条律给 F35 的收口判据**：若要让计数成为一次性声明，补段必须用代称、不复述本体；反过来说，R174-R2 段写入后 V557/V558/V559 三版 F35 行 sha256 恒为 `8fdd3d267ec7`（逐字节相同）⇒ 自指在**没有新补段**时不会自己恶化。

**三 · F29 的第一个不动点（本轮唯一正文改动）.** R170 段逐字写「该串在 statement **1** 次、limitations **2** 次、合计 **3** 次」，而该段**自身即含被计数的串 1 次** ⇒ 落盘后 limitations 实为 **3**、合计 **4**（逐版：V540–V544 limitations 1、V545–V549 **2**、V550 起 **3**，statement 恒 1；`_r177/r177e` 9 断言 0 FAIL）。V560 在 F29.limitations 末尾追加一段**只用「该串」指代、不复述本体**的订正段，声明 limitations 3 / 合计 4 —— 写入后实测仍为 3/4 ⇒ **声明值与实测值重合，是不动点**。反控（必须为假）：把该段的「该串」换回本体，实测立刻变 4 ≠ 声明 3（`_r177/r177i` 32 断言 0 FAIL，含 csv 回环与逐单元 diff：差分行恰 F29、差列恰 limitations、其余 54 行 × 5 列逐字节相同）。**这也把 R176 遗留待办 2「F35 计数随每加一段 +1」的处置前提补齐**：不是「每加一段 +1」，而是「加多少复述就加多少」，故终止式只要保证复述为 0 就成立。

**四 · F24 的 86.19% 八处逐处定性（任务单 ②）.** 判据：按小句切（千分位逗号不作界、括注内标点不作界），某处出现若其小句或后置括注内含撤销词（撤下/撤销/撤回/不得再）或定性词（补集/覆盖率/口径/未覆盖），判非裸用。实测 statement 3 处 + limitations 5 处 = **8 处：5 处撤回说明 + 3 处定性说明 + 0 处裸用**（`_r177/r177g` 10 断言，正控「因此 86.19% 是剔除 bounds 的理由」判裸用、反控「86.19% 已由 R138 撤销」判撤回）。结构判据同时在场：statement「单列地址」2 次、展开式「没有可回原址复核的第二列」1 次、「仍剔」1 次 ⇒ **数字撤下、结构判据保留，两者确已分开处理**。

**五 · F24 语料值的失效期标注（任务单 ③）.** 四个被测值 31 处：`4,417` 10 处、`737,517,286` 13 处、`65 件` 4 处、`44,470,975` 4 处。二态判据实测 **30/31 已限定**，唯一落空的是 limitations 里「**主引值本身未变**（737,517,286 B 自 v5.29 起一直是它）」——它做的是**版本跨度**断言（自 v5.29 起未变，逐版实测为真），不是**磁盘体量**断言 ⇒ 「快照/现盘」二态判据对它**沉默**，这是**判据的盲区**、不是正文的缺陷；该句属历史段，本轮只登记不改（`_r177/r177h` 10 断言，断言方向固定为「恰 1 处且恰是该句」，多一处或落到别句都 FAIL）。

**六 · 落盘与门禁.** V559→**V560** = **130,510 B** / 55 行 5 列 / CR 0 / sha256 `ede48f3c32048040…`；只改 F29.limitations（14,222 → **15,259** B，+1,037）、全文 **+1,105 B**。门禁重钉：`EXPECT_CUR`→V560、`CUR_SHA256`→`ede48f3c…`、`TOTAL_BYTES`→130510、`FLOORS['F29']` (3435,14222)→**(3435,15259)**、`MASTER_SHA256` `b5fdc174…`→**`db88d9b87ffdd8d0…`**（facts 恰 5 行、gate_runner 恰 1 行；改前先 ast 取 12 个常量复算旧 MASTER 命中 `b5fdc174…` 作硬闸）。三段实跑：`facts_floors` D0/D6/D8/D9 全过 exit 0、`check_disc` exit 0（C16 NOTE 175 sections pinned 175 unpinned 0）、`gate_runner` G1=G2=G3=ok（`GATE_VER` 仍 R166）；反向验证显式传 V559 实测 **D0 + D6 + D8 三红**。

**七 · 自错 S-642..S-645（全部由可失败断言当场抓出，无一条进入结论）.** S-642 把「全文等值」当段身份（见第二节）；S-643 把「6 个不同桩体在 limitations 3 次」写反成「不在 limitations」；S-644 r177f 首版断言方向写成「新增段全文相等」而非「段头索引」；S-645 r177h 首版把「二态判据 100% 覆盖」当应然，实测 30/31 —— 处置是**给盲区定性并固定盲区数量**，不是把断言放宽成恒真。

**八 · 未取得（不因本轮开工而改变）.** coverage.tsv 与 function_atlas.tsv 仍不可读 ⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 n 分母仍不可重数；F23/F35 的 grade 未改（裁定不是取证）；C7 三死分支 exists/bytes=/none 仍各 0 行；C11 十二个永不 FAIL 的 id 未动；86.19% 原值仍不可重算；`_ext/f_partial_triage/` 两件未补版本号。
'''
raw = open(P, 'rb').read()
ck('A1 pre bytes', len(raw) == 1549611, '%d' % len(raw))
ck('A2 pre CR=1081', raw.count(b'\r') == 1081, '%d' % raw.count(b'\r'))
ck('A3 pre LF', raw.count(b'\n') == 13963, '%d' % raw.count(b'\n'))
# S-646：A4 首版写成 `== '<假 sha>' or True`，是恒真断言（本项目点名的「永远通过子项」）。
# 改为拿备份文件的 sha 作真实对照，并在写盘后断言母本前态未被本脚本改动。
_bak = None
for fn in sorted(os.listdir('R17_LEAD_BASELINE')):
    if fn.startswith('R14_COMMON.md.before_r177_') and fn.endswith('.bak'):
        _bak = os.path.join('R17_LEAD_BASELINE', fn)
if _bak is None:
    ck('A4 找不到本轮备份，无法建立硬闸', False)
    sys.exit(1)
_braw = open(_bak, 'rb').read()
ck('A4 pre sha == 本轮备份 sha（真实对照，非恒真）', hashlib.sha256(raw).hexdigest() == hashlib.sha256(_braw).hexdigest(),
   hashlib.sha256(raw).hexdigest()[:16])
ck('A4b 备份字节数等于读入字节数', len(_braw) == len(raw), len(_braw))
txt = raw.decode('utf-8')
ck('B1 2.182 未存在', '## 2.182' not in txt, txt.count('## 2.182'))
ck('B2 2.181 存在恰 1', txt.count('## 2.181') == 1, txt.count('## 2.181'))
ck('B3 段尾以 LF 结束', txt.endswith('\n'))
ck('B4 新段不含 CR', '\r' not in SEC)
ck('B5 新段以 LF 开始与结束', SEC.startswith('\n') and SEC.endswith('\n'))
new = txt + SEC
ck('C1 CR 仍 1081', new.count('\r') == 1081, new.count('\r'))
ck('C2 LF 增量为新段行数', new.count('\n') - txt.count('\n') == SEC.count('\n'), new.count('\n') - txt.count('\n'))
ck('C3 旧内容逐字保留（前缀相同）', new.startswith(txt))
ck('C4 2.182 恰 1 次', new.count('## 2.182') == 1, new.count('## 2.182'))
ck('C5 新段声明值 3/4 与实测对应', 'limitations 3 / 合计 4' in SEC)
if FAIL:
    print('ABORT %d FAIL' % FAIL); sys.exit(1)
rb = open(P, 'rb').read()
import sys as _s
if '--dry' in _s.argv:
    print('--dry: A/B/C 段断言完毕，未写盘。C1..C5 针对「若写盘会怎样」的构造值。')
    print('---- %d PASS / %d FAIL (dry) ----' % (PASS, FAIL)); _s.exit(0 if not FAIL else 1)
with open(P, 'wb') as f:
    f.write(new.encode('utf-8'))
rb = open(P, 'rb').read()
ck('D1 readback equals', rb == new.encode('utf-8'))
ck('D2 readback CR=1081', rb.count(b'\r') == 1081, rb.count(b'\r'))
ck('D3 readback LF=%d' % (13963 + SEC.count('\n')), rb.count(b'\n') == 13963 + SEC.count('\n'), rb.count(b'\n'))
print('R14_COMMON = %d B / cr=%d / lf=%d' % (len(rb), rb.count(b'\r'), rb.count(b'\n')))
import re
m = re.search(r'(?s)\n## 2\.182 .*', new)
secbytes = len(m.group(0).encode())
print('§2.182 measured bytes = %d -> C16 floor = %d' % (secbytes, secbytes // 2))
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
