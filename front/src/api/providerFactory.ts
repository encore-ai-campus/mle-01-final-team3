import { ApiProvider } from "./apiProvider";
import { FixtureProvider } from "./fixtureProvider";
import type { DataProvider } from "../types/api";
import type { ArtifactScenarioId } from "../fixtures/artifactScenarios";

export function createDataProvider(scenarioId: ArtifactScenarioId = "LG-1"): DataProvider {
  return import.meta.env.VITE_USE_FIXTURES === "true" ? new FixtureProvider(scenarioId) : new ApiProvider();
}
