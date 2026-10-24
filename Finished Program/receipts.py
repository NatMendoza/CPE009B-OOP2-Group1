import re
from decimal import Decimal
from pathlib import Path

from config import RECEIPT_WIDTH, STORE_ADDRESS, STORE_NAME
from errors import StorageError, ValidationError
from transaction import Transaction

# transaction numbers look like TXN-20261023-0001
_ID_PATTERN = re.compile(r"^TXN-\d{8}-\d{4,}$")


def build_receipt(txn: Transaction) -> str:
    # short name for the receipt width
    W = RECEIPT_WIDTH
    zero = Decimal("0.00")

    # one line with the label on the left and the value on the right
    def row(label, value):
        return str(label)[:W - 14].ljust(W - 14) + f"{value:>14}"

    discount = txn.discount_amount
    out = [STORE_NAME.center(W), STORE_ADDRESS.center(W), "=" * W,
           f"Transaction No: {txn.transaction_id}",
           f"Date/Time: {txn.completed_at:%Y-%m-%d %H:%M:%S}",
           f"Cashier: {txn.cashier}",
           f"Customer: {txn.customer_type.replace('_', ' ').title()}", "-" * W]
    # each item takes two lines, the name then the qty x price and total
    for l in txn.lines:
        out.append(l.name[:W])
        out.append(row(f"  {l.quantity} x {l.unit_price:,.2f}", f"{l.line_total:,.2f}"))
    out += ["-" * W, row("Subtotal", f"{txn.subtotal:,.2f}")]
    # only show the minus sign when there is really a discount
    if discount > zero:
        out.append(row("Discount", f"-{discount:,.2f}"))
        out.append(f"  ({txn.discount_name})"[:W])
    else:
        out.append(row("Discount", "0.00"))
    out += [row("VAT (12%) included", f"{txn.vat:,.2f}"),
            row("TOTAL (PHP)", f"{txn.total:,.2f}"),
            row("Payment", f"{txn.payment:,.2f}"),
            row("Change", f"{txn.change:,.2f}"),
            "=" * W, "Thank you for shopping!".center(W)]
    return "\n".join(out)


class ReceiptStore:
    # Saves each receipt as receipts/TXN-YYYYMMDD-0001.txt

    def __init__(self, folder):
        self._folder = Path(folder)

    def _path(self, transaction_id: str) -> Path:
        tid = str(transaction_id).strip().upper()
        if not _ID_PATTERN.match(tid):          # also blocks '../' tricks
            raise ValidationError(f"Invalid transaction number: {transaction_id!r}.")
        return self._folder / f"{tid}.txt"

    def save(self, transaction_id: str, text: str) -> Path:
        path = self._path(transaction_id)
        try:
            self._folder.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            raise StorageError(f"Could not save receipt file {path.name}: {e}") from e
        return path

    def read(self, transaction_id: str) -> str:
        path = self._path(transaction_id)
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            raise StorageError(f"Could not read receipt file {path.name}: {e}") from e