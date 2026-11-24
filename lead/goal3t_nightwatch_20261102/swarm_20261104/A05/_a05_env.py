# A05 现场自证：覆盖率 + 主泵窗口反汇编
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==")
print(eng.coverage)
print()
print("== disasm 0x5D4D50 (0x200 bytes) ==")
for line in eng.disasm(0x5D4D50, 0x200):
    print(line)
