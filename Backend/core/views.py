from django.http import JsonResponse

from .contracts import build_api_contract


def api_root(request):
    return JsonResponse(build_api_contract())


def health_check(request):
    return JsonResponse({"status": "ok"})
