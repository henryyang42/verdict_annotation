import os
import json
import requests
from shutil import copy
from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

from collections import defaultdict
from .models import *
# Create your views here.

logger = logging.getLogger(__name__)


def get_annotation_status(user):
    all_ct = Annotation.objects.filter(user=user).count()
    done_ct = Annotation.objects.filter(user=user, status=Annotation.DONE).count()
    pending_ct = Annotation.objects.filter(user=user, status=Annotation.PENDING).count()
    undone_ct = Annotation.objects.filter(user=user, status=Annotation.UNDONE).count()
    smoothing = 300
    smct = len([ct for ct in [done_ct, pending_ct, undone_ct] if ct])
    return {
        'done_pct': done_ct and (done_ct + smoothing) / (all_ct + smct * smoothing) * 100,
        'pending_pct': pending_ct and (pending_ct + smoothing) / (all_ct + smct * smoothing) * 100,
        'remaining_pct': undone_ct and (undone_ct + smoothing) / (all_ct + smct * smoothing) * 100,
        'done': done_ct,
        'pending': pending_ct,
        'pass': pending_ct,
        'remaining': undone_ct,
        'undone': undone_ct
    }


@login_required(login_url='/auth/login')
def editor(request):
    user = request.user
    annotation_status = get_annotation_status(user)
    Anno = Annotation
    if request.method == 'GET':
        id_ = request.GET.get('id')
        if id_:
            verdict = get_object_or_404(verdict, id=id_)
            annotation = get_object_or_404(author=user, verdict=verdict)
        else:
            if annotation_status['remaining']:
                annotation = Annotation.objects.filter(author=user, status=Annotation.UNDONE)[0]
                entry = annotation.entry
            else:
                all_finished = True
                return render(request, 'editor.html', locals())
        logger.info('%s ANNOTATIING annotation.id=%s' % (user, annotation.id))
        sentences = json.loads(verdict.raw)
        return render(request, 'editor.html', locals())

    elif request.method == 'POST':
        POST = request.POST
        logger.info('%s POSTED %s' % (user, json.dumps(request.POST)))
        verdict = get_object_or_404(verdict, id=POST['id'])
        annotation = get_object_or_404(Annotation, author=user, verdict=verdict)

        annotation.save()
    return redirect('/annotate/')


@login_required(login_url='/auth/login')
def list_annotation(request):
    page = request.GET.get('page')

    annotations = Annotation.objects.filter(author=request.user, status=Annotation.DONE).order_by('-update_time')        
    paginator = Paginator(agents, 100)  # Show 100 contacts per page
    try:
        agents = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        agents = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        agents = paginator.page(paginator.num_pages)
    return render(request, 'editor/list.html', {
        'annotations': annotations,
    })
