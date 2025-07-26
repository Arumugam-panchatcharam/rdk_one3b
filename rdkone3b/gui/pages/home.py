import random
import pandas as pd
from dash import Input, Output, State, callback, dcc, html, no_update, register_page

register_page(__name__, path="/")

layout = html.Div(
    [
        html.H1("Overview", className="text-center mb-4"),
    ]
)