"""
Model equations and constraints:
Emission trading module
Type: no trade
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, RegionalConstraint, Param
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
                lambda m, t, r: m.mitigation_costs[t, r]
                == (
                    AC(m.emissions_other_regional_relative_abatement[t, r], m, t, r) * m.emissions_other_regional_baseline[t, r]
                    + (
                        (m.L(m.year(t), r) / sum(m.L(m.year(t), x) for x in m.regions))
                        * global_AC_industry(m.emissions_industry_global_relative_abatement[t], m, t)
                        * m.emissions_industry_global_baseline[t]
                    )
                    + (
                        (m.L(m.year(t), r) / sum(m.L(m.year(t), x) for x in m.regions))
                        * global_AC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                        * (1 - m.emissions_industry_global_relative_abatement[t]) #considering emissions after non-CE-related emissions abatement
                        * m.emissions_industry_global_baseline[t]
                    )
                ),
                #sector-feature
                # == AC(m.emissions_other_regional_relative_abatement[t, r], m, t, r) * m.emissions_other_regional_baseline[t, r],
                # == AC(m.emissions_other_regional_relative_abatement[t, r], m, t, r) * m.emissions_total_regional_baseline[t, r],
                "mitigation_costs",
            ),
        ]
    )

    return constraints
