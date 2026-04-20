from django.shortcuts import HttpResponse

def index(request):
    return HttpResponse('Hi')

# Create your views here.
