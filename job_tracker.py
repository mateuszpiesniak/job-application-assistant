import csv
from pathlib import Path
from datetime import date

DATABASE = Path("data/jobs.csv")

FIELDS = [
    "id", "date_found", "portal", "company", "job_title",
    "location", "url", "match_score", "status", "notes"
]

STATUSES = [
    "Do sprawdzenia",
    "Do aplikowania",
    "Aplikowano",
    "Odpowiedź otrzymana",
    "Odrzucono",
]

def get_priority(score, title=""):
    """Określa priorytet na podstawie punktacji i tytułu stanowiska."""

    if score is None or str(score).strip() == "":
        return "DO OCENY"

    try:
        score = int(score)
    except (ValueError, TypeError):
        return "DO OCENY"

    title = title.lower()

    if score <= 0:
        return "NISKI"

    if any(word in title for word in [
        "senior", "lead", "principal", "director", "head of"
    ]):
        return "NISKI"

    junior = any(word in title for word in [
        "junior", "entry-level", "entry level",
        "trainee", "intern", "młodszy", "mlodszy",
    ])

    if junior and score >= 10:
        return "WYSOKI"
    elif score >= 12:
        return "WYSOKI"
    elif score >= 6:
        return "ŚREDNI"
    else:
        return "NISKI"

def load_jobs():
    with DATABASE.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def add_job():
    print("\n=== Dodawanie oferty ===")
    portal = input("Portal: ").strip()
    company = input("Firma: ").strip()
    job_title = input("Stanowisko: ").strip()
    location = input("Lokalizacja: ").strip()
    url = input("Link do oferty: ").strip()

    if not portal or not job_title or not url:
        print("Błąd: portal, stanowisko i link są wymagane.")
        return

    jobs = load_jobs()

    if any(job["url"].strip() == url for job in jobs):
        print("Ta oferta już znajduje się w bazie.")
        return

    ids = [int(job["id"]) for job in jobs if job["id"].isdigit()]
    new_id = str(max(ids, default=0) + 1)

    new_job = {
        "id": new_id,
        "date_found": date.today().isoformat(),
        "portal": portal,
        "company": company,
        "job_title": job_title,
        "location": location,
        "url": url,
        "match_score": "",
        "status": "Do sprawdzenia",
        "notes": "",
    }

    with DATABASE.open("a", newline="", encoding="utf-8") as file:
        csv.DictWriter(file, fieldnames=FIELDS).writerow(new_job)

    print(f"Dodano ofertę: {job_title} (ID: {new_id})")


def list_jobs():
    jobs = load_jobs()

    if not jobs:
        print("Brak ofert w bazie.")
        return

    jobs.sort(
        key=lambda job: (
            job.get("match_score", "").strip() == "",
            -int(job["match_score"])
            if job.get("match_score", "").strip().isdigit()
            else 0,
        )
    )

    print("\n=== Lista ofert (od najwyższej punktacji) ===")
    for job in jobs:
        score = job.get("match_score", "").strip() or "brak"
        reason = job.get("notes", "").strip() or "Brak uzasadnienia"

        print(
            f'ID: {job["id"]} | {job["job_title"]} | '
            f'{job["company"]} | {job["portal"]} | {job["status"]}'
        )
        print(f"  Punktacja: {score}")
        print(f"  Priorytet: {get_priority(job.get('match_score', ''), job.get('job_title', ''))}")
        print(f"  Dopasowanie: {reason}")

def update_status():
    jobs = load_jobs()

    if not jobs:
        print("Brak ofert w bazie.")
        return

    list_jobs()
    job_id = input("\nPodaj ID oferty: ").strip()
    selected = next((job for job in jobs if job["id"] == job_id), None)

    if selected is None:
        print("Nie znaleziono oferty o takim ID.")
        return

    print("\nDostępne statusy:")
    for number, status in enumerate(STATUSES, start=1):
        print(f"{number}. {status}")

    choice = input("Wybierz numer statusu: ").strip()

    if not choice.isdigit() or not 1 <= int(choice) <= len(STATUSES):
        print("Nieprawidłowy wybór.")
        return

    selected["status"] = STATUSES[int(choice) - 1]

    with DATABASE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(jobs)

    print("Status został zaktualizowany.")



