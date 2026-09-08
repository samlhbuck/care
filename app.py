from datetime import date, timedelta
from functools import lru_cache

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash import Dash, Input, Output, callback, dcc, html

ENDPOINT = "https://data.seattle.gov/resource/33kz-ixgy.json"


class Columns:
    # Event identity and classification
    EVENT_ID = "cad_event_number"
    RESPONSE_CATEGORY = "cad_event_response_category"
    CALL_TYPE_INDICATOR = "call_type_indicator"
    INITIAL_CALL_TYPE = "initial_call_type"
    FINAL_CALL_TYPE = "final_call_type"
    EVENT_GROUP = "event_group"
    PRIORITY = "priority"
    CLEARANCE_DESCRIPTION = "cad_event_clearance_description"

    # Geography
    PRECINCT = "dispatch_precinct"
    SECTOR = "dispatch_sector"
    BEAT = "dispatch_beat"
    NEIGHBORHOOD = "dispatch_neighborhood"
    ADDRESS = "dispatch_address"
    LATITUDE = "dispatch_latitude"
    LONGITUDE = "dispatch_longitude"
    CENSUS_BLOCK = "census_block_2020"

    # Overall event timing
    QUEUED_TIME = "cad_event_original_time_queued"
    ARRIVED_TIME = "cad_event_arrived_time"
    EVENT_FIRST_RESPONSE_SECONDS = "cad_event_first_response_time_s_"

    # First CARE unit
    CARE_DISPATCH_TIME = "first_care_call_sign_dispatch_time"
    CARE_ARRIVAL_TIME = "first_care_call_sign_at_scene_time"
    CARE_LAST_IN_SERVICE_TIME = "last_care_call_sign_in_service_time"
    CARE_DISPATCH_DELAY_SECONDS = (
        "first_care_call_sign_dispatch_delay_time_s_"
    )
    CARE_RESPONSE_SECONDS = (
        "first_care_call_sign_response_time_s_"
    )
    CARE_TOTAL_SERVICE_SECONDS = (
        "care_call_sign_total_service_time_s_"
    )

    # First SPD unit
    SPD_DISPATCH_TIME = "first_spd_call_sign_dispatch_time"
    SPD_ARRIVAL_TIME = "first_spd_call_sign_at_scene_time"
    SPD_LAST_IN_SERVICE_TIME = "last_spd_call_sign_in_service_time"
    SPD_DISPATCH_DELAY_SECONDS = (
        "first_spd_call_sign_dispatch_delay_time_s_"
    )
    SPD_RESPONSE_SECONDS = (
        "first_spd_call_sign_response_time_s_"
    )
    SPD_TOTAL_SERVICE_SECONDS = (
        "spd_call_sign_total_service_time_s_"
    )

    # SPD/CARE co-response
    CO_RESPONSE_DISPATCH_TIME = (
        "first_co_response_call_sign_dispatch_time"
    )
    CO_RESPONSE_ARRIVAL_TIME = (
        "first_co_response_call_sign_at_scene_time"
    )
    CO_RESPONSE_LAST_IN_SERVICE_TIME = (
        "last_co_response_call_sign_in_service_time"
    )
    CO_RESPONSE_DISPATCH_DELAY_SECONDS = (
        "first_co_response_call_sign_dispatch_delay_time_s_"
    )
    CO_RESPONSE_RESPONSE_SECONDS = (
        "first_co_response_call_sign_response_time_s_"
    )
    CO_RESPONSE_TOTAL_SERVICE_SECONDS = (
        "co_response_call_sign_total_service_time_s_"
    )

    # Individual dispatched-unit measurements
    CALL_SIGN_DISPATCH_TIME = "call_sign_dispatch_time"
    CALL_SIGN_ARRIVAL_TIME = "call_sign_at_scene_time"
    CALL_SIGN_IN_SERVICE_TIME = "call_sign_in_service_time"
    CALL_SIGN_DISPATCH_DELAY_SECONDS = (
        "call_sign_dispatch_delay_time_s_"
    )
    CALL_SIGN_RESPONSE_SECONDS = "call_sign_response_time_s_"
    CALL_SIGN_SERVICE_SECONDS = "call_sign_total_service_time_s_"

