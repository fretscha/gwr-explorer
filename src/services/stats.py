from django.db import connection


class StatsService:
    def metric(self, name: str) -> list[dict]:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT dim_key, dim_label, value FROM mv_stats WHERE metric = %s ORDER BY value DESC",
                (name,),
            )
            return [{"key": r[0], "label": r[1], "value": r[2]} for r in cur.fetchall()]
