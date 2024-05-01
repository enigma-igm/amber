import numpy as np
import sys
from glob import glob
import re
import os
import subprocess


num_for_test = 10

all_model_filenames = glob('/pscratch/sd/d/doughty/emuinf/reionization_fields/IC*')  # the fields (no mention of DT)

prefix = 'nyx_cdm_128_v30_20Mpc_zreion_amber_'
counter = 0
for model_filename in all_model_filenames:
    if counter >= num_for_test:
        print('\nFinished set for testing.\n')
        sys.exit()
    else:
        counter += 1
    Ngrid = int(re.findall(r'\d+', re.findall(r'_hii\d+_', model_filename)[0])[0])  # find the grid size
    field = np.fromfile(model_filename, dtype=np.float32)  # load the binary files from reionization_fields in Fortran (column-row) order
    #output_dir = re.findall(r'\S+_hii\d+', model_filename)[0]  # where the file gets saved
    missing_DT_output_filepath = f"/pscratch/sd/d/doughty/emuinf/grid/{prefix}{model_filename.split('/')[-1][:-6]}"  # strip the _20Mpc off the end
    full_output_filepath = glob(f'{missing_DT_output_filepath}*')
    if len(full_output_filepath) > 1:
        print('Found multiple possible paths for', missing_DT_output_filepath)
        continue
    else:
        full_output_filepath = full_output_filepath[0]
    field_3d = field.reshape((Ngrid,Ngrid,Ngrid), order='F')  # reshaping, accounting for the Fortran ordering
    field_3d.flatten(order='C').astype(np.float32).tofile(f"{full_output_filepath}/zhi.bin")  # saving in C order for converter
    if not os.path.exists(f"{full_output_filepath}/zhi"):
        os.makedirs(f"{full_output_filepath}/zhi")
    os.chdir(f"{full_output_filepath}")
    subprocess.call(["/pscratch/sd/d/doughty/Nyx/Util/zhi_converter/main3d.gnu.x86-milan.TPROF.MPI.ex.128"])
    os.rename(f"{full_output_filepath}/zhi/zhi_D_00000", f"{full_output_filepath}/zhi_D_00000")
    os.rename(f"{full_output_filepath}/zhi/zhi_H", f"{full_output_filepath}/zhi_H")

    sys.exit()
