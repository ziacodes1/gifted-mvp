import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { InternalAxiosRequestConfig } from "axios";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const STORAGE_KEY = "gifted.lang";

/** Fresh i18n module per test, so initialization from localStorage is exercised like a page load. */
async function loadI18n() {
  vi.resetModules();
  return import("./index");
}

beforeEach(() => localStorage.clear());
afterEach(cleanup);

describe("i18n setup", () => {
  it("defaults to English when nothing is saved", async () => {
    const { default: i18n, currentLanguage } = await loadI18n();
    expect(currentLanguage()).toBe("en");
    expect(i18n.t("nav.home")).toBe("Home");
  });

  it("switches en → uz → ru and saves the choice", async () => {
    const { default: i18n, setLanguage } = await loadI18n();
    await setLanguage("uz");
    expect(i18n.t("nav.home")).toBe("Bosh sahifa");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("uz");
    await setLanguage("ru");
    expect(i18n.t("nav.home")).toBe("Главная");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("ru");
    expect(document.documentElement.lang).toBe("ru");
  });

  it("restores the saved language after a refresh", async () => {
    localStorage.setItem(STORAGE_KEY, "uz");
    const { currentLanguage, default: i18n } = await loadI18n();
    expect(currentLanguage()).toBe("uz");
    expect(i18n.t("assessment.next")).toBe("Keyingi savol");
  });

  it("ignores an unsupported saved value", async () => {
    localStorage.setItem(STORAGE_KEY, "fr");
    const { currentLanguage } = await loadI18n();
    expect(currentLanguage()).toBe("en");
  });

  it("uses Russian plural forms", async () => {
    const { default: i18n, setLanguage } = await loadI18n();
    await setLanguage("ru");
    expect(i18n.t("mission.steps.points", { count: 1 })).toBe("1 балл");
    expect(i18n.t("mission.steps.points", { count: 3 })).toBe("3 балла");
    expect(i18n.t("mission.steps.points", { count: 10 })).toBe("10 баллов");
  });
});

describe("API client", () => {
  it("sends the current language as Accept-Language on every request", async () => {
    const { setLanguage } = await loadI18n();
    const { api } = await import("../api/client");
    const seen: (string | undefined)[] = [];
    api.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
      seen.push(config.headers.get("Accept-Language")?.toString());
      return { data: {}, status: 200, statusText: "OK", headers: {}, config };
    };
    await api.get("/passport/");
    await setLanguage("uz");
    await api.post("/ai/profile-synthesis/", {});
    await setLanguage("ru");
    await api.get("/missions/");
    expect(seen).toEqual(["en", "uz", "ru"]);
  });
});

describe("translated pages", () => {
  it("landing page + language switcher render each language", async () => {
    const { default: i18n } = await loadI18n();
    const { I18nextProvider } = await import("react-i18next");
    const { LandingPage } = await import("../pages/public/LandingPage");
    const { LanguageSwitcher } = await import("../components/LanguageSwitcher");

    render(
      <I18nextProvider i18n={i18n}>
        <MemoryRouter>
          <LanguageSwitcher />
          <LandingPage />
        </MemoryRouter>
      </I18nextProvider>,
    );
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Discover what you could become.");
    expect(screen.getByRole("radio", { name: "English" }).getAttribute("aria-checked")).toBe("true");

    await act(async () => fireEvent.click(screen.getByRole("radio", { name: "O‘zbekcha" })));
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Kim bo‘lishingiz mumkinligini kashf eting.");
    expect(screen.getByText("Men ota-onaman")).toBeTruthy();

    await act(async () => fireEvent.click(screen.getByRole("radio", { name: "Русский" })));
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Узнай, кем ты можешь стать.");
    expect(screen.getByRole("radio", { name: "Русский" }).getAttribute("aria-checked")).toBe("true");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("ru");
  });

  it("login page is translated", async () => {
    localStorage.setItem(STORAGE_KEY, "uz");
    const { default: i18n } = await loadI18n();
    const { I18nextProvider } = await import("react-i18next");
    const { LoginPage } = await import("../pages/public/LoginPage");
    const { AuthProvider } = await import("../features/auth/AuthContext");
    const { QueryClient, QueryClientProvider } = await import("@tanstack/react-query");

    render(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={new QueryClient()}>
          <AuthProvider>
            <MemoryRouter>
              <LoginPage />
            </MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      </I18nextProvider>,
    );
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Qaytganingizdan xursandmiz");
    expect(screen.getByRole("tab", { name: "Ota-ona" })).toBeTruthy();
    expect(screen.getByLabelText("Parol")).toBeTruthy();
  });
});
