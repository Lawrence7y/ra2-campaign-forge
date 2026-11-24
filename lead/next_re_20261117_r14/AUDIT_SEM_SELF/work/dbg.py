
import importlib.util
spec = importlib.util.spec_from_file_location('eng', r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\engine.py')
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
import capstone
body = eng.extent(0x6f9e50)
print('n', len(body))
n=0
for i in body:
    if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
        ops=i.operands
        print(hex(i.address), i.mnemonic, i.op_str, 'ops=', [(o.type, getattr(o,'imm',None)) for o in ops])
        n+=1
        if n>8: break
