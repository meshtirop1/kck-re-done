from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Page, News, Testimonial

def community_index(request):
    return render(request, 'community/index.html')

def community_history(request):
    return render(request, 'community/history.html')

def community_location(request):
    return render(request, 'community/location.html')

def community_hours(request):
    return render(request, 'community/hours.html')

def community_mission(request):
    return render(request, 'community/mission.html')

def community_vision(request):
    return render(request, 'community/vision.html')

def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, active=True)
    return render(request, 'community/page_detail.html', {'page': page})

def news_list(request):
    news = News.objects.filter(published=True)
    paginator = Paginator(news, 9)
    page = request.GET.get('page', 1)
    news_page = paginator.get_page(page)
    return render(request, 'community/news_list.html', {'news': news_page})

def news_detail(request, slug):
    article = get_object_or_404(News, slug=slug, published=True)
    related = News.objects.filter(published=True).exclude(id=article.id)[:3]
    return render(request, 'community/news_detail.html', {'article': article, 'related': related})

def testimonials(request):
    testimonials = Testimonial.objects.filter(active=True)
    return render(request, 'community/testimonials.html', {'testimonials': testimonials})
