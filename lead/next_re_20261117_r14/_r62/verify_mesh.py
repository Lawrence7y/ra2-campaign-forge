import io, os, json, struct

ROOT = r'D:\Project\ra2-campaign-forge'
ap = None
for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
    if 'mesh_imm32.json' in fs:
        ap = os.path.join(dp, 'mesh_imm32.json'); break
d = json.load(io.open(ap, encoding='utf-8', errors='replace'))

# 找 gamemd.exe
exe = None
for dp, _, fs in os.walk(ROOT):
    for f in fs:
        if f.lower() == 'gamemd.exe':
            exe = os.path.join(dp, f); break
    if exe: break
print('gamemd.exe:', exe.replace(ROOT + '\\', '') if exe else 'NOT FOUND')
if not exe:
    raise SystemExit

buf = io.open(exe, 'rb').read()
print('exe size:', len(buf))
# PE ImageBase
pe = struct.unpack_from('<I', buf, 0x3C)[0]
magic = struct.unpack_from('<H', buf, pe + 24)[0]
imgbase = struct.unpack_from('<I', buf, pe + 24 + 28)[0]
print('PE offset=%#x magic=%#x ImageBase=%#x' % (pe, magic, imgbase))

def at(va):
    off = va - imgbase
    if 0 <= off < len(buf):
        return buf[off:off + 8]
    return None

# 检查 imm['00407100'] 的前几个使用点
print()
print('=== imm["00407100"] 的使用点（十进制地址）可否回原址 ===')
for va in d['imm']['00407100'][:6]:
    b = at(va)
    print('  VA=%#010x  bytes=%s' % (va, b.hex(' ').upper() if b else 'OUT OF RANGE'))

print()
print('=== abs["007E1208"] 的使用点 ===')
for va in d['abs']['007E1208'][:6]:
    b = at(va)
    print('  VA=%#010x  bytes=%s' % (va, b.hex(' ').upper() if b else 'OUT OF RANGE'))

# 正控：抽 20 个随机使用点，看有多少在 exe 范围内
import random
random.seed(7)
allv = []
for k, lst in list(d['imm'].items())[:200]:
    allv += lst[:20]
for k, lst in list(d['abs'].items())[:200]:
    allv += lst[:20]
samp = random.sample(allv, min(20, len(allv)))
ok = sum(1 for va in samp if at(va) is not None)
print()
print('正控：抽 %d 个使用点，在 exe 范围内 %d 个' % (len(samp), ok))
