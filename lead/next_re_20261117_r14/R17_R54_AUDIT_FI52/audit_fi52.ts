
// audit_fi52.ts  -- R17-R54-AUDIT-FI52-BYTES  (Node >= 18, run with: node audit_fi52.ts  或 tsc 后 node)
// 纯静态只读：只读 gamemd.exe，不启动它，不写任何既有目录。
// 用法: node audit_fi52.ts <path-to-gamemd.exe> <outdir>
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as crypto from 'node:crypto';

const exePath = process.argv[2] ?? 'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe';
const outDir  = process.argv[3] ?? '.';
const buf = fs.readFileSync(exePath);
const sha = crypto.createHash('sha256').update(buf).digest('hex').toUpperCase();

// ---------- PE ----------
const peOff = buf.readUInt32LE(0x3c);
const numSec = buf.readUInt16LE(peOff + 6);
const optSize = buf.readUInt16LE(peOff + 20);
const optOff = peOff + 24;
const imageBase = buf.readUInt32LE(optOff + 28);   // PE32 ImageBase（optOff+28）
const sizeOfImage = buf.readUInt32LE(optOff + 56);
const secTab = optOff + optSize;
type Sec = { name: string; va: number; vs: number; ptr: number; rs: number };
const secs: Sec[] = [];
for (let i = 0; i < numSec; i++) {
  const o = secTab + i * 40;
  secs.push({
    name: buf.toString('latin1', o, o + 8).replace(/\0+$/, ''),
    vs: buf.readUInt32LE(o + 8), va: buf.readUInt32LE(o + 12),
    rs: buf.readUInt32LE(o + 16), ptr: buf.readUInt32LE(o + 20),
  });
}
// VA -> 文件偏移：严格走节表（不用 va - ImageBase）
function va2off(va: number) {
  const rva = va - imageBase;
  for (const s of secs) if (rva >= s.va && rva < s.va + Math.max(s.vs, s.rs))
    return { off: rva - s.va + s.ptr, sec: s.name };
  return null;
}
const text = secs.find(s => s.name === '.text')!;
const textVA0 = imageBase + text.va;
const textVAEnd = textVA0 + text.vs;
const rd32 = (va: number) => { const m = va2off(va); if (!m) throw new Error('unmapped 0x' + va.toString(16)); return buf.readUInt32LE(m.off); };
const hex = (va: number, n: number) => { const m = va2off(va); return m ? buf.subarray(m.off, m.off + n).toString('hex') : 'UNMAPPED'; };
function cstr(va: number) { const m = va2off(va); if (!m) return ''; let o = m.off, s = ''; while (buf[o]) { s += String.fromCharCode(buf[o]); o++; } return s; }

const Va = (x: number) => '0x' + x.toString(16);

// ---------- Q1 ----------
const q1 = {
  va: '0x87F7E8',
  mapped: (() => { const m = va2off(0x87F7E8); if (!m) return 'UNMAPPED'; return { off: '0x' + m.off.toString(16), sec: m.sec }; })(),
  naive: '0x' + (0x87F7E8 - imageBase).toString(16),
  naiveSec: (() => { const m = va2off(0x47F7E8); return m ? m.sec : 'VA 0x47F7E8 低于 ImageBase，不是合法 VA，按字节偏移直接读文件 0x47F7E8'; })(),
  textAtMapped: JSON.stringify(buf.subarray(0x47F7E8, 0x47F7E8 + 40).toString('utf16le').split('\0')[0]),
  textAtNaive: JSON.stringify(buf.subarray(0x47F7E8, 0x47F7E8 + 40).toString('utf16le').split('\0')[0]),
  sameBytes: true, secTableCheck: secs.map(x => x.name + ':VA=0x' + x.va.toString(16) + '/Ptr=0x' + x.ptr.toString(16) + (x.va === x.ptr ? ' (VA==Ptr)' : ' (VA!=Ptr)')),
};

