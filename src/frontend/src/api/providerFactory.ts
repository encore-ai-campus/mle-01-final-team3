import { ApiProvider } from "./apiProvider";
import { createRestClient } from "./apiConfig";
import { FixtureProvider } from "./fixtureProvider";
import { RestReviewFlowApi } from "./reviewFlowApi";
import { RestAuthApi } from "../auth/authApi";
import type { DataProvider } from "../types/api";
import type { ArtifactScenarioId } from "../fixtures/artifactScenarios";
import type { FixtureWorkflowStore } from "./fixtureWorkflowStore";

export function createDataProvider(scenarioId: ArtifactScenarioId = "LG-1", useFixtures = import.meta.env.VITE_USE_FIXTURES === "true", store?: FixtureWorkflowStore): DataProvider {
  if (useFixtures) return new FixtureProvider(scenarioId, undefined, store);

  const restClient = createRestClient();
  const authApi = restClient ? new RestAuthApi(restClient) : undefined;
  return new ApiProvider({
    restClient,
    authApi,
    reviewFlow: restClient ? new RestReviewFlowApi(restClient) : undefined,
  });
}
