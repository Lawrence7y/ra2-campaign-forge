
import importlib.util
spec = importlib.util.spec_from_file_location('eng', r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\engine.py')
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
print('entries loaded', len(eng._ENT))
for a in (0x6bb9a0, 0x653100, 0x6f9e50, 0x417fe0, 0x4f54a0):
    f,_ = eng.analyze(a)
    print(hex(a),'n=',f['n_instr'],'span=',f['span'],'jcc=',f['jcc'],'loops=',f['loop_count'],'jt=',f['n_jmp_table'],'calls=',f['n_call'])
