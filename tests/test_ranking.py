from packages.shared.ranking import score_candidate


def test_official_beats_live_variant():
    query = "song name artist"
    official = {
        "title": "Song Name - Official Audio",
        "channel": "Artist Official",
        "view_count": 50_000_000,
    }
    live = {
        "title": "Song Name Live at Stadium",
        "channel": "Random Channel",
        "view_count": 2_000_000,
    }

    assert score_candidate(query, official) > score_candidate(query, live)
