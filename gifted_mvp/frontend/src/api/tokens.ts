import type { AuthTokens } from "../types/auth";

const ACCESS_KEY = "gifted_access";
const REFRESH_KEY = "gifted_refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: AuthTokens) {
    localStorage.setItem(ACCESS_KEY, tokens.access);
    localStorage.setItem(REFRESH_KEY, tokens.refresh);
  },
  setAccess(access: string) {
    localStorage.setItem(ACCESS_KEY, access);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};
