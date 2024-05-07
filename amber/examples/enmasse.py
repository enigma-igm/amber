import numpy as np
import sys
from glob import glob
import re
import os
import subprocess
import shutil


def find_redshift_of_pltfile(runlog_dirpath, pltfile):
    pltnumber, redshift = np.loadtxt(f"{runlog_dirpath}/runlog", usecols=(0,3), unpack=True, dtype=str)
    search_string = str(pltfile[3:].lstrip('0'))
    index = list(pltnumber).index(search_string)
    return f'{float(redshift[index]):.1f}', search_string


def convert_reion_field(reion_fields_dir, reion_fields_prefix, sim_dir, sim_prefix, cap=10):
    """
        Converts the given AMBER-format reionization field to the format required by Nyx.
        Checks all directories for zhi.bin and copy the reionization field to them if not present. Calls
        the zhi file converter to get the zhi_D_00000 and zhi_H files.

        Inputs:
                reion_fields_dir: Containing directory for all the reionization field binary files.
                reion_fields_prefix: Common text prefix for all the reionization field binary files
                                     (avoid any other files in dir.)
                sim_dir: Containing directory for all the individual simulation directories.
                sim_prefix: Prefix with the simulation details (e.g. 'nyx_cdm_128_v30_20Mpc_zreion_amber_')
                cap: Number of directories to populate before stopping.

        Returns:

    """

    all_model_filenames = glob(f'{reion_fields_dir}/{reion_fields_prefix}*')

    counter = 0
    for model_filename in all_model_filenames:

        # Checking and updating the counter limit (arbitrary)
        if counter >= cap:
            print('\nFinished set for testing.\n')
            sys.exit()

        # Find the grid size
        Ngrid = int(re.findall(r'\d+', re.findall(r'_hii\d+_', model_filename)[0])[0])

        # Full output filepath, minus the DT parameter.
        missing_DT_output_filepath = f"{sim_dir}/{sim_prefix}{model_filename.split('/')[-1][:-6]}"  # strip the _20Mpc off the end

        # Find all partial matches for the parameter combination
        full_output_filepath = glob(f'{missing_DT_output_filepath}*')

        # Skip parameter combination if there are multiple matches (means too much ambiguity in naming convention)
        if len(full_output_filepath) > 1:
            print('Found multiple possible paths for', missing_DT_output_filepath, '....Skipping.')
            continue
        else:
            full_output_filepath = full_output_filepath[0]

        # Checking for/adding the zhi.bin file.
        if os.path.exists(f"{full_output_filepath}/zhi.bin"):
            continue
        else:
            # Load the binary files from reionization_fields in AMBER native (Fortran, column-row) order
            field = np.fromfile(model_filename, dtype=np.float32)

            # Reshaping, accounting for the Fortran ordering
            field_3d = field.reshape((Ngrid, Ngrid, Ngrid), order='F')

            # Saving in C order for converter
            field_3d.flatten(order='C').astype(np.float32).tofile(f"{full_output_filepath}/zhi.bin")
            print(f'\nSaved file {full_output_filepath}/zhi.bin\n')

        # Checking for/adding the zhi directory.
        if not os.path.exists(f"{full_output_filepath}/zhi"):
            print('\nMaking the zhi directory.\n')
            os.makedirs(f"{full_output_filepath}/zhi")

        # Checking for zhi_D_00000 and zhi_H files and calling the zhi file converter if not present.
        if not os.path.exists(f"{full_output_filepath}/zhi_D_00000"):
            print('\nCall the zhi file converter.\n')
            os.chdir(f"{full_output_filepath}")
            subprocess.call(["/pscratch/sd/d/doughty/Nyx/Util/zhi_converter/main3d.gnu.x86-milan.TPROF.MPI.ex.128"])
            os.rename(f"{full_output_filepath}/zhi/zhi_D_00000", f"{full_output_filepath}/zhi_D_00000")
            os.rename(f"{full_output_filepath}/zhi/zhi_H", f"{full_output_filepath}/zhi_H")
            counter += 1


def submit_sim_job(sim_dir, sim_prefix, cap=10):

    sim_dirs = glob(f'{sim_dir}/{sim_prefix}*')

    counter = 0
    for directory in sim_dirs:
        print('Calls', counter)
        if counter >= cap:
            print(f"\nInitiated {cap} runs, as requested.\n")
            sys.exit()

        # first check if the reion. field is converted to correct format
        if not os.path.exists(f"{directory}/zhi_H"):
            continue

        pltlist = glob(f"{directory}/plt*")
        # second check if there are already plt files
        if len(pltlist) > 0:
            continue
        else:
            shutil.copyfile('/pscratch/sd/d/doughty/emuinf/templates/run_nyx.saul', f"{directory}/run_nyx.saul")
            os.chdir(f"{directory}")
            subprocess.Popen(['sbatch', 'run_nyx.saul'])
            print(f"\nRunning the job in directory {directory}.\n")
            counter += 1


def submit_convert_job(sim_dir, sim_prefix, template_input_file, exe_path, cap=10):
    sim_dirs = glob(f'{sim_dir}/{sim_prefix}*')
    sim_dirs.sort()  # to keep the order consistent

    counter = 0

    for directory in sim_dirs:

        if counter >= cap:
            print(f"\nInitiated {cap} runs.\n")
            sys.exit()

        model_name = directory.split('/')[-1]
        hdf5list = glob(f"{directory}/*.hdf5")
        if len(hdf5list) > 0:  # there are hdf5 files, so continue
            print(f'\nFound hdf5files in {model_name}, so continuing to avoid overwrite.\n')
            continue
        else:
            pltfiles = glob(f"{directory}/plt*")
            print(f'\nFound {len(pltfiles)} pltfiles in dir {directory}.')
            if not len(pltfiles) > 0:
                continue
            print('Running on model', model_name)
            for entry in pltfiles:
                counter += 1
                pltfilename = entry.split('/')[-1]
                redshift, snapnumber = find_redshift_of_pltfile(directory, pltfilename)
                shutil.copy(template_input_file,
                            f"{directory}/run_converter_{snapnumber}.saul")  # overwrites any existing "_{snapnumber}.saul file
                with open(f"{directory}/run_converter_{snapnumber}.saul", 'a') as f:
                    f.write(
                        f'srun --cpu_bind=cores {exe_path}/convert3d.gnu.x86-milan.PROF.MPI.ex '
                        f'input_path={directory}/{pltfilename} output_path={directory}/{model_name}_cicass_'
                        f'z{redshift}0.hdf5')
                    f.write('\n')

                    f.write('date "+%Y-%m-%d_%H:%M:%S"\n')
                    f.close()
                os.chdir(f"{directory}")
                subprocess.Popen(['sbatch', f'run_converter_{snapnumber}.saul'])


convert_reion_field('/pscratch/sd/d/doughty/emuinf/reionization_fields', 'IC',
                    '/pscratch/sd/d/doughty/emuinf/grid', 'nyx_cdm_128_v30_20Mpc_zreion_amber_')

submit_sim_job('/pscratch/sd/d/doughty/emuinf/grid', 'nyx')

submit_convert_job('/pscratch/sd/d/doughty/emuinf/grid', 'nyx',
                   template_input_file='/pscratch/sd/d/doughty/emuinf/templates/run_converter_template.saul',
                   exe_path='/pscratch/sd/d/doughty')