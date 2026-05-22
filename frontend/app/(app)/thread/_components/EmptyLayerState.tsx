import { cn } from "@/lib/utils";

type EmptyLayerStateProps = {
  title: string;
  description: string;
  className?: string;
};

export function EmptyLayerState({ title, description, className }: EmptyLayerStateProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center",
        className,
      )}
    >
      <p className="font-display text-base font-semibold text-slate-800">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-slate-500">{description}</p>
    </div>
  );
}
