import type { ApiContract, ReviewQuery } from "../types/api";
import type { DecisionInput, PasswordUpdateInput } from "../types/domain";

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
