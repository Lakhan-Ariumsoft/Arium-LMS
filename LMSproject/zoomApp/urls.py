from django.urls import path
from . import views
# from .views import ZoomMeetingCRUD
from .views import ZoomMeetingListCreateAPIView , ZoomMeetingDetailAPIView


urlpatterns = [
    path('zoom/webhook/', views.zoom_webhook, name='zoom_webhook'),
    path('meetings/', ZoomMeetingListCreateAPIView.as_view(), name='list_create_meeting'),
    path('meetings/<int:pk>/', ZoomMeetingDetailAPIView.as_view(), name='retrieve_update_delete_meeting'),

]

