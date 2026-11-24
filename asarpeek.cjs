const fs = require('fs');
const ASAR = 'D:/DeepSeek/resources/app.asar';
const mode = process.argv[2] || 'list';
const target = process.argv[3] || '';
const fd = fs.openSync(ASAR, 'r');
const head = Buffer.alloc(16);
fs.readSync(fd, head, 0, 16, 0);
const headerSize = head.readUInt32LE(4);
const jsonLen = head.readUInt32LE(12);
const buf = Buffer.alloc(jsonLen);
fs.readSync(fd, buf, 0, jsonLen, 16);
const header = JSON.parse(buf.toString('utf8'));
const dataStart = 8 + headerSize;
function walk(n, p, o) {
  for (const k of Object.keys(n.files || {})) {
    const v = n.files[k];
    const q = p ? p + '/' + k : k;
    if (v.files) walk(v, q, o);
    else o.push({ p: q, size: v.size, offset: String(v.offset) });
  }
}
const all = [];
walk(header, '', all);
if (mode === 'list') {
  const re = new RegExp(target || '.');
  const hits = all.filter(f => re.test(f.p) && f.p.split('/').length <= 7);
  console.log('TOTAL=' + all.length + ' matched=' + hits.length);
  for (const h of hits.slice(0, 120)) console.log(h.p + '  ' + h.size);
} else if (mode === 'cat') {
  const f = all.find(x => x.p === target);
  if (!f) { console.log('NOT_FOUND'); process.exit(1); }
  const b = Buffer.alloc(f.size);
  fs.readSync(fd, b, 0, f.size, dataStart + Number(f.offset));
  process.stdout.write(b.toString('utf8'));
}
