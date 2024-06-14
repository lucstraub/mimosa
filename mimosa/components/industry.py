"""
Model equations and constraints:
Industry MAC curves for non-CE and CE measures to reduce emissions
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    GeneralConstraint,
    GlobalConstraint,
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

    # industry and non-industry scaling factors
    m.industry_scaling_factor = Var(m.t)
    m.non_industry_scaling_factor = Var(m.t)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.industry_scaling_factor[t] == 0.011355298773375551 * m.year(t) - 22.287871097393577,
                "industry scaling factor",
            ),

            GlobalConstraint(
                lambda m, t: m.non_industry_scaling_factor[t] == -0.006245140521591652 * m.year(t) + 13.77368790184011,
                "non-industry scaling factor",
            ),
        ]
    )

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    # (
                    #     sum(m.L(m.year(t), r) * m.carbonprice[t, r] for r in m.regions)
                    #     / sum(m.L(m.year(t), x) for x in m.regions)
                    # )
                    m.carbonprice[t, "USA"]
                    == global_MAC_industry(m.emissions_industry_global_relative_abatement[t], m, t)
                ),
                "carbonprice industry emissions abatement matching",
            ),

            GlobalConstraint(
                lambda m, t: (
                    # (
                    #     sum(m.L(m.year(t), r) * m.carbonprice[t, r] for r in m.regions)
                    #     / sum(m.L(m.year(t), x) for x in m.regions)
                    # )
                    m.carbonprice[t, "USA"]
                    == global_MAC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                ),
                "carbonprice industry CE-based emissions abatement matching",
            ),
        ]
    )

    return constraints

def global_MAC_industry(a, m, t):
    factor = m.learning_factor[t] * m.industry_scaling_factor[t]
    return factor * m.MAC_gamma * a ** m.MAC_beta

def global_AC_industry(a, m, t):
    factor = m.learning_factor[t] * m.industry_scaling_factor[t]
    return factor * m.MAC_gamma * a ** (m.MAC_beta + 1) / (m.MAC_beta + 1)

def global_MAC_industry_CE(a, m, t):
    factor = (1 + m.learning_factor[t]) / 2 #delayed learning factor for CE measures
    return factor * 10000 * a ** 5

def global_AC_industry_CE(a, m, t):
    factor = (1 + m.learning_factor[t]) / 2 #delayed learning factor for CE measures
    return factor * 10000 * a ** (5 + 1) / (5 + 1)