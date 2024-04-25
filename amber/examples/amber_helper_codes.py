"""
    Code to make directories to hold Nyx+AMBER simulation output.
"""
import numpy as np
import os
from amber.examples.reion_model import ReionModel
from matplotlib import pyplot as plt
import subprocess
import sys


def read_reionization_parameters(input_filename):
    """
        Read a 6 column txt file containing the AMBER+heat reionization model parameters.
        The temperature values are not used in AMBER, but are used later in the modeling process.

        Inputs:
                input_filename (str): Path+name of the txt file containing input parameters.

        Outputs:
                midpoint (array): Mass-weighted reionization midpoints.

                duration (array): History durations, defined as difference in redshift
                                  between 5 and 95 percent ionized.

                asymmetry (array): Asymmetries, defined as the redshift difference
                                   between the first half of the process (zearly-zmid)
                                   divided by that of the second half (zmid-zlate).

                minimum_halp_mass (array): Minimum halo mass permitted to contribute
                                           ionizing photons.

                mean_free_path (array): Mean free path of ionizing photons to use.

                heat_injected (array): Maximum amount of heat injected when cell is reionized.
    """
    midpoint, duration, asymmetry, minimum_halo_mass, mean_free_path, heat_injected = \
        np.loadtxt(input_filename, unpack=True)
    return zip(midpoint, duration, asymmetry, minimum_halo_mass, mean_free_path, heat_injected)


def grid_run(parameter_file, input_file_path, output_directory_path, amber_executeable_path):
    """
        Generate AMBER reionization fields given file with parameter list.

        Inputs:
                parameter_file (string): Nyx+AMBER model parameter txt file path + name. These values will be passed
                                         via command line call to the AMBER code to generate reionization fields.

                input_file_path (string): AMBER input file. Contains many of the AMBER model parameters and settings,
                                          e.g. whether to run/write/save the grf step.

                output_directory_path (string): Path to output directory containing AMBER outputs.

                amber_executeable_path (string): Path to AMBER Fortran executable (amber.x).

        Returns:
                Nothing directly, but calls the AMBER code to generate reionization fields.
    """
    parameter_zip = read_reionization_parameters(input_filename=parameter_file)
    for parameters in parameter_zip:
        # verbose, but make it clear what each parameters[index] is supposed to be
        midpoint = float(parameters[0])
        duration = float(parameters[1])
        asymmetry = float(parameters[2])
        Mmin = float(parameters[3])
        mfp = float(parameters[4])
        print(midpoint, duration, asymmetry, Mmin, mfp)
        fin = open(input_file_path, "r")
        fout = open("{:s}/zmid{:.1f}_Deltaz{:.1f}_Az{:.1f}_Mmin{:.1E}_mfp{:.1f}_log.txt".format(
            output_directory_path, midpoint, duration, asymmetry, Mmin, mfp), "w")

        # calls the AMBER executeable, passes the parameters from fin into the command line, and writes the terminal
        # output to a log file fout
        subprocess.call(["{:s}/amber.x".format(amber_executeable_path), "{:.1f}".format(midpoint),
                         "{:.1f}".format(duration), \
                         "{:.1f}".format(asymmetry), "{:.1E}".format(Mmin), "{:.1f}".format(mfp)], stdin=fin,
                        stdout=fout)
        fout.close()
        fin.close()


