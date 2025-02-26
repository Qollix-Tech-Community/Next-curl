from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Avg, Count
from django.utils import timezone
from .models import Course, Lesson, Enrollment, LessonProgress
from .serializers import CourseSerializer, LessonSerializer, EnrollmentSerializer, CourseAnalyticsSerializer, EnrollmentAnalyticsSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'enroll']:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        student = request.user
        if course.enrollments.filter(student=student).exists():
            return Response(
                {'detail': 'You are already enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        enrollment = Enrollment.objects.create(course=course, student=student)
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def analytics(self, request, pk=None):
        course = self.get_object()
        if request.user != course.instructor and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to view these analytics."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CourseAnalyticsSerializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def student_progress(self, request, pk=None):
        course = self.get_object()
        if request.user != course.instructor and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to view student progress."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        enrollments = Enrollment.objects.filter(course=course)
        serializer = EnrollmentAnalyticsSerializer(enrollments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def engagement_metrics(self, request, pk=None):
        course = self.get_object()
        if request.user != course.instructor and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to view these metrics."},
                status=status.HTTP_403_FORBIDDEN
            )

        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        metrics = {
            'total_students': course.enrollments.count(),
            'active_students_30d': course.enrollments.filter(
                last_accessed__gte=thirty_days_ago
            ).count(),
            'average_progress': course.enrollments.aggregate(
                Avg('progress')
            )['progress__avg'] or 0,
            'completion_rate': course.get_completion_rate(),
            'lesson_completion_rates': LessonProgress.objects.filter(
                lesson__course=course
            ).values('lesson__title').annotate(
                completion_rate=Count('completed', filter=models.Q(completed=True)) * 100.0 / Count('*')
            )
        }
        
        return Response(metrics)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]