import re
import csv
import requests
from pathlib import Path
from datetime import date
from html import unescape
from re import sub

API_URL = "https://solid.jobs/public-api/offers/IT"
CAMPAIGN = "job-assistant-test"

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "data" / "jobs.csv"

FIELDS = [
    "id", "date_found", "portal", "company", "job_title",
    "location", "url", "match_score", "status", "notes"
]


CYBER_KEYWORDS = [
    "cybersecurity", "cyber security", "security analyst",
    "soc analyst", "soc", "siem", "incident response",
    "information security", "it security", "security tester",
    "vulnerability", "penetration tester", "security operations",
]

JUNIOR_WORDS = [
    "junior", "entry level", "entry-level", "trainee",
    "graduate", "intern", "internship", "młodszy", "mlodszy",
    "początkujący", "poczatkujacy",
]

EXCLUDED_LEVELS = {"senior", "lead", "principal", "executive"}

EXCLUDED_KEYWORDS = [
    "ui / ux", "ux designer", "game designer",
    "sales manager", "account manager",
]


def clean_html(value):
    """Usuwa znaczniki HTML z opisu stanowiska."""
    value = sub(r"<[^>]+>", " ", value or "")
    return " ".join(unescape(value).split())


def load_existing_urls():
    """Wczytuje linki ofert, aby uniknąć duplikatów."""
    if not CSV_FILE.exists():
        return set()

    with CSV_FILE.open("r", encoding="utf-8", newline="") as file:
        return {
            row.get("url", "").strip()
            for row in csv.DictReader(file)
            if row.get("url")
        }


