"""Publication de l'image sur GitHub Pages via l'API GitHub (pas besoin de git)."""
import base64

import requests

API = "https://api.github.com"


class GitHubPages:
    def __init__(self, token, repo, branch="gh-pages", path="prog.png"):
        self.repo = repo          # "utilisateur/depot"
        self.branch = branch
        self.path = path
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    @property
    def public_url(self):
        owner, name = self.repo.split("/")
        if name.lower() == f"{owner.lower()}.github.io":
            return f"https://{owner.lower()}.github.io/{self.path}"
        return f"https://{owner.lower()}.github.io/{name}/{self.path}"

    def _ensure_branch(self):
        r = self.s.get(f"{API}/repos/{self.repo}/branches/{self.branch}")
        if r.status_code == 200:
            return
        if r.status_code != 404:
            r.raise_for_status()
        # Crée la branche à partir de la branche par défaut du dépôt.
        repo = self.s.get(f"{API}/repos/{self.repo}")
        repo.raise_for_status()
        default = repo.json()["default_branch"]
        ref = self.s.get(f"{API}/repos/{self.repo}/git/ref/heads/{default}")
        ref.raise_for_status()
        self.s.post(f"{API}/repos/{self.repo}/git/refs", json={
            "ref": f"refs/heads/{self.branch}",
            "sha": ref.json()["object"]["sha"],
        }).raise_for_status()

    def upload(self, local_file, message="Progression update"):
        self._ensure_branch()
        url = f"{API}/repos/{self.repo}/contents/{self.path}"
        r = self.s.get(url, params={"ref": self.branch})
        sha = r.json().get("sha") if r.status_code == 200 else None
        with open(local_file, "rb") as fh:
            content = base64.b64encode(fh.read()).decode()
        body = {"message": message, "content": content, "branch": self.branch}
        if sha:
            body["sha"] = sha
        self.s.put(url, json=body).raise_for_status()
        return self.public_url
