from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.utils import timezone

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New fields for analytics
    total_duration = models.IntegerField(default=0)  # in minutes
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='beginner'
    )

    def get_analytics(self):
        return {
            'total_students': self.enrollments.count(),
            'average_progress': self.enrollments.aggregate(Avg('progress'))['progress__avg'] or 0,
            'completion_rate': self.get_completion_rate(),
            'total_lessons': self.lessons.count(),
            'active_students': self.enrollments.filter(last_accessed__gte=timezone.now() - timezone.timedelta(days=30)).count()
        }

    def get_completion_rate(self):
        total_enrollments = self.enrollments.count()
        if total_enrollments == 0:
            return 0
        completed = self.enrollments.filter(progress=100).count()
        return (completed / total_enrollments) * 100

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.course.title})"

class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    progress = models.IntegerField(default=0)  # 0-100%
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"

class LessonProgress(models.Model):
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='progress_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    watched_duration = models.IntegerField(default=0)  # in seconds
    completed = models.BooleanField(default=False)
    last_watched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('lesson', 'student') 