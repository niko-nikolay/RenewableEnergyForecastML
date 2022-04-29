In this project I like to use weather data (temperature, wind, solar flux) with respect to location data to predict the solar and wind energy production. ML techniques will be used for the prediction and hopefully to identify hot spots (i.e. coordinates where the weather has most influence; should coincide with wind and solar farms).

Installation process with linux

1. create virtual environment
	python3 -m venv ./python_venv
2. activate virtual environment
	source ./python_venv/bin/activate
3. install requirements
	python3 -m pip install -r ./python_venv/requirements.txt


after usage, deactivate virtual environment
	deactivate
