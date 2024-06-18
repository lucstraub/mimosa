from datetime import datetime
from mimosa import MIMOSA, load_params
from datetime import datetime

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False
params["emissions"]["baseline carbon intensity"] = False
# params["time"]["dt"] = 10
params["emissions"]["inertia"]["global"] = -0.05
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = True # changed constraint from regional to global
params['industry']['basic_material_scaling_baseline'] = 0.66 # based on Material Economics

model1 = MIMOSA(params)
model1.solve()
# model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
model1.save(f"testrun_industry{params['industry']['industry_scaling_baseline']}x{params['industry']['basic_material_scaling_baseline']}_with_CE_MAC_curves0.4_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")
    
# model1.plot(filename="result")