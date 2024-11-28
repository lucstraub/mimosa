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
params["emissions"]["inertia"]["global"] = -0.05
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = False # changed constraint from regional to global
params["model"]["welfare module"] = "cost_minimising"

#---------------------------------------------------
# Uncomment below code for single base scenario runs

model1 = MIMOSA(params)
model1.solve()
# model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
model1.save(f"result_base_budget{params['emissions']['carbonbudget']}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")

#---------------------------------------------------
# Uncomment below code for total mitigation cost calibration runs in base scenario

# params["economics"]["damages"]["ignore damages"] = True
 
# try:
#     os.mkdir("output/calibration")
# except FileExistsError:
#     pass
 
# carbon_budgets = np.arange(200, 1501, 100)
 
# for budget in carbon_budgets:
#     params["emissions"]["carbonbudget"] = f"{budget} GtCO2"
 
#     model = MIMOSA(params)
#     model.solve()
#     model.save(f"calibration/base_cb_{budget}")

# # Calculate the NPV of the mitigation costs for each run:
 
# def npv(values, discount_rate):
#     years = values.index.astype(float)
#     t = years - years[0]
#     discount_factor = np.exp(-discount_rate * t)
#     return np.trapz(values * discount_factor, t)

# results = []

# for budget in carbon_budgets:
#     outp = pd.read_csv(f"output/calibration/base_cb_{budget}.csv")
#     global_mitig_costs = outp.loc[outp["Variable"] == "mitigation_costs", "2020":].sum(
#         axis=0
#     )
#     global_gdp_gross = outp.loc[outp["Variable"] == "GDP_gross", "2020":].sum(axis=0)
#     r = 0.03
#     npv_costs = npv(global_mitig_costs, r) / npv(global_gdp_gross, r)
#     results.append({"budget": budget, "npv_costs": npv_costs})
#     print(f"NPV of mitigation costs for {budget} GtCO2: {npv_costs:.1%}")

# results = pd.DataFrame(results)
# results.to_csv("output/calibration/base_npv_costs.csv", index=False)