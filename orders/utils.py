from django.utils import timezone


def restore_stock_for_order(order, new_status, skip_statuses=None):
    """
    Restores stock for all items in an order that aren't already
    in a terminal status (cancelled/returned).
    Prevents double-restoring stock.
    """
    if skip_statuses is None:
        skip_statuses = ['cancelled', 'returned']

    for item in order.items.all():
        if item.status not in skip_statuses:
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock'])
            item.status = new_status
            item.save()


def cancel_order(order, reason=''):
    """
    Cancels an order, saves reason and timestamp,
    restores stock for all non-cancelled items.
    """
    order.status = 'cancelled'
    order.cancellation_reason = reason
    order.cancelled_at = timezone.now()
    order.save()
    restore_stock_for_order(order, new_status='cancelled')


def return_order(order, reason):
    """
    Marks an order as returned, saves reason and timestamp,
    restores stock for all non-returned/cancelled items.
    """
    order.status = 'returned'
    order.return_reason = reason
    order.returned_at = timezone.now()
    order.save()
    restore_stock_for_order(order, new_status='returned')