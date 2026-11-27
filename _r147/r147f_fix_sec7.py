#!/usr/bin/env python3
"""R147 F：更正 R144 §七/§八① 的「0x7E6060 未找到装表站点」（R146 下轮待办 #1）。

被更正的原句（R14_COMMON §2.149，两处）：
  §七  「它只是**没有找到装表站点**（可能作为次虚表被基址+常量偏移访问），不是假表。」
  §八① 「`0x7E6060` 的装表位置未定位（它可能是「只被基址+常量偏移读取」的次虚表）」

已由 r147 一手字节证伪（三条独立事实）：
  F-a 装表站点在 0x4A8660，形态是 `mov dword ptr [eax - 8], 0x7e6060` —— 这正是
      R145 定位的「负位移」形态；R144 的解析器（r143lib.norm 的空白压缩字符类
      [+,*] 不含 '-'）整类丢弃 [reg - N]，所以「未找到」是解析器缺陷的产物。
  F-b 该站点属于一个**静态数组初始化循环**：入口块
      `0x4A8630 mov eax,0x8a0368 / mov edx,5 / xor ecx,ecx`，
      循环体 0x4A863C..0x4A866B，步长 `add eax,0x18`，`dec edx / jne` 共 5 个元素，
      每个元素依次写三张虚表：`[eax-8]=0x7e192c` → `[eax-8]=0x7e4f64` → `[eax-8]=0x7e6060`
      （最后一次写覆盖前两次，即派生类 vptr 最后落位），再 `[eax+0xc]=0xa`、`[eax+8]=ecx`。
      数组基址 0x8A0360 在 .data，静态内容全 0 ⇒ 运行期由该循环填充。
  F-c 0x7E6060 的 RTTI 完整：COL=0x7FFC28（locator=0/offset=0）、TD=0x816B10 名
      `.?AVLayerClass@@`、前 8 槽 8/8 落 .text
      （0x4AEB50/0x40CCD0/0x40CE50/0x40CC70/0x40CF00/0x40CCA0/0x40CCC0/0x5519B0）。

写法纪律（S-327 教训）：
  * 备份用 wx 独占创建，路径含唯一时间戳，存在即失败；
  * 写入前断言「旧文本必须存在且只出现一次」（幂等前置断言，重跑直接失败而非静默追加）；
  * 写入后回读校验：新 sha、CR 计数、旧串出现 0 次、新串出现 1 次；
  * 只改这两处，不动其它任何字节。
"""
import io, os, re, sys, json, time, hashlib

HERE = '/home/t628/projects/ra2-campaign-forge'
DOC = HERE + '/lead/next_re_20261117_r14/R14_COMMON.md'
BAK = HERE + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'

OLD7 = ('它只是**没有找到装表站点**（可能作为次虚表被基址+常量偏移访问），不是假表。')
NEW7 = ('~~它只是**没有找到装表站点**（可能作为次虚表被基址+常量偏移访问），不是假表。~~'
        '**【R147 更正·已找到装表站点，原文为解析器缺陷产物】** 装表站点在 **`0x4A8660`**，'
        '形态 `mov dword ptr [eax - 8], 0x7e6060`（**负位移**）。R144 当时用 '
        '`r143lib.norm` 归一，其空白压缩字符类 `[+,*]` 不含 `-`，capstone 打印的 '
        '`[eax - 8]` 带空格 ⇒ `RE_STORE` 整类拒收负位移写入，故「未找到」。'
        '该站点是一个**静态数组初始化循环**：`0x4A8630 mov eax,0x8A0368` / `mov edx,5` / '
        '`xor ecx,ecx`，循环体 `0x4A863C..0x4A866B`，步长 `add eax,0x18`，共 **5** 个元素；'
        '每元素依次写三张虚表 `[eax-8]=0x7E192C` → `0x7E4F64` → `0x7E6060`（后者最后落位），'
        '再 `[eax+0xC]=0xA`、`[eax+8]=ecx`。数组基址 `0x8A0360` 在 `.data`，静态内容全 0 '
        '⇒ 运行期由该循环填充（R147 实测）。')

OLD8 = ('① `0x7E6060` 的装表位置未定位（它可能是「只被基址+常量偏移读取」的次虚表）；')
NEW8 = ('① ~~`0x7E6060` 的装表位置未定位（它可能是「只被基址+常量偏移读取」的次虚表）~~ '
        '**已定位（R147）**：`0x4A8660`，负位移 `mov dword ptr [eax - 8],0x7E6060`，'
        '属 `0x4A8630` 起、基址 `0x8A0368`、步长 `0x18`、5 元素的静态数组初始化循环；')

