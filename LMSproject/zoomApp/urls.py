from django.urls import path
from . import views
# from .views import ZoomMeetingCRUD
from .views import RecordingsView ,GetValidRecordingUrl , UploadRecordingView


urlpatterns = [
    path('zoom/webhook/', views.zoom_webhook, name='zoom_webhook'),
    path('recordings/', RecordingsView.as_view(), name='list_create_meeting'),
    path('recordings/<int:pk>/', RecordingsView.as_view(), name='retrieve_update_delete_meeting'),
    path('GetValidRecordingUrl/<int:pk>/', GetValidRecordingUrl.as_view(), name='signedUrl'),
    path("uploadRecording/", UploadRecordingView.as_view(), name="upload-recording"),
]

