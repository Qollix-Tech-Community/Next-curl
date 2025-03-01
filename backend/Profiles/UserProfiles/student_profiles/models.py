from django.db import models

# Create your models here.

class StudentProfile(models.Model):
    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(blank=False, unique=True)
    phone = models.CharField(max_length=10, blank=False)
    address = models.CharField(max_length=100, blank=True, null=True)
    prof_pic = models.ImageField(upload_to='profile_pics', blank=True)
    bio = models.TextField(max_length=500, blank=True)
    institution = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=100, blank=True, null=True)
    subjects = models.ManyToManyField('Subject', related_name='students', blank=False)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100, blank=False, unique=True)

    def __str__(self):
        return self.name