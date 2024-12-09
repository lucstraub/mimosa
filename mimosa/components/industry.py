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
    Constraint,
    quant,
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

    m.mitigation_costs_industry_global = Var(
        m.t,
        # within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )

    m.carbonprice_industry_global = Var(
        m.t,
        # bounds=lambda m: (0, 2 * 1.46003066623869 * m.gamma_scaling * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )

    # m.carbonprice_industry_global_max = Var(
    #     m.t,
    #     # bounds=lambda m: (0, 2 * 1.46003066623869 * m.gamma_scaling * m.MAC_gamma),
    #     units=quant.unit("currency_unit/emissions_unit"),
    # )

    m.gamma_scaling = Param(doc="::industry.gamma_scaling")

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    m.carbonprice_industry_global[t]
                    == global_MAC_industry(m.emissions_industry_global_relative_abatement[t], m, t)
                    if t > 0
                    else Constraint.Skip
                ),
                "global carbonprice industry (non-CE)",
            ),

            GlobalInitConstraint(
                lambda m: m.carbonprice_industry_global[0] == 0,
                "init_carbon_price_industry (non-CE)",
            ),

            # GlobalConstraint(
            #     lambda m, t: (
            #         m.carbonprice_industry_global_max[t]
            #         == global_MAC_industry(m.industry_max_relative_abatement, m, t)
            #         if t > 0
            #         else Constraint.Skip
            #     ),
            #     "limit to global carbonprice industry (non-CE)",
            # ),

            GlobalConstraint(
                lambda m, t: (
                    m.carbonprice_other_global[t]
                    >= m.carbonprice_industry_global[t]
                    if t > 0
                    else Constraint.Skip
                ),
                "sectoral carbon price linkage (non-CE)",
            ),
        ]
    )

    return constraints

def global_MAC_industry(a, m, t):
    factor = m.learning_factor[t] * 1.46003066623869 * m.gamma_scaling # fixed industry scaling factor calibrated to 2070 data which shows hard-to-abate character 
    return factor * m.MAC_gamma * a ** m.MAC_beta

def global_AC_industry(a, m, t):
    factor = m.learning_factor[t] * 1.46003066623869 * m.gamma_scaling # fixed industry scaling factor calibrated to 2070 data which shows hard-to-abate character 
    return factor * m.MAC_gamma * a ** (m.MAC_beta + 1) / (m.MAC_beta + 1)