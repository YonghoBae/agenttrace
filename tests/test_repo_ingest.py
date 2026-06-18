from __future__ import annotations

from agenttrace.services.repo_ingest import (
    MAX_REPO_INGEST_README_CHARS,
    repo_digest_to_summary_request,
)


def test_repo_digest_to_summary_request_truncates_large_content_payload():
    payload = {
        "repo_url": "obra/superpowers",
        "content": "x" * (MAX_REPO_INGEST_README_CHARS + 1),
        "tree": "Directory structure:\n└── README.md",
    }

    summary_request = repo_digest_to_summary_request(
        payload,
        fallback_full_name="obra/superpowers",
    )

    assert summary_request.repository.repository_id == "obra/superpowers"
    assert summary_request.repository.full_name == "obra/superpowers"
    assert summary_request.repository.github_url == "https://github.com/obra/superpowers"
    assert summary_request.readme_text is not None
    assert len(summary_request.readme_text) < MAX_REPO_INGEST_README_CHARS + 100
    assert "Truncated by AgentTrace" in summary_request.readme_text
    assert summary_request.shallow_file_tree == ["README.md"]


def test_repo_digest_to_summary_request_maps_repository_digest_fields():
    payload = {
        "repository": {
            "id": "repo-1",
            "full_name": "acme/weather-agent",
            "html_url": "https://github.com/acme/weather-agent",
            "description": "Weather automation helpers",
            "topics": ["agent", None, "weather"],
            "language": "Python",
            "stargazers_count": 11,
            "forks_count": 3,
            "pushed_at": "2026-06-16T00:00:00Z",
            "updated_at": "2026-06-17T00:00:00Z",
        },
        "readme": "# Weather Agent",
        "file_tree": ["README.md", {"path": "src/weather_agent/"}],
    }

    summary_request = repo_digest_to_summary_request(
        payload,
        fallback_full_name="fallback/repo",
    )

    assert summary_request.repository.model_dump() == {
        "repository_id": "repo-1",
        "full_name": "acme/weather-agent",
        "github_url": "https://github.com/acme/weather-agent",
        "description": "Weather automation helpers",
        "topics": ["agent", "weather"],
        "primary_language": "Python",
        "stars": 11,
        "forks": 3,
        "pushed_at": "2026-06-16T00:00:00Z",
        "github_updated_at": "2026-06-17T00:00:00Z",
    }
    assert summary_request.readme_text == "# Weather Agent"
    assert summary_request.shallow_file_tree == ["README.md", "src/weather_agent/"]


def test_repo_digest_to_summary_request_preserves_zero_stars_and_forks():
    payload = {
        "repository": {
            "full_name": "acme/weather-agent",
            "html_url": "https://github.com/acme/weather-agent",
            "stars": 0,
            "stargazers_count": 11,
            "forks": 0,
            "forks_count": 3,
        }
    }

    summary_request = repo_digest_to_summary_request(
        payload,
        fallback_full_name="fallback/repo",
    )

    assert summary_request.repository.stars == 0
    assert summary_request.repository.forks == 0


def test_repo_digest_to_summary_request_normalizes_repo_url_alias():
    payload = {"repo_url": "https://github.com/acme/weather-agent"}

    summary_request = repo_digest_to_summary_request(
        payload,
        fallback_full_name="fallback/repo",
    )

    assert summary_request.repository.full_name == "acme/weather-agent"
    assert summary_request.repository.github_url == "https://github.com/acme/weather-agent"


def test_repo_digest_to_summary_request_normalizes_short_repo_url_alias():
    payload = {"short_repo_url": "https://github.com/acme/weather-agent"}

    summary_request = repo_digest_to_summary_request(
        payload,
        fallback_full_name="fallback/repo",
    )

    assert summary_request.repository.full_name == "acme/weather-agent"
    assert summary_request.repository.github_url == "https://github.com/acme/weather-agent"
