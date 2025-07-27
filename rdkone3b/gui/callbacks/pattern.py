#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import os
import dash
import base64
import pandas as pd
import plotly.express as px

from dash import html, Input, Output, State, callback, dash_table, ctx, ALL

import dash_bootstrap_components as dbc

from rdkone3b.preprocess.log_parser import LogParser
from rdkone3b.preprocess.uploaded_file_processor import UPloadedFilesProcessor
from rdkone3b.gui.pages.utils import UPLOAD_DIRECTORY

PARSING_APP = LogParser()

def create_attribute_component(attributes):
    table = dash_table.DataTable(
        id="attribute-table",
        data=[{c: "*" for c in attributes.columns}],
        columns=[
            {"id": c, "name": c, "presentation": "dropdown"} for c in attributes.columns
        ],
        editable=True,
        dropdown={
            c: {
                "options": [{"label": "*", "value": "*"}]
                + [{"label": i, "value": i} for i in attributes[c].unique()]
            }
            for c in attributes.columns
        },
        style_header_conditional=[{"textAlign": "left"}],
        style_cell_conditional=[{"textAlign": "left"}],
    )
    return html.Div(children=[table, html.Div(id="table-dropdown-container")])

"""
@callback(
    Output("attribute-name-options", "options"),
    Output("attribute-name-options", "value"),
    [
        Input(component_id="log-type-select", component_property="value"),
    ],
)
def get_attributes(log_type):
    attributes = PARSING_APP.get_attributes()
    if attributes is None:
        return [], []

    options = [{"label": str(c), "value": str(c)} for c in attributes]
    values = [str(c) for c in attributes]
    return options, values
"""

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

def list_merged_files():
    """List all files saved in the uploads folder."""
    try:
        merged_logs_path = os.path.join(UPLOAD_DIRECTORY, "merged_logs")
        return sorted(os.listdir(merged_logs_path))
    except FileNotFoundError:
        return []


@callback(
    Output('filelist-dropdown', 'children'),
    [
        Input('upload-data', 'filename'),
        Input('upload-data', 'contents'),
    ],
)
def file_processing( filenames, contents):

    ctx = dash.callback_context
    try:
        if ctx.triggered:
            prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if prop_id == "upload-data":
                if filenames and contents:
                    for name, data in zip(filenames, contents):
                        save_file(name, data)

                    all_files = list_uploaded_files()

                    if not all_files:
                        return [dbc.DropdownMenuItem("No files uploaded", disabled=True)]

                    # Extract and Merge uploaded files
                    process_files = UPloadedFilesProcessor()
                    process_files.process_uploaded_files()

                    merged_files = list_merged_files()
                    return [
                        dbc.DropdownMenuItem(
                            name,
                            id={"type": "file-item", "index": i},
                            n_clicks=0,
                            href=None  # Prevent navigation
                        )
                        for i, name in enumerate(merged_files)
                        ]
        else:
            return [dbc.DropdownMenuItem("File not selected!", disabled=True)]
    except Exception as error:
        return [dbc.DropdownMenuItem("Error occured", disabled=True)]

"""
# === Show selected file name from dropdown click ===
callback(
    Output("attribute-options", "children"),
    Input({"type": "file-item", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def update_selected_file_label(n_clicks_list):
    print("Callback Map Keys:", app.callback_map.keys())
    triggered_id = ctx.triggered_id

    if not triggered_id or "index" not in triggered_id:
        return ""

    index = triggered_id["index"]

    # Get up-to-date file list from disk
    merged_files = list_merged_files()
    selected_file = merged_files[index] if index < len(merged_files) else None
    if not selected_file:
        return
    
    PARSING_APP.parse_logs(selected_file)

    return (
            create_attribute_component(
                PARSING_APP.get_attributes()
            ),
        )
"""
# === Show selected file name from dropdown click ===
callback(
    Output("attribute-options", "children"),
    Output("selected-file-label", "children"),
    Input({"type": "file-item", "index": ALL}, "n_clicks"),
)
def update_selected_file_label(n_clicks_list):
    print("Button was clicked!", flush=True)
    triggered_id = ctx.triggered_id

    if not triggered_id or "index" not in triggered_id:
        return ""

    index = triggered_id["index"]

    # Get up-to-date file list from disk
    all_files = list_merged_files()
    # Get up-to-date file list from disk
    merged_files = list_merged_files()
    selected_file = merged_files[index] if index < len(merged_files) else None
    if not selected_file:
        return
    
    PARSING_APP.parse_logs(selected_file)
    print("Button was clicked! list files", flush=True)
    
    if index < len(all_files):
        print("Button was clicked! list files", flush=True)
        #return f"Selected: {all_files[index]}"
    
    return (
        f"Selected: {all_files[index]}",
            create_attribute_component(
                PARSING_APP.get_attributes()
            ),
        )

