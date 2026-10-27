import json
from pathlib import Path
from playwright.sync_api import sync_playwright

DRY_RUN = True

def main():
    """Uruchamia przeglądarkę z lokalnym formularzem testowym."""

    profile_path = Path("private/profile.json")

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
        page.goto(form_path.as_uri())

        print("Tytuł formularza:", page.title())
        
        page.locator("#first_name").fill(profile["first_name"])
        assert page.locator("#first_name").input_value() == profile["first_name"], "Nieprawidłowe imię"        
        
        page.locator("#last_name").fill(profile["last_name"])        
        assert page.locator("#last_name").input_value() == profile["last_name"], "Nieprawidłowe nazwisko"
        page.locator("#email").fill(profile["email"])
        assert page.locator("#email").input_value() == profile["email"], "Nieprawidłowy adres e-mail"

        page.locator("#phone").fill(profile["phone"])
        assert page.locator("#phone").input_value() == profile["phone"], "Nieprawidłowy numer telefonu"

        page.locator("#availability").fill(profile["availability"])
        assert page.locator("#availability").input_value() == profile["availability"], "Nieprawidłowa dyspozycyjność"
        
        page.locator('input[name="student_status"][value="' + profile["student_status"] + '"]').check()
        assert page.locator('input[name="student_status"]:checked').input_value() == profile["student_status"], "Nieprawidłowy status studenta"
        print("Status studenta: poprawnie zaznaczony")        
        
        cv_path = Path(profile["cv_path"]).resolve()        
        page.locator("#cv").set_input_files(str(cv_path))
        print("Dołączono CV:", cv_path.name)

        print("Dane kandydata zostały wpisane do formularza testowego")
        
        if DRY_RUN:
            print("DRY RUN: Wysyłanie formularza zablokowane")
            browser.close()
            return

        page.get_by_role("button", name="Wyślij aplikację (TEST)").click()
        print("Kliknięto przycisk wysyłania (TEST)")
        confirmation = page.locator("#confirmation").inner_text()

        if confirmation == "Aplikacja testowa wysłana poprawnie":
            print("SUKCES: Formularz testowy potwierdzony")
        else:
            print("BŁĄD: Brak potwierdzenia")
        
        browser.close()

if __name__ == "__main__":
    main()
