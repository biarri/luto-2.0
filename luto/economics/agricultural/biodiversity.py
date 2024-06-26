"""
Pure functions to calculate biodiversity by lm, lu.
"""


import itertools
import numpy as np

from luto import settings
from luto.ag_managements import AG_MANAGEMENTS_TO_LAND_USES
from luto.data import Data


def get_non_penalty_land_uses(data: Data) -> list[int]:
    """
    Return a list of land uses that contribute to biodiversity output without penalty.

    Parameters:
    - data: The input data containing land use information.

    Returns:
    - A list of land use indices.
    """
    return list(set(data.LU_NATURAL) - set(data.LU_LVSTK_INDICES))  # returns [23], the index of Unallocated - natural land index


def get_livestock_natural_land_land_uses(data: Data) -> list[int]:
    """
    Return a list of land uses that contribute to biodiversity but are penalised as per the 
    BIODIV_LIVESTOCK_IMPACT setting (i.e., livestock on natural land).

    Parameters:
    - data: The input data containing land use information.

    Returns:
    - A list of land use codes.
    """

    return list(set(data.LU_NATURAL) & set(data.LU_LVSTK_INDICES)) # returns [2, 6, 15], Beef, Dairy, Sheep on natural land


def get_breq_matrices(data):
    """
    Return b_mrj biodiversity score matrices by land management, cell, and land-use type.

    Parameters:
    - data: The data object containing information about land management, cells, and land-use types.

    Returns:
    - np.ndarray.
    """
    b_mrj = np.zeros((data.NLMS, data.NCELLS, data.N_AG_LUS))

    biodiv_non_penalty_lus = get_non_penalty_land_uses(data)
    livestock_nat_land_lus = get_livestock_natural_land_land_uses(data)

    for j in biodiv_non_penalty_lus:
        b_mrj[:, :, j] = data.BIODIV_SCORE_WEIGHTED_LDS_BURNING * data.REAL_AREA

    # if settings.BIODIV_LIVESTOCK_IMPACT > 0:
    for j in livestock_nat_land_lus:
        b_mrj[:, :, j] = ( data.BIODIV_SCORE_WEIGHTED_LDS_BURNING -                       # Base biodiversity score considering assumed late-dry season burning
                          (data.BIODIV_SCORE_WEIGHTED * settings.BIODIV_LIVESTOCK_IMPACT) # Minus impact of livestock on biodiversity value
                         ) * data.REAL_AREA
    
    return b_mrj


def get_asparagopsis_effect_b_mrj(data: Data):
    """
    Gets biodiversity impacts of using Asparagopsis taxiformis (no effect)

    Parameters:
    - data: The input data object containing NLMS and NCELLS attributes.

    Returns:
    - An array of zeros with shape (data.NLMS, data.NCELLS, nlus).
    """
    nlus = len(AG_MANAGEMENTS_TO_LAND_USES["Asparagopsis taxiformis"])
    return np.zeros((data.NLMS, data.NCELLS, nlus))


def get_precision_agriculture_effect_b_mrj(data: Data):
    """
    Gets biodiversity impacts of using Precision Agriculture (no effect)

    Parameters:
    - data: The input data object containing NLMS and NCELLS information

    Returns:
    - An array of zeros with shape (data.NLMS, data.NCELLS, nlus)
    """
    nlus = len(AG_MANAGEMENTS_TO_LAND_USES["Precision Agriculture"])
    return np.zeros((data.NLMS, data.NCELLS, nlus))


def get_ecological_grazing_effect_b_mrj(data: Data):
    """
    Gets biodiversity impacts of using Ecological Grazing (no effect)

    Parameters:
    - data: The input data object containing information about NLMS and NCELLS.

    Returns:
    - An array of zeros with shape (NLMS, NCELLS, nlus)
    """
    nlus = len(AG_MANAGEMENTS_TO_LAND_USES["Ecological Grazing"])
    return np.zeros((data.NLMS, data.NCELLS, nlus))


def get_savanna_burning_effect_b_mrj(data):
    """
    Gets biodiversity impacts of using Savanna Burning.

    Land that can perform Savanna Burning but does not is penalised for not doing so.
    Thus, add back in the penalised amount to get the positive effect of Savanna
    Burning on biodiversity.

    Parameters:
    - data: The input data containing information about land management and biodiversity.

    Returns:
    - new_b_mrj: A numpy array representing the biodiversity impacts of using Savanna Burning.
    """
    nlus = len(AG_MANAGEMENTS_TO_LAND_USES["Savanna Burning"])
    new_b_mrj = np.zeros((data.NLMS, data.NCELLS, nlus))

    eds_sav_burning_biodiv_benefits = np.where( data.SAVBURN_ELIGIBLE, 
                                                (1 - settings.LDS_BIODIVERSITY_VALUE) * data.BIODIV_SCORE_WEIGHTED * data.REAL_AREA, 
                                                0
                                              )
    

    for m, j in itertools.product(range(data.NLMS), range(nlus)):
        new_b_mrj[m, :, j] = eds_sav_burning_biodiv_benefits

    return new_b_mrj


def get_agtech_ei_effect_b_mrj(data):
    """
    Gets biodiversity impacts of using AgTech EI (no effect)

    Parameters:
    - data: The input data object containing information about NLMS and NCELLS.

    Returns:
    - An array of zeros with shape (NLMS, NCELLS, nlus)
    """
    nlus = len(AG_MANAGEMENTS_TO_LAND_USES["AgTech EI"])
    return np.zeros((data.NLMS, data.NCELLS, nlus))


def get_agricultural_management_biodiversity_matrices(data: Data):
    """
    Calculate the biodiversity matrices for different agricultural management practices.

    Parameters:
    - data: The input data used for calculations.

    Returns:
    A dictionary containing the biodiversity matrices for different agricultural management practices.
    The keys of the dictionary represent the management practices, and the values represent the corresponding biodiversity matrices.
    """

    asparagopsis_data = get_asparagopsis_effect_b_mrj(data) if settings.AG_MANAGEMENTS['Asparagopsis taxiformis'] else 0
    precision_agriculture_data = get_precision_agriculture_effect_b_mrj(data) if settings.AG_MANAGEMENTS['Precision Agriculture'] else 0
    eco_grazing_data = get_ecological_grazing_effect_b_mrj(data) if settings.AG_MANAGEMENTS['Ecological Grazing'] else 0
    sav_burning_data = get_savanna_burning_effect_b_mrj(data) if settings.AG_MANAGEMENTS['Savanna Burning'] else 0
    agtech_ei_data = get_agtech_ei_effect_b_mrj(data) if settings.AG_MANAGEMENTS['AgTech EI'] else 0

    return {
        'Asparagopsis taxiformis': asparagopsis_data,
        'Precision Agriculture': precision_agriculture_data,
        'Ecological Grazing': eco_grazing_data,
        'Savanna Burning': sav_burning_data,
        'AgTech EI': agtech_ei_data,
    }


def get_biodiversity_limits(data: Data, yr_cal: int):
    """
    Calculate the biodiversity limits for a given year used as a constraint.

    The biodiversity score target timeline is specified in data.BIODIV_GBF_TARGET_2.

    Parameters:
    - data: The data object containing relevant information.
    - yr_cal: The calendar year for which to calculate the biodiversity limits.

    Returns:
    - The biodiversity limit for the given year.

    """

    return data.BIODIV_GBF_TARGET_2[yr_cal]
