from mimosa import MIMOSA, load_params

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False
# params["emissions"]["carbonbudget"] = "500 GtCO2"

model1 = MIMOSA(params)
model1.solve()
model1.save("run1")
# model1.save("run1_budget500")
