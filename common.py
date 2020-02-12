from enum import Enum

import matplotlib.pyplot as plt
import numpy as np

class MeasurementType(Enum):
	Signatures = 'Signatures'
	Hours = 'Hours'
	HourlyRate = 'Hourly Rate'

class InputOptions:
	def __init__(self, metadata):
		# All fields required
		self.name = metadata['name']
		self.location = metadata['location']
		self.measurementType = MeasurementType(metadata['measurement'])

class ShiftResult:
	def __init__(self, metadata):
		# No fields individually required; caller knows context from InputOptions
		self.name = metadata.get('name')
		self.location = metadata.get('location')
		self.date = metadata.get('date')
		self.num_signatures = int(metadata.get('num_signatures', 0))
		self.total_hours = float(metadata.get('total_hours', 0))
		self.start_time = metadata.get('start_time')
		self.end_time = metadata.get('end_time')

# Key can be used to group shift reports for aggregation or coloring
def grouping_function_for_input(input_options):
	if input_options.name == 'All':
		return lambda result: result.name
	elif input_options.location == 'All':
		return lambda result: result.location
	else:
		return lambda result: result.date

# This info gets used for aggregation in the caller
def measurement_function_for_input(input_options):
	measurement = input_options.measurementType

	if measurement == MeasurementType.Signatures:
		return lambda result: result.num_signatures
	elif measurement == MeasurementType.Hours:
		return lambda result: result.total_hours
	elif measurement == MeasurementType.HourlyRate:
		return lambda result: (result.num_signatures, result.total_hours)

def scatter_value_for_input(input_options):
	measurement = input_options.measurementType

	# Higher primary measurement value goes higher in the scatter y-axis
	if measurement == MeasurementType.Signatures:
		return lambda result: result.num_signatures
	elif measurement == MeasurementType.Hours:
		return lambda result: result.total_hours
	elif measurement == MeasurementType.HourlyRate:
		return lambda result: result.num_signatures / result.total_hours

def scatter_size_for_input(input_options):
	measurement = input_options.measurementType

	# Higher secondary measurement (rate, shift length) gets bigger point size in the scatter plot
	if measurement == MeasurementType.Signatures:
		# Typical range (5, 25) -> (40, 200)
		return lambda result: result.num_signatures / result.total_hours * 8
	elif measurement == MeasurementType.Hours:
		# Typical range (5, 25) -> (40, 200)
		return lambda result: result.num_signatures / result.total_hours * 8
	elif measurement == MeasurementType.HourlyRate:
		# Typical range (0.5, 3) -> (36, 216)
		return lambda result: result.total_hours * 72

def scatter_color_loop(input_options, shift_results):
	# group shifts based on input then cycle through colors
	color_key = grouping_function_for_input(input_options)
	color_labels = [color_key(shift) for shift in shift_results]
	color_groups, color_indexes = np.unique(color_labels, return_inverse=True)
	color_cycle = wrapping_color_cycle(len(color_groups))
	colors = [color_cycle[i] for i in color_indexes]

	return color_labels, colors

def wrapping_color_cycle(num_groups):
	color_map = plt.get_cmap('gist_rainbow')

	# kind of arbitrary wrapping loop through the color cycle
	# meant to spread out colors so the graph isn'doesn't have too much of a single color
	# TODO: smarter way to distribute this?
	color_step = int(num_groups / 7) * 1.15 + 1
	return [color_map((color_step * n % num_groups) / num_groups) for n in range(num_groups)]

def graph_title_for_input(input_options):
	name = input_options.name
	location = input_options.location
	measurement = input_options.measurementType.value

	if name == 'All':
		return measurement + " for " + input_options.location + " by Name"
	elif location == 'All':
		return measurement + " for " + input_options.name + " by Location"
	elif name == 'Any':
		return measurement + " for all locations"
	elif location == 'Any':
		return measurement + " for all names"
	else:
		return measurement + " for " + input_options.name + " at " + input_options.location