def score_job(job):
    """Ocenia dopasowanie oferty do cyberbezpieczeństwa i IT Support."""
    title = (job.get("title") or "").lower()
    description = clean_html(job.get("description") or "").lower()

    skills_data = job.get("skills") or []
    skills = " ".join(
        skill.get("name", "") if isinstance(skill, dict) else str(skill)
        for skill in skills_data
    ).lower()


    # Języki, które akceptujemy w ofertach pracy
    accepted_languages = [
        "polish", "polski",
        "english", "angielski",
    ]

    # Inne języki wymagające dodatkowej weryfikacji
    additional_languages = {
        "german": "niemiecki",
        "deutsch": "niemiecki",
        "dutch": "niderlandzki",
        "french": "francuski",
        "spanish": "hiszpański",
        "italian": "włoski",
    }

    level = (job.get("experienceLevel") or "").strip().lower()
    text = f"{title} {description} {skills}"
    # Wykrywanie wymaganej liczby lat doświadczenia
    experience_match = re.search(
        r"\b(?:minimum|min\.?|at least)\s+(\d+)\s+(?:years?|lat|lata)\b",
        description
    )
    # Wykrywanie języka niemieckiego jako obowiązkowego wymagania
    german_required_patterns = [
        r"\bgerman\s+(?:language\s+)?(?:is\s+)?required\b",
        r"\bgerman\s+(?:language\s+)?(?:is\s+)?mandatory\b",
        r"\bfluent\s+german\s+(?:is\s+)?required\b",
        r"\bwymagany\s+j[eę]zyk\s+niemiecki\b",
	r"\bbiegła\s+znajomość\s+języka\s+niemieckiego\b",
        r"\bgerman\s+(?:language\s+)?(?:at\s+least\s+)?(?:a[12]|b[12]|c[12])\s+(?:is\s+)?required\b",
    ]

    if any(re.search(pattern, description) for pattern in german_required_patterns):
        return 0, "Wymagany język niemiecki"
    # Wykrywanie innych obowiązkowych języków w opisach ofert
    other_required_languages = {
        "francuski": "french",
        "hiszpański": "spanish",
        "włoski": "italian",
        "niderlandzki": "dutch",
    }
    polish_language_forms = {
        "francuski": "francuskiego",
        "hiszpański": "hiszpańskiego",
        "włoski": "włoskiego",
	"niderlandzki": "niderlandzkiego",
    }
    for language_name, language_form in polish_language_forms.items():
        pattern = rf"\bwymagana\s+znajomość\s+języka\s+{language_form}\b"
        if re.search(pattern, description):
            return 0, f"Wymagany język: {language_name}"

        pattern = rf"\bbiegła\s+znajomość\s+języka\s+{language_form}\b"
        if re.search(pattern, description):
            return 0, f"Wymagany język: {language_name}"
    for language_name, language in other_required_languages.items():
        patterns = [
            rf"\b{language}\s+(?:language\s+)?(?:is\s+)?required\b",
            rf"\b{language}\s+(?:language\s+)?(?:is\s+)?mandatory\b",
            rf"\bfluent\s+{language}\s+(?:is\s+)?required\b",
            rf"\b{language}\s+(?:language\s+)?(?:at\s+least\s+)?(?:a[12]|b[12]|c[12])\s+(?:is\s+)?required\b",  
            rf"\bminimum\s+(?:a[12]|b[12]|c[12])\s+in\s+{language}\b",
        ]

        if any(re.search(pattern, description) for pattern in patterns):
            return 0, f"Wymagany język: {language_name}"    

    excluded_titles = [
        "php developer", "python developer", "react developer",
        "frontend developer", "front-end developer",
        "backend developer", "back-end developer",
        "software developer", "game designer", "ux designer",
        "ui / ux", "project manager", "sales manager",
        "account manager", "business analyst",
        "customer support", "customer service",
        "it support manager",
    ]

    if any(word in title for word in excluded_titles):
        return 0, "Stanowisko poza zakresem"

    advanced_title_keywords = [
        "senior", "sr.", "lead", "principal",
        "staff engineer", "head of", "director",
    ]

    if any(word in title for word in advanced_title_keywords):
        return 0, "Stanowisko zbyt zaawansowane"

    if any(word in level for word in [
        "senior", "lead", "principal", "executive"
    ]):
        return 0, "Poziom zbyt zaawansowany"

    cyber_keywords = [
        "cybersecurity", "cyber security", "cyberbezpieczeństwo",
        "cyberbezpieczeństwa",
        "soc analyst", "security analyst", "security engineer", "analityk soc",
        "information security", "it security", "security tester",
        "penetration test", "vulnerability", "incident response",
        "threat detection", "security operations",
        "analityk bezpieczeństwa", "analityk bezpieczenstwa",
        "security operations center",
    ]

    support_keywords = [
        "helpdesk", "help desk", "service desk", "it support",
        "technical support",
        "specjalista ds. wsparcia it",
        "1st line support", "first line support",
        "2nd line support", "second line support",
        "desktop support",
        "system administrator", "systems administrator",
        "server administrator", "network administrator",
        "network support", "linux administrator",
        "administrator systemów", "administrator systemow",
        "administrator sieci", "wsparcie techniczne it",
    ]    

    junior_keywords = [
        "junior", "entry level", "entry-level", "trainee",
        "graduate", "intern", "internship", "młodszy",
        "mlodszy", "stażysta", "staż",
    ]
    # Wykrywanie dodatkowych języków w tytule stanowiska
    language_patterns = {
        "niemiecki": [
            r"\bgerman\b",
            r"\bdeutsch\b",
            r"\bniemieck\w*\b",
        ],
        "niderlandzki": [
            r"\bdutch\b",
            r"\bniderlandzk\w*\b",
            r"\bholendersk\w*\b",
        ],
        "francuski": [
            r"\bfrench\b",
            r"\bfrancusk\w*\b",
        ],
        "hiszpański": [
            r"\bspanish\b",
            r"\bhiszpańsk\w*\b",
        ],
        "włoski": [
            r"\bitalian\b",
            r"\bwłosk\w*\b",
        ],
    }

    for language_name, patterns in language_patterns.items():
        if any(re.search(pattern, title) for pattern in patterns):
            return 0, f"Dodatkowy język w tytule: {language_name}"
    cyber_title = any(word in title for word in cyber_keywords)
    support_title = any(word in title for word in support_keywords)
    junior_title = any(word in title for word in junior_keywords)

    # Opis pomaga tylko wtedy, gdy stanowisko jest już technicznie dopasowane.
    if not cyber_title and not support_title:
        return 0, "Brak dopasowania w tytule stanowiska"

    score = 0
    reasons = []

    if cyber_title:
        score += 8
        reasons.append("Cyberbezpieczeństwo w tytule")

    if support_title:
        score += 6
        reasons.append("IT Support / administracja w tytule")

    technical_keywords = [
        "linux", "siem", "splunk", "sentinel", "wireshark",
        "log analysis", "analiza logów", "analiza logow",
        "incident handling", "troubleshooting",
        "python", "bash", "sql", "git",
        "windows", "networking", "tcp/ip", "dns",
    ]    

    technical_hits = [
        word for word in technical_keywords
        if re.search(r"\b" + re.escape(word) + r"\b", text)
    ]

    if technical_hits:
        score += min(len(technical_hits), 4)
        reasons.append("Technologie: " + ", ".join(technical_hits))

    if junior_title:
        score += 4
        reasons.append("Junior / entry-level")

    if level in ["junior", "intern", "internship"]:
        score += 3
        reasons.append("Poziom juniorski / stażowy")
    elif level == "regular":
        score += 1
        reasons.append("Poziom regular — sprawdź wymagania")

    if not junior_title and level not in ["junior", "intern", "internship"]:
        reasons.append("Sprawdź wymagane doświadczenie")
    if experience_match:
        required_years = int(experience_match.group(1))
        if required_years >= 3:
            reasons.append(f"UWAGA: wymagane minimum {required_years} lat doświadczenia")
    return score, ", ".join(reasons)

