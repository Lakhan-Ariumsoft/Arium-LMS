from django.urls import path
from . import views
# from .views import ZoomMeetingCRUD
from .views import ZoomMeetingView


urlpatterns = [
    path('zoom/webhook/', views.zoom_webhook, name='zoom_webhook'),
    path('meetings/', ZoomMeetingView.as_view(), name='list_create_meeting'),
    path('meetings/<int:meeting_id>/', ZoomMeetingView.as_view(), name='retrieve_update_delete_meeting'),

]

