import { Card, CardContent } from "@/components/ui/card";

export default function ThreadPlaceholderPage() {
  return (
    <main className="p-8">
      <Card className="max-w-lg py-0 shadow-none">
        <CardContent className="p-6">
          <h1 className="font-display text-2xl font-bold text-slate-900">The Thread</h1>
          <p className="mt-2 text-slate-500">Coming in Phase 1.</p>
        </CardContent>
      </Card>
    </main>
  );
}
