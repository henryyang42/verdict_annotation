import io
import os
import requests
from shutil import copy
from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

from collections import defaultdict
from .models import *
# Create your views here.


@login_required(login_url='/auth/login')
def editor(request):
    rs = ReactionScript()
    if request.method == 'POST':
        POST = dict(request.POST)
        POST.pop('csrfmiddlewaretoken')
        idx = POST.pop('id')
        if idx and idx[0] not in ['None']:
            rs = get_object_or_404(ReactionScript, id=idx[0], author=request.user)
        POST = {k: v[0] for k, v in POST.items()}
        actions = defaultdict(dict)
        for k, v in POST.items():
            if '-' in k:
                k, idx = k.split('-')
                actions[idx][k] = v
                actions[idx]['step'] = idx
            else:
                rs.__setattr__(k, v)
        rs.__setattr__('author', request.user)
        rs.__setattr__('update_time', timezone.now())
        rs.save()
        rs.behavior.all().delete()
        for k in sorted(actions.keys()):
            action = Action.objects.create(**actions[k])
            action.save()
            rs.behavior.add(action)
        rs.save()
        if rs.agent.all():
            agent = rs.agent.all()[0]
            return redirect(f'/editor/list?id={ agent.id }')
        return redirect('/editor/list_agent')
    else:
        idx = request.GET.get('id')
        if idx:
            rs = get_object_or_404(ReactionScript, id=idx, author=request.user)

    return render(request, 'editor/editor.html', {
        'rs': rs,
        'behavior': rs.behavior.all() if rs.intent and rs.behavior.all() else range(10)
    })


@login_required(login_url='/auth/login')
def export(request):
    idx = request.GET.get('id')
    agent = get_object_or_404(Agent, id=idx, author=request.user)
    zip_name, zip_path = agent.prepare_zip()
    response = HttpResponse(io.open(zip_path, mode="rb").read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
    return response


@login_required(login_url='/auth/login')
def publish(request):
    idx = request.GET.get('id')
    agent = get_object_or_404(Agent, id=idx, author=request.user)
    try:
        agent.prepare_zip()
        download_link = f"http://{request.get_host()}{settings.MEDIA_URL}{agent.export_file_path}".replace('\\', '/')
        # download_link = 'http://13.59.23.46:8000/media/dialogueflow/export/reaction_engine.zip'
        data = {'language': 'en',
                'author': request.user.username,
                'path': download_link}
        resp = requests.post("http://www.aeolus-chatbot.com/update", json=data)
    except:
        import traceback
        traceback.print_exc()
        return HttpResponse(status=500)
        
    return HttpResponse(resp.text, status=resp.status_code)


@login_required(login_url='/auth/login')
def list_rs(request):
    page = request.GET.get('page')
    idx = request.GET.get('id')

    agent = get_object_or_404(Agent, author=request.user, id=idx)
    reaction_scripts = agent.scripts.all().order_by('-update_time')
    paginator = Paginator(reaction_scripts, 100)  # Show 100 contacts per page
    try:
        reaction_scripts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        reaction_scripts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        reaction_scripts = paginator.page(paginator.num_pages)
    return render(request, 'editor/list.html', {
        'reaction_scripts': reaction_scripts,
        'agent': agent
    })


@login_required(login_url='/auth/login')
def list_agent(request):
    page = request.GET.get('page')

    agents = Agent.objects.filter(author=request.user).order_by('-update_time')
    for agent in agents:
        if not agent.export_file_path:
            agent.prepare_zip()
    paginator = Paginator(agents, 100)  # Show 100 contacts per page
    try:
        agents = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        agents = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        agents = paginator.page(paginator.num_pages)
    return render(request, 'editor/list_agent.html', {
        'agents': agents,
    })


@login_required(login_url='/auth/login')
def delete(request):
    idx = request.GET.get('id')
    next_page = request.META.get('HTTP_REFERER', '/editor/list')

    rs = get_object_or_404(ReactionScript, id=idx, author=request.user)
    rs.delete()
    return redirect(next_page)


@login_required(login_url='/auth/login')
def update_agent(request):
    form = AgentForm()
    idx = request.GET.get('id')
    agent = Agent()
    if idx:
        agent = get_object_or_404(Agent, id=idx, author=request.user)
        form = AgentForm(instance=agent)
    if request.method == 'POST':
        old_zip_name = agent.content.name
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            agent.author = request.user
            agent = form.save()
            if agent.content.name != old_zip_name:
                agent.import_zip()
            return redirect('/editor/list_agent')

    return render(request, 'editor/agent.html', {'form': form})


@login_required(login_url='/auth/login')
def delete_agent(request):
    idx = request.GET.get('id')
    next_page = request.META.get('HTTP_REFERER', '/editor/list')

    agent = get_object_or_404(Agent, id=idx)
    agent.delete()
    return redirect(next_page)
