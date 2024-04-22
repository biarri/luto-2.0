import luto.simulation as sim
from luto.tools.write import write_data
import pandas as pd

### Run this test from root folder of your code on solver server, i.e harrison/ or luto-2.0/

MASTER_OBJ_VALUE = 9.34790480e+05

 # TODO: When you would like to run this test reset these valu
PREV_OUTPUT_FP = 'luto/tests/regression_tests/current_output_data/2024_04_22__00_45_08_hard_mincost_RF3_P1e5_2010-2030_snapshot_4Mt'
CURRENT_OUTPUT_FP = 'luto/tests/regression_tests/current_output_data/2024_04_22__00_45_08_hard_mincost_RF3_P1e5_2010-2030_snapshot_4Mt'
TIMESTAMP = '2024_04_22__00_45_08'
PREV_TIMESTAMP = '2024_04_22__00_45_08'


def test_regression():
    # data = sim.load_data()
    # sim.run(data, 2010, 2030)
# 
    # assert round(data.obj_vals[2030],2) == MASTER_OBJ_VALUE

    # write_data(data, path=CURRENT_OUTPUT_FP) TODO: fix this up to write new data

    # assert all quantities in quantity_comparison.csv only differ by maximum 5% of their previous values.
    prev_quantity_comparrison_df = pd.read_csv(PREV_OUTPUT_FP + f'/out_2030/quantity_comparison_{PREV_TIMESTAMP}.csv')
    current_quantity_comparrison_df = pd.read_csv(CURRENT_OUTPUT_FP + f'/out_2030/quantity_comparison_{TIMESTAMP}.csv')

    quantity_comparrison_df = pd.DataFrame()

    quantity_comparrison_df = (
        (
            current_quantity_comparrison_df[['Prod_base_year (tonnes, KL)', 'Prod_targ_year (tonnes, KL)', 'Demand (tonnes, KL)', 'Prop_diff (%)']] - 
            prev_quantity_comparrison_df[['Prod_base_year (tonnes, KL)', 'Prod_targ_year (tonnes, KL)', 'Demand (tonnes, KL)', 'Prop_diff (%)']]
        ) / current_quantity_comparrison_df[['Prod_base_year (tonnes, KL)', 'Prod_targ_year (tonnes, KL)', 'Demand (tonnes, KL)', 'Prop_diff (%)']]
    ) * 100
    assert quantity_comparrison_df['Prod_base_year (tonnes, KL)'].between(-5,5).all()
    assert quantity_comparrison_df['Prod_targ_year (tonnes, KL)'].between(-5,5).all()
    assert quantity_comparrison_df['Demand (tonnes, KL)'].between(-5,5).all()

    # assert all prop_diff fields in quantity_comparison.csv are all > 0%.
    assert current_quantity_comparrison_df['Prop_diff (%)'].gt(0).all()

    # assert that two ghg scores are within 5% of eachother
    old_ghg_score_df = pd.read_csv(PREV_OUTPUT_FP + f'/out_2030/GHG_emissions_{PREV_TIMESTAMP}.csv')
    new_ghg_score_df = pd.read_csv(CURRENT_OUTPUT_FP + f'/out_2030/GHG_emissions_{TIMESTAMP}.csv')

    ghg_comparrison_df = (
        (
            old_ghg_score_df[['GHG_EMISSIONS_LIMIT_TCO2e', 'GHG_EMISSIONS_TCO2e']] - 
            new_ghg_score_df[['GHG_EMISSIONS_LIMIT_TCO2e', 'GHG_EMISSIONS_TCO2e']]
        ) / old_ghg_score_df[['GHG_EMISSIONS_LIMIT_TCO2e', 'GHG_EMISSIONS_TCO2e']]
    ) * 100

    assert ghg_comparrison_df['GHG_EMISSIONS_LIMIT_TCO2e'].between(-5,5).all()
    assert ghg_comparrison_df['GHG_EMISSIONS_TCO2e'].between(-5,5).all()

    # assert that two biodiversity scores are within 5% of eachother
    old_bd_score_df = pd.read_csv(PREV_OUTPUT_FP + f'/out_2030/biodiversity_{PREV_TIMESTAMP}.csv')
    new_bd_score_df = pd.read_csv(CURRENT_OUTPUT_FP + f'/out_2030/biodiversity_{TIMESTAMP}.csv')

    bd_comparrison_df = (
        (
            old_bd_score_df[['Biodiversity score limit', 'Solve biodiversity score (2030)']] - 
            new_bd_score_df[['Biodiversity score limit', 'Solve biodiversity score (2030)']]
        ) / old_bd_score_df[['Biodiversity score limit', 'Solve biodiversity score (2030)']]
    ) * 100
    
    assert ghg_comparrison_df['Biodiversity score limit'].between(-5,5).all()
    assert ghg_comparrison_df['Solve biodiversity score (2030)'].between(-5,5).all()


    # assert that TOT_WATER_REQ_ML does not change by more than 10% for a new solve water_demand_vs_use
    old_water_demand_use_score_df = pd.read_csv(PREV_OUTPUT_FP + f'/out_2030/water_demand_vs_use_{PREV_TIMESTAMP}.csv')
    new_water_demand_use_score_df = pd.read_csv(CURRENT_OUTPUT_FP + f'/out_2030/water_demand_vs_use_{TIMESTAMP}.csv')

    water_demand_use_comparrison_df = (
        (
            old_water_demand_use_score_df['WATER_USE_LIMIT_ML'] - 
            new_water_demand_use_score_df['WATER_USE_LIMIT_ML']
        ) / old_water_demand_use_score_df['WATER_USE_LIMIT_ML']
    ) * 100

    assert water_demand_use_comparrison_df['WATER_USE_LIMIT_ML'].between(-10,10).all()

    breakpoint()

