import { useState } from "react";
import ResponseViewer from "../components/ResponseViewer";
import type { AppHelpers } from "../App";
import type { SearchCandidate } from "../types";

type SearchPageProps = {
  helpers: AppHelpers;
  responseText: string;
  clearResponse: () => void;
};

export default function SearchPage({ helpers, responseText, clearResponse }: SearchPageProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchCandidate[]>([]);

  async function runSearch() {
    if (!helpers.requireAuth()) return;
    const data = (await helpers.api(`/songs/search?q=${encodeURIComponent(query)}`)) as {
      candidates?: SearchCandidate[];
    };
    const candidates = data.candidates || [];
    setResults(candidates);
    helpers.setResponse(data);
    if (candidates.length === 0) helpers.notify("No results found.");
  }

  async function importSong(candidate: SearchCandidate) {
    if (!helpers.requireAuth()) return;
    const data = await helpers.api("/songs/import", {
      method: "POST",
      body: JSON.stringify({
        source_provider: candidate.source_provider || "youtube",
        source_id: candidate.source_id,
        title: candidate.title,
        artist: candidate.channel || "Unknown",
        candidate_meta: candidate
      })
    });
    helpers.setResponse(data);
    helpers.notify("Song import started.");
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-panel p-4">
        <h2 className="mb-3 text-lg font-semibold">Search Top 3</h2>
        <div className="flex flex-col gap-2 md:flex-row">
          <input
            className="input flex-1"
            placeholder="Type song name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn-primary" onClick={() => runSearch().catch((e) => helpers.notify(e.message))}>
            Search
          </button>
        </div>
      </section>

      <section className="grid gap-3">
        {results.map((item, i) => (
          <article key={item.source_id} className="rounded-xl border border-slate-200 bg-panel p-4">
            <h3 className="font-semibold">
              {i + 1}. {item.title}
            </h3>
            <p className="text-sm text-muted">
              {item.channel} | score {item.confidence_score?.toFixed(3)}
            </p>
            <div className="mt-3 flex gap-2">
              <button className="btn-primary" onClick={() => importSong(item).catch((e) => helpers.notify(e.message))}>
                Add to Library
              </button>
              <button
                className="btn-secondary"
                onClick={() => window.open(`https://www.youtube.com/watch?v=${encodeURIComponent(item.source_id)}`, "_blank")}
              >
                Open on YouTube
              </button>
            </div>
          </article>
        ))}
      </section>

      <ResponseViewer data={responseText} onClear={clearResponse} />
    </div>
  );
}
