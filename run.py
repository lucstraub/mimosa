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
params["emissions"]["inertia"]["global"] = -0.049999 # changed constraint to sectoral
# params["emissions"]["inertia"]["global_reverse"] = 0.05 # introduced constraint for emission increases
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = False # changed constraint from regional to global
# params['industry']['basic_material_scaling_baseline'] = 1.0 # 0.66 in EU based on Material Economics
# params["industry"]["CE_abatement_adjustment"] = 1.0
# params["industry"]["gamma_scaling"] = 1.0
params["model"]["welfare module"] = "cost_minimising"
params["industry"]["low_CE_cost"] = False
# params["industry"]["climate_policy_overlap"] = 0.24

run_type = 'single'
# choose either 'single' or 'CE_cost_sensitivity' or 'CE_abatement_sensitivity'

if run_type == 'single':
    # Below code for single scenario runs

    model1 = MIMOSA(params)
    model1.solve()
    # model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
    model1.save(f"result_CE_budget{params['emissions']['carbonbudget']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_CEcost{params['industry']['max_CE_cost']}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")

    # model1.plot(filename="result")

    #---------------------------------------------------

elif run_type == 'CE_cost_sensitivity':
    # Below code for CE cost sensitivity runs in high CE cost scenario
    
    try:
        os.mkdir("output/CE_sensitivity_cost")
    except FileExistsError:
        pass

    # CE_max_costs = np.arange(200, 1001, 200)
    # CE_max_costs = [100, 1000]
    CE_max_costs = [100]

    for cost in CE_max_costs:
        params["industry"]["max_CE_cost"] = cost
        if cost == 100:
            params["industry"]["low_CE_cost"] = True
        else:
            params["industry"]["low_CE_cost"] = False

        model = MIMOSA(params)
        model.solve()
        model.save(f"CE_sensitivity_cost/result_CE_budget{params['emissions']['carbonbudget']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_CEcost{cost}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")

elif run_type == 'CE_abatement_sensitivity':
    # Below code for CE abatement sensitivity runs
    
    try:
        os.mkdir("output/CE_sensitivity_abatement")
    except FileExistsError:
        pass

    # for reduced CE abatement potential scenarios
    # CE_max_rel_abatement = [0.2, 0.6]
    CE_max_rel_abatement = [0.649]
    basic_material_scaling = [0.5]
    
    # for agumented CE abatement potential scenarios
    # CE_max_rel_abatement = [1.0]
    # basic_material_scaling = [0.5, 0.75]
    # params['industry']['CE_fast_scaling'] = True

    for abatement in CE_max_rel_abatement:
        params["industry"]["CE_abatement_adjustment"] = abatement

        for scaling in basic_material_scaling:
            params['industry']['basic_material_scaling_baseline'] = scaling

            model = MIMOSA(params)
            model.solve()
            model.save(f"CE_sensitivity_abatement/result_CE_budget{params['emissions']['carbonbudget']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_fastScaling{params['industry']['CE_fast_scaling']}_CEabatement{abatement}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")
