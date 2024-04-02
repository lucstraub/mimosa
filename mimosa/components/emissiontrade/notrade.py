"""
Model equations and constraints:
Emission trading module
Type: no trade
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, RegionalConstraint, Param
from mimosa.components.energy import AC_enery_carbon_intensity

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
                    m.mitigation_costs[t, r]
                    == (
                        AC(m.relative_abatement[t, r], m, t, r) * m.baseline_other[t, r]
                        + (
                            (m.L(m.year(t), r) / sum(m.L(m.year(t), x) for x in m.regions))
                            * AC_enery_carbon_intensity(m.relative_reduction_energy_carbon_intensity[t], m, t)
                            * m.baseline_energy_carbon_intensity[t]
                            * (m.baseline_energy_primary_material[t] + m.baseline_energy_secondary_material[t])
                        )
                    )
                    # == AC(m.relative_abatement[t, r], m, t, r) * m.baseline_other[t, r]
                    # #sector-feature
                    # == AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r]
                ),
                "mitigation_costs",
            ),
        ]
    )

    return constraints
