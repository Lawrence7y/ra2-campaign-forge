import json

syms = json.load(open('out/reverse/symbols.json'))
targets = [
    0x0075AEC0, 0x005B01C0, 0x004DE710, 0x00577C90, 
    0x004A9CA0, 0x00508F60, 0x0050BD10, 0x006CC390, 
    0x006CD70C, 0x005678E0, 0x00567F70, 0x004555D0,
    0x004556D0, 0x00455820, 0x00455980, 0x00455A80
]
for f in syms.get('functions', []):
    a = int(f['address'], 16)
    if a in targets:
        print(f"Func 0x{a:08X}: {f.get('name')}")
for cname, cinfo in syms.get('classes', {}).items():
    vf = cinfo.get('vfuncs', [])
    for i, v in enumerate(vf):
        if v:
            va = int(v, 16)
            if va in targets:
                print(f"VFunc {cname}::v[{i}] (+0x{i*4:03X}) = 0x{va:08X}")
