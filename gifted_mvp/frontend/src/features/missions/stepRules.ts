import type { MissionStep, StepResponse } from "../../types/mission";

/** Client-side mirror of the server rules, used only to enable "Continue". */
export function isStepComplete(step: MissionStep, value: StepResponse | undefined): boolean {
  const c = step.content;
  if (step.type === "CONTEXT") return true;
  if (!value) return false;
  if (step.type === "MULTI_SELECT") {
    const n = selectedList(value).length;
    return n >= (c.min ?? 1) && n <= (c.max ?? n);
  }
  if (step.type === "BUDGET") {
    const sel = selectedList(value);
    return sel.length >= (c.min_items ?? 1) && spent(step, sel) <= (c.budget ?? 0);
  }
  if (step.type === "SINGLE_CHOICE") return typeof value.selected === "string";
  if (step.type === "REFLECTION") {
    return (c.fields ?? []).every((f) => {
      const len = String(value[f.key] ?? "").trim().length;
      return (!f.required || len >= (f.min_length ?? 1)) && len <= (f.max_length ?? 600);
    });
  }
  return false;
}

export function selectedList(value: StepResponse | undefined): string[] {
  return Array.isArray(value?.selected) ? (value!.selected as string[]) : [];
}

export function spent(step: MissionStep, selected: string[]) {
  const costs = Object.fromEntries((step.content.options ?? []).map((o) => [o.key, o.cost ?? 0]));
  return selected.reduce((sum, k) => sum + (costs[k] ?? 0), 0);
}
