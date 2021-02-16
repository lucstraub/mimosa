##############################################
# Model equations and constraints:
# Objective function
#
##############################################

from model.common.pyomo import *

def constraints(m):
    """Equations and constraints for the objective of the optimisation
    (global costs specification)

    Necessary variables:
        

    Returns:
        - Objective
        - list of constraints (GlobalConstraint, GlobalInitConstraint, RegionalConstraint, RegionalInitConstraint)
    """
    constraints = []

    m.NPV = Var(m.t)
    m.PRTP = Param()
    constraints.extend([
        GlobalConstraint(
            lambda m,t: m.NPV[t] == m.NPV[t-1] + m.dt * exp(-m.PRTP * (m.year(t) - m.beginyear)) * (
                sum(m.abatement_costs[t,r] for r in m.regions) 
                + sum(m.damage_costs[t,r] * m.GDP_gross[t,r] for r in m.regions)
            )
            if t > 0 else Constraint.Skip,
            name='NPV'
        ),
        GlobalInitConstraint(lambda m: m.NPV[0] == 0)
    ])

    objective = Objective(rule=lambda m: m.NPV[m.tf], sense=minimize)

    return objective, constraints