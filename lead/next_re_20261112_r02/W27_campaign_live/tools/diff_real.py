import json
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out"
a=json.load(open(p+r"\real_pre.json",encoding="utf-8"))
b=json.load(open(p+r"\real_post.json",encoding="utf-8"))
print("PRE :",a["file_count"],a["total_bytes"],a["maplike_count"])
print("POST:",b["file_count"],b["total_bytes"],b["maplike_count"])
am={x["rel"]:x for x in a["files"]}; bm={x["rel"]:x for x in b["files"]}
added=sorted(set(bm)-set(am)); removed=sorted(set(am)-set(bm))
changed=[k for k in sorted(set(am)&set(bm)) if am[k]!=bm[k]]
print("added=",len(added),added[:10])
print("removed=",len(removed),removed[:10])
print("changed=",len(changed),changed[:10])
for k in changed[:10]: print("  ",k,"pre",am[k],"post",bm[k])
print("REAL_RA2MD_INI_POST=",bm["RA2MD.INI"]["sha256"])
print("IDENTICAL_TREE=",a["files"]==b["files"])
