# -*- coding: utf-8 -*-
import json

from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


def sendEmailToken(request, token):
    title = _('PyCon Korea 2018 one-time login token')
    sender = _('PyCon Korea 2018') + '<no-reply@pycon.kr>'
    html = render_to_string('mail/token_html.html', {'token': token}, request)
    text = render_to_string('mail/token_text.html', {'token': token}, request)

    msg = EmailMultiAlternatives(
        title,
        text,
        sender,
        [token.email])
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


def is_pycon_user(email):
    return str.endswith(email, '@pycon.kr')


def render_json(data_dict):
    return HttpResponse(json.dumps(data_dict),
                        'application/javascript')


def render_template_json(template, context):
    return HttpResponse(render_to_string(template, context),
                        'application/javascript')


def render_io_error(reason):
    response = HttpResponse(reason)
    response.status_code = 406
    return response
