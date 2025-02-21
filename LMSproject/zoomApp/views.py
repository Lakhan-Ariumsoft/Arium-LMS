import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from google.cloud import storage
from datetime import datetime
import hmac
import hashlib
import tempfile

import base64
from datetime import datetime
from google.cloud import storage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import time

from django.http import JsonResponse
from django.core.paginator import Paginator
from rest_framework import status
from datetime import datetime
from django.db.models import Q
from django.core.paginator import Paginator

from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime
from rest_framework import status

from zoomApp.models import Recordings  # Import the ZoomMeeting model
from courses.models import Courses  # Import the Courses model
from django.db import IntegrityError


from django.http import JsonResponse
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Recordings
from courses.models import Courses
from .serializers import RecordingsSerializer

load_dotenv()
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
GCP_CREDENTIALS = os.getenv("GCP_CREDENTIALS")
ZOOM_SECRET_TOKEN='yFoUWja9QpuLqSjFdSZjIQ'
ZOOM_OAUTH_URL = "https://zoom.us/oauth/token"
ZOOM_RECORDINGS_URL = "https://api.zoom.us/v2/users/me/recordings"
ZOOM_DELETE_RECORDINGS_URL = "https://api.zoom.us/v2/meetings"


# def get_access_token():
#     """
#     Generate an OAuth access token using the client credentials.
#     """
#     payload = {
#         "grant_type": "account_credentials",
#         "account_id": ZOOM_ACCOUNT_ID
#     }
#     response = requests.post(
#         ZOOM_OAUTH_URL,
#         params=payload,
#         auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
#     )
#     response.raise_for_status()
#     return response.json()["access_token"]


