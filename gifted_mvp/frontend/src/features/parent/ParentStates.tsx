export function ParentPageState({ error }: { error: boolean }) {
  if (error) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">We couldn't load this page right now.</p>
        <p className="mt-2 text-sm text-sage-600">Please try again in a moment.</p>
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-6xl animate-pulse space-y-5" aria-busy="true">
      <div className="h-72 rounded-3xl bg-white" />
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="h-56 rounded-2xl bg-white" />
        <div className="h-56 rounded-2xl bg-white" />
      </div>
    </div>
  );
}

export function NoChildConnected() {
  return (
    <div className="card mx-auto max-w-xl md:p-10">
      <h1 className="text-3xl">No child connected yet</h1>
      <p className="mt-3 leading-relaxed text-sage-600">
        Ask your child for their Gifted connection code (it looks like <span className="font-medium text-forest-700">GFT-48291</span>)
        to see their growth signals here.
      </p>
    </div>
  );
}
