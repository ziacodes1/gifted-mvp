import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import ru from "./locales/ru.json";
import uz from "./locales/uz.json";

/** Supported UI languages. The same codes go to the backend as `Accept-Language`,
 * which localizes server-driven content (assessment, missions, labels) and AI output. */
export const LANGUAGES = [
  { code: "uz", short: "UZ", label: "O‘zbekcha" },
  { code: "en", short: "EN", label: "English" },
  { code: "ru", short: "RU", label: "Русский" },
] as const;

export type Language = (typeof LANGUAGES)[number]["code"];

export const DEFAULT_LANGUAGE: Language = "en";
export const STORAGE_KEY = "gifted.lang";

export function isLanguage(value: unknown): value is Language {
  return LANGUAGES.some((l) => l.code === value);
}

function savedLanguage(): Language {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return isLanguage(value) ? value : DEFAULT_LANGUAGE;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

/** The language currently shown (always one of the supported codes). */
export function currentLanguage(): Language {
  return isLanguage(i18n.resolvedLanguage) ? i18n.resolvedLanguage : DEFAULT_LANGUAGE;
}

export async function setLanguage(lang: Language): Promise<void> {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    /* private mode: the choice still applies for this visit */
  }
  await i18n.changeLanguage(lang);
}

i18n.on("languageChanged", (lng) => {
  if (typeof document !== "undefined") document.documentElement.lang = lng;
});

void i18n.use(initReactI18next).init({
  // Locale files are small, so they are bundled — no extra network requests.
  resources: { en: { translation: en }, uz: { translation: uz }, ru: { translation: ru } },
  lng: savedLanguage(),
  fallbackLng: DEFAULT_LANGUAGE,
  supportedLngs: LANGUAGES.map((l) => l.code),
  interpolation: { escapeValue: false }, // React already escapes
  returnNull: false,
});

export default i18n;
