#!/bin/bash
# prep_reel.sh N  - run in the batch's edit folder: plan -> cut-outs -> AE text (delete+rebuild RN_TEXT).
# Then: ae_save_project, and in Premiere: var BUILD_DATA=".../rN_prem.json"; $.evalFile(".../jsx/build_reel.jsx");
K="C:/Users/btaza/.claude/skills/anan-reel-edit/scripts"; N=$1
python "plan_r$N.py" || exit 1
python - "$N" "$K" <<'PY'
import json,subprocess,sys
n,k=sys.argv[1],sys.argv[2]
for src,ss,dur,out in json.load(open(f'r{n}_cutouts.json')):
    r=subprocess.run(['python',f'{k}/cutout_rvm.py',src,str(ss),str(dur),out],capture_output=True,text=True)
    print(r.stdout.strip() or r.stderr.strip()[-300:])
PY
timeout 900 node "$K/ae_call.mjs" call ae_do "@$(cygpath -m "$(pwd)")/r${N}_ae_call.json" 2>/dev/null > "r${N}_ae_result.json"
python - "$N" <<'PY'
import json,sys
t=open(f'r{sys.argv[1]}_ae_result.json',encoding='utf-8').read()  # Bangla in the output: read as UTF-8
d=json.loads(t[t.index('{'):])  # a failed op prefixes the JSON with a text line
res=d.get('result',{}).get('results',[])
bad=[(i,x) for i,x in enumerate(res) if not x.get('ok',True) and i>0]  # op 0 = deleting a comp that may not exist yet
print('AE ok',d.get('ok'),'ops',len(res),'failed',len(bad)); [print(i,json.dumps(x)[:300]) for i,x in bad[:5]]
PY
