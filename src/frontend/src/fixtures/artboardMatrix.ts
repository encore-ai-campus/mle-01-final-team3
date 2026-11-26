import { artifactScenarioIds, artifactScenarios, type ArtifactScenarioId } from "./artifactScenarios";

export interface ArtboardCase {
  id: ArtifactScenarioId;
  route: "/" | "/reviews" | "/reviews/:reviewId" | "/account" | "/notifications";
  scenario: ArtifactScenarioId;
  expectedState: string;
  expectedInteraction: string;
}

const routeById: Record<ArtifactScenarioId, ArtboardCase["route"]> = {
  "LG-1": "/", "LG-2": "/", "LG-3": "/",
  "LG-4": "/account",
  "LG-5": "/reviews", "LG-6": "/reviews", "LG-7": "/reviews", "LG-8": "/reviews", "LG-9": "/reviews", "LG-10": "/reviews", "LG-11": "/reviews",
  "LG-12": "/reviews/:reviewId", "LG-13": "/reviews/:reviewId", "LG-14": "/reviews", "LG-15": "/reviews/:reviewId", "LG-16": "/reviews/:reviewId", "LG-17": "/reviews/:reviewId", "LG-18": "/reviews/:reviewId", "LG-19": "/reviews/:reviewId", "LG-20": "/reviews/:reviewId", "LG-21": "/reviews", "LG-22": "/reviews/:reviewId", "LG-23": "/reviews/:reviewId", "LG-24": "/reviews/:reviewId", "LG-25": "/reviews", "LG-26": "/reviews/:reviewId", "LG-27": "/reviews/:reviewId", "LG-28": "/reviews", "LG-29": "/reviews/:reviewId", "LG-30": "/reviews/:reviewId", "LG-31": "/reviews/:reviewId", "LG-32": "/reviews/:reviewId", "LG-33": "/reviews/:reviewId", "LG-34": "/reviews/:reviewId",
  "LG-35": "/notifications", "LG-36": "/notifications", "LG-37": "/notifications",
  "LG-38": "/account", "LG-39": "/account", "LG-40": "/account", "LG-41": "/notifications",
};

export const artboardMatrix: ArtboardCase[] = artifactScenarioIds.map((id) => ({
  id,
  route: routeById[id],
  scenario: id,
  expectedState: artifactScenarios[id].expectedState,
  expectedInteraction: artifactScenarios[id].expectedInteraction,
}));
