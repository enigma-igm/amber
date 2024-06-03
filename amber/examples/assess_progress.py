from glob import glob
import sys
import numpy as np
from IPython import embed
import os


def find_missing_hdf5s(expected_hdf5s, expected_redshifts):
    os.chdir('/pscratch/sd/d/doughty/emuinf/grid')
    sim_directories = glob('nyx*')

    finished_flag = True
    for directory in sim_directories:
        matching_hdf5s = glob(f'hdf5s/{directory}*.hdf5')
        sample_count = len(matching_hdf5s)
        if sample_count < expected_hdf5s:
            finished_flag = False
            print('\nFound too few hdf5s in dir:', directory)
            try:
                found = set([float(x[-9:-5]) for x in matching_hdf5s])
                missing = expected_redshifts.difference(found)
                print('Missing these redshifts:', list(missing))
            except:
                embed(header='finding diff didnt work')
                sys.exit()
    if finished_flag:
        print('\nConversions to hdf5 are all done!\n')


def count_finished_sims(expected_plts):
    sim_directories = glob('/pscratch/sd/d/doughty/emuinf/grid/nyx*')

    total_output_count = 0
    for directory in sim_directories:
       pltfiles = glob(f'{directory}/plt*')
       sample_count = len(pltfiles)
       total_output_count += sample_count

       if sample_count < expected_plts:
           print(f'{directory.split("/")[-1]} is missing some outputs.')
       
    print('\n' + f'Found {total_output_count} pltfiles')
    runs_based_on_num_plts = total_output_count/expected_plts
    print(f'or {runs_based_on_num_plts} sims finished.' + '\n')


def count_hdf5_files():
    hdf5_list = glob('/pscratch/sd/d/doughty/emuinf/grid/hdf5s/*.hdf5')
    total_hdf5s = len(hdf5_list)
    print(f'Found {total_hdf5s} hdf5 files')
    print(f'or {total_hdf5s/11} sims finished')

count_finished_sims(11)
#count_hdf5_files()
find_missing_hdf5s(11, set(np.linspace(5.0, 6.0, 11)))
