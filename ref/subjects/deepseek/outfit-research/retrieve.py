"""Read-only public-source retrieval for bounded outfit research."""
from pathlib import Path
import os,threading,time,json,hashlib,subprocess,sys,urllib.request,concurrent.futures
stop=threading.Timer(45,lambda:os._exit(124));stop.daemon=True;stop.start()
ROOT=Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8')
mode=sys.argv[1]
if mode=='domains':
    env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
    cmd=[sys.executable,'C:/Users/Administrator/.agents/skills/anysearch/scripts/anysearch_cli.py','get_sub_domains','--domain','social_media']
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=36,env=env)
    (ROOT/'anysearch-domains.txt').write_bytes(p.stdout+p.stderr);print((p.stdout+p.stderr).decode('utf-8',errors='replace')[:9000])
elif mode=='cetus':
    base='https://raw.githubusercontent.com/AvroraCL/CETUS-Desktop/7f14ea7819dfb025bafce2f0d088e4901aefead6/'
    jobs=[('cetus-README.md','README.md'),('cetus-splash.png','src/Cetus.Desktop/Assets/cetus-splash.png'),('cetus-titlebar.png','src/Cetus.Desktop/Assets/cetus-titlebar.png'),('cetus-logo.png','src/Cetus.Desktop/Assets/logo.png')]
    def fetch(job):
        name,path=job;url=base+path
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Aikon-reference-research'})
            with urllib.request.urlopen(req,timeout=22) as r:data=r.read()
            (ROOT/name).write_bytes(data)
            return {'file':name,'url':url,'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':'ok'}
        except Exception as e:return {'file':name,'url':url,'status':'error','error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(fetch,jobs))
    (ROOT/'cetus-retrieval.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
elif mode=='search':
    env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
    queries=[{'query':'"CETUS-Desktop" "女仆"'},{'query':'"AvroraCL" "CETUS" "立绘"'},{'query':'"DeepSeek" "Grok" "女仆"','domain':'social_media','sub_domain':'social_media.social_media','sub_domain_params':'type=x_media,keyword=DeepSeek Grok 女仆,region='}]
    cmd=[sys.executable,'C:/Users/Administrator/.agents/skills/anysearch/scripts/anysearch_cli.py','batch_search','--queries',json.dumps(queries,ensure_ascii=False),'--max_results','3']
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=36,env=env)
    (ROOT/'anysearch-search.txt').write_bytes(p.stdout+p.stderr);print((p.stdout+p.stderr).decode('utf-8',errors='replace')[:18000])
elif mode=='candidates':
    jobs=[('candidate-a-maid.jpg','https://raw.githubusercontent.com/fornarwhal/deepseek-whale-girl-icon/main/original-whale-girl.jpg'),('candidate-b-gothic.png','https://i0.hdslb.com/bfs/new_dyn/3c682551e90b44b1a02c01ed337b22884456176.png'),('candidate-c-hoodie.png','https://i0.hdslb.com/bfs/new_dyn/d46536f7163fd739bb6e105c3d964b834456176.png')]
    def fetch(job):
        name,url=job
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Aikon-reference-research'})
            with urllib.request.urlopen(req,timeout=22) as r:data=r.read()
            (ROOT/name).write_bytes(data)
            return {'file':name,'url':url,'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':'ok'}
        except Exception as e:return {'file':name,'url':url,'status':'error','error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(fetch,jobs))
    (ROOT/'candidate-retrieval.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
else:raise ValueError(mode)
stop.cancel()
