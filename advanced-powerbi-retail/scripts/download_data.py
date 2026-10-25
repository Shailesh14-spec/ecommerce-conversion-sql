"""Download original CC BY 4.0 UCI data and verify extracted workbook bytes."""
from pathlib import Path
from urllib.request import urlopen
import zipfile,io,hashlib
ROOT=Path(__file__).resolve().parents[1]
URL='https://archive.ics.uci.edu/static/public/352/online+retail.zip'
EXPECTED='43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d'
with urlopen(URL,timeout=120) as response:payload=response.read()
with zipfile.ZipFile(io.BytesIO(payload)) as archive:workbook=archive.read('Online Retail.xlsx')
if hashlib.sha256(workbook).hexdigest()!=EXPECTED:raise ValueError('Upstream workbook changed; review before accepting a new checksum')
p=ROOT/'data/raw/Online Retail.xlsx';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(workbook)
print('Downloaded and checksum-verified the original workbook. Attribution: docs/DATA_SOURCE.md')
