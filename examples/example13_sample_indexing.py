import numpy as np
import pandas as pd
import lime
from pathlib import Path

spectrum_log_path = Path(f'sample_data/gp121903_linelog.txt')
sample_log_path = Path(f'sample_data/sample_log.txt')

# Load the logs
log_spec = lime.load_log(spectrum_log_path)

sample = lime.Sample()
sample.load_log(sample_log_path)

# # Select fluxes and compute the line ratios
# flux_entry_headers = ['line_flux', 'line_flux_err']
# lime.extract_fluxes(log_spec, column_names=flux_entry_headers, column_positions=[1, 2])
# lime.relative_fluxes(log_spec, 'H1_4861A', flux_entries=flux_entry_headers, column_positions=[1, 2])
# ratio_log = lime.compute_line_ratios(log_spec, ['H1_6563A/H1_4861A', 'O3_5007A/O3_4959A'],
#                                      flux_columns=flux_entry_headers)
#
# lime.save_log(log_spec, Path(f'sample_data/gp121903_relativeLineLog.txt'))
# lime.save_log(ratio_log, Path(f'sample_data/gp121903_ratiosLineLog.txt'))
#
#
# # Same for the sample object
# sample.extract_fluxes()
# sample.relative_fluxes('H1_4862A')
# ratio_log = sample.compute_line_ratios(line_ratios=['H1_6565A/H1_4862A', 'O3_5008A/O3_4960A'])
# sample.save_log(Path(f'sample_data/sample_relative_log.txt'))
# lime.save_log(ratio_log, Path(f'sample_data/sample_ratio_log.txt'))


# import pandas as pd
# import lime
# from pathlib import Path
# import numpy as np
#
# log_folder = Path(r'D:\Dropbox\Astrophysics\Data\CEERs\reduction_v0.1\fluxes')
# file_list = list(log_folder.glob(f'*.txt'))
#
# log_dict = {}
# for file in file_list:
#     log = lime.load_log(file)
#     obj_ref = file.stem[:-7]
#     log_dict[obj_ref] = log
#
# obj_list, log_list = list(log_dict.keys()), list(log_dict.values())
# sample = lime.Sample(list(log_dict.keys()), log_list=log_list)
#
# # Setting the indeces names
# sample.log.rename_axis(index=["id", "line"], inplace=True)
# # sample.log.index.set_names(['ref', 'line'], inplace=True)
#
# # Get unique lines
# sample.log.index.get_level_values('line').unique()
#
# # Get string parts from a column and add them as new columns to a dataframe
# param_list = ['point', 'disp', 'MPT', '_MPT', 'ext']
# obs_ref_comps = sample.log.index.get_level_values('id').str.split('_', expand=True)
# obs_ref_comps.set_names(param_list, inplace=True)
# for param in param_list:
#     sample.log[param] = obs_ref_comps.get_level_values(param)
#
# # Change type to numeric
# sample.log['MPT'] = pd.to_numeric(sample.log['MPT'])
#
# # Sorting by a few columns
# sample.log.sort_values(by=['MPT', 'disp', 'point', 'wavelength'], ascending=[True, False, True, True], inplace=True)
#
# log_address = Path(r'C:\Users\lativ\OneDrive\Desktop\sample_log.txt')
# ratios_address = Path(r'C:\Users\lativ\OneDrive\Desktop\ratios_log.txt')
# sample.save_log(log_address)

# lime.extract_fluxes(sample.log, column_names=['line_flux', 'line_flux_err'], column_positions=[1, 2])
# lime.relative_fluxes(sample.log, normalization_line='H1_4862A', flux_entries=['line_flux', 'line_flux_err'], column_positions=[1, 2])
# ratios_df = lime.line_ratios(sample.log, ['H1_6565A/H1_4862A', 'O3_5008A/O3_4960A'], flux_entries=['line_flux', 'line_flux_err'])
#
#
# log_address = Path(r'C:\Users\lativ\OneDrive\Desktop\test_log.txt')
# ratios_address = Path(r'C:\Users\lativ\OneDrive\Desktop\ratios_log.txt')
# sample.save_log(log_address)
# print(sample.log)
# lime.save_log(ratios_df, ratios_address)

# log = lime.load_log(log_address, sample_levels=['ref', 'line'])
# print(log)

# sample.save_log(log_address)
# log2 = lime.load_log(log_address)
# lime.save_log(sample.log.reset_index(1), log_address)
#
# log_address = Path(r'C:\Users\lativ\OneDrive\Desktop\test_log.txt')
# lime.save_log(sample.log.reset_index(), log_address)
# b = lime.load_log(log_address)
#
# isinstance(sample.log.index, pd.MultiIndex)
#
# b.set_index(['ref', 'line'], inplace=True)
#
# series_log = sample.log.iloc[0]
# series_b = b.iloc[0]
#
# for item, value in series_b.items():
#     print(item, value, series_log[item], '\t \t \t \t', value == series_log[item])


# df_slice = sample.panel.xs('O3_5008A', level="line")
#
# obj_slice_list = sample.panel.xs('O3_5008A', level="line", drop_level=False).index
# # obj_slice_list2 = df_slice.index
#
# sample.plot.properties('z_line', 'intg_flux', obj_slice_list, y_param_err='intg_err')


# import matplotlib.pyplot as plt
# import mplcursors
# import numpy as np
#
# labels = ["a", "b", "c", "d", "e"]
# x = np.array([0, 1, 2, 3, 4])
#
# fig, ax = plt.subplots()
# line, = ax.plot(x, x, "ro")
# mplcursors.cursor(ax).connect("add", lambda sel: sel.annotation.set_text(labels[sel.index]))
#
# plt.show()

# Get list of objects and their components
# observation_list = sample.panel.index.get_level_values('ref').values.astype(str)

# # Get unique lines elements
# df_slice = sample.panel.xs('O3_5008A', level="line")
#
# # Get a row
# line_flux = sample.panel.loc[('p10_G140M_11088_s11088_x1d', 'O2_3727A'), 'intg_flux']
# line_flux = sample.panel.loc['p10_G140M_11088_s11088_x1d'].loc['O2_3727A', 'intg_flux']
#
# # Get object observations
# obj_index = sample.panel.index.get_level_values('ref').str.contains('323')
# obj_index = sample.panel.MPT == 323
# panel_slice = sample.panel.loc[obj_index]




