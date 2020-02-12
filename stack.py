#!/usr/bin/env python
import common
from common import MeasurementType

import json

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import mpld3

# converts raw value array to cumulative array.
# eg [0, 1, 2, 3, 4] returns [0, 1, 3, 6, 10]
def to_cumulative_array(array):
   for i in range(1, len(array)):
      array[i] += array[i-1]
   return array

# adds together pairs of values that are in the same group (eg. multiple shifts per day)
def sum_pairs(pairs):
   return (sum([p[0] for p in pairs]), sum([p[1] for p in pairs]))

# converts pairs representing fractions into a cumulative array of weighted rates.
# eg [(1, 2), (3, 2), (12, 4)] which represents [1/2, 3/2, 12/4]
#   has a cumulative weighted average of [0.5, 1.0, 2.0]
def cumulative_rates_from_pairs(pairs):
   numer = to_cumulative_array([p[0] for p in pairs])
   denom = to_cumulative_array([p[1] for p in pairs])
   return [numer[i] / denom[i] if denom[i] > 0 else 0 for i in range(len(pairs))]

def agg_function_for_input(input_options, dates):
   measurement = input_options.measurementType
   measurement_function = common.measurement_function_for_input(input_options)

   # build cumulative array of measurement value for each date
   if measurement == MeasurementType.Signatures:
      return lambda shifts: to_cumulative_array([sum([measurement_function(shift) for shift in shifts if shift.date == date]) for date in dates])
   elif measurement == MeasurementType.Hours:
      return lambda shifts: to_cumulative_array([sum([measurement_function(shift) for shift in shifts if shift.date == date]) for date in dates])
   elif measurement == MeasurementType.HourlyRate:
      return lambda shifts: cumulative_rates_from_pairs([sum_pairs([measurement_function(shift) for shift in shifts if shift.date == date]) for date in dates])

# parse input sent from php
raw_metadata = input()
metadata = json.loads(raw_metadata)
shift_results = [common.ShiftResult(info) for info in metadata['shift_info']]
input_options = common.InputOptions(metadata['input'])
dates = metadata['all_dates']

grouping_function = common.grouping_function_for_input(input_options)
agg_function = agg_function_for_input(input_options, dates)

# get lists of daily measurements for each grouping
sorted_groups, sort_index = np.unique([grouping_function(shift) for shift in shift_results], return_index = True)
all_groups = [z[1] for z in sorted(zip(sort_index, sorted_groups))]
groups_per_date = [agg_function([shift for shift in shift_results if grouping_function(shift) == group]) for group in all_groups]

# set up x axis with dates and 8 tick marks
num_dates = len(dates)
date_x = np.arange(num_dates)
x_ticks = np.arange(num_dates / 16, num_dates, num_dates / 8)
x_labels = [dates[int(i)] for i in x_ticks]

# weighted rainbow for pretty, even color spectrum
visibility_padding = max([d[-1] for d in groups_per_date]) * 0.05
color_weights = [d[-1] + visibility_padding for d in groups_per_date]
color_weights_sum = sum(color_weights)
color_weights = [1.0 * c / color_weights_sum for c in color_weights]
# make weights cumulative from 0-1
cum_weights = to_cumulative_array(color_weights)
cm = plt.get_cmap('gist_rainbow')
color_cycle = [cm(c) for c in cum_weights]

# zero out linewidths to avoid json bug parsing 'edgewidth'
line_widths = [0.0, 0.0]

fig, ax = plt.subplots()
plots = ax.stackplot(date_x, *groups_per_date, colors=color_cycle, linewidths = line_widths, baseline="zero")
ax.axis("tight")
ax.set_title(common.graph_title_for_input(input_options), size=20)

# Remove divider lines so it's a smooth rainbow
[plots[i].set_edgecolor(color_cycle[i]) for i in range(len(plots))]

# Cast to float to get around mpld3 json-parsing bug that throws an error on tick 0
ax.xaxis.set_ticks([float(tick) for tick in x_ticks])
ax.xaxis.set_ticklabels(x_labels)

# Add tooltips for each group on the stack areas
tooltips = [mpld3.plugins.LineLabelTooltip(plots[i], label=str(all_groups[i] + " - " + str(groups_per_date[i][-1]))) for i in range(len(all_groups))]
[mpld3.plugins.connect(fig, tooltip) for tooltip in tooltips]

# dump figure to json and print it to the php pipe
dict = mpld3.fig_to_dict(fig)
json = json.dumps(dict)
print(json)

