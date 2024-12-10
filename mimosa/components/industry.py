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
    value,
    soft_max
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

    m.CE_mitigation_costs_industry = Var(
        m.t,
        # within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )

    m.CE_carbonprice = Var(
        m.t,
        bounds=lambda m: (0, None),
        units=quant.unit("currency_unit/emissions_unit"),
    )

    m.gamma_scaling = Param(doc="::industry.gamma_scaling")
    m.high_CE_cost = Param(doc="::industry.high_CE_cost")

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    m.industry_carbonprice[t]
                    == global_MAC_industry(m.emissions_industry_global_relative_abatement[t], m, t)
                ),
                "non-CE carbonprice industry",
            ),

            GlobalConstraint(
                lambda m, t: (
                    m.industry_carbonprice_max[t]
                    == global_MAC_industry(m.industry_max_relative_abatement, m, t)
                ),
                "limit to carbonprice industry",
            ),
            
            GlobalConstraint(
                lambda m, t: (
                    m.nonindustry_carbonprice[t]
                    >= m.industry_carbonprice[t]
                    # (soft_max(m.nonindustry_carbonprice[t], m.industry_carbonprice_max[t], 1000) - m.industry_carbonprice[t]) ** 2
                    # <= 0.0001
                    # m.industry_carbonprice[t]
                    # == soft_max(m.nonindustry_carbonprice[t], m.industry_carbonprice_max[t], 1000)
                ),
                "sectoral non-CE carbon price linkage",
            ),

            GlobalConstraint(
                lambda m, t: (
                    (
                        m.CE_carbonprice[t]
                        == global_MAC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                    )
                    if value(m.high_CE_cost)
                    else
                    (
                        m.CE_carbonprice[t]
                        == global_MAC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t], m, t) # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity
                        # == global_MAC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                        # in case of issues with piecewise linear function, CE carbon price can be assigned lower limit of 0 and this constraint can be changed:
                        # instead of exactly assigned global_MAC_industry_CE, it can be eased and calculated as bigger or equal, having the effect that the model may choose CE carbon prices
                        # that are higher than the MAC curve would suggest (it should minimize them nevertheless)
                    )
                ),
                "CE carbonprice industry",
            ),

            # GlobalConstraint(
            #     lambda m, t: (
            #         (m.CE_carbonprice[t] >= m.CE_max_abatement[t] / 2)
            #         if value(m.high_CE_cost) is False # only in case of low cost scenario with piecewise linear function, assuming any abatement potential at zero cost is implemented, overcoming complexities of implementing piecewise linear function with ipopt solver
            #         else Constraint.Skip
            #     ),
            #     "CE carbonprice industry lower bound",
            # ),

            GlobalConstraint(
                lambda m, t: (
                    (m.CE_carbonprice[t] <= 200 * 1.0508474576271185 / 1000) #conversion factor from 2015Euro to 2005USD & conversion from USD/tCO2 to trillion USD/Gt CO2
                    if value(m.high_CE_cost)
                    else
                    (m.CE_carbonprice[t] <= 100 * 1.0508474576271185 / 1000) #conversion factor from 2015Euro to 2005USD & conversion from USD/tCO2 to trillion USD/Gt CO2
                ),
                "CE carbonprice industry upper bound",
            ),

            GlobalConstraint(
                lambda m, t: (
                    m.nonindustry_carbonprice[t]
                    >= m.CE_carbonprice[t]
                ),
                "carbonprice industry CE-based emissions abatement matching 1",
            ),

            GlobalConstraint(
                lambda m, t: (
                    m.industry_carbonprice[t]
                    >= m.CE_carbonprice[t]
                ),
                "carbonprice industry CE-based emissions abatement matching 2",
            ),
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
                lambda m, t: (m.CE_max_abatement[t] / 2 >= m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t]),
                "time-dependent upper boundary at half CE_max_abatement for upper half of CE abatement curve",
            ),
            GlobalConstraint(
                lambda m, t: (m.emissions_industry_global_relative_reduction_from_CE[t] >= m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t]),
                "Entire CE abatement must be equal or bigger than upper half of CE abatement curve",
            ),
            GlobalConstraint(
                lambda m, t: (m.CE_max_abatement[t] / 2 >= m.emissions_industry_global_relative_reduction_from_CE[t] - m.emissions_industry_global_relative_reduction_from_CE_upperHalf[t]),
                "time-dependent upper boundary at half CE_max_abatement for lower half of CE abatement curve",
            ),
        ]
    )

    # industry abatement cost curve time dynamics, based on Material Economics abatement curve, linear approximation
    m.CE_max_abatement = Var(m.t)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    (
                        m.CE_max_abatement[t] == 0 + (0.4 / 30) * (m.year(t) - 2020) #linear approximation for 2020-2050
                    )
                    if (m.year(t) <= 2050 and m.year(t) > 2020)
                    else (
                        m.CE_max_abatement[t] == 0.4 + (0.2 / 50) * (m.year(t) - 2050) #linear approximation after 2050
                        # this currently also includes 2020 which is not correct but avoids a division by zero error
                        # this has no effect on the results as the year 2020 is set to 0 abatement and 0 carbon price
                    )
                ),
                "CE abatement curve time-dependent maximum abatement",
            ),

            GlobalConstraint(
                lambda m, t: (m.CE_max_abatement[t] >= m.emissions_industry_global_relative_reduction_from_CE[t]),
                "time-dependent upper boundary for CE abatement curve",
            ),
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

