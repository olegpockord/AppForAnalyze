from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.template.response import TemplateResponse

class IndexView(TemplateView):
    template_name = "main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "index"
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)
