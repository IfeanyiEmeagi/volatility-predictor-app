import warnings
warnings.filterwarnings("ignore")

import os
import pandas as pd
from glob import glob

from data import AlphaVantageApi, SQLRepository
import joblib
from arch import arch_model
from config import settings

class GarchModel:
    """ Train the Garch model and make volatility prediction
    Parameters:
    -----------
    ticker: str
        The stock symbol whose volatility will be predicted
    repo: SQLRepository
        The repository where the train data will be saved
    use_new_data: bool
        Whether to download new data from AlphaVantage or use the existing
        data stored in the database
    model_directory: str
        path where the model is stored.

    Methods:
    -------
    wrangle_data
        Generate equity returns from data in database
    fit
        Fit model to training data
    predict
        Predict volatility from trained model
    dump
        Save trained model to file
    load
        Load trained model from file
    """
    

    def __init__(self, ticker, repo, model_directory, use_new_data):
        self.ticker = ticker
        self.repo = repo
        self.use_new_data = use_new_data
        self.model_directory = model_directory
    
    def wrangle_data(self, n_observations):
        """Extract data from database or AlphaVantage api, transform it 
        for training model and attach it to self.data
        
        Parameters:
        -----------
        n_observations: int
            The number of data to retrieve from the database
        
        Returns:
        --------
        None    
        """
        if self.use_new_data:
            api = AlphaVantageApi()
            df = api.get_historical_data(ticker=self.ticker, output_size = "full")
            self.repo.insert_table(table_name=self.ticker, records = df, if_exists = "replace")
        #pull the data from database
        df = self.repo.read_table(table_name = self.ticker, limit = n_observations + 1)

        #Clean the data and attach it to the class as self.data
        df.sort_index(ascending = True, inplace = True)
        df["return"] = df["close"].pct_change() * 100
        self.data = df["return"].dropna()

    def fit(self, p , q):
        """Create model, fit to self.data and attach to self.model
        Parameters:
        -----------
        p: int
            Lag order of the symmetric innovation
        q: int
            Lag order of the volatility

        Returns:
        --------
        None
        """
        #Train model and attach to self.model
        self.model = arch_model(self.data, p=p, q=q, rescale=False).fit(disp=0)

    def __clean_prediction(self, prediction):
        """Reformat prediction to JSON

        Parameters:
        -----------
        prediction: pd.DataFrame
            Variance from archModelForecast

        Returns:
        --------
        dict
            Forecast of volatility. Each key is dated in ISO 8601 format.
            Each value is predicted volatility.

        """
        #Calculate prediction start date
        start = prediction.index[0] + pd.DateOffset(days=1)

        #Prediction date range
        prediction_dates = pd.bdate_range(start=start, periods=prediction.shape[1])

        #Create prediction index labels, ISO 8601 format
        prediction_index = [d.isoformat() for d in prediction_dates]

        #Extract predictions from DataFrame and get its square root
        data = prediction.values.flatten() ** 0.5

        #Combine data and prediction index into series
        prediction_formatted = pd.Series(data, index= prediction_index)

        return prediction_formatted.to_dict()

    
    def predict_volatility(self, horizon=5):
        """Predicts volatility using the self.model

        Parameters:
        ----------
        horizon: int
            Specify the forecast days. By default is set to 5

        Returns:
        -------
        dict
            Forecast of volatility. Each key is date formatted in ISO 8601 format.
            The value is the predicted volatility

        """
        #Generate variance forecast from the self.model
        prediction = self.model.forecast(horizon=horizon, reindex = False).variance

        #Clean the prediction
        prediction_formatted = self.__clean_prediction(prediction)

        #Return the result
        return prediction_formatted


    def dump(self):
        """ Save model to self.model_directory with timestamp

        Returns:
        --------
        str
            file path where the model was saved.
        """
        #Create time stamp in iso format
        timestamp = pd.Timestamp.now().isoformat()

        #Create the file path
        filepath = os.path.join(self.model_directory, f"{timestamp}_{self.ticker}.pkl") 

        #Save the model
        joblib.dump(self.model, filepath)

        return filepath

    def load(self):
        """Load the recent self.model in self.model_directory for the self.ticker

        """
        #Create pattern for glob search
        pattern = os.path.join(self.model_directory, f"*{self.ticker}.pkl")

        #Use the glob to get the most recent model and handle errors
        try:
            model_path = sorted(glob(pattern))[-1]
        except IndexError:
            raise Exception(f"The ticker symbol {self.ticker} is not correct")

        #Load model and attach it to self.model
        self.model = joblib.load(model_path)










        
