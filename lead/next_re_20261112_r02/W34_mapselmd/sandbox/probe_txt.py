import importlib.util,sys
spec=importlib.util.spec_from_file_location("s3",r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W34_mapselmd\EVIDENCE\step3_disasm_stage.py")
m=importlib.util.module_from_spec(spec); sys.modules["s3"]=m; spec.loader.exec_module(m)
rows=m.disasm(0x005CEEF0,0x005CF0E0)
for a,b,mm,o,n in rows:
    if a in (0x005CEFD3,0x005CEFE7,0x005CF042,0x005CF045,0x005CF04B):
        print(f"0x{a:08X} |{mm}| |{o}|")
