"""Set the Power Query import folder in the generated semantic model."""
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--data-folder',type=Path,default=ROOT/'data/model');args=p.parse_args()
folder=args.data_folder.resolve()
if not (folder/'FactTransactions.csv').is_file():raise FileNotFoundError('Run build_data.py first')
model_path=ROOT/'powerbi/RetailIntelligence.SemanticModel/model.bim'
model=json.loads(model_path.read_text())
for expression in model['model']['expressions']:
 if expression['name']=='SourceFolder':expression['expression']='"'+str(folder).replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
model_path.write_text(json.dumps(model,indent=2)+'\n')
print('SourceFolder configured. Open powerbi/RetailIntelligence.pbip on Windows and refresh.')
