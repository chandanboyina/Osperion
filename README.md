<p align="center">
  <img src="static/osperion-banner.svg" alt="OSPERION — Your Collection. Your Investigation. In Your Control.">
</p>



<p align="center">
  <strong>Your Collection. Your Investigation. In Your Control.</strong><br>
  <em>Collect • Correlate • Investigate</em><br>
  Local-first digital evidence correlation and investigation workspace
</p>


<p align="center">
  <img src="https://img.shields.io/badge/status-active%20development-blue" alt="Project status">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/storage-SQLite-lightgrey" alt="SQLite">
  <img src="https://img.shields.io/badge/license-open%20source-green" alt="Open source">
</p>

OSPERION is a **local-first digital evidence correlation and investigation workspace** for organizing, analyzing, and correlating publicly available or legitimately obtained browser evidence.

It is designed for OSINT practitioners, cybersecurity researchers, investigators, analysts, students, and developers who need a structured workspace for working with digital evidence while keeping the interpretation evidence-based.

> **Correlation is not identity.** OSPERION records observable artifacts and relationships; it does not automatically conclude that correlated artifacts belong to the same real-world person.

---

## ⚠️ Live Demo — Sample Only

The publicly deployed OSPERION web version is a **sample/demo environment** intended to showcase the interface and workflow.

### Do not use the live demo for real investigations.

**Never upload real, sensitive, confidential, private, or personally identifiable investigation data to the public demo.**

Do not submit:

- Real investigation evidence
- Confidential research material
- Private information
- Personally identifiable information (PII)
- Sensitive screenshots, HTML, JSON, or images
- Information you are not authorized to share

The public deployment should **not** be treated as a private or hardened investigation server.

### Recommended use

For actual investigations, **clone OSPERION and run it locally** on your own computer.

> **Your evidence should stay under your control.**

---

## ✨ Features

- 🔎 **Evidence analysis** — analyze Inspect/DOM/View Source/JSON evidence
- 🧩 **Artifact extraction** — identifiers, usernames, URLs, media IDs, URNs, timestamps and other observable artifacts
- 🔗 **Evidence correlation** — compare new evidence with previously saved observations
- 🗂️ **Investigation workspaces** — keep evidence and research organized by investigation
- 📝 **Research journal** — Notes, Reports and Remarks
- 🖼️ **Image correlation** — SHA-256, pHash and dHash
- 📄 **PDF investigation reports** — export a complete saved investigation
- 🔍 **Investigation search** — search previously saved artifacts
- 💾 **Local SQLite storage** — no central database required for local use
- 📴 **Local-first workflow** — designed to keep investigation data on your machine
- 🐳 **Docker support** — run OSPERION in a container
- 🧪 **Testable codebase** — extraction and application workflows can be tested locally

---

# 🧭 How OSPERION Works

The basic workflow is:

```text
Browser / Evidence Source
          │
          ▼
   Inspect / Source
          │
          ▼
      OSPERION
          │
          ├── Platform Detection
          ├── Evidence Parsing
          ├── Artifact Extraction
          ├── Normalization
          ├── Correlation
          ├── Image Analysis
          └── Investigation Workspace
                     │
                     ▼
                Local SQLite
```

OSPERION works with evidence that the user already possesses legitimately.

Typical inputs include:

- Browser Inspect / Elements HTML
- View Source
- JSON
- Saved HTML
- Exported text
- Locally saved images

---

# 🚀 Quick Start

## Requirements

- Python 3.11+
- Git
- pip

Check your installation:

```bash
python --version
git --version
```

## 1. Clone the repository

```bash
git clone https://github.com/chandanboyina/Osperion.git
cd Osperion
```

## 2. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Start OSPERION

```bash
python -m osperion web
```

Open:

```text
http://127.0.0.1:8000
```

---

# 🖥️ Web UI Guide

## 1. Create an Investigation

From the home screen select:

**Create investigation**

Provide:

- Investigation name
- Description

Example:

```text
Name:
Example Investigation

Description:
Research project for testing authorized/public evidence.
```

---

## 2. Analyze Evidence

Open:

**Evidence & Analyze**

You can:

- Paste Inspect/DOM/View Source/JSON
- Upload `.html`
- Upload `.htm`
- Upload `.txt`
- Upload `.json`
- Upload `.mhtml`

Choose a platform or use **Auto detect**.

Then select:

**Analyze evidence**

OSPERION extracts observable artifacts and displays their confidence, type, value and context.

### Analysis is temporary

Analyzed evidence is **not automatically saved**.

To retain it, select:

**Save to this investigation**

---

## 3. Review Correlations

OSPERION compares new evidence with previously **saved evidence in the current investigation**.

A match means that an artifact was previously observed.

It does **not** automatically mean:

- Same person
- Same account owner
- Same organization
- Same operator

The investigator must validate the surrounding context.

---

## 4. Image Correlation

Open:

**Image Correlation**

Supply a locally saved profile/media image.

OSPERION can calculate:

- SHA-256
- pHash
- dHash
- Image dimensions
- File size

You can compare the image with images already saved in the investigation.

### Match semantics

