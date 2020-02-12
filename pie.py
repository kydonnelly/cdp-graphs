#!/usr/bin/env python
import common
from common import MeasurementType

import json

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import mpld3

# Aggregates output of common.measurement_function_for_input
def agg_function_for_input(input_options):
   measurement = input_options.measurementType

   if measurement == MeasurementType.Signatures:
      return lambda num_sigs: sum([n for n in num_sigs])
   elif measurement == MeasurementType.Hours:
      return lambda num_hours: sum([h for h in num_hours])
   elif measurement == MeasurementType.HourlyRate:
      return lambda ratios: sum([r[0] for r in ratios]) / sum(r[1] for r in ratios)

# custom label formatting for pie pieces
def make_pct(sigs, group_sum, max_precision):
   def formatted_pct(pct):
      val = pct * group_sum / 100.0
      if pct > 10.0:
         precision = str(int(max_precision))
         format_str = "{v:." + precision + "f}"
         return format_str.format(v=val)
      elif pct > 4.0:
         precision = str(int(max_precision / 2))
         format_str = "{v:." + precision + "f}"
         return format_str.format(v=val)
      elif pct > 1.5:
         return "{v:.0f}".format(v=val)
      else:
         return ""
   return formatted_pct

# Caps precision of pie label percentages
def max_precision_for_input(input_options):
   measurement = input_options.measurementType
   if measurement == MeasurementType.Signatures:
      return 0
   elif measurement == MeasurementType.Hours:
      return 2
   elif measurement == MeasurementType.HourlyRate:
      return 2

# parse input sent from php
raw_metadata = input()
metadata = json.loads(raw_metadata)
shift_results = [common.ShiftResult(info) for info in metadata['shift_info']]
input_options = common.InputOptions(metadata['input'])

grouping_function = common.grouping_function_for_input(input_options)
measurement_function = common.measurement_function_for_input(input_options)
agg_function = agg_function_for_input(input_options)

# get unique groups and aggregate the measured values within each group
all_groups = np.unique([grouping_function(shift) for shift in shift_results])
group_values = [agg_function([measurement_function(shift) for shift in shift_results if grouping_function(shift) == group]) for group in all_groups]

# color cycle through all groups (pie pieces)
color_cycle = common.wrapping_color_cycle(len(all_groups))

# custom label formatting setup
group_sum = sum(group_values)
max_precision = max_precision_for_input(input_options)
auto_formatting = make_pct(group_values, group_sum, max_precision)

# Alternate pie chart option: https://medium.com/@kvnamipara/a-better-visualisation-of-pie-charts-by-matplotlib-935b7667d77f
title = common.graph_title_for_input(input_options)
fig, ax = plt.subplots()
_, texts, pct_texts = ax.pie(group_values, labels=all_groups, colors=color_cycle, autopct=auto_formatting, pctdistance=0.8, labeldistance=1.033)
ax.axis('equal')
ax.set_title(title, size=20)

# Mess around with labels
max_size_amount = group_sum * 0.10
[pct_texts[i].set_fontsize(6 + 8 * min(max_size_amount, group_values[i]) / max_size_amount) for i in range(len(pct_texts))]

# dump figure to json and print it to the php pipe
dict = mpld3.fig_to_dict(fig)
json = json.dumps(dict)
print(json)
