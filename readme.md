This project uses weather data (temperature, wind, solar flux) with respect to locations to predict solar and wind energy production. ML techniques are used for the prediction and to identify hot spots (i.e. coordinates where the weather has most influence; should coincide with wind and solar farms).

Installation process of the virtual environment with linux:

1. create virtual environment

   python3 -m venv ./python_venv_renew

2. activate virtual environment

   source ./python_venv_renew/bin/activate

3. install requirements

   (for Mac with M1 processor execute "brew install gdal" first)
   python3 -m pip install -r ./python_venv_renew/requirements.txt

4. install and add kernel to jupyter:

   pip install --user ipykernel
   python -m ipykernel install --user --name=python_venv_renew

after usage, deactivate virtual environment:

    deactivate

"energy-charts*Electricity*..." contains historical data about the
actual generation of electric energy from wind and solar with a 15 min
resolution, taken from:

https://energy-charts.info/charts/power/chart.htm?l=en&c=DE&stacking=stacked_absolute_area&source=sw&interval=year&year=2020&download-format=text%2Fcsv&timezone=utc
