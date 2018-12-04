import csv
import glob
import random
import string

import tqdm
from access_django import *
from django.contrib.auth.models import User
from editor.models import *
from django.conf import settings


def random_password(N=10):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(N))


if __name__ == '__main__':
    print('Creating {} annotator accounts.'.format(settings.ANNOTATORS))
    users, passwords = [], []
    for i in range(settings.ANNOTATORS):
        password = random_password()
        username = 'annotator00{}'.format(i + 1)
        user =  User.objects.create_user(username=username, password=password)
        users.append(user)
        passwords.append(password)


    paths = glob.glob("modify/*.json")[:100]
    print('Inserting {} verdicts into DB...'.format(len(paths)))
    for i, path in enumerate(tqdm.tqdm(paths)):
        _, filename = path.split('/')
        court_no, year, court_type, verdict_no, date = filename.replace('.json', '').split(',')[:5]
        with open(path) as f:
            verdict = Verdict.objects.create(
                court_no=court_no,
                year=year,
                court_type=court_type,
                verdict_no=verdict_no,
                date=date,
                raw=f.read(),
            )
            Annotation.objects.create(
                author=users[i % settings.ANNOTATORS],
                verdict=verdict,
            )
    with open('accounts.csv', 'w') as csvfile:
        fieldnames = ['username', 'password', 'annotation_ct']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for user, password in zip(users, passwords):
            anno_ct = Annotation.objects.filter(author=user).count()
            writer.writerow({'username': user.username, 'password': password, 'annotation_ct': anno_ct})
    print('Accounts & passwords are saved to `accoints.csv`')