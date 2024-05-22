from datetime import datetime
from mimosa import MIMOSA, load_params
from datetime import datetime

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False
# params["emissions"]["baseline carbon intensity"] = False

model1 = MIMOSA(params)
model1.solve()
# model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
model1.save(f"testrun_industry_with_CE_dummy_MAC_curves_{datetime.today().strftime('%Y-%m-%d')}")
    
# model1.plot(filename="result")