def global_MAC_industry_CE(a, m, t):
    conversion_factor = 1.0508474576271185 / 1000 #conversion factor from 2015Euro to 2005USD & conversion from USD/tCO2 to trillion USD/Gt CO2

    #based on Material Economics abatement curve, adjusted to 2005USD
    if m.high_CE_cost:
        return conversion_factor * ((200 / m.CE_max_abatement[t]) * a) # high cost scenario: max price = 200 USD/tCO2, min price = 0 USD/tCO2
    else:
        mid_point = m.CE_max_abatement[t] / 2
        return conversion_factor * (100 / mid_point) * a # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity
        # return conversion_factor * (100 / mid_point) * (a - mid_point) # max price = 100 USD/tCO2, min price = 0 USD/tCO2, piecewise linear function with cost starting at mid-point of abatement curve
        # return conversion_factor * ((100 / m.CE_max_abatement[t]) * a) # max price = 100 USD/tCO2, min price = 0 USD/tCO2
        # return conversion_factor * ((200 / m.CE_max_abatement[t]) * a - 100) # max price = 100 USD/tCO2, min price = -100 USD/tCO2

def global_AC_industry_CE(a, m, t):
    conversion_factor = 1.0508474576271185 / 1000 #conversion factor from 2015Euro to 2005USD & conversion from USD/tCO2 to trillion USD/Gt CO2

    #based on Material Economics abatement curve, adjusted to 2005USD
    if m.high_CE_cost:
        # high cost scenario: max price = 200 USD/tCO2, min price = 0 USD/tCO2
        return conversion_factor * (200 / m.CE_max_abatement[t]) * a ** (1 + 1) / (1 + 1)
    else:
        # max price = 100 USD/tCO2, min price = 0 USD/tCO2, piecewise linear function with cost starting at mid-point of abatement curve
        mid_point = m.CE_max_abatement[t] / 2
        return conversion_factor * (100 / mid_point) * (a ** (1 + 1) / (1 + 1)) # currently using upper half of CE abatement curve adjustment, due to piecewise linear function implementation complexity
        # return conversion_factor * (100 / mid_point) * ((a ** (1 + 1) / (1 + 1) - mid_point * a ** (0 + 1) / (0 + 1)) - (mid_point ** (1 + 1) / (1 + 1) - mid_point * mid_point ** (0 + 1) / (0 + 1))) # due to implementation complexity of piecewise linear function, the cost function is adjusted to start at mid-point of abatement curve (offsetting the negative cost up to midpoint)
        # return conversion_factor * (100 / m.CE_max_abatement[t]) * a ** (1 + 1) / (1 + 1) # max price = 100 USD/tCO2, min price = 0 USD/tCO2
        # return conversion_factor * ((200 / m.CE_max_abatement[t]) * a ** (1 + 1) / (1 + 1) - 100 * a ** (0 + 1) / (0 + 1)) # max price = 100 USD/tCO2, min price = -100 USD/tCO2
