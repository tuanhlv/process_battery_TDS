import os
import pytest
import pandas as pd
from analytics import extract_temperature_columns, plot_rate_charge, plot_rate_discharge, plot_temperature_perf
from unittest.mock import patch


# ====================================================================================
# 1. Test temperature extraction from the raw csv
# ====================================================================================
@pytest.mark.parametrize(
    "csv_filename, expected_t1_first, expected_t2_first",
    [
        ("test_arbin_8.csv", 26.2, None),       # CSV 1: Contains an 'T_..._interp' column
        ("test_arbin_7.csv", 23.4, None),       # CSV 2: Contains an 'X' column
        ("test_neware9.csv", 26.0, 24.9),       # CSV 3: Contains 'T1' and 'T2'
        ("test_PT.csv", None, None),            # CSV 4: No temperature columns at all
        ("test_corrupted.csv", 20.0, None),     # CSV 5: Has text in T1, should fallback to X
    ]
)
def test_temperature_extraction(csv_filename, expected_t1_first, expected_t2_first):
    csv_path = os.path.join("tests", csv_filename)
    assert os.path.exists(csv_path), f"Test file missing: {csv_path}"  # Fail immediately with a clear error if the dummy CSV is missing 
    df_input = pd.read_csv(csv_path)
    df_result = extract_temperature_columns(df_input)
    
    # Compare the first row's value to expected values
    
    # Check T1
    if expected_t1_first is None:
        assert df_result['Temperature1'].isnull().all(), f"T1 should be all NaN in {csv_filename}"
    else:
        res_t1_first = df_result['Temperature1'].iloc[0]
        assert res_t1_first == expected_t1_first, f"T1 mismatch in {csv_filename}. Expected {expected_t1_first}, got {res_t1_first}"

    # Check T2
    if expected_t2_first is None:
        assert df_result['Temperature2'].isnull().all(), f"T2 should be all NaN in {csv_filename}"
    else:
        res_t2_first = df_result['Temperature2'].iloc[0]
        assert res_t2_first == expected_t2_first, f"T2 mismatch in {csv_filename}. Expected {expected_t2_first}, got {res_t2_first}"
        
    # Ensure the original dataframe wasn't mutated
    assert 'Temperature1' not in df_input.columns, "Original DataFrame was incorrectly modified in place"


# ====================================================================================
# 2. Test Input Validation and Exceptions:
#    plot_rate_charge, plot_rate_discharge,
#    plot_temperature_perf
# ====================================================================================
@pytest.mark.parametrize(
    "cycles_str, rates, expected_error_msg",
    [
        # Scenario 1: Mismatched lengths (3 cycles, 2 rates)
        ("1, 2, 3", "0.2, 0.5", "Cycle numbers count must match rates count."),
        
        # Scenario 2: Mismatched lengths (2 cycles, 3 rates)
        ("1, 2", "0.2, 0.5, 1.0", "Cycle numbers count must match rates count."),
        
        # Scenario 3: Missing reference 0.2 rate
        # Note: Lengths match, but 0.2 is missing
        ("1, 2", "0.5, 1.0", "Reference C-rate 0.2 not found in the input list."),
        
        # Scenario 4: Empty inputs
        ("", "", "Reference C-rate 0.2 not found in the input list."),
    ]
)

def test_rate_inputs(cycles_str, rates, expected_error_msg):
    with pytest.raises(ValueError) as exc1_info:
        plot_rate_charge(
            csv_file_path="fake_path.csv", 
            cycle_numbers_str=cycles_str, 
            rates_str=rates,
            png_path1="fake1.png", 
            png_path2="fake2.png",
            csv_res_path="fake_res.csv",
            processed_folder="fake_folder", 
        )
    assert expected_error_msg in str(exc1_info.value)
    
    with pytest.raises(ValueError) as exc2_info:
        plot_rate_discharge(
            csv_file_path="fake_path.csv", 
            cycle_numbers_str=cycles_str, 
            rates_str=rates,
            png_path1="fake1.png", 
            png_path2="fake2.png",
            csv_res_path="fake_res.csv",
            processed_folder="fake_folder"
        )
    assert expected_error_msg in str(exc2_info.value)
    

@pytest.mark.parametrize(
    "cycles_str, temp_str, expected_error_msg",
    [
        # Scenario 1: Mismatched lengths (3 cycles, 2 temperatures)
        ("1, 2, 3", "20, 30", "Cycles count must match temperatures count."),
        
        # Scenario 2: Mismatched lengths (2 cycles, 3 temperatures)
        ("1, 2", "20, 30, 40", "Cycles count must match temperatures count."),
        
        # Scenario 3: Missing reference 20C
        ("1, 2", "30, 40", "Reference temperature 20°C not found."),
        
        # Scenario 4: Empty inputs
        ("", "", "Reference temperature 20°C not found."),
    ]
)

def test_hlt_inputs(cycles_str, temp_str, expected_error_msg):
    with pytest.raises(ValueError) as exc_info:
        plot_temperature_perf(
            csv_file_path="fake_path.csv", 
            cycle_numbers_str=cycles_str, 
            temperatures_str=temp_str,
            png_path1="fake1.png", 
            png_path2="fake2.png", 
            processed_folder="fake_folder", 
            csv_res_path="fake_res.csv"
        )
    assert expected_error_msg in str(exc_info.value)
    


# ====================================================================================
# 3. Test Handling of Missing/Empty Cycles:
#    plot_rate_charge
#    plot_discharge_rate
# ====================================================================================

# Use @patch to intercept saving csv files and figures
@patch("analytics.charge.pd.DataFrame.to_csv")
@patch("analytics.charge.plt.Figure.savefig")

def test_missing_cycles():
    rawcsv_fn = "test_missing_cycle.csv"
    rawcsv_path = os.path.join("tests", rawcsv_fn)
    assert os.path.exists(csv_path), f"Test file missing: {csv_path}"  # Fail immediately with a clear error if the dummy CSV is missing 
    cycles = "1, 7"
    rates = "0.2, 10"
    
    plot_rate_charge(
            csv_file_path=rawcsv_path, 
            cycle_numbers_str=cycles, 
            rates_str=rates,
            png_path1="fake1.png", 
            png_path2="fake2.png",
            csv_res_path="fake_res.csv",
            processed_folder="fake_folder", 
        )
    assert mock_savefig.call_count == 2, "Processed cycle 1, succesfully skipped cycle 7 -> Expected savefig to be called twice"