# CARE Response Explorer

**Explore the distribution of emergency-dispatch response times in Seattle's CARE and police-response data.**

A Dash/Plotly dashboard for exploring [Seattle's published dispatch event data](https://data.seattle.gov/resource/33kz-ixgy.json), with filters for call type, response category, and time period.

## Problem and audience

Seattle's Community Assisted Response and Engagement (CARE) program and the Seattle Police Department (SPD) can respond to different kinds of calls. Simple overall averages can hide differences in timing and call mix. How do response-time distributions vary among **CARE**, **SPD/CARE co-response**, and **SPD** for a selected *initial call type* and date range?

The application is designed for curious residents, journalists, civic researchers, and public-sector analysts who want to examine the underlying descriptive patterns. It is an independent exploration, not an official City of Seattle dashboard or an evaluation of which response model is superior.

## What it shows

- Select one or more response categories and a specific initial call type.
- Compare predefined periods (including recent windows and calendar years) or choose custom dates.
- Inspect the **median, 25th percentile, 75th percentile, and 90th percentile** of the source's first-response-time metric, in minutes.
- See the number of distinct dispatch events represented in each selected category.
- Explore the comparison in a Plotly chart built with Python, pandas, and Dash.

### Screenshots / demo

The current repository does not document a verified public demo URL or include a captured screenshot. The app can be viewed locally using the steps below. A representative screenshot and a tested public deployment link should be added before making this repository a featured public portfolio item.

## Data and methods

The application queries the City of Seattle's public [dispatch dataset](https://data.seattle.gov/resource/33kz-ixgy.json) through its Socrata API. It selects records with a non-null event-first-response-time field, the **DISPATCH** call-type indicator, matching initial call type and response category, and a date range based on the event's original queued timestamp.

Response seconds are converted to minutes. Within each response category, pandas calculates quantiles and distinct event counts; Plotly renders the middle 50% around the median and a separate 90th-percentile marker. API results are cached in process for repeated combinations of filters.

## Important limitations

- **Descriptive, not causal.** Categories may differ in dispatch criteria, urgency, call mix, operating periods, staffing, and geography. These comparisons do not identify the effect of CARE on response times or establish service quality.
- **Know the metric.** The visualization uses the published **cad_event_first_response_time_s_** field; it is not a reconstruction of every responder's arrival, on-scene service, or resolution time.
- **Coverage and completeness.** Results depend on the completeness, definitions, and updates of the underlying City dataset. Missing response-time values are excluded.
- **Query limit.** The current API retrieval uses a 50,000-row limit without pagination or a completeness warning. Broad filters may therefore return an incomplete set. Do not publish broad-period estimates as definitive without addressing this.
- **Event counts and timing.** Counts use distinct dispatch-event identifiers, but quantiles are calculated from returned response-time records. Interpretation depends on source-row granularity.
- **Operational limits.** The dashboard needs a working connection to the City API; the repository does not provide a fixed, versioned analysis dataset or a verified hosted URL.

## Run locally

Requires Python 3 and internet access to retrieve the published City records.

~~~bash
git clone https://github.com/samlhbuck/care.git
cd care
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
~~~

Open **http://127.0.0.1:8050** (Dash's usual development address). The **app.py** module contains the dashboard and query logic; **assets/style.css** supplies styling. **requirements.txt** lists Python dependencies, including Dash, pandas, Plotly, requests, and Gunicorn.

## Deployment and next steps

The repository includes configuration for a Plotly Cloud app, but no public app URL is recorded here. Before a public portfolio launch, validate current data definitions and large-query completeness, verify a deployed demo, capture an authentic dashboard screenshot, and review the repository for anything that should remain private.

This is an exploratory analytical tool, not a completed policy-impact study.