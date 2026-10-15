import json,sys,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"runtime/iwp"))
from driver import screens
# Measured centre panel rectangle from E002 tour / E019 REGIONS.phase-panel.
RECT=(262,502,276,70)
def attack_red(r,g,b):return r>150 and g<60 and b<60
rows=[]
for arg in sys.argv[1:]:
 for p in sorted(Path(arg).glob("*.png")):
  raw=subprocess.run(["convert",str(p),"-depth","8","rgb:-"],check=True,capture_output=True).stdout
  if len(raw)!=800*600*3:continue
  rows.append({"bundle":Path(arg).name,"asset":p.name,"file_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"raw_rgb8_sha256":hashlib.sha256(raw).hexdigest(),"centre_red":screens.count(raw,RECT,attack_red),"screen":screens.name_of(raw),"signals":{k:v for k,v in screens.signals(raw).items() if k in ("menu","score-panel","notice-panel","continue-green","keep-playing","accept-loss")}})
print(json.dumps({"method":"Main-session RGB8 census over preserved E002/E019 frames. Centre phase-panel rectangle from measured E002/E019. Candidate red predicate r>150,g<60,b<60 searched to separate red human ATTACK control from human menus/placement, computer play, capture move-in and card prompts. A predicate alone identifies no state; main must attest positive visual frames and bounded population; no new runtime threshold yet.","rect":RECT,"predicate":{"r_gt":150,"g_lt":60,"b_lt":60},"frames":rows},indent=2))
