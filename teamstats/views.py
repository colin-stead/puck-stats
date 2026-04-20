from django.shortcuts import HttpResponse

def index(request):
    return HttpResponse('Team Stats')
