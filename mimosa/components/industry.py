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
    quant,
    value
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
        m.regions,
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
        m.regions,
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

    # # industry and non-industry scaling factors
    # m.industry_scaling_factor = Var(m.t)
    # m.non_industry_scaling_factor = Var(m.t)
    # constraints.extend(
    #     [
    #         GlobalConstraint(
    #             lambda m, t: m.industry_scaling_factor[t] == 0.011355298773375551 * m.year(t) - 22.287871097393577,
    #             "industry scaling factor",
    #         ),

    #         GlobalConstraint(
    #             lambda m, t: m.non_industry_scaling_factor[t] == -0.006245140521591652 * m.year(t) + 13.77368790184011,
    #             "non-industry scaling factor",
    #         ),
    #     ]
    # )

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
                    == global_MAC_industry(m.max_relative_abatement, m, t)
                ),
                "limit to carbonprice industry",
            ),
            
            GlobalConstraint(
                lambda m, t: (
                    (
                        sum(m.L(m.year(t), r) * m.carbonprice[t, r] for r in m.regions)
                        / sum(m.L(m.year(t), x) for x in m.regions)
                    )
                    # m.carbonprice[t, "USA"]
                    >= m.industry_carbonprice[t]
                ),
                "carbonprice industry emissions abatement matching",
            ),

            GlobalConstraint(
                lambda m, t: (
                    m.CE_carbonprice[t]
                    >= global_MAC_industry_CE(m.emissions_industry_global_relative_reduction_from_CE[t], m, t)
                    # currently not exactly assigned but calculated as bigger or equal, having the effect that the model may choose CE carbon prices
                    # that are higher than the MAC curve would suggest (it should minimize them nevertheless)
                ),
                "CE carbonprice industry",
            ),

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
                    (
                        sum(m.L(m.year(t), r) * m.carbonprice[t, r] for r in m.regions)
                        / sum(m.L(m.year(t), x) for x in m.regions)
                    )
                    # m.carbonprice[t, "USA"]
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
        return conversion_factor * (100 / mid_point) * (a - mid_point) # max price = 100 USD/tCO2, min price = 0 USD/tCO2, piecewise linear function with cost starting at mid-point of abatement curve
        # return conversion_factor * ((100 / m.CE_max_abatement[t]) * a) # max price = 100 USD/tCO2, min price = 0 USD/tCO2
        # return conversion_factor * ((200 / m.CE_max_abatement[t]) * a - 100) # max price = 100 USD/tCO2, min price = -100 USD/tCO2

def global_AC_industry_CE(a, m, t):
    conversion_factor = 1.0508474576271185 / 1000 #conversion factor from 2015Euro to 2005USD & conversion from USD/tCO2 to trillion USD/Gt CO2

    #based on Material Economics abatement curve, adjusted to 2005USD
    if m.high_CE_cost:
        return conversion_factor * (200 / m.CE_max_abatement[t]) * a ** (1 + 1) / (1 + 1) # high cost scenario: max price = 200 USD/tCO2, min price = 0 USD/tCO2
    else:
        mid_point = m.CE_max_abatement[t] / 2
        return conversion_factor * (100 / mid_point) * (a ** (1 + 1) / (1 + 1) - mid_point * a ** (0 + 1) / (0 + 1)) # max price = 100 USD/tCO2, min price = 0 USD/tCO2, piecewise linear function with cost starting at mid-point of abatement curve
        # return conversion_factor * (100 / m.CE_max_abatement[t]) * a ** (1 + 1) / (1 + 1) # max price = 100 USD/tCO2, min price = 0 USD/tCO2
        # return conversion_factor * ((200 / m.CE_max_abatement[t]) * a ** (1 + 1) / (1 + 1) - 100 * a ** (0 + 1) / (0 + 1)) # max price = 100 USD/tCO2, min price = -100 USD/tCO2
