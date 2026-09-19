# OSPERION 0.5.0

**Local-first digital evidence correlation and investigation workspace.**

OSPERION accepts browser Inspect/DOM/View Source/JSON evidence supplied by the user. It extracts observable artifacts, compares them with previously saved observations, and lets the user organize a research project into an **Investigation** containing evidence plus a research journal.

## What changed in 0.4.0

- Added local profile/media image evidence storage per investigation.
- Added SHA-256, pHash and dHash calculation.
- Added temporary image analysis before saving.
- Added exact-file and perceptual image correlation against saved investigation images.
- Added Image Correlation UI with explicit Save/Delete controls.
- Added CLI image analysis and save confirmation.
- Added an offline-safe built-in pHash/dHash fallback while still using ImageHash when installed.

## What changed in 0.3.1

- New **Investigations home page** shown when the UI opens.
- Existing investigations are listed with evidence/artifact/journal counts.
- **Create Investigation** flow with name and description.
- Each investigation has its own workspace.
- Evidence saved from Analyze is attached to the selected investigation.
- Correlation searches can be scoped to the current investigation.
- Added journal entries with three types:
  - **Note** — working notes and research process.
  - **Report** — structured findings.
  - **Remark** — short observations.
- Journal entries support **create, edit, and delete**.
- Investigations support **create, edit, and delete**.
- Investigation overview shows recent evidence and workspace statistics.
- Existing 30-day temporary/local retention behavior remains for evidence history.
- Existing OSPERION 0.2.0 databases are migrated automatically when opened.

## Important data behavior

OSPERION has two different concepts:

1. **Analysis**: temporary. It is analyzed and compared against existing saved evidence but is not stored as evidence unless the user chooses Save.
2. **Saved evidence**: persisted in the local SQLite database and attached to an investigation when one is selected.

Journal entries are part of an investigation and are not automatically deleted by evidence retention.

The original Inspect code is not stored in SQLite by default. The database stores the evidence metadata and extracted artifacts. This keeps the database small and avoids silently retaining raw submitted source.

## UI workflow

```text
OSPERION
   |
   v
Investigations
   |
   +-- Existing investigations
   |
   +-- Create investigation
            |
            v
     Investigation workspace
            |
     +------+---------+----------------+
     |                |                |
   Overview       Evidence         Journal
                    |                |
                 Analyze         Note / Report
                    |             / Remark
                    |                |
                 Correlate       Create/Edit/Delete
                    |
               Save (optional)
```

When evidence is analyzed inside an investigation, OSPERION searches previously **saved evidence in that same investigation**. A match means that an artifact was previously observed; it is not proof that two accounts belong to the same person.

## CLI

Create an investigation:

```bash
python -m osperion investigation create "Investigation 1" --description "Research project"
```

List investigations:

```bash
python -m osperion investigation list
```

Analyze and ask whether to save:

```bash
python -m osperion analyze inspect.html --investigation 1
```

Non-interactive save:

```bash
python -m osperion analyze inspect.html --investigation 1 --save
```

Analyze without saving:

```bash
python -m osperion analyze inspect.html --investigation 1 --no-save
```

Search saved artifacts:

```bash
python -m osperion search 6439661898
```

View investigation evidence:

```bash
python -m osperion history --investigation 1
```

View statistics:

```bash
python -m osperion stats --investigation 1
```

## Web UI

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python -m osperion web
```

Open:

```text
http://127.0.0.1:8000
```

The server binds to localhost by default. To intentionally expose it on another interface, use the CLI `--host` option and understand the security implications.

## Local database

OSPERION uses SQLite. No PostgreSQL/MySQL server is required.

Default database:

```text
~/.osperion/osperion.sqlite3
```

Override the data directory:

```bash
OSPERION_DATA_DIR=/path/to/data
```

On Windows PowerShell:

```powershell
$env:OSPERION_DATA_DIR="C:\OSPERIONData"
```

## Data model

```text
investigations
    |
    +-- evidence
    |      |
    |      +-- artifacts
    |
    +-- investigation_entries
           |
           +-- note
           +-- report
           +-- remark
```

Every extracted artifact retains provenance fields such as:

- source filename
- source location
- extraction method
- context
- platform
- confidence
- raw value
- normalized value

## Accuracy model

OSPERION intentionally does **not** conclude that two accounts belong to the same person.

Examples:

- Stable structured platform identifier → strong/exact artifact match.
- Exact file SHA-256 → exact file match.
- Normalized URL → URL artifact match.
- CDN filename → candidate correlation.
- Username → weak/historical correlation.
- Perceptual image similarity → similarity signal, not identity proof.
- Generic numeric ID → candidate only until context establishes its meaning.

The UI therefore uses terms such as **previously observed**, **correlation**, and **candidate** rather than identity conclusions.

## Supported input

OSPERION is designed for evidence the user already has legitimately, such as:

- copied browser Inspect/Elements HTML
- saved page source
- copied JSON
- exported text
- locally saved HTML/JSON files

It does not automate login, bypass access controls, access private profiles, evade rate limits, or retrieve leaked/private information.

## Project structure

```text
osperion/
├── app/
│   ├── api.py
│   ├── config.py
│   ├── db.py
│   ├── extract.py
│   ├── models.py
│   └── service.py
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/
│   └── test_extract.py
├── data/
├── osperion.py
├── requirements.txt
├── pyproject.toml
└── LICENSE
```

## Development checks

The included extraction tests cover structured identifiers and URL normalization. The investigation CRUD and API workflow are also exercised during release testing.

## Profile image correlation (0.4.0)

OSPERION can now keep **locally saved profile/media images** as investigation assets and compare a newly supplied image against those assets.

For each image it calculates:

- SHA-256 — exact file identity (same bytes)
- pHash — perceptual visual fingerprint
- dHash — an additional visual fingerprint
- dimensions and file size

The UI provides **Image Correlation** inside each investigation. Image analysis is temporary until the user clicks **Save image to this investigation**. Saved images and hashes remain under the local OSPERION data directory (`~/.osperion/images` by default) and are indexed in SQLite.

CLI examples:

```bash
python -m osperion image analyze profile.jpg --investigation 1
python -m osperion image analyze profile.jpg --investigation 1 --save
python -m osperion image analyze profile.jpg --investigation 1 --no-save
python -m osperion image list --investigation 1
```

### How image matches are reported

- `exact_file`: SHA-256 is identical; the files are byte-for-byte the same.
- `exact`: pHash distance is zero, but the files may still have different bytes (for example, a re-encoded copy).
- `very_close`: small pHash Hamming distance.
- `similar`: moderate pHash Hamming distance.

A perceptual match is **only a visual correlation signal**. It is not an assertion that two accounts belong to the same person, and pHash can miss heavily cropped/edited images or produce false positives. OSPERION therefore preserves the hash, distance, source image, investigation and timestamp rather than turning a visual match into an identity claim.

The application uses the `ImageHash` package when it is installed. A small built-in pHash/dHash implementation is also included so local operation does not fail solely because the optional package cannot be installed in an offline environment.
