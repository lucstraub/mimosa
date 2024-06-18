from mimosa import MIMOSA, load_params

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False
# params["emissions"]["carbonbudget"] = "500 GtCO2"
params["emissions"]["baseline carbon intensity"] = False
# params["time"]["dt"] = 10
params["emissions"]["inertia"]["global"] = -0.05
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["regional min level"] = False
params["emissions"]["non increasing emissions after 2100"] = True # changed constraint from regional to global

model1 = MIMOSA(params)
model1.solve()
model1.save("base")
# model1.save("base_budget500")
