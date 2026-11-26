import { FixtureCheckProvider } from "./checkFixtureProvider";
import type { CheckDataProvider } from "../types/api";
import type {
  CheckDraftResult,
  CheckInput,
  CheckProgress,
  CheckResult,
  CheckStartResult,
  DataState,
  CheckRecommendationResult,
  MarketingWorkflowActionInput,
} from "../types/domain";
import type { ArtifactScenarioId } from "../fixtures/artifactScenarios";
import type { FixtureWorkflowStore } from "./fixtureWorkflowStore";

const notConfiguredMessage = "검증된 광고 검사 API 연결이 설정되지 않았습니다.";

export class ApiCheckProvider implements CheckDataProvider {
  public getResult(checkId: string): Promise<DataState<CheckResult>> {
    return Promise.resolve(this.notConfigured(`getResult(${checkId})`));
  }

  public saveDraft(input: CheckInput): Promise<DataState<CheckDraftResult>> {
    void input;
    return Promise.resolve(this.notConfigured("saveDraft"));
  }

  public startCheck(input: CheckInput): Promise<DataState<CheckStartResult>> {
    void input;
    return Promise.resolve(this.notConfigured("startCheck"));
  }

  public getProgress(checkId: string): Promise<DataState<CheckProgress>> {
    return Promise.resolve(this.notConfigured(`getProgress(${checkId})`));
  }

  public requestRecommendation(checkId: string): Promise<DataState<CheckRecommendationResult>> {
    return Promise.resolve(this.notConfigured(`requestRecommendation(${checkId})`));
  }

  public requestAdCheck(input: CheckInput): Promise<DataState<CheckStartResult>> {
    void input;
    return Promise.resolve(this.notConfigured("requestAdCheck"));
  }

  public performMarketingAction(input: MarketingWorkflowActionInput): Promise<DataState<CheckResult>> {
    void input;
    return Promise.resolve(this.notConfigured("performMarketingAction"));
  }

  private notConfigured<T>(operation: string): DataState<T> {
    return { status: "not-configured", message: `${operation}: ${notConfiguredMessage}` };
  }
}

export function createCheckProvider(scenarioId: ArtifactScenarioId = "LG-1", useFixtures = import.meta.env.VITE_USE_FIXTURES === "true", store?: FixtureWorkflowStore): CheckDataProvider {
  return useFixtures ? new FixtureCheckProvider(scenarioId, store) : new ApiCheckProvider();
}

export { FixtureCheckProvider } from "./checkFixtureProvider";
