import sqlite3

from data import AlphaVantageApi, SQLRepository
from model import GarchModel
from config import settings
from pydantic import BaseModel
from fastapi import FastAPI


class FitIn(BaseModel):
    ticker: str
    use_new_data: bool
    n_observations: int
    p: int
    q: int

class FitOut(FitIn):
    success: str
    message: str

class PredictIn(BaseModel):
    ticker: str
    n_days: int

class PredictOut(PredictIn):
    success: str
    forecast: dict
    message: str


def build_model(ticker, use_new_data):

    #Create DB connection
    connection = sqlite3.connect(settings.db_name, check_same_thread=False)

    #Instantiate the AlphaVantage class
    api = AlphaVantageApi()

    #Instantiate the repo class
    repo = SQLRepository(connection=connection)

    #Instantiate the model class
    model = GarchModel(ticker=ticker, repo=repo, use_new_data=use_new_data)

    return model


app = FastAPI()

#Test case - Hello world
@app.get('/hello', status_code=200)
def hello():
    """Return a dictionary with welcome message"""
    return {"message": "Hello World"}

# Fit path '/fit', status code = 200
@app.post('/fit', status_code = 200, response_model = FitOut)
def fit_model(request: FitIn):
    """Fit model, return confirmation message
    Parameters:
    -----------
    request: FitIn

    Returns:
    --------
    dict
        Must conform to FitOut
    """
    #Create response dictionary from request
    response = request.dict()

    #Use try block to handle exception
    try:
        #Build model with model_build function
        model = build_model(request.ticker, request.use_new_data)

        #Wrangle data
        model.wrangle_data(n_observations=request.n_observations)

        #Fit the model
        model.fit(p=request.p, q=request.q)

        #Save model
        filename = model.dump()

        #Add success key to response
        response["success"] = True

        #Add message key to response with filename
        response["message"] = f"Trained and saved '{filename}'"

    except Exception as e:
        #Add success key to response
        response["success"] = False

        #Add message key to response with filename
        response["message"] = str(e)

    return response


@app.post('/predict', status_code = 200, response_model = PredictOut)
def predict_volatility(request: PredictIn):
    """Predict volatility
    Parameters:
    ----------
    request: PredictIn

    Returns:
    -------
    dict
        conform to PredictOut
    """

    #Create dictionary response
    response = request.dict()

    try:
        #Build model with build_model function
        model = build_model(ticker = request.ticker, use_new_data = False)

        #Load stored model
        model.load()

        #Generate prediction
        prediction = model.predict_volatility(horizon = request.n_days)

        #Add success key to response
        response["success"] = True

        #Add forecast key to response
        response["forecast"] = prediction

        #Add message key to response
        response["message"] = ""

    except Exception as e:
        #Add success key to response
        response["success"] = False

        #Add forecast key to response
        response["forecast"] = {}

        #Add message key to response
        response["message"] = str(e)

    return response