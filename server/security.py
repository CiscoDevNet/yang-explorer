import logging
from django.shortcuts import render_to_response
from django.template import RequestContext

def policy_handler(request):
    return render_to_response('crossdomain.xml', {}, RequestContext(request))
