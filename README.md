# Invisible Hands API Triage

Invisible Hands API Triage is a small methodological prototype and Streamlit research demonstrator for working with V&A Collections API metadata. It searches object records through the V&A CSV endpoint, displays catalogue fields, scores records for archival tractability, and recommends next archival follow-up steps.

The app is related to research questions around craft labour, attribution, place, material process, technique, and documentation gaps in the context of the AHRC CDP project "Invisible Hands: Migrant Labour and British Craft in the Long Eighteenth Century" at UCL and the V&A.

## What the App Does

- Queries the V&A Collections API CSV endpoint.
- Displays object records and object page links.
- Shows thumbnails where a `_primaryImageId` is present, with a sidebar Thumbnail limit slider controlling how many image-bearing records are previewed.
- Adds a transparent archival tractability score from visible catalogue fields.
- Adds evidence-status labels and evidence reasons.
- Recommends archival next steps for follow-up research.
- Allows CSV export through the browser.
- Includes fallback sample rows so the interface still works if the live API is unavailable.

## What the App Does Not Do

- It does not identify migrant makers automatically.
- It does not infer migrant status from names, places, maker fields, or catalogue metadata alone.
- It does not use machine learning, LLM summaries, network graphs, private credentials, or stored secrets.
- It does not claim historical proof from catalogue metadata alone.

## Why the Score Is Archival Tractability

The score is "archival tractability", not "migrant likelihood". It counts visible catalogue fields that can make a record easier to follow up through archives: object type, title, place, maker name, maker role, date, material, technique, and image id.

A high score means the record may offer more catalogue-supported routes into archival work. It does not mean the object, maker, place, or technique proves anything about migrant labour. Any historical claim must be checked against external evidence such as object files, departmental card indexes, business archives, apprenticeship records, company records, correspondence, ledgers, and other archival sources.

## Catalogue Evidence, Archival Follow-Up, and Labour Visibility

Museum catalogue data can help researchers notice where craft labour might be more visible, partially visible, or difficult to trace. This app separates catalogue-supported clues from research prompts and evidence gaps. It is designed as a triage device for deciding which object records may deserve closer archival attention.

Fallback rows in `data/sample_records.csv` are illustrative sample data. They are not authoritative V&A records unless live API data is loaded from the V&A Collections API.

## Install Dependencies on Windows

Run these commands in PowerShell from the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks environment activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run Locally on Windows

From the repository root, run:

```powershell
python -m streamlit run app.py
```

After dependencies are installed, Windows users can also run the app by double-clicking:

```text
run_app.bat
```

The app entrypoint is:

```text
app.py
```

No credentials, API keys, passwords, or `secrets.toml` file are required.

## Panel-facing use

This prototype should be treated as an optional demonstration of method rather than a formal research output. It is intended to show how V&A Collections API metadata can support first-stage archival triage by making catalogue clues, evidence gaps, and follow-up routes more explicit.

## Run Tests on Windows

```powershell
python -m pytest -q
python -m py_compile app.py
python -m py_compile src\__init__.py
python -m py_compile src\vam_api.py
python -m py_compile src\scoring.py
python -m py_compile src\archival_routes.py
python -m py_compile src\utils.py
```

## Deploy online with Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app.
4. Select the GitHub repository.
5. Select the main branch.
6. Set the app file / entrypoint to:

```text
app.py
```

7. Deploy.
8. Test the public URL in an incognito/private browser window.

The deployed app is an optional methodological prototype, not a formal research output. The app should be tested shortly before sharing with a panel because free hosted apps may sleep after inactivity. If the live API is unavailable, use the fallback sample data checkbox to demonstrate the method.
