from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum
from .models import Course, Enrollment, LessonProgress
from .serializers import CourseSerializer
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

def get_recommendations(user):
    """
    Generate course recommendations for the given user based on historical enrollment data.
    This function:
      1. Finds courses the user is not enrolled in.
      2. Computes a 'popularity' score based on total enrollments.
      3. Uses KMeans clustering to separate courses into two groups.
      4. Selects the cluster with the highest average enrollments.
      5. Returns the top 3 courses from that cluster, ordered by enrollment count.
    """
    # Get courses the user is already enrolled in.
    enrolled_course_ids = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
    # Candidate courses are those the user is not enrolled in.
    candidates = Course.objects.exclude(id__in=enrolled_course_ids)
    
    # Build a list of [course_id, total_enrollments] for each candidate.
    course_data = []
    for course in candidates:
        total_enrollments = Enrollment.objects.filter(course=course).count()
        course_data.append([course.id, total_enrollments])
    
    # If no candidates, return an empty list.
    if not course_data:
        return []
    
    # Prepare data for clustering (using only the popularity metric).
    data = np.array([x[1] for x in course_data]).reshape(-1, 1)
    
    # Use KMeans clustering if there are at least 2 candidates.
    if len(data) >= 2:
        kmeans = KMeans(n_clusters=2, random_state=42)
        labels = kmeans.fit_predict(data)
        # Compute the average enrollment in each cluster.
        cluster_avg = {}
        for label in np.unique(labels):
            cluster_avg[label] = np.mean(data[labels == label])
        # Choose the cluster with the highest average enrollment.
        best_cluster = max(cluster_avg, key=cluster_avg.get)
        # Filter candidate courses that belong to the best cluster.
        recommended_ids = [course_data[i][0] for i in range(len(course_data)) if labels[i] == best_cluster]
    else:
        recommended_ids = [x[0] for x in course_data]
    
    # Annotate each course with enrollment count and order by popularity.
    recommended_courses = (
        Course.objects.filter(id__in=recommended_ids)
        .annotate(enrollment_count=Count('enrollments'))
        .order_by('-enrollment_count')[:3]
    )
    
    return recommended_courses

class RecommendationView(APIView):
    """
    API endpoint that returns personalized course recommendations for an authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get_user_profile(self, user):
        """Generate user profile based on their learning history"""
        enrollments = Enrollment.objects.filter(student=user)
        
        if not enrollments.exists():
            return None
        
        profile = {
            'preferred_difficulty': self.get_preferred_difficulty(enrollments),
            'avg_completion_rate': enrollments.aggregate(Avg('progress'))['progress__avg'] or 0,
            'total_learning_time': self.get_total_learning_time(user),
            'completed_courses': enrollments.filter(completed=True).count()
        }
        return profile

    def get_preferred_difficulty(self, enrollments):
        """Determine user's preferred difficulty level"""
        difficulty_counts = (
            enrollments
            .values('course__difficulty_level')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return difficulty_counts[0]['course__difficulty_level'] if difficulty_counts else 'beginner'

    def get_total_learning_time(self, user):
        """Calculate total time spent learning"""
        return LessonProgress.objects.filter(student=user).aggregate(
            total_time=Sum('watched_duration')
        )['total_time'] or 0

    def get_course_features(self, course):
        """Extract relevant features for course similarity"""
        return {
            'difficulty_level': self.difficulty_to_numeric(course.difficulty_level),
            'total_duration': course.total_duration,
            'avg_rating': self.get_course_rating(course),
            'completion_rate': course.get_completion_rate(),
            'total_lessons': course.lessons.count()
        }

    def difficulty_to_numeric(self, difficulty):
        """Convert difficulty level to numeric value"""
        mapping = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
        return mapping.get(difficulty, 1)

    def get_course_rating(self, course):
        """Calculate course rating (placeholder for actual rating system)"""
        return course.get_completion_rate() * 0.01 * 5  # Simple conversion to 5-star scale

    def get_similar_courses(self, user_profile, excluded_courses):
        """Find courses similar to user's preferences"""
        # Get all courses except those user is already enrolled in
        available_courses = Course.objects.exclude(id__in=excluded_courses)
        
        if not available_courses.exists():
            return []

        # Create feature matrix
        course_features = []
        course_ids = []
        
        for course in available_courses:
            features = self.get_course_features(course)
            course_features.append(list(features.values()))
            course_ids.append(course.id)

        # Convert to numpy array and normalize
        X = np.array(course_features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Create user preference vector
        user_vector = np.array([[
            self.difficulty_to_numeric(user_profile['preferred_difficulty']),
            user_profile['avg_completion_rate'] * 10,  # Scale to similar range as course duration
            user_profile['total_learning_time'] / 3600,  # Convert to hours
            user_profile['completed_courses'],
            user_profile['completed_courses'] * 2  # Proxy for expected lessons
        ]])
        user_vector_scaled = scaler.transform(user_vector)

        # Calculate similarity scores
        similarities = cosine_similarity(user_vector_scaled, X_scaled)[0]
        
        # Get top 5 most similar courses
        top_indices = similarities.argsort()[-5:][::-1]
        recommended_courses = []
        
        for idx in top_indices:
            course_id = course_ids[idx]
            similarity_score = similarities[idx]
            course = available_courses.get(id=course_id)
            recommended_courses.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'difficulty_level': course.difficulty_level,
                'similarity_score': round(similarity_score * 100, 2)
            })

        return recommended_courses

    def get(self, request):
        user = request.user
        user_profile = self.get_user_profile(user)
        
        if not user_profile:
            # New user recommendations
            return Response({
                'type': 'new_user',
                'recommendations': self.get_beginner_recommendations()
            })

        # Get courses user is already enrolled in
        enrolled_course_ids = Enrollment.objects.filter(
            student=user
        ).values_list('course_id', flat=True)

        # Get personalized recommendations
        recommendations = self.get_similar_courses(user_profile, enrolled_course_ids)

        return Response({
            'type': 'personalized',
            'user_profile': user_profile,
            'recommendations': recommendations
        })

    def get_beginner_recommendations(self):
        """Get recommendations for new users"""
        return list(Course.objects.filter(
            difficulty_level='beginner'
        ).order_by('-enrollments__count')[:5].values(
            'id', 'title', 'description', 'difficulty_level'
        ))
