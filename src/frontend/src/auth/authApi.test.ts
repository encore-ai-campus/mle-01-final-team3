import { describe, expect, it, vi } from "vitest";
import { RestClient } from "../api/restClient";
import { RestAuthApi, mapBackendUser, type BackendUser } from "./authApi";

describe("backend auth contract", () => {
  it("maps backend roles and mustChangePassword to the app account model", () => {
    const account = mapBackendUser({
      userId: "usr_001",
      name: "홍기표",
      email: "marketing@adguard.local",
      role: "MARKETING",
      mustChangePassword: true,
    });

    expect(account).toEqual({
      userId: "usr_001",
      name: "홍기표",
      email: "marketing@adguard.local",
      department: "marketing",
      role: "reviewer",
      needsPasswordChange: true,
    });
  });

  it("sends the documented login body and credentials", async () => {
    const fetchImpl = vi.fn<typeof fetch>(async (_input, init) => {
      expect(init?.credentials).toBe("include");
      expect(init?.method).toBe("POST");
      expect(init?.body).toBe(JSON.stringify({
        email: "admin@adguard.local",
        password: "adguard1234",
        loginType: "ADMIN",
      }));
      return new Response(JSON.stringify({
        user: {
          userId: "usr_admin",
          name: "관리자",
          email: "admin@adguard.local",
          role: "ADMIN",
        },
        mustChangePassword: false,
      }), { status: 200, headers: { "Content-Type": "application/json" } });
    });
    const api = new RestAuthApi(new RestClient({ baseUrl: "http://localhost:8000/api/v1", fetchImpl }));

    await expect(api.login({ email: "admin@adguard.local", password: "adguard1234", loginType: "ADMIN" })).resolves.toMatchObject({
      userId: "usr_admin",
      role: "admin",
      department: "unknown",
    });
    expect(fetchImpl).toHaveBeenCalledWith("http://localhost:8000/api/v1/auth/login", expect.anything());
  });

  it("loads /me and handles logout's 204 response", async () => {
    const responses = [
      new Response(JSON.stringify({
        userId: "usr_legal",
        name: "법무 담당자",
        email: "legal@adguard.local",
        role: "LEGAL",
        mustChangePassword: false,
      }), { status: 200, headers: { "Content-Type": "application/json" } }),
      new Response(null, { status: 204 }),
    ];
    const fetchImpl = vi.fn<typeof fetch>(async () => responses.shift() as Response);
    const api = new RestAuthApi(new RestClient({ baseUrl: "http://localhost:8000/api/v1", fetchImpl }));

    await expect(api.me()).resolves.toMatchObject({ department: "legal", role: "reviewer" });
    await expect(api.logout()).resolves.toBeUndefined();
    expect(fetchImpl).toHaveBeenNthCalledWith(1, "http://localhost:8000/api/v1/me", expect.objectContaining({ credentials: "include" }));
    expect(fetchImpl).toHaveBeenNthCalledWith(2, "http://localhost:8000/api/v1/auth/logout", expect.objectContaining({ method: "POST" }));
  });

  it("changes the password through the documented PATCH endpoint", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({
        userId: "usr_legal",
        name: "법무 담당자",
        email: "legal@adguard.local",
        role: "LEGAL",
        mustChangePassword: false,
      }), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    const api = new RestAuthApi(new RestClient({ baseUrl: "http://localhost:8000/api/v1", fetchImpl }));

    await expect(api.changePassword({ currentPassword: "old-password", newPassword: "new-password" })).resolves.toMatchObject({ department: "legal", needsPasswordChange: false });
    expect(fetchImpl).toHaveBeenCalledWith("http://localhost:8000/api/v1/me/password", expect.objectContaining({
      method: "PATCH",
      body: JSON.stringify({ currentPassword: "old-password", newPassword: "new-password" }),
    }));
  });

  it("rejects an unknown backend role instead of granting access", () => {
    const payload: BackendUser = {
      userId: "usr_unknown",
      name: "알 수 없음",
      email: "unknown@adguard.local",
      role: "UNKNOWN" as BackendUser["role"],
      mustChangePassword: false,
    };

    expect(() => mapBackendUser(payload)).toThrow();
  });
});
