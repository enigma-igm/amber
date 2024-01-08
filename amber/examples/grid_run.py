import numpy as np
import os
import subprocess


def read_amber_parameters(input_filename):
    """
        Read a 6 column txt file containing the AMBER model parameters plus a temperature column at the end.
        The temperature values are not used in AMBER, but are used later in the grid modeling process.

        Inputs:
                input_filename (str): Name of the txt file containing input parameters.

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
    """
    # last column should be temperature, which is not used in AMBER
    midpoint, duration, asymmetry, minimum_halo_mass, mean_free_path, _ = np.loadtxt(input_filename, unpack=True)
    return zip(midpoint, duration, asymmetry, minimum_halo_mass, mean_free_path)


if __name__ == '__main__':
    # python grid_run.py --parameter_file input/model_params.txt --input_file_path input/input.txt --output_directory_path output --amber_executeable_path .
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Generate AMBER reionization fields given file with parameter list.')
    parser.add_argument('--parameter_file', required=True,
                        help='Parameter txt file name.', metavar='')
    parser.add_argument('--input_file_path', metavar='', required=True,
                        help='AMBER input file.')
    parser.add_argument('--output_directory_path', metavar='', required=True,
                        help='Path to output directory containing AMBER outputs.')
    parser.add_argument('--amber_executeable_path', metavar='', required=True,
                        help='Path to AMBER executable (amber.x).')

    args = parser.parse_args()

    parameter_zip = read_amber_parameters(input_filename=args.parameter_file)
    for parameters in parameter_zip:
        midpoint = float(parameters[0])
        duration = float(parameters[1])
        asymmetry = float(parameters[2])
        Mmin = float(parameters[3])
        mfp = float(parameters[4])
        print(midpoint, duration, asymmetry, Mmin, mfp)
        fin = open(args.input_file_path, "r")
        fout = open("{:s}/zmid{:.1f}_Deltaz{:.1f}_Az{:.1f}_Mmin{:.1E}_mfp{:.1f}_log.txt".format(args.output_directory_path, midpoint, duration, asymmetry, Mmin, mfp), "w")
        subprocess.call(["{:s}/amber.x".format(args.amber_executeable_path), "{:.1f}".format(midpoint), "{:.1f}".format(duration), \
                         "{:.1f}".format(asymmetry), "{:.1E}".format(Mmin), "{:.1f}".format(mfp)], stdin=fin, stdout=fout)
        fout.close()
        fin.close()

