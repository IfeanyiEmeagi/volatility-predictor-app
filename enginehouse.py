#Required Libraries

import sqlite3
import plotly.express as px
import datetime

from data import AlphaVantageApi, SQLRepository
from model import GarchModel
from config import settings
import pandas as pd
import plotly.graph_objects as go

def build_model(ticker, use_new_data=False):

    #Create DB connection
    connection = sqlite3.connect(settings.db_name, check_same_thread=False)

    #Instantiate the AlphaVantage class
    api = AlphaVantageApi()

    #Instantiate the repo class
    repo = SQLRepository(connection=connection)

    #Instantiate the model class
    model = GarchModel(ticker=ticker, repo=repo, use_new_data=use_new_data)

    return model


class ProcessWorkflow:

    def __init__(self, repo = SQLRepository(connection=sqlite3.connect(settings.db_name, check_same_thread=False)), api = AlphaVantageApi()):
        self.repo= repo
        self.api = api

    def plot_graph(self, ticker, graph_type, n_observations = 2000):
        self.ticker = ticker
        self.graph_type = graph_type
        self.n_observations = n_observations

        """ Plot Graph
        Parameter
        ========
        Input: ticker: str, graph_type: str

        Return
        ======
        Output: graph fig
        """
        try:
            #check if the table exists in the database
            connection = sqlite3.connect(settings.db_name, check_same_thread=False)
            res = connection.execute("SELECT name FROM sqlite_master WHERE name= '%s' " %ticker)
            if res.fetchone() != None:
                #if the table exist, check if the data is up to date
                data = self.repo.read_table(table_name=ticker, limit=n_observations+1)
                if data.index.max() == datetime.datetime.now().date().strftime('%Y-%m-%d'):
                    data = data
                else:
                    #Download a new data using the ticker
                   
                    data = self.api.get_historical_data(ticker=ticker)
                    self.repo.insert_table(table_name = ticker, records = data, if_exists="replace")
                    data = self.repo.read_table(table_name=ticker, limit=n_observations + 1)
            else:
                #Download a new data using the ticker
                data =self.api.get_historical_data(ticker=ticker)
                self.repo.insert_table(table_name =ticker, records = data, if_exists="replace")
                data = self.repo.read_table(table_name=ticker, limit=n_observations + 1)

            data.sort_index(ascending = True, inplace = True)
            data["return"] = data["close"].pct_change() * 100
            data = data.dropna()

            #Build the graph
            #================
            if graph_type == "Volatility":
                data['rolling_6d_volatility'] = data['return'].rolling(window=6).std().dropna()
                fig = px.line(data, x=data.index, y='rolling_6d_volatility', title = f"{self.ticker} 6D Rolling Volatility")
                fig.update_layout(xaxis_title = "Date", yaxis_title = "Price")
        
            else:
                fig = px.line(data, x=data.index, y='close', title = f"{self.ticker} Historical Price")
                fig = go.Figure(fig)
                fig.update_layout(xaxis_title = "Date", yaxis_title = "Price")
        
        except Exception as e:
            print(str(e))
        
        return fig

    def fit_model(self, ticker, use_new_data: bool, p: int, q: int):
        self.ticker = ticker
        self.use_new_data = use_new_data
        self.p = p
        self.q = q
        """Function, returns confirmation message after training
        Parameters:
        -----------
        Input: ticker: str, use_new_data: bool, n_observations: int, p: int, q: int

        Returns:
        --------
        dict
            
        """

        #Use try block to handle exception
        try:
            #Build model with model_build function
            model = build_model(self.ticker, use_new_data = False)

            #Wrangle data
            model.wrangle_data(n_observations=self.n_observations)

            #Fit the model
            model.fit(p=p, q=q)

            #Save model
            filename = model.dump()

        except Exception as e:
            print(str(e))

        return filename

    def predict_volatility(self, n_days):
        self.n_days = n_days

        try:
            #Build model with build_model function
            model = build_model(ticker = self.ticker)

            #Load stored model
            model.load()

            #Generate prediction
            prediction = model.predict_volatility(horizon = n_days)

        except Exception as e:
            print(e)

        return prediction

