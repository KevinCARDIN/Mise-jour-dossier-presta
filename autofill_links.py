"""Job planifie : ajoute le lien du questionnaire sur les lignes du groupe
PRESTATAIRES : Validés qui ne l'ont pas encore. Idempotent — execute periodiquement
sur Railway (cron) pour couvrir les nouveaux prestataires."""
import os
import json
import time
import requests

MONDAY_API = "https://api.monday.com/v2"
BOARD_ID = 1281234391
GROUP_ID = "nouveau_groupe77136"          # PRESTATAIRES : Validés
LINK_COL = "link_mm3f6vq8"                # colonne "Questionnaire prestataire"
APP_BASE = "https://questionnaire-presta-production.up.railway.app/?item="
TOKEN = os.environ["MONDAY_API_TOKEN"]


def mq(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    r = requests.post(MONDAY_API, json=payload,
                      headers={"Authorization": TOKEN, "API-Version": "2024-10"}, timeout=60)
    d = r.json()
    if d.get("errors"):
        raise RuntimeError(d["errors"])
    return d["data"]


def fetch_group_items():
    items, cursor = [], None
    while True:
        if cursor:
            q = ('query ($c: String!) { next_items_page(cursor: $c, limit: 250) '
                 '{ cursor items { id column_values(ids: ["%s"]) { text } } } }') % LINK_COL
            page = mq(q, {"c": cursor})["next_items_page"]
        else:
            q = ('{ boards(ids: %d) { groups(ids: ["%s"]) { items_page(limit: 250) '
                 '{ cursor items { id column_values(ids: ["%s"]) { text } } } } } }') % (
                BOARD_ID, GROUP_ID, LINK_COL)
            page = mq(q)["boards"][0]["groups"][0]["items_page"]
        items += page["items"]
        cursor = page["cursor"]
        if not cursor:
            break
    return items


def main():
    items = fetch_group_items()
    todo = [it["id"] for it in items
            if not (it["column_values"][0]["text"] or "").strip()]
    print(f"{len(items)} prestataires validés, {len(todo)} sans lien.")

    ok, batch = 0, 15
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        decl = ",".join(f"$v{j}:JSON!" for j in range(len(chunk)))
        body, vs = "", {}
        for j, iid in enumerate(chunk):
            body += (f' m{j}: change_multiple_column_values'
                     f'(board_id:{BOARD_ID},item_id:"{iid}",column_values:$v{j}){{id}}')
            vs[f"v{j}"] = json.dumps(
                {LINK_COL: {"url": APP_BASE + iid, "text": "Ouvrir le questionnaire"}})
        mq("mutation(" + decl + "){" + body + "}", vs)
        ok += len(chunk)
        time.sleep(0.3)
    print(f"Liens ajoutés : {ok}")


if __name__ == "__main__":
    main()
