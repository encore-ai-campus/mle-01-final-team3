import { ApiProvider } from "./apiProvider";
import { createRestClient } from "./apiConfig";
import { FixtureProvider } from "./fixtureProvider";
import type { DataProvider } from "../types/api";
import type { ArtifactScenarioId } from "../fixtures/artifactScenarios";
import type { FixtureWorkflowStore } from "./fixtureWorkflowStore";

export function createDataProvider(scenarioId: ArtifactScenarioId = "LG-1", useFixtures = import.meta.env.VITE_USE_FIXTURES === "true", store?: FixtureWorkflowStore): DataProvider {
  return useFixtures
    ? new FixtureProvider(scenarioId, undefined, store)
    : new ApiProvider({ restClient: createRestClient() });
}
