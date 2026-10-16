"""Client minimal pour l'API v2 (GraphQL) de FFLogs."""
import time

import requests

TOKEN_URL = "https://www.fflogs.com/oauth/token"
API_URL = "https://www.fflogs.com/api/v2/client"
ASSETS = "https://assets.rpglogs.com/img/ff"


def zone_image_url(zone_id):
    return f"{ASSETS}/zones/zone-{zone_id}.png"


def boss_image_url(encounter_id):
    return f"{ASSETS}/bosses/{encounter_id}-icon.jpg"


class FFLogs:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_exp = 0

    def _auth(self):
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        r = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        self._token = data["access_token"]
        self._token_exp = time.time() + data.get("expires_in", 3600)
        return self._token

    def query(self, gql, variables=None):
        r = requests.post(
            API_URL,
            json={"query": gql, "variables": variables or {}},
            headers={"Authorization": f"Bearer {self._auth()}"},
            timeout=60,
        )
        r.raise_for_status()
        payload = r.json()
        if payload.get("errors"):
            raise RuntimeError(payload["errors"])
        return payload["data"]

    # --- Référentiel -----------------------------------------------------

    def zones(self):
        """Tous les contenus (zones) avec leurs boss."""
        data = self.query("""
            { worldData { zones {
                id name frozen
                expansion { id name }
                encounters { id name }
            } } }""")
        return data["worldData"]["zones"]

    def zone(self, zone_id):
        data = self.query("""
            query($id: Int!) { worldData { zone(id: $id) {
                id name expansion { name } encounters { id name }
            } } }""", {"id": zone_id})
        return data["worldData"]["zone"]

    def guild(self, guild_id=None, name=None, server=None, region=None):
        if guild_id:
            args, variables = "id: $id", {"id": guild_id}
            sig = "$id: Int"
        else:
            args = "name: $name, serverSlug: $server, serverRegion: $region"
            variables = {"name": name, "server": server, "region": region}
            sig = "$name: String, $server: String, $region: String"
        data = self.query(f"""
            query({sig}) {{ guildData {{ guild({args}) {{
                id name server {{ name }} tags {{ id name }}
            }} }} }}""", variables)
        return data["guildData"]["guild"]

    # --- Rapports ------------------------------------------------------------

    def report_list(self, guild_id, zone_id, tag_id=None, max_pages=20):
        """Liste (code, startTime, endTime) des rapports du groupe pour la zone."""
        out, page = [], 1
        while page <= max_pages:
            data = self.query("""
                query($g: Int, $t: Int, $z: Int, $p: Int) { reportData {
                    reports(guildID: $g, guildTagID: $t, zoneID: $z, limit: 100, page: $p) {
                        has_more_pages
                        data { code startTime endTime }
                    }
                } }""", {"g": guild_id, "t": tag_id, "z": zone_id, "p": page})
            reports = data["reportData"]["reports"]
            out.extend(reports["data"])
            if not reports["has_more_pages"]:
                break
            page += 1
        return out

    def report_fights(self, codes):
        """Combats de plusieurs rapports en une requête (alias GraphQL)."""
        if not codes:
            return {}
        parts = []
        for i, code in enumerate(codes):
            parts.append(f"""
                r{i}: report(code: "{code}") {{
                    code
                    phases {{ encounterID phases {{ id name isIntermission }} }}
                    fights {{
                        id encounterID difficulty kill
                        fightPercentage bossPercentage
                        lastPhase lastPhaseIsIntermission
                    }}
                }}""")
        data = self.query("{ reportData {" + "".join(parts) + "} }")
        return {v["code"]: v for v in data["reportData"].values() if v}
