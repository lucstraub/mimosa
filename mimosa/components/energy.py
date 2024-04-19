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

    m.baseline_energy_primary_material = Var(m.t) #unit: EJ/yr
    m.baseline_energy_secondary_material = Var(m.t) #unit: EJ/yr
    m.baseline_energy_carbon_intensity = Var(m.t) #unit: GtCO2/EJ
    m.mitigated_energy_carbon_intensity = Var(m.t) #unit: GtCO2/EJ
    m.relative_reduction_energy_carbon_intensity = Var(m.t) #unit: %

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.baseline_energy_carbon_intensity[t]
                == 0.05,
                "baseline energy carbon intensity",
            ),

            GlobalConstraint(
                lambda m, t: m.mitigated_energy_carbon_intensity[t]
                == (1-m.relative_reduction_energy_carbon_intensity[t]) * m.baseline_energy_carbon_intensity[t]
                if t > 0
                else Constraint.Skip,
                "mitigated energy carbon intensity",
            ),
            
            GlobalInitConstraint(
                lambda m: m.mitigated_energy_carbon_intensity[0]
                == m.baseline_energy_carbon_intensity[0]
            ),

            GlobalConstraint(
                lambda m, t: m.carbonprice[t, "USA"]
                == MAC_enery_carbon_intensity(m.relative_reduction_energy_carbon_intensity[t], m, t),
                "carbonprice energy carbon intensity matching",
            ),

            # GlobalConstraint(
            #     lambda m, t: m.carbonprice[t, "USA"]
            #     == MAC_industry(m.relative_abatement_industry[t], m, t),
            #     "carbonprice industry emissions matching",
            # ),

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
                lambda m, t: m.global_emissions_industry[t]
                == (m.baseline_energy_primary_material[t] + m.baseline_energy_secondary_material[t]) * m.mitigated_energy_carbon_intensity[t],
                # == sum(m.baseline_industry[t,r] for r in m.regions),
                "global industry emissions",
            ),

            GlobalConstraint(
                lambda m, t: m.global_baseline_industry[t]
                == (m.baseline_energy_primary_material[t] + m.baseline_energy_secondary_material[t]) * m.baseline_energy_carbon_intensity[t],
                # == sum(m.baseline_industry[t,r] for r in m.regions),
                "global industry baseline",
            ),
        ]
    )

    return constraints

def MAC_enery_carbon_intensity(a, m, t):
    factor = m.learning_factor[t]
    return factor * m.MAC_gamma * a ** m.MAC_beta

def MAC_industry(a, m, t):
    factor = m.learning_factor[t]
    return factor * m.MAC_gamma * a ** m.MAC_beta

def AC_industry(a, m, t):
    factor = m.learning_factor[t]
    return factor * m.MAC_gamma * a ** (m.MAC_beta + 1) / (m.MAC_beta + 1)