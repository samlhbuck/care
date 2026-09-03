import requests

endpoint = "https://data.seattle.gov/resource/33kz-ixgy.json"

params = {
    "$select": """
        date_extract_y(cad_event_original_time_queued) AS year,
        cad_event_response_category,
        count(DISTINCT cad_event_number) AS events
    """,
    "$where": "cad_event_original_time_queued >= '2023-10-26T00:00:00'",
    "$group": "year, cad_event_response_category",
    "$order": "year, cad_event_response_category"
}

response = requests.get(endpoint, params=params, timeout=30)
response.raise_for_status()
results = response.json()