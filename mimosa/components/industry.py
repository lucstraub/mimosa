"""
Model equations and constraints:
Industry MAC curves for non-CE and CE measures to reduce emissions
"""

from typing import Sequence

import numpy as np
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    Constraint,
    quant,
    value,
    soft_max,
    soft_min,
    exp,
    NonNegativeReals
)
import pyomo.kernel as knl

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

    m.non_CE_mitigation_costs_industry = Var(
        m.t,
        within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )

    m.industry_carbonprice_marg = Var(
        m.t,
        # bounds=lambda m: (0, 2 * 1.46003066623869 * m.gamma_scaling * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )

    m.industry_carbonprice_marg_max = Var(
        m.t,
        # bounds=lambda m: (0, 2 * 1.46003066623869 * m.gamma_scaling * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )

    m.CE_mitigation_costs_industry = Var(
        m.t,
        # within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )

    m.CE_carbonprice_marg = Var(
        m.t,
        bounds=lambda m: (0, None),
        units=quant.unit("currency_unit/emissions_unit"),
    )

    m.gamma_scaling = Param(doc="::industry.gamma_scaling")
    m.low_CE_cost = Param(doc="::industry.low_CE_cost") #boolean to distinguish low cost scenario for CE measures that uses an alternative CE MAC curve shape
    m.max_CE_cost_2050 = Param(doc="::industry.max_CE_cost_2050")
    m.max_CE_abatement_2050 = Param(doc="::industry.max_CE_abatement_2050")
    m.max_CE_abatement_2100 = Param(doc="::industry.max_CE_abatement_2100")

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    m.industry_carbonprice_marg[t] # this carbon price is assumed to implicitly include cost for some overlapping CE measures
                    == global_MAC_industry(m.emissions_industry_global_relative_abatement_after_CE[t], m, t)
                ),
                "marginal non-CE carbonprice industry",
            ),

            GlobalInitConstraint(
                lambda m: m.industry_carbonprice_marg[0] == 0, "marginal init_carbon_price industry"
            ),

            GlobalConstraint(
                lambda m, t: (
                    m.industry_carbonprice_marg_max[t]
                    == global_MAC_industry(m.industry_max_relative_abatement, m, t)
                ),
                "limit to marginal non-CE carbonprice industry",
            ),
            
            # GlobalConstraint(
            #     lambda m, t: (
            #         m.nonindustry_carbonprice_marg[t]
            #         >= m.industry_carbonprice_marg[t]
            #         # (soft_max(m.nonindustry_carbonprice_marg[t], m.industry_carbonprice_marg_max[t], 1000) - m.industry_carbonprice_marg[t]) ** 2
            #         # <= 0.0001
            #         # m.industry_carbonprice_marg[t]
            #         # == soft_max(m.nonindustry_carbonprice_marg[t], m.industry_carbonprice_marg_max[t], 1000)
            #     ),
            #     "sectoral marginal non-CE carbon price linkage",
            # ),

            GlobalConstraint(
                lambda m, t: (
                    (
                        m.CE_carbonprice_marg[t]
                        == global_MAC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t], m, t) # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity in ipopt solver
                        # in case of issues with piecewise linear function, marginal CE carbon price can be assigned lower limit of 0 and this constraint can be changed:
                        # instead of exactly assigned global_MAC_industry_CE, it can be eased and calculated as bigger or equal, having the effect that the model may choose CE carbon prices
                        # that are higher than the MAC curve would suggest (it should minimize them nevertheless)
                    )
                    if value(m.low_CE_cost)
                    else
                    (
                        m.CE_carbonprice_marg[t]
                        == global_MAC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                    )
                ),
                "marginal CE carbonprice industry",
            ),

            GlobalInitConstraint(
                lambda m: m.CE_carbonprice_marg[0] == 0, "marginal init_carbon_price CE industry"
            ),

            # GlobalConstraint(
            #     lambda m, t: (
            #         (m.CE_carbonprice_marg[t] <= m.max_CE_cost_2050 * 1.0508474576271185 / 1000) #conversion factor from 2015Euro to 2005USD & conversion from USD/tCO2 to trillion USD/Gt CO2
            #     ),
            #     "marginal CE carbonprice industry upper bound",
            # ),

            # GlobalConstraint(
            #     lambda m, t: (
            #         m.nonindustry_carbonprice_marg[t]
            #         >= m.CE_carbonprice_marg[t]
            #     ),
            #     "marginal carbonprice industry CE-based emissions abatement linkage 1",
            # ),

            # GlobalConstraint(
            #     lambda m, t: (
            #         m.industry_carbonprice_marg[t]
            #         >= m.CE_carbonprice_marg[t]
            #     ),
            #     "marginal carbonprice industry CE-based emissions abatement linkage 2",
            # ),
        ]
    )

    # helper variable and constraint to implement a workaround for piecewise linear CE industry MAC curve
    m.emissions_industry_global_relative_reduction_from_CE_upperHalf = Var(
        m.t, units=quant.unit("fraction_of_baseline_emissions"),
        initialize=0,
        bounds=(0, 1),
    )
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (m.CE_max_abatement[t] / 2 >= m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t])
                    if value(m.low_CE_cost)
                    else Constraint.Skip,
                "time-dependent upper boundary at half CE_max_abatement for upper half of CE abatement curve",
            ),
            GlobalConstraint(
                lambda m, t: (m.emissions_industry_global_relative_reduction_from_CE[t] >= m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t])
                    if value(m.low_CE_cost)
                    else Constraint.Skip,
                "Entire CE abatement must be equal or bigger than upper half of CE abatement curve",
            ),
            GlobalConstraint(
                lambda m, t: (m.CE_max_abatement[t] / 2 >= m.emissions_industry_global_relative_reduction_from_CE[t] - m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t])
                    if value(m.low_CE_cost)
                    else Constraint.Skip,
                "time-dependent upper boundary at half CE_max_abatement for lower half of CE abatement curve",
            ),
            # note that this can lead to positive value for emissions_industry_global_relative_reduction_from_CE in 2020 in the output file (linked to m.CE_max_abatement[2020] calculation below)
            # this has no consequence for calculations as abatement and cost logic correctly calculates 0 abatement and cost in 2020
        ]
    )

    # industry abatement cost curve time dynamics, based on Material Economics abatement curve, linear approximation
    m.CE_max_abatement = Var(m.t)
    m.CE_abatement_adjustment = Param(doc="::industry.CE_abatement_adjustment") #can be used to reduce CE max abatement potential, adapted for alternative CE scenarios
    # m.CE_fast_scaling = Param(doc="::industry.CE_fast_scaling") # replaced by parameter max_CE_abatement_2050 to adjust 2050 abatement potential directly for faster scaling
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    (
                        m.CE_max_abatement[t] == m.CE_abatement_adjustment * (0 + (m.max_CE_abatement_2050 / 30) * (m.year(t) - 2020)) #linear approximation for 2020-2050 up to specified max_CE_abatement_2050 (default: 40-45% abatement potential)
                    )
                    if (m.year(t) <= 2050 and m.year(t) > 2020)
                    else (
                        m.CE_max_abatement[t] == m.CE_abatement_adjustment * (m.max_CE_abatement_2050 + ((m.max_CE_abatement_2100 - m.max_CE_abatement_2050) / 50) * (m.year(t) - 2050)) #linear approximation after 2050 (default: increasing more slowly up to 60% in 2100)
                        # this currently also includes 2020 which is not correct but avoids some solver/ solution path complexity (linked to exponential function in CE MAC/AC curves)
                        # this has no effect on the results as the year 2020 is set to 0 abatement
                    )
                ),
                "CE abatement curve time-dependent maximum abatement",
            ),

            # GlobalConstraint(
            #     lambda m, t: (m.CE_max_abatement[t] >= m.emissions_industry_global_relative_reduction_from_CE[t]),
            #     "time-dependent upper boundary for CE abatement curve",
            # ),
        ]
    )

    ### Technological learning

    # Learning by doing
    # m.LBD_scaling_CE = Param()
    m.LBD_scaling_CE = m.LBD_scaling * m.industry_scaling_baseline * m.basic_material_scaling_baseline
    m.LBD_factor_CE = Var(m.t, bounds=(1e-6,1), initialize=1.0)
    constraints.append(
        GlobalConstraint(
            lambda m, t: m.LBD_factor_CE[t]
            == soft_min(
                (
                    m.cumulative_emissions_abatement_CE[t]
                )
                / m.LBD_scaling_CE
                + 1.0
            )
            ** m.log_LBD_rate,
            name="LBD CE",
        )
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

#CE MAC and AC curve, based on Material Economics abatement curve, adjusted to 2005USD
conversion_factor = 1.0508474576271185 / 1000 #conversion factor from 2015Euro to 2005USD & conversion from USD/tCO2 to trillion USD/Gt CO2
def global_MAC_industry_CE(a, m, t):

    if value(m.low_CE_cost):
        # low cost scenario: max price = 100 USD/tCO2, min price = 0 USD/tCO2, piecewise linear function with cost starting to increase towards max price at mid-point of abatement curve
        mid_point = 0.425 / 2
        # return m.LBD_factor_CE[t] * conversion_factor * ((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / mid_point) * a # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity in ipopt solver
        return m.LBD_factor_CE[t] * conversion_factor * (((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / mid_point) * a + exp(150 * (a - m.CE_max_abatement[t]/2 + 0.025))) # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity in ipopt solver
        # return conversion_factor * (100 / mid_point) * (a - mid_point)
    else:
        # default and high cost scenario: linear function, max price to be set at 40% abatement (e.g., 200 USD/tCO2), min price = 0 USD/tCO2
        # return m.LBD_factor_CE[t] * conversion_factor * ((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / 0.425) * a
        return m.LBD_factor_CE[t] * conversion_factor * (((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / 0.425) * a + exp(150 * (a - m.CE_max_abatement[t] + 0.025)))

def global_AC_industry_CE(a, m, t):

    if value(m.low_CE_cost):
        # low cost scenario: max price = 100 USD/tCO2, min price = 0 USD/tCO2, piecewise linear function with cost starting at mid-point of abatement curve
        mid_point = 0.425 / 2
        # return m.LBD_factor_CE[t] * conversion_factor * ((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / mid_point) * (a ** (1 + 1) / (1 + 1)) # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity in ipopt solver
        return m.LBD_factor_CE[t] * conversion_factor * (((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / mid_point) * (a ** (1 + 1) / (1 + 1)) + exp(150 * (a - m.CE_max_abatement[t]/2 + 0.025)) / 150) # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity in ipopt solver
        # return conversion_factor * (100 / mid_point) * ((a ** (1 + 1) / (1 + 1) - mid_point * a ** (0 + 1) / (0 + 1)) - (mid_point ** (1 + 1) / (1 + 1) - mid_point * mid_point ** (0 + 1) / (0 + 1))) # integral includes subtraction of term of lower half abatement cost offsetting the negative cost up to midpoint/ ensuring zero cost up to midpoint
    else:
        # default and high cost scenario: linear function, max price to be set (e.g., 200 USD/tCO2), min price = 0 USD/tCO2
        # return m.LBD_factor_CE[t] * conversion_factor * ((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / 0.425) * a ** (1 + 1) / (1 + 1)
        return m.LBD_factor_CE[t] * conversion_factor * (((m.max_CE_cost_2050 / m.LBD_factor_CE[6]) / 0.425) * a ** (1 + 1) / (1 + 1) + exp(150 * (a - m.CE_max_abatement[t] + 0.025)) / 150)
