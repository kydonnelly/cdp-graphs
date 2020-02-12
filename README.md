# CDP Graphs
Files used to create graphs analyzing shift reports submitted to the Community Democracy Project's signature gathering campaign, built by Kyle / Cooperative 4 the Community. You can view pie graphs, scatter plots, and stack plots. Supports grouping by name, location, overall progress, etc.

## Environment
PHP: 7.3.14

Python: 3.7.6

NumPy: 1.18.1

Matplotlib: 3.1.3

mpld3: 0.3

WordPress: 5.2.5

WordPress plugin Code Embed: 2.3.2

Gather 10-100,000 signatures for participatory budgeting (or other direct democracy practices) in your community, and keep track of names/dates/locations/signatures.

## Installation
Track shift reports in your database, or import from another tool like Google Sheets. Use '-' for any shifts that are missing hours. See sql file for db schema.

Add cdp-graphs to your server's wp-content/plugin directory and activate it from WordPress plugins. Make sure the python and php files are in this same directory and executable.

Copy/Paste the top of cdp-graphs.html into your WordPress page using Code Editor. 
Copy/Paste the javascript functions into the Code Embed area of the WordPress page.

## Screenshots
Stack plot showing the cumulative number of signatures gathered by all volunteers at Any location.

![Image of stack plot](https://cooperative4thecommunity.com/wp-content/uploads/2020/02/sum_stack.png)

Scatter plot showing the hourly signature gathering rate at Sprouts for All volunteers over six months.

![Image of scatter plot](https://cooperative4thecommunity.com/wp-content/uploads/2020/02/sprouts_scatter.png)

Weekly scatter plot showing the hourly signature gathering rate for Kyle at All locations.

![Image of weekly scatter plot](https://cooperative4thecommunity.com/wp-content/uploads/2020/02/kyle_weekly.png)

Pie chart showing the time spent by Ellen at All locations.

![Image of pie chart](https://cooperative4thecommunity.com/wp-content/uploads/2020/02/ellen_pie.png) 

## Acknowledgements
Tia, Victoria, and Emily for meticulous data gathering and recording.
