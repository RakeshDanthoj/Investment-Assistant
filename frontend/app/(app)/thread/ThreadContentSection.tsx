import ThreadExperience from "./_components/ThreadExperience";
import { CardDetailFetchError, fetchCardDetail } from "@/lib/api/server";

type ThreadContentSectionProps = {
  cardId: string;
};

/** Async RSC boundary: streams Thread payload after shell HTML (P2.5-S4 / PC-2.1). */
export async function ThreadContentSection({ cardId }: ThreadContentSectionProps) {
  try {
    const initialData = await fetchCardDetail(cardId, "current");
    return <ThreadExperience cardId={cardId} initialData={initialData} />;
  } catch (error) {
    const message =
      error instanceof CardDetailFetchError
        ? error.message
        : error instanceof Error
          ? error.message
          : "Could not load card.";

    return <ThreadExperience cardId={cardId} initialError={message} />;
  }
}
