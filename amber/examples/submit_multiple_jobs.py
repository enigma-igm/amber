import subprocess
from glob import glob
import os
import sys
import shutil

sim_dirs = glob('/pscratch/sd/d/doughty/emuinf/grid/nyx*')

target_successes = 3
success_counter = 0

for directory in sim_dirs:
    print('Calls', success_counter)
    if success_counter >= target_successes:
        print(f"\nInitiated {target_successes} runs.\n")
        sys.exit()

    # first check if the reion. field is converted to correct format
    if not os.path.exists(f"{directory}/zhi_H"):
        continue

    # check if the job to run nyx is already submitted
    if os.path.exists(f"{directory}/RUN_JOB_SUBMITTED"):
        continue

    pltlist = glob(f"{directory}/plt*")
    # second check if there are already plt files
    if len(pltlist) > 0:
        continue
    else:
        subprocess.Popen(['touch', f'{directory}/RUN_JOB_SUBMITTED'])
        shutil.copyfile('/pscratch/sd/d/doughty/emuinf/templates/run_nyx.saul', f"{directory}/run_nyx.saul")
        os.chdir(f"{directory}")
        subprocess.Popen(['sbatch', 'run_nyx.saul'])
        print(f"\nRunning the job in directory {directory}.\n")
        success_counter += 1

