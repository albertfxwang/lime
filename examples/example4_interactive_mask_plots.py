import lime

# Input the data files
obsFitsFile = './sample_data/gp121903_BR.fits'
lineMaskFile = './sample_data/gp121903_BR_mask.txt'
cfgFile = './sample_data/example_configuration_file.cfg'

# Output mask file address
corrected_lineMaskFile = './sample_data/gp121903_BR_mask_corrected'

# Load configuration
sample_cfg = lime.load_cfg(cfgFile, objList_check=True)

# Load mask
maskDF = lime.load_lines_log(lineMaskFile)

# Load spectrum
wave, flux, header = lime.load_fits(obsFitsFile, instrument='OSIRIS')

# Object properties
z_obj = sample_cfg['sample_data']['z_array'][2]
norm_flux = sample_cfg['sample_data']['norm_flux']

# Run the interative plot
lime.MaskSelector(maskDF, corrected_lineMaskFile, wave, flux, redshift=z_obj, norm_flux=norm_flux)


