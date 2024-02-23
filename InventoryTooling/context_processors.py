#   tampilkan notifikasi ex. navbar.html
from .models import ModelLocation, ModelTempPickCart, ModelTempProdLoc
from django.db.models import Q, Sum, Count, Case, When, Min, Max, F


def notifications(request):
    # Your logic to fetch notifications goes here
    # For example, you can fetch notifications from a database model
    # and pass them to the template context.

    if request.user.is_authenticated:
        pending_cart = ModelTempPickCart.objects.filter(prod_code__isnull=False).count()
        text_pending = 'There are parts pending in your cart!'

        duplicate = ModelTempProdLoc.objects.values('prod_code').annotate(total_prod_code=Count('prod_code'),
                                                                          my_sum=Sum('qty')).filter(
            total_prod_code__gt=1, prod_code__is_active=True)
        duplicate_code = [item['prod_code'] for item in duplicate]
        letdown = ModelTempProdLoc.objects.filter(prod_code__in=duplicate_code, no_loc__assign="P",
                                                             qty__lte=F('prod_code__stock_min')).count()

        text_letdown = 'Check needed for replenishing parts. Please review and take necessary action.'
        # response_text = f'{cart_pending} {text2}'
        #return {'notifications': response_text}
        context1 = {'count_pending': pending_cart}
        context2 = {'msg_pending': text_pending}
        context3 = {'count_letdown': letdown}
        context4 = {'msg_letdown': text_letdown}

        combined_context = {**context1, **context2, **context3, **context4}
        return combined_context
    else:
        context1 = {'count_pending': None}
        context2 = {'msg_pending': None}
        context3 = {'count_letdown': None}
        context4 = {'msg_letdown': None}

        combined_context = {**context1, **context2, **context3, **context4}
        return combined_context
    # return {'notifications': 0}
    # return get_notifications(request)
