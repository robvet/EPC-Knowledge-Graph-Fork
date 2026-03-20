import sys
from src.data.seed import seed
from src.workflows.simulations import SIMULATIONS

g = seed()

for sim_id, sim in SIMULATIONS.items():
    print(f"\n--- Running {sim_id} ---")
    try:
        res = sim["run"]("PRJ-001")
        print("SUCCESS:", res['scenario'])
    except Exception as e:
        import traceback
        traceback.print_exc()