def format_salary(job):
    """Formatuje zakres wynagrodzenia i rodzaj umowy."""
    salary = job.get("salary") or {}

    if not salary:
        return "Nie podano"

    start = salary.get("from")
    end = salary.get("to")
    currency = salary.get("currency") or ""
    period = salary.get("period") or ""
    contract = salary.get("employmentType") or ""

    if start is None and end is None:
        amount = "Nie podano kwoty"
    elif start is None:
        amount = f"do {end:,.0f}".replace(",", " ")
    elif end is None:
        amount = f"od {start:,.0f}".replace(",", " ")
    elif start == end:
        amount = f"{start:,.0f}".replace(",", " ")
    else:
        amount = f"{start:,.0f}–{end:,.0f}".replace(",", " ")

    period_labels = {
        "Month": "mies.",
        "Year": "rok",
        "Hour": "godz.",
        "Day": "dzień",
        "Week": "tydz.",
    }
    period_label = period_labels.get(period, period)
    details = " ".join(part for part in [currency, period_label] if part)
    result = f"{amount} {details}".strip()

    if contract:
        result += f" | Umowa: {contract}"

    return result


def format_work_mode(job):
    """Określa tryb pracy na podstawie pól API."""
    remote = bool(job.get("isRemote"))
    hybrid = bool(job.get("isHybrid"))

    if remote and hybrid:
        return "Zdalna / hybrydowa"
    if remote:
        return "Zdalna"
    if hybrid:
        return "Hybrydowa"
    return "Stacjonarna lub nieokreślona"

def fetch_jobs():
    """Pobiera oferty ze wszystkich stron API."""
    session = requests.Session()
    params = {"campaign": CAMPAIGN, "pageSize": 100}

    response = session.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    jobs = list(data.get("jobs", []))
    total_pages = data.get("totalPages", 1)

    for page in range(1, total_pages):
        params["pageIndex"] = page
        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        jobs.extend(response.json().get("jobs", []))

    return jobs

def categorize_job(job):
    """Przypisuje ofertę do kategorii zawodowej."""
    title = (job.get("title") or "").lower()

    if any(word in title for word in [
        "security", "cyber", "soc analyst", "penetration test",
        "security tester", "incident response",
    ]):
        return "Cyberbezpieczeństwo"

    if any(word in title for word in [
        "helpdesk", "help desk", "service desk", "it support",
        "technical support", "desktop support", "support engineer",
        "1st line support", "first line support",
        "2nd line support", "second line support",
    ]):
        return "IT Support"
    if any(word in title for word in [
        "administrator", "system administrator", "network support",
        "network administrator",
    ]):
        return "Administracja systemami i sieciami"

    return "Inne IT"

def main():
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing_urls = load_existing_urls()

    print("Pobieram oferty z Solid.jobs...")

    try:
        jobs = fetch_jobs()
    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"Nie udało się pobrać ofert: {error}")
        return
    print(f"Pobrano ofert: {len(jobs)}")

    matches = []

    for job in jobs:
        title = job.get("title") or ""
        level = (job.get("experienceLevel") or "").lower()

        if level in EXCLUDED_LEVELS:
            continue

        valid_to = job.get("validTo")
        if valid_to and valid_to[:10] < date.today().isoformat():
            continue

        score, reason = score_job(job)

        if score >= 4 and job.get("url"):
            matches.append((score, reason, job))

    matches.sort(key=lambda item: item[0], reverse=True)

    new_rows = []

    for score, reason, job in matches:
        url = job.get("url", "").strip()

        if not url or url in existing_urls:
            continue

        locations = job.get("locations") or []
        location = ", ".join(locations) if locations else "Nie podano"

        new_rows.append({
            "id": "",
            "date_found": date.today().isoformat(),
            "portal": "Solid.jobs",
            "company": job.get("company") or "Nie podano",
            "job_title": job.get("title") or "Nie podano",
            "location": location,
            "url": url,
            "match_score": score,
            "status": "Do sprawdzenia",
            "notes": reason,
        })

        existing_urls.add(url)

    file_exists = CSV_FILE.exists() and CSV_FILE.stat().st_size > 0

    with CSV_FILE.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if not file_exists:
            writer.writeheader()

        next_id = 1
        if file_exists:
            with CSV_FILE.open("r", encoding="utf-8", newline="") as existing_file:
                rows = list(csv.DictReader(existing_file))
                next_id = max(
                    (int(row["id"]) for row in rows if row.get("id", "").isdigit()),
                    default=0,
                ) + 1

        for row in new_rows:
            row["id"] = next_id
            next_id += 1
            writer.writerow(row)

    print(f"Oferty pasujące do filtrów: {len(matches)}")
    print(f"Zapisano nowych ofert: {len(new_rows)}")
    print(f"Plik wynikowy: {CSV_FILE}")
    print("\nNajlepiej dopasowane oferty:")

    for score, reason, job in matches[:15]:
        print(f"\n[{score} pkt] {job.get('title', 'Bez tytułu')}")
        print(f"Firma: {job.get('company') or 'Nie podano'}")
        print(f"Kategoria: {categorize_job(job)}")
        print(f"Poziom: {job.get('experienceLevel') or 'Nie podano'}")
        locations = job.get("locations") or []
        print(f"Lokalizacja: {', '.join(locations) if locations else 'Nie podano'}")
        print(f"Tryb pracy: {format_work_mode(job)}")
        print(f"Wynagrodzenie: {format_salary(job)}")
        print(f"Link: {job.get('url')}")
        print(f"Dopasowanie: {reason}")


if __name__ == "__main__":
    main()
