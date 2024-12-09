"""
Model equations and constraints:
Emission trading module
Type: no trade
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, GlobalConstraint, RegionalConstraint, Param, Constraint
from mimosa.components.industry import global_AC_industry
from mimosa.components.mitigation import AC


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emission trading equations and constraints
    (no-trade specification)

    Necessary variables:
        m.mitigation_costs (abatement costs as paid for by this region)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.import_export_emission_reduction_balance = Param(m.t, m.regions, initialize=0)

    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: (
                    m.mitigation_costs_total_regional[t, r]
                    == (
                        (m.mitigation_costs_other_global[t] + m.mitigation_costs_industry_global[t])
                        * (m.L(m.year(t), r) / sum(m.L(m.year(t), x) for x in m.regions))
                        # population-weighted regional mitigation costs assignment
                    )
                ),
                "mitigation_costs",
            ),

            GlobalConstraint(
                lambda m, t: m.mitigation_costs_industry_global[t]
                == (
                    global_AC_industry(m.emissions_industry_global_relative_abatement[t], m, t)
                    * m.industry_scaling_baseline * sum(m.emissions_total_regional_baseline[t,r] for r in m.regions)
                ),
                "mitigation_costs_industry",
            ),

            GlobalConstraint(
                lambda m, t: m.mitigation_costs_other_global[t]
                == (
                    AC(m.emissions_other_global_relative_abatement[t], m, t)
                    * (1 - m.industry_scaling_baseline) * sum(m.emissions_total_regional_baseline[t,r] for r in m.regions)
                ),
                "mitigation_costs_nonindustry",
            )
        ]
    )

    return constraints
