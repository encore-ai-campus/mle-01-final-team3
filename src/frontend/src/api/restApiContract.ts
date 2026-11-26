import type { ApiContract, ReviewQuery } from "../types/api";
import { mapReviewListResponse } from "./mappers";
import type { RestClient } from "./restClient";

export interface RestApiRoutes {
  listReviews: string;
}

export interface RestApiContractOptions {
  client: RestClient;
  routes: RestApiRoutes;
}

export function createRestApiContract(options: RestApiContractOptions): Pick<ApiContract, "listReviews"> | null {
  const listReviewsPath = options.routes.listReviews.trim();
  if (listReviewsPath.length === 0) return null;

  return {
    listReviews: async (query: ReviewQuery) => {
      const path = appendQuery(listReviewsPath, query);
      const response = await options.client.request<unknown>(path);
      return mapReviewListResponse(response.data).items;
    },
  };
}

function appendQuery(path: string, query: ReviewQuery): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (typeof value === "string" && value.trim().length > 0) params.set(key, value);
  }

  const queryString = params.toString();
  if (queryString.length === 0) return path;
  return `${path}${path.includes("?") ? "&" : "?"}${queryString}`;
}
