import random
import pandas as pd
from dash import Input, Output, State, callback, dcc, html, no_update, register_page
import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_ag_grid as dag

register_page(__name__, path="/preprocess")


layout = html.Div(
    [
        html.H1("Preprocess Data", className="text-center mb-4"),
    ]
    )
