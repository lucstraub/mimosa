import os
import numpy as np
import pandas as pd
from mimosa import MIMOSA, load_params
from datetime import datetime
# from pyomo.environ import value

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = "500 GtCO2"
params["time"]["end"] = 2100
params["emissions"]["baseline carbon intensity"] = False
# params["time"]["dt"] = 10
params["emissions"]["inertia"]["global"] = -0.04 # changed constraint to sectoral
# params["emissions"]["inertia"]["global_reverse"] = 0.05 # introduced constraint for emission increases
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = False # changed constraint from regional to global
# params["industry"]["gamma_scaling"] = 1.0
params["model"]["welfare module"] = "cost_minimising"

run_type = 'single'
# choose either 'single' or 'gamma_calibration' or 'cost_calibration'

if run_type == 'single':
    # Below code for single scenario runs

    model1 = MIMOSA(params)
    # print("Value of Gamma: ", value(model1.concrete_model.MAC_gamma))
    model1.solve()
    # model1.solve(use_neos=True, neos_email="l.straub@uu.nl")
    model1.save(f"result_nonCE_budget{params['emissions']['carbonbudget']}_industry{params['industry']['industry_scaling_baseline']}_gammascale{params['industry']['gamma_scaling']}_run{datetime.today().strftime('%Y-%m-%d-%H-%M')}")

    # model1.plot(filename="result")

    #---------------------------------------------------

elif run_type == 'gamma_calibration':
    # Below code for total mitigation cost/ gamma scaling factor calibration runs in industry scenario

    params["economics"]["damages"]["ignore damages"] = True
    
    try:
        os.mkdir("output/calibration_gamma")
    except FileExistsError:
        pass

    # gamma_scaling_factors = np.arange(0.6, 1.5, 0.2)
    gamma_scaling_factors = [1.1, 0.97]
    # carbon_budgets = np.arange(500, 701, 100)
    carbon_budgets = np.arange(400, 1101, 100)

    for scaling in gamma_scaling_factors:
        params["industry"]["gamma_scaling"] = scaling

        for budget in carbon_budgets:
            params["emissions"]["carbonbudget"] = f"{budget} GtCO2"
        
            model = MIMOSA(params)
            model.solve()
            model.save(f"calibration_gamma/industry_detailed_budget_data/industry_gamma_{scaling:.3f}_cb_{budget}")

    # Calculate the NPV of the mitigation costs for each run:
    
    def npv(values, discount_rate):
        years = values.index.astype(float)
        t = years - years[0]
        discount_factor = np.exp(-discount_rate * t)
        return np.trapz(values * discount_factor, t)

    for scaling in gamma_scaling_factors:
        results = []

        print(f"Gamma scaling factor: {scaling:.3f}")

        for budget in carbon_budgets:
            outp = pd.read_csv(f"output/calibration_gamma/industry_detailed_budget_data/industry_gamma_{scaling:.3f}_cb_{budget}.csv")
            global_mitig_costs = outp.loc[outp["Variable"] == "mitigation_costs_regional", "2020":].sum(
                axis=0
            )
            global_gdp_gross = outp.loc[outp["Variable"] == "GDP_gross", "2020":].sum(axis=0)
            r = 0.03
            npv_costs = npv(global_mitig_costs, r) / npv(global_gdp_gross, r)
            results.append({"budget": budget, "npv_costs": npv_costs})
            print(f"NPV of mitigation costs for {budget} GtCO2: {npv_costs:.1%}")

        results = pd.DataFrame(results)
        results.to_csv(f"output/calibration_gamma/industry_gamma_{scaling:.3f}_npv_costs.csv", index=False)
        
    #---------------------------------------------------

elif run_type == 'cost_calibration':
    # Below code for total mitigation cost calibration runs

    # carbon_budgets = np.arange(620, 631, 1)
    carbon_budgets = np.arange(600, 651, 10)

    for budget in carbon_budgets:
        params["emissions"]["carbonbudget"] = f"{budget} GtCO2"

        model = MIMOSA(params)
        model.solve()
        model.save(f"calibration_cost/result_nonCE_budget{params['emissions']['carbonbudget']}_industry{params['industry']['industry_scaling_baseline']}_gammascale{params['industry']['gamma_scaling']}")

    # Calculate the NPV of the mitigation costs for each run:
    
    def npv(values, discount_rate):
        years = values.index.astype(float)
        t = years - years[0]
        discount_factor = np.exp(-discount_rate * t)
        return np.trapz(values * discount_factor, t)

    results = []

    for budget in carbon_budgets:
        params["emissions"]["carbonbudget"] = f"{budget} GtCO2"
        outp = pd.read_csv(f"output/calibration_cost/result_nonCE_budget{params['emissions']['carbonbudget']}_industry{params['industry']['industry_scaling_baseline']}_gammascale{params['industry']['gamma_scaling']}.csv")
        global_mitig_costs = outp.loc[outp["Variable"] == "mitigation_costs_regional", "2020":].sum(
            axis=0
        )
        global_gdp_gross = outp.loc[outp["Variable"] == "GDP_gross", "2020":].sum(axis=0)
        r = 0.03
        npv_costs_abs = npv(global_mitig_costs, r)
        npv_costs_rel = npv(global_mitig_costs, r) / npv(global_gdp_gross, r)
        results.append({"budget": budget, "npv_costs_abs": npv_costs_abs, "npv_costs_rel": npv_costs_rel})
        print(f"NPV of mitigation costs for {budget} GtCO2 CE base scenario: {npv_costs_abs:.1f} trillion*usd ({npv_costs_rel:.8%} of GDP)")

    results = pd.DataFrame(results)
    results.to_csv(f"output/calibration_cost/npv_costs_nonCE_industry{params['industry']['industry_scaling_baseline']}_gammascale{params['industry']['gamma_scaling']}.csv", index=False)
