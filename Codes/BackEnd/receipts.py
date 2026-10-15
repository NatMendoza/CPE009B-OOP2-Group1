from pathlib import Path

from config import RECEIPT_WIDTH, STORE_ADDRESS, STORE_NAME
from errors import StorageError
from transaction import Transaction


def build_receipt(txn: Transaction) -> str:
    W = RECEIPT_WIDTH

    def row(label, value):
        return f"{label}".ljust(W - 14) + f"{value:>14}"

    out = [STORE_NAME.center(W), STORE_ADDRESS.center(W), "=" * W,
           f"Transaction No: {txn.transaction_id}",
           f"Date/Time: {txn.completed_at:%Y-%m-%d %H:%M:%S}",
           f"Cashier: {txn.cashier}", "-" * W]
    for l in txn.lines:
        out.append(l.name[:W])
        out.append(row(f"  {l.quantity} x {l.unit_price:,.2f}", f"{l.line_total:,.2f}"))
    out += ["-" * W,
            row("Subtotal", f"{txn.subtotal:,.2f}"),
            row("Discount", f"-{txn.discount_amount:,.2f}"),
            f"  ({txn.discount_name})"[:W],
            row("VAT (12%) included", f"{txn.vat:,.2f}"),
            row("TOTAL (PHP)", f"{txn.total:,.2f}"),
            row("Payment", f"{txn.payment:,.2f}"),
            row("Change", f"{txn.change:,.2f}"),
            "=" * W, "Thank you for shopping!".center(W)]
    return "\n".join(out)


class ReceiptStore:
    """Saves each receipt as receipts/TXN-YYYYMMDD-0001.txt"""

    def __init__(self, folder):
        self._folder = Path(folder)

    def save(self, transaction_id: str, text: str) -> Path:
        path = self._folder / f"{transaction_id}.txt"
        try:
            self._folder.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            raise StorageError(f"Could not save receipt file {path.name}: {e}") from e
        return path

