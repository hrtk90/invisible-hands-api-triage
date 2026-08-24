# Invisible Hands: V&A Collections API Research Prototype

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22082885.svg)](https://doi.org/10.5281/zenodo.22082885)
[![GitHub release](https://img.shields.io/github/v/release/hrtk90/invisible-hands-api-triage)](https://github.com/hrtk90/invisible-hands-api-triage/releases)
[![License: MIT](https://img.shields.io/github/license/hrtk90/invisible-hands-api-triage)](LICENSE)
[![Top language](https://img.shields.io/github/languages/top/hrtk90/invisible-hands-api-triage)](https://github.com/hrtk90/invisible-hands-api-triage)
[![V&A Collections API](https://img.shields.io/badge/Data%20source-V%26A%20Collections%20API%20v2-555555)](https://developers.vam.ac.uk/collections/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?logo=streamlit&logoColor=white)](https://invisible-hands-api-triage.streamlit.app/)

Invisible Hands: V&A Collections API Research Prototype is an independent Streamlit-based research demonstrator for exploratory work with V&A Collections API metadata. It searches object records through the V&A CSV endpoint, displays catalogue fields, scores records for archival tractability, and recommends potential archival follow-up routes.

**Live demo:** [Open the Streamlit prototype](https://invisible-hands-api-triage.streamlit.app/)

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

## Research Scope and Intended Use

This prototype tests how V&A Collections API metadata can support first-stage archival triage by making catalogue-supported clues, documentation gaps, and potential follow-up routes more explicit. Its outputs support close object study and archival research by providing a structured exploratory layer for collections-data analysis.

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

The deployed app should be checked before it is shared or cited in application materials, as free hosted apps may sleep after inactivity. If the live API is unavailable, the fallback sample data provides an illustrative demonstration of the workflow.

## License

The source code in this repository is available under the MIT License.

V&A collections data accessed through the API remains subject to the V&A's applicable terms of use.