def get_access_token(client_id, client_secret, account_id):
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"
    auth_header = f"{client_id}:{client_secret}".encode("utf-8")
    headers = {
        "Authorization": f"Basic {base64.b64encode(auth_header).decode('utf-8')}"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Failed to generate access token.")
        return None


def get_recording_details(access_token, meeting_id):
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch recording details. Status code: {response.status_code}")
        return None

def download_recording(recording_url, save_path, file_name, access_token):
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    full_file_path = os.path.join(save_path, file_name)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(recording_url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(full_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded {file_name} to {save_path}")
    else:
        print(f"Failed to download {file_name}. Status code: {response.status_code}")
    return full_file_path


# def upload_to_gcp(local_file_path, bucket_name, gcp_credentials_path):
#     try:
#         # Set the environment variable for authentication
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_credentials_path

#         # Initialize the GCS client
#         client = storage.Client()

#         # Access the GCP bucket
#         bucket = client.bucket(bucket_name)

#         # Create a blob (object) in the bucket for the file
#         blob_name = os.path.basename(local_file_path)
#         blob = bucket.blob(blob_name)

#         # Upload the local file to the GCP bucket
#         blob.upload_from_filename(local_file_path, content_type="video/mp4")
#         print(f"Uploaded {blob_name} to GCP bucket {bucket_name} successfully.")

#     except Exception as e:
#         print(f"Error uploading file to GCP: {e}")


def get_cloud_recordings(access_token, from_date):
    """
    Retrieve cloud recordings starting from a specific date.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"from": from_date}
    response = requests.get(ZOOM_RECORDINGS_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["meetings"]


def delete_cloud_recording(access_token, meeting_id):
    """
    Delete a cloud recording for a specific meeting ID.
    """
    url = f"{ZOOM_DELETE_RECORDINGS_URL}/{meeting_id}/recordings"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"Recording for meeting ID {meeting_id} deleted successfully.")
    else:
        print(f"Failed to delete recording for meeting ID {meeting_id}: {response.text}")

def delete_old_recordings():
    """
    Delete recordings older than 7 days and return a list of deleted recordings.
    """
    try:
        print("::::::::::   Delete 001 OLD Recordings :::::::")
        # Get today's date and calculate the date 7 days ago
        import datetime
        today = datetime.date.today()
        seven_days_ago = today - datetime.timedelta(days=7)
        seven_days_ago_str = seven_days_ago.strftime("%Y-%m-%d")

        # Get access token
        access_token = get_access_token(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID)

        # Get all recordings from the past month (Zoom API requires "from" date)
        recordings = get_cloud_recordings(access_token, seven_days_ago_str)

        # Check if there are recordings
        if not recordings:
            print("No recordings found to delete.")
            return

        deleted_recordings = []

        # Filter and delete recordings older than 7 days
        for recording in recordings:
            recording_date = datetime.datetime.strptime(recording["start_time"], "%Y-%m-%dT%H:%M:%SZ").date()
            if recording_date <= seven_days_ago:
                meeting_id = recording["id"]
                if delete_cloud_recording(access_token, meeting_id):
                    print("\nDeleted Recordings:")
                else:
                    print("No recordings were found that are older than 7 days to delete.")

                    # deleted_recordings.append({
                    #     "id": meeting_id,
                    #     "topic": recording.get("topic"),
                    #     "start_time": recording.get("start_time")
                    # })

        # Print results
        # if deleted_recordings:
            # print("\nDeleted Recordings:")
            # for rec in deleted_recordings:
            #     print(f"ID: {rec['id']}, Topic: {rec['topic']}, Start Time: {rec['start_time']}")
       
    except Exception as e:
        print(f"An error occurred: {e}")


@csrf_exempt
def zoom_webhook(request):
    """Handle Zoom webhooks and validation."""
    if request.method == "POST":
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body.decode("utf-8"))
            print(data)  # For debugging, you can remove this once it's working
            
            # Handle the URL validation event (this is the first step Zoom performs)
            if data.get("event") == "endpoint.url_validation":
                plain_token = data.get("payload", {}).get("plainToken")
                if plain_token:
                    # Generate encrypted token as Zoom requires
                    secret_token = ZOOM_SECRET_TOKEN.encode("utf-8")
                    mess = plain_token.encode("utf-8")
                    has = hmac.new(secret_token, mess, hashlib.sha256).digest()
                    hex_message = has.hex()

                    # Send back the plainToken and encryptedToken
                    response = JsonResponse({
                        "plainToken": plain_token,
                        "encryptedToken": hex_message,
                    })
                    response['Content-Type'] = 'application/json'  # Explicitly set Content-Type
                    print("Validation Response:", response.content)
                    return response
                else:
                    return JsonResponse({"error": "No plainToken found"}, status=400)

            # Handle other events (like recording.completed)
            if data.get("event") == "recording.completed":
                recording = data.get("payload", {}).get("object", {})
                # print("::::::::::             :::::::::::      RECORDINGS       :::::::::::::",recording)
                meeting_id = recording.get("id", "None")

                _ = helperFunction(meeting_id)

                print("DELETE RECORDINGS :::::            ::::")
                delete_old_recordings()


            return JsonResponse({"message": "Webhook received successfully."})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": "Invalid data"}, status=400)

    return JsonResponse({"error": "Invalid method"}, status=400)



def helperFunction(meeting_id):
    """Process and upload recordings for a given meeting ID."""
    try:
        # Get Zoom access token
        access_token = get_access_token(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID)
        if not access_token:
            raise Exception("Failed to retrieve access token from Zoom")

        # Get meeting recording details
        details = get_recording_details(access_token, meeting_id)
        if not details:
            raise Exception(f"Failed to retrieve recording details for meeting {meeting_id}")

        recordings = details.get("recording_files", [])
        meeting_topic = details.get("topic", "Unknown_Meeting").replace("/", "_").replace(":", "_")
        meeting_folder = f"{meeting_topic}_{meeting_id}"  # Folder name: Meeting title + Meeting ID

        # Extract the course name from the meeting topic (assuming it's the first part before the first underscore)
        course_name = meeting_topic.split("_")[0]

        # Initialize Google Cloud Storage client
        storage_client = storage.Client.from_service_account_json(GCP_CREDENTIALS)
        bucket = storage_client.bucket(GCP_BUCKET_NAME)

        # Check if the folder exists
        folder_blob = bucket.blob(f"{meeting_folder}/")
        folder_exists = folder_blob.exists()

        if not folder_exists:
            # Create the folder if it doesn't exist
            folder_blob.upload_from_string("", content_type="application/x-www-form-urlencoded")
            print(f"Folder '{meeting_folder}' created in bucket '{GCP_BUCKET_NAME}'.")

        # Process each recording
        for recording in recordings:
            if recording.get("file_type") == "MP4":
                file_url = recording["download_url"]
                playURL = recording['play_url']
                recording_id = recording["id"]
                start_time = recording.get("recording_start", "unknown_start").replace(":", "_").replace("T", "_")
                file_name = f"{meeting_topic}_{recording_id}_{start_time}.mp4"
                file_path = f"{meeting_folder}/{file_name}"  # Path in the bucket

                # Check if the file already exists and is uploaded
                blob = bucket.blob(file_path)
                if blob.exists() and blob.metadata and blob.metadata.get("status") == "uploaded":
                    print(f"File '{file_name}' already uploaded successfully. Skipping upload.")
                    continue

                try:
                    # Download the recording file
                    headers = {"Authorization": f"Bearer {access_token}"}
                    response = requests.get(file_url, headers=headers, stream=True, timeout=60)

                    if response.status_code == 200:
                        print(f"Uploading '{file_name}' to GCP...")

                        # Upload to GCP
                        blob.metadata = {"status": "uploading", "meeting_id": meeting_id}
                        blob.chunk_size = 26214400  # 25MB chunk size
                        blob.upload_from_file(
                            response.raw,
                            content_type="video/mp4"
                        )
                        print(f"Recording '{file_name}' uploaded successfully to GCP.")

                        # Update metadata to mark upload as complete
                        blob.metadata = {"status": "uploaded", "meeting_id": meeting_id}
                        blob.patch()

                        # Save Zoom meeting details to the database
                        try:
                            # Find the course based on the course name
                            course = Courses.objects.filter(courseName=course_name).first()
                            # Create a new recording entry
                            recording = Recordings.objects.create(
                                title=meeting_topic,
                                meeting_id=meeting_id,
                                duration=recording.get("duration", 0),  # Assuming duration is available
                                recording_url=playURL
                            )

                            # If a course is found, associate it with the recording
                            if course:
                                recording.course.add(course)  # Correct way to set ManyToManyField
                                course.videosCount = course.videosCount + 1  # Increment videoCount
                                course.save(update_fields=["videosCount"])

                            print(f"Recording '{meeting_topic}' added to database.")
                        except IntegrityError as e:
                            print(f"Integrity error while saving Recording: {e}")
                    else:
                        raise Exception(f"Failed to download file from Zoom. Status Code: {response.status_code}")
                except Exception as e:
                    print(f"Error uploading file '{file_name}': {e}")
    except Exception as e:
        print(f"Critical error in upload_recordings for meeting ID '{meeting_id}': {e}")


from django.shortcuts import get_object_or_404
from django.db.models import F
from django.db.models import ManyToManyField
from users.permissions import IsModeratorOrInstructor 
from rest_framework.permissions import IsAuthenticated



class RecordingsView(APIView):

    permission_classes = [IsAuthenticated, IsModeratorOrInstructor] 

    
    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")  # Check if 'pk' is provided in the URL

        if pk:
            # Fetch a single Recording instance by pk if it exists
            try:
                recording = Recordings.objects.get(pk=pk)
                serializer = RecordingsSerializer(recording)

                # Return in the same format as list response
                return JsonResponse({
                    "status": True,
                    "message": "Recording fetched successfully.",
                    "data": serializer.data,
                    "total": 1,  # Single recording, so total = 1
                    "limit": 1,  # Limit is 1 for a single item
                    "page": 1,   # Only one page when fetching one item
                    "pages": 1   # One page in this case
                }, status=status.HTTP_200_OK)
            except Recordings.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Recording not found.",
                    "data": [],
                    "total": 0,
                    "limit": 1,
                    "page": 1,
                    "pages": 1
                }, status=status.HTTP_404_NOT_FOUND)

        # If no pk, continue with the filtering logic
        unassigned_videos = request.GET.get('specialClasses', None)
        dateRange = request.GET.get('dateRange', None)
        searchCourse = request.GET.get('searchCourse', None)
        search_text = request.GET.get('searchText', None)
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))

        queryset = Recordings.objects.all()

        # Filter for recordings with no assigned course (i.e., course is null or empty)
        if unassigned_videos:
            queryset = queryset.filter(course__isnull=True)

        # Filter for recordings associated with a specific course by ID
        if searchCourse:
            try:
                course_id = int(searchCourse)
                queryset = queryset.filter(course__id=course_id)
            except ValueError:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid course ID format.",
                    "data": [],
                    "total": 0,
                    "limit": limit,
                    "page": page,
                    "pages": 1
                }, status=status.HTTP_400_BAD_REQUEST)

        # Multi-field search for title, course name, duration, and created_at
        if search_text:
            queryset = queryset.filter(
                Q(title__icontains=search_text) |
                # Q(course__name__icontains=search_text) |
                Q(duration__icontains=search_text) |
                Q(created_at__icontains=search_text)
            )

        # Filter recordings by date range
        if dateRange:
            try:
                start_date_str, end_date_str = dateRange.split(":")
                start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)

                queryset = queryset.filter(updated_at__range=(start_date, end_date))
            except ValueError:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid date range format. Use 'YYYY-MM-DD:YYYY-MM-DD'."
                }, status=status.HTTP_400_BAD_REQUEST)

        paginator = Paginator(queryset, limit)
        paged_data = paginator.get_page(page)

        if not paged_data:
            return JsonResponse({
                "status": False,
                "message": "No search data found.",
                "data": [],
                "total": 0,
                "limit": limit,
                "page": page,
                "pages": 1
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = RecordingsSerializer(paged_data, many=True)

        # Return the paginated results with course name list and id list
        return JsonResponse({
            "status": True,
            "message": "Recordings fetched successfully.",
            "data": serializer.data,
            "total": paginator.count,
            "limit": limit,
            "page": page,
            "pages": paginator.num_pages
        }, status=status.HTTP_200_OK)

    
    def post(self, request):
        try:
            # Get the list of course IDs from the request data
            course_ids = request.data.get('addRecordingList', [])
            
            # Pass the course IDs along with other data to the serializer
            serializer = RecordingsSerializer(data=request.data)
            
            if serializer.is_valid():
                # Save the recording, which will also assign courses through `create` method
                recording = serializer.save(addRecordingList=course_ids)
                
                # Prepare the response data to include course names and IDs
                courses = recording.course.all()  # Get all related courses
                course_data = [{"id": course.id, "courseName": course.courseName} for course in courses]
                
                return Response({
                    "status": True,
                    "message": "Recording created successfully.",
                    "data": serializer.data,
                    "courses": course_data  # Include course data (ID + name)
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "status": False,
                "message": "Invalid data.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except ValueError as ve:
            return Response({
                "status": False,
                "message": "Value error occurred.",
                "error": str(ve)
            }, status=status.HTTP_400_BAD_REQUEST)

        except TypeError as te:
            return Response({
                "status": False,
                "message": "Type error occurred.",
                "error": str(te)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": "An unexpected error occurred.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def put(self, request, *args, **kwargs):
        pk = kwargs.get("pk")  # Get 'pk' from kwargs
        recording = get_object_or_404(Recordings, pk=pk)

        # Extract fields to update (only those present in request)
        update_fields = {}
        if "meeting_id" in request.data:
            update_fields["meeting_id"] = request.data["meeting_id"]
        if "title" in request.data:
            update_fields["title"] = request.data["title"]
        if "recording_url" in request.data:
            update_fields["recording_url"] = request.data["recording_url"]
        if "duration" in request.data:
            update_fields["duration"] = request.data["duration"]

        # Apply partial updates only if fields are provided
        for field, value in update_fields.items():
            setattr(recording, field, value)

        # Handle courses
        add_course_ids = set(request.data.get("addRecordingList", []))  # Courses to add
        remove_course_ids = set(request.data.get("removeRecordingList", []))  # Courses to remove

        # Add new courses without removing existing ones
        if add_course_ids:
            existing_course_ids = set(recording.course.values_list("id", flat=True))
            new_courses_to_add = Courses.objects.filter(id__in=add_course_ids - existing_course_ids)

            recording.course.add(*new_courses_to_add)  # Add only new courses

            # Update video counts for added courses
            for course in new_courses_to_add:
                course.videosCount += 1
                course.save()

        # Remove courses as per the remove list
        if remove_course_ids:
            courses_to_remove = recording.course.filter(id__in=remove_course_ids)

            recording.course.remove(*courses_to_remove)  # Remove courses

            # Update video counts for removed courses
            for course in courses_to_remove:
                course.videosCount = max(0, course.videosCount - 1)
                course.save()

        # Save the recording only if any field was updated
        if update_fields or add_course_ids or remove_course_ids:
            recording.save()

        # Return response with updated course list
        return Response({
            "status": True,
            "message": "Recording updated successfully.",
            "updated_fields": update_fields,
            "updated_courses": list(recording.course.values_list("id", flat=True))  # Return updated course IDs
        }, status=status.HTTP_200_OK)



   
    
    def delete(self, request, pk):
        try:
            recording = Recordings.objects.get(id=pk)
            
            # Check if the recording is assigned to a course
            if recording.course.exists():  # This checks if there is any course related to the recording
                # Get the first related course (assuming only one course is related, adjust as needed)
                course = recording.course.first()

                # Update the videosCount field of the course
                if course:
                    course.videosCount -= 1
                    course.save()
            
            # Delete the recording
            recording.delete()

            return Response({"status": True, "message": "Recording deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
        except Recordings.DoesNotExist:
            return Response({"status": False, "message": "Recording not found."}, status=status.HTTP_404_NOT_FOUND)


# from django.http import JsonResponse
# from django.views import View
# from django.shortcuts import get_object_or_404
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
# from django.core.exceptions import PermissionDenied
# from .models import ZoomMeeting
# from courses.models import Courses  # Ensure this is imported correctly
# from django.views.decorators.csrf import csrf_exempt
# import json

# from users.decorators import role_required 

# # Decorator to check role
# def role_required(roles):
#     def decorator(view_func):
#         def _wrapped_view(request, *args, **kwargs):
#             if not request.user.is_authenticated:
#                 return JsonResponse({'error': 'Authentication required'}, status=401)
#             if request.user.role not in roles:
#                 raise PermissionDenied("You do not have permission to perform this action.")
#             return view_func(request, *args, **kwargs)
#         return _wrapped_view
#     return decorator


# @method_decorator([login_required, role_required(['moderator', 'instructor'])], name='dispatch')
# @method_decorator(csrf_exempt, name='dispatch')  # To allow POST, PUT, and DELETE without CSRF token
# class ZoomMeetingView(View):
#     def get(self, request, meeting_id=None):
#         """
#         Retrieve a specific Zoom meeting or list all meetings.
#         """
#         if request.user.role == 'Student':
#             return JsonResponse({"detail": "Permission Denied"}, status=403)

#         if meeting_id:
#             meeting = get_object_or_404(ZoomMeeting, id=meeting_id)
#             data = {
#                 "id": meeting.id,
#                 "course": meeting.course.title if meeting.course else None,
#                 "title": meeting.title,
#                 "meeting_id": meeting.meeting_id,
#                 "duration": meeting.duration,
#                 "recording_url": meeting.recording_url,
#                 "created_at": meeting.created_at,
#                 "updated_at": meeting.updated_at,
#             }
#             return JsonResponse(data, status=200)
#         else:
#             meetings = ZoomMeeting.objects.all()
#             data = [
#                 {
#                     "id": meeting.id,
#                     "course": meeting.course.title if meeting.course else None,
#                     "title": meeting.title,
#                     "meeting_id": meeting.meeting_id,
#                     "duration": meeting.duration,
#                     "recording_url": meeting.recording_url,
#                     "created_at": meeting.created_at,
#                     "updated_at": meeting.updated_at,
#                 }
#                 for meeting in meetings
#             ]
#             return JsonResponse(data, safe=False, status=200)

#     def post(self, request):
#         """
#         Create a new Zoom meeting.
#         """
#         try:
            
#             if request.user.role == 'student':
#                 return JsonResponse({"detail": "Permission Denied"}, status=403)
        
#             data = json.loads(request.body)
#             course_id = data.get('course')
#             course = Courses.objects.get(id=course_id) if course_id else None

#             meeting = ZoomMeeting.objects.create(
#                 course=course,
#                 title=data['title'],
#                 meeting_id=data['meeting_id'],
#                 duration=data['duration'],
#                 recording_url=data['recording_url'],
#             )
#             return JsonResponse({"message": "Zoom meeting created successfully", "id": meeting.id}, status=201)
#         except Courses.DoesNotExist:
#             return JsonResponse({"error": "Course not found"}, status=404)
#         except KeyError as e:
#             return JsonResponse({"error": f"Missing field: {e}"}, status=400)

#     def put(self, request, pk):
#         """
#         Update an existing Zoom meeting.
#         """

#         if request.user.role == 'student':
#             return JsonResponse({"detail": "Permission Denied"}, status=403)
        
#         meeting = get_object_or_404(ZoomMeeting, id=pk)
#         try:
#             data = json.loads(request.body)
#             course_id = data.get('course')
#             course = Courses.objects.get(id=course_id) if course_id else None

#             meeting.course = course
#             meeting.title = data.get('title', meeting.title)
#             meeting.meeting_id = data.get('meeting_id', meeting.meeting_id)
#             meeting.duration = data.get('duration', meeting.duration)
#             meeting.recording_url = data.get('recording_url', meeting.recording_url)
#             meeting.save()

#             return JsonResponse({"message": "Zoom meeting updated successfully"}, status=200)
#         except Courses.DoesNotExist:
#             return JsonResponse({"error": "Course not found"}, status=404)
#         except KeyError as e:
#             return JsonResponse({"error": f"Missing field: {e}"}, status=400)

#     def delete(self, request, meeting_id):
#         """
#         Delete a Zoom meeting.
#         """

#         if request.user.role == 'student':
#             return JsonResponse({"detail": "Permission Denied"}, status=403)
        
#         meeting = get_object_or_404(ZoomMeeting, id=meeting_id)
#         meeting.delete()
#         return JsonResponse({"message": "Zoom meeting deleted successfully"}, status=200)



# ]]]]]]]]]]'']

# from django.http import JsonResponse
# from django.views import View
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from .models import ZoomMeeting
# from courses.models import Courses
# import json
# from users.permissions import is_moderator_or_instructor

# @method_decorator(csrf_exempt, name='dispatch')
# class ZoomMeetingCRUD(View):
#     """Handle all CRUD operations for ZoomMeeting model (Create, Retrieve, Update, Delete)."""
    
#     def dispatch(self, request, *args, **kwargs):
#         if not is_moderator_or_instructor(request.user):
#             return JsonResponse({'error': 'Access denied. Only moderators and instructors can perform this action.'}, status=403)
#         return super().dispatch(request, *args, **kwargs)
    
#     def get(self, request, meeting_id=None):
#         """Retrieve Zoom meeting details (single or all)."""
#         if meeting_id:
#             try:
#                 meeting = ZoomMeeting.objects.get(id=meeting_id)
#                 meeting_data = {
#                     "id": meeting.id,
#                     "title": meeting.title,
#                     "course": meeting.course.name if meeting.course else None,
#                     "meeting_id": meeting.meeting_id,
#                     "duration": meeting.duration,
#                     "recording_url": meeting.recording_url
#                 }
#                 return JsonResponse(meeting_data, status=200)
#             except ZoomMeeting.DoesNotExist:
#                 return JsonResponse({'error': 'Zoom meeting not found.'}, status=404)
#         else:
#             meetings = ZoomMeeting.objects.all()
#             meetings_data = [{"id": meeting.id, "title": meeting.title, "course": meeting.course.name if meeting.course else None} for meeting in meetings]
#             return JsonResponse(meetings_data, safe=False, status=200)
    
#     def post(self, request):
#         """Create a new Zoom meeting."""
#         try:
#             data = json.loads(request.body)
#             course_name = data.get('course_name')
#             course = Courses.objects.filter(name=course_name).first()

#             meeting = ZoomMeeting.objects.create(
#                 course=course,
#                 title=data.get('title'),
#                 meeting_id=data.get('meeting_id'),
#                 duration=data.get('duration', 0),
#                 recording_url=data.get('recording_url')
#             )
#             return JsonResponse({'message': 'Zoom meeting created', 'meeting_id': meeting.id}, status=201)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)

#     def put(self, request, meeting_id):
#         """Update an existing Zoom meeting."""
#         try:
#             meeting = ZoomMeeting.objects.get(id=meeting_id)
#             data = json.loads(request.body)

#             # Update the fields
#             meeting.title = data.get('title', meeting.title)
#             meeting.duration = data.get('duration', meeting.duration)
#             meeting.recording_url = data.get('recording_url', meeting.recording_url)

#             # If course is provided, update course association
#             course_name = data.get('course_name')
#             if course_name:
#                 course = Courses.objects.filter(name=course_name).first()
#                 meeting.course = course

#             meeting.save()
#             return JsonResponse({'message': 'Zoom meeting updated', 'meeting_id': meeting.id}, status=200)

#         except ZoomMeeting.DoesNotExist:
#             return JsonResponse({'error': 'Zoom meeting not found.'}, status=404)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)

#     def delete(self, request, meeting_id):
#         """Delete a Zoom meeting."""
#         try:
#             meeting = ZoomMeeting.objects.get(id=meeting_id)
#             meeting.delete()
#             return JsonResponse({'message': 'Zoom meeting deleted successfully'}, status=200)
#         except ZoomMeeting.DoesNotExist:
#             return JsonResponse({'error': 'Zoom meeting not found.'}, status=404)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)































































# from google.cloud import storage
# from datetime import datetime
# import requests

# def helperFunction(meeting_id):
#     """Process and upload recordings for a given meeting ID."""
#     try:
#         # Get Zoom access token
#         access_token = get_access_token(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID)
#         if not access_token:
#             raise Exception("Failed to retrieve access token from Zoom")

#         # Get meeting recording details
#         details = get_recording_details(access_token, meeting_id)
#         if not details:
#             raise Exception(f"Failed to retrieve recording details for meeting {meeting_id}")

#         recordings = details.get("recording_files", [])
#         meeting_topic = details.get("topic", "Unknown_Meeting").replace("/", "_").replace(":", "_")
#         meeting_folder = f"{meeting_topic}_{meeting_id}"  # Folder name: Meeting title + Meeting ID

#         # Initialize Google Cloud Storage client
#         storage_client = storage.Client.from_service_account_json(GCP_CREDENTIALS)
#         bucket = storage_client.bucket(GCP_BUCKET_NAME)

#         # Check if the folder exists
#         folder_blob = bucket.blob(f"{meeting_folder}/")
#         folder_exists = folder_blob.exists()

#         if not folder_exists:
#             # Create the folder if it doesn't exist
#             folder_blob.upload_from_string("", content_type="application/x-www-form-urlencoded")
#             print(f"Folder '{meeting_folder}' created in bucket '{GCP_BUCKET_NAME}'.")

#         # Process each recording
#         for recording in recordings:
#             if recording.get("file_type") == "MP4":
#                 file_url = recording["download_url"]
#                 recording_id = recording["id"]
#                 start_time = recording.get("recording_start", "unknown_start").replace(":", "_").replace("T", "_")
#                 file_name = f"{meeting_topic}_{recording_id}_{start_time}.mp4"
#                 file_path = f"{meeting_folder}/{file_name}"  # Path in the bucket

#                 # Check if the file already exists and is uploaded
#                 blob = bucket.blob(file_path)
#                 if blob.exists() and blob.metadata and blob.metadata.get("status") == "uploaded":
#                     print(f"File '{file_name}' already uploaded successfully. Skipping upload.")
#                     continue

#                 try:
#                     # Download the recording file
#                     headers = {"Authorization": f"Bearer {access_token}"}
#                     response = requests.get(file_url, headers=headers, stream=True, timeout=60)

#                     if response.status_code == 200:
#                         print(f"Uploading '{file_name}' to GCP...")

#                         # Upload to GCP
#                         blob.metadata = {"status": "uploading", "meeting_id": meeting_id}
#                         blob.chunk_size = 26214400  # 25MB chunk size
#                         blob.upload_from_file(
#                             response.raw,
#                             content_type="video/mp4"
#                         )
#                         print(f"Recording '{file_name}' uploaded successfully to GCP.")

#                         # Update metadata to mark upload as complete
#                         blob.metadata = {"status": "uploaded", "meeting_id": meeting_id}
#                         blob.patch()
#                     else:
#                         raise Exception(f"Failed to download file from Zoom. Status Code: {response.status_code}")
#                 except Exception as e:
#                     print(f"Error uploading file '{file_name}': {e}")
#     except Exception as e:
#         print(f"Critical error in upload_recordings for meeting ID '{meeting_id}': {e}")


# import time
# from datetime import datetime
# import requests
# from google.cloud import storage

# Constants for retry logic
# RETRY_BACKOFF_SECONDS = 10
# MAX_RETRIES = 5


# def helperFunction(meeting_id):
#     """Process and upload recordings for a given meeting ID."""
#     try:
#         # Get Zoom access token
#         access_token = get_access_token(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID)
#         if not access_token:
#             raise Exception("Failed to retrieve access token from Zoom")

#         # Get meeting recording details
#         details = get_recording_details(access_token, meeting_id)
#         if not details:
#             raise Exception(f"Failed to retrieve recording details for meeting {meeting_id}")

#         recordings = details.get("recording_files", [])
#         meeting_topic = details.get("topic", "Unknown_Meeting").replace("/", "_").replace(":", "_")
#         timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace(":", "_")

#         # Initialize Google Cloud Storage client
#         storage_client = storage.Client.from_service_account_json(GCP_CREDENTIALS)
#         bucket = storage_client.bucket(GCP_BUCKET_NAME)

#         # Process each recording
#         for recording in recordings:
#             if recording.get("file_type") == "MP4":
#                 file_url = recording["download_url"]
#                 file_name = f"{meeting_topic}_{recording['id']}.mp4"

#                 # Check if the file already exists and is uploaded
#                 blob = bucket.blob(file_name)
#                 if blob.exists() and blob.metadata and blob.metadata.get("status") == "uploaded":
#                     print(f"File '{file_name}' already uploaded successfully. Skipping upload.")
#                     continue

#                 try:
#                     # Download the recording file
#                     headers = {"Authorization": f"Bearer {access_token}"}
#                     response = requests.get(file_url, headers=headers, stream=True, timeout=60)

#                     if response.status_code == 200:
#                         print(f"Uploading '{file_name}' to GCP...")

#                         # Upload to GCP
#                         blob.metadata = {"status": "uploading", "meeting_id": meeting_id}
#                         blob.chunk_size = 26214400  # 25MB chunk size
#                         blob.upload_from_file(
#                             response.raw,
#                             content_type="video/mp4"
#                         )
#                         print(f"Recording '{file_name}' uploaded successfully to GCP.")

#                         # Update metadata to mark upload as complete
#                         blob.metadata = {"status": "uploaded", "meeting_id": meeting_id}
#                         blob.patch()
#                     else:
#                         raise Exception(f"Failed to download file from Zoom. Status Code: {response.status_code}")
#                 except Exception as e:
#                     print(f"Error uploading file '{file_name}': {e}")
#     except Exception as e:
#         print(f"Critical error in upload_recordings for meeting ID '{meeting_id}': {e}")




# import time
# import threading
# from datetime import datetime
# import requests
# from google.cloud import storage

# # Constants for retry logic
# RETRY_BACKOFF_SECONDS = 10
# MAX_RETRIES = 5
# RETRY_INTERVAL = 3600  # Retry failed uploads every hour


# def retry_failed_uploads():
#     """Retry failed uploads every hour."""
#     while True:
#         print("Retrying failed uploads...")
#         try:
#             storage_client = storage.Client.from_service_account_json(GCP_CREDENTIALS)
#             bucket = storage_client.bucket(GCP_BUCKET_NAME)
#             blobs = bucket.list_blobs()

#             for blob in blobs:
#                 # Retry only files explicitly marked as "failed"
#                 if blob.metadata and blob.metadata.get("status") == "failed":
#                     meeting_id = blob.metadata.get("meeting_id")
#                     print(f"Retrying upload for file: {blob.name}")
#                     helperFunction(meeting_id, retry_failed=True)
#         except Exception as e:
#             print(f"Error while retrying failed uploads: {e}")
#         time.sleep(RETRY_INTERVAL)


# def helperFunction(meeting_id, retry_failed=False):
#     """Process and upload recordings for a given meeting ID."""
#     try:
#         # Get Zoom access token
#         access_token = get_access_token(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID)
#         if not access_token:
#             raise Exception("Failed to retrieve access token from Zoom")

#         # Get meeting recording details
#         details = get_recording_details(access_token, meeting_id)
#         if not details:
#             raise Exception(f"Failed to retrieve recording details for meeting {meeting_id}")

#         recordings = details.get("recording_files", [])
#         meeting_topic = details.get("topic", "Unknown_Meeting").replace("/", "_").replace(":", "_")


#         # Initialize Google Cloud Storage client
#         storage_client = storage.Client.from_service_account_json(GCP_CREDENTIALS)
#         bucket = storage_client.bucket(GCP_BUCKET_NAME)

#         # Process each recording
#         for recording in recordings:
#             if recording.get("file_type") == "MP4":
#                 file_url = recording["download_url"]
#                 file_name = f"{meeting_topic}_{recording['id']}.mp4"

#                 # Check if file already exists and uploaded successfully
#                 blob = bucket.blob(file_name)
#                 if blob.exists():
#                     if blob.metadata and blob.metadata.get("status") == "uploaded":
#                         print(f"File '{file_name}' already uploaded successfully. Skipping upload.")
#                         continue
#                     elif blob.metadata and blob.metadata.get("status") == "uploading":
#                         print(f"File '{file_name}' is in progress. Skipping redundant upload.")
#                         continue

#                 retry_count = 0
#                 success = False

#                 while retry_count < MAX_RETRIES and not success:
#                     try:
#                         # Stream download from Zoom
#                         headers = {"Authorization": f"Bearer {access_token}"}
#                         response = requests.get(file_url, headers=headers, stream=True, timeout=60)

#                         if response.status_code == 200:
#                             print(f"Uploading '{file_name}' to GCP...")

#                             # Mark blob as "uploading" before uploading
#                             blob.metadata = {"status": "uploading", "meeting_id": meeting_id}
#                             blob.chunk_size = 26214400  # 25MB chunk size
#                             blob.upload_from_file(
#                                 response.raw,
#                                 content_type="video/mp4",
#                                 retry=storage.retry.DEFAULT_RETRY,
#                             )

#                             # Verify upload success
#                             if blob.exists():
#                                 print(f"Recording '{file_name}' uploaded successfully to GCP.")
#                                 success = True
#                                 blob.metadata = {"status": "uploaded", "meeting_id": meeting_id}
#                                 blob.patch()
#                             else:
#                                 raise Exception(f"Upload verification failed for '{file_name}'")
#                         else:
#                             raise Exception(f"Failed to download file from Zoom. Status Code: {response.status_code}")

#                     except Exception as e:
#                         retry_count += 1
#                         print(f"Error processing file '{file_name}': {e}")
#                         if retry_count < MAX_RETRIES:
#                             backoff_time = RETRY_BACKOFF_SECONDS * (2 ** (retry_count - 1))
#                             print(f"Retrying... ({retry_count}/{MAX_RETRIES}) after {backoff_time} seconds.")
#                             time.sleep(backoff_time)
#                         else:
#                             print(f"Failed to process file '{file_name}' after {MAX_RETRIES} attempts.")
#                             blob.metadata = {"status": "failed", "meeting_id": meeting_id}
#                             blob.patch()

#     except Exception as e:
#         print(f"Critical error in helper_function for meeting ID '{meeting_id}': {e}")

#     print(f"All recordings for meeting '{meeting_id}' have been processed.")


# # Start the retry thread
# retry_thread = threading.Thread(target=retry_failed_uploads, daemon=True)
# retry_thread.start()

 


# def helperFunction(meeting_id):
#     client_id = ZOOM_CLIENT_ID
#     client_secret = ZOOM_CLIENT_SECRET
#     account_id = ZOOM_ACCOUNT_ID

#     # Google Cloud credentials
#     gcp_credentials_path = GCP_CREDENTIALS  # Path to your GCP credentials JSON file
#     gcp_bucket_name = GCP_BUCKET_NAME  # Your GCP bucket name

#     try:
#         # Get Zoom access token
#         access_token = get_access_token(client_id, client_secret, account_id)
#         if not access_token:
#             raise Exception("Failed to retrieve access token from Zoom")

#         print("AccessToken ::::  ", access_token)
#         print("MEETING ID :::::::::::::      ::::::   :::::  :::", meeting_id)

#         # Get meeting recording details
#         details = get_recording_details(access_token, meeting_id)
#         print(":::::::::: Details :::::: :::: :: ", details)
#         if not details:
#             raise Exception(f"Failed to retrieve recording details for meeting {meeting_id}")

#         recordings = details.get('recording_files', [])

#         # Sanitize meeting_topic to remove invalid characters
#         meeting_topic = details.get('topic', 'Unknown_Meeting').replace('/', '_').replace(':', '_')

#         # Sanitize timestamp to remove invalid characters
#         timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace(':', '_')

#         # Initialize Google Cloud Storage client
#         storage_client = storage.Client.from_service_account_json(gcp_credentials_path)
#         bucket = storage_client.bucket(gcp_bucket_name)

#         # Process each recording
#         for recording in recordings:
#             if recording.get('file_type') == 'MP4':
#                 file_url = recording['download_url']
#                 file_name = f"{meeting_topic}_{timestamp}.mp4"

#                 print("Processing file:", file_name)

#                 # Check if file already exists in GCP
#                 blob = bucket.blob(file_name)
#                 if blob.exists():
#                     print(f"File '{file_name}' already exists in GCP. Skipping upload.")
#                     continue

#                 # Retry logic for downloading and uploading
#                 retry_count = 5
#                 while retry_count > 0:
#                     try:
#                         # Stream download
#                         headers = {"Authorization": f"Bearer {access_token}"}
#                         response = requests.get(file_url, headers=headers, stream=True, timeout=60)

#                         if response.status_code == 200:
#                             print(f"Uploading '{file_name}' to GCP...")

#                             # Ensure resumable uploads
#                             blob.chunk_size = 262144  # 256 KB
#                             blob.upload_from_file(response.raw, content_type='video/mp4', retry=storage.retry.DEFAULT_RETRY)

#                             # Verify if upload was successful
#                             if blob.exists():
#                                 print(f"Recording '{file_name}' uploaded successfully to GCP.")
#                             else:
#                                 raise Exception(f"Upload verification failed for '{file_name}'")

#                             break
#                         else:
#                             raise Exception(f"Failed to download file from Zoom. Status Code: {response.status_code}")

#                     except Exception as e:
#                         retry_count -= 1
#                         print(f"Error processing file '{file_name}': {e}")
#                         if retry_count > 0:
#                             print(f"Retrying... ({5 - retry_count}/5)")
#                             time.sleep(5)
#                         else:
#                             print(f"Failed to process file '{file_name}' after multiple attempts.")
#                             raise e

#     except Exception as e:
#         print(f"Critical error in helperFunction: {e}")

#     print(f"All recordings for meeting '{meeting_id}' have been processed.")



















# def helperFunction(meeting_id):
#     client_id = ZOOM_CLIENT_ID
#     client_secret = ZOOM_CLIENT_SECRET
#     account_id = ZOOM_ACCOUNT_ID

#     # Google Cloud credentials
#     gcp_credentials_path = GCP_CREDENTIALS # Replace with your GCP credentials file path
#     gcp_bucket_name = GCP_BUCKET_NAME  # Replace with your GCP bucket name


#     access_token = get_access_token(client_id, client_secret, account_id)
#     if not access_token:
#         return


#     print("AccessToken ::::  ", access_token)
#     print("MEETING ID :::::::::::::      ::::::   :::::  :::", meeting_id)
#     details = get_recording_details(access_token, meeting_id)
#     print(":::::::::: Details :::::: :::: :: ",details)
#     if not details:
#         return

#     recordings = details.get('recording_files', [])

#     # Sanitize meeting_topic to remove invalid characters
#     meeting_topic = details.get('topic', 'Unknown_Meeting').replace('/', '_').replace(':', '_')

#     # Sanitize timestamp to remove invalid characters
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace(':', '_')

#     # Base folder for recordings
#     base_path = r"C:\\Users\\sudhi\\zoomRecordings"  # Replace with your desired local directory
#     if not os.path.exists(base_path):
#         os.makedirs(base_path)

#     # Subfolder for the specific meeting
#     meeting_folder = f"{meeting_topic}_{timestamp}"
#     save_path = os.path.join(base_path, meeting_folder)

#     # Ensure the save_path directory is created
#     if not os.path.exists(save_path):
#         os.makedirs(save_path)

#     # Download and upload only the recording video
#     for recording in recordings:
#         print("recordingsss:::::::: ::::: ::::", recordings)
#         if recording.get('file_type') == 'MP4':
#             file_url = recording['download_url']
#             file_name = f"{meeting_topic}.mp4"

#             print("file_name ::: ::    :::  ",file_name )
#             # Download recording
#             local_file_path = download_recording(file_url, save_path, file_name, access_token)

#             # Upload to GCP
#             upload_to_gcp(local_file_path, gcp_bucket_name, gcp_credentials_path)

#     print(f"All recordings for meeting '{meeting_topic}' saved locally and uploaded to GCP.")

    # meeting_topic = details.get('topic', 'Unknown_Meeting').replace('/', '_')
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # # Base folder for recordings
    # base_path = r"C:\\Users\\sudhi\\zoomRecordings"  # Replace with your desired local directory
    # if not os.path.exists(base_path):
    #     os.makedirs(base_path)

    # # Subfolder for the specific meeting
    # meeting_folder = f"{meeting_topic}_{timestamp}"
    # save_path = os.path.join(base_path, meeting_folder)

    # # Download and upload only the recording video
    # for recording in recordings:
    #     if recording.get('file_type') == 'MP4':
    #         file_url = recording['download_url']
    #         file_name = f"{recording['id']}.mp4"

    #         # Download recording
    #         local_file_path = download_recording(file_url, save_path, file_name, access_token)

    #         # Upload to GCP
    #         upload_to_gcp(local_file_path, gcp_bucket_name, gcp_credentials_path)

    # print(f"All recordings for meeting '{meeting_topic}' saved locally and uploaded to GCP.")























# //////////////////////////////////////


# # Load environment variables
# load_dotenv()
# ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
# ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
# ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
# GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
# GCP_CREDENTIALS = os.getenv("GCP_CREDENTIALS")
# ZOOM_SECRET_TOKEN='yFoUWja9QpuLqSjFdSZjIQ'


# # Initialize GCP client


# def get_zoom_access_token():
#     """Fetch OAuth access token for Zoom."""
#     url = "https://zoom.us/oauth/token"
#     params = {
#         "grant_type": "account_credentials",
#         "account_id": ZOOM_ACCOUNT_ID,
#     }
#     auth = (ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
#     response = requests.post(url, params=params, auth=auth)
#     if response.status_code == 200:
#         return response.json().get("access_token")
#     else:
#         print(f"Error fetching access token: {response.text}")
#         return None
    

# def download_recording(recording_url, save_path, file_name, access_token):
#     if not os.path.exists(save_path):
#         os.makedirs(save_path)




# def upload_to_gcp(file_url, file_name):
#     """
#     Download a file from a URL and upload it to a GCP bucket.

#     Args:
#         file_url (str): The URL of the file to be downloaded.
#         file_name (str): The name of the file to be saved in the bucket.
#     """
#     try:
#         # Set the environment variable for authentication
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_CREDENTIALS

#         # Initialize the GCS client
#         client = storage.Client()

#         # Access the bucket
#         bucket = client.bucket(GCP_BUCKET_NAME)

#         # Create a blob for the file
#         blob = bucket.blob(file_name)

#         # Download the file from the URL to a temporary location
#         response = requests.get(file_url, stream=True)
#         if response.status_code == 200:
            
#             blob.upload_from_file(response.raw, content_type="video/mp4")
#             print(f"Uploaded {file_name} to GCP bucket.")

            
#         else:
#             print(f"Error downloading file: {response.status_code} - {response.text}")

#     except Exception as e:
#         print(f"Error uploading file to GCP: {e}")


# @csrf_exempt
# def zoom_webhook(request):
#     """Handle Zoom webhooks and validation."""
#     if request.method == "POST":
#         try:
#             # Parse the incoming JSON data
#             data = json.loads(request.body.decode("utf-8"))
#             print(data)  # For debugging, you can remove this once it's working
            
#             # Handle the URL validation event (this is the first step Zoom performs)
#             if data.get("event") == "endpoint.url_validation":
#                 plain_token = data.get("payload", {}).get("plainToken")
#                 if plain_token:
#                     # Generate encrypted token as Zoom requires
#                     secret_token = ZOOM_SECRET_TOKEN.encode("utf-8")
#                     mess = plain_token.encode("utf-8")
#                     has = hmac.new(secret_token, mess, hashlib.sha256).digest()
#                     hex_message = has.hex()

#                     # Send back the plainToken and encryptedToken
#                     response = JsonResponse({
#                         "plainToken": plain_token,
#                         "encryptedToken": hex_message,
#                     })
#                     response['Content-Type'] = 'application/json'  # Explicitly set Content-Type
#                     print("Validation Response:", response.content)
#                     return response
#                 else:
#                     return JsonResponse({"error": "No plainToken found"}, status=400)

#             # Handle other events (like recording.completed)
#             if data.get("event") == "recording.completed":
#                 recording = data.get("payload", {}).get("object", {})
#                 meeting_name = recording.get("topic", "Untitled Meeting")
#                 # Loop through all recording files
#                 for file in recording.get("recording_files", []):
#                     if file.get("file_type") == "MP4":
#                         file_name = f"{meeting_name}_{file.get('id')}.mp4"
#                         # Call your upload function here
#                         upload_to_gcp(file.get("download_url"), file_name)

            

#             return JsonResponse({"message": "Webhook received successfully."})
#         except Exception as e:
#             print(f"Error: {e}")
#             return JsonResponse({"error": "Invalid data"}, status=400)

#     return JsonResponse({"error": "Invalid method"}, status=400)



# /////////////////////////////  end 


# @csrf_exempt
# def zoom_webhook(request):
#     print(":::::::::::::zoom webhook in", request.method)
#     """Handle Zoom webhooks and validation."""
#     if request.method == "POST":
#         try:
#             # Parse the incoming JSON data
#             data = json.loads(request.body.decode("utf-8"))
#             print(data)  # Debugging: Log the incoming data
            
#             # Handle the URL validation event
#             if data.get("event") == "endpoint.url_validation":
#                 plain_token = data.get("payload", {}).get("plainToken")
#                 if plain_token:
#                     print("Returning plainToken:", plain_token)
                    
#                     # Return the response in the expected format
#                     response = JsonResponse({"plainToken": plain_token})
#                     response["Content-Type"] = "application/json"
#                     return response
#                 else:
#                     return JsonResponse({"error": "plainToken not found"}, status=400)
            
#             # Handle other events (e.g., recording.completed)
#             if data.get("event") == "recording.completed":
#                 recording = data.get("payload", {}).get("object", {})
#                 meeting_name = recording.get("topic", "Untitled Meeting")
                
#                 # Process recording files
#                 for file in recording.get("recording_files", []):
#                     if file.get("file_type") == "MP4":
#                         file_name = f"{meeting_name}_{file.get('id')}.mp4"
#                         # Call your upload function here
#                         upload_to_gcp(file.get("download_url"), file_name)
            
#             return JsonResponse({"message": "Webhook received successfully."})
#         except Exception as e:
#             print(f"Error: {e}")
#             return JsonResponse({"error": "Invalid data"}, status=400)

#     return JsonResponse({"error": "Invalid method"}, status=400)



# def get_access_token(client_id, client_secret, account_id):
#     url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"
#     auth_header = f"{client_id}:{client_secret}".encode("utf-8")
#     headers = {
#         "Authorization": f"Basic {base64.b64encode(auth_header).decode('utf-8')}"
#     }
#     response = requests.post(url, headers=headers)
#     if response.status_code == 200:
#         return response.json()["access_token"]
#     else:
#         print("Failed to generate access token.")
#         return None
    
# @csrf_exempt
# def zoom_webhook(request):
#     """Handle Zoom webhooks and validation."""
#     if request.method == "POST":
#         try:
#             # Parse the incoming JSON data
#             data = json.loads(request.body.decode("utf-8"))
#             print(data)  # For debugging, you can remove this once it's working
            
#             # Handle the URL validation event (this is the first step Zoom performs)
#             if data.get("event") == "endpoint.url_validation":
#                 plain_token = data.get("payload", {}).get("plainToken")
#                 if plain_token:
#                     # Generate encrypted token as Zoom requires
#                     secret_token = ZOOM_SECRET_TOKEN.encode("utf-8")
#                     mess = plain_token.encode("utf-8")
#                     has = hmac.new(secret_token, mess, hashlib.sha256).digest()
#                     hex_message = has.hex()

#                     # Send back the plainToken and encryptedToken
#                     response = JsonResponse({
#                         "plainToken": plain_token,
#                         "encryptedToken": hex_message,
#                     })
#                     response['Content-Type'] = 'application/json'  # Explicitly set Content-Type
#                     print("Validation Response:", response.content)
#                     return response
#                 else:
#                     return JsonResponse({"error": "No plainToken found"}, status=400)

#             # Handle other events (like recording.completed)
#             if data.get("event") == "recording.completed":
#                 recording = data.get("payload", {}).get("object", {})
#                 print("::::::::::             :::::::::::      RECORDINGS       :::::::::::::",recording)
#                 meeting_id = recording.get("id", "None")

#                 result = helperFunction(meeting_id)
#                 # Loop through all recording files
#                 # for file in recording.get("recording_files", []):
#                 #     if file.get("file_type") == "MP4":
#                 #         meeting_id = file.get('id').replace(" ","")

                        

#                         # file_name = f"{meeting_name}_{file.get('id')}.mp4"
#                         # Call your upload function here
#                         # upload_to_gcp(file.get("download_url"), file_name)

            

#             return JsonResponse({"message": "Webhook received successfully."})
#         except Exception as e:
#             print(f"Error: {e}")
#             return JsonResponse({"error": "Invalid data"}, status=400)

#     return JsonResponse({"error": "Invalid method"}, status=400)
    

# def helperFunction(meeting_id):
#     client_id = ZOOM_CLIENT_ID
#     client_secret = ZOOM_CLIENT_SECRET
#     account_id = ZOOM_ACCOUNT_ID

#     # Google Cloud credentials
#     gcp_credentials_path = GCP_CREDENTIALS # Replace with your GCP credentials file path
#     gcp_bucket_name = GCP_BUCKET_NAME  # Replace with your GCP bucket name


#     access_token = get_access_token(client_id, client_secret, account_id)
#     if not access_token:
#         return


#     print("AccessToken ::::  ", access_token)
#     print("MEETING ID :::::::::::::      ::::::   :::::  :::", meeting_id)
#     details = get_recording_details(access_token, meeting_id)
#     print(":::::::::: Details :::::: :::: :: ",details)
#     if not details:
#         return

#     recordings = details.get('recording_files', [])

#     # Sanitize meeting_topic to remove invalid characters
#     meeting_topic = details.get('topic', 'Unknown_Meeting').replace('/', '_').replace(':', '_')

#     # Sanitize timestamp to remove invalid characters
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace(':', '_')

#     # Base folder for recordings
#     base_path = r"C:\\Users\\sudhi\\zoomRecordings"  # Replace with your desired local directory
#     if not os.path.exists(base_path):
#         os.makedirs(base_path)

#     # Subfolder for the specific meeting
#     meeting_folder = f"{meeting_topic}_{timestamp}"
#     save_path = os.path.join(base_path, meeting_folder)

#     # Ensure the save_path directory is created
#     if not os.path.exists(save_path):
#         os.makedirs(save_path)

#     # Download and upload only the recording video
#     for recording in recordings:
#         print("recordingsss:::::::: ::::: ::::", recordings)
#         if recording.get('file_type') == 'MP4':
#             file_url = recording['download_url']
#             file_name = f"{meeting_topic}.mp4"

#             print("file_name ::: ::    :::  ",file_name )
#             # Download recording
#             local_file_path = download_recording(file_url, save_path, file_name, access_token)

#             # Upload to GCP
#             upload_to_gcp(local_file_path, gcp_bucket_name, gcp_credentials_path)

#     print(f"All recordings for meeting '{meeting_topic}' saved locally and uploaded to GCP.")

    # meeting_topic = details.get('topic', 'Unknown_Meeting').replace('/', '_')
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # # Base folder for recordings
    # base_path = r"C:\\Users\\sudhi\\zoomRecordings"  # Replace with your desired local directory
    # if not os.path.exists(base_path):
    #     os.makedirs(base_path)

    # # Subfolder for the specific meeting
    # meeting_folder = f"{meeting_topic}_{timestamp}"
    # save_path = os.path.join(base_path, meeting_folder)

    # # Download and upload only the recording video
    # for recording in recordings:
    #     if recording.get('file_type') == 'MP4':
    #         file_url = recording['download_url']
    #         file_name = f"{recording['id']}.mp4"

    #         # Download recording
    #         local_file_path = download_recording(file_url, save_path, file_name, access_token)

    #         # Upload to GCP
    #         upload_to_gcp(local_file_path, gcp_bucket_name, gcp_credentials_path)

    # print(f"All recordings for meeting '{meeting_topic}' saved locally and uploaded to GCP.")























# //////////////////////////////////////


# # Load environment variables
# load_dotenv()
# ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
# ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
# ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
# GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
# GCP_CREDENTIALS = os.getenv("GCP_CREDENTIALS")
# ZOOM_SECRET_TOKEN='yFoUWja9QpuLqSjFdSZjIQ'


# # Initialize GCP client


# def get_zoom_access_token():
#     """Fetch OAuth access token for Zoom."""
#     url = "https://zoom.us/oauth/token"
#     params = {
#         "grant_type": "account_credentials",
#         "account_id": ZOOM_ACCOUNT_ID,
#     }
#     auth = (ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
#     response = requests.post(url, params=params, auth=auth)
#     if response.status_code == 200:
#         return response.json().get("access_token")
#     else:
#         print(f"Error fetching access token: {response.text}")
#         return None
    






# def upload_to_gcp(file_url, file_name):
#     """
#     Download a file from a URL and upload it to a GCP bucket.

#     Args:
#         file_url (str): The URL of the file to be downloaded.
#         file_name (str): The name of the file to be saved in the bucket.
#     """
#     try:
#         # Set the environment variable for authentication
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_CREDENTIALS

#         # Initialize the GCS client
#         client = storage.Client()

#         # Access the bucket
#         bucket = client.bucket(GCP_BUCKET_NAME)

#         # Create a blob for the file
#         blob = bucket.blob(file_name)

#         # Download the file from the URL to a temporary location
#         response = requests.get(file_url, stream=True)
#         if response.status_code == 200:
            
#             blob.upload_from_file(response.raw, content_type="video/mp4")
#             print(f"Uploaded {file_name} to GCP bucket.")

            
#         else:
#             print(f"Error downloading file: {response.status_code} - {response.text}")

#     except Exception as e:
#         print(f"Error uploading file to GCP: {e}")


# @csrf_exempt
# def zoom_webhook(request):
#     """Handle Zoom webhooks and validation."""
#     if request.method == "POST":
#         try:
#             # Parse the incoming JSON data
#             data = json.loads(request.body.decode("utf-8"))
#             print(data)  # For debugging, you can remove this once it's working
            
#             # Handle the URL validation event (this is the first step Zoom performs)
#             if data.get("event") == "endpoint.url_validation":
#                 plain_token = data.get("payload", {}).get("plainToken")
#                 if plain_token:
#                     # Generate encrypted token as Zoom requires
#                     secret_token = ZOOM_SECRET_TOKEN.encode("utf-8")
#                     mess = plain_token.encode("utf-8")
#                     has = hmac.new(secret_token, mess, hashlib.sha256).digest()
#                     hex_message = has.hex()

#                     # Send back the plainToken and encryptedToken
#                     response = JsonResponse({
#                         "plainToken": plain_token,
#                         "encryptedToken": hex_message,
#                     })
#                     response['Content-Type'] = 'application/json'  # Explicitly set Content-Type
#                     print("Validation Response:", response.content)
#                     return response
#                 else:
#                     return JsonResponse({"error": "No plainToken found"}, status=400)

#             # Handle other events (like recording.completed)
#             if data.get("event") == "recording.completed":
#                 recording = data.get("payload", {}).get("object", {})
#                 meeting_name = recording.get("topic", "Untitled Meeting")
#                 # Loop through all recording files
#                 for file in recording.get("recording_files", []):
#                     if file.get("file_type") == "MP4":
#                         file_name = f"{meeting_name}_{file.get('id')}.mp4"
#                         # Call your upload function here
#                         upload_to_gcp(file.get("download_url"), file_name)

            

#             return JsonResponse({"message": "Webhook received successfully."})
#         except Exception as e:
#             print(f"Error: {e}")
#             return JsonResponse({"error": "Invalid data"}, status=400)

#     return JsonResponse({"error": "Invalid method"}, status=400)



# /////////////////////////////  end 


# @csrf_exempt
# def zoom_webhook(request):
#     print(":::::::::::::zoom webhook in", request.method)
#     """Handle Zoom webhooks and validation."""
#     if request.method == "POST":
#         try:
#             # Parse the incoming JSON data
#             data = json.loads(request.body.decode("utf-8"))
#             print(data)  # Debugging: Log the incoming data
            
#             # Handle the URL validation event
#             if data.get("event") == "endpoint.url_validation":
#                 plain_token = data.get("payload", {}).get("plainToken")
#                 if plain_token:
#                     print("Returning plainToken:", plain_token)
                    
#                     # Return the response in the expected format
#                     response = JsonResponse({"plainToken": plain_token})
#                     response["Content-Type"] = "application/json"
#                     return response
#                 else:
#                     return JsonResponse({"error": "plainToken not found"}, status=400)
            
#             # Handle other events (e.g., recording.completed)
#             if data.get("event") == "recording.completed":
#                 recording = data.get("payload", {}).get("object", {})
#                 meeting_name = recording.get("topic", "Untitled Meeting")
                
#                 # Process recording files
#                 for file in recording.get("recording_files", []):
#                     if file.get("file_type") == "MP4":
#                         file_name = f"{meeting_name}_{file.get('id')}.mp4"
#                         # Call your upload function here
#                         upload_to_gcp(file.get("download_url"), file_name)
            
#             return JsonResponse({"message": "Webhook received successfully."})
#         except Exception as e:
#             print(f"Error: {e}")
#             return JsonResponse({"error": "Invalid data"}, status=400)

#     return JsonResponse({"error": "Invalid method"}, status=400)





# def upload_to_gcp(file_url, file_name):
#     """Upload file to GCP bucket."""
#     blob = bucket.blob(file_name)
#     response = requests.get(file_url, stream=True)
#     if response.status_code == 200:
#         blob.upload_from_file(response.raw, content_type="video/mp4")
#         print(f"Uploaded {file_name} to GCP bucket.")
#     else:
#         print(f"Error downloading file: {response.text}")


# @csrf_exempt
# def zoom_webhook(request):
#     print(":::::::::::::zoom webhook in" , request.method)
#     """Handle Zoom webhooks and validation."""
#     if request.method == "GET" and "validationToken" in request.GET:
#         # Respond with the validationToken in plain text
#         validation_token = request.GET["validationToken"]
#         return JsonResponse({"message": validation_token}, safe=False)

#     if request.method == "POST":
#         try:
#             # Parse the incoming JSON data
#             data = json.loads(request.body.decode("utf-8"))
#             print(data)  # For debugging, you can remove this once it's working
            
#             # Handle the URL validation event (this is the first step Zoom performs)
#             if data.get("event") == "endpoint.url_validation":
#                 plain_token = data.get("payload", {}).get("plainToken")
#                 if plain_token:
#                     # Ensure the correct response format
#                     print("result::::",{"plainToken": plain_token})
#                     response = JsonResponse({"plainToken": plain_token})
#                     response['Content-Type'] = 'application/json'
#                     print(":::",response.get('plainToken'))
#                     return response


#                     # return JsonResponse({"plainToken": plain_token})
#                     # response['Content-Type'] = 'application/json'
#                 else:
#                     return JsonResponse({"error": "No plainToken found"}, status=400)

#             # Handle other events (like recording.completed)
#             if data.get("event") == "recording.completed":
#                 recording = data.get("payload", {}).get("object", {})
#                 meeting_name = recording.get("topic", "Untitled Meeting")
#                 # Loop through all recording files
#                 for file in recording.get("recording_files", []):
#                     if file.get("file_type") == "MP4":
#                         file_name = f"{meeting_name}_{file.get('id')}.mp4"
#                         # Call your upload function here
#                         upload_to_gcp(file.get("download_url"), file_name)

#             return JsonResponse({"message": "Webhook received successfully."})  
#         except Exception as e:
#             print(f"Error: {e}")
#             return JsonResponse({"error": "Invalid data"}, status=400)


#     return JsonResponse({"error": "Invalid method"}, status=400)

