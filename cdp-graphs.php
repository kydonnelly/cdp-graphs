<?php
/**
 * Plugin Name: CDP Graphs
 * Plugin URI: https://www.cooperative4thecommunity.com/cdp-graphs
 * Description: A plugin to generate and display graphs from the CDP Voter database.
 * Version: 1.0
 * Author: Kyle Donnelly
 * Author URI: https://www.cooperative4thecommunity.com
 */

defined( 'ABSPATH' ) || exit;

// Database uses these tokens for shifts where time wasn't reported
define('HOURS_MISSING_TOKEN', '-');
define('TIME_MISSING_TOKEN', '');

// enum for user-facing measurement options
abstract class MeasurementType {
  const Signatures = 'Signatures';
  const Hours = 'Hours';
  const HourlyRate = 'Hourly Rate';

  public static function allTypes() {
    return [self::Signatures, self::Hours, self::HourlyRate];
  }
}

// enum for user-facing chart types
abstract class ChartType {
  const Stack = 'Stack';
  const Pie = 'Pie';
  const Scatter = 'Scatter';
  const WeeklyScatter = 'Weekly Scatter';
  const List = 'List';

  public static function script_for_type($chartType) {
    switch ($chartType) {
      case self::Stack:
        return 'stack.py';
      case self::Pie:
        return 'pie.py';
      case self::Scatter:
        return 'scatter.py';
      case self::WeeklyScatter:
        return 'weekly_scatter.py';
      case self::List:
        // Lists are handled entirely in php
        return null;
    }
  }

  public static function allTypes() {
    return [self::Stack, self::Scatter, self::WeeklyScatter, self::Pie, self::List];
  }

  public static function is_scatter($chartType) {
    return ($chartType == self::Scatter || $chartType == self::WeeklyScatter);
  }
}

function cdp_graph_table_name() {
  global $wpdb;
  return $wpdb->prefix . "shift_reports";
}

function cdp_graph_table_query($query) {
  global $wpdb;
  return $wpdb->get_results($query);
}

function cdp_select_for_input($name, $location, $measurement, $type) {
  $cols = [];
 
  // showing all names instead of filtering by them
  if ($name == 'All') {
    $cols[] = 'name';
  }

  // showing all locations instead of filtering by them
  if ($location == 'All') {
    $cols[] = 'location';
  }

  // pie charts don't include dates,
  //   except the special case of All/All where the pieces will be dates.
  if ($type != ChartType::Pie || ($location != 'All' && $name != 'All')) {
    $cols []= 'date';
  }

  // Weekly scatter shows hourly x axis
  if ($type == ChartType::WeeklyScatter || $type == ChartType::List) {
    $cols[] = 'start_time';
    $cols[] = 'end_time';
  }

  // Scatters use total_hours to determine point sizes
  if (ChartType::is_scatter($type) || $measurement == MeasurementType::HourlyRate || $measurement == MeasurementType::Hours) {
    $cols[] = 'total_hours';
  }

  // Scatters show number of signatures / rate in the y axis
  if (ChartType::is_scatter($type) || $measurement == MeasurementType::HourlyRate || $measurement == MeasurementType::Signatures) {
    $cols[] = 'num_signatures';
  }

  return $cols;
}

function cdp_where_for_input($name, $location, $measurement, $type) {
  $clauses = [];

  if ($name != 'All' && $name != 'Any') {
    $clauses []= ['name', '=', $name];
  }

  if ($location != 'All' && $location != 'Any') {
    $clauses []= ['location', '=', $location];
  }
  
  if ($measurement == MeasurementType::HourlyRate || $measurement == MeasurementType::Hours || ChartType::is_scatter($type)) {
    // Hourly Rate and Hours measure the total_hours, so ignore any shifts without that.
    // Scatters use the total hours to determine point sizes.
    // TODO: update so that they show a default size instead of ignoring those shifts.
    $clauses []= ['total_hours', '!=', HOURS_MISSING_TOKEN];
  }

  if ($type == ChartType::WeeklyScatter) {
    // Weekly scatter shows hourly x axis
    $clauses []= ['start_time', '!=', TIME_MISSING_TOKEN];
    $clauses []= ['end_time', '!=', TIME_MISSING_TOKEN];
  }

  if (empty($clauses)) {
    return "";
  } else {
    $mapped = array_map(function($c) { return "$c[0] $c[1] '$c[2]'"; }, $clauses);
    return " WHERE " . join(' AND ', $mapped);
  }
}

function cdp_should_show_all_dates($type) {
  return ($type == ChartType::Scatter || $type == ChartType::Stack);
}

