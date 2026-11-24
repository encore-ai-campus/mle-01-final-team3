import { FixtureCheckProvider } from "./checkFixtureProvider";
import type { CheckDataProvider } from "../types/api";
import type {
  CheckDraftResult,
  CheckInput,
  CheckProgress,
  CheckResult,
  CheckStartResult,
  DataState,
} from "../types/domain";
import type { ArtifactScenarioId } from "../fixtures/artifactScenarios";

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

  private notConfigured<T>(operation: string): DataState<T> {
    return { status: "not-configured", message: `${operation}: ${notConfiguredMessage}` };
  }
}

export function createCheckProvider(scenarioId: ArtifactScenarioId = "LG-1"): CheckDataProvider {
  void scenarioId;
  return import.meta.env.VITE_USE_FIXTURES === "true" ? new FixtureCheckProvider() : new ApiCheckProvider();
}

export { FixtureCheckProvider } from "./checkFixtureProvider";
