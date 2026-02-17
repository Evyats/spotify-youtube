export type SearchCandidate = {
  source_provider: string;
  source_id: string;
  title: string;
  channel: string;
  confidence_score: number;
};

export type LibrarySong = {
  id: string;
  title: string;
  artist: string;
};
