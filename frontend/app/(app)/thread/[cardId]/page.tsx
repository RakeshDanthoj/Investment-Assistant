import { Suspense } from "react";

import { ThreadContentSection } from "../ThreadContentSection";

import ThreadLoading from "./loading";

type ThreadPageProps = {
  params: { cardId: string };
};

export default function ThreadByCardPage({ params }: ThreadPageProps) {
  const cardId = params.cardId;

  return (
    <Suspense fallback={<ThreadLoading />}>
      <ThreadContentSection cardId={cardId} />
    </Suspense>
  );
}
