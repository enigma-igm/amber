"""
    Code to make directories to hold Nyx+AMBER simulation output.
"""
import numpy as np
import os
from grid_run import read_reionization_parameters


if __name__ == '__main__':
    # example call:
    # python setup_simulation_grid.py --parameter_file input/model_params.txt
    # --simulation_directory_path ../../../processed/data_experiments/testdir
    # --template_input_file ../../../processed/data_experiments/template_inputs/template_inputs.txt
    # (optional, with default values) --Ngrid 256 --ics_Ngrid 128 --Lbox 20 --vbc 30 --hii_Ngrid 128
    import argparse

    values_dict = {'nyx.geometry.prob_hi':'', 'nyx.final_z':'', 'nyx.plot_z_values':'', 'nyx.inhomo_grid':'',
                   'amr.n_cell':'', 'nyx.reionization_T_zHI':''}
    parser = argparse.ArgumentParser(description='Make directories and copy/modify input files for AMBER+Nyx '
                                                 'reionization models.')
    parser.add_argument('--parameter_file', required=True,
                        help='Nyx+AMBER model parameter txt file name.', metavar='')
    parser.add_argument('--simulation_directory_path', metavar='', required=True,
                        help='Top level directory to hold the directories for simulation output.')
    parser.add_argument('--template_input_file', metavar='', required=True,
                        help='Filename of template inputs.txt file.')
    parser.add_argument('--Ngrid', metavar='', required=True, default=256,
                        help='Simulation grid size.')
    parser.add_argument('--ics_Ngrid', metavar='', required=True, default=128,
                        help='Gridsize of initial conditions to generate the reionization redshift field.')
    parser.add_argument('--Lbox', metavar='', required=True, default=20,
                        help='Domain size of the simulation/reionization redshift field.')
    parser.add_argument('--vbc', metavar='', required=True, default=30,
                        help='Streaming velocity used in initial conditions.')
    parser.add_argument('--hii_Ngrid', metavar='', required=True, default=128,
                        help='Gridsize of the reionization redshift field.')
    args = parser.parse_args()
    values_dict['amr.n_cell'] = '{:d} {:d} {:d}'.format(int(args.Ngrid), int(args.Ngrid), int(args.Ngrid))
    values_dict['nyx.geometry.prob_hi'] = '{:.6f}'.format(float(args.Lbox)/0.675)
    values_dict['nyx.inhomo_grid'] = '{:d}'.format(int(args.hii_Ngrid))
    values_dict['nyx.final_z'] = '5.1'
    values_dict['nyx.plot_z_values'] = '5.1'

    parameter_zip = read_reionization_parameters(input_filename=args.parameter_file)
    for parameters in parameter_zip:
        midpoint = float(parameters[0])
        duration = float(parameters[1])
        asymmetry = float(parameters[2])
        Mmin = float(parameters[3])
        mfp = float(parameters[4])
        heat_injected = float(parameters[5])

        values_dict['nyx.reionization_T_zHI'] = '{:.1E}'.format(heat_injected)

        sim_dir_name = 'nyx_cdm_{:d}_v{:d}_{:s}Mpc_zreion_amber_IC{:d}_zm{:.1f}_Dz{:.1f}_Az{:.1f}_Mm{:.1E}_mfp{:.1f}_' \
                       'hii{:.1f}_DT{:.1E}'.format(int(args.Ngrid), int(args.vbc), args.Lbox, int(args.ics_Ngrid),
                                                   midpoint, duration, asymmetry, Mmin, mfp, int(args.hii_Ngrid),
                                                   heat_injected)
        if os.path.exists('{:s}/{:s}'.format(args.simulation_directory_path, sim_dir_name)):
            print('Simulation directory exists already.')
        else:
            print('Simulation directory does not exist. Making it now.')
            os.makedirs('{:s}/{:s}'.format(args.simulation_directory_path, sim_dir_name))
            
        # assumes that running this code means you want to overwrite any existing inputs.txt file
        with open(args.template_input_file) as f:
            new_file = open('{:s}/{:s}/inputs.txt'.format(args.simulation_directory_path, sim_dir_name), 'w')
            lines = f.readlines()
            for line in lines:
                first_element = line.split()[0] if len(line.split())>0 else line.split()
                if first_element in list(values_dict.keys()):
                    new_line = '{:s} = {:s}\n'.format(first_element, values_dict[first_element])
                    new_file.write(new_line)
                else:
                    new_file.write(line)
