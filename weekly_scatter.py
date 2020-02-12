#!/usr/bin/env python
import common
import json

import matplotlib.pyplot as plt
import numpy as np
import mpld3

from datetime import datetime
from time import mktime

# Returns time info for a given string date and time
def to_datetime_str(date, time):
   full_str = date + ' ' + time
   return datetime.strptime(full_str, '%m/%d/%Y %H:%M')

# parse input sent from php
raw_metadata = input()
metadata = json.loads(raw_metadata)
shift_results = [common.ShiftResult(info) for info in metadata['shift_info']]
input_options = common.InputOptions(metadata['input'])

seconds_in_an_hour = 60 * 60
seconds_in_a_day = 24 * seconds_in_an_hour
seconds_in_a_week = 7 * seconds_in_a_day
random_sunday = '6/9/2019'
sunday_date = to_datetime_str(random_sunday, '00:00')
start_sunday = mktime(sunday_date.timetuple())

# Find earliest and latest time
# ASSUMPTION: all shifts start/end on the same day (no shifts through midnight)
min_time = min([to_datetime_str(random_sunday, shift.start_time) for shift in shift_results])
max_time = max([to_datetime_str(random_sunday, shift.end_time) for shift in shift_results])
hour_index = 3 # 0: month, 1: day, 2:year, 3: hour, 4: minute
min_hour = min_time.timetuple()[hour_index]
max_hour = max_time.timetuple()[hour_index]

# ASSUMPTION: shifts are clustered in afternoons/evenings, and no shifts are near midnight.
#   Spread out these clusters a bit by translating along the x-axis
earliest_hour = max(1, min_hour - 2)
latest_hour = min(23, max_hour + 2)
fill_day_multiplier = 24.0 / (latest_hour - earliest_hour)

# Returns the number of seconds into the week (ie from Sunday midnight) for the middle of the shift
#   with some fudging based on the fill_day_multiplier above.
def weekly_timestamp_for_shift(shift):
   start_time = to_datetime_str(shift.date, shift.start_time)
   end_time = to_datetime_str(shift.date, shift.end_time)
   mid_time = 0.5 * (mktime(start_time.timetuple()) + mktime(end_time.timetuple()))
   time_from_sunday = (mid_time - start_sunday) % seconds_in_a_week
   day_index = int(time_from_sunday / seconds_in_a_day)
   return (seconds_in_a_day * day_index) + (time_from_sunday % seconds_in_a_day - earliest_hour * 60 * 60) * fill_day_multiplier

# get the start
x_dates = [weekly_timestamp_for_shift(shift) for shift in shift_results]

# get the y value for each shift
parse_function = common.scatter_value_for_input(input_options)
y_rates = [parse_function(shift) for shift in shift_results]

# get the size of the scatter point for each shift
size_function = common.scatter_size_for_input(input_options)
sizes = [size_function(shift) for shift in shift_results]

# lower alpha so overlapping points are visible
alpha = 0.67
color_labels, colors = common.scatter_color_loop(input_options, shift_results)

# x axis labels every day in the middle of shift hours (roughly)
mid_hour = (earliest_hour + latest_hour) / 2
x_ticks = np.arange(mid_hour * seconds_in_an_hour, seconds_in_a_week, seconds_in_a_day)
x_labels = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

fig, ax = plt.subplots()
scatter = ax.scatter(x_dates,
                     y_rates,
                     c=colors,
                     s=sizes,
                     alpha=alpha)

# avoid mpld3 bug where linewidths break json export
# https://stackoverflow.com/questions/49584653/mpld3-produces-axes-property-value-that-cannot-be-serialized-to-json
# https://tutel.me/c/programming/questions/47808676/pythontypeerror+array+1+is+not+json+serializable
scatter.set_linewidths([])
ax.grid(color='white', linestyle='solid')
ax.set_title(common.graph_title_for_input(input_options), size=20)
ax.axis("tight")
# Cast to float to get around mpld3 json-parsing bug that throws an error on tick 0
ax.xaxis.set_ticks([float(tick) for tick in x_ticks])
ax.xaxis.set_ticklabels(x_labels)

# Add tooltip showing the grouping label when hovering over a point
tooltip_labels = [color_labels[i] + ": " + shift_results[i].start_time + " - " + shift_results[i].end_time for i in range(len(color_labels))]
tooltip = mpld3.plugins.PointLabelTooltip(scatter, labels=tooltip_labels)
mpld3.plugins.connect(fig, tooltip)

# dump figure to json and print it to the php pipe
dict = mpld3.fig_to_dict(fig)
json = json.dumps(dict)
print(json)

