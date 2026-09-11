import re

from django.db import connection


class SearchService:
    """Search entrances by street/address text or bare EGID.

    Bare digits are treated as an exact EGID lookup (fast path for the common
    "I know the EGID" case). Free text uses Postgres full-text search over
    entrance.search_vector, ranked by ts_rank; a pg_trgm similarity fallback
    on STRNAME covers typos when FTS finds nothing (FTS requires matching
    lexemes, so it can't tolerate misspellings on its own).
    """

    def search(self, term: str, limit: int = 20) -> list[dict]:
        term = (term or "").strip()
        if not term:
            return []
        if re.fullmatch(r"\d+", term):
            rows = self._egid(int(term), limit)
            if rows:
                return rows
        if not re.search(r"\w", term):
            # No word characters (e.g. "!!!") would make plainto_tsquery
            # produce an empty tsquery, which matches nothing usefully.
            return []
        rows = self._fts(term, limit)
        if not rows:
            rows = self._trgm(term, limit)
        return rows

    def _egid(self, egid, limit):
        with connection.cursor() as cur:
            cur.execute(
                'SELECT DISTINCT "EGID", address_label FROM entrance WHERE "EGID" = %s LIMIT %s',
                (egid, limit),
            )
            return [{"egid": r[0], "label": r[1]} for r in cur.fetchall()]

    def _fts(self, term, limit):
        with connection.cursor() as cur:
            cur.execute(
                'SELECT "EGID", address_label, ts_rank(search_vector, q) AS rank '
                "FROM entrance, plainto_tsquery('simple', %s) q "
                "WHERE search_vector @@ q ORDER BY rank DESC LIMIT %s",
                (term, limit),
            )
            return [{"egid": r[0], "label": r[1]} for r in cur.fetchall()]

    def _trgm(self, term, limit):
        with connection.cursor() as cur:
            # The "%" operator's default pg_trgm.similarity_threshold (0.3) is
            # already permissive enough to catch a single-character typo on a
            # street-name-length string; verified via test_search_fuzzy_typo.
            cur.execute(
                'SELECT "EGID", address_label, similarity("STRNAME", %s) AS sim '
                'FROM entrance WHERE "STRNAME" %% %s ORDER BY sim DESC LIMIT %s',
                (term, term, limit),
            )
            return [{"egid": r[0], "label": r[1]} for r in cur.fetchall()]
