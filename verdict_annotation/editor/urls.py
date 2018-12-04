from django.urls import path

from . import views

urlpatterns = [
    path('', views.editor, name='editor'),
    path('agent/export', views.export, name='export'),
    path('list', views.list_rs, name='list'),
    path('delete', views.delete, name='delete'),
    path('agent', views.update_agent, name='agent'),
    path('list_agent', views.list_agent, name='list_agent'),
    path('agent/delete', views.delete_agent, name='delete_agent'),
    path('agent/publish', views.publish, name='publish'),
]
