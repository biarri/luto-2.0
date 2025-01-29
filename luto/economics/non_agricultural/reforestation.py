"""
Pure functions to calculate water net yield by lm, lu and water limits.
"""

import re
import numpy as np
import pandas as pd
from collections import defaultdict
from itertools import pairwise
from typing import Optional


import luto.settings as settings
from luto.data import Data, ReforestationNetYieldLimit
from luto.economics.agricultural.quantity import get_yield_pot, lvs_veg_types
import luto.economics.non_agricultural.water as non_ag_water


def get_reforestation_net_yield_limit_values(
    data: Data,
) -> dict[int, ReforestationNetYieldLimit]:
    """
    Return reforestation net yield limits for regions (River Regions or Drainage Divisions as specified in luto.settings.py).

    Parameters:
    - data: The data object containing the necessary input data.

    Returns:
    reforestation_net_yield_limits: dict[int, ReforestationNetYieldLimit]

    Raises:
    - None

    """

    limits_by_region = {}

    return limits_by_region
