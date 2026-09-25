import { api } from "./client";
import type { Passport } from "../types/passport";

export const passportApi = {
  /** One-shot read model: signals + saved insight + evidence. Never triggers AI generation. */
  async mine(): Promise<Passport> {
    const { data } = await api.get<Passport>("/passport/");
    return data;
  },
};
