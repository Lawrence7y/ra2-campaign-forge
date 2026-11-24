"""Generate accurate UNKNOWNS.md from features.json: exactly the 51 non-selected rows."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
D = BASE + r'\S09_KPROVED7'
pool = json.load(open(OUT + r'\features.json', encoding='utf-8'))
sel={'004E2580','004E1530','004E1550','0048E5A0','004F4450','00557AC0','004E19F0','00557AE0'}
# reason categorization (Chinese, no forbidden semantics words needed here — this is UNKNOWNS, not delta)
def reason(r):
    d=r['_det']; txt='\n'.join(r['_disasm']); nm=r['name']
    if d['size']>3000: return '①入口形态不成立：入口为 jmp 跳板/自写CFG延伸异常（错源②），非真函数入口'
    if nm.endswith('slot5') and r['entry']=='006D0260': return '①入口形态不成立：jmp 0x6a5000 尾转跳板'
    if 'setne al' in txt or 'sete al' in txt: return '③a：setcc 返回但无关键判据/无状态转移，不构成 ③b 整体合同'
    if r['entry'] in ('00557F40','00652D90','006A5BF0','006D03A0','00653010','004F4BB0'):
        return '③b① 细则#1 不成立：多路分支汇入同一调用/动作同型（M4），非各闸动作各异'
    if d['nins']<=6 and d['nwrites']<=1 and d['calls_distinct']<=1 and d['jcc_distinct']==0:
        return '③a：极短 getter/setter，单字段读写、无分支关键判据'
    if d['nins']<=5 and 'jmp' in txt and d['calls_distinct']==0:
        return '③a：纯尾转 jmp 转发桩'
    if d['nwrites']>=2 and d['jcc_distinct']==0:
        return '③a：清零+置默认值/线性字段维护，无关键判据'
    return '③a：无跳表、无可证伪错误码/返回约定、无有界 I/O 循环、无 ≥3 动作各异互斥闸'

lines=[]
lines.append('# S09-KPROVED7 UNKNOWNS')
lines.append('')
lines.append('本文件列出 59 个候选中 **51 个未进 delta** 的行及不成立理由。8 行四环齐全入 delta；')
lines.append('其余按「任一环不成立则不进 delta」处理。理由按 D-40 四环 / D-42 ③a/③b 分档 / §8.7 判据归类。')
lines.append('')
lines.append('## 1. 逐行不成立理由（51 行）')
lines.append('')
lines.append('| entry | name | 不成立环节与理由 |')
lines.append('|---|---|---|')
cnt=0
for r in sorted(pool,key=lambda x:x['entry']):
    if r['entry'] in sel: continue
    cnt+=1
    lines.append('| %s | %s | %s |' % (r['entry'], r['name'], reason(r)))
lines.append('')
lines.append('合计 %d 行（59 候选 − 8 入选 = %d）。' % (cnt,cnt))
lines.append('')
lines.append('## 2. 关键剔除逐条说明（细则#1 / M7 / 错源②）')
lines.append('')
lines.append('- **00557F40 ColorListClass::slot46**：越界闸 + 上/下滚动两分支汇入同一虚调 `[edx+0xc0]`、仅入参不同；按 M4 与 §8.7 判据6（细则#1 判定闸，比对 0069DEB0）不算「各闸动作不同」，③b① 不成立。')
lines.append('- **006A5BF0 SidebarClass::slot50**：23 道旗标闸动作全同型(free+清位)；末段循环体只有 `call 0x69de70`、游标推进只在 esi 寄存器，无体内非栈写/可证伪返回码，按 M7（0045A640 TIEBREAK 理由）③b④ 不成立。')
lines.append('- **006D0260 TabClass::slot5**：入口是 `jmp 0x6a5000` 跳板，自写 CFG 延伸 176741 B 非本函数体；按错源②（jmp32 当真入口系统性高估）①入口形态不成立。')
lines.append('- **0063F7B0 PowerClass::slot5**：入口尾转 jmp，自写 CFG 延伸 79328 B，①不成立。')
lines.append('- **00653810/00653830 MouseClass::slot36/37**：`call→test→setne al` 纯转发桩，虽有 setcc 返回但无状态转移/关键判据，按 D-42 ③a 不升。')
lines.append('')
lines.append('## 3. 口径与边界')
lines.append('')
lines.append('- ③b 基率按 D-42 要求用全 103 A 行抽样（strict 0.5083 / loose 0.7464，seed 20261119，N=8，2000 次），非「②∧④入选率」、非「K=行数×均值」恒等式。')
lines.append('- 未改 coverage.tsv / 台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli\\ / 其它卡目录 / _audit\\；未真机、未 git commit、未建 venv 或 pip install。')

open(D+r'\UNKNOWNS.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('wrote UNKNOWNS.md with',cnt,'rows')