def optional_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

@lru_cache(maxsize=32)
def fetch_event_type_options(start_date, end_date):
    start = date.fromisoformat(start_date)
    end_exclusive = date.fromisoformat(end_date) + timedelta(days=1)

    params = {
        "$select": (
            f"{Columns.INITIAL_CALL_TYPE}, "
            f"count(distinct {Columns.EVENT_ID}) AS event_count"
        ),
        "$where": (
            f"{Columns.QUEUED_TIME} >= '{start.isoformat()}T00:00:00' "
            f"AND {Columns.QUEUED_TIME} "
            f"< '{end_exclusive.isoformat()}T00:00:00' "
            f"AND {Columns.RESPONSE_CATEGORY} IN "
            "('CARE', 'SPD/CARE Co-Response') "
            f"AND {Columns.EVENT_FIRST_RESPONSE_SECONDS} IS NOT NULL "
            f"AND {Columns.CALL_TYPE_INDICATOR} = 'DISPATCH'"
        ),
        "$group": Columns.INITIAL_CALL_TYPE,
        "$order": "event_count DESC",
        "$limit": 5000,
    }

    response = requests.get(ENDPOINT, params=params, timeout=(5, 60))
    response.raise_for_status()
    results = response.json()

   
    return [
        {
            "label": (
                f"{row[Columns.INITIAL_CALL_TYPE]} "
                f"({row['event_count']} CARE-related events)"
            ),
            "value": row[Columns.INITIAL_CALL_TYPE],
        }
        for row in results
    ]


