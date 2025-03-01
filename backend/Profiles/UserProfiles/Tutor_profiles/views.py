from django.shortcuts import render, redirect, get_object_or_404
from .models import TutorProfile
from .forms import TutorProfileForm

def update_tutor_profile(request, pk):
    tutor = get_object_or_404(TutorProfile, pk=pk)
    if request.method == 'POST':
        form = TutorProfileForm(request.POST, request.FILES, instance=tutor)
        if form.is_valid():
            form.save()
            return redirect('tutor_profile_detail', pk=tutor.pk)
    else:
        form = TutorProfileForm(instance=tutor)
    return render(request, 'update_tutor_profile.html', {'form': form})
