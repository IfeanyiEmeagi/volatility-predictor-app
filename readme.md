# Volatility Predictor App
The volatility predictor app predicts the volatility of selected ETF stocks using the Autoregressive Conditional Heteroscedastic Model (ARCH).

The application is subdivided into three levels:
* Base level: This is basically the database where the preprocessed historical data are stored.
* Middle level: This is like the businness unit that retrieves information from the base level, applies logic to it, and then passes the information to the visualization level.
* Visualization level: This level uses a Dash application to display the received object figure.
  
The trained models on each ETF stock are saved using the date and time they were trained. This system also utilizes this information (date and time) to trigger training of new model when required. By default, training of new models are initiated once the difference between the model trained date and current date is more than 1.

### Setting Up the Application
- Set up a virtual environment.
- Install all the dependencies listed in the requirements.txt file.
- Run the app.py file.


