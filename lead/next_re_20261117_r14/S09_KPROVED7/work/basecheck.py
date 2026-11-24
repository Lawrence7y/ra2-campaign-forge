"""List candidates where disk-name class is the base class of all held tables,
or nHolds==1, and show ③b-relevant features."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = json.load(open(OUT + r'\features.json', encoding='utf-8'))
cov=open(BASE+r'\COVERAGE\coverage.tsv',encoding='utf-8'); cov.readline(); d={}
for line in cov:
    p=line.rstrip('\n').split('\t')
    if len(p)>=5: d[p[0]]=p
cov.close()
# known ancestor map (base -> derived prefixes)
bases = {
 'GadgetClass':['ControlClass','StaticButtonClass','TextLabelClass','TextButtonClass','ShapeButtonClass','ToggleClass','EditClass','SliderClass','GaugeClass','TriColorGaugeClass','ListClass','ColorListClass','CheckListClass','DropListClass','LinkClass','Dial8Class','SBGadgetClass','SelectClass','TacticalClass','RTacticalClass'],
 'ControlClass':['CheckListClass','ColorListClass','Dial8Class','DropListClass','EditClass','SliderClass','GaugeClass','TriColorGaugeClass','ListClass'],
 'ListClass':['CheckListClass','ColorListClass','DropListClass'],
 'GaugeClass':['TriColorGaugeClass'],
 'GScreenClass':['MouseClass','DisplayClass','MapClass','TabClass','PowerClass','RadarClass','ScrollClass','SidebarClass'],
 'MapClass':['DisplayClass','TabClass','PowerClass','RadarClass','ScrollClass','SidebarClass'],
 'DisplayClass':['TabClass','PowerClass','RadarClass','ScrollClass','SidebarClass'],
 'TabClass':['ScrollClass'],
 'ToggleClass':['TextButtonClass','ShapeButtonClass'],
}
def cls_of(name):
    # disk name like GadgetClass::slot31 → GadgetClass
    return name.split('::')[0].replace('.?AV','').replace('@@','')
def name_class(c):
    return c.replace('.?AV','').replace('@@','').replace('TacticalClass@DisplayClass@@','TacticalClass')
for r in sorted(pool, key=lambda x:x['entry']):
    disk=d[r['entry']][2]; c=cls_of(disk)
    holds=r['holds']; classes=[name_class(h[2]) for h in holds]
    if not classes: continue
    # is c a base of all other classes?
    derived = bases.get(c,[])
    ok = all((x==c) or (x in derived) or ('@' in x) for x in classes)
    if not ok: continue
    det=r['_det']
    if det['size']>3000: continue
    txt='\n'.join(r['_disasm'])
    boolret = ('xor eax, eax' in txt and ('mov eax, 1' in txt or 'sete al' in txt or 'setne al' in txt))
    print('%-10s %-24s nh=%d sz=%d W=%d call=%d jcc=%d bool=%s' % (
        r['entry'], disk[:24], r['n_holds'], det['size'], det['nwrites'], det['calls_distinct'], det['jcc_distinct'], boolret))
