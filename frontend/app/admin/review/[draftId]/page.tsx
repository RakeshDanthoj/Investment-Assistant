import ReviewWorkspace from "./ReviewWorkspace";

export default function EditorialReviewPage({
  params,
}: Readonly<{ params: { draftId: string } }>) {
  return <ReviewWorkspace draftId={params.draftId} />;
}
