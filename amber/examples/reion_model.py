import numpy as np
from IPython import embed
import sys
from scipy.interpolate import interp1d
import os

class ReionModel:
    def __init__(self, method, Lbox, ic_dimension, hii_dimension, zmid, Deltaz, Az, Mmin, mfp, density_file=None):
        '''
            Inputs:
                method (string): Describing method used to generate reionization field (e.g. density, amber, 21cmfast).
                Lbox (float): Box size of the reionization field in cMpc/h.
                ic_dimension (int): Dimension of the initial conditions used to generate the reion. field.
                hii_dimension (int): Dimension of the final reion. field.
                zmid (float): Reionization midpoint.
                Deltaz (float): Reionization duration in z units.
                Az (float): Reionization asymmetry as defined in Trac et al. 2022.
                datadir (string): Path to the reionization field data files.
        '''

        self.method = 'amber'
        self.Lbox = float(Lbox)
        self.ic_dimension = int(ic_dimension)
        self.hii_dimension = int(hii_dimension)
        self.zmid = float(zmid)
        self.Deltaz = float(Deltaz)
        self.Az = float(Az)
        self.Mmin = float(Mmin)
        self.mfp = float(mfp)
        self._DeltaT = None

        # reionization field file name format
        #  removed 'method' property to deal with Fortan filename length limitations
        self.table_name = 'IC{:d}_zm{:.1f}_Dz{:.1f}_Az{:.1f}_Mm{:.1E}_mfp{:.1f}_hii{:d}_{:d}Mpc'. \
            format(self.ic_dimension, self.zmid, self.Deltaz, self.Az, self.Mmin, self.mfp,
                   self.hii_dimension, int(self.Lbox))

        if self.method == 'amber':
            try:
                data = np.fromfile('{0}/zreion_fields/{1}'.format(os.environ.get("DATADIR"), self.table_name),
                                   dtype=np.float32)
            except:
                print('\n', self.table_name, 'does not exist.\n')
                raise ValueError("method=amber is specified, but there isn't any existing model field.")
            self.field = np.reshape(data, [self.hii_dimension, self.hii_dimension, self.hii_dimension], order='F')
        elif self.method == 'density':
            if not density_file: # if density_file is not named, then break
                raise ValueError("When making the reionization field by abundance-matching to a density field, \n"
                                 "you need to provide the filename of the stored density field to use.")
            self.field = self.make_zreion_field_from_density(density_file) # not sure if best way to do this...
        else:
            raise ValueError("You didn't define a method for generating the field.")

    @property
    def DeltaT(self):
        return self._DeltaT

    @DeltaT.setter  # these are kind of silly, because you don't actually need them.
    def DeltaT(self, value):
        self._DeltaT = value

    def retrieve_xHI_redshift(self, bins=100):
        '''
            Inputs:
                _zlist (float list): List of redshifts where ionized fraction should be evaluated.
            Returns:
                xHIIv_list (float list): Ionized fractions at each value in _zlist.
        '''
        PDF, x = np.histogram(self.field.flatten(), bins=bins, density=True)
        dx = x[1] - x[0]
        CDF = np.cumsum(PDF) * dx
        return x, CDF

    def inside_flexknot(self, _redshifts, xhiv_list):
        '''
            Inputs:
                _redshifts (float list): List of redshifts where neutral fraction is compared to FlexKnot.
                xhiv_list (float_list): List of neutral fractions at each z in _redshifts.
            Returns:
                unnamed (Boolean): False if model violates FlexKnot limits. True if xHI history is within the limits.
        '''
        lims = retrieve_flexknot_limits(_redshifts)
        if np.any(xhiv_list < (lims[0]-0.05)):  # < 5 percent violation of xhi lower limits
            return False
        if np.any(xhiv_list > (lims[1]+0.05)):  # > 5 percent violation of xhi upper limits
            return False

        return True

    def make_zreion_field_from_density(self, xHI_history, density_file):
        '''
        Modifed from a code from H. Park. Haven't tested since I copied it in here.

            Inputs:
                xHI_history (namedtuple): Namedtuple from collections package, includes array of redshifts
                                          (xHI_history.z) and array of neutral fractions (xHI_history.xHI)
                density_file (string): Full path to file containing overdensity field saved as a binary file of
                                    single precision.
            Returns:
                zre (ndarray floats): The 3D reionization field.
        '''
        den = np.fromfile(density_file).reshape((self.hii_dimension, self.hii_dimension, self.hii_dimension))
        den = (den + 1)
        cfac = 1  # Coarsening factor, currently not used

        ndim = self.hii_dimension
        ndiml = round(ndim / cfac)
        denl = np.zeros((ndiml, ndiml, ndiml), dtype=float)  # Coarsened density mesh

        # A 3D loop to coarsen the density cube
        for ix in range(0, ndim, cfac):
            ilx = round(ix / cfac)
            for iy in range(0, ndim, cfac):
                ily = round(iy / cfac)
                for iz in range(0, ndim, cfac):
                    ilz = round(iz / cfac)
                    denl[ilx, ily, ilz] = np.sum(den[ix:ix + cfac, iy:iy + cfac, iz:iz + cfac]) / cfac ** 3

        rtop = 1.0  # cMpc/h, smoothing radius, same as in Battaglia+2013

        tdenl = np.fft.fftn(denl)
        tsmden = np.copy(tdenl)  # First FFW the density field

        klist = np.mod(np.arange(ndiml) + ndiml / 2, ndiml) - ndiml / 2
        klist = klist * 2. * np.pi / self.Lbox

        for ix in range(ndiml):
            kx = klist[ix]
            for iy in range(ndiml):
                ky = klist[iy]
                for iz in range(ndiml):
                    kz = klist[iz]
                    kmag = (kx ** 2 + ky ** 2 + kz ** 2) ** 0.5
                    Rk = rtop * kmag
                    tsmden[ix, iy, iz] = tdenl[ix, iy, iz] * 3 / (Rk ** 3) * (
                                np.sin(Rk) - Rk * np.cos(Rk))  # fixed the kernel in fourier space, error in original code.

        tsmden[0, 0, 0] = 0.  # Setting the average to 0 since the average does not matter anyway.

        smden = np.fft.ifftn(tsmden).astype('float32')  # Inverse FFW to the real space
        PDF, x = np.histogram(smden, bins=100, density=True)
        smden_grid = (x[:100] + x[1:]) / 2.
        dx = x[1] - x[0]
        CDF = np.cumsum(PDF) * dx
        zarr = np.linspace(5, 20, 40)
        xhi_interpd = interp1d(xHI_history.z, xHI_history.xHI, bounds_error=False, fill_value=(1.0, 0.0))
        Xarr = xhi_interpd(zarr)
        zre = np.copy(smden)
        for ii in range(ndiml):  # 3D loop
            for ji in range(ndiml):
                for ki in range(ndiml):
                    _Xin = np.interp(smden[ii, ji, ki], smden_grid, 1. - CDF)
                    zre[ii, ji, ki] = np.interp(_Xin, Xarr[::-1], zarr[::-1])
        return zre

