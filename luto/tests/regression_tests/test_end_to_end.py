import luto.simulation as sim
from luto.tools.write import write_data

MASTER_OBJ_VALUE = 0


if __name__ == "__main__":
    data = sim.load_data()
    sim.run(data, 2010, 2030)

    assert data.obj_vals[2030] == MASTER_OBJ_VALUE

    write_data(data, path="luto/regression_tests/current_output_data")

    # assert all quantities in quantity_comparison.csv only differ by maximum 5% of their previous values.
    # assert all prop_diff fields in quantity_comparison.csv are all > 0%.
    # assert that two ghg scores are within 5% of eachother
    # assert that two biodiversity scores are within 5% of eachother
    # assert that TOT_WATER_REQ_ML does not change by more than 10% for a new solve water_demand_vs_use