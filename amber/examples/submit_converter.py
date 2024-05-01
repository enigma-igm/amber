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
        if len(hdf5list) > 0:  # there are hdf5 files, so continue
            print('\nfound hdf5files in', model_name, 'so continuing\n')
            continue
        else:
            pltfiles = glob(f"{directory}/plt*")
            print('\nfound', len(pltfiles), 'pltfiles in dir', directory)
            if len(pltfiles) > 0: success_counter += 1
            for entry in pltfiles:
                pltfilename = entry.split('/')[-1]
                print('running on model', model_name)
                print('on pltfile', entry)
                redshift, snapnumber = find_redshift_of_pltfile(directory, pltfilename)
                shutil.copy(template_input_file, f"{directory}/run_converter_{snapnumber}.saul")  # overwrites any existing "_{snapnumber}.saul file
                with open(f"{directory}/run_converter_{snapnumber}.saul", 'a') as f:

                    f.write(f'srun --cpu_bind=cores /pscratch/sd/d/doughty/convert3d.gnu.x86-milan.PROF.MPI.ex input_path={directory}/{pltfilename} output_path={directory}/{model_name}_cicass_z{redshift}0.hdf5')
                    f.write('\n')

                    f.write('date "+%Y-%m-%d_%H:%M:%S"\n')
                    f.close()

run_hdf5_converter('/pscratch/sd/d/doughty/emuinf/grid', target_successes=3, template_input_file='/pscratch/sd/d/doughty/emuinf/templates/run_converter_template.saul')
#find_redshift_of_pltfile('/pscratch/sd/d/doughty/emuinf/grid/nyx_cdm_128_v30_20Mpc_zreion_amber_IC128_zm10.0_Dz2.7_Az7.9_Mm1.0E+09_mfp3.0_hii128_DT2.6E+04', 'plt00356')
