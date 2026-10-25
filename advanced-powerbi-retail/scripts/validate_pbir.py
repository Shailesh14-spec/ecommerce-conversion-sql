"""Validate PBIP/PBIR JSON against Microsoft's public schemas, with a local cache."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urldefrag
import hashlib,json,warnings
import jsonschema
warnings.filterwarnings('ignore',category=DeprecationWarning)
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.schema-cache';CACHE.mkdir(exist_ok=True)
def retrieve(url):
 url=urldefrag(url)[0]
 p=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
 if not p.exists():
  # Some Microsoft schema URLs declare a different canonical $id. Resolve that
  # identity to the already-downloaded, unchanged official document.
  for cached in CACHE.glob('*.json'):
   document=json.loads(cached.read_text())
   if document.get('$id')==url:return document
  if not url.startswith('https://developer.microsoft.com/json-schemas/'):raise ValueError('Unapproved schema host: '+url)
  print('FETCH',url,flush=True)
  with urlopen(url,timeout=30) as r:p.write_bytes(r.read())
 return json.loads(p.read_text())
count=0
for p in sorted((ROOT/'powerbi').rglob('*')):
 if not p.is_file() or p.suffix not in ['.json','.pbip','.pbir','.pbism']:continue
 obj=json.loads(p.read_text())
 if '$schema' not in obj:continue
 schema=retrieve(obj['$schema'])
 resolver=jsonschema.RefResolver(base_uri=obj['$schema'],referrer=schema,handlers={'https':retrieve,'http':retrieve})
 validator=jsonschema.Draft7Validator(schema,resolver=resolver)
 errors=sorted(validator.iter_errors(obj),key=lambda e:str(e.path))
 if errors:raise ValueError(str(p)+': '+str(errors[0]))
 count+=1
print(f'PASS: {count} native project/report JSON definitions match Microsoft public schemas.')
