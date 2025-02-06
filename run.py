import os
import numpy as np
import pandas as pd
from mimosa import MIMOSA, load_params
from datetime import datetime

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = "500 GtCO2"
params["time"]["end"] = 2100
params["emissions"]["baseline carbon intensity"] = False
# params["time"]["dt"] = 10
params["emissions"]["inertia"]["global"] = -0.05 # changed constraint to sectoral
params["emissions"]["inertia"]["global_reverse"] = False # introduced constraint for emission increases
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = False # changed constraint from regional to global
params['industry']['basic_material_scaling_baseline'] = 0.55 # 0.66 in EU based on Material Economics
params["industry"]["CE_abatement_scaling"] = 1.0
params["industry"]["gamma_scaling"] = 1.0
params["model"]["welfare module"] = "cost_minimising"
params["industry"]["high_CE_cost"] = False

run_type = 'single'
# choose either 'single' or 'CE_cost_sensitivity'

if run_type == 'single':
    # Below code for single scenario runs

    model1 = MIMOSA(params)
    model1.solve()
    # model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
    model1.save(f"result_CE_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_highCEscenario{params['industry']['high_CE_cost']}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")

    # model1.plot(filename="result")

    #---------------------------------------------------

elif run_type == 'CE_cost_sensitivity':
    # Below code for CE cost sensitivity runs in high CE cost scenario

    params["industry"]["high_CE_cost"] = True
    
    try:
        os.mkdir("output/CE_cost_sensitivity")
    except FileExistsError:
        pass

    CE_max_costs = np.arange(200, 1000, 200)

    for cost in CE_max_costs:
        params["industry"]["max_CE_cost"] = cost

        model = MIMOSA(params)
        model.solve()
        model.save(f"CE_cost_sensitivity/result_CE_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_highCEscenario{params['industry']['high_CE_cost']}_CEcost{cost}")
