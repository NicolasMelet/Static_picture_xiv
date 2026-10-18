"""Publishes the image on GitHub Pages through the GitHub REST API (no git needed)."""
import base64
from pathlib import Path

import requests

API = "https://api.github.com"


class GitHubPages:
    def __init__(self, token, repo, branch="gh-pages", path="prog.png"):
        self.repo = repo          # "owner/name"
        self.branch = branch
        self.path = path
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    @property
    def public_url(self):
        owner, name = self.repo.split("/")
        return f"https://{owner.lower()}.github.io/{name}/{self.path}"

    def upload(self, local_file, message):
        """Creates or replaces the file on the branch (one commit); GitHub Pages then redeploys."""
        url = f"{API}/repos/{self.repo}/contents/{self.path}"
        current = self.session.get(url, params={"ref": self.branch})
        body = {
            "message": message,
            "branch": self.branch,
            "content": base64.b64encode(Path(local_file).read_bytes()).decode(),
        }
        if current.status_code == 200:
            body["sha"] = current.json()["sha"]      # required to replace an existing file
        self.session.put(url, json=body).raise_for_status()
        return self.public_url
