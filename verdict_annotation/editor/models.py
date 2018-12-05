import os
import json
import zipfile
from shutil import copy

from django.utils import timezone
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Verdict(models.Model):
    court_no = models.CharField(max_length=10, default='')
    court_type = models.CharField(max_length=10, default='')
    verdict_no = models.CharField(max_length=10, default='')
    year = models.CharField(max_length=10, default='')
    date = models.CharField(max_length=10, default='')
    raw = models.TextField(blank=True)

    def __str__(self):
        return "{court_type}-{court_no}-{verdict_no} ({date})".format(
            court_type=self.court_type, court_no=self.court_no,
            verdict_no=self.verdict_no, date=self.date
        )


class Annotation(models.Model):
    NOT_DONE, PENDING, DONE = 'Not done', 'Pass', 'Done'
    STATUS_CHOICES = (
        (NOT_DONE, NOT_DONE),
        (PENDING, PENDING),
        (DONE, DONE)
    )
    verdict = models.ForeignKey(Verdict, on_delete=models.PROTECT)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=NOT_DONE)
    update_time = models.DateTimeField(default=timezone.now)
    annotation = models.TextField(blank=True)

    def save(self, **kwargs):
        self.update_time = timezone.now()
        super(Annotation, self).save(**kwargs)
