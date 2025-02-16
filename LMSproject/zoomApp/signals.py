# from django.db.models.signals import m2m_changed
# from django.dispatch import receiver
# from .models import ZoomMeeting
# from courses.models import Courses

# @receiver(m2m_changed, sender=ZoomMeeting.course)
# def update_video_count(sender, instance, action, reverse, model, pk_set, **kwargs):
#     """
#     Signal to update the videosCount field in Course model
#     whenever a ZoomMeeting is added or removed.
#     """

#     print("Update video count___+++++")
#     if action == "post_add":  # If a course is assigned to a recording
#         for course_id in pk_set:
#             course = Courses.objects.get(id=course_id)
#             course.videosCount += 1
#             course.save()

#     elif action in ["post_remove", "post_clear"]:  # If a course is unassigned or all are removed
#         for course_id in pk_set:
#             course = Courses.objects.get(id=course_id)
#             course.videosCount = max(course.videosCount - 1, 0)  # Prevent negative values
#             course.save()
