# CARE Response Explorer

An independent, exploratory Dash/Plotly dashboard using the City of Seattle's published dispatch records. **Not an official City of Seattle or CARE Department product.**

## Problem

For a given type of dispatched request, what does the recorded time to first on-scene response look like across **SPD-only**, **CARE-only**, and **SPD/CARE co-response** events? A single average obscures both the typical wait and unusually long waits. The dashboard makes these distributions easier to compare while keeping the limits of the comparison visible.

## Data / method

- **Source:** [City of Seattle, *Call Data* (dataset 33kz-ixgy)](https://data.seattle.gov/Public-Safety/Call-Data/33kz-ixgy), queried live through the Socrata API. The City describes the dataset as incrementally updated daily and periodically reconciled.
- **Unit:** Distinct CAD event within its recorded response category (deduplicated by `cad_event_number` and category for the plotted summaries).
- **Response-time metric:** `cad_event_first_response_time_s_` / 60, measured in minutes from an event first being queued to **the first responding unit arriving on scene**. It includes dispatch delay and travel, not just driving time. For a co-response event, this **does not necessarily measure when a CARE unit arrived**.
- **Selection:** Choose the inclusive date range and **initial** call type. The event-type dropdown is populated from call types associated with CARE or SPD/CARE co-response; SPD-only events of that same initial call type provide the comparison. Records must have `call_type_indicator = 'DISPATCH'` and a response category of SPD, CARE, or SPD/CARE Co-Response.
- **Excluded records:** On-view / field-initiated events, other or erroneous response categories, missing first-response duration, and durations **under 60 seconds**. The short-duration threshold is an analytical choice that may exclude legitimate rapid responses; reported results apply **only to this filtered population**.
- **Display:** One dot per response category is the median; whiskers span the 25th to 75th percentile; an open diamond marks the 90th percentile; `n` counts distinct included CAD events. A comparison with small `n` should be interpreted cautiously.

## Finding

The dashboard is intended to answer **both** “What is typical?” (median) and “How long is the slower tail?” (90th percentile) for a selected call classification and period. These are different operational questions.

**Verified numerical finding: not yet captured.** Before using this project in an application, fill in the snapshot below **from the live dashboard** rather than implying a measured conclusion without recorded source results:

- Initial call type: *[to record]*
- Inclusive dates: *[to record]*
- Response categories, event counts, median, 25th–75th percentiles, and 90th percentile: *[to record]*
- One-sentence interpretation: *[to record; describe association, not causal performance]*
- Screenshot: *[to capture; use the same filters and date range]*

## Limitation

These response categories are **not comparable treatment groups**. Priority, location, time of day, dispatch protocols, service availability, and case mix may differ, even within the same initial call type. Recorded first-unit arrival is not the same as CARE-only arrival, scene resolution, patient/client outcome, or the quality of a response. Short-duration and missing-timing exclusions create selection bias; dispatched events cleared before a field response may be absent from the published data. Initial classification may differ from final disposition.

**Data integrity check still needed:** `fetch_events` currently requests at most **50,000 rows** for the chosen filter, so a larger response is silently truncated. This is a blocker for using high-volume filter combinations in a published numerical claim until pagination or an explicit coverage check is implemented. Verify sample sizes against a source-side distinct-event count before quoting them.

## Decision supported

The display can help a public-service analyst **identify which call classifications and operating periods warrant closer review**: for example, where a long 90th-percentile tail makes dispatch delay, responder availability, or call-classification practices worth examining. It **cannot** establish whether CARE or SPD is more effective or whether routing a particular caller to one team would improve outcomes.

## Public demonstration checklist

1. Verify the deployment works and the selected call type returns complete data; use a date window that avoids the 50,000-row limit.
2. Select one CARE-relevant initial call type with enough observations in the relevant categories; record the exact dates, `n`, median, and 90th percentile.
3. Capture **one real screenshot** showing selected filters, readable chart title/axis, all intended comparisons, and methodological caveat. Do not substitute fabricated sample values.
4. Paste the measured numbers and one-sentence interpretation into **Finding**, then link the screenshot and the working demo here.
5. Add a simple check for the 50,000-row coverage issue and confirm deployment configuration before claiming the app is production-ready.

## Run locally

Install dependencies from `requirements.txt`, then run `python app.py`. Internet access is needed for the live City of Seattle data API. For a public deployment, provide a production WSGI runner and verify the hosted URL independently.
