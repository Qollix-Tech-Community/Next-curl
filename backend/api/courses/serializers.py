from rest_framework import serializers
from .models import Course, Lesson, Enrollment, LessonProgress

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'order']

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    instructor = serializers.StringRelatedField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'instructor', 'created_at', 'updated_at', 'lessons']

class EnrollmentSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField()
    student = serializers.StringRelatedField()

    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'student', 'enrolled_at']

class CourseAnalyticsSerializer(serializers.ModelSerializer):
    analytics = serializers.SerializerMethodField()
    student_progress = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'analytics', 'student_progress']

    def get_analytics(self, obj):
        return obj.get_analytics()

    def get_student_progress(self, obj):
        return Enrollment.objects.filter(course=obj).values(
            'student__username',
            'progress',
            'last_accessed'
        )

class EnrollmentAnalyticsSerializer(serializers.ModelSerializer):
    lesson_progress = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ['student', 'progress', 'enrolled_at', 'last_accessed', 'lesson_progress']

    def get_lesson_progress(self, obj):
        return LessonProgress.objects.filter(
            student=obj.student,
            lesson__course=obj.course
        ).values('lesson__title', 'watched_duration', 'completed', 'last_watched')