from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ai_processing.models import VideoAnalysis, AnalysisProvider, Brand


@require_http_methods(["GET"])
def stream_analysis(request, stream_id):
    analyses = VideoAnalysis.objects.filter(stream_id=stream_id).order_by('-timestamp')
    return JsonResponse({'results': [a.to_dict() for a in analyses]})


@require_http_methods(["GET"]) 
def providers(request):
    providers = AnalysisProvider.objects.filter(active=True)
    return JsonResponse({
        'providers': [
            {'id': str(p.id), 'name': p.name, 'capabilities': p.capabilities} 
            for p in providers
        ]
    })


@require_http_methods(["GET"])
def brands(request):
    brands = Brand.objects.filter(active=True) 
    return JsonResponse({
        'brands': [
            {'id': str(b.id), 'name': b.name, 'category': b.category}
            for b in brands
        ]
    })
