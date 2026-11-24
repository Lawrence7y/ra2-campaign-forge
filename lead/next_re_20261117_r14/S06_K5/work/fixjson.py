
import json
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06_K5\work\candidate_scan.json'
obj=json.load(open(p,encoding='gbk'))
json.dump(obj,open(p,'w',encoding='utf-8'),indent=1,ensure_ascii=False)
print("resaved utf8, keys:",list(obj.keys()))
