import { api } from "./client";
import type { LoginResponse, Role, User } from "../types/auth";

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
  role?: Exclude<Role, "ADMIN">;
}

export const authApi = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>("/auth/login/", { email, password });
    return data;
  },
  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await api.post<User>("/auth/register/", payload);
    return data;
  },
  async me(): Promise<User> {
    const { data } = await api.get<User>("/auth/me/");
    return data;
  },
};
