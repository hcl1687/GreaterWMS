from django.urls import path, re_path
from . import views

urlpatterns = [
path(r'', views.APIViewSet.as_view({"get": "list", "post": "create"}), name="shopsku"),
path(r'file/', views.FileDownloadView.as_view({"get": "list"}), name="shopskufiledownload"),
re_path(r'^(?P<pk>\d+)/$', views.APIViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
}), name="shopsku"),
path(r'sync/', views.SyncViewSet.as_view({"get": "list", "post": "create"}), name="shopskusync"),
path(r'task/', views.TaskViewSet.as_view({"get": "list"}), name="shopskutask"),
]
