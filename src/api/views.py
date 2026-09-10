from django.shortcuts import render

from src.services.search import SearchService


def search(request):
    return render(request, "search.html")


def search_results(request):
    hits = SearchService().search(request.GET.get("q", ""))
    return render(request, "partials/search_results.html", {"hits": hits})
