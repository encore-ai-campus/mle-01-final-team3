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
});
