#!/usr/bin/env python3
# R131 r131w2: close-out append -- records the gate work done AFTER the first append
# (C16 re-pin of 2.135, C18 controls, and the four self-errors found while doing it),
# so the ledger does not describe a state that no longer exists.
import hashlib, io, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
R14=os.path.join(ROOT,'lead','next_re_20261117_r14')
COMMON=os.path.join(R14,'R14_COMMON.md'); LEDGER=os.path.join(ROOT,'lead','GOAL_THREE_TARGETS_20261018.md')
LOCK=os.path.join(ROOT,'lead','LEAD_LOCK'); BOARD=os.path.join(R14,'STATUS_BOARD.md')
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131w2_closeout.json'
A=[]
def chk(n,c,d=''):
    A.append({'assert':n,'ok':bool(c),'detail':d}); print(('PASS ' if c else 'FAIL ')+n+(' :: '+str(d) if d else ''))

COMMON_ADD = """
十一、收口期追加（如实记，不改上文）。写完 2.135 后门禁当场报 unpinned 1——新增一节就白得一张永久免检票，正是本仓被咬过多次的那件事。按半量规则重钉：2.135 正文实测 6118 B，取 3059；表条目 128 -> 129；摘要 9bc92f2c05c797ef -> 0241a4666162ba57。重钉后 pinned 129 / unpinned 0 / hollow 0 / missing 0 / min margin 1155。

十二、C16 重钉的反控 11/11（r131z）：正控 exit 0 且 C16 显示 pinned 129、unpinned 0；把 135 的下界从 3059 改成 1，exit 1 命中 C16d（摘要不对）；改成 99999，exit 1 同时命中 C16d 与 C16 hollowed out [(135, 6118, 99999)]；把 135 条目整条删掉，exit 1 命中 C16d——注意此时未钉节数是 1，仍在阈值 2 以内，所以**只有摘要那一道拦得住**，这就是加摘要钉的意义；把 2.135 正文换成单个字符，exit 1 命中 C16 hollowed out [(135, 10, 3059)]；每次恢复都只从内存写回，R14_COMMON 与 check_disc 的字节与 CR 均回基线。

十三、C18 的独立反控 9/9（r131v）：正控 exit 0；把 c17_checked 改 1、c11_ok 改 5、frozen_rows 改 13，三次各自 exit 1 并命中 C18；只把因果那一行关掉而三个计数不动时仍 exit 0——这一条是关键，它证明 C18 是两个条件（计数 + 因果），不是把同一个判断写两遍；六次改盘后门禁字节逐字节回原。

十四、自错再四条留案。S-205：把调用点窗口取成「站点减 0x30」，落在指令中间，解出 aam 0xf5，args 直接为空；改从循环自己的指令边界 0x6bc342 起解。S-206：把 7 & 0x14 算成 0（其实是 4），于是把「CoCreateInstance 确实被调」写成了反的。S-208：判断门禁有无失败时用了 'FAIL' not in out，而 NOTE 文本里就有 "can never FAIL" 这个短语，于是永远判有失败；改成只看行首 'FAIL '。S-209：把正文分节的正则套在门禁源码上用，当然找不到 2.135 标题，随后在 None 上取 .start() 崩掉。另有 S-211：r131y 是幂等性坏的——重跑一次会在 C16_FLOORS 里再追加一条 135，而摘要仍算「OK」，因为重复项被 normalize 成同一个字典键。这一条最值得记：**摘要校验挡不住重复条目**，靠的是人看一眼 C16 打印的条目数（129 而不是 130）。

十五、边界重申：本节全部结论是「字节是什么」与「字节算出来是什么」。blowfish.dll 在运行期是否真的被注册成功，静态看不到；「为何只带一个自注册 DLL」是构建配置问题，静态也没有答案。
"""

