"""
Model equations and constraints:
Damage and adaptation costs, RICE specification
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
    value,
    Any,
    exp,
)

from .ad_rice2012 import get_slr_constraints


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Damage and adaptation costs equations and constraints
    (COACCH specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs multiplied by gross GDP)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    # Sea level rise
    constraints.extend(get_slr_constraints(m))

    m.damage_costs = Var(m.t, m.regions)
    m.damage_scale_factor = Param()

    # Damages not related to SLR (dependent on temperature)
    m.resid_damages = Var(m.t, m.regions)

    m.damage_noslr_form = Param(m.regions, within=Any)  # String for functional form
    m.damage_noslr_b1 = Param(m.regions)
    m.damage_noslr_b2 = Param(m.regions)
    m.damage_noslr_b3 = Param(m.regions)
    # (b2 and b3 are only used for some functional forms)

    m.damage_noslr_a = Param(m.regions)

    # Quadratic damage function for non-SLR damages. Factor `a` represents
    # the damage quantile
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.resid_damages[t, r]
            == damage_fct(m.temperature[t], m.T0, m, r, is_slr=False),
            "resid_damages",
        )
    )

    # SLR damages
    m.SLR_damages = Var(m.t, m.regions)

    m.damage_slr_form = Param(m.regions, within=Any)  # String for functional form
    m.damage_slr_b1 = Param(m.regions)
    m.damage_slr_b2 = Param(m.regions)
    m.damage_slr_b3 = Param(m.regions)
    # (b2 and b3 are only used for some functional forms)

    m.damage_slr_a = Param(m.regions)

    # Linear damage function for SLR damages, including adaptation costs
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.SLR_damages[t, r]
            == damage_fct(m.total_SLR[t], None, m, r, is_slr=True),
            "SLR_damages",
        )
    )

    # Total damages are sum of non-SLR and SLR damages
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.damage_costs[t, r]
            == m.resid_damages[t, r] + m.SLR_damages[t, r],
            "damage_costs",
        ),
    )

    return constraints


#################
## Utils
#################


# Damage function


def functional_form(x, m, r, is_slr=False):
    if is_slr:
        form = m.damage_slr_form[r]
        b1, b2, b3 = m.damage_slr_b1[r], m.damage_slr_b2[r], m.damage_slr_b3[r]
        a = m.damage_slr_a[r]
    else:
        form = m.damage_noslr_form[r]
        b1, b2, b3 = m.damage_noslr_b1[r], m.damage_noslr_b2[r], m.damage_noslr_b3[r]
        a = m.damage_noslr_a[r]

    # Linear functional form
    if value(form) in ["Robust-Linear", "OLS-Linear"]:
        return a * b1 * x / 100.0

    # Quadratic functional form
    if value(form) in ["Robust-Quadratic", "OLS-Quadratic"]:
        return a * (b1 * x + b2 * x ** 2) / 100.0

    # Logistic functional form
    if value(form) in ["Robust-Logistic", "OLS-Logistic"]:
        return a * logistic(x, b1, b2, b3) / 100.0

    raise NotImplementedError


def damage_fct(x, x0, m, r, is_slr):
    # TODO COACCH damage functions are as function of 1980-2005 temperature, not PI
    damage = functional_form(x, m, r, is_slr)
    if x0 is not None:
        damage -= functional_form(x0, m, r, is_slr)

    return damage


def logistic(x, b1, b2, b3):
    return b1 / (1 + b2 * exp(-b3 * x)) - b1 / (1 + b2)
