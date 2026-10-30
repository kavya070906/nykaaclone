from pathlib import Path
from html.parser import HTMLParser
from urllib.request import urlopen, Request
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor, as_completed
import re,hashlib,html,json
root=Path(__file__).parent/'dist'
files=[*root.rglob('*.html'),*root.glob('*.css'),*root.glob('*.js')]
urls=set()
class Assets(HTMLParser):
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag in ['img','source','video'] and attrs.get('src','').startswith('https://'):urls.add(attrs['src'])
for f in files:
 t=f.read_text()
 if f.suffix=='.html':Assets().feed(t)
 for u in re.findall(r'url\([\"\']?(https://[^\)\"\']+)',t):urls.add(html.unescape(u))
 for u in re.findall(r'src=[\"\'](https://[^\"\']+)',t):urls.add(html.unescape(u))
urls={u for u in urls if any(h in urlsplit(u).netloc for h in ['nykaa','naikaa'])}
def get(u):
 ext=Path(urlsplit(u).path).suffix.lower()
 if ext not in ['.jpg','.jpeg','.png','.gif','.svg','.webp','.woff','.woff2','.avif']:ext='.bin'
 rel='assets/'+hashlib.sha256(u.encode()).hexdigest()[:18]+ext
 try:
  with urlopen(Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=12) as r:b=r.read()
  if not b:raise ValueError('empty')
  (root/rel).write_bytes(b)
  return u,'/'+rel,None
 except Exception as e:return u,None,type(e).__name__
mapping={};errors=[]
with ThreadPoolExecutor(max_workers=16) as ex:
 for u,p,e in ex.map(get,sorted(urls)):
  if p:mapping[u]=p
  else:errors.append({'url':u,'error':e})
for f in files:
 t=f.read_text()
 for u,p in mapping.items():t=t.replace(html.escape(u,quote=True),p).replace(u,p)
 f.write_text(t)
Path('asset-manifest.json').write_text(json.dumps({'assets':mapping,'unavailable':errors},indent=2))
print(json.dumps({'saved':len(mapping),'unavailable':errors}))
