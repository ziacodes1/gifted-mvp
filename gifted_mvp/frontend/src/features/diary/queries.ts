import { useQuery } from "@tanstack/react-query";
import { diaryApi } from "../../api/diary";

export const DIARY_OVERVIEW_KEY = ["diary-overview"] as const;

/** Object URL for a private diary photo (fetched with the learner's token; cached per id). */
export function usePhotoUrl(id: number | undefined) {
  return useQuery({
    queryKey: ["diary-photo", id],
    queryFn: async () => URL.createObjectURL(await diaryApi.photoBlob(id!)),
    enabled: id !== undefined,
    staleTime: Infinity,
    gcTime: 30 * 60_000,
  }).data;
}
