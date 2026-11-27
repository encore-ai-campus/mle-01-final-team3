import { describe, expect, it } from "vitest";
import { RestClient } from "./restClient";
import { createRestClient, getApiBaseUrl } from "./apiConfig";

describe("API configuration", () => {
  it("returns null when the public API URL is empty", () => {
    expect(getApiBaseUrl({ VITE_API_BASE_URL: "   " })).toBeNull();
  });

  it("trims whitespace and trailing slashes from the public API URL", () => {
    expect(getApiBaseUrl({ VITE_API_BASE_URL: " https://api.example.test/ " })).toBe(
      "https://api.example.test",
    );
  });

  it("creates a RestClient only when the public API URL is configured", () => {
    expect(createRestClient({ VITE_API_BASE_URL: "" })).toBeNull();
    expect(createRestClient({ VITE_API_BASE_URL: "https://api.example.test" })).toBeInstanceOf(
      RestClient,
    );
  });
});
