# Transportation Cost Visualization Data
This project creates data for the [transportation-cost-viz](https://github.com/thomaslorincz/transportation-cost-viz) project
## Requirements
- Python 3.x
- This project has no external dependencies or configuration files
## Usage
The main script requires 3 input files: A households file, a persons file, and a trips file.

Execute the following in a command shell:
```
python main.py <path to households file> <path to persons file> <path to trips file> <output file name>
```

Example:
```
python main.py households_2020.csv persons_2020.csv total_trips_2020.csv output_cost_proportion.csv
```
## Output
The script will output a single CSV with columns: ```zone```, ```cost```, and ```proportion```.
The output file is typically small (~10MB) so it can be directly added to the [transportation-cost-viz](https://github.com/thomaslorincz/transportation-cost-viz) project without compression.