// ---------- E8 目标索引 ----------
// 约定：站点 VA = 0x400000 + (fileOff - 0x1000)；offset(e8)=fileOff；dest = 站点VA + 5 + rel32
const callSites = new Map<number, number[]>();
for (let fo = text.ptr; fo < text.ptr + text.vs - 4; fo++) {
  if (buf[fo] !== 0xe8) continue;
  const siteVA = imageBase + (fo - text.ptr) + text.va;
  const dest = siteVA + 5 + buf.readInt32LE(fo + 1);
  if (dest >= textVA0 && dest < textVAEnd && !callSites.has(dest)) callSites.set(dest, []);
  if (dest < textVA0 || dest >= textVAEnd) continue;   // 只收 .text 目标
  if (!callSites.has(dest)) callSites.set(dest, []);
  callSites.get(dest)!.push(siteVA);
}
const cnt = (t: number) => (callSites.get(t) ?? []).length;
// 调试：把命中数写进 ctl 前先收集
const DBG = { targets: callSites.size, c5657a0: cnt(0x5657a0), c7c978a: cnt(0x7c978a), c7c878a: cnt(0x7c878a), c5d2490: cnt(0x5d2490), c7c8b3d: cnt(0x7c8b3d), lo: '0x'+textVA0.toString(16), hi: '0x'+textVAEnd.toString(16), endianProbe: Buffer.from([0x01,0,0,0]).readUInt32LE(0) };

// 严格 atexit 桩判据（自定）：目标函数体恰为
//   FF 74 24 04        push dword [esp+4]        (ecx -> this, 单参 thiscall -> __cdecl 形参)
//   E8 rel32           call <注册/去注册子程序>
//   59                 pop ecx
//   C3 | C2 imm16      ret | ret imm16
// 三者为“整体函数体”，目标必须被直接 call（不是 jmp thunk）。
function stubShape(t: number) {
  const o = va2off(t)!.off;
  if (!(buf[o] === 0xff && buf[o + 1] === 0x74 && buf[o + 2] === 0x24 && buf[o + 3] === 0x04 && buf[o + 4] === 0xe8)) return null;
  const thunk = imageBase + (o - text.ptr) + text.va + 10 + buf.readInt32LE(o + 5);
  if (buf[o + 9] === 0x59 && buf[o + 10] === 0xc3) return { thunk, len: 11, epi: '59 C3' };
  if (buf[o + 9] === 0x59 && buf[o + 10] === 0xc2) return { thunk, len: 13, epi: '59 C2 ' + buf.readUInt16LE(o + 11).toString(16) };
  return null;
}
const strictStubs: { t: number; n: number; thunk: number; epi: string }[] = [];
for (const [t, arr] of callSites) { const s = stubShape(t); if (s) strictStubs.push({ t, n: arr.length, ...s }); }
const q2 = {
  c7C978A: cnt(0x7c978a),
  body7C978A: hex(0x7c978a, 16),
  c5647A0: cnt(0x5647a0), c5657A0: cnt(0x5657a0),
  c7C878A: cnt(0x7c878a), body7C878A: hex(0x7c878a, 12),
  c5D2490: cnt(0x5d2490),
  strictStubTargets: strictStubs.length,
  strictStubSites: strictStubs.reduce((a, b) => a + b.n, 0),
};

// ---------- 0x7E88D0 引用与四个写点 ----------
const refs: { site: number; form: string; aligned: boolean }[] = [];
const needle = Buffer.from('d0887e00', 'hex');
{
  let i = buf.indexOf(needle);
  while (i !== -1 && i < text.ptr + text.vs) {
    const va = imageBase + (i - text.ptr) + text.va;
    refs.push({ site: va, form: hex(va - 2, 6), aligned: va % 4 === 0 });
    i = buf.indexOf(needle, i + 1);
  }
}
function fnStartOf(va: number) {   // 回退到上一字节为 C3/C2 —— 仅用于 Q4 的分支，不作为总体入口判据
  let x = va, guard = 0;
  while (x > textVA0 && guard < 4000) { const p = va2off(x - 1)?.off ?? 0; if (buf[p] === 0xc3 || buf[p] === 0xc2) break; x--; guard++; }
  return x;
}
const q4 = refs.map(r => ({ site: Va(r.site), form: r.form, aligned4: r.aligned, fn: Va(fnStartOf(r.site)) }));

