from mimosa import MIMOSA, load_params

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False

# model1 = MIMOSA(params)
# model1.solve()
# model1.save("run1")

#sector-feature
for scaling_industry in [0.2, 0.8]:
    params["industry"]["industry_scaling_baseline"] = scaling_industry
    params["emissions"]["baseline carbon intensity"] = False

    model1 = MIMOSA(params)
    model1.solve()
    model1.save(f"testrun_scaling_{scaling_industry}")
    
# model1.plot(filename="result")