import numpy as np
import os
import subprocess

# TODO 
# read in a file with the model parameters and load them into the code

def read_amber_parameters(input_filename):
    """
        Read a 3 column txt file containing the AMBER model parameters.

        Inputs:
                input_filename (str): Name of the txt file containing input parameters.

        Outputs:
                midpoint (array): Mass-weighted reionization midpoints.

                duration (array): History durations, defined as difference in redshift 
                                  between 5 and 95 percent ionized.

                asymmetry (array): Asymmetries, defined as the redshift difference 
                                   between the first half of the process (zearly-zmid)
                                   divided by that of the second half (zmid-zlate).
    """
    parameters = np.loadtxt(input_filename)
    midpoint, duration, asymmetry = np.loadtxt(input_filename, unpack=True)
    return zip(midpoint, duration, asymmetry)


if __name__ == '__main__':
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
        #fin = open("/data2/doughty/repos/amber/examples/input/input.txt", "r")
        #fout = open("output/zmid{:.1f}_Deltaz{:.1f}_Az{:.1f}_log.txt".format(midpoints[zmi], durations[dzi], asymmetries[ai]), "w")
        #subprocess.call(["/data2/doughty/repos/amber/examples/amber.x", "{:.1f}".format(midpoints[zmi]), "{:.1f}".format(durations[dzi]), \
        #                "{:.1f}".format(asymmetries[ai])], stdin=fin, stdout=fout)
        midpoint = float(parameters[0])
        duration = float(parameters[1])
        asymmetry = float(parameters[2])
        fin = open(args.input_file_path, "r")
        fout = open("{:s}/zmid{:.1f}_Deltaz{:.1f}_Az{:.1f}_log.txt".format(args.output_directory_path, midpoint, duration, asymmetry), "w")
        subprocess.call(["{:s}/amber.x".format(args.amber_executeable_path), "{:.1f}".format(midpoint), "{:.1f}".format(duration), \
                         "{:.1f}".format(asymmetry)], stdin=fin, stdout=fout)
        fout.close()
        fin.close()