LEDGER_ADD = """
- **交付七（C16 重钉 2.135）**：正文实测 6118 B 取 3059，条目 128 -> 129，摘要 9bc92f2c05c797ef -> 0241a4666162ba57；重钉后 pinned 129 / unpinned 0 / hollow 0 / missing 0。反控 11/11（r131z），含「删掉条目时未钉节数 1 仍在上限 2 内，只有摘要拦得住」这一条。
- **交付八（C18 反控 9/9）**：三个计数各改一次均 exit 1 命中 C18；只关因果那一行而计数不动仍 exit 0，证明 C18 是两个独立条件而非同一判断写两遍。
- **自错再四条**：S-205 调用点窗口落指令中间（解出 aam，args 为空）；S-206 把 7 & 0x14 算成 0；S-208 用 'FAIL' 子串判断门禁失败，而 NOTE 里有 "can never FAIL"；S-209 把正文分节正则套在门禁源码上。另有 S-211：r131y 不幂等，重跑会重复追加 135 而摘要仍报 OK——**摘要挡不住重复条目**，靠看条目数。
"""

LOCK_ADD = """
KW. 收口期追加（如实记，不改上文）：写完 2.135 后门禁报 unpinned 1，按半量规则重钉（正文实测 6118 B 取 3059，条目 128 -> 129，摘要 9bc92f2c05c797ef -> 0241a4666162ba57），重钉后 pinned 129 / unpinned 0 / hollow 0 / missing 0 / min margin 1155。反控 11/11（r131z）：下界改 1、改 99999、整条删掉、正文换单字符，四次各自 exit 1；其中「整条删掉」这一次未钉节数是 1、仍在上限 2 以内，**只有摘要那一道拦得住**，这就是加摘要钉的意义。恢复只从内存写回，两文件字节与 CR 均回基线。

KX. C18 的独立反控 9/9（r131v）：三个计数各改一次均 exit 1 命中 C18；只把因果那一行关掉而计数不动时仍 exit 0——证明 C18 是两个独立条件（计数 + 因果），不是把同一个判断写两遍。六次改盘后门禁字节逐字节回原。

KY. 自错本轮共七条，后四条是收口期新增。S-205：调用点窗口取「站点减 0x30」，落在指令中间解出 aam 0xf5，args 为空；改从循环自身指令边界 0x6bc342 起解。S-206：7 & 0x14 算成 0（实为 4），把「CoCreateInstance 确实被调」写反。S-208：用 'FAIL' 子串判断门禁有无失败，而 NOTE 文本里就有 "can never FAIL"，于是永远判有失败；改成只看行首。S-209：把正文分节正则套在门禁源码上，找不到 2.135 标题后在 None 上崩。S-211 最值得记：r131y 不幂等，重跑一次会在 C16_FLOORS 里重复追加 135 条目，而摘要校验仍报 OK（重复项 normalize 成同一个字典键）——**摘要挡不住重复条目**，靠人看 C16 打印的条目数是 129 而不是 130。

KZ. 断言合计：r131q 35 + r131r 12 + r131s 9 + r131t 15 + r131v 9 + r131y 12 + r131z 11 + r131w 11 = 114 项全 PASS（r131p 8 项另计入探索口径）。终态 check_disc.py exit 0、C10 ok(R131)、C16 pinned 129 / unpinned 0、C18 note 在场。五项 CR 1081/137/337/0/2952 全绿；看板 174 行未到 260 阈值，本轮不归档（归档 CR 仍 2952）。
"""