function cdp_graph_load() {
  // ignore initial (or any) page load where the user didn't submit yet
  if (!isset($_POST['submit'])) {
    return;
  }

  $name = $_POST['volunteer'];
  $location = $_POST['location'];
  $measurement = $_POST['measurement'];
  $type = $_POST['type'];

  $safe_name = sanitize_text_field($name);
  $safe_location = sanitize_text_field($location);

  $select_cols = cdp_select_for_input($safe_name, $safe_location, $measurement, $type);
  $where_query = cdp_where_for_input($safe_name, $safe_location, $measurement, $type);

  $table_name = cdp_graph_table_name();
  $select_query = join(', ', $select_cols);
  $query = "SELECT $select_query FROM $table_name $where_query;";
  $results = cdp_graph_table_query($query);

  if (empty($results)) {
    return;
  }

  // convert result objects into associative array
  $shift_results = array_map(function($r) use ($select_cols) {
    $shift_result = array();
    foreach ($select_cols as $col) {
      $shift_result[$col] = $r->$col;
    }
    return $shift_result;
  }, $results);
  
  $all_dates = [];
  if (cdp_should_show_all_dates($type)) {
    // ASSUMPTION: dates are sorted
    $dates_query = "SELECT DISTINCT date FROM $table_name;";
    $dates_results = cdp_graph_table_query($dates_query);
    $all_dates = array_map(function($r) { return $r->date; }, $dates_results);
  }

  echo cdp_graph_html($name, $location, $measurement, $type, $shift_results, $all_dates, $select_cols);
}

function cdp_load_mpld3_graph($name, $location, $measurement, $type, $shift_info, $all_dates) {
  // Send info to the python script as JSON
  $metadata = [
    'shift_info' => $shift_info,
    'all_dates' => $all_dates,
    'input' => [
      'location' => $location,
      'name' => $name,
      'measurement' => $measurement
    ]
  ];
  $metajson = json_encode($metadata);
  $script_name = __DIR__ . '/' . ChartType::script_for_type($type);

  // proc_open the script so we can write the metadata then read the output
  $descriptorspec = array(
    0 => array("pipe", "r"),
    1 => array("pipe", "w"),
    2 => array("pipe", "w")
  );
  $script_cmd = 'python3 ' . $script_name;
  $process = proc_open($script_cmd, $descriptorspec, $pipes);

  fwrite($pipes[0], $metajson . "\n");
  $output = '';
  while (!feof($pipes[1])) {
    $output .= fgets($pipes[1]);
  }

  // Uncomment this to debug any setup errors
  // while (!feof($pipes[2])) {
  //   echo 'error ' .  fgets($pipes[2]);
  // }

  fclose($pipes[2]); 
  fclose($pipes[1]);
  fclose($pipes[0]);
  $ret_close = proc_close($process);

  return $output;
}

function cdp_graph_html($name, $location, $measurement, $type, $shift_info, $all_dates, $cols) {
    if ($type == ChartType::List) {
      // Show simple table of all shifts, no fancy charts
      $html = "<table style=\"width:100%\">\n";
      $html .= "<tr>\n";
      foreach ($cols as $col) {
        $html .= "<th>" . $col . "</th>\n";
      }
      $html .= "</tr>\n";
      foreach ($shift_info as $info) {
        $html .= "<tr>\n";
        foreach ($cols as $col) {
          $html .= "<th>" . $info[$col] . "</th>\n";
        }
        $html .= "</tr>\n";
      }
      $html .= "</table>";

      return $html;
    } else {
      // Load mpld3 js libraries and then draw the graph
      $html = "";
      $html .= "<script>\n";
      $html .= "cdp_load_graph_library(\"https://mpld3.github.io/js/d3.v3.min.js\", function(){\n";
      $html .= "  cdp_load_graph_library(\"https://mpld3.github.io/js/mpld3.v0.3.js\", function(){\n";
      $html .= "    mpld3.draw_figure(\"fig_el538247566028465488501563758\",\n";
      $html .= cdp_load_mpld3_graph($name, $location, $measurement, $type, $shift_info, $all_dates);
      $html .= "    )\n";
      $html .= "  })\n";
      $html .= "});\n";
      $html .= "</script>\n"; 

      return $html;
    }
}

function cdp_dropdown_menu_html($id, $options) {
  $html = "<select name=\"$id\" id=\"$id\">\n";
  foreach ($options as $option) {
    $html .= "<option value=\"" . $option . "\"";
    if ($option == $_POST[$id]) {
      $html .= " selected";
    }
    $html .= ">" . $option . "</option>\n";
  }
  $html .= "</select><br />\n";
  return $html;
}

function cdp_db_dropdown_menu_html($id, $colname) {
  // Gets list of dropdown options from the database (all names, locations, etc)
  $query = "SELECT DISTINCT $colname FROM " . cdp_graph_table_name() . " ORDER BY $colname;";
  $results = cdp_graph_table_query($query);
  $options = array_map(function ($r) use ($colname) { return $r->$colname; }, $results);

  // Add All, Any at top of list for charts that don't filter by this field
  array_unshift($options, "Any");
  array_unshift($options, "All");

  return cdp_dropdown_menu_html($id, $options);
}

function cdp_graph_form_code() {
  echo '<form action="" id="graph_form" method="post">';
  echo '<p>Name: ' . cdp_db_dropdown_menu_html('volunteer', 'name');
  echo '<p>Location: ' . cdp_db_dropdown_menu_html('location', 'location');
  echo '<p>Measurement: ' . cdp_dropdown_menu_html('measurement', MeasurementType::allTypes());
  echo '<p>Graph Type: ' . cdp_dropdown_menu_html('type', ChartType::allTypes());
  echo '<p><input type="submit" name="submit" id="submitButton" value="Submit">';
  echo '</form>';
}

function cf_embed_python_graph_shortcode() {
  // wordpress entry point
  ob_start();

  cdp_graph_form_code();
  cdp_graph_load();

  return ob_get_clean();
}

add_shortcode('cdp_embed_python_graph', 'cf_embed_python_graph_shortcode');
?>
