from functools import lru_cache

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from dash import Dash, Input, Output, callback, dcc, html

ENDPOINT = "https://data.seattle.gov/resource/33kz-ixgy.json"


class Columns:
    # Event identity and classification
    EVENT_ID = "cad_event_number"
    RESPONSE_CATEGORY = "cad_event_response_category"
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

def fetch_event_type_options():
    params = {
        "$select": (
        f"{Columns.INITIAL_CALL_TYPE}, "
        f"count(distinct {Columns.EVENT_ID}) as num_events"
        ),
        "$where": (
            "cad_event_original_time_queued >= '2023-10-26T00:00:00' "
            f"AND {Columns.INITIAL_CALL_TYPE} IS NOT NULL "
            f"AND {Columns.RESPONSE_CATEGORY} like '%CARE%' "
            f"AND {Columns.EVENT_FIRST_RESPONSE_SECONDS} > 60"
        ),
        "$group": f"{Columns.INITIAL_CALL_TYPE} ",
        "$order": "num_events DESC,"
        f"{Columns.INITIAL_CALL_TYPE} ASC",
        "$limit": 5000,
    }

    response = requests.get(ENDPOINT, params=params, timeout=30)
    response.raise_for_status()
    results = response.json()

   
    return [
        {
            "label": (
                f"{row[Columns.INITIAL_CALL_TYPE]} "
                f"({row['num_events']} CARE-related events)"
            ),
            "value": row[Columns.INITIAL_CALL_TYPE],
        }
        for row in results
    ]


@lru_cache(maxsize=8)
def fetch_events(response_categories, event_type):
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

    params = {
        "$select": (
            f"distinct {Columns.EVENT_ID}, "
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
            f"{Columns.QUEUED_TIME} >= '2023-10-26T00:00:00' "
            f"AND {Columns.RESPONSE_CATEGORY} IN ({quoted_categories}) "
            f"AND {Columns.INITIAL_CALL_TYPE} = '{safe_event_type}' "
            f"AND {Columns.EVENT_FIRST_RESPONSE_SECONDS} is not null "
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


EVENT_TYPE_OPTIONS = fetch_event_type_options()
app = Dash(__name__)


app.layout = html.Main(
    [
        html.H1("CARE Response Explorer"),
        html.P("""Explore how event types have historically
        moved through Seattle's emergency response system"""),
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
            options=EVENT_TYPE_OPTIONS,
            placeholder="Search event types",
            searchable=True,
            clearable=True,
        ),
        dcc.Graph(id="response-chart"),
    ]
)


@callback(
    Output("response-chart", "figure"),
    Input("response-category", "value"),
    Input("event-type", "value"),
)
def update_chart(response_categories, event_type):
    if not response_categories:
        return px.bar(title="Select at least one category")

    if not event_type:
        return px.bar(title="Select an event type")

    events = fetch_events(
        tuple(sorted(response_categories)), event_type
    )

    if not events:
        return px.bar(
            title=f"No response data found for: {event_type}"
        )
    
    short_names = {
        "SPD": "SPD",
        "CARE": "CARE",
        "SPD/CARE Co-Response": "Co-response",
    }

    event_ids_by_category = {}

    for row in events:
        category = row["response_unit"]

        event_ids_by_category.setdefault(category, set()).add(
            row[Columns.EVENT_ID]
        )

    counts = {
        category: len(event_ids)
        for category, event_ids in event_ids_by_category.items()
    }

    for row in events:
        category = row["response_unit"]
        row["response_label"] = (
            f"{short_names[category]}<br>"
            f"n={counts[category]:,}"
        )
    
    positive_events = [
        row
        for row in events
        if row["response_minutes"] > 0
    ]
    
    response_figure = px.box(
        positive_events,
        x="response_label",
        y="response_minutes",
        color="response_unit",
        points="outliers",
        title=f"Response time — {event_type}",
        labels={
            "response_label": "",
            "response_minutes": "Response time (minutes)",
        },
    )

    response_figure.update_traces(
        hoveron="boxes+points",
        hovertemplate=None,
    )
    short_names = {
        "SPD": "SPD",
        "CARE": "CARE",
        "SPD/CARE Co-Response": "Co-response",
    }

    for trace in response_figure.data:
        trace.name = short_names.get(trace.name, trace.name)

    response_figure.update_layout(showlegend=False)
    
    return response_figure


if __name__ == "__main__":
    app.run(debug=True)
