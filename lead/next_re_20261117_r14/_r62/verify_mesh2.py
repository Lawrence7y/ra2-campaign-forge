import io, os, json, struct, random

ROOT = r'D:\Project\ra2-campaign-forge'
EXE = os.path.join(ROOT, r'lead\next_re_20261117_r14\PATCH_D35R\work\run\gamemd.exe')
ap = None
for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
    if 'mesh_imm32.json' in fs:
        ap = os.path.join(dp, 'mesh_imm32.json'); break

buf = io.open(EXE, 'rb').read()
pe = struct.unpack_from('<I', buf, 0x3C)[0]
imgbase = struct.unpack_from('<I', buf, pe + 24 + 28)[0]
print('exe=%d B ; ImageBase=%#x' % (len(buf), imgbase))

def at(va):
    off = va - imgbase
    return buf[off:off + 8] if 0 <= off < len(buf) - 8 else None

d = json.load(io.open(ap, encoding='utf-8', errors='replace'))
print('imm keys=%d ; abs keys=%d' % (len(d['imm']), len(d['abs'])))

print()
print('=== imm["00407100"] 使用点逐字节 ===')
for va in d['imm']['00407100']:
    b = at(va)
    print('  VA=%#010x  %s' % (va, b.hex(' ').upper() if b else 'OUT'))

print()
print('=== abs["007E1208"] 前 5 个使用点 ===')
for va in d['abs']['007E1208'][:5]:
    b = at(va)
    print('  VA=%#010x  %s' % (va, b.hex(' ').upper() if b else 'OUT'))

# 正控：随机抽 50 个使用点
random.seed(11)
pool = []
for k, lst in list(d['imm'].items())[:500]:
    pool += lst[:10]
for k, lst in list(d['abs'].items())[:200]:
    pool += lst[:10]
samp = random.sample(pool, 50)
ok = sum(1 for va in samp if at(va) is not None)
print()
print('正控：抽 50 个使用点，在 exe 内可回原址 %d/50' % ok)

# 负控：抽 50 个明显不在 .text 的假地址
fake = [0x10000000 + i * 0x111 for i in range(50)]
okf = sum(1 for va in fake if at(va) is not None)
print('负控：50 个假地址（0x10000000+）在 exe 内 %d/50（应 0）' % okf)
