"""Every project decision lives here as one setting.
Change a decision here, not inside the other files."""

# --- Device (decision F1) ---
DEVICE = "ibm_torino"          # 133-qubit Heron. ibm_kyoto was retired in Sep 2024.
TWO_QUBIT_GATE = "cz"          # Heron chips use CZ as their two-qubit gate.

# --- Delays, measured in calibration cycles crossed (decision F2) ---
DELAYS = [1, 2, 3, 7]

# --- Predictors (decisions D1, D2) ---
WINDOW = 5                     # how many past cycles the predictors look at
PENALTY = 1.0                  # stability method: average + PENALTY x swing

# --- Circuits (decision D4) ---
CIRCUITS = ["ghz5", "ghz8", "bv8"]

# --- Compiler and simulator (decisions D6, D7) ---
OPT_LEVEL = 2                  # Qiskit's default optimization level
SEED_TRANSPILE = 11            # fixed, so differences come from the strategy, not randomness
SHOTS = 4000
SEED_SIM = 3

# --- Data cleaning (decision D8) ---
ERR_CAP = 0.5                  # max allowed error; missing/broken values are set to this so the compiler avoids them
MISSING_T1 = 10e-6             # 10 microseconds: a "very bad qubit" stand-in for a missing T1

# --- Synthetic drift (decision D9 fallback). These are ASSUMPTIONS, replaced by real data later. ---
SYNTH_CYCLES = 20              # number of fake calibration cycles to generate
SYNTH_SEED = 7
SYNTH_PERSISTENCE = 0.6        # how much of last cycle's deviation carries over (0 = none, 1 = all)
SYNTH_VOL_MEDIAN = 0.15        # typical per-cycle swing of a qubit's error (in log units)
SYNTH_VOL_SPREAD = 0.8         # how different qubits are from each other in swinginess
SYNTH_JUMP_RATE = 0.05         # average chance per cycle of a sudden TLS-like jump
SYNTH_JUMP_MIN, SYNTH_JUMP_MAX = 3.0, 10.0   # a jump multiplies a qubit's errors by 3x to 10x

# --- Folders ---
SNAPSHOT_DIR = "snapshots"
RESULTS_DIR = "results"
PLOTS_DIR = "plots"
