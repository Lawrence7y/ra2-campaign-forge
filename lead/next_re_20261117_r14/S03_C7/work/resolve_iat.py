import common as C
# Resolve key IAT addresses used in our functions
iats = [0x7e11e0, 0x7e1200, 0x7e1128, 0x7e1124, 0x7e11a0, 0x7e1208, 0x7e120c, 0x7e1300]
print("=== IAT resolution ===")
pe = C._pe
if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
    for imp in pe.DIRECTORY_ENTRY_IMPORT:
        dll = imp.dll.decode('latin-1')
        for ent in imp.imports:
            if ent.address in iats:
                print(f"  0x{ent.address:08X} -> {dll}!{ent.name.decode('latin-1') if isinstance(ent.name,bytes) else ent.name}")
print("\n=== direct-call target function heads (context) ===")
for t in [0x431f10, 0x431f70, 0x4325a0, 0x4325c0, 0x4325c0, 0x43ad00, 0x5b4430, 0x65cdd0, 0x65cf00, 0x65cce0, 0x431dd0, 0x65cca0, 0x7e11a0]:
    try:
        b = C.bytes_at(t, 16).hex()
    except Exception as e:
        b = 'ERR ' + str(e)
    print(f"  0x{t:08X}: {b}")
