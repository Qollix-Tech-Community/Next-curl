from django.shortcuts import render, redirect, get_object_or_404
from .models import StudentProfile
from .forms import StudentProfileForm

def update_profile(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return redirect('profile_detail', pk=student.pk)
    else:
        form = StudentProfileForm(instance=student)
    return render(request, 'update_profile.html', {'form': form})
