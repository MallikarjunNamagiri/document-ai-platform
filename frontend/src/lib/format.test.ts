import { describe, expect, it } from "vitest";
import { formatMetric } from "./format";

describe("formatMetric", () => {
  it.each([
    [0.834, "83%"],
    [1, "100%"],
    [0, "0%"], // a real zero score is a real result and must stay visible
  ])("formats %s as %s", (value, expected) => {
    expect(formatMetric(value)).toBe(expected);
  });

  it.each([[null], [undefined], [Number.NaN]])(
    "shows n/a (never 0%%) when the metric could not be computed: %s",
    (value) => {
      expect(formatMetric(value)).toBe("n/a");
    }
  );
});