def filter_jobs_by_status():
    jobs = load_jobs()

    print("\n=== Filtrowanie ofert według statusu ===")
    for number, status in enumerate(STATUSES, start=1):
        print(f"{number}. {status}")

    choice = input("Wybierz numer statusu: ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(STATUSES):
        print("Nieprawidłowy wybór.")
        return

    selected_status = STATUSES[int(choice) - 1]
    filtered = [job for job in jobs if job["status"] == selected_status]

    if not filtered:
        print(f"Brak ofert ze statusem: {selected_status}")
        return

    print(f"\nOferty ze statusem: {selected_status}")
    for job in filtered:
        print(
            f'ID: {job["id"]} | {job["job_title"]} | '
            f'{job["company"]} | {job["status"]}'
        )
        print(f'  {job["url"]}')


def filter_jobs_by_category():
    from job_finder import score_job, categorize_job

    jobs = load_jobs()

    categories = [
        "Cyberbezpieczeństwo",
        "IT Support",
        "Administracja systemami i sieciami",
    ]

    print("\n=== Filtrowanie według kategorii ===")
    for number, category in enumerate(categories, start=1):
        print(f"{number}. {category}")

    choice = input("Wybierz kategorię: ").strip()

    if not choice.isdigit() or not 1 <= int(choice) <= len(categories):
        print("Nieprawidłowy wybór.")
        return

    selected_category = categories[int(choice) - 1]
    filtered = []

    for job in jobs:
        title = job.get("job_title", "")
        score, reason = score_job({"title": title})

        if score == 0:
            continue

        category = categorize_job({"title": title})

        if category == selected_category:
            filtered.append((job, score, reason))

    filtered.sort(key=lambda item: item[1], reverse=True)

    print(f"\n=== {selected_category} ===")
    print(f"Liczba dopasowanych ofert: {len(filtered)}")

    for job, score, reason in filtered:
        print(f'\nID: {job["id"]} | {job["job_title"]}')
        print(f'  Firma: {job["company"]}')
        print(f'  Punktacja na podstawie tytułu: {score}')
        print(f'  Status: {job["status"]}')
        print(f'  Dopasowanie: {reason}')
        print(f'  Link: {job["url"]}')


def summarize_statuses():
    jobs = load_jobs()

    print("\n=== Podsumowanie ofert ===")
    for status in STATUSES:
        count = sum(1 for job in jobs if job["status"] == status)
        print(f"{status}: {count}")

    print(f"Łącznie ofert: {len(jobs)}")
def filter_jobs_by_priority():
    """Wyświetla oferty według wybranego priorytetu."""

    jobs = load_jobs()

    print("\n=== Filtrowanie według priorytetu ===")
    print("1. WYSOKI")
    print("2. ŚREDNI")
    print("3. NISKI")
    print("4. DO OCENY")

    priorities = ["WYSOKI", "ŚREDNI", "NISKI", "DO OCENY"]
    choice = input("Wybierz numer priorytetu: ").strip()

    if choice not in ["1", "2", "3", "4"]:
        print("Nieprawidłowy wybór.")
        return

    selected_priority = priorities[int(choice) - 1]

    filtered = [
        job for job in jobs
        if get_priority(
            job.get("match_score", ""),
            job.get("job_title", "")
        ) == selected_priority
    ]

    print(f"\nZnaleziono ofert: {len(filtered)}")

    for job in filtered:
        print(
            f'ID: {job["id"]} | {job["job_title"]} | '
            f'{job["company"]} | {job["status"]}'
        )
        print(f'  Link: {job["url"]}')

def main():
    while True:
        print("\n=== JOB APPLICATION ASSISTANT ===")
        print("1. Dodaj ofertę")
        print("2. Wyświetl oferty")
        print("3. Zmień status aplikacji")
        print("4. Filtruj oferty według statusu")
        print("5. Podsumowanie statusów")
        print("6. Filtruj oferty według kategorii")
        print("7. Filtruj oferty według priorytetu")
        print("8. Zakończ")
        choice = input("Wybierz opcję: ").strip()

        if choice == "1":
            add_job()
        elif choice == "2":
            list_jobs()
        elif choice == "3":
            update_status()
        elif choice == "4":
            filter_jobs_by_status()
        elif choice == "5":
            summarize_statuses()
        elif choice == "6":
            filter_jobs_by_category()
        elif choice == "7":
            filter_jobs_by_priority()
        elif choice == "8":
            print("Do zobaczenia!")
            break            
        else:
            print("Nieprawidłowy wybór.")

if __name__ == "__main__":
    main()
