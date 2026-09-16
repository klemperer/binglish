from binglish.core.constants import (
    GITHUB_LATEST_RELEASE_URL,
    GITHUB_RELEASES_URL,
    RELEASE_JSON_URL,
)
from binglish.services.update import github_releases_url


def test_github_urls_exist():
    assert GITHUB_RELEASES_URL.startswith("https://github.com/")
    assert GITHUB_LATEST_RELEASE_URL.endswith("/releases/latest")
    assert "blueforge" in RELEASE_JSON_URL  # CDN channel retained


def test_github_releases_url_helper():
    assert github_releases_url() == GITHUB_LATEST_RELEASE_URL


def test_tag_stripping_semantics():
    from binglish.core.version import is_newer

    # tag_name from GitHub is usually v2.0.0
    assert is_newer("2.1.0", "2.0.0")
    assert not is_newer("2.0.0", "2.0.0")
