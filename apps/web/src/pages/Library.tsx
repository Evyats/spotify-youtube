import { useEffect, useState } from "react";
import ResponseViewer from "../components/ResponseViewer";
import type { AppHelpers } from "../App";
import type { LibrarySong } from "../types";

type LibraryPageProps = {
  helpers: AppHelpers;
  responseText: string;
  clearResponse: () => void;
};

export default function LibraryPage({ helpers, responseText, clearResponse }: LibraryPageProps) {
  const [songs, setSongs] = useState<LibrarySong[]>([]);
  const [nowPlaying, setNowPlaying] = useState("");
  const [audioSrc, setAudioSrc] = useState("");

  async function loadLibrary() {
    if (!helpers.requireAuth()) return;
    const data = (await helpers.api("/library")) as { songs?: LibrarySong[] };
    setSongs(data.songs || []);
    helpers.setResponse(data);
  }

  async function playSong(song: LibrarySong) {
    const data = (await helpers.api(`/stream/${song.id}`)) as { stream_url?: string };
    if (!data.stream_url) throw new Error("Missing stream URL");
    setAudioSrc(data.stream_url);
    setNowPlaying(`${song.title} - ${song.artist}`);
    helpers.setResponse(data);
  }

  useEffect(() => {
    loadLibrary().catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-panel p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Library</h2>
          <button className="btn-secondary" onClick={() => loadLibrary().catch((e) => helpers.notify(e.message))}>
            Reload
          </button>
        </div>
        {songs.length === 0 ? <p className="text-sm text-muted">Library is empty.</p> : null}
        <div className="grid gap-3">
          {songs.map((song) => (
            <article key={song.id} className="rounded-lg border border-slate-200 p-3">
              <h3 className="font-semibold">{song.title}</h3>
              <p className="text-sm text-muted">{song.artist}</p>
              <button className="btn-primary mt-2" onClick={() => playSong(song).catch((e) => helpers.notify(e.message))}>
                Play
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-panel p-4">
        <h3 className="mb-1 font-semibold">Now Playing</h3>
        <p className="mb-3 text-sm text-muted">{nowPlaying || "Nothing selected"}</p>
        <audio controls className="w-full" src={audioSrc} />
      </section>

      <ResponseViewer data={responseText} onClear={clearResponse} />
    </div>
  );
}
