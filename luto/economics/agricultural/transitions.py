# Copyright 2022 Fjalar J. de Haan and Brett A. Bryan at Deakin University
#
# This file is part of LUTO 2.0.
#
# LUTO 2.0 is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# LUTO 2.0 is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# LUTO 2.0. If not, see <https://www.gnu.org/licenses/>.

"""
Data about transitions costs.
"""

import numpy as np
from typing import Dict

from luto.economics.agricultural.water import get_wreq_matrices
import luto.tools as tools


def get_exclude_matrices(data, base_year: int, lumaps: Dict[int, np.ndarray]):
    """Return x_mrj exclude matrices.

    An exclude matrix indicates whether switching land-use for a certain cell r 
    with land-use i to all other land-uses j under all land management types 
    (i.e., dryland, irrigated) m is possible. 

    Parameters
    ----------

    data: object/module
        Data object or module with fields like in `luto.data`.
    base_year: int
        Current base year of the solve.
    lumaps: dict[str, numpy.ndarray]
        All previously generated land-use maps (shape = ncells, dtype=int).

        
    Returns
    -------

    numpy.ndarray
        x_mrj exclude matrix. The m-slices correspond to the
        different land-management versions of the land-use `j` to switch _to_.
        With m==0 conventional dry-land, m==1 conventional irrigated.
    """    
    # Boolean exclusion matrix based on SA2/NLUM agricultural land-use data (in mrj structure).
    # Effectively, this ensures that in any SA2 region the only combinations of land-use and land management
    # that can occur in the future are those that occur in 2010 (i.e., YR_CAL_BASE)
    x_mrj = data.EXCLUDE

    # Raw transition-cost matrix is in $/ha and lexicographically ordered by land-use (shape = 28 x 28).
    t_ij = data.AG_TMATRIX

    lumap = lumaps[base_year]
    lumap_2010 = lumaps[2010]

    # Get all agricultural and non-agricultural cells
    ag_cells, non_ag_cells = tools.get_ag_and_non_ag_cells(lumap)
    
    # Transition costs from current land-use to all other land-uses j using current land-use map (in $/ha).
    t_rj = np.zeros((data.NCELLS, len(data.AGRICULTURAL_LANDUSES)))
    t_rj[ag_cells, :] = t_ij[lumap[ag_cells]]
    # For non-agricultural cells, use the original 2010 solve's LUs to determine what LUs are possible for a cell
    t_rj[non_ag_cells, :] = t_ij[lumap_2010[non_ag_cells]]

    # To be excluded based on disallowed switches as specified in transition cost matrix i.e., where t_rj is NaN.
    t_rj = np.where(np.isnan(t_rj), 0, 1)

    # Overall exclusion as elementwise, logical `and` of the 0/1 exclude matrices.
    x_mrj = (x_mrj * t_rj).astype(np.int8)
    
    return x_mrj


def get_transition_matrices(data, yr_idx, base_year, lumaps, lmmaps):
    """Return t_mrj transition-cost matrices.

    A transition-cost matrix gives the cost of switching a cell r from its 
    current land-use and land management type to every other land-use and land 
    management type. The base costs are taken from the raw transition costs in 
    the `data` module and additional costs are added depending on the land 
    management type (e.g. costs of irrigation infrastructure). 

    Parameters
    ----------

    data: object/module
        Data object or module with fields like in `luto.data`.
    yr_idx : int
        Number of years from base year, counting from zero.
    base_year: int
        The base year of the current solve.
    lumaps : dict[int, numpy.ndarray]
        All previously generated land-use maps (shape = ncells, dtype=int).
    lmmaps : dict[int, numpy.ndarray]
        ll previously generated land management maps (shape = ncells, dtype=int).

    Returns
    -------

    numpy.ndarray
        t_mrj transition-cost matrices. The m-slices correspond to the
        different land management types, r is grid cell, and j is land-use.
    """
    lumap = lumaps[base_year]
    lmmap = lmmaps[base_year]
    
    # Return l_mrj (Boolean) for current land-use and land management
    l_mrj = tools.lumap2ag_l_mrj(lumap, lmmap)

    ag_cells, non_ag_cells = tools.get_ag_and_non_ag_cells(lumap)

    n_ag_lms, ncells, n_ag_lus = data.AG_L_MRJ.shape


    # -------------------------------------------------------------- #
    # Establishment costs (upfront, amortised to annual, per cell).  #
    # -------------------------------------------------------------- #

    # Raw transition-cost matrix is in $/ha and lexigraphically ordered (shape: land-use x land-use).
    t_ij = data.AG_TMATRIX

    # Non-irrigation related transition costs for cell r to change to land-use j calculated based on lumap (in $/ha).
    # Only consider for cells currently being used for agriculture.
    t_rj = np.zeros((ncells, n_ag_lus))
    t_rj[ag_cells, :] = t_ij[lumap[ag_cells]]

    # Amortise upfront costs to annualised costs and converted to $ per cell via REAL_AREA
    t_rj = tools.amortise(t_rj) * data.REAL_AREA[:, np.newaxis]
    

    # -------------------------------------------------------------- #
    # Water license costs (upfront, amortised to annual, per cell).  #
    # -------------------------------------------------------------- #
    
    # Get water requirements from current agriculture, converting water requirements for LVSTK from ML per head to ML per cell (inc. REAL_AREA).
    w_mrj = get_wreq_matrices(data, yr_idx)
    
    # Sum total water requirements of current land-use and land management 
    w_r = (w_mrj * l_mrj).sum(axis = 0).sum(axis = 1)
    
    # Net water requirements calculated as the diff in water requirements between current land-use and all other land-uses j.
    w_net_mrj = w_mrj - w_r[:, np.newaxis]
    
    # Water license cost calculated as net water requirements (ML/ha) x licence price ($/ML).
    w_delta_mrj = w_net_mrj * data.WATER_LICENCE_PRICE[:, np.newaxis]
    
    # When land-use changes from dryland to irrigated add $10k per hectare for establishing irrigation infrastructure
    new_irrig_cost = 7500 * data.REAL_AREA[:, np.newaxis]
    w_delta_mrj[1] = np.where(l_mrj[0], w_delta_mrj[1] + new_irrig_cost, w_delta_mrj[1])

    # When land-use changes from irrigated to dryland add $3k per hectare for removing irrigation infrastructure
    remove_irrig_cost = 3000 * data.REAL_AREA[:, np.newaxis]
    w_delta_mrj[0] = np.where(l_mrj[1], w_delta_mrj[0] + remove_irrig_cost, w_delta_mrj[0])

    # Amortise upfront costs to annualised costs
    w_delta_mrj = tools.amortise(w_delta_mrj)


    # -------------------------------------------------------------- #
    # Total costs.                                                   #
    # -------------------------------------------------------------- #

    # Sum annualised costs of land-use and land management transition in $ per ha
    t_mrj = np.zeros((n_ag_lms, ncells, n_ag_lus))
    t_mrj[:, ag_cells, :] = w_delta_mrj[:, ag_cells, :] + t_rj[ag_cells, :] # + o_delta_mrj

    # Ensure cost for switching to the same land-use and land management is zero.
    t_mrj = np.where(l_mrj, 0, t_mrj)
    
    # Set costs to nan where transitions are not allowed
    x_mrj = get_exclude_matrices(data, base_year, lumaps)
    t_mrj = np.where(x_mrj == 0, np.nan, t_mrj)
    
    return t_mrj