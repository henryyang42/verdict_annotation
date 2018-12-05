from django.urls import path

from . import views

urlpatterns = [
    path('', views.editor, name='editor'),
    path('list', views.list_annotation, name='list'),
]
