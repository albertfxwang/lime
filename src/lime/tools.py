import numpy as np
import pandas as pd
import astropy.units as au

from lmfit.models import PolynomialModel
from sys import exit

from lime import _logger

try:
    from specutils import Spectrum1D, SpectralRegion
    from specutils.manipulation import noise_region_uncertainty
    from specutils.fitting import find_lines_derivative
    specutils_check = True

except ImportError:
    specutils_check = False

VAL_LIST = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
SYB_LIST = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]

WAVE_UNITS_DEFAULT, FLUX_UNITS_DEFAULT = au.AA, au.erg / au.s / au.cm ** 2 / au.AA

UNITS_LATEX_DICT = {'A': '\AA',
                    'um': '\mu\!m',
                    'nm': 'nm',
                    'erg/cm^2/s/A': r'erg\,cm^{-2} s^{-1} \AA^{-1}',
                    'Jy': 'Jy',
                    'mJy': 'mJy'}

#[Y erg/cm^2/s/A] = 2.99792458E+21 * [X1 W/m^2/Hz] / [X2 A]^2
# 2.99792458E+17 units
# 1 Jy = 10−26 W⋅m−2⋅Hz−1
# 1 Jy = 10−23 erg⋅s−1⋅cm−2⋅Hz−1
# 1 nm = 2.99792458E+17