def retrieve_flexknot_limits(_redshifts,
                             planck_file='/Users/cdoughty/research/processed/data_boera19_comparison/obs_'
                                             'comparisons/Planck_2018_xe.txt'):
    '''
        Copied from neutralfraction_yang.py.

        Inputs:
            _redshifts (float list): List of redshifts to interpolate the FlexKnot limits at.
        Returns:
            xhi_lower_limit (float list): List of lower limits on volume-weighted neutral fraction, xHI, at each
                                          value in _redshifts.
            xhi_upper_limit (float list): List of upper limits on volume-weighted neutral fraction, xHI, at each
                                          value in _redshifts.
    '''
    catp = np.genfromtxt(planck_file)  #
    z_m2, xe_m2, z_m1, xe_m1, z_p1, xe_p1, z_p2, xe_p2 = catp[:, 0], catp[:, 1], catp[:, 2], catp[:, 3], catp[:, 4], \
                                                         catp[:, 5], catp[:, 6], catp[:, 7]
    xe_p2 = np.interp(_redshifts, z_p2, xe_p2)
    xe_m2 = np.interp(_redshifts, z_m2, xe_m2)
    xhi_upper_limit = 1 - xe_m2  # xe_m2 = two sigma high lim
    xhi_lower_limit = 1 - xe_p2  # xe_p2 = two sigma low lim
    fix_negatives = np.where(xhi_upper_limit < 0)
    xhi_upper_limit[fix_negatives] = 0.0
    fix_negatives = np.where(xhi_lower_limit < 0)
    xhi_lower_limit[fix_negatives] = 0.0
    return xhi_lower_limit, xhi_upper_limit
