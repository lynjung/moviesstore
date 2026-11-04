from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from movies.models import Movie
from .utils import calculate_cart_total
from .models import Order, Item


def get_cart(request):
    raw = request.session.get('cart', {})
    cart = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            try:
                movie_id, quantity = int(key), int(value)
            except (TypeError, ValueError):
                continue
            if movie_id > 0 and 1 <= quantity <= 10:
                cart[str(movie_id)] = quantity
    movies = list(Movie.objects.filter(id__in=cart))
    cart = {str(movie.id): cart[str(movie.id)] for movie in movies}
    request.session['cart'] = cart
    return cart, movies


def index(request):
    cart, movies = get_cart(request)
    return render(request, 'cart/index.html', {'template_data': {
        'title': 'Cart', 'movies_in_cart': movies,
        'cart_total': calculate_cart_total(cart, movies)}})


@require_POST
def add(request, id):
    get_object_or_404(Movie, id=id)
    try:
        quantity = int(request.POST.get('quantity', ''))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('Quantity must be a whole number between 1 and 10.')
    if not 1 <= quantity <= 10:
        return HttpResponseBadRequest('Quantity must be between 1 and 10.')
    cart, _ = get_cart(request)
    cart[str(id)] = quantity
    request.session['cart'] = cart
    return redirect('cart.index')


@require_POST
def clear(request):
    request.session['cart'] = {}
    return redirect('cart.index')


@login_required
@require_POST
def purchase(request):
    cart, movies = get_cart(request)
    if not movies:
        return redirect('cart.index')
    with transaction.atomic():
        order = Order.objects.create(user=request.user, total=calculate_cart_total(cart, movies))
        for movie in movies:
            Item.objects.create(movie=movie, price=movie.price, order=order,
                                quantity=cart[str(movie.id)])
    request.session['cart'] = {}
    return render(request, 'cart/purchase.html', {'template_data': {
        'title': 'Purchase confirmation', 'order_id': order.id}})