def int_to_roman(num):
    i, roman_num = 0, ''
    while num > 0:
        for _ in range(num // VAL_LIST[i]):
            roman_num += SYB_LIST[i]
            num -= VAL_LIST[i]
        i += 1
    return roman_num


def label_decomposition(lines, recomb_atom=('H1', 'He1', 'He2'), comp_dict={}, scalar_output=False,
                        user_format={}, units_wave='A'):

    """

    This function returns the ion, wavelength and transition label latex from the input line list with the LiMe line
    notation.

    :param lines: A string or array of strings with the LiMe transition notation, e.g. O3_5007A
    :type lines: str, list

    :param recomb_atom: An array with the ions producing photons from a recombination process. By default the function
                        assumes that these are H1, He1 and He2 while the metal ions produce photons from a collisional
                        excited state.
    :type recomb_atom: str, list

    :param comp_dict: Dictionary with the user latex format for the latex labels, overwritting the default notation.
    :type comp_dict: dict, optional

    :param scalar_output: Boolean for a scalar output in case of a single input line input.
    :type scalar_output: bool, optional

    :param user_format: Dictionary with the user notation for the latex labels. This overwrites the default notation.
    :type user_format: dict, optional

    :param units_wave: Label wavelength units. The default value "A" is angstrom.
    :type units_wave: str, optional

    :return: 3 arrays (or scalars) with the input transition line(s) ion, wavelength and scientific notation in latex format.
    :rtype: numpy.ndarray

    :Example:
        >>> import lime
        >>> lime.label_decomposition('O3_5007A', scalar_output=True)
        O3, 5007.0, '$5007\\AA\\,[OIII]$'
        >>> lime.label_decomposition('H1_6563A_b', comp_dict={"H1_6563A_b":"H1_6563A-N2_6584A-N2_6548A"})
        ['H1'], [6563.], ['$6563\\AA\\,HI+6584\\AA\\,[NII]+6548\\AA\\,[NII]$']

    """

    # Confirm input array has one dimension
    # TODO for blended lines it may be better to return all the blended components individually
    lines = np.array(lines, ndmin=1)

    # TODO current workflow breaks if repeated labels
    uniq, count = np.unique(lines, return_counts=True)
    assert not np.any(count > 1), '- ERROR: The input line labels in lime.label_decomposition includes repeated entries, please remove them'

    # Containers for input data
    ion_dict, wave_dict, latexLabel_dict = {}, {}, {}

    for lineLabel in lines:

        # Case the user provides his own format
        if lineLabel in user_format:
            ion_dict[lineLabel], wave_dict[lineLabel], latexLabel_dict[lineLabel] = user_format[lineLabel]

        # Default format
        else:

            # Check if line reference corresponds to blended component
            mixture_line = False
            if (lineLabel[-2:] == '_b') or (lineLabel[-2:] == '_m'):
                mixture_line = True
                if lineLabel in comp_dict:
                    lineRef = comp_dict[lineLabel]
                else:
                    lineRef = lineLabel[:-2]
            else:
                lineRef = lineLabel

            # Split the components if they exists
            lineComponents = lineRef.split('-')

            # Decomponse each component
            latexLabel = ''
            for line_i in lineComponents:

                # Check that the line has the right units
                kinem_comp_check = False if line_i.count('_') == 1 else True

                # Get ion:
                if 'r_' in line_i: # Case recombination lines
                    ion = line_i[0:line_i.find('_')-1]
                else:
                    ion = line_i[0:line_i.find('_')]

                # Get wavelength and their units # TODO add more units and more facilities for extensions
                if (line_i.endswith(units_wave)) or kinem_comp_check:
                    wavelength = line_i[line_i.find('_') + 1:line_i.rfind(units_wave)]
                    units = UNITS_LATEX_DICT[units_wave]
                    ext = f'-{line_i[line_i.rfind("_")+1:]}' if kinem_comp_check else ''
                else:
                    wavelength = line_i[line_i.find('_') + 1:]
                    units = ''
                    ext = ''

                # Get classical ion notation
                atom, ionization = ion[:-1], int(ion[-1])
                ionizationRoman = int_to_roman(ionization)

                # TODO add metals notation
                # Define the label
                if ion in recomb_atom:
                    comp_line = f'{atom}{ionizationRoman}\,{wavelength}{units}{ext}'
                else:
                    comp_line = f'[{atom}{ionizationRoman}]\,{wavelength}{units}{ext}'

                # In the case of a mixture line we take component with the _b as the parent
                if mixture_line:
                    if lineLabel[:-2] == line_i:
                        ion_dict[lineRef] = ion
                        wave_dict[lineRef] = float(wavelength)
                        latexLabel = comp_line if len(latexLabel) == 0 else f'{latexLabel}+{comp_line}'
                    else:
                        latexLabel = comp_line if len(latexLabel) == 0 else f'{latexLabel}+{comp_line}'

                # This logic will expand the blended lines, but the output list will be larger than the input one
                else:
                    ion_dict[line_i] = ion
                    wave_dict[line_i] = float(wavelength)
                    latexLabel_dict[line_i] = '$'+comp_line+'$'

            if mixture_line:
                latexLabel_dict[lineRef] = '$'+latexLabel +'$'

    # Convert to arrays
    label_array = np.array([*ion_dict.keys()], ndmin=1)
    ion_array = np.array([*ion_dict.values()], ndmin=1)
    wavelength_array = np.array([*wave_dict.values()], ndmin=1)
    latexLabel_array = np.array([*latexLabel_dict.values()], ndmin=1)

    assert label_array.size == wavelength_array.size, 'Output ions do not match wavelengths size'
    assert label_array.size == latexLabel_array.size, 'Output ions do not match labels size'

    if ion_array.size == 1 and scalar_output:
        output = (ion_array[0], wavelength_array[0], latexLabel_array[0])
    else:
        output = (ion_array, wavelength_array, latexLabel_array)

    return output

def compute_line_width(idx_peak, spec_flux, delta_i, min_delta=2, emission_check=True):
    """
    Algororithm to measure emision line width given its peak location
    :param idx_peak:
    :param spec_flux:
    :param delta_i:
    :param min_delta:
    :return:
    """

    i = idx_peak

    if emission_check:
        while (spec_flux[i] > spec_flux[i + delta_i]) or (np.abs(idx_peak - (i + delta_i)) <= min_delta):
            i += delta_i
    else:
        while (spec_flux[i] < spec_flux[i + delta_i]) or (np.abs(idx_peak - (i + delta_i)) <= min_delta):
            i += delta_i

    return i


def compute_FWHM0(idx_peak, spec_flux, delta_wave, cont_flux, emission_check=True):

    """

    :param idx_peak:
    :param spec_flux:
    :param delta_wave:
    :param cont_flux:
    :param emission_check:
    :return:
    """

    i = idx_peak
    i_final = 0 if delta_wave < 0 else spec_flux.size - 1

    if emission_check:
        while (spec_flux[i] >= cont_flux[i]) and (i != i_final):
            i += delta_wave
    else:
        while (spec_flux[i] <= cont_flux[i]) and (i != i_final):
            i += delta_wave

    return i


def blended_label_from_log(line, log):

    # Default values: single line
    blended_check = False

    if line in log.index:

        if log.loc[line, 'profile_label'] == 'no':
            profile_label = 'no'
        elif line.endswith('_m'):
            profile_label = log.loc[line, 'profile_label']
        else:
            blended_check = True
            profile_label = log.loc[line, 'profile_label']
    else:
        # TODO this causes and error if we forget the '_b' componentes in the configuration file
        exit(f'\n-- ERROR: line {line} not found input lines log')

    return blended_check, profile_label


def latex_science_float(f, dec=2):
    float_str = f'{f:.{dec}g}'
    if "e" in float_str:
        base, exponent = float_str.split("e")
        return r"{0} \times 10^{{{1}}}".format(base, int(exponent))
    else:
        return float_str


class LineFinder:

    def __init__(self):

        return

    def match_line_mask(self, log, noise_region, detect_threshold=3, emis_threshold=(4, 4), abs_threshold=(1.5, 1.5),
                        poly_degree=(3, 7), width_tol=5, line_type='emission', width_mode='fixed'):

        """
        This function compares a spectrum flux peaks and troughs with the input lines mask log to confirm the presence of
        emission or absorption lines. The user can specify the line type with the ``line_type='emission'`` or ``line_type='absorption'``
        parameter.

        The user must specify a wavelength range (in the rest frame) to establish the region from which the spectrum
        noise standard deviation is calculated. This region must not have absorptions or emissions.

        The treatment requires a normalized spectrum (continuum at zero). This is done by fitting the spectrum
        as a polynomial function in an iterative process. The user can specify in the ``poly_degree`` parameter as an
        an array with values in increasing magnitude for the polynomial order. The user should specify ``emis_threshold``
        and ``abs_threshold`` for the emission and absorptions intensity threshold. This masking is necessary to avoid
        intense emission/absorptions affecting the continuum normalization.

        Afterwards, the task runs the `find_lines_derivative <https://specutils.readthedocs.io/en/stable/api/specutils.fitting.find_lines_derivative.html>`_
        function to find peaks and troughs in the normalized spectrum. The intensity threshold in this detection is read
        from the ``detect_threshold`` parameter. The output table from this function is the first return of this task.

        In the next step, the task compares the input lines ``log`` bands with the peaks/troughs location from the `find_lines_derivative <https://specutils.readthedocs.io/en/stable/api/specutils.fitting.find_lines_derivative.html>`_
        output. Those matching the line band limits (w3, w4 in the ``log``) plus the tolerance in the ``width_tol``
        parameter (in the spectrum wavelength units) count as a positive detection. These lines are the second return
        as a new log.

        Finally, the task can attempt to adjust the line band width to the width of the emission/absorption feature.
        In the ``width_mode='auto'`` the non-blended lines w3, w4 values in the output log band will be changed to the
        first pixel wavelength, starting from the maximum/minimum at which there is an increase/decrease in flux intensity
        for emission and absorption lines respectively. In blended lines, the w3, w4 values are not modified.
        In the ``width_mode='fix'`` setting the line masks wavelengths are not modified.

        :param log: Lines log with the masks. The required columns are: the line label (DF index), w1, w2, w3, w4, w5 and w6.
                    These wavelengths must be in the rest frame.
        :type log: pandas.DataFrame

        :param noise_region: 2 value array with the wavelength limits for the noise region (in rest frame).
        :type noise_region: numpy.array

        :param detect_threshold: Intensity factor for the continuum signal for an emission/absorption detection.
        :type detect_threshold: float, optional

        :param emis_threshold: Array with the intensity factor for the emission features masking during the continuum normalization.
        :type emis_threshold: numpy.array, optional

        :param abs_threshold: Array with the intensity factor for the absorption features masking during the continuum normalization.
        :type abs_threshold: numpy.array, optional

        :param poly_degree: Array with the polynomial order for the iterative fitting for the continuum normalization in increasing order.
        :type poly_degree: numpy.array, optional

        :param width_tol: Tolerance for the peak/trough detection with respect to the input line masks w3 and w4 values.
        :type width_tol: float, optional

        :param line_type: Type of lines matched in the output lines log. Accepted values are 'emission' and 'absorption'
        :type line_type: str, optional

        :param width_mode: Scheme for the line band mask detection. If set to "fixed" the input w3 and w4 values won't be modified.
        :type width_tol: str, optional

        :return: Table with the peaks/trough detected and log with the matched lines.
        :rtype: astropy.Table and pandas.DataFrame

        """

        # Remove the continuum
        if specutils_check:

            # Convert the noise region to the the observed frame
            noise_region_obs = noise_region * (1 + self.redshift)

            # Normalize the continuum to zero
            flux_no_continuum = self.remove_continuum(noise_region_obs, emis_threshold, abs_threshold, poly_degree)

            # Find the emission, absorption peaks
            peaks_table = self.peak_indexing(flux_no_continuum, noise_region_obs, detect_threshold)

            # Match peaks with theoretical lines
            matched_DF = self.label_peaks(peaks_table, log, width_tol=width_tol, width_mode=width_mode,
                                          line_type=line_type)

            return peaks_table, matched_DF

        else:
            exit(f'\n- WARNING: specutils is not installed')
            return None, None

    def remove_continuum(self, noise_region, emis_threshold, abs_threshold, cont_degree_list):

        assert self.wave[0] < noise_region[0] and noise_region[1] < self.wave[-1], \
            f'Error noise region {self.wave[0]/(1+self.redshift)} < {noise_region[0]/(1+self.redshift)} ' \
            f'and {noise_region[1]/(1+self.redshift)} < {self.wave[-1]/(1+self.redshift)}'

        # Wavelength range and flux to use
        input_wave, input_flux = self.wave, self.flux

        # Identify high flux regions
        idcs_noiseRegion = (noise_region[0] <= input_wave) & (input_wave <= noise_region[1])
        noise_mean, noise_std = input_flux[idcs_noiseRegion].mean(), input_flux[idcs_noiseRegion].std()

        # Perform several continuum fits to improve the line detection
        for i in range(len(emis_threshold)):

            # Mask line regions
            emisLimit = emis_threshold[i] * (noise_mean + noise_std)
            absoLimit = (noise_mean + noise_std) / abs_threshold[i]
            # emisLimit = emis_threshold[i][0] * (noise_mean + noise_std)
            # absoLimit = (noise_mean + noise_std) / emis_abs_threshold[i][1]
            idcsLineMask = np.where((input_flux >= absoLimit) & (input_flux <= emisLimit))
            wave_masked, flux_masked = input_wave[idcsLineMask], input_flux[idcsLineMask]

            # Perform continuum fits iteratively
            poly3Mod = PolynomialModel(prefix=f'poly_{cont_degree_list[i]}', degree=cont_degree_list[i])
            poly3Params = poly3Mod.guess(flux_masked, x=wave_masked)
            poly3Out = poly3Mod.fit(flux_masked, poly3Params, x=wave_masked)

            input_flux = input_flux - poly3Out.eval(x=input_wave) + noise_mean

        return input_flux - noise_mean

    def peak_indexing(self, flux, noise_region, line_threshold=3):

        assert self.wave[0] < noise_region[0] and noise_region[1] < self.wave[-1], \
            f'Error noise region {self.wave[0]/(1+self.redshift)} < {noise_region[0]/(1+self.redshift)} ' \
            f'and {noise_region[1]/(1+self.redshift)} < {self.wave[-1]/(1+self.redshift)}'

        # Establish noise values
        idcs_noiseRegion = (noise_region[0] <= self.wave) & (self.wave <= noise_region[1])
        noise_region = SpectralRegion(noise_region[0] * WAVE_UNITS_DEFAULT, noise_region[1] * WAVE_UNITS_DEFAULT)
        flux_threshold = line_threshold * flux[idcs_noiseRegion].std()

        input_spectrum = Spectrum1D(flux * FLUX_UNITS_DEFAULT, self.wave * WAVE_UNITS_DEFAULT)
        input_spectrum = noise_region_uncertainty(input_spectrum, noise_region)
        linesTable = find_lines_derivative(input_spectrum, flux_threshold)

        return linesTable

    def label_peaks(self, peak_table, mask_df, line_type='emission', width_tol=5, width_mode='auto', detect_check=False):

        # TODO auto param should be changed to boolean

        matched_DF = pd.DataFrame.copy(mask_df)

        # Security check for case no lines detected
        if len(peak_table) == 0:
            return pd.DataFrame(columns=matched_DF.columns)

        # Query the lines from the astropy finder tables #
        idcsLineType = peak_table['line_type'] == line_type
        idcsLinePeak = np.array(peak_table[idcsLineType]['line_center_index'])
        wave_peaks = self.wave_rest[idcsLinePeak]

        # Theoretical wave values
        ion_array, waveTheory, latexLabel_array = label_decomposition(matched_DF.index.values, units_wave=self.units_wave)
        matched_DF['wavelength'] = waveTheory

        # Match the lines with the theoretical emission
        tolerance = np.diff(self.wave_rest).mean() * width_tol
        matched_DF['observation'] = 'not detected'
        unidentifiedLine = dict.fromkeys(matched_DF.columns.values, np.nan)

        for i in np.arange(wave_peaks.size):

            idx_array = np.where(np.isclose(a=waveTheory, b=wave_peaks[i], atol=tolerance))

            if len(idx_array[0]) == 0:
                unknownLineLabel = 'xy_{:.0f}A'.format(np.round(wave_peaks[i]))

                # Scheme to avoid repeated lines
                if (unknownLineLabel not in matched_DF.index) and detect_check:
                    newRow = unidentifiedLine.copy()
                    newRow.update({'wavelength': wave_peaks[i], 'w3': wave_peaks[i] - 5, 'w4': wave_peaks[i] + 5,
                                   'observation': 'not_identified'})
                    matched_DF.loc[unknownLineLabel] = newRow

            else:

                row_index = matched_DF.index[matched_DF.wavelength == waveTheory[idx_array[0][0]]]
                matched_DF.loc[row_index, 'observation'] = 'detected'
                theoLineLabel = row_index[0]

                blended_check = True if '_b' in theoLineLabel else False
                minSeparation = 4 if blended_check else 2

                # Width is only computed for blended lines
                if width_mode == 'auto':
                    if blended_check is False:
                        emission_check = True if line_type == 'emission' else False
                        idx_min = compute_line_width(idcsLinePeak[i], self.flux, delta_i=-1, min_delta=minSeparation, emission_check=emission_check)
                        idx_max = compute_line_width(idcsLinePeak[i], self.flux, delta_i=1, min_delta=minSeparation, emission_check=emission_check)
                        matched_DF.loc[row_index, 'w3'] = self.wave_rest[idx_min]
                        matched_DF.loc[row_index, 'w4'] = self.wave_rest[idx_max]

        # Include_only_detected
        idcs_unknown = matched_DF['observation'] == 'not detected'
        matched_DF.drop(index=matched_DF.loc[idcs_unknown].index.values, inplace=True)

        # Sort by wavelength
        matched_DF.sort_values('wavelength', inplace=True)
        matched_DF.drop(columns=['wavelength', 'observation'], inplace=True)

        # Latex labels
        # ion_array, wavelength_array, latexLabel_array = label_decomposition(matched_DF.index.values)
        # matched_DF['latexLabel'] = latexLabel_array

        return matched_DF