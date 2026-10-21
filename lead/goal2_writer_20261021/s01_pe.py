import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
print('imagebase %08X entry %08X image size %08X' % (pe.image_base, pe.entry_rva + pe.image_base, pe.size_of_image))
print('text range %08X-%08X' % (pe.text_lo, pe.text_hi))
print(pe.dump_sections())
print('--- raw bytes at crash site ---')
print(pe.read(0x0054A540, 0x50).hex())
