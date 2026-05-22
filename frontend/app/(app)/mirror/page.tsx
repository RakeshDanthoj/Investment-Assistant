import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function MirrorPlaceholderPage() {
  return (
    <main className="p-8">
      <Card className="max-w-lg border-none shadow-none">
        <CardHeader>
          <CardTitle className="font-display text-2xl font-bold">The Mirror</CardTitle>
          <CardDescription>Phase 2 surface.</CardDescription>
        </CardHeader>
        <CardContent />
      </Card>
    </main>
  );
}
