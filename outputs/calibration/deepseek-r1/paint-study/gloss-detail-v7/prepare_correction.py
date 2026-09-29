"""Record the only measured correction; do not rewrite the main trial."""
from pathlib import Path
import json
here=Path(__file__).resolve().parent
plan=json.loads((here/'trial-main.json').read_text())
plan['correction_basis']='Main trial reduced main fin 1-4px MAE 7.551 to 4.856 but all-region RMSE rose 9.191 to 9.225; visually its lower glint was too thin/peaky next to the soft source. Reduce the narrow peak while slightly raising the broad weak transition. All other parameters unchanged.'
plan['open_rims'][0]['bands'][0]['opacity']=0.14
plan['open_rims'][0]['bands'][1]['opacity']=0.24
path=here/'trial-correction.json'
assert not path.exists()
path.write_text(json.dumps(plan,indent=2)+'\n')