BOARD_ADD = """
**十三 · 收口期：新节必须当场钉住。** 写完 2.135 后门禁立刻报 unpinned 1。按本仓半量规则重钉：正文实测 6118 B 取 3059，条目 128 到 129，摘要换成新值。重钉后 pinned 129 / unpinned 0 / hollow 0 / missing 0。反控 11/11，其中一条特别值得记：把 135 条目整条删掉时，未钉节数是 1、仍在上限 2 以内，**只有摘要那一道拦得住**——这就是摘要钉存在的理由。

**十四 · C18 反控 9/9，关键在于它证明自己不是一个判断写两遍。** 三个计数各改一次都 exit 1 命中 C18；而只把「因果」那一行关掉、三个计数都不动时，门禁仍然 exit 0。若是同一判断写两遍，这一条必然也 FAIL。六次改盘后门禁字节逐字节回原，恢复只从内存写。

**十五 · 自错七条全留案，最后四条是收尾期现抓的。** S-205 把调用点窗口取成「站点减 0x30」，落在指令中间解出 aam，参数直接为空；S-206 把 7 & 0x14 算成 0（实为 4），把结论写反；S-208 用 'FAIL' 子串判断门禁有无失败，而 NOTE 里就有「can never FAIL」这个短语，于是永远判有失败；S-209 把正文分节正则套在门禁源码上，在 None 上崩。

**十六 · S-211 单独拎出来：摘要校验挡不住重复条目。** 我写的重钉脚本不幂等，重跑一次会在 C16_FLOORS 里再追加一条 135；而摘要仍报 OK，因为重复项 normalize 进同一个字典键。发现它靠的是人看一眼门禁打印的条目数（129 而不是 130）。已删掉重复项并逐字节核对。这条的教训不是「加更多校验」，而是「幂等性要单独测」——摘要只证明表内容，不证明表没有冗余。

**十七 · 收口复验。** r131q 35 + r131r 12 + r131s 9 + r131t 15 + r131v 9 + r131y 12 + r131z 11 + r131w 11 = 114 项断言全 PASS。终态 check_disc.py exit 0、C10 ok(R131)、C16 pinned 129 / unpinned 0、C18 note 在场；五项 CR 1081/137/337/0/2952 全绿；看板 174 行未到 260 阈值，本轮不归档。
"""

def crlf(b): return b.count(b'\r\n')
def app(path, text, want_cr, label):
    orig=io.open(path,'rb').read(); osha=hashlib.sha256(orig).hexdigest(); ocr=crlf(orig)
    chk('%s CR before == %d'%(label,want_cr), ocr==want_cr, ocr)
    body=text.encode('utf-8')
    chk('%s appended text has no CR'%label, b'\r' not in body)
    if not orig.endswith(b'\n'): raise SystemExit(label+' no trailing LF')
    if not body.endswith(b'\n'): body+=b'\n'
    new=orig+body
    try:
        io.open(path,'wb').write(new)
        back=io.open(path,'rb').read()
        chk('%s readback identical'%label, back==new)
        chk('%s CR preserved'%label, crlf(back)==want_cr, crlf(back))
        print('   %-34s CR %d->%d  +%d bytes'%(label,ocr,crlf(back),len(back)-len(orig)))
        return {'ok':True,'sha_before':osha,'sha_after':hashlib.sha256(back).hexdigest()}
    except Exception:
        io.open(path,'wb').write(orig); raise

rec={}
rec['common']=app(COMMON,COMMON_ADD,1081,'R14_COMMON.md')
rec['ledger']=app(LEDGER,LEDGER_ADD,337,'GOAL_THREE_TARGETS_20261018.md')
rec['lock']=app(LOCK,LOCK_ADD,137,'LEAD_LOCK')
rec['board']=app(BOARD,BOARD_ADD,0,'STATUS_BOARD.md')
b=io.open(BOARD,'rb').read(); rec['board_lines']=b.count(b'\n')
chk('board under 300 lines',rec['board_lines']<=300,rec['board_lines'])
chk('board CR still 0',b.count(b'\r\n')==0)
rec['assertions']=A; rec['summary']={'total':len(A),'pass':sum(1 for x in A if x['ok']),
  'fail':[x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'%(rec['summary']['total'],rec['summary']['pass'],len(rec['summary']['fail'])))
json.dump(rec,open(OUT,'w'),ensure_ascii=False,indent=1)
raise SystemExit(1 if rec['summary']['fail'] else 0)
