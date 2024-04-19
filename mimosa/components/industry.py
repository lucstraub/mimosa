"""
Model equations and constraints:
Energy and energy carbon intensity
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    Constraint,
    value,
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

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.carbonprice[t, "USA"]
                == global_MAC_industry(m.emissions_industry_global_relative_abatement[t], m, t),
                "carbonprice industry emissions matching",
            ),

            GlobalConstraint(
                lambda m, t: m.emissions_industry_global_baseline[t]
                == sum(m.emissions_industry_regional_baseline[t,r] for r in m.regions),
                "global industry baseline",
            ),
        ]
    )

    return constraints

def global_MAC_industry(a, m, t):
    factor = m.learning_factor[t]
    return factor * m.MAC_gamma * a ** m.MAC_beta

def global_AC_industry(a, m, t):
    factor = m.learning_factor[t]
    return factor * m.MAC_gamma * a ** (m.MAC_beta + 1) / (m.MAC_beta + 1)