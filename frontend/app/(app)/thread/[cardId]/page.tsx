import ThreadExperience from "../_components/ThreadExperience";

type ThreadPageProps = {
  params: { cardId: string };
};

export default function ThreadByCardPage({ params }: ThreadPageProps) {
  return <ThreadExperience cardId={params.cardId} />;
}
