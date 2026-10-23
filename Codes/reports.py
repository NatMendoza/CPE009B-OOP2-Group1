from collections import Counter
from datetime import date, datetime
from decimal import Decimal

from errors import StorageError, ValidationError
from storage import TransactionLog
from validators import money, parse_quantity


class SalesReport:
    # Voided sales are left out of every number here.

    def __init__(self, log: TransactionLog):
        self._log = log

    @staticmethod
    def _day(day) -> str:
        # Accepts None (today), a date/datetime, or a 'YYYY-MM-DD' string.
        if day is None:
            return date.today().isoformat()
        if isinstance(day, datetime):
            return day.date().isoformat()
        if isinstance(day, date):
            return day.isoformat()
        try:
            return date.fromisoformat(str(day).strip()).isoformat()
        except ValueError:
            raise ValidationError("Date must be in YYYY-MM-DD format, e.g. 2026-10-10.") from None

    # gets the sales of one day, voided ones are skipped unless asked for
    def _headers_for(self, iso_day: str, include_voided=False) -> list[dict]:
        return [r for r in self._log.read_headers()
                if r["datetime"].startswith(iso_day)
                and (include_voided or r.get("status", "paid") != "voided")]

    def summary(self, day=None) -> dict:
        iso = self._day(day)
        rows = self._headers_for(iso)
        zero = Decimal("0.00")
        # voided count is all the sales that day minus the normal ones
        voided = len(self._headers_for(iso, include_voided=True)) - len(rows)
        return {
            "date": iso,
            "transactions": len(rows),
            "voided": voided,
            "gross_sales": sum((money(r["subtotal"]) for r in rows), zero),
            "discounts": sum((money(r["discount"]) for r in rows), zero),
            "vat": sum((money(r["vat"]) for r in rows), zero),
            "net_sales": sum((money(r["total"]) for r in rows), zero),
            "by_customer_type": dict(Counter(r["customer_type"] for r in rows)),
        }

    def best_sellers(self, limit=5, day=None) -> list[dict]:
        limit = parse_quantity(limit)
        # only count items that belong to the sales of that day
        ids = {r["transaction_id"] for r in self._headers_for(self._day(day))}
        qty, revenue, names = Counter(), {}, {}
        for r in self._log.read_details():
            if r["transaction_id"] not in ids:
                continue
            try:
                q = int(r["quantity"])
            except ValueError:
                raise StorageError(
                    f"transaction_items.csv has a bad quantity: {r['quantity']!r}") from None
            qty[r["serial"]] += q
            revenue[r["serial"]] = revenue.get(r["serial"], Decimal("0.00")) + money(r["line_total"])
            names[r["serial"]] = r["name"]
        # most sold first, then highest revenue
        ranked = sorted(qty, key=lambda s: (-qty[s], -revenue[s], s))[:limit]
        return [{"serial": s, "name": names[s], "quantity": qty[s], "revenue": revenue[s]}
                for s in ranked]