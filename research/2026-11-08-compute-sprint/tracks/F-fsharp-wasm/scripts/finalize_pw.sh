T=/home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm
P=/home/user/sprint-scratch/F/pw
cd $T
python3 - <<'PY'
import json, subprocess, glob
T="/home/user/sprint-wt/F-fsharp-wasm/research/2026-11-08-compute-sprint/tracks/F-fsharp-wasm"
P="/home/user/sprint-scratch/F/pw"
sets={"r008":[f"{P}/r008-run{i}.json" for i in (1,2,3)],"r009":[f"{P}/r009-run{i}.json" for i in (1,2,3)],"r010":[f"{P}/r010-run{i}.json" for i in (1,2,3)],
      "r010-trimfull":sorted(glob.glob(f"{P}/r010-fullclean-run*.json"))}
out={}
for k,fs in sets.items():
    if not fs: continue
    d=json.loads(subprocess.run(["python3","scripts/playwright_stability.py",k,"--project","chromium",*fs],capture_output=True,text=True,check=True).stdout)
    d["nonPassing"]={t:o for t,o in d["nonPassing"].items()}
    out[k]=d
json.dump(out,open(f"{T}/measurements/playwright-stability.json","w"),indent=1)
print({k:(v["tests"],v["verdicts"]) for k,v in out.items()})
PY
