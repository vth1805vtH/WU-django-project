from .models import Wishlist


def wishlist_info(request):
    count = 0
    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        count = wishlist.total_items
    return {'wishlist_total_items': count}
