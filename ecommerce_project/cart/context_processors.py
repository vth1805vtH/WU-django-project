from . import utils


def cart_info(request):
    return {
        'cart_total_items': utils.get_total_items(request),
    }
