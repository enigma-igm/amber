import subprocess
from glob import glob
import os
import sys
import shutil
import numpy as np
from IPython import embed


def find_redshift_of_pltfile(runlog_dirpath, pltfile):
    pltnumber, redshift = np.loadtxt(f"{runlog_dirpath}/runlog", usecols=(0,3), unpack=True, dtype=str)
    search_string = str(pltfile[3:].lstrip('0'))
    index = list(pltnumber).index(search_string)
    return f'{float(redshift[index]):.1f}', search_string


def run_hdf5_converter(grid_directory_path, target_successes, template_input_file):

    sim_dirs = glob(f'{grid_directory_path}/nyx*')
    sim_dirs.sort()  # to keep the order consistent

    success_counter = 0

    for directory in sim_dirs:
        
        if success_counter >= target_successes:
            print(f"\nInitiated {target_successes} runs.\n")
            sys.exit()

        model_name = directory.split('/')[-1]
        hdf5list = glob(f"{directory}/*.hdf5")
        convert_files = glob(f"{directory}/Convert.o*")

        if os.path.exists(f'{directory}/CONVERT_JOB_SUBMITTED'):
            continue

        if (len(hdf5list) > 0) or (len(convert_files) > 0):  # there are hdf5 or Convert.ofiles, so continue
            print(f'\nFound hdf5/Convert files in {model_name}, so continuing to avoid overwrite.\n')
            continue
        else:
            pltfiles = glob(f"{directory}/plt*")
            print(f'\nFound {len(pltfiles)} pltfiles in dir {directory}.')
            if not len(pltfiles) > 0:  # if there are no pltfiles, the simulation hasn't been run yet, so skip.
                continue
            print('Running on model', model_name)
            for entry in pltfiles:
                success_counter += 1
                pltfilename = entry.split('/')[-1]
                redshift, snapnumber = find_redshift_of_pltfile(directory, pltfilename)
                shutil.copy(template_input_file, f"{directory}/run_converter_{snapnumber}.saul")  # overwrites any existing "_{snapnumber}.saul file
                subprocess.Popen(['touch', f'{directory}/CONVERT_JOB_SUBMITTED'])
                with open(f"{directory}/run_converter_{snapnumber}.saul", 'a') as f:

                    f.write(f'srun --cpu_bind=cores /pscratch/sd/d/doughty/convert3d.gnu.x86-milan.PROF.MPI.ex input_path={directory}/{pltfilename} output_path={directory}/{model_name}_cicass_z{redshift}0.hdf5')
                    f.write('\n')

                    f.write('date "+%Y-%m-%d_%H:%M:%S"\n')
                    f.close()
                os.chdir(f"{directory}")
                subprocess.Popen(['sbatch', f'run_converter_{snapnumber}.saul'])


# first run before timing checks
# make the .saul files for converter, and call sbatch on the script
run_hdf5_converter('/pscratch/sd/d/doughty/emuinf/grid', target_successes=30, template_input_file='/pscratch/sd/d/doughty/emuinf/templates/run_converter_template.saul')
sys.exit()
from time import time

total_time_hr = 2.0  # in hours
total_time_sec = total_time_hr * 60.0 * 60.0  # in seconds

start = time()

current_runtime = time() - start

while current_runtime < total_time_sec:

    p = subprocess.Popen(['squeue', '-u', 'doughty'], stdout=subprocess.PIPE)

    out, err = p.communicate()

    result = out.decode('utf-8').split()

    # jobs in the queue
    user_instances = result.count('doughty')

    if user_instances < 22:  # one sim has finished
        run_hdf5_converter('/pscratch/sd/d/doughty/emuinf/grid', target_successes=11, template_input_file='/pscratch/sd/d/doughty/emuinf/templates/run_converter_template.saul')
    # update elapsed time
    current_runtime = time() - start

