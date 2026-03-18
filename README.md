# QuickBase Battery Test Analytics

A Python suite designed to automate the end-to-end workflow of battery performance testing. This project integrates with the **QuickBase API** to fetch test metadata, processes raw battery log files (Arbin/Neware) stored locally, and generates comprehensive analytical reports including CSV summaries and high-fidelity visualizations.

## KEY FEATURES

* **QuickBase Integration:** Automated querying of Cell Test and Cell Part tables to synchronize metadata with local test files.
* **Comprehensive Battery Analytics:**
    * **Charge/Discharge Profiling:** Capacity and voltage analysis across varying C-rates.
    * **DCIR Analysis:** Direct Current Internal Resistance calculation at multiple pulse durations (1s, 10s, 30s, 60s).
    * **OCV vs. SOC:** Open Circuit Voltage mapping for state-of-charge characterization.
    * **Temperature Performance:** Comparative analysis of discharge curves across HLT (High/Low Temperature) ranges.
    * **Cycle Life Tracking:** Capacity retention and degradation plotting across long-term testing.
* **Technical Architecture:**
    * **Object-Oriented Design:** Modular classes for API interaction, data analysis, and pipeline orchestration.
    * **Robust Validation:** Utilizes **Pydantic** models for strict configuration and data schema enforcement.
    * **Advanced Python Patterns:** Implements Type Hinting, Decorators for error handling, Context Managers for logging, and List Comprehensions for efficient data transformation.

---

## TECHNICAL STACK

* **Language:** Python 3.9+
* **Data Processing:** `pandas`, `numpy`
* **Visualization:** `matplotlib`
* **Schema Validation:** `pydantic`
* **API Communication:** `requests`

---

## INSTALLATION

1. **Clone the repository:**
bash
   git clone https://github.com/tuanhlv/process_battery_TDS.git
   
2. **Install Dependencies:**
bash
   pip install pandas matplotlib requests pydantic numpy

## CONFIGURATION
The system uses a QuickBaseConfig model for authentication. Ensure your environment or script is configured with the correct credentials:
- token: Your QuickBase User Token
- hostnameYour QuickBase Realm URL (e.g., https://company.quickbase.com)
- test_table_ID: Target DB ID for Cell Tests
- cell_part_table_ID: Target DB ID for Cell Parts

## OUTPUT ARTIFACTS
- Plots: Saved as .png files (e.g., Charge_Profile.png, DCIR_vs_SOC.png).
- Processed Data: Cleaned and filtered .csv files for downstream modeling.
- Logs: scheduledProcessedLog.csv capturing all execution stages and errors.

## PROJECT STRUCTURE
- scheduleProcess.py: The entry point and pipeline orchestrator.
- BatteryAnalyzer: core class containing processing logic for battery physics.
- QuickBaseAPIClient: Handles authentication and payload formatting for the QuickBase JSON API.
- ExecutionLogger: Context manager for real-time process tracking.
   
