import ThreadExperience from "../_components/ThreadExperience";
import { CardDetailFetchError, fetchCardDetail } from "@/lib/api/server";

type ThreadPageProps = {
  params: { cardId: string };
};

export default async function ThreadByCardPage({ params }: ThreadPageProps) {
  const cardId = params.cardId;

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
