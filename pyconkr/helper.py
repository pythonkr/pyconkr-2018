# -*- coding: utf-8 -*-
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import json


def sendEmailToken(request, token):
    html = render_to_string('mail/token_html.html', {'token': token}, request)
    text = render_to_string('mail/token_text.html', {'token': token}, request)

    msg = EmailMultiAlternatives(
        settings.EMAIL_LOGIN_TITLE,
        text,
        settings.EMAIL_SENDER,
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
