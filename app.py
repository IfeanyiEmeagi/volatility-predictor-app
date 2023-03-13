import dash_bootstrap_components as dbc
import os
import datetime
import pandas as pd
import plotly.express as px
import sqlite3
from config import settings
import dash
from dash import Input, Output, State, dcc, html, Dash
from enginehouse import ProcessWorkflow
from data import AlphaVantageApi, SQLRepository
from model import GarchModel
import time



app = Dash( 
    external_stylesheets=[dbc.themes.DARKLY])

#Instantiate the Process Workflow
work_flow = ProcessWorkflow()

#Selected list of ETF and Stocks
item_list = [
    "AGZ-iShares Agency Bond ETF ",
    "AMJ-JPMorgan Chase & Company ETF",
    "BAD-B.A.D. ETF",
    "CUT-Invesco MSCI Global Timber ETF",
    "ACB-Aurora Cannabis Stock",
    "IBM-International Business Machines Corp Stock",
    "ADBE-Adobe Stock",
    "ADP-Automatic Data Processing Inc Stock"
]

def graph_func(prediction, ticker):
    df_pred = pd.DataFrame(prediction, index=["prediction"]).transpose()
    ds_pred = df_pred["prediction"]
    fig = px.line(ds_pred, x=ds_pred.index, y= "prediction", markers=True, title = f"{ticker} 5 Day Volatility Prediction")
    fig.update_layout(xaxis_title = "Date", yaxis_title = "Price")
    return fig


inputs = [{"label": x, "value": x} for x in sorted(item_list)]

#Layout section: Bootstrap using Darkly themes
#----------------------------------------------


app.layout = dbc.Container(
    [
        dbc.Row(
                [
                    dbc.Col(html.H1("Volatility Predictor App", className="text-center text-success mb-4"), width=12)
                ]
                ),
        dbc.Row(
                [
                    
                     dbc.Col(dbc.Select(id="select", value=f"{list(inputs[0].values())[1]}", options=inputs, className="mb-4"),
                                           width={"size": 4, "offset": 1, "order": 2}),
                    dbc.Col(dbc.RadioItems(id="radio_items", value="Volatility", 
                                           options= [{"label":"6D-Rolling Volatility", "value": "Volatility"}, 
                                                    {"label": "Price", "value": "Price"}], inline = True), width={"size": 3, "offset": 1, "order": 3}),
                     dbc.Col(dbc.Button("Prediction", id="predictions", n_clicks =0, size="lg", color="success", className="mb-4"), 
                                    width={"size": 3, "order": 1})
                            
                ]
                ),
        dbc.Row(
                [
                   dbc.Col(id="price_volatility", className="mb-2", width={"size": 8, "order": 5}),
                   dbc.Col(id="my_prediction", className="mb-2",  width={"size": 4,  "order": 4})
                    
                ]
                ),
        dbc.Row(
                [
                 dbc.Col(dbc.Card(dbc.CardBody([
                   html.H6("Guide:", className = "card-title"),
                   html.P("Select a stock or ETF from the dropdown to view the 6-day rolling volatility or the last 2000 historical price and " 
                          "the prediction of next five days volatility. The app uses a daily trained Garch model for each ticker to make its prediction.")
                        
                 ])  ), style = {"width":"18rem"}),
                dbc.CardBody(html.P("Build by Ifeanyi Emeagi. This is for educational purposes and not a financial advise."), 
                             style = {"color": "orange"} )
                ]
                )
    ], fluid=True
)


#Callback section
#*****************

@app.callback(
    Output("price_volatility", "children"), 
    [   Input("select", "value"),
        Input("radio_items", "value")]
)
def price_volatility_graph(symbol, selected_option):
    global ticker 
    ticker = symbol.split('-')[0]
    time.sleep(2)
    fig = work_flow.plot_graph(ticker, selected_option)

    return dcc.Graph(figure = fig) 

@app.callback(
    Output("my_prediction", "children"),
    [
    #Input("predictions", "n_clicks"),
    Input("select", "value"),
    ]
)
def predict(symbol):
    if (symbol != ""):
        time.sleep(3)
        ticker = symbol.split('-')[0]
        file_paths = os.listdir("models/")
        today_date = datetime.datetime.now().date().strftime("%Y-%m-%d")
        for path in file_paths:
            fitted_ticker = path.split('.')[1].split('_')[1]
            fitted_date = path.split('T')[0]

            if (ticker == fitted_ticker) & (fitted_date == today_date):
                #call the prediction function
                key = True
                break
            else: 
                key = False
        if key:
            prediction = work_flow.predict_volatility(n_days=5)
            fig = graph_func(prediction, ticker)
            return dcc.Graph(figure = fig)
        else:
            #call the fit function
            work_flow.fit_model(ticker, use_new_data=False, p=1, q=1)
            #call the prediction function
            prediction = work_flow.predict_volatility(n_days=5)
            #plot the predictions on a graph
            fig = graph_func(prediction, ticker)

            return dcc.Graph(figure = fig)
    else:
        return dash.no_update()
    


if __name__ == "__main__":
    app.run_server(debug=True, port=8000)
  






