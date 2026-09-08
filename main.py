from pprint import pprint

import requests

endpoint = "https://data.seattle.gov/resource/33kz-ixgy.json"

params = {
    "$select": """
        --date_extract_y(cad_event_original_time_queued) AS year,
        date_extract_m(cad_event_original_time_queued)
        --cad_event_response_category,
        initial_call_type,
        priority,
        count(DISTINCT cad_event_number) AS events
    """,
    "$where": """cad_event_original_time_queued >= '2023-10-26T00:00:00' 
    and cad_event_response_category like '%CARE%'""",
    "$group": "year, cad_event_response_category, initial_call_type",
    "$order": "year, cad_event_response_category",
}
params = {
    "$limit": 10,
    "$where": """
        cad_event_original_time_queued >= '2023-10-26T00:00:00'
        AND cad_event_response_category LIKE '%CARE%'
    """,
    "$order": "cad_event_original_time_queued DESC",
}
response = requests.get(endpoint, params=params, timeout=30)
response.raise_for_status()
results = response.json()

pprint(results)
