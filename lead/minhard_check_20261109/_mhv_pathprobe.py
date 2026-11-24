import os
p="D:/Project/ra2-campaign-forge/lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md"
print("exists",os.path.exists(p))
print("open",len(open(p,encoding="utf-8").read()))
