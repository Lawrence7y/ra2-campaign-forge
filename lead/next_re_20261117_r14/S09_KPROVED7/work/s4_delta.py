"""Build S09_KPROVED7 deliverables: coverage_delta.tsv + PROGRESS/UNKNOWNS/DISAGREE."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
EV = BASE + r'\S09_KPROVED7\EVIDENCE'
D = BASE + r'\S09_KPROVED7'
summ = json.load(open(OUT + r'\rings8.json', encoding='utf-8'))
by = {s['entry']: s for s in summ}
base = json.load(open(OUT + r'\baseline_3b.json', encoding='utf-8'))

# disk first-half (subsystem description) preserved verbatim; base-class name used per M1/16
# spec: entry, name(final), sem_core, tier
SPEC = [
 ('004E2580','GaugeClass::slot34','GaugeClass 虚表槽 34(+0x88)：UI/侧栏/菜单/对话框/输入 方法',
  '③b② 把入参与当前值[this+0x30]比较，仅当真变化才写回当前值并经虚方法[vptr+0x48]通知刷新、返回1，值未变则原样返回0——可证伪的写时变更布尔返回约定',
  '③b②','GaugeClass'),
 ('004E1530','GadgetClass::slot31','GadgetClass 虚表槽 31(+0x7C)：UI/侧栏/菜单/对话框/输入 方法',
  '③b② 入参非零则置位标志[this+0x1c]=1、携带入参调虚方法[vptr+0x78]通知并返回1，入参为零则原样返回0不做动作——可证伪的布尔返回加门控状态转移约定',
  '③b②','GadgetClass'),
 ('004E1550','GadgetClass::slot27','GadgetClass 虚表槽 27(+0x6C)：UI/侧栏/菜单/对话框/输入 方法',
  '③b② 入参非零或当前标志[this+0x1c]已置则清标志为0并返回1，两者皆否则原样返回0——可证伪的布尔返回加双闸或清除约定',
  '③b②','GadgetClass'),
 ('0048E5A0','ControlClass::slot31','ControlClass 虚表槽 31(+0x7C)：UI/侧栏/菜单/对话框/输入 方法',
  '③b① 把控件状态汇总成位掩码写入出参[edi]：子对象缺失写0、有效则置0x80、再按入参位0x40与[this+0x20]位0x10置0x40，随后若[this+0x28]存在则调其虚方法[vptr+0x4c]并调0x4e1530置标志——多道互斥闸动作各异(清0/置0x80/置0x40/两种相异调用)整体合同',
  '③b①','ControlClass'),
 ('004F4450','GScreenClass::slot13','GScreenClass 虚表槽 13(+0x34)：UI/侧栏/菜单/对话框/输入/命令派发 方法',
  '③b② 先经虚方法[this+0x2c]询问入参对象是否可登记，否则原样返回0；可登记则调该对象虚方法[+0x24]取值、缓存到全局[0xa8ef54]并返回1——可证伪的布尔返回加两段式虚分派约定',
  '③b②','GScreenClass'),
 ('00557AC0','ListClass::slot40','ListClass 虚表槽 40(+0xA0)：UI/侧栏/菜单/对话框/输入/命令派发 方法',
  '③b② 按索引取元素：空表直接返回0，否则把索引上钳到Count减一后返回Items[索引]——可证伪的边界钳制返回约定(空表闸加上界闸两道)',
  '③b②','ListClass'),
 ('004E19F0','GadgetClass::slot22','GadgetClass 虚表槽 22(+0x58)：UI/侧栏/菜单/对话框/输入 方法',
  '③b② 以恒等比较判定本控件是否为当前全局焦点控件[0x8b3e90]：相等返回1否则返回0——可证伪的焦点恒等谓词返回约定',
  '③b②','GadgetClass'),
 ('00557AE0','ListClass::slot39','ListClass 虚表槽 39(+0x9C)：UI/侧栏/菜单/对话框/输入/命令派发 方法',
  '③b② 返回当前选中项：当前索引小于Count时返回Items[索引]，否则返回0——可证伪的界内判定返回约定',
  '③b②','ListClass'),
]

# anchors per entry (entry-relative, must match DISASM files exactly)
ANCHOR = {
 '004E2580':'+0x04 mov edx,[ecx+0x30] 读当前值 / +0x07 cmp eax,edx / +0x09 je 未变出口 / +0x0B mov [ecx+0x30],eax 写 / +0x10 call [eax+0x48] 通知 / +0x13 mov eax,1 / +0x1B xor eax,eax',
 '004E1530':'+0x04 test eax,eax / +0x06 je 零出口 / +0x0B mov byte [ecx+0x1c],1 置位 / +0x0F call [edx+0x78] 通知 / +0x12 mov eax,1 / +0x1A xor eax,eax',
 '004E1550':'+0x04 test eax,eax / +0x06 jne 清除 / +0x0B test al,al 读当前标志 / +0x0D jne 清除 / +0x14 mov byte [ecx+0x1c],0 / +0x18 mov eax,1 / +0x0F xor eax,eax',
 '0048E5A0':'+0x0D test ebx / +0x14 test [esi+0x24] / +0x1B test bl,0x40 / +0x22 test byte [esi+0x20],0x10 / +0x18 or ah,0x80 / +0x28 or ah,0x40 / +0x2F mov [edi],0 / +0x41 call [eax+0x4c] / +0x4A call 0x4e1530',
 '004F4450':'+0x08 call [eax+0x2c] 询问 / +0x0B test al,al / +0x0D jne / +0x17 call [edx+0x24] 取值 / +0x1A mov [0xa8ef54],eax 缓存 / +0x1F mov al,1 / +0x10 ret 4 返回0',
 '00557AC0':'+0x03 test eax,eax 空表闸 / +0x05 jne / +0x07 ret 4 返回0 / +0x0E dec eax / +0x0F cmp edx,eax 上界闸 / +0x13 mov edx,eax 钳制 / +0x18 mov eax,[eax+edx*4] 取元素',
 '004E19F0':'+0x00 mov edx,[0x8b3e90] 读全局焦点 / +0x08 cmp ecx,edx 恒等比较 / +0x0A sete al 谓词 / +0x0D ret',
 '00557AE0':'+0x00 mov eax,[ecx+0x16c] 当前索引 / +0x06 mov edx,[ecx+0x44] Count / +0x09 cmp edx,eax 界内闸 / +0x0B jg / +0x0D xor eax,eax 返回0 / +0x13 mov eax,[ecx+eax*4] 取元素',
}

rows = ['entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path']
for entry, name, core, contract, tier, baseCls in SPEC:
    s = by[entry]
    holds = s['holds']
    cls_list = ';'.join(sorted(set(h['td8'].replace('.?AV','').replace('@@','') for h in holds)))
    vtslot = ';'.join('%s:slot%d' % (h['vt'], h['slot']) for h in holds)
    sites = s['direct']
    site_str = ','.join(x.replace('0x','') for x in sites[:6])
    if len(sites) > 6: site_str += '等%d处' % len(sites)
    sem = (core + '（' + contract +
           '；②全表枚举%d张同槽持有表(%s)按M1/⑯归共同基类%s、name栏同类；' % (len(holds), vtslot, baseCls) +
           '锚 ' + ANCHOR[entry] +
           '；④direct E8@%s(site+5+rel32==entry、E8@指令边界、体外、非自环)）' % site_str)
    grade = '[已证]'
    evp = ('EVIDENCE/VTABLES_ALL8.tsv;EVIDENCE/DIRECT_SITES_8.tsv;EVIDENCE/DISASM_%s.txt;' % entry +
           'EVIDENCE/ANCHOR_%s.txt' % entry)
    rows.append('\t'.join([entry,'S09',name,sem,grade,evp]))

open(D + r'\coverage_delta.tsv','w',encoding='utf-8').write('\n'.join(rows)+'\n')

# per-entry anchor evidence files (excerpt from DISASM for the anchor addresses)
for entry, name, core, contract, tier, baseCls in SPEC:
    s = by[entry]
    lines = open(EV + r'\DISASM_%s.txt' % entry, encoding='utf-8').read()
    open(EV + r'\ANCHOR_%s.txt' % entry,'w',encoding='utf-8').write(
        'S09-KPROVED7 anchor evidence entry=%s\n' % entry +
        'tier=%s final_name=%s base=%s\n' % (tier,name,baseCls) +
        '④ direct sites: %s\n' % ','.join(s['direct']) +
        '② holding tables: %d\n' % s['n_holds'] +
        '\n' + lines)

print('wrote coverage_delta.tsv rows=%d' % (len(rows)-1))
for r in rows[1:]:
    p=r.split('\t'); print(' ',p[0],p[2],'| sem len',len(p[3]))