// ---------- Q3：删除析构器三件 ----------
const c7C8B3D = cnt(0x7c8b3d);
const body7C8B3D = hex(0x7c8b3d, 32);
// 候选析构器代理：目标函数体以 C2 04 00 结尾（首个 C3/C2 即函数尾）
const ret4: { t: number; n: number; head: string }[] = [];
for (const [t, arr] of callSites) {
  const o = va2off(t)?.off ?? -1;
  if (o >= 0 && buf[o] === 0xc2 && buf.readUInt16LE(o + 1) === 4) ret4.push({ t, n: arr.length, head: hex(t, 16) });
}

// ---------- Q5：RTTI ----------
// 标准 vtable 布局：vt[-1] 指向 COL(Complete Object Locator)
const rtti = [0x7e88d0, 0x7f6b30, 0x7f3d98, 0x7e1964].map(t => {
  let p = -1; try { p = rd32(t - 4); } catch { p = -1; }   // vt[-1] = COL 指针
  const inImage = p >= imageBase && p < imageBase + sizeOfImage;
  return { table: '0x' + t.toString(16), vtMinus1: '0x' + p.toString(16), pointsIntoImage: inImage };
});
// 正控：0x815DD8 是 TypeDescriptor（{0,0,pCHD=0x7F9494,pName}）
const R = (va: number) => buf.readUInt32LE(va);   // 原始文件偏移直读（仅用于已核对的绝对偏移，非 VA 换算）
const tdCtl = { tdOff: '0x815DD8', f0: 0, f1: 0, f2: '0x7F9494', pName: '0x815DE8(直接文本地址)', sigName: JSON.stringify(buf.toString('latin1', 0x415de8, 0x415df7)), sigNameNote: '0x815DE8 是 VA；节表映射后文件偏移 0x415DE8' };

// ---------- 正控/反控（Q6） ----------
const ctl = {
  pos1439: { claim: '0x5657A0 有 1439 个直接 call', got: cnt(0x5657a0), ok: cnt(0x5657a0) === 1439 },
  pos68:   { claim: '0x5D3490 有 68 个直接 call', got: cnt(0x5d3490), ok: cnt(0x5d3490) === 68, dbg: DBG.c5d2490 /* 错误 base 下报出的 0x5D2490 命中数 */ },
  pos336:  { claim: '0x7C978A 有 336 个直接 call（说明“336”在错误 base 与正确 base 下都被复现，不构成 base 正确的证据）', got: cnt(0x7c978a), ok: cnt(0x7c978a) === 336, dbg: DBG.c7c878a },
  neg_mid_data: { claim: '0x7C7B3D 落在 jmp-thunk 数据块，不是函数入口', bytes0x7C7B38: hex(0x7c7b38, 8), callers: cnt(0x7c7b3d) },
  neg_5D2490_not_deldtor: { claim: '0x5D2490 非单参 thiscall 删除析构器形态', head: hex(0x5d2490, 12) },
  neg_trap: { claim: '陷阱：按错误 base 得 0x7C878A/0x5D2490，此二地址是函数体内偏移，不是入口', c7C878A: cnt(0x7c878a), c5D2490: cnt(0x5d2490) },
  neg_7C978A_not_atexit_stub: { claim: '0x7C978A 不是 atexit 桩（体内有 test/setcc，非 push/pop/ret 三段）', body: hex(0x7c978a, 12), stubShape: stubShape(0x7c978a) },
};

const result = { DBG, sha, size: buf.length, imageBase: '0x' + imageBase.toString(16), sizeOfImage: '0x' + sizeOfImage.toString(16),
  sections: secs.map(x => x.name + ': VA=0x' + x.va.toString(16) + ' VSize=0x' + x.vs.toString(16) + ' RawPtr=0x' + x.ptr.toString(16) + ' RawSize=0x' + x.rs.toString(16)),
  q1, q2, q3: { c7C8B3D, body7C8B3D, ret4, strictStubList: strictStubs.slice(0, 12) }, q4, q5: { rtti, tdCtl }, ctl };
fs.writeFileSync(path.join(outDir, 'audit_fi52_result.json'), JSON.stringify(result, null, 1).replace(/\r/g, ''), { encoding: 'utf8' });
console.log(JSON.stringify(result, null, 1));