@callback(Output("log-patterns", "children"), [Input("summary-scatter", "clickData")])
def update_log_pattern(data):
    if data is not None:
        res = data["points"][0]["customdata"]

        return html.Div(
            children=[html.B(res)],
            style={
                "width": "100 %",
                "display": "in-block",
                "align-items": "left",
                "justify-content": "left",
            },
        )
    else:
        return html.Div()


@callback(
    Output("log-dynamic-lists", "children"), [Input("summary-scatter", "clickData")]
)
def update_dynamic_lists(data):
    if data is not None:
        df = PARSING_APP.get_dynamic_parameter_list(
            data["points"][0]["customdata"]
        )
        df["values"] = df["values"].apply(lambda x: ", ".join(set(filter(None, x))))
        df = df.rename(
            columns={"position": "Position", "value_counts": "Count", "values": "Value"}
        )
        columns = [{"name": c, "id": c} for c in df.columns]
        return dash_table.DataTable(
            data=df.to_dict("records"),
            columns=columns,
            style_table={"overflowX": "scroll"},
            style_cell={"max-width": "900px", "textAlign": "left"},
            editable=False,
            row_selectable="multi",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
        )
    else:
        return dash_table.DataTable()


@callback(
    Output("select-loglines", "children"), [Input("summary-scatter", "clickData")]
)
def update_logline(data):
    if data is not None:
        df = PARSING_APP.get_log_lines(data["points"][0]["customdata"])
        columns = [{"name": c, "id": c} for c in df.columns]
        return dash_table.DataTable(
            data=df.to_dict("records"),
            columns=columns,
            style_table={"overflowX": "scroll"},
            style_cell={
                "max-width": "900px",
                "textAlign": "left",
            },
            editable=True,
            row_selectable="multi",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            page_action="native",
            page_size=20,
            page_current=0,
        )
    else:
        return dash_table.DataTable()


@callback(
    Output("summary-scatter", "figure"),
    [Input("attribute-table", "data")],
)
def update_summary_graph(data):
    attribute = []
    for c in data:
        for k, v in c.items():
            if not v == "*":
                attribute.append({k: v})

    scatter_df = PARSING_APP.summary_graph_df(attribute)

    fig = px.bar(
        scatter_df,
        x="order",
        y="counts",
        labels={"order": "log pattern", "counts": "Occurrence (Log Scale)"},
        hover_name=scatter_df.index.values,
    )
    fig.update_traces(customdata=scatter_df.index.values)

    fig.update_yaxes(type="log")

    fig.update_layout(margin={"l": 40, "b": 40, "t": 10, "r": 0}, hovermode="closest")
    return fig


@callback(
    Output("pattern-time-series", "figure"),
    [Input("summary-scatter", "clickData"), Input("time-interval", "value")],
    prevent_initial_call=True,
)
def update_y_timeseries(data, interval):
    print(data)
    interval_map = {0: "1s", 1: "1min", 2: "1h", 3: "1d"}
    pattern = data["points"][0]["customdata"]
    freq = interval_map[interval]
    result_df = PARSING_APP.result_table
    dff = result_df[result_df["parsed_logline"] == pattern][
        ["timestamp", "parsed_logline"]
    ]

    ts_df = (
        dff[["timestamp", "parsed_logline"]]
        .groupby(pd.Grouper(key="timestamp", freq=freq, offset=0, label="right"))
        .size()
        .reset_index(name="count")
    )

    title = "Trend of Occurrence at Freq({})".format(freq)
    return create_time_series(ts_df, "Linear", title)


def create_time_series(dff, axis_type, title):
    fig = px.scatter(
        dff,
        x="timestamp",
        y="count",
        labels={"count": "Occurrence", "timstamp": "Time"},
        title=title,
    )

    fig.update_traces(mode="lines+markers")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(type="linear" if axis_type == "Linear" else "log")
    fig.update_layout(margin={"l": 20, "b": 30, "r": 10, "t": 30})
    return fig


@callback(
    Output("log-summarization-summary", "children"),
    [
        Input("attribute-table", "data"),
    ],
)
def summary(data):
    if len(data) > 0:
        result_table = PARSING_APP.result_table
        total_loglines = result_table.shape[0]
        total_log_patterns = len(result_table["parsed_logline"].unique())

        return html.Div(
            [
                html.P("Total Number of Loglines: {}".format(total_loglines)),
                html.P("Total Number of Log Patterns: {}".format(total_log_patterns)),
            ]
        )
    else:
        return html.Div(
            [
                html.P("Total Number of Loglines: "),
                html.P("Total Number of Log Patterns: "),
            ]
        )
