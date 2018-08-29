from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.conf import settings

from .models import Target
from .forms import SiderealTargetCreateForm, NonSiderealTargetCreateForm


class TargetListView(FilterView):
    template_name = 'tom_targets/target_list.html'
    paginate_by = 25
    model = Target
    filterset_fields = ['type', 'identifier', 'name', 'designation']


class TargetCreate(CreateView):
    model = Target
    fields = '__all__'

    def get_default_target_type(self):
        try:
            return settings.DEFAULT_TARGET_TYPE
        except AttributeError:
            return Target.SIDEREAL

    def get_initial(self):
        return {'type': self.get_default_target_type(), **dict(self.request.GET.items())}

    def get_context_data(self, **kwargs):
        context = super(TargetCreate, self).get_context_data(**kwargs)
        context['type_choices'] = Target.TARGET_TYPES
        return context

    def get_form_class(self):
        target_type = self.get_default_target_type()
        if self.request.GET:
            target_type = self.request.GET.get('type', target_type)
        elif self.request.POST:
            target_type = self.request.POST.get('type', target_type)
        if target_type == Target.SIDEREAL:
            self.initial['type'] = Target.SIDEREAL
            return SiderealTargetCreateForm
        elif target_type == Target.NON_SIDEREAL:
            self.initial['type'] = Target.NON_SIDEREAL
            return NonSiderealTargetCreateForm


class TargetUpdate(UpdateView):
    model = Target
    fields = '__all__'


class TargetDelete(DeleteView):
    success_url = reverse_lazy('targets:list')
    model = Target


class TargetDetail(DetailView):
    model = Target
    fields = '__all__'