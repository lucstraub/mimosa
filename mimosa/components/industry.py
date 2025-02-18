"""
Model equations and constraints:
Industry MAC curves for non-CE and CE measures to reduce emissions
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    quant,
    soft_max
)

def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Industry equations and constraints

    Necessary variables:
        ...

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.mitigation_costs_industry = Var(
        m.t,
        # within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )

    m.industry_carbonprice = Var(
        m.t,
        # bounds=lambda m: (0, 2 * 1.46003066623869 * m.gamma_scaling * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )

    m.industry_carbonprice_max = Var(
        m.t,
        # bounds=lambda m: (0, 2 * 1.46003066623869 * m.gamma_scaling * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )

    m.gamma_scaling = Param(doc="::industry.gamma_scaling")

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    m.industry_carbonprice[t]
                    == global_MAC_industry(m.emissions_industry_global_relative_abatement[t], m, t)
                ),
                "non-CE carbonprice industry",
            ),

            GlobalInitConstraint(
                lambda m: m.industry_carbonprice[0] == 0, "init_carbon_price industry"
            ),

            GlobalConstraint(
                lambda m, t: (
                    m.industry_carbonprice_max[t]
                    == global_MAC_industry(m.industry_max_relative_abatement, m, t)
                ),
                "limit to carbonprice industry",
            ),

            # GlobalConstraint(
            #     lambda m, t: (
            #         m.nonindustry_carbonprice[t]
            #         >= m.industry_carbonprice[t]
            #         # (soft_max(m.nonindustry_carbonprice[t], m.industry_carbonprice_max[t], 1000) - m.industry_carbonprice[t]) ** 2
            #         # <= 0.0001
            #         # m.industry_carbonprice[t]
            #         # == soft_max(m.nonindustry_carbonprice[t], m.industry_carbonprice_max[t], 1000)
            #     ),
            #     "sectoral carbon price linkage",
            # ),
        ]
    )

    return constraints

def global_MAC_industry(a, m, t):
    # factor = m.learning_factor[t] * m.industry_scaling_factor[t]
    factor = m.learning_factor[t] * 1.46003066623869 * m.gamma_scaling # fixed industry scaling factor calibrated to 2070 data which shows hard-to-abate character 
    return factor * m.MAC_gamma * a ** m.MAC_beta

def global_AC_industry(a, m, t):
    # factor = m.learning_factor[t] * m.industry_scaling_factor[t]
    factor = m.learning_factor[t] * 1.46003066623869 * m.gamma_scaling # fixed industry scaling factor calibrated to 2070 data which shows hard-to-abate character 
    return factor * m.MAC_gamma * a ** (m.MAC_beta + 1) / (m.MAC_beta + 1)