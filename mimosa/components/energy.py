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
    """Energy and energy carbon intensity equations and constraints

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

    m.baseline_energy_primary_material = Var(m.t) #unit: EJ
    m.baseline_energy_secondary_material = Var(m.t) #unit: EJ
    m.baseline_energy_carbon_intensity = Var(m.t) #unit: GtCO2/EJ
    m.mitigated_energy_carbon_intensity = Var(m.t) #unit: GtCO2/EJ
    m.relative_reduction_energy_carbon_intensity = Var(m.t) #unit: %

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.baseline_energy_carbon_intensity[t]
                == 0.05,
                "fixed energy carbon intensity",
            ),

            GlobalConstraint(
                lambda m, t: m.mitigated_energy_carbon_intensity[t]
                == (1-m.relative_reduction_energy_carbon_intensity[t]) * m.baseline_energy_carbon_intensity[t],
                "mitigated energy carbon intensity",
            ),

            GlobalConstraint(
                lambda m, t: m.carbonprice[t, "USA"]
                == MAC_enery_carbon_intensity(m.relative_reduction_energy_carbon_intensity[t], m, t),
                "carbonprice energy carbon intensity matching",
            ),

            GlobalConstraint(
                lambda m, t: m.carbonprice[t, "USA"]
                == MAC_industry(m.emissions_industry_regional_relative_abatement[t], m, t),
                "carbonprice industry emissions matching",
            ),

            GlobalConstraint(
                lambda m, t: m.baseline_energy_primary_material[t]
                == 100,
                "fixed energy of primary material",
            ),

            GlobalConstraint(
                lambda m, t: m.baseline_energy_secondary_material[t]
                == 100,
                "fixed energy of secondary material",
            ),

            #sector-feature
            GlobalConstraint(
                lambda m, t: m.emissions_industry_global_mitigation[t]
                == (m.baseline_energy_primary_material[t] + m.baseline_energy_secondary_material[t]) * m.mitigated_energy_carbon_intensity[t],
                # == sum(m.emissions_industry_regional_baseline[t,r] for r in m.regions),
                "global industry emissions",
            ),

            GlobalConstraint(
                lambda m, t: m.emissions_industry_global_baseline[t]
                == sum(m.emissions_industry_regional_baseline[t,r] for r in m.regions),
                "global industry baseline",
            ),
        ]
    )

    return constraints

def MAC_enery_carbon_intensity(a, m, t):
    factor = m.learning_factor[t]
    return factor * 0.6 * a**3

def MAC_industry(a, m, t):
    factor = m.learning_factor[t]
    return factor * 0.6 * a**3

def AC_industry(a, m, t):
    factor = m.learning_factor[t]
    return factor * 0.6 * a ** (3 + 1) / (3 + 1)