@lru_cache(maxsize=32)
def fetch_events(
        response_categories,
        event_type,
        start_date,
        end_date,
    ):
    allowed_categories = {
        "SPD",
        "CARE",
        "SPD/CARE Co-Response",
    }
    selected = [
        category for category in response_categories if category in allowed_categories
    ]

    quoted_categories = ", ".join(f"'{category}'" for category in selected)

    safe_event_type = event_type.replace("'", "''")

    start = date.fromisoformat(start_date)
    end_exclusive = date.fromisoformat(end_date) + timedelta(days=1)

    params = {
        "$select": (
            f"{Columns.EVENT_ID}, "
            f"{Columns.LATITUDE},"
            f"{Columns.LONGITUDE},"
            f"{Columns.RESPONSE_CATEGORY},"
            f"{Columns.QUEUED_TIME},"
            f"{Columns.FINAL_CALL_TYPE},"
            f"{Columns.CLEARANCE_DESCRIPTION},"
            f"{Columns.PRIORITY},"
            f"{Columns.SPD_DISPATCH_DELAY_SECONDS},"
            f"{Columns.CARE_DISPATCH_DELAY_SECONDS},"
            f"{Columns.CO_RESPONSE_DISPATCH_DELAY_SECONDS},"
            f"{Columns.EVENT_FIRST_RESPONSE_SECONDS},"
            f"{Columns.SPD_TOTAL_SERVICE_SECONDS},"
            f"{Columns.CARE_TOTAL_SERVICE_SECONDS},"
            f"{Columns.CO_RESPONSE_TOTAL_SERVICE_SECONDS},"
            f"{Columns.BEAT},"
            f"{Columns.NEIGHBORHOOD}"
        ),
        "$where": (
            f"{Columns.QUEUED_TIME} >= '{start.isoformat()}T00:00:00' "
            f"AND {Columns.QUEUED_TIME} "
            f"< '{end_exclusive.isoformat()}T00:00:00' "
            f"AND {Columns.RESPONSE_CATEGORY} IN ({quoted_categories}) "
            f"AND {Columns.INITIAL_CALL_TYPE} = '{safe_event_type}' "
            f"AND {Columns.EVENT_FIRST_RESPONSE_SECONDS} is not null "
            f"AND {Columns.CALL_TYPE_INDICATOR} = 'DISPATCH' "
        ),
        "$limit": 50000,
        "$order": f"{Columns.EVENT_ID}"
    }

    response = requests.get(ENDPOINT, params=params, timeout=30)
    response.raise_for_status()

    results = response.json()


    dispatch_delay_field = {
    "CARE": Columns.CARE_DISPATCH_DELAY_SECONDS,
    "SPD": Columns.SPD_DISPATCH_DELAY_SECONDS,
    "SPD/CARE Co-Response": Columns.CO_RESPONSE_DISPATCH_DELAY_SECONDS,
    }



    for row in results:
        category = row[Columns.RESPONSE_CATEGORY]
        delay_field = dispatch_delay_field[category]

        raw_delay = row.get(delay_field)
        row["dispatch_delay_seconds"] = (
            float(raw_delay) if raw_delay is not None else None
        )   

        response_seconds = float(row[Columns.EVENT_FIRST_RESPONSE_SECONDS])

        raw_delay = row.get(delay_field)
        dispatch_seconds = ( 
            float(raw_delay) if raw_delay is not None else None
        )

        row["response_unit"] = category
        row["response_minutes"] = response_seconds / 60
        row["dispatch_delay_minutes"] = ( 
            dispatch_seconds / 60 
            if dispatch_seconds is not None 
            else None )
        travel_seconds = (
            response_seconds - dispatch_seconds
        )
        row["travel_minutes"] = (
            travel_seconds / 60
            if dispatch_seconds is not None
            and response_seconds >= dispatch_seconds
            else None
        )
        latitude = row.get(Columns.LATITUDE)
        longitude = row.get(Columns.LONGITUDE)

        row["latitude"] = optional_float(
            latitude
        )
        row["longitude"] = optional_float(
            longitude
        )
    
    print("Rows returned:", len(results))

    return results


app = Dash(__name__)


app.layout = html.Main(
    [
        html.Div(
            [
                html.H1("CARE Response Explorer"),
                html.P("""Explore how calls move
                     through Seattle's emergency response system"""),
            ], className = "page-header",
        ),
        html.Div(
            [
                html.Label("Responding Entity"),
                dcc.Dropdown(
                    id="response-category",
                    options=[
                        {"label": "SPD", "value": "SPD"},
                        {"label": "CARE", "value": "CARE"},
                        {"label": "SPD/CARE co-response", "value": "SPD/CARE Co-Response"},
                    ],
                    value=["CARE", "SPD/CARE Co-Response"],
                    multi=True,
                ),
            
                html.Label("Event Type"),
                dcc.Dropdown(
                    id="event-type",
                    options=[],
                    placeholder="Search event types",
                    searchable=True,
                    clearable=True,
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Start date"),
                                dcc.DatePickerSingle(
                                    id="start-date",
                                    min_date_allowed=date(2023, 10, 26),
                                    max_date_allowed=date.today(),
                                    date=date(2023, 10, 26),
                                    display_format="MMM D, YYYY",
                                    clearable=False,
                                ),
                            ],
                            className="date-field",
                        ),
                        html.Div(
                            [
                                html.Label("End date"),
                                dcc.DatePickerSingle(
                                    id="end-date",
                                    min_date_allowed=date(2023, 10, 26),
                                    max_date_allowed=date.today(),
                                    date=date.today(),
                                    display_format="MMM D, YYYY",
                                    clearable=False,
                                ),
                                html.Small(
                                    "Latest available date recommended",
                                    className="field-hint",
                                ),
                            ],
                            className="date-field"
                    ),
                    ],
                    className="date-fields"
                ),
            ],
            className = "filter-grid"),

        html.Div( 
            [
            dcc.Graph(id="response-chart"),
            ], className = "chart-grid"
        )
    ], className = "filter-grid"
)


