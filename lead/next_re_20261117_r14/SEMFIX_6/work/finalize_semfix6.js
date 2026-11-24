const fs = require('node:fs');
const path = require('node:path');
const base = String.raw`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_6`;
const src = String.raw`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv`;
const ev = path.join(base, 'EVIDENCE');

const semantics = {
  '0040F0A0': 'DynamicVector<VoxClass*> 容量设置 vslot2：0x40F0C2 按需分配新缓冲，0x40F0EE..0x40F0FC 以读 [edx+eax*4-4]→写 [edi+eax*4-4]→inc eax→jl 回边完成逐元素搬迁，0x40F109 释放旧块，0x40F11A/0x40F122 回写 [+0x4]/[+0x8] 并用 +0xC/+0xD 标记分配归属；③b④ 完整循环 I/O + ③b③ 内存形状。',
  '0040F150': 'DynamicVector<VoxClass*> 查找 vslot4：以 [ecx+0x10] 为有效长度、[ecx+0x4] 为指针数组，0x40F163 cmp [ecx],esi 比较目标、0x40F167 inc eax 与 0x40F168 add ecx,4 推进，0x40F16B/0x40F16D 边界回边；命中返回索引，未命中 0x40F16F or eax,-1 形成可证伪 -1 约定；③b② 错误码/返回约定 + ③b④ 完整循环 I/O。',
  '00417FE0': 'AircraftClass::vslot132 按 [esi+0xBC] 的状态枚举做 10 路互斥分派：0x417FF1 取索引、0x417FF7 cmp eax,0xA 与 0x417FF9 ja 0x418D1D 构成越界守卫，0x417FFF jmp dword[eax*4+0x418D58] 跳表；10 个槽目标同落 .text，越界走默认数值计算分支；③b① 跳表多路分支可逐路核。',
  '0041A5C0': 'AircraftClass::vslot135 对目标与自身状态作复合守卫决策并给出互斥结果：0x41A5CF 取 [esi+0x6C4] 对象 vt[+0xBC] 值，0x41A5DB 取本对象 vt[+0x1C8] 结果，0x41A5E1 cmp/0x41A5E3 jne 决定首层分岔；随后 vt[+0x2AC]/[+0x528]/[+0x3C8] 谓词、0x41A6E6 cmp ecx,-1 与 RNG 0x65AE30/0x65AD30 交织成互斥结局；③b① 多路守卫链可核。',
  '0041FB10': 'AITriggerTypeClass::LoadFromINI 解析并格式化 AI 触发器类型：0x41FB51 读 [esi+0xA0] 拥有方类别，0x41FB57/0x41FB5A dec+je/jne 将 1/2/其它三路映射到 <all> 或 0x818118；0x41FB65 读 [esi+0xA8] house 索引，0x41FB6B cmp -1 排除哨兵，0x41FB70..0x41FB79 从 0xA83C9C 数组取 HouseType 并 +0x24；0x41FBA3/0x41FC64 格式化、0x41FC85 登记；③b① 三路分派 + ③b② -1 哨兵可证伪。',
  '0044ACF0': 'BuildingClass::vslot132 依虚拟查询返回的状态码分发建筑处理：0x44B0C6 调 vt[+0x3C0]、0x44B0CC 取 eax 为 edi，0x44B0CE cmp edi,0xA 与 0x44B0D1 ja 0x44B14E 完成越界守护，0x44B0D7 jmp dword[edi*4+0x44B728] 进入 11 槽跳表；各槽目标均落 .text 且部分共用 0x44B0DE/0x44B14E 终点；③b① 跳表多路分支可逐路核。'
};
const order = Object.keys(semantics);
const srcLines = fs.readFileSync(src, 'utf8').split(/\r?\n/);
const srcByEntry = new Map();
for (const line of srcLines.slice(1)) {
  const f = line.split('\t');
  if (f.length >= 5) srcByEntry.set(f[0].toUpperCase(), f);
}
const banned = ['[静态推断]', '[未证]', '槽语义未证', 'rtti-vftable'];
const rows = [];
const zero = [];
const offsets = [];
const md = ['# SEMFIX-6 D-42 ③b 语义补写', ''];
let allOk = true;
for (const entry of order) {
  const srow = srcByEntry.get(entry);
  if (!srow) throw new Error('source row missing: ' + entry);
  const sem = semantics[entry];
  const len = sem.length;
  const bad = banned.filter(b => sem.includes(b));
  const disasmPath = path.join(ev, 'DISASM_FULL_' + entry + '.txt');
  const tablePath = path.join(ev, 'JUMP_TARGETS_' + entry + '.txt');
  const bodies = [disasmPath, tablePath].filter(p => fs.existsSync(p)).map(p => ({p, t: fs.readFileSync(p, 'utf8').toUpperCase()}));
  const toks = [...new Set([...sem.matchAll(/0x[0-9a-fA-F]{6,}/g)].map(m => m[0].toUpperCase()))];
  const miss = [];
  for (const tok of toks) {
    const addr = tok.slice(2);
    let hit = null;
    for (const b of bodies) {
      if (b.t.includes(tok) || b.t.includes(addr) || new RegExp('^' + addr + '\\s', 'm').test(b.t)) { hit = path.relative(base, b.p).replace(/\\/g, '/'); break; }
    }
    offsets.push([entry, tok, hit || 'MISS', hit ? 'OK' : 'FAIL'].join('\t'));
    if (!hit) miss.push(tok);
  }
  const ok = len >= 80 && bad.length === 0 && miss.length === 0 && srow[4] === '[已证]';
  if (!ok) allOk = false;
  rows.push([
    entry, srow[1], srow[2], sem, srow[4],
    'EVIDENCE/DISASM_FULL_' + entry + '.txt',
    /vslot/i.test(srow[2]) ? 'rtti-slot' : 'symbolic',
    '[已证]→[已证]'
  ].join('\t'));
  zero.push([entry, srow[1], srow[2], srow[4], srow[1], srow[2], srow[4], ok ? 'MATCH' : 'MISMATCH'].join('\t'));
  md.push('## ' + entry);
  md.push('- chars=' + len + '；grade=' + srow[4] + '；name=' + srow[2]);
  md.push('- ' + sem);
  md.push('- offsets=' + toks.join(' ') + '；missing=' + (miss.join(' ') || 'none'));
  md.push('');
}
fs.writeFileSync(path.join(base, 'coverage_delta.tsv'), 'entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\t旧grade→新grade\n' + rows.join('\n') + '\n', 'utf8');
fs.writeFileSync(path.join(ev, 'D42_SEMANTICS.md'), md.join('\n'), 'utf8');
fs.writeFileSync(path.join(ev, 'OFFSET_HITS.tsv'), 'entry\toffset\tevidence\tverdict\n' + offsets.join('\n') + '\n', 'utf8');
fs.writeFileSync(path.join(ev, 'GRADE_NAME_ZERO_CHANGE.tsv'), 'entry\tsrc_subsystem\tsrc_name\tsrc_grade\tdelta_subsystem\tdelta_name\tdelta_grade\tverdict\n' + zero.join('\n') + '\n', 'utf8');
const result = {rows: rows.length, allOk, charCounts: Object.fromEntries(order.map(e => [e, semantics[e].length])), offsetChecks: offsets.length, offsetMisses: offsets.filter(l => l.endsWith('FAIL')).length, zeroChange: zero.every(l => l.endsWith('MATCH'))};
fs.writeFileSync(path.join(base, 'work', 'verification.json'), JSON.stringify(result, null, 2), 'utf8');
console.log(JSON.stringify(result, null, 2));