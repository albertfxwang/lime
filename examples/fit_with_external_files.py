
# Include the library into the python path
import sys
from pathlib import Path
example_file_path = Path(__file__).resolve()
lime_path = example_file_path.parent.parent/'src'
src_folder = str(lime_path)
sys.path.append(src_folder)
import lime

# Declare the data location
example_path = Path(__file__).parent
obsFitsFile = example_path/'sample_data/gp121903_BR.fits'
lineMaskFile = example_path/'sample_data/gp121903_BR_mask.txt'
cfgFile = example_path/'sample_data/gtc_greenpeas_data.ini'

# Load configuration
obsConf = lime.loadConfData(cfgFile, objList_check=True)

# Load mask
maskDF = lime.lineslogFile_to_DF(lineMaskFile)

# Load spectrum
wave, flux, header = lime.import_fits_data(obsFitsFile, instrument='OSIRIS')
user_conf = obsConf['gp121903_line_fitting']

# Declare line measuring object
z_obj = obsConf['sample_data']['z_array'][2]
norm_flux = obsConf['sample_data']['norm_flux']
lm = lime.Spectrum(wave, flux, redshift=z_obj, normFlux=norm_flux)
lm.plot_spectrum()


lm.wave
# Find lines
norm_spec = lime.continuum_remover(lm.wave_rest, lm.flux, noiseRegionLims=obsConf['sample_data']['noiseRegion_array'])
obsLinesTable = lime.line_finder(lm.wave_rest, norm_spec, noiseWaveLim=obsConf['sample_data']['noiseRegion_array'], intLineThreshold=3)
matchedDF = lime.match_lines(lm.wave_rest, lm.flux, obsLinesTable, maskDF)
lm.plot_spectrum(obsLinesTable=obsLinesTable, matchedLinesDF=matchedDF, specLabel=f'Emission line detection')

# Correct line region
corrected_mask_file = Path('./sample_data/gp121903_BR_mask_corrected.txt')

# Load corrected masks
objMaskDF = lime.lineslogFile_to_DF(corrected_mask_file)

# Measure the emission lines
for i, lineLabel in enumerate(objMaskDF.index.values):
    wave_regions = objMaskDF.loc[lineLabel, 'w1':'w6'].values
    lm.fit_from_wavelengths(lineLabel, wave_regions, user_conf=user_conf)
    # lm.display_results(show_fit_report=True, show_plot=True, log_scale=True, frame='obs')

# Display results
lm.plot_line_grid(lm.linesDF, frame='obs')

# # Save the results
home_folder = Path.home()
lm.save_lineslog(lm.linesDF, home_folder/'linesLog.txt')
lm.table_fluxes(lm.linesDF, home_folder/'linesTable')



