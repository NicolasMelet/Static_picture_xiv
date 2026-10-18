"""Minimal client for the FFLogs v2 GraphQL API (client credentials, public data only)."""
import time

import requests

TOKEN_URL = "https://www.fflogs.com/oauth/token"
API_URL = "https://www.fflogs.com/api/v2/client"


class FFLogs:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expiry = 0

    def _auth(self):
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        r = requests.post(TOKEN_URL, data={"grant_type": "client_credentials"},
                          auth=(self.client_id, self.client_secret), timeout=30)
        r.raise_for_status()
        data = r.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600)
        return self._token

    def query(self, gql, variables=None):
        r = requests.post(API_URL, json={"query": gql, "variables": variables or {}},
                          headers={"Authorization": f"Bearer {self._auth()}"}, timeout=60)
        r.raise_for_status()
        payload = r.json()
        if payload.get("errors"):
            raise RuntimeError(payload["errors"])
        return payload["data"]

    def zones(self):
        """Every zone (raid tier, ultimate, trial group...) with its fights."""
        data = self.query("""
            { worldData { zones { id name expansion { id name } encounters { id name } } } }""")
        return data["worldData"]["zones"]

    def zone(self, zone_id):
        data = self.query("""
            query($id: Int!) { worldData { zone(id: $id) { id name encounters { id name } } } }""",
                          {"id": zone_id})
        return data["worldData"]["zone"]

    def static(self, static_id):
        """A static is an FFLogs guild of type 1; its tags are its raid teams."""
        data = self.query("""
            query($id: Int!) { guildData { guild(id: $id) {
                id name server { name } tags { id name }
            } } }""", {"id": static_id})
        return data["guildData"]["guild"]

    def report_list(self, static_id, zone_id, raid_team_id=None):
        """Code, start and end time of every report of the static for a zone."""
        reports, page = [], 1
        while True:
            data = self.query("""
                query($g: Int, $t: Int, $z: Int, $p: Int) { reportData {
                    reports(guildID: $g, guildTagID: $t, zoneID: $z, limit: 100, page: $p) {
                        has_more_pages
                        data { code startTime endTime }
                    }
                } }""", {"g": static_id, "t": raid_team_id, "z": zone_id, "p": page})
            result = data["reportData"]["reports"]
            reports.extend(result["data"])
            if not result["has_more_pages"]:
                return reports
            page += 1

    def report_fights(self, codes):
        """Fights and phase definitions of several reports, in a single query (GraphQL aliases)."""
        if not codes:
            return {}
        parts = [f"""
            r{i}: report(code: "{code}", allowUnlisted: true) {{
                code startTime
                phases {{ encounterID phases {{ id name isIntermission }} }}
                fights {{
                    startTime encounterID difficulty kill fightPercentage bossPercentage
                    lastPhase lastPhaseAsAbsoluteIndex lastPhaseIsIntermission
                }}
            }}""" for i, code in enumerate(codes)]
        data = self.query("{ reportData {" + "".join(parts) + "} }")
        return {report["code"]: report for report in data["reportData"].values() if report}
