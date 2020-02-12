#!/usr/bin/env python
import common
import json

import matplotlib.pyplot as plt
import numpy as np
import mpld3

# parse input sent from php
raw_metadata = input()
metadata = json.loads(raw_metadata)
shift_results = [common.ShiftResult(info) for info in metadata['shift_info']]
input_options = common.InputOptions(metadata['input'])

# get a list of unique unordered dates (don't want to worry about string comparison), and the corresponding index in all shifts
dates = metadata['all_dates']
x_dates = [dates.index(shift.date) for shift in shift_results]

# get the y value for each shift
parse_function = common.scatter_value_for_input(input_options)
y_rates = [parse_function(shift) for shift in shift_results]

# get the size of the scatter point for each shift
size_function = common.scatter_size_for_input(input_options)
sizes = [size_function(shift) for shift in shift_results]

# lower alpha so overlapping points are visible
alpha = 0.67
color_labels, colors = common.scatter_color_loop(input_options, shift_results)

# x axis labels at every 1/8th of the way through chart
x_ticks = np.arange(len(dates) / 16, len(dates), len(dates) / 8)
x_labels = [str(dates[int(i)]) for i in x_ticks]

# draw the scatter plot!
fig, ax = plt.subplots()
scatter = ax.scatter(x_dates,
                     y_rates,
                     c=colors,
                     s=sizes,
                     alpha=alpha)

# avoid mpld3 bug where linewidths break json export
# https://stackoverflow.com/questions/49584653/mpld3-produces-axes-property-value-that-cannot-be-serialized-to-json
scatter.set_linewidths([])
ax.grid(color='white', linestyle='solid')
ax.set_title(common.graph_title_for_input(input_options), size=20)
ax.axis("tight")
# Cast to float to get around mpld3 json-parsing bug that throws an error on tick 0
ax.xaxis.set_ticks([float(tick) for tick in x_ticks])
ax.xaxis.set_ticklabels(x_labels)

# Add tooltip showing the grouping label when hovering over a point
tooltip = mpld3.plugins.PointLabelTooltip(scatter, labels=color_labels)
mpld3.plugins.connect(fig, tooltip)

# dump figure to json and print it to the php pipe
dict = mpld3.fig_to_dict(fig)
json = json.dumps(dict)
print(json)

