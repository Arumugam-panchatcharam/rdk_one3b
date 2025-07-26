import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, ALL
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.io as pio
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_ag_grid as dag
import pandas as pd

from rdkone3b.gui.pages.utils import UPLOAD_DIRECTORY

import os
import base64
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
else:
    for fname in os.listdir(UPLOAD_DIRECTORY):
        fpath = os.path.join(UPLOAD_DIRECTORY, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)

# adds  templates to plotly.io
load_figure_template(["darkly"])

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
from flask import Flask
flask_server = Flask(__name__)
app = Dash(__name__,
           suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
           title="RDK_One3B",
           use_pages=True,
           server=flask_server,
           )

RDKONE3B_LOGO = "./assets/img/rdk_one3b_logo.png"

NAVBAR = {
    "Preproces": {
        "Overview": {"icon": "bi bi-house", "relative_path": "/"},
    },
    "Analysis": {
        "Analysis": {"icon": "bi bi-file-bar-graph", "relative_path": "/preprocess"},
    },
    "About": {
        "About": {"icon": "bi bi-info-circle", "relative_path": "/about"},
    },
}

# === Upload + Dropdown section for navbar ===
upload_controls = dbc.Row(
    [
        dbc.Col(
            dcc.Upload(
                id="upload-data",
                children=dbc.Button("Upload Files", color="primary", outline=True),
                multiple=True,
            ),
            width="auto",
        ),
        dbc.Col(
            dbc.DropdownMenu(
                id='filelist-dropdown',
                label="Select File",
                menu_variant="dark",
                children=[
                    dbc.DropdownMenuItem("No files uploaded", disabled=True, n_clicks=0, href=None),
                ],
                style={"marginLeft": "15px"},
            ),
            width="auto",
        ),
        dbc.Col(
            html.Span(id="selected-file-label", style={"fontWeight": "bold", "marginLeft": "15px"}),
            width="auto",
        ),
    ],
    align="center",
    className="g-2",
)

# === Save uploaded file to local folder ===
def save_file(name, content):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    file_path = os.path.join(UPLOAD_DIRECTORY, name)
    with open(file_path, "wb") as f:
        f.write(decoded)

def list_uploaded_files():
    """List all files saved in the uploads folder."""
    try:
        return sorted(os.listdir(UPLOAD_DIRECTORY))
    except FileNotFoundError:
        return []

# === Update dropdown list on upload ===
@app.callback(
    Output('filelist-dropdown', 'children'),
    Input('upload-data', 'filename'),
    Input('upload-data', 'contents'),
)
def update_dropdown(filenames, contents):
    if filenames and contents:
        for name, data in zip(filenames, contents):
            save_file(name, data)

    all_files = list_uploaded_files()

    if not all_files:
        return [dbc.DropdownMenuItem("No files uploaded", disabled=True)]

    return [
        dbc.DropdownMenuItem(
            name,
            id={"type": "file-item", "index": i},
            n_clicks=0,
            href=None  # Prevent navigation
        )
        for i, name in enumerate(all_files)
    ]


# === Show selected file name from dropdown click ===
@app.callback(
    Output("selected-file-label", "children"),
    Input({"type": "file-item", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def update_selected_file_label(n_clicks_list):
    triggered_id = ctx.triggered_id

    if not triggered_id or "index" not in triggered_id:
        return ""

    index = triggered_id["index"]

    # Get up-to-date file list from disk
    all_files = list_uploaded_files()
    
    if index < len(all_files):
        return f"Selected: {all_files[index]}"
    
    return ""

def generate_nav_links(navbar_dict):
    nav_items = []
    for category, items in navbar_dict.items():
        # Add a category header
        nav_items.append(html.Div(category, className="navbar-category"))
        # Add links for each item in the category
        for label, details in items.items():
            nav_items.append(
                dbc.NavLink(
                    [
                        html.I(className=details["icon"], style={"margin-right": "0.8rem"}),
                        label,
                    ],
                    href=details["relative_path"],
                    className="nav-link",
                )
            )
    return nav_items

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    #"background-color": "#f8f9fa",
}

sidebar = html.Div(
    [
        html.Img(src=RDKONE3B_LOGO, width=200, className="mb-0"),
        html.Hr(),
        #html.P("RDK_One3B App", className="lead"),
        dbc.Nav([], vertical=True, pills=True, id="sidebar-nav"),
    ],
    style=SIDEBAR_STYLE,
    className="d-none d-md-block",  # Hidden on small screens, visible on medium+
    id="sidebar",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            dcc.Link(
                [
                    html.Img(src=RDKONE3B_LOGO, width=30, height=30, className="ms-2"),
                    "RDK_One3B",
                ],
                href="/",
                className="navbar-brand",
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                generate_nav_links(NAVBAR),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
    className="d-block d-md-none",  # Visible only on small screens, hidden on medium+
)

content = html.Div(
    dbc.Spinner(
        dash.page_container,
        delay_show=0,
        delay_hide=100,
        color="primary",
        spinner_class_name="fixed-top",
        spinner_style={"margin-top": "100px"},
    ),
    className="content",
)

app.layout = html.Div(
    [
        dbc.Navbar(
        dbc.Container([
                dbc.NavbarBrand("", className="me-4"),
                upload_controls
            ]),
            color="transparent",
            dark=True,
            sticky="top",
            className="shadow-0",
        ),
        dcc.Location(id="url"),
        sidebar,
        navbar,
        content,
    ]
)


@app.callback(Output("sidebar-nav", "children"), Input("url", "pathname"))
def update_navbar(url: str) -> list:
    return [
        html.Div(
            [
                html.H5(navbar_group),
                html.Hr(),
                html.Div(
                    [
                        dcc.Link(
                            html.Div(
                                [html.I(className=page_values["icon"] + " mr-1"), page_name],
                                className="d-flex align-items-center",
                            ),
                            href=page_values["relative_path"],
                            className="nav-link active mb-1"
                            if page_values["relative_path"] == url
                            else "nav-link mb-1",
                        )
                        for page_name, page_values in navbar_pages.items()
                    ]
                ),
            ],
            className="mb-4",
        )
        for navbar_group, navbar_pages in NAVBAR.items()
    ]


@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks"), Input("url", "pathname")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, _, is_open):
    # close collapse when navigating to new page
    if dash.callback_context.triggered_id == "url":
        return False

    if n:
        return not is_open
    return is_open

if __name__ == "__main__":
    app.run(debug=True, port=8080)
