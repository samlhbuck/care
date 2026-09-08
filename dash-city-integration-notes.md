# Integrating the CARE Dash App into a City Website

A Dash dashboard cannot simply be pasted into a City webpage because its callbacks require a running Python server. The City would first deploy it as a web service, then integrate that service into the existing site.

| Approach | How it works | Best use |
|---|---|---|
| Standalone link | Seattle page links to the hosted dashboard | Easiest pilot |
| `<iframe>` embed | Existing page embeds the hosted app | Quick visual integration |
| Reverse proxy | City routes a Seattle.gov path to the Dash service | Best way to preserve the app |
| Native rebuild | City developers recreate the interface in the website frontend | Best long-term integration |

## Production deployment

The City would:

1. Package `app.py`, `assets/`, and dependencies.
2. Run it with a production server rather than `app.run(debug=True)`.
3. Host it on an approved City server or cloud platform.
4. Add caching so every visitor does not trigger expensive Socrata queries.
5. Route or embed it within the City site.
6. Complete accessibility, security, privacy, and performance review.

With a current Dash version, a production command could be:

```text
gunicorn app:app --workers 4
```

Plotly documents Gunicorn as the production alternative to running `python app.py`.

## Iframe pilot

An existing content-management page could embed the hosted application:

```html
<iframe
    src="https://dashboard-host.seattle.gov/"
    title="Seattle emergency response explorer"
    width="100%"
    height="900"
    loading="lazy">
</iframe>
```

The dashboard host's security headers would need to permit embedding by `seattle.gov`.

## Same-domain path

A cleaner deployment could give the app a City URL such as:

```text
https://www.seattle.gov/care/response-explorer/
```

A reverse proxy would send requests under that path to the Dash service. The application might need a corresponding prefix:

```python
app = Dash(
    __name__,
    url_base_pathname="/care/response-explorer/",
)
```

## Native integration

For full native integration, the City could retain the analytical design and Python/API layer while rebuilding the visible controls and charts in its existing website framework. This would provide the closest match to City navigation, typography, analytics, and accessibility standards, but require more development.

## Portfolio framing

The prototype does not need to solve the City's deployment infrastructure. A useful handoff statement is:

> The prototype can operate as a standalone public Dash application, be embedded in an existing page, or be deployed behind a City-managed URL path; the query and visualization layers are separated to support later integration into another frontend.

One production issue is already visible in the prototype: `fetch_event_type_options()` should not remain a blocking startup dependency. A deployed version should cache those options or load them after the page becomes available.

## Reference

- [Dash app deployment structure](https://dash.plotly.com/dash-enterprise/application-structure/dash-app?de-version=5.3)
