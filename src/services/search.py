import re

from django.db import connections


class SearchService:
    def search(self, term: str, limit: int = 20) -> list[dict]:
        term = (term or "").strip()
        if not term:
            return []
        results: list[dict] = []
        if re.fullmatch(r"\d+", term):
            with connections["default"].cursor() as cur:
                cur.execute("SELECT egid, label FROM search_entrance WHERE egid = ? LIMIT ?", (int(term), limit))
                results = [{"egid": r[0], "label": r[1]} for r in cur.fetchall()]
            if results:
                return results
        match = " ".join(f'"{w}"*' for w in re.findall(r"\w+", term))
        if not match:
            # No word characters at all (e.g. "!!!", "-", "???") — an empty FTS5
            # MATCH operand raises "fts5: syntax error near ''"; short-circuit
            # instead of letting that propagate as an uncaught 500 from the
            # live keyup search box.
            return []
        with connections["default"].cursor() as cur:
            cur.execute(
                "SELECT egid, label FROM search_entrance WHERE search_entrance MATCH ? ORDER BY rank LIMIT ?",
                (match, limit),
            )
            results = [{"egid": r[0], "label": r[1]} for r in cur.fetchall()]
        return results
