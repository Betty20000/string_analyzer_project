from django.urls import path
from . import views

urlpatterns = [
    path('strings/filter-by-natural-language', views.natural_language_filter, name='natural_language_filter'),
    path('strings', views.strings, name='strings'),  # GET + POST
    path('strings/', views.strings, name='strings'), 
    path('strings/<str:string_value>', views.string_detail, name='string_detail'),  # GET + DELETE
    
]
