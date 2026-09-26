import type { TFunction } from "i18next";
import type { Confidence } from "../types/assessment";

export function confidenceWording(confidence: Confidence, t: TFunction): string {
  return t(`confidence.${confidence}`);
}
