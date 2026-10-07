import { describe, expect, it } from "vitest";
import { band, examText, groupQuestions, labelBand, localDate, parseLocal, signed } from "../src/util.js";
import { detailToMessage } from "../src/api.js";

describe("localDate", () => {
  it("uses the local calendar day, not UTC", () => {
    // 00:30 local on 5 Oct would be 4 Oct in UTC for any zone east of UTC; localDate must still say the 5th
    expect(localDate(new Date(2026, 9, 5, 0, 30))).toBe("2026-10-05");
    expect(localDate(new Date(2026, 0, 1, 23, 59))).toBe("2026-01-01");
  });
  it("round-trips with parseLocal", () => {
    expect(localDate(parseLocal("2026-03-09"))).toBe("2026-03-09");
  });
});

describe("risk bands", () => {
  it("maps 0-10 scores to bands", () => {
    expect(band(0)).toBe("low");
    expect(band(3.49)).toBe("low");
    expect(band(3.5)).toBe("mid");
    expect(band(6.5)).toBe("high");
    expect(band(null)).toBe("none");
  });
  it("maps labels", () => {
    expect(labelBand("Medium")).toBe("mid");
    expect(labelBand("nope")).toBe("none");
  });
});

describe("formatting", () => {
  it("signs numbers", () => {
    expect(signed(1.234)).toBe("+1.2");
    expect(signed(-0.5)).toBe("-0.5");
    expect(signed(null)).toBe("—");
  });
  it("describes the exam countdown", () => {
    expect(examText({ days_remaining: 9, exam_label: "Finals" })).toBe("9 days to Finals");
    expect(examText({ days_remaining: 1, exam_label: null })).toBe("1 day to your exam");
    expect(examText({ days_remaining: 0, exam_label: "Finals" })).toBe("Finals is today");
    expect(examText({ days_remaining: -2, exam_label: "Finals" })).toBe("Finals was 2 days ago");
    expect(examText({ days_remaining: null })).toBeNull();
  });
  it("groups questions in order", () => {
    const g = groupQuestions([{ group: "Mind", key: "a" }, { group: "Body", key: "b" }, { group: "Mind", key: "c" }]);
    expect(g.map((x) => [x.name, x.items.length])).toEqual([["Mind", 2], ["Body", 1]]);
  });
});

describe("API error messages", () => {
  it("passes string details through", () => {
    expect(detailToMessage("Incorrect email or password")).toBe("Incorrect email or password");
  });
  it("flattens FastAPI validation errors", () => {
    const msg = detailToMessage([{ loc: ["body", "password"], msg: "String should have at least 8 characters" }]);
    expect(msg).toBe("password: String should have at least 8 characters");
  });
  it("returns null when there is no detail", () => {
    expect(detailToMessage(undefined)).toBeNull();
  });
});