| Match | Meaning |
|---|---|
| `exact_file` | Same SHA-256 / identical file bytes |
| `exact` | pHash distance is zero |
| `very_close` | Small perceptual distance |
| `similar` | Moderate perceptual similarity |

> Perceptual similarity is a visual correlation signal, not identity proof.

Images can be cropped, edited, resized, recompressed, reused, or independently sourced.

---

## 5. Research Journal

Open:

**Notes & Reports**

Create:

- **Note** — working thoughts and research process
- **Report** — structured findings
- **Remark** — short observations

Entries can be:

- Created
- Edited
- Deleted

The journal travels with the investigation and provides context for later review.

---

## 6. Search Investigation Memory

Open:

**Search Memory**

Search saved artifacts such as:

- Profile IDs
- Usernames
- URLs
- CDN URLs
- Media IDs
- URNs
- Other extracted identifiers

Example:

```text
6439661898
```

Search is scoped to the saved investigation when used from an investigation workspace.

---

## 7. Download an Investigation Report

Inside an investigation select:

**↓ Download report**

OSPERION generates a PDF containing the saved investigation state, including:

- Investigation information
- Timestamps
- Statistics
- Evidence inventory
- Evidence filenames
- Platforms
- SHA-256 hashes
- Parser versions
- Extracted artifacts
- Confidence and provenance information
- Notes
- Reports
- Remarks
- Saved image metadata
- Image hashes
- Accuracy/interpretation guidance

The filename is:

```text
OSPERION_<investigation-name>_report.pdf
```

The report is a **point-in-time export**.

Temporary and unsaved analysis is not included.

---

# 💻 CLI Usage

OSPERION can also be used without the web UI.

## Create an investigation

```bash
python -m osperion investigation create "Investigation 1"
```

With a description:

```bash
python -m osperion investigation create "Investigation 1" --description "Research project"
```

## List investigations

```bash
python -m osperion investigation list
```

## Analyze evidence

```bash
python -m osperion analyze inspect.html --investigation 1
```

## Analyze and save

```bash
python -m osperion analyze inspect.html --investigation 1 --save
```

## Analyze without saving

```bash
python -m osperion analyze inspect.html --investigation 1 --no-save
```

## Search saved artifacts

```bash
python -m osperion search 6439661898
```

## View investigation history

```bash
python -m osperion history --investigation 1
```

## View statistics

```bash
python -m osperion stats --investigation 1
```

---

# 🖼️ CLI Image Analysis

Analyze an image:

```bash
python -m osperion image analyze profile.jpg --investigation 1
```

Analyze and save:

```bash
python -m osperion image analyze profile.jpg --investigation 1 --save
```

Analyze without saving:

```bash
python -m osperion image analyze profile.jpg --investigation 1 --no-save
```

List saved images:

```bash
python -m osperion image list --investigation 1
```

---

# 📄 Investigation Reports

Every investigation can be exported as a PDF.

The report contains:

- Investigation name and description
- Creation/update/report timestamps
- Evidence statistics
- Evidence inventory
- Evidence SHA-256 hashes
- Filenames
- Platforms
- Parser versions
- Extracted artifacts
- Confidence
- Provenance
- Research journal
- Saved image metadata
- SHA-256
- pHash
- Interpretation and accuracy notes

The report only contains information already saved in the investigation.

---

# 💾 Data Storage

OSPERION uses SQLite for local persistence.

Default database:

```text
~/.osperion/osperion.sqlite3
```

Saved image assets:

```text
~/.osperion/images/
```

You can override the data directory.

### Linux / macOS

```bash
export OSPERION_DATA_DIR=/path/to/data
```

### Windows PowerShell

```powershell
$env:OSPERION_DATA_DIR="C:\OSPERIONData"
```

No PostgreSQL or MySQL server is required for normal local operation.

---

# 🧠 Accuracy & Interpretation

OSPERION deliberately separates **observable evidence** from **identity conclusions**.

Examples:

| Evidence | Interpretation |
|---|---|
| Stable structured identifier | Strong/exact artifact correlation |
| Same SHA-256 | Identical file bytes |
| Normalized URL | URL artifact correlation |
| CDN filename | Candidate correlation |
| Username | Weak/historical correlation |
| pHash similarity | Visual similarity signal |
| Generic numeric ID | Requires contextual validation |

The application uses language such as:

- **Previously observed**
- **Exact match**
- **Correlation**
- **Candidate**
- **Similarity**

rather than making unsupported identity claims.

---

# 🔬 Evidence & Provenance

Each extracted artifact can retain information such as:

- Source filename
- Source location
- Extraction method
- Context
- Platform
- Confidence
- Raw value
- Normalized value
- Additional details

This allows an investigator to understand:

```text
What was found?
Where was it found?
How was it extracted?
What platform was associated with it?
How confident was the parser?
```

---

# 🔐 Privacy & Security

OSPERION is local-first, but local software still depends on the security of the computer running it.

For sensitive work:

- Keep your operating system updated
- Protect your user account
- Encrypt storage where appropriate
- Restrict permissions on the OSPERION data directory
- Back up important investigations securely
- Do not upload sensitive evidence to the public demo
- Do not expose the local server publicly unless you understand the security implications

