from django.core.paginator import Paginator

NUMBER_OF_ELEMENTS = 10


def get_paginator(queryet, request):
    paginator = Paginator(queryet, NUMBER_OF_ELEMENTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
