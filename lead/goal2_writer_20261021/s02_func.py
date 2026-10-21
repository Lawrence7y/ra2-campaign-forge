import importlib.util, os
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()

LO = 0x0054A400
HI = 0x0054A5A0
insns = pt.disasm_range(pe, md, LO, HI)
print(pt.fmt(insns, mark=(0x0054A56E, 0x0054A566, 0x0054A575)))