The public demo should not be considered a secure private investigation environment.

---

# ⚖️ Responsible Use

OSPERION is intended for legitimate and authorized use cases including:

- OSINT research
- Cybersecurity research
- Digital evidence organization
- Security education
- Academic research
- Public-information analysis
- Authorized investigations
- Incident research
- Evidence correlation

Only process information that you are legally and legitimately authorized to access or analyze.

OSPERION does not grant permission to access restricted information.

---

# 🚫 What OSPERION Does Not Do

OSPERION does **not**:

- Automate login
- Bypass authentication
- Access private profiles
- Bypass access controls
- Evade rate limits
- Retrieve leaked/private information
- Break into accounts
- Exploit websites
- Circumvent security mechanisms
- Automatically determine real-world identity from correlations

The user supplies the evidence being analyzed.

---

# 🏗️ Project Structure

```text
Osperion/
├── app/
│   ├── api.py
│   ├── config.py
│   ├── db.py
│   ├── extract.py
│   ├── image_hash.py
│   ├── models.py
│   ├── report.py
│   └── service.py
│
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── tests/
│   └── test_extract.py
│
├── data/
├── osperion.py
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── render.yaml
├── README.md
└── LICENSE
```

---

# 🐳 Docker

Build the image:

```bash
docker build -t osperion .
```

Run:

```bash
docker run -p 8000:8000 osperion
```

Open:

```text
http://127.0.0.1:8000
```

For real investigations, ensure that persistent storage and filesystem permissions are configured appropriately.

---

# 🧪 Development

Clone the repository:

```bash
git clone https://github.com/chandanboyina/Osperion.git
cd Osperion
```

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python -m osperion web
```

Run tests:

```bash
pytest
```

---

# 🤝 Contributing

OSPERION is an open-source project and contributions are welcome.

Potential contribution areas include:

- Parser improvements
- New platform adapters
- Extraction rules
- Correlation logic
- Image analysis
- UI/UX improvements
- Documentation
- Tests
- Performance improvements
- Security improvements
- Bug fixes

## Typical contribution workflow

Fork the repository and clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/Osperion.git
cd Osperion
```

Create a feature branch:

```bash
git checkout -b feature/my-feature
```

Make your changes and run the tests:

```bash
pytest
```

Test the web application:

```bash
python -m osperion web
```

Commit:

```bash
git add .
git commit -m "Add my feature"
```

Push:

```bash
git push origin feature/my-feature
```

Then open a Pull Request.

---

# 🔌 Platform & Parser Development

OSPERION can be extended with platform-specific extraction logic.

Potential platforms include:

- Instagram
- Facebook
- LinkedIn
- X / Twitter
- Reddit
- TikTok
- YouTube
- GitHub
- Threads
- Pinterest
- Telegram
- Discord
- Twitch
- Medium

Platform-specific extraction should preserve evidence provenance and avoid turning uncertain values into definitive conclusions.

A useful artifact should retain:

```text
Platform
Artifact type
Value
Normalized value
Confidence
Context
Location
Extraction method
```

---

# 🗺️ Investigation Workflow

A typical workflow looks like:

```text
Create Investigation
        │
        ▼
Collect authorized/public evidence
        │
        ▼
Save Inspect / HTML / JSON locally
        │
        ▼
Analyze evidence
        │
        ▼
Review extracted artifacts
        │
        ▼
Save relevant evidence
        │
        ▼
Collect additional evidence
        │
        ▼
Analyze new evidence
        │
        ▼
Correlate with previous observations
        │
        ▼
Validate correlations
        │
        ▼
Add Notes / Reports / Remarks
        │
        ▼
Analyze image evidence when applicable
        │
        ▼
Export investigation PDF
```

---

# 📴 Local-First Design

The intended real-investigation workflow is:

```text
Your Computer
│
├── OSPERION
├── SQLite Database
├── Investigation Workspace
├── Evidence Metadata
└── Saved Image Assets
```

The public web deployment exists primarily to demonstrate the application.

For sensitive or confidential work:

> **Run OSPERION locally.**

---

# 📌 Version History

## 0.5.0

- Investigation workspaces
- Evidence organization
- Research journal
- Notes / Reports / Remarks
- Image correlation
- Investigation PDF reports
- Local-first SQLite workflow
- Web UI
- CLI workflows

## 0.4.0

- Local profile/media image evidence
- SHA-256
- pHash
- dHash
- Image correlation
- Temporary image analysis
- Image save/delete workflow
- CLI image analysis

## 0.3.1

- Investigation home page
- Investigation CRUD
- Investigation-specific evidence
- Investigation-specific correlations
- Research journal
- Evidence/artifact/image/entry counts
- Database migration support

---

# 📜 License

See the [LICENSE](LICENSE) file for the project's applicable open-source license.

---

# ⭐ OSPERION

**Collect • Correlate • Investigate**

A local-first workspace for structured digital evidence research.

**Use the public demo to explore.  
Run OSPERION locally for real investigations.**
