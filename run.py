from mimosa import MIMOSA, load_params
from datetime import datetime

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = "500 GtCO2"
params["time"]["end"] = 2100
params["emissions"]["baseline carbon intensity"] = False
# params["time"]["dt"] = 10
params["emissions"]["inertia"]["global"] = -0.05
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = False # changed constraint from regional to global
params['industry']['basic_material_scaling_baseline'] = 0.55 # 0.66 in EU based on Material Economics
params["industry"]["gamma_scaling"] = 0.985
params["industry"]["high_CE_cost"] = True

model1 = MIMOSA(params)
model1.solve()
# model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
model1.save(f"testrun_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_with_CE_MAC_curves0.4high{params['industry']['high_CE_cost']}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")
    
# model1.plot(filename="result")