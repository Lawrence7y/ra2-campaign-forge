#!/usr/bin/env python3
"""Write coverage_delta.tsv with real TAB separators. Only the 7 four-ring-complete rows.
one_line_semantics are rewritten from bytes (NOT copied from direct-call delta old column)."""
rows = [
 ('0065CAC0','S03','RawFileClass::slot2',
  '[已证] RawFile 重开：句柄+open 标志同时置位才 fclose 并清零两字段；filename 为 NULL 静默返回 0，fopen 失败经虚错误报告器(vptr+0x40)返回 0，否则置 open 标志返回新句柄。','[已证]'),
 ('004324B0','S03','CDFileClass::vslot10',
  '[已证] CDFile seek：未 open 则委托 RawFile；origin 0/1/2 三路分别写 pos=0/保持/size，按前缀基址调整并夹到 [0,size]，再按缓冲窗决定只改窗内索引还是冲刷重读。','[已证]'),
 ('00552490','S03','LCWStraw::slot2',
  '[已证] LCWStraw read(buffer,count)：buffer 空或 count<1 返回 0；循环取 min(count,剩余已解码) 用 memmove 写入并推进三指针，剩余耗尽则按 codec 读并校验 4 字节 LCW 头、解压或读长度字原始拷贝，回跳至 count 用尽。','[已证]'),
 ('006C9890','S03','FileStraw::slot1',
  '[已证] FileStraw 换绑 pipe：新 pipe 与当前相同则幂等返回；否则按两级 NULL 闸虚解绑新 pipe 旧 straw、清旧 pipe 回指，最后双向绑定 this↔pipe。','[已证]'),
 ('00631CC0','S03','FilePipe::slot3',
  '[已证] FilePipe 换绑 straw（与 slot1 对称）：幂等闸后经 pipe vt+0xC 虚解绑、清旧回指、对旧 straw 补一次 vt+4 虚通知，再双向绑定 straw↔pipe。','[已证]'),
 ('0065D150','S03','CDFileClass::slot3',
  '[已证] CDFile 复位/回绕：先虚 close 再虚 seek-to-end(origin=2)；结果为 0 返回 false，否则缓存字段非 -1 时虚复位缓冲窗、再 close 后返回 true。','[已证]'),
 ('00431E80','S03','BufferIOFileClass::vslot2',
  '[已证] BufferIOFile 确保以指定名打开：当前名为 NULL 或未 open 直接重开；否则逐字节 strcmp，相等返回当前名，不等则 close 后以新名 RawFile Open 再返回名字。','[已证]'),
]
base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C4"
with open(base + r"\coverage_delta.tsv", 'w', encoding='utf-8', newline='') as f:
    f.write('entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n')
    for e,sub,name,sem,grade in rows:
        ev = f'EVIDENCE/THREE_B_DETERMINATION.md#{e}'
        f.write('\t'.join([e,sub,name,sem,grade,ev]) + '\n')
# verify (ASCII-safe print: console is GBK)
with open(base + r"\coverage_delta.tsv", encoding='utf-8') as f:
    content = f.read()
for line in content.rstrip('\n').split('\n'):
    print(line.split('\t')[0], 'tabs=', line.count('\t'))
