import sqlite3
import pandas as pd
from config import settings
import requests


class AlphaVantageApi:
    def __init__(self, api_key = settings.alpha_api_key):
        self.__api_key = api_key

    def get_historical_data(self, ticker, output_size = "full"):
        """
        A method that downloads the historical data from Alpha Vantage website
        Parameters:
        -----------
        ticker: str
            The stock or the index symbol.
        output_size: str optional
            It has two options: compact and full. 'Compact' downloads the latest 100 days price of the selected ticker,
            while the 'full' downloads all the available data for the ticker. The default value is 'full'
        
        Return
        ------
        df: Dataframe
            The method returns a dataframe with open, high, low and close as columns and a datetime index named date.
        """

        self.ticker = ticker
        url = ("https://www.alphavantage.co/query?"
                    "function=TIME_SERIES_DAILY_ADJUSTED&"
                    f"symbol={ticker}&"
                    f"outputsize={output_size}&"
                    f"apikey={self.__api_key}"
                )
        #Send a get request to Alpha Vantage server
        response = requests.get(url=url) 

        #Extract the json from the response
        response_json = response.json()

        #Catch invalid ticker exception
        if "Time Series (Daily)" not in response_json.keys():
            raise Exception (
                f"Invalid API call. Check that the ticker symbol:'{ticker}' is correct"
            )

        #Extract the Daily Time series
        data_dict = response_json["Time Series (Daily)"]

        #Convert the data dictionary into DataFrame
        df = pd.DataFrame.from_dict(data_dict, orient = "index", dtype = float)

        #Convert the index to datetime and set the name to date
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"

        #Clean the column names
        df.columns = [c.split(". ")[1] for c in df.columns] 

        #Drop the unwanted columns
        df = df.drop(["adjusted close", "volume", "dividend amount", "split coefficient"], axis = 1)

        return df

class SQLRepository:
    def __init__(self, connection):
        self.connection = connection

    def insert_table(self, table_name, records, if_exists = "fail"):
        """
        Insert the DataFrame in SQlite database

        Parameters:
        -----------
        table_name: str
            the ticker symbol can be used as a table_name
        records: DataFrame
        if_exists: str optional
            'fail' - If the table exist, fail and raise error message
            'replace' - Replace the table with the new records
            'append' - Append the new record at the end of the existing record

        Returns: dict
            'Transaction successful: bool'
            'Number of records inserted: int
        """
        n_inserted = records.to_sql(name = table_name, con=self.connection, if_exists = if_exists)

        return {
            "Transaction successful": True,
            "Number of records inserted": int(len(records))
        }

    def read_table(self, table_name, limit=None):
        """
        Read the data from the database using a set limit.

        Parameters
        ----------
        table_name: str
            The name of the database
        limit: int, optional
            It retrieve the most recent value of the limit from the database. When set to none, it retrieve 
            all the data. The default value is none.
            
        Returns
        ------
        pd.DataFrame
            Index is DatetimeIndex "date. Column names are open, high, low and close
            All column values are numeric
        """

        #Create the sql query with limit
        if limit:
            sql = f"SELECT * FROM '{table_name}' LIMIT '{limit}'"
        else:
            sql = f"SELECT * FROM '{table_name}'"

        #Retrieve the data
        df = pd.read_sql(sql = sql, con=self.connection, parse_dates = ["date"], index_col="date")

        #Return DataFrame
        return df

        