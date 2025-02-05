from rest_framework import serializers
from .models import Recordings
from courses.models import Courses

class RecordingsSerializer(serializers.ModelSerializer):
    addRecordingList = serializers.ListField(write_only=True, required=False)
    removeRecordingList = serializers.ListField(write_only=True, required=False)
    # courseId = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    course_names = serializers.SerializerMethodField()

    # class Meta:
        # model = Recordings
        # fields = ['id', 'title', 'meeting_id', 'duration', 'recording_url', 'created_at', 'updated_at', 'courseId', 'course_names' , 'course' ]
    class Meta:
        model = Recordings
        fields = '__all__'

    def get_course_names(self, obj):
        return obj.course.courseName if obj.course else None  # Directly access courseName


    def create(self, validated_data):
        courseId = validated_data.pop('addRecordingList', [])
        recording = Recordings.objects.create(**validated_data)

        if courseId:
            courses = Courses.objects.filter(id__in=courseId).first()  # Get courses by IDs
            if courses:
                recording.course = courses  # Assign multiple courses
            # Increment videosCount for each assigned course
                # for course in :
                courses.videosCount += 1
                courses.save()
            # else:
            #     recording.status = "unassigned"
            recording.save()

        return recording
    

    # def update(instance, validated_data):
    #     print("+++++++++++++++", instance.course)
    #     add_list = set(validated_data.get('addRecordingList', []))
    #     remove_list = set(validated_data.get('removeRecordingList', [])) if 'removeRecordingList' in validated_data else set()

    #     # Ensure old_courses exists, even if instance.course is None
    #     old_courses = set(instance.course.all()) if instance.course else set()

    #     # Identify courses to remove
    #     removed_courses = {course for course in old_courses if course.id in remove_list} if remove_list else set()

    #     # Identify courses to add
    #     new_courses = set(Courses.objects.filter(id__in=add_list))

    #     # Compute final course set and update the recording's course field
    #     final_courses = (old_courses - removed_courses) | new_courses

    #     # Update the course field (if no previous courses, set the new courses)
    #     if not instance.course.exists():  # If no course was previously assigned, we can add new courses
    #         instance.course.set(new_courses)
    #     else:
    #         instance.course.set(final_courses)

    #     # Track changes summary
    #     changes_summary = {
    #         "added_courses": [course.courseName for course in new_courses - old_courses],
    #         "removed_courses": [course.courseName for course in removed_courses],
    #         "updated_fields": []
    #     }

    #     # Update `videosCount` for newly added courses
    #     for course in new_courses - old_courses:
    #         course.videosCount += 1
    #         course.save()

    #     # Update `videosCount` for removed courses
    #     for course in removed_courses:
    #         course.videosCount = max(0, course.videosCount - 1)
    #         course.save()

    #     # Update only specified fields in the `Recordings` table (skip `addRecordingList` and `removeRecordingList`)
    #     for attr, value in validated_data.items():
    #         if attr not in ['addRecordingList', 'removeRecordingList']:
    #             setattr(instance, attr, value)
    #             changes_summary["updated_fields"].append(attr)

    #     instance.save()
    #     return instance, changes_summary