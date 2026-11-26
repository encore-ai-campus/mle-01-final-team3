import { describe, expect, it } from "vitest";
import { artifactScenarioIds, artifactScenarios } from "../fixtures/artifactScenarios";
import { artboardMatrix } from "../fixtures/artboardMatrix";

describe("Artifact artboard coverage", () => {
  it("contains exactly one case for each of the 41 reference artboards", () => {
    const ids = artboardMatrix.map((item) => item.id);
    expect(ids).toHaveLength(41);
    expect(new Set(ids).size).toBe(41);
    expect(ids).toEqual([...artifactScenarioIds]);
  });

  it("maps every case to a fixture scenario and a supported route", () => {
    for (const item of artboardMatrix) {
      expect(artifactScenarios[item.scenario].id).toBe(item.scenario);
      expect(item.expectedState).not.toHaveLength(0);
      expect(item.expectedInteraction).not.toHaveLength(0);
    }
  });
});
