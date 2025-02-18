"""
Model equations and constraints:
Emission trading module
Type: no trade
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, GlobalConstraint, RegionalConstraint, Param, value
from mimosa.components.industry import global_AC_industry, global_AC_industry_CE
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
                lambda m, t, r: m.mitigation_costs_regional[t, r]
                == (m.L(m.year(t), r) / sum(m.L(m.year(t), x) for x in m.regions)) # population weighted total regional mitigation costs
                    * (m.mitigation_costs_nonindustry[t] + m.non_CE_mitigation_costs_industry[t] + m.CE_mitigation_costs_industry[t]),
                "mitigation_costs",
            ),

            GlobalConstraint(
                lambda m, t: m.non_CE_mitigation_costs_industry[t]
                == (
                    global_AC_industry(m.emissions_industry_global_relative_abatement_after_CE[t], m, t)
                    * m.emissions_industry_global_mitigation_CE[t] #considering emissions after CE-related emissions abatement
                    - (
                        m.climate_policy_overlap
                        * m.CE_mitigation_costs_industry[t] #assuming uniform distribution of cost for overlapping CE-related emissions abatement
                    )
                ),
                "non_CE_mitigation_costs_industry",
            ),

            GlobalConstraint(
                lambda m, t: (
                    (
                        m.CE_mitigation_costs_industry[t]
                        == (
                            global_AC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                            * m.basic_material_scaling_baseline * m.emissions_industry_global_baseline[t] # applying reduction through CE to basic material production share of industry emissions
                        )
                    )
                    if value(m.high_CE_cost)
                    else
                    (
                        m.CE_mitigation_costs_industry[t]
                        == (
                            global_AC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t], m, t) # currently using the upper half of the range of CE-related emissions abatement
                            # * global_AC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                            * m.basic_material_scaling_baseline * m.emissions_industry_global_baseline[t] # applying reduction through CE to basic material production share of industry emissions
                        )
                    )
                ),
                "CE_mitigation_costs_industry",
            ),
            GlobalConstraint(
                lambda m, t: m.mitigation_costs_nonindustry[t]
                == (
                    AC(m.emissions_other_global_relative_abatement[t], m, t)
                    * m.emissions_other_global_baseline[t]
                ),
                "mitigation_costs_nonindustry",
            )
        ]
    )

    return constraints
