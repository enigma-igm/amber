import subprocess
from glob import glob
import os
import sys
import shutil
import numpy as np
from IPython import embed

# TODO make run one queue job per sim, rather than per snapshot


def find_redshift_of_pltfile(runlog_dirpath, pltfile):
    pltnumber, redshift = np.loadtxt(f"{runlog_dirpath}/runlog", usecols=(0,3), unpack=True, dtype=str)
    search_string = str(pltfile[3:].lstrip('0'))
    index = list(pltnumber).index(search_string)
    return f'{float(redshift[index]):.1f}', search_string


def run_hdf5_converter(grid_directory_path, target_successes, template_input_file):

    sim_dirs = glob(f'{grid_directory_path}/nyx*')
    sim_dirs.sort()  # to keep the order consistent

    success_counter = 0
    last_job = None

    for directory in sim_dirs:
        
        if success_counter >= target_successes:
            print(f"\nInitiated {target_successes} runs.\n")
            sys.exit()

        model_name = directory.split('/')[-1]
        hdf5list = glob(f"{directory}/*.hdf5")
        convert_files = glob(f"{directory}/Convert.o*")

        if os.path.exists(f'{directory}/CONVERT_JOB_SUBMITTED'):
            continue

        if (len(hdf5list) > 0) or (len(convert_files) > 0):  # there are hdf5 (or Convert.ofiles if I've moved the hdf5 files elsewhere for transfer), so continue
            print(f'\nFound hdf5/Convert files in {model_name}, so continuing to avoid overwrite.\n')
            continue
        else:
            pltfiles = glob(f"{directory}/plt*")
            print(f'\nFound {len(pltfiles)} pltfiles in dir {directory}.')
            if not len(pltfiles) > 0:  # if there are no pltfiles, the simulation hasn't been run yet, so skip.
                continue
            print('Running on model', model_name)

            shutil.copy(template_input_file, f"{directory}/run_converter.saul")  # overwrites any existing ".saul file
            subprocess.Popen(['touch', f'{directory}/CONVERT_JOB_SUBMITTED'])

            zlist = []
            snaplist = []
            success_counter += 1
            for entry in pltfiles:
                pltfilename = entry.split('/')[-1]
                redshift, snapnumber = find_redshift_of_pltfile(directory, pltfilename)
                zlist.append(redshift)  # probably a one liner way to do this...
                snaplist.append(f"{int(snapnumber):05d}")

            snaplist_string = 'export pltlist=(' + ' '.join(snaplist) + ')'
            zlist_string = 'export zlist=(' + ' '.join(zlist) + ')'

            with open(f"{directory}/run_converter.saul", 'a') as f:  # appends new material to the end of the .saul file
                # defining env variables for the .saul file
                f.write(f'export dirpath="{directory}"')
                f.write('\n')
                f.write(f'export model="{model_name}"')
                f.write('\n')

                # making the loop for each snapshot

                f.write('export zlist=(' + ' '.join(zlist) + ')' + '\n\n')
                f.write('export pltlist=(' + ' '.join(snaplist) + ')' + '\n\n')
                        
                f.write('for i in "${!zlist[@]}"; do\n\n')

                f.write('    srun --cpu_bind=cores /pscratch/sd/d/doughty/convert3d.gnu.x86-milan.PROF.MPI.ex input_path=${dirpath}/plt${pltlist[$i]} output_path=${dirpath}/${model}_cicass_z${zlist[$i]}0.hdf5')
                f.write('\n\n')
                f.write('done\n\n')

                f.write('date "+%Y-%m-%d_%H:%M:%S"\n')
                f.close()
            os.chdir(f"{directory}")
            subprocess.Popen(['sbatch', f'run_converter.saul'])

# for each directory
# assign each plt snap number to a redshift
# make a run_converter.saul or whatever code that contains its own loop for each snap number



# make the .saul files for converter, and call sbatch on the script
run_hdf5_converter('/pscratch/sd/d/doughty/emuinf/grid', target_successes=1, template_input_file='/pscratch/sd/d/doughty/emuinf/templates/run_converter_template.saul')
