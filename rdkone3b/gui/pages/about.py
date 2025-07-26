import random
import pandas as pd
from dash import Input, Output, State, callback, dcc, html, no_update, register_page

df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/solar.csv")


register_page(__name__, path="/about")

layout = html.Div(
    [
        html.H1("Contributions", className="text-center mb-4"),
    ]
)