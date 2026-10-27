import csv
import os
from pathlib import Path
from job_finder import fetch_jobs, score_job, FIELDS

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "data" / "jobs.csv"
TEMP_FILE = CSV_FILE.with_suffix(".tmp")


def main():
    print("Pobieram aktualne oferty Solid.jobs...")
    jobs = fetch_jobs()
    jobs_by_url = {
        job.get("url", "").strip(): job
        for job in jobs
        if job.get("url")
    }

    with CSV_FILE.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    updated = 0
    unchanged = 0
    not_found = 0

    for row in rows:
        if row.get("portal") != "Solid.jobs":
            unchanged += 1
            continue

        job = jobs_by_url.get(row.get("url", "").strip())

        if not job:
            not_found += 1
            continue

        score, reason = score_job(job)
        row["match_score"] = str(score)
        row["notes"] = reason
        updated += 1

    with TEMP_FILE.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    os.replace(TEMP_FILE, CSV_FILE)

    print(f"Zaktualizowano ofert Solid.jobs: {updated}")
    print(f"Nie znaleziono w API: {not_found}")
    print(f"Pozostawiono bez zmian (inne portale): {unchanged}")
    print("Statusy i identyfikatory zostały zachowane.")


if __name__ == "__main__":
    main()
