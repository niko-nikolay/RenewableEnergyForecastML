In this project I like to use weather data (temperature, wind, solar flux) with respect to location data to predict the solar and wind energy production. ML techniques will be used for the prediction and hopefully to identify hot spots (i.e. coordinates where the weather has most influence; should coincide with wind and solar farms).

Installation process with linux

1. create virtual environment
	python3 -m venv ./python_venv_renew
2. activate virtual environment
	source ./python_venv_renew/bin/activate
3. install requirements
	python3 -m pip install -r ./python_venv_renew/requirements.txt
4. install and add kernel to jupyter:
	pip install --user ipykernel
	python -m ipykernel install --user --name=python_venv_renew

after usage, deactivate virtual environment
	deactivate



"energy-charts_Electricity_..." contains historical data about the
actual generation of electric energy from wind and solar with a 15 min
resolution, taken from:

https://energy-charts.info/charts/power/chart.htm?l=en&c=DE&stacking=stacked_absolute_area&source=sw&interval=year&year=2020&download-format=text%2Fcsv&timezone=utc
