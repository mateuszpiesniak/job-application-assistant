# Job Application Assistant

A Python-based project designed to support and organize the job application process, with a focus on entry-level IT and cybersecurity opportunities.

## Features

- **Job Search:** Collects job opportunities from Solid.jobs.
- **Job Filtering:** Filters job offers based on selected criteria, including location, language requirements and job categories.
- **Job Ranking:** Evaluates and prioritizes job opportunities.
- **Application Tracker:** Helps organize and track job applications.
- **Form Automation:** Uses Playwright to fill a local test recruitment form with candidate information.
- **Form Handlers:** Stores recruitment form selectors in a separate configuration module.
- **Privacy Protection:** Keeps personal information, CV files and local job databases outside the public repository.

## Technologies

- Python
- Playwright
- HTML
- CSV
- Git
- Linux (Ubuntu / WSL2)

## Project Structure

```text
job-application-assistant/
├── job_finder.py
├── job_tracker.py
├── refresh_jobs.py
├── auto_apply.py
├── form_handlers.py
├── erecruiter_dummy_test.py
├── erecruiter_test_form.html
├── test_form.html
├── README.md
└── .gitignore
```

Additional scripts are used for testing and development.

## Installation

Clone the repository:

```bash
git clone https://github.com/mateuszpiesniak/job-application-assistant.git
cd job-application-assistant
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Playwright and its Chromium browser:

```bash
pip install playwright
python -m playwright install chromium
```

## Usage

The main project components are:

```bash
python job_finder.py
python job_tracker.py
```

The form automation component uses a local HTML test form, a dummy candidate profile and a dummy CV file.

These test files must be prepared locally before running the automation demo.

## Safety and Privacy

The project is intended for learning, portfolio demonstration and responsible automation.

- Personal candidate information is stored locally.
- Real CV documents are excluded from version control.
- Local job databases are excluded from the repository.
- The demonstrated application form workflow runs in dry-run mode without submitting applications.
- Real recruitment websites should not be used for automated submissions without review and authorization.

## Current Status

**Portfolio prototype**

Job search, filtering, ranking, application tracking and local recruitment form automation have been developed and tested during the project.

Support for additional recruitment platforms is planned as a possible future improvement.

## Author

**Mateusz Pieśniak**

Cybersecurity Master's student interested in SOC analysis, IT security, Linux, Python and automation.

GitHub: https://github.com/mateuszpiesniak
