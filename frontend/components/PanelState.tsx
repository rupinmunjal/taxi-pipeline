export function PanelState({ message, error = false }: { message: string; error?: boolean }) {
  return (
    <div
      className={`mt-6 flex h-64 items-center justify-center rounded-xl border border-dashed px-6 text-center text-sm ${
        error ? "border-red-200 bg-red-50 text-red-800" : "border-zinc-200 bg-zinc-50 text-zinc-500"
      }`}
      role={error ? "alert" : "status"}
    >
      {message}
    </div>
  );
}

export function PanelSkeleton() {
  return <div className="mt-6 h-64 animate-pulse rounded-xl bg-zinc-100" aria-label="Loading chart" />;
}
