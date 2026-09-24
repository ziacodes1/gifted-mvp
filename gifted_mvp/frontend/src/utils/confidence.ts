import type { Confidence } from "../types/assessment";

const WORDING: Record<Confidence, string> = {
  LOW: "An early signal — more exploration will help clarify this.",
  MEDIUM: "A fairly consistent early signal.",
  HIGH: "A strong, consistent signal across your answers.",
};

export function confidenceWording(confidence: Confidence): string {
  return WORDING[confidence];
}
