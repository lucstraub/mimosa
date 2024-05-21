from datetime import datetime
from mimosa import MIMOSA, load_params
from datetime import datetime

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False
# params["emissions"]["baseline carbon intensity"] = False

# model1 = MIMOSA(params)
# model1.solve()
# model1.save("run1")

#sector-feature
for scaling_industry in [0.25]:
    params["industry"]["industry_scaling_baseline"] = scaling_industry
    
    model1 = MIMOSA(params)
    model1.solve()
    #model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
    model1.save(f"testrun_industry_scaling_{scaling_industry}_with_CE_{datetime.today().strftime('%Y-%m-%d')}")
    
# model1.plot(filename="result")