def read():
    return io.open(DOC, encoding='utf-8', newline='').read()

def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def cr(s):
    return s.count('\r')

def backup(path, tag):
    ts = time.strftime('%Y%m%d_%H%M%S')
    p = os.path.join(BAK, 'R14_COMMON.md.before_r147f_%s_%s.bak' % (tag, ts))
    with open(p, 'x', encoding='utf-8', newline='') as f:     # 'x' = wx 独占
        f.write(read())
    return p

checks = []
def ck(n, c, got, want):
    checks.append({'name': n, 'ok': bool(c), 'got': got, 'want': want})

s0 = read()
h0 = sha(s0); cr0 = cr(s0); n0 = len(s0.encode('utf-8'))

ck('前置 CR == 1081', cr0 == 1081, cr0, 1081)
ck('前置 旧§七串出现恰 1 次（幂等前置断言）', s0.count(OLD7) == 1, s0.count(OLD7), 1)
ck('前置 旧§八串出现恰 1 次（幂等前置断言）', s0.count(OLD8) == 1, s0.count(OLD8), 1)
ck('前置 新§七串尚未出现（防重复追加）', '【R147 更正·已找到装表站点' not in s0,
   '【R147 更正·已找到装表站点' in s0, False)
ck('前置 新§八串尚未出现（防重复追加）', '**已定位（R147）**' not in s0,
   '**已定位（R147）**' in s0, False)

if any(not c['ok'] for c in checks):
    print(json.dumps({'aborted': 'precheck failed', 'checks': checks}, ensure_ascii=False, indent=1))
    sys.exit(2)

b1 = backup(DOC, 'sec7')
s1 = s0.replace(OLD7, NEW7, 1)
b2 = backup(DOC, 'sec8')
s2 = s1.replace(OLD8, NEW8, 1)

with io.open(DOC, 'w', encoding='utf-8', newline='') as f:
    f.write(s2)

s3 = read()
# S-335：旧§七串被**有意**保留在删除线 ~~...~~ 内（便于对照原文），因此计数仍为 1。
# 正确的断言是「它只以删除线形态存在、且没有第二次出现」，不是「消失」。
ck('回读 旧§七串仅在删除线内出现 1 次（不被误判为未改）',
   s3.count(OLD7) == 1 and s3.count('~~' + OLD7 + '~~') == 1,
   [s3.count(OLD7), s3.count('~~' + OLD7 + '~~')], [1, 1])
ck('回读 旧§八串消失', s3.count(OLD8) == 0, s3.count(OLD8), 0)
ck('回读 新§七串出现恰 1 次', s3.count('【R147 更正·已找到装表站点') == 1,
   s3.count('【R147 更正·已找到装表站点'), 1)
ck('回读 旧§八串亦仅在删除线内', s3.count('~~' + OLD8 + '~~') == 1,
   s3.count('~~' + OLD8 + '~~'), 1)
ck('回读 新§八串出现恰 1 次', s3.count('**已定位（R147）**') == 1,
   s3.count('**已定位（R147）**'), 1)
ck('回读 CR 仍为 1081', cr(s3) == 1081, cr(s3), 1081)
ck('回读 字节数增加量 == 两处替换净增', len(s3.encode('utf-8')) - n0
   == (len(NEW7.encode()) - len(OLD7.encode())) + (len(NEW8.encode()) - len(OLD8.encode())),
   len(s3.encode('utf-8')) - n0,
   (len(NEW7.encode()) - len(OLD7.encode())) + (len(NEW8.encode()) - len(OLD8.encode())))
ck('回读 §2.149 仍出现恰 1 次', s3.count('## 2.149') == 1, s3.count('## 2.149'), 1)
ck('回读 §2.150 段数未受影响', s3.count('## 2.150') == 1, s3.count('## 2.150'), 1)

out = {'checks': checks, 'fails': [c['name'] for c in checks if not c['ok']],
       'old_sha': h0, 'new_sha': sha(s3), 'old_bytes': n0,
       'new_bytes': len(s3.encode('utf-8')), 'cr': cr(s3),
       'backup1': os.path.basename(b1), 'backup2': os.path.basename(b2)}
json.dump(out, open(HERE + '/_r147/r147f_fix_sec7.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
