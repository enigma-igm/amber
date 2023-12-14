import numpy as np
from matplotlib import pyplot as plt
from reion_model import ReionModel
import time
import sys
import os
from grid_run import read_amber_parameters

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Plot all AMBER reionization histories.')
    parser.add_argument('--parameter_file', required=True,
                        help='Parameter txt file name.', metavar='')
    parser.add_argument('--data_directory', metavar='', required=True,
                        help='Directory containing zreion_fields directory.')
    parser.add_argument('--figure_directory', metavar='', required=True,
                        help='Directory in which to save the figure.')
    parser.add_argument('--upper_z', metavar='', type=float, default=10.0, required=False,
			help='Highest redshift to plot')
    parser.add_argument('--lower_z', metavar='', type=float, default=5.5, required=False,
                        help='Lowest redshift to plot')
    parser.add_argument('--show_figure', metavar='', required=False, action=argparse.BooleanOptionalAction,
                        help='Whether to show the figure.')
    args = parser.parse_args()
    os.environ['DATADIR'] = args.data_directory  # setting the environment variable for the data file path
    os.environ['FIGDIR'] = args.figure_directory

    parameters_zip = read_amber_parameters(args.parameter_file)

    fig, ax = plt.subplots()
    ax.set_xlabel('redshift')
    ax.set_ylabel(r'$x_\mathrm{HI,v}$')
    for parameters in parameters_zip:
        try:  # see if the zre file exists
            zreion_model = ReionModel(Lbox=20, ic_dimension=128, hii_dimension=128, Az=parameters[2],
                                      zmid=parameters[0], Deltaz=parameters[1], method='amber')
            z, xHII1 = zreion_model.retrieve_xHI_redshift(bins=np.linspace(args.lower_z, args.upper_z, 100))
            ax.plot(z[1:], xHII1, color='b', alpha=0.2)
        except:
            print('\nThe model does not exist. Continuing with other models...\n')
    plt.savefig('{:s}/xHI_histories.png'.format(args.figure_directory), dpi=300, bbox_inches='tight')
    if args.show_figure: plt.show()
