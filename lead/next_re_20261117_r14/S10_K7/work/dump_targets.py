from common import Image, EV
img=Image()
out=[]
for va in (0x006B7010,0x004E0E80):
    out.append(f"===== {va:08X} =====")
    out.append("bytes256: "+img.read(va,256).hex())
    for ins in img.disasm(va,0x300,maxins=160,stop_ret=False):
        out.append(img.fmt(ins))
        if ins.mnemonic.startswith("ret") or (ins.mnemonic=="jmp" and ins.op_str.startswith("0x")):
            break
    out.append("")
(EV/"target_disasm.txt").write_text("\n".join(out),encoding="utf-8")
print("\n".join(out))
