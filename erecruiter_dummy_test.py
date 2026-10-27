import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from form_handlers import FORM_HANDLERS

DRY_RUN = True
STUDENT_STATUS_MAP = {
    "Tak - studenta": "1",
    "Tak - ucznia": "2",
    "Nie": "3"
}

def main():
    """Uruchamia przeglądarkę z lokalnym formularzem testowym."""

    profile_path = Path("private/dummy_profile.json")

    with profile_path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    print("Profil kandydata został poprawnie wczytany")
    form_path = Path("test_form.html").resolve()

    if not form_path.exists():
        print("Brak formularza testowego: test_form.html")
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.route("**/*", lambda route: route.abort() if route.request.method in ("POST", "PUT", "PATCH", "DELETE") else route.continue_())
        page.goto(Path("erecruiter_test_form.html").resolve().as_uri())
        page.route("**/*", lambda route: route.abort())

        print("Tytuł formularza:", page.title())
        
        page.locator(FORM_HANDLERS["erecruiter"]["first_name"]).fill(profile["first_name"])
        assert page.locator(FORM_HANDLERS["erecruiter"]["first_name"]).input_value() == profile["first_name"], "Nieprawidłowe imię"        
        
        page.locator(FORM_HANDLERS["erecruiter"]["last_name"]).fill(profile["last_name"])        
        assert page.locator(FORM_HANDLERS["erecruiter"]["last_name"]).input_value() == profile["last_name"], "Nieprawidłowe nazwisko"
        page.locator(FORM_HANDLERS["erecruiter"]["email"]).fill(profile["email"])
        assert page.locator(FORM_HANDLERS["erecruiter"]["email"]).input_value() == profile["email"], "Nieprawidłowy adres e-mail"

        page.locator(FORM_HANDLERS["erecruiter"]["phone"]).fill(profile["phone"])
        assert page.locator(FORM_HANDLERS["erecruiter"]["phone"]).input_value() == profile["phone"], "Nieprawidłowy numer telefonu"

        status = STUDENT_STATUS_MAP[profile["student_status"]]
        radio = page.locator(FORM_HANDLERS["erecruiter"]["student_status"] + "[value=\"" + status + "\"]")
        radio.check()
        assert radio.is_checked() and radio.input_value() == status, "Nieprawidłowy status studenta"
        print("Status studenta: poprawnie zaznaczony")

        page.locator(FORM_HANDLERS["erecruiter"]["availability"]).fill(profile["availability"])
        assert page.locator(FORM_HANDLERS["erecruiter"]["availability"]).input_value() == profile["availability"], "Nieprawidłowa dyspozycyjność"
        
        
        cv_path = Path(profile["cv_path"]).resolve()        
        page.locator(FORM_HANDLERS["erecruiter"]["cv"]).set_input_files(str(cv_path))
        attached = page.locator(FORM_HANDLERS["erecruiter"]["cv"]).evaluate("(el) => el.files.length === 1 && el.files[0].name === 'dummy_cv.pdf'")
        assert attached, "Nieprawidłowy załącznik CV"      
        print("Dołączono CV:", cv_path.name)

        print("Dane kandydata zostały wpisane do formularza testowego")
        
        print("DRY RUN: Formularz przygotowany, bez wysyłania")
        browser.close()

if __name__ == "__main__":
    main()
