import os
import json
import requests
import logging
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
    all_ct = Annotation.objects.filter(author=user).count()
    done_ct = Annotation.objects.filter(author=user, status=Annotation.DONE).count()
    pending_ct = Annotation.objects.filter(author=user, status=Annotation.PENDING).count()
    not_done_ct = Annotation.objects.filter(author=user, status=Annotation.NOT_DONE).count()
    smoothing = 300
    smct = len([ct for ct in [done_ct, pending_ct, not_done_ct] if ct])
    return {
        'done_pct': done_ct and (done_ct + smoothing) / (all_ct + smct * smoothing) * 100,
        'pending_pct': pending_ct and (pending_ct + smoothing) / (all_ct + smct * smoothing) * 100,
        'remaining_pct': not_done_ct and (not_done_ct + smoothing) / (all_ct + smct * smoothing) * 100,
        'done': done_ct,
        'pending': pending_ct,
        'pass': pending_ct,
        'remaining': not_done_ct,
        'not_done': not_done_ct,
        'Annotation': Annotation
    }


@login_required(login_url='/auth/login')
def editor(request):
    user = request.user
    annotation_status = get_annotation_status(user)
    annotation = None
    sentences = []
    related_indexes = []
    if request.method == 'GET':
        id_ = request.GET.get('id')
        if id_:
            verdict = get_object_or_404(Verdict, id=id_)
            annotation = get_object_or_404(Annotation, author=user, verdict=verdict)

        elif annotation_status['remaining']:
            annotation = Annotation.objects.filter(author=user, status=Annotation.NOT_DONE)[0]
            logger.info('%s ANNOTATIING annotation.id=%s' % (user, annotation.id))

        if annotation:
            try:
                sentences = json.loads(annotation.verdict.raw)
                related_indexes = json.loads(annotation.annotation)
            except:
                import traceback
                traceback.print_exc()

        return render(request, 'editor/editor.html', {
            'sentences': sentences,
            'annotation': annotation,
            'related_indexes': related_indexes,
            'annotation_status': annotation_status
        })

    elif request.method == 'POST':
        POST = request.POST
        logger.info('%s POSTED %s' % (user, json.dumps(request.POST)))
        verdict = get_object_or_404(Verdict, id=POST['id'])
        annotation = get_object_or_404(Annotation, author=user, verdict=verdict)
        sentences = json.loads(verdict.raw)
        annotation.guilty = True if POST['guilty'] else False
        annotation.sentence_year = int(POST['sentence_year'])
        annotation.sentence_month = int(POST['sentence_month'])
        annotation.sentence_day = int(POST['sentence_day'])
        annotation.fine = int(POST['fine'])

        for key in POST.keys():
            if 'insult-' in key:
                _, idx = key.split('-')
                assert(int(idx) < len(sentences) and int(idx) >= 0)
                related_indexes.append(int(idx))
        annotation.annotation = json.dumps(related_indexes)
        annotation.status = Annotation.DONE
        annotation.save()
    return redirect('/anno/')


@login_required(login_url='/auth/login')
def list_annotation(request):
    user = request.user
    page = request.GET.get('page')
    status = request.GET.get('status')

    annotations = Annotation.objects.filter(author=user).order_by('-update_time')
    if status:
        annotations = annotations.filter(status=status)
    paginator = Paginator(annotations, 100)  # Show 100 contacts per page
    try:
        annotations = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        annotations = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        annotations = paginator.page(paginator.num_pages)
    return render(request, 'editor/list.html', {
        'annotations': annotations,
        'annotation_status': get_annotation_status(user),
    })
