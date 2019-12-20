# Transportation Cost Visualization Data
This project creates data for the [transportation-cost-viz](https://github.com/thomaslorincz/transportation-cost-viz) project
## Requirements
- Python 3.x
- Create a [virtual environment](https://docs.python.org/3/tutorial/venv.html): ```python -m venv venv```
- Activate the virtual environment:
    - Windows: ```venv\Scripts\activate.bat```
    - Unix or MacOS: ```source venv/bin/activate```
- Install requirements: ```pip install -r requirements.txt```
## Configuration
The data generation script (main.py) requires 2 GeoJSON config files:  ```zones.json``` and ```residences.json.br```.
### zones.json
This file is a [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON) FeatureCollection of all CMA zone boundaries.
This file contains few features so it is stored in the ```config``` directory uncompressed.

Each feature must:
- Contain a unique ```id``` property
- Specify its geometry in [EPSG:3776](https://epsg.io/3776) coordinates (however, the script is easy to modify if a different spatial reference is used)
### residences.json.br
This file is a [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON) FeatureCollection of all CMA residential parcel boundaries (that are currently available).
This file contains many feature so it is stored in the ```config``` directory compressed (see usages of compress.py/decompress.py below).

Each feature must:
- Contain a ```zone``` property that maps to the ```id``` property of the zone that encloses it
- Specify its geometry in [EPSG:3776](https://epsg.io/3776) coordinates (however, the script is easy to modify if a different spatial reference is used)
## Usage
Note: To run any of the following scripts, please ensure that your virtual environment is activated (see requirements above)
### main.py
The main script requires 3 input files: A households file, a persons file, and a trips file.

Execute the following in a command shell:
```
python main.py <path to households file> <path to persons file> <path to trips file> <output file name>
```

Example:
```
python main.py households_2020.csv persons_2020.csv total_trips_2020.csv output_2020.csv
```

The script will output a single CSV with columns: ```lon```, ```lat```, ```cost```, and ```proportion```.
The output file is typically small (~10MB) so it can be directly added to the [transportation-cost-viz](https://github.com/thomaslorincz/transportation-cost-viz) project without compression.
### compress.py
The compress script is used to compress files using the [Brotli](https://en.wikipedia.org/wiki/Brotli) compression algorithm

Execute the following in a command shell:
```
python compress.py <path to file to compress>
```

Example:
```
python compress.py output_2020.csv
```

The script will output a version of the input file that is compressed (e.g. ```output_2020.csv.br```)
### decompress.py
The decompress script is used to decompress files that are compressed with the [Brotli](https://en.wikipedia.org/wiki/Brotli) compression algorithm

Execute the following in a command shell:
```
python decompress.py <path to file to decompress>
```

Example:
```
python decompress.py output_2020.csv.br
```

The script will output a version of the input file that is uncompressed (e.g. ```output_2020.csv```)
