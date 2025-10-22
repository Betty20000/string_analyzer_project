from django.urls import path
from . import views

urlpatterns = [
    path('strings', views.create_string), 
    path('strings/', views.list_strings, name='list_strings'),                     # POST /strings
    
    path('strings/filter-by-natural-language', views.natural_language_filter),                       # GET /strings/
    path('strings/<str:string_value>', views.get_string),       # GET /strings/{value}
    path('strings/<str:string_value>/', views.delete_string),   # DELETE /strings/{value}/
]