def plot_xHI_history(parameter_file, data_directory, figure_directory, volume_weighted=True, upper_z=10.0, lower_z=5.5,
                     show_figure=True):
    """
        Plot all AMBER reionization histories as xHI vs. redshift. Volume-weighted or mass-weighted (eventually),
        and saves the figure.

        Inputs:
                parameter_file (string): Nyx+AMBER model parameter txt file path + name. These values will be passed
                                         via command line call to the AMBER code to generate reionization fields.

                data_directory (string): Directory containing zreion_fields directory. Assigned to an environmental
                                         variable 'DATADIR' for use in the ReionModel class.

                figure_directory (string): Directory in which to save the figure.

                volume_weighted (bool): Default True, whether to calculate xHI as volume weighted (True) or
                                        mass weighted (False).

                upper_z (float): Highest redshift to plot.

                lower_z (float): Lowest redshift to plot.

                show_figure (bool): Whether to show the figure.

    Returns:
            Nothing is returned, but a figure xHI_histories.png is saved to the figure_directory.

    """
    if not volume_weighted:
        print('Mass weighted ionization fraction not implemented yet.')
        sys.exit()

    os.environ['DATADIR'] = data_directory  # setting the environment variable for the data file path

    parameters_zip = read_reionization_parameters(parameter_file)

    fig, ax = plt.subplots()
    ax.set_xlabel('redshift')
    ax.set_ylabel(r'$x_\mathrm{HI,v}$')
    for parameters in parameters_zip:
        try:  # see if the zre file exists
            zreion_model = ReionModel(Lbox=20, ic_dimension=128, hii_dimension=128, Az=parameters[2],
                                      zmid=parameters[0], Deltaz=parameters[1], Mmin=parameters[3], mfp=parameters[4],
                                      method='amber')
            z, xHII1 = zreion_model.retrieve_xHI_redshift(bins=np.linspace(lower_z, upper_z, 100))
            ax.plot(z[1:], xHII1, color='b', alpha=0.2)
        except:
            print('\nThe model does not exist. Continuing with other models...\n')
    plt.savefig('{:s}/xHI_histories.png'.format(figure_directory), dpi=300, bbox_inches='tight')
    if show_figure: plt.show()


def setup_simulation_grid(parameter_file, simulation_directory_path, template_input_file, Ngrid=256, ics_Ngrid=128,
                          Lbox=20, vbc=30, hii_Ngrid=128):
    """
        Make directories and copy/modify input files for AMBER+Nyx reionization models.

        Inputs:
                parameter_file (string): Nyx+AMBER model parameter txt file path + name. These values will be passed
                                         via command line call to the AMBER code to generate reionization fields.

                simulation_directory_path (string): Top level directory to hold the directories for simulation output.

                template_input_file (string): Path + name of template inputs.txt file.

                Ngrid (int): Simulation grid size.

                ics_Ngrid (int): Gridsize of initial conditions to generate the reionization redshift field.

                Lbox (float): Domain size of the simulation/reionization redshift field.

                vbc (int): Streaming velocity used in initial conditions.

                hii_Ngrid (int): Gridsize of the reionization redshift field.

        Returns:
                Nothing is returned, but directories are made and input files are copied and modified.

    """
    # TODO fix hardcoded h=0.675 value
    values_dict = {'nyx.geometry.prob_hi': '{:.6f}'.format(float(Lbox) / 0.675), 'nyx.final_z': '5.1',
                   'nyx.plot_z_values': '5.1', 'nyx.inhomo_grid': '{:d}'.format(int(hii_Ngrid)),
                   'amr.n_cell': '{:d} {:d} {:d}'.format(int(Ngrid), int(Ngrid), int(Ngrid)),
                   'nyx.reionization_T_zHI': ''}

    parameter_zip = read_reionization_parameters(input_filename=parameter_file)
    for parameters in parameter_zip:
        # verbose, but make it clear what each parameters[index] is supposed to be
        midpoint = float(parameters[0])
        duration = float(parameters[1])
        asymmetry = float(parameters[2])
        Mmin = float(parameters[3])
        mfp = float(parameters[4])
        heat_injected = float(parameters[5])

        values_dict['nyx.reionization_T_zHI'] = '{:.1E}'.format(heat_injected)

        sim_dir_name = f'nyx_cdm_{Ngrid}_v{vbc}_{Lbox}Mpc_zreion_amber_IC{ics_Ngrid}_zm{midpoint:.1f}_Dz{duration:.1f}_Az{asymmetry:.1f}_Mm{Mmin:.1E}_mfp{mfp:.1f}_hii{hii_Ngrid}_DT{heat_injected:.1E}'
        if os.path.exists('{:s}/{:s}'.format(simulation_directory_path, sim_dir_name)):
            print('Simulation directory exists already.')
        else:
            print('Simulation directory does not exist. Making it now.')
            os.makedirs('{:s}/{:s}'.format(simulation_directory_path, sim_dir_name))
            
        # assumes that running this code means you want to overwrite any existing inputs.txt file
        with open(template_input_file) as f:
            new_file = open('{:s}/{:s}/inputs.txt'.format(simulation_directory_path, sim_dir_name), 'w')
            lines = f.readlines()
            for line in lines:
                first_element = line.split()[0] if len(line.split())>0 else line.split()
                if first_element in list(values_dict.keys()):
                    new_line = '{:s} = {:s}\n'.format(first_element, values_dict[first_element])
                    new_file.write(new_line)
                else:
                    new_file.write(line)
