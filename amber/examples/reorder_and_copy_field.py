import numpy as np
import sys
from glob import glob
import re
import os
import subprocess


num_for_test = 3

all_model_filenames = glob('/pscratch/sd/d/doughty/emuinf/reionization_fields/IC*')  # the fields (no mention of DT)

prefix = 'nyx_cdm_256_v30_20Mpc_zreion_amber_'
counter = 0
for model_filename in all_model_filenames:

    # Checking and updating the counter limit (arbitrary)
    if counter >= num_for_test:
        print('\nFinished set for testing.\n')
        sys.exit()

    # Find the grid size
    Ngrid = int(re.findall(r'\d+', re.findall(r'_hii\d+_', model_filename)[0])[0])

    # Full output filepath, minus the DT parameter.
    missing_DT_output_filepath = f"/pscratch/sd/d/doughty/emuinf/grid/{prefix}{model_filename.split('/')[-1][:-6]}"  # strip the _20Mpc off the end

    # Find all partial matches for the parameter combination
    full_output_filepath = glob(f'{missing_DT_output_filepath}*')

    # Skip parameter combination if there are multiple matches (means too much ambiguity in naming convention)
    if len(full_output_filepath) > 1:
        print('Found multiple possible paths for', missing_DT_output_filepath, '....Skipping.')
        continue
    else:
        full_output_filepath = full_output_filepath[0]



    if os.path.exists(f"{full_output_filepath}/zhi.bin"):
        continue
    else:
        # Load the binary files from reionization_fields in AMBER native (Fortran, column-row) order
        field = np.fromfile(model_filename, dtype=np.float32)

        # Reshaping, accounting for the Fortran ordering    
        field_3d = field.reshape((Ngrid,Ngrid,Ngrid), order='F')

        # Saving in C order for converter
        field_3d.flatten(order='C').astype(np.float32).tofile(f"{full_output_filepath}/zhi.bin")
        print(f'\nSaved file {full_output_filepath}/zhi.bin\n')
    
    if not os.path.exists(f"{full_output_filepath}/zhi"):
        print('\nMaking the zhi directory.\n')
        os.makedirs(f"{full_output_filepath}/zhi")

    if not os.path.exists(f"{full_output_filepath}/zhi_D_00000"):
        print('\nCall the zhi file converter.\n')
        os.chdir(f"{full_output_filepath}")
        subprocess.call(["/pscratch/sd/d/doughty/Nyx/Util/zhi_converter/main3d.gnu.x86-milan.TPROF.MPI.ex.128"])
        os.rename(f"{full_output_filepath}/zhi/zhi_D_00000", f"{full_output_filepath}/zhi_D_00000")
        os.rename(f"{full_output_filepath}/zhi/zhi_H", f"{full_output_filepath}/zhi_H")
        counter += 1
    print('\nCounter', counter, '\n')
    #sys.exit()
