
from capstone import *
m = Cs(CS_ARCH_X86, CS_MODE_32); m.detail=True; m.skipdata=True
tests = [
  bytes.fromhex('885E3F'),   # mov [esi+0x3f], bl
  bytes.fromhex('8A4A3F'),   # mov cl, [edx+0x3f]
  bytes.fromhex('803A00'),   # cmp byte [edx], 0
  bytes.fromhex('0158E5'),   # add [eax+0xe5], ebx
  bytes.fromhex('C6050004A80001'), # mov byte [0xA80400], 1
]
for t in tests:
  for i in m.disasm(t, 0x400000):
    print(i.mnemonic, i.op_str, [(o.access, o.size, o.type) for o in i.operands])
