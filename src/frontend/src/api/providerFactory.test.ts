import { describe, expect, it } from "vitest";
import { ApiCheckProvider, createCheckProvider, FixtureCheckProvider } from "./checkProvider";
import { ApiProvider } from "./apiProvider";
import { createDataProvider } from "./providerFactory";
import { FixtureProvider } from "./fixtureProvider";

describe("Provider factory", () => {
  it("selects the existing fixture providers when fixture mode is enabled", () => {
    expect(createDataProvider("LG-1", true)).toBeInstanceOf(FixtureProvider);
    expect(createCheckProvider("LG-1", true)).toBeInstanceOf(FixtureCheckProvider);
  });

  it("selects API providers without making a request during construction", async () => {
    const dataProvider = createDataProvider("LG-1", false);
    const checkProvider = createCheckProvider("LG-1", false);

    expect(dataProvider).toBeInstanceOf(ApiProvider);
    expect(checkProvider).toBeInstanceOf(ApiCheckProvider);
    await expect(dataProvider.getDashboard()).resolves.toMatchObject({ status: "not-configured" });
    await expect(checkProvider.getResult("check-1")).resolves.toMatchObject({ status: "not-configured" });
  });

  it("uses the shared auth contract for account pages", async () => {
    const account = {
      userId: "usr_001",
      name: "마케팅 담당자",
      email: "marketing@adguard.local",
      department: "marketing" as const,
      role: "reviewer" as const,
      needsPasswordChange: true,
    };
    const authApi = {
      login: async () => account,
      me: async () => account,
      changePassword: async () => ({ ...account, needsPasswordChange: false }),
      logout: async () => undefined,
    };
    const provider = new ApiProvider({ authApi });

    await expect(provider.getAccount()).resolves.toMatchObject({ status: "ready", data: account });
    await expect(provider.updatePassword({ currentPassword: "old", newPassword: "new", confirmation: "new" })).resolves.toMatchObject({
      status: "ready",
      data: { account: { needsPasswordChange: false } },
    });
  });
});
