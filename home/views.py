from django.shortcuts import render, get_object_or_404, redirect
from .models import home
from .forms import homeForm


def index(request):
    return render(request, 'index.html')


def home_list(request):
    homes = home.objects.all().order_by('-created_at')
    return render(request, 'home_list.html', {'homes': homes})



def home_create(request):
    if request.method == "POST":
        form = homeForm(request.POST, request.FILES)
        if form.is_valid():
            home_obj = form.save(commit=False)
            home_obj.user = request.user
            home_obj.save()
            return redirect('home_list')
    else:
        form = homeForm()
    return render(request, 'home_form.html', {'form': form})


def home_edit(request, home_id):
    home_obj = get_object_or_404(home, pk=home_id, user=request.user)
    if request.method == 'POST':
        form = homeForm(request.POST, request.FILES, instance=home_obj)
        if form.is_valid():
            home_obj = form.save(commit=False)
            home_obj.user = request.user
            home_obj.save()
            return redirect('home_list')
    else:
        form = homeForm(instance=home_obj)
    return render(request, 'home_form.html', {'form': form})


def home_delete(request, home_id):
    home_obj = get_object_or_404(home, pk=home_id, user=request.user)
    if request.method == 'POST':
        home_obj.delete()
        return redirect('home_list')
    return render(request, 'home_confirm_delete.html', {'home': home_obj})
