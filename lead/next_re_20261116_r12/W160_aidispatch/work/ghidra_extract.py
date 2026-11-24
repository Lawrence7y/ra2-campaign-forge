import re,os
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE\W160_Ghidra_gather.log"
t=open(p,encoding='utf-8',errors='replace').read()
for pat in [r'XREF_TO_SUM.*',r'FUNC_AT.*',r'WORD .*',r'INSTR_TOTAL.*',r'CALL_5C_TOTAL.*',r'CALL_5C_FUNCS.*',r'DECOMP .*',r'DECOMP_FAIL.*']:
    for m in re.findall(pat,t): print(m)
print('\n=== decomp 55AFB0 first 260 lines ===')
s=t.find('=== DECOMP 0055AFB0')
e=t.find('=== DECOMP 0055B8F0') if '=== DECOMP 0055B8F0' in t else t.find('=== DECOMP 0040CB80')
print(t[s:e][:20000])
