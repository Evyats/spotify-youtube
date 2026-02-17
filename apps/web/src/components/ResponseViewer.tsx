type ResponseViewerProps = {
  data: string;
  onClear: () => void;
};

export default function ResponseViewer({ data, onClear }: ResponseViewerProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-panel p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Response Viewer</h3>
        <button
          type="button"
          onClick={onClear}
          className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
        >
          Clear
        </button>
      </div>
      <pre className="max-h-80 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{data}</pre>
    </section>
  );
}
