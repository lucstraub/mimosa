from mimosa import MIMOSA, load_params
from datetime import datetime

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False
# params["emissions"]["baseline carbon intensity"] = False

# #sector-feature
# for scaling_industry in [0.25]:
#     params["industry"]["industry_scaling_baseline"] = scaling_industry
#     params["emissions"]["baseline carbon intensity"] = False

#     model1 = MIMOSA(params)
#     model1.solve()
#     model1.save(f"testrun_industry_scaling_{scaling_industry}_{datetime.today().strftime('%Y-%m-%d')}")

model1 = MIMOSA(params)
model1.solve()
model1.save(f"testrun_industry_energy_carbon_intensity_{datetime.today().strftime('%Y-%m-%d')}")

# model1.plot(filename="result")