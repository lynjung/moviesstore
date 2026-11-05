from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.db.models import Case, IntegerField, Value, When
from django.views.decorators.http import require_POST, require_http_methods

class ReviewForm(forms.Form):
    comment = forms.CharField(max_length=255, widget=forms.Textarea(attrs={"class": "form-control"}))

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    catalog_order = [
        'Inception', 'Avatar', 'The Dark Knight', 'Titanic',
        'Interstellar', 'La La Land', '20th Century Girl', 'Baby Driver',
    ]
    movies = movies.order_by(
        Case(
            *[When(name=name, then=Value(position))
              for position, name in enumerate(catalog_order)],
            default=Value(len(catalog_order)),
            output_field=IntegerField(),
        ),
        'id',
    )
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html',
                  {'template_data': template_data})

def show(request, id):
    movie = get_object_or_404(Movie, id=id)
    reviews = Review.objects.filter(movie=movie, reported=False).select_related("user")
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    return render(request, 'movies/show.html',
                  {'template_data': template_data})

@login_required
@require_POST
def create_review(request, id):
    movie = get_object_or_404(Movie, id=id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.create(comment=form.cleaned_data['comment'], movie=movie, user=request.user)
    else:
        messages.error(request, 'Please enter a review between 1 and 255 characters.')
    return redirect('movies.show', id=id)

@login_required
@require_http_methods(['GET', 'POST'])
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, movie_id=id, user=request.user)
    form = ReviewForm(request.POST if request.method == 'POST' else None,
                      initial={'comment': review.comment})
    if request.method == 'POST' and form.is_valid():
        review.comment = form.cleaned_data['comment']
        review.save(update_fields=['comment'])
        return redirect('movies.show', id=id)
    return render(request, 'movies/edit_review.html', {'template_data': {
        'title': 'Edit Review', 'review': review, 'form': form}})

@login_required
@require_POST
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, movie_id=id,
        user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

@login_required
@require_POST
def report_review(request, id, review_id):
    review = get_object_or_404(
        Review,
        id=review_id,
        movie_id=id
    )

    if request.method == 'POST':
        review.reported = True
        review.save()

    return redirect('movies.show', id=id)