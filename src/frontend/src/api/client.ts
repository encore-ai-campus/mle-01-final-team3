import type { ApiContract, ReviewQuery } from "../types/api";
import type { DecisionInput, PasswordUpdateInput, ReviewReportStage, EmployeeInput, ReviewUpdateInput, ReviewWorkflowActionInput } from "../types/domain";

export class ContractApiClient {
  public constructor(private readonly contract: ApiContract) {}

  public getDashboard(): Promise<unknown> {
    return this.requireOperation(this.contract.getDashboard, "getDashboard")();
  }

  public listReviews(query: ReviewQuery): Promise<unknown> {
    return this.requireOperation(this.contract.listReviews, "listReviews")(query);
  }

  public getReviewDetail(reviewId: string): Promise<unknown> {
    return this.requireOperation(this.contract.getReviewDetail, "getReviewDetail")(reviewId);
  }

  public submitDecision(input: DecisionInput): Promise<unknown> {
    return this.requireOperation(this.contract.submitDecision, "submitDecision")(input);
  }

  public getAccount(): Promise<unknown> {
    return this.requireOperation(this.contract.getAccount, "getAccount")();
  }

  public updatePassword(input: PasswordUpdateInput): Promise<unknown> {
    return this.requireOperation(this.contract.updatePassword, "updatePassword")(input);
  }

  public listNotifications(): Promise<unknown> {
    return this.requireOperation(this.contract.listNotifications, "listNotifications")();
  }

  public markNotificationsRead(): Promise<unknown> {
    return this.requireOperation(
      this.contract.markNotificationsRead,
      "markNotificationsRead",
    )();
  }

  public listEmployees(search?: string): Promise<unknown> { return this.requireOperation(this.contract.listEmployees, "listEmployees")(search); }
  public getEmployee(employeeId: string): Promise<unknown> { return this.requireOperation(this.contract.getEmployee, "getEmployee")(employeeId); }
  public createEmployee(input: EmployeeInput): Promise<unknown> { return this.requireOperation(this.contract.createEmployee, "createEmployee")(input); }
  public updateEmployee(employeeId: string, input: EmployeeInput): Promise<unknown> { return this.requireOperation(this.contract.updateEmployee, "updateEmployee")(employeeId, input); }
  public deleteEmployee(employeeId: string): Promise<unknown> { return this.requireOperation(this.contract.deleteEmployee, "deleteEmployee")(employeeId); }
  public getReviewReport(reviewId: string, stage: ReviewReportStage): Promise<unknown> { return this.requireOperation(this.contract.getReviewReport, "getReviewReport")(reviewId, stage); }
  public updateReview(reviewId: string, input: ReviewUpdateInput): Promise<unknown> { return this.requireOperation(this.contract.updateReview, "updateReview")(reviewId, input); }
  public performReviewAction(input: ReviewWorkflowActionInput): Promise<unknown> { return this.requireOperation(this.contract.performReviewAction, "performReviewAction")(input); }

  private requireOperation<TArgs extends unknown[], TResult>(
    operation: ((...args: TArgs) => Promise<TResult>) | undefined,
    name: string,
  ): (...args: TArgs) => Promise<TResult> {
    if (!operation) {
      throw new Error(`검증된 API 작업이 없습니다: ${name}`);
    }

    return operation;
  }
}