@callback(
    Output("event-type", "options"),
    Input("start-date", "date"),
    Input("end-date", "date"),
)
def update_event_type_options(start_date, end_date):
    if not start_date or not end_date:
        return []

    return fetch_event_type_options(start_date, end_date)


@callback(
    Output("response-chart", "figure"),
    Input("response-category", "value"),
    Input("event-type", "value"),
    Input("start-date", "date"),
    Input("end-date", "date"),
)
def update_dashboard(response_categories, event_type, start_date, end_date):
    if not response_categories:
        return px.bar(title="Select at least one category")

    if not event_type:
        return px.bar(title="Select an event type")

    if not start_date or not end_date:
        return px.bar(title="Select a date range")

    events = fetch_events(
        tuple(sorted(response_categories)),
        event_type,
        start_date,
        end_date,
    )
    if not events:
        return px.bar(title=f"No response data found for: {event_type}")

    event_frame = pd.DataFrame(events)

    summary = (
        event_frame.groupby("response_unit", as_index=False)
        .agg(
            event_count=(Columns.EVENT_ID, "nunique"),
            q1=("response_minutes", lambda values: values.quantile(0.25)),
            median=("response_minutes", "median"),
            q3=("response_minutes", lambda values: values.quantile(0.75)),
            p90=("response_minutes", lambda values: values.quantile(0.90)),
        )
    )

    short_names = {
        "SPD": "SPD",
        "CARE": "CARE",
        "SPD/CARE Co-Response": "Co-response",
    }

    summary["display_label"] = summary.apply(
        lambda row: (
            f"{short_names[row['response_unit']]} "
            f"(n={row['event_count']:,})"
        ),
        axis=1,
    )

    summary["q3_distance"] = summary["q3"] - summary["median"]
    summary["q1_distance"] = summary["median"] - summary["q1"]

    if not events:
        return px.bar(
            title=f"No response data found for: {event_type}"
        )
    
    short_names = {
        "SPD": "SPD",
        "CARE": "CARE",
        "SPD/CARE Co-Response": "Co-response",
    }
    
    response_figure = go.Figure()

    response_figure.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={
            "family": "Inter, system-ui, sans-serif",
            "color": "#18324a",
        },
        margin={"l": 110, "r": 30, "t": 80, "b": 60},
    )

    response_figure.add_trace(
        go.Scatter(
            x=summary["median"],
            y=summary["display_label"],
            mode="markers",
            marker={
                "size": 13,
                "color": "#275d8c",
            },
            error_x={
                "type": "data",
                "symmetric": False,
                "array": summary["q3_distance"],
                "arrayminus": summary["q1_distance"],
                "thickness": 6,
                "width": 0,
                "color": "#82a9ca",
            },
            customdata=summary[
                ["q1", "q3", "p90", "event_count"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Median: %{x:.1f} minutes<br>"
                "25th percentile: %{customdata[0]:.1f}<br>"
                "75th percentile: %{customdata[1]:.1f}<br>"
                "90th percentile: %{customdata[2]:.1f}<br>"
                "Events: %{customdata[3]:,.0f}"
                "<extra></extra>"
            ),
            name="Median and middle 50%",
        )
    )

    response_figure.add_trace(
        go.Scatter(
            x=summary["p90"],
            y=summary["display_label"],
            mode="markers",
            marker={
                "size": 11,
                "symbol": "diamond-open",
                "color": "#b44b39",
                "line": {"width": 2},
            },
            hovertemplate=(
                "<b>%{y}</b><br>"
                "90% responded within %{x:.1f} minutes"
                "<extra></extra>"
            ),
            name="90th percentile",
        )
    )
    
    return response_figure


if __name__ == "__main__":
    app.run(debug=True)
