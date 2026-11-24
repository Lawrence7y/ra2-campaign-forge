# -*- coding: utf-8 -*-
# P01 v0 现场自证：coverage + SHA + 无 gamemd 进程
import subprocess, sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
cov = eng.coverage
print("coverage = %.2f%% / %d insns / resync=%d" % cov)
print("image sha256 =", eng.sha)
print(".text  = [%X, %X) fileoff=%X size=%X" % (eng.TLO, eng.THI, eng.TB, eng.TSZ))

out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq gamemd.exe"],
                     capture_output=True).stdout.decode("gbk", "replace")
print("tasklist gamemd:", out.strip().replace("\n", " | "))

# 基线锚点 sanity
print("u32(0xA8B230) const in image =", hex(eng.u32(0xA8B230)))
print("u32(0x7E11F0) const in image =", hex(eng.u32(0x7E11F0)))
print("iat(0x7E11F0) =", eng.resolve_iat(0x7E11F0))
print("iat(0x7E1530) =", eng.resolve_iat(0x7E1530))
