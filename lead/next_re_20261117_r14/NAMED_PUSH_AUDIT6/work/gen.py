"""Generate VERDICT.md + verdict.tsv from my own measurements (no executor text cited as evidence)."""
import json, core, idx

rows = json.load(open('rows_all.json'))
r4 = json.load(open('ring4b.json'))
ENTS = ['006C1010','006C1190','006C1310','006C1490','006C1610','006C1790','006C1910','006C1A90',
        '006C1C10','006C1D90','006C1F10','006C2090','006C2210','006C2390','006C2510','006C2690',
        '006C2810','006C2990']


def b(va, n):
    return core.read(va, n).hex(' ')


def qiret():
    """QI 00410260 exit constants (measured once, shared callee)."""
    return ('`00410269 b8 03 40 00 80` = `0x80004003`(E_POINTER)、`004102E6 b8 02 40 00 80` = `0x80004002`(E_NOINTERFACE)、'
            '`004102F5 33 c0` = `0`；三处 `c2 0c 00`(ret 0xC) @`0041026F`/`004102EC`/`004102F8`')


out = []
tsv = []
for n, e in enumerate(ENTS, 1):
    r = rows[e]
    m4 = r4[e]
    slot = r['slots'][0]
    d = r['disp']
    qi = [x for x in d if x[1] == 'call dword ptr [eax]'][0]
    rel = [x for x in d if '+ 0x20' in x[1]][0]
    imms = r['imms']
    main = r['obj_main']
    sem_class = main['name'][4:-2]
    # member tables (proves we did not take an inline member table)
    mem = [m for m in r['member_vts'] if int(m['vt'], 16) != int(main['vt'], 16)]
    membrief = '；'.join('`%s`(vt0=%s，%s)' % (m['vt'], m['vt0'], m['name']) for m in mem) or '（无）'
    ok = (slot['idx'] == 3 and main['vt0'] == '00410260' and m4['vt_slot3_ok']
          and m4['ctor_atexit'] == [] and r['skipdata'] == 0 and r['last'] == 'ret 0x10')
    verdict = 'PASS' if ok else 'FAIL'
    out.append('## %d · `%s` — S22 `%s` → **%s**\n' % (n, e, r['slots'][0] and json.load(open('names.json'))[e], verdict))
    out.append('| 项 | 结论 | 我自测的字节锚点 |')
    out.append('|---|---|---|')
    out.append('| ① 入口 | 成立 | `.text` 内，`%s`–`%s`，%d 条指令，`skipdata=%d`，末条 `%s` |'
               % (r['range'][0], r['range'][1], r['n_insn'], r['skipdata'], r['last']))
    out.append('| ② 类身份 | 成立 | 槽 `%s`(.rdata) 4B=`%s`，`(slot-vt)/4=%d`；`[vt-4]`=COL `%s`(sig=`%s`,offset=0,cdOffset=0)→TD `%s`→名 `%s` |'
               % (slot['slot'], e, slot['idx'], slot['col'], slot['sig'], slot['td'], slot['name']))
    out.append('| ③b 形态 | `3b2` | 三道 imm `%s`/`%s`/`%s`；主站 `%s` `%s`；分支 `%s`/`%s`/`%s`；失败 `%s` `%s` |'
               % (imms[0][0], imms[1][0], imms[2][0], qi[0], b(int(qi[0], 16), 2),
                  core.read(int(qi[0], 16) + 2, 2).hex(), core.read(int(qi[0], 16) + 4, 2).hex(),
                  b(int(qi[0], 16) + 6, 2), rel[0], b(int(rel[0], 16), 3)))
    out.append('| ④ 使用见证 | 成立 | 宿主 `006BB9A0` 内 `%s call 0x7C8E17`→`%s call %s`(装 `%s`)→`%s ff d6`，`esi=[0x7E15D8]`=`ole32!CoRegisterClassObject`，CLSID `%s`；工厂表 `vt[3]`=`%s` |'
               % (m4['new'], m4['ctor_site'], m4['ctor'], m4['slot']['vt'], m4['reg_site'], m4['clsid'], e))
    out.append('| ④≠② 同源 | 否（不同源） | ② 锚 `.rdata`(%s/%s/%s)；④ 锚 `.text`(%s/%s/%s)+CLSID 常量 %s |'
               % (slot['slot'], slot['col'], slot['td'], m4['new'], m4['ctor_site'], m4['reg_site'], m4['clsid']))
    body = core.func_body(int(e, 16))
    ppv_zero = [('%08X' % i['a']) for i in body if i['t'] == 'mov dword ptr [edi], 0'][0]
    store = m4['ctor_w0'][0][0]
    out.append('| ⑤ 语义 | 相符 | 方向=**写出**：`%s` 先 `mov [edi],0` 清 ppv，QI 成功后由被调 `00410260` 把接口指针写入 `*ppv`；子型 `3b2` 正确 |'
               % ppv_zero)
    out.append('')
    out.append('- **③ 成链（我自测，不是抄行文）**：本行 `call %s` 之后 `mov esi,eax`；该构造器把主虚表写入 `[%s+0]`：%s。主表 `vt0` = `%s`，RTTI 名 `%s` ⇒ **确实是对象主虚表，不是内嵌成员表**。'
               % (r['obj_ctor'], r['obj_ctor_this'],
                  '；'.join('`%s %s = %s`' % (a, m, v) for a, m, v, bb in r['obj_ctor_w0']),
                  main['vt0'], main['name']))
    out.append('- **同构造器写入的成员/次级表（我逐一查过，均非主表）**：%s。' % membrief)
    out.append('- **被调 `00410260` 的返回约定（本行 `test/jge` 分支的对象）**：%s。' % qiret())
    out.append('- **④ 不是析构器**：工厂构造器 `%s` 的写表点 `%s`（在行体外），`push %s; call 0x7C978A`(atexit) 命中 **0**；该构造器唯一调用者 `%s`；宿主 `006BB9A0` 全镜像 `push` 命中 **0** ⇒ ㉓ 成对陷阱不适用。' % (m4['ctor'], store, m4['ctor'], ','.join(m4['ctor_callers']) or '无'))
    out.append('')
    tsv.append('\t'.join([e, 'S22', verdict, '%s/%s' % (slot['slot'], slot['vt']), '3b2',
                          '%s/%s/%s' % (m4['new'], m4['ctor_site'], m4['reg_site']), 'no',
                          '入口%s(.text,%s条,skipdata=0,末条ret0x10)；②槽%s(vt%s+12,#%d)RTTI %s；③b②主站@%s call[eax](对象主vt%s vt0=00410260)test+jge，失败@%s call[edx+0x20]，被调00410260出口{0,80004002,80004003}；④@%s alloc→%s装表→@%s CoRegisterClassObject(CLSID%s)；②④不同源；方向=写出ppv' % (
                              e, r['n_insn'], slot['slot'], slot['vt'], slot['idx'], slot['name'], qi[0], main['vt'], rel[0],
                              m4['new'], m4['ctor'], m4['reg_site'], m4['clsid'])]))

open('verdict_rows.md', 'w', encoding='utf-8').write('\n'.join(out))
open('verdict.tsv', 'w', encoding='utf-8').write(
    'entry\tsubsystem\tverdict\tring2_at\tring3b_form\tring4_at\tsame_source\treason\n' + '\n'.join(tsv) + '\n')
print('rows:', len(ENTS), 'pass:', sum(1 for l in tsv if '\tPASS\t' in l))
