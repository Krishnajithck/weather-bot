import json
import os
from datetime import datetime

import requests

USERNAME = os.environ.get("GITHUB_USERNAME", "krishnajithck")
OUTPUT_FILE = "projects.json"
API_URL = f"https://api.github.com/users/{USERNAME}/repos"


def get_repos():
    headers = {
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    params = {
        "per_page": 100,
        "sort": "updated",
        "direction": "desc",
    }

    response = requests.get(API_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def normalize_repo(repo):
    return {
        "name": repo.get("name"),
        "description": repo.get("description") or "",
        "html_url": repo.get("html_url"),
        "language": repo.get("language") or "",
        "stargazers_count": repo.get("stargazers_count", 0),
        "forks_count": repo.get("forks_count", 0),
        "updated_at": repo.get("updated_at"),
        "homepage": repo.get("homepage") or "",
    }


def build_payload(repos):
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "github_username": USERNAME,
        "repository_count": len(repos),
        "projects": [normalize_repo(repo) for repo in repos],
    }
    return payload


if __name__ == "__main__":
    try:
        repos = get_repos()
        payload = build_payload(repos)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=2, sort_keys=False)
        print(f"Generated {OUTPUT_FILE} for {USERNAME} with {len(repos)} repos.")
    except requests.HTTPError as http_err:
        print(f"GitHub API request failed: {http_err}")
        raise
    except Exception as err:
        print(f"Unable to generate projects JSON: {err}")
        raise
