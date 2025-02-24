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
params["emissions"]["inertia"]["global_reverse"] = 0.05 # introduced constraint for emission increases
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = False # changed constraint from regional to global
# params['industry']['basic_material_scaling_baseline'] = 1.0 # 0.66 in EU based on Material Economics
# params["industry"]["CE_abatement_scaling"] = 1.0
# params["industry"]["gamma_scaling"] = 1.0
params["model"]["welfare module"] = "cost_minimising"
params["industry"]["high_CE_cost"] = False
# params["industry"]["climate_policy_overlap"] = 0.24

run_type = 'CE_abatement_sensitivity'
# choose either 'single' or 'CE_cost_sensitivity' or 'CE_abatement_sensitivity'

if run_type == 'single':
    # Below code for single scenario runs

    model1 = MIMOSA(params)
    model1.solve()
    # model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
    model1.save(f"result_CE_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_highCEscenario{params['industry']['high_CE_cost']}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")
    # currently need to adjust CE MAC curve scaling manually in industry file:
    # model1.save(f"result_CE_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_highCEscenario{params['industry']['high_CE_cost']}_fastScaling_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")

    # model1.plot(filename="result")

    #---------------------------------------------------

elif run_type == 'CE_cost_sensitivity':
    # Below code for CE cost sensitivity runs in high CE cost scenario

    params["industry"]["high_CE_cost"] = True
    
    try:
        os.mkdir("output/CE_sensitivity_cost")
    except FileExistsError:
        pass

    CE_max_costs = np.arange(200, 1001, 200)

    for cost in CE_max_costs:
        params["industry"]["max_CE_cost"] = cost

        model = MIMOSA(params)
        model.solve()
        model.save(f"CE_sensitivity_cost/result_CE_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_highCEscenario{params['industry']['high_CE_cost']}_CEcost{cost}")

elif run_type == 'CE_abatement_sensitivity':
    # Below code for CE abatement sensitivity runs
    
    try:
        os.mkdir("output/CE_sensitivity_abatement")
    except FileExistsError:
        pass

    CE_max_rel_abatement = [0.6]

    for abatement in CE_max_rel_abatement:
        params["industry"]["CE_abatement_scaling"] = abatement

        model = MIMOSA(params)
        model.solve()
        model.save(f"CE_sensitivity_abatement/result_CE_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_highCEscenario{params['industry']['high_CE_cost']}_CEabatement{abatement}")
        # currently need to adjust CE MAC curve scaling manually in industry file:
        # model.save(f"CE_sensitivity_abatement/result_CE_budget{params['emissions']['carbonbudget']}_gammascale{params['industry']['gamma_scaling']}_industry{params['industry']['industry_scaling_baseline']}material{params['industry']['basic_material_scaling_baseline']}_highCEscenario{params['industry']['high_CE_cost']}_fastScaling_CEabatement{abatement}")
