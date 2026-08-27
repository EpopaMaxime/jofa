from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from orders.cart import Cart
from recommendations.engine import RecommendationEngine
from recommendations.models import RoutineBundle

from .ai import SkinAnalyzer
from .forms import ConsultationPhotoForm, ConsultationStartForm
from .models import ConsultationPhoto, SkinConsultation


def _get_consultation(request, public_id):
    consultation = get_object_or_404(SkinConsultation, public_id=public_id)
    if request.user.is_staff:
        return consultation
    if consultation.user_id:
        if request.user.is_authenticated and consultation.user_id == request.user.id:
            return consultation
        return None
    if consultation.session_key and consultation.session_key == request.session.session_key:
        return consultation
    return None


class ConsultationLandingView(View):
    template_name = 'consultation/landing.html'

    def get(self, request):
        return render(request, self.template_name)


class ConsultationStartView(FormView):
    template_name = 'consultation/start.html'
    form_class = ConsultationStartForm

    def form_valid(self, form):
        if not self.request.session.session_key:
            self.request.session.create()
        consultation = form.save(commit=False)
        consultation.session_key = self.request.session.session_key or ''
        if self.request.user.is_authenticated:
            consultation.user = self.request.user
        consultation.status = 'draft'
        consultation.save()
        return redirect('consultation:upload', public_id=consultation.public_id)


class ConsultationUploadView(View):
    template_name = 'consultation/upload.html'

    def get(self, request, public_id):
        consultation = _get_consultation(request, public_id)
        if consultation is None:
            messages.error(request, 'Consultation not found or access denied.')
            return redirect('consultation:landing')
        return render(
            request,
            self.template_name,
            {
                'consultation': consultation,
                'form': ConsultationPhotoForm(),
                'photos': consultation.photos.filter(deleted=False),
                'max_photos': getattr(settings, 'CONSULTATION_MAX_PHOTOS', 4),
            },
        )

    def post(self, request, public_id):
        consultation = _get_consultation(request, public_id)
        if consultation is None:
            messages.error(request, 'Consultation not found or access denied.')
            return redirect('consultation:landing')

        action = request.POST.get('action', 'upload')
        form = ConsultationPhotoForm(request.POST, request.FILES)
        pending_files = []
        angle = 'face'
        if form.is_valid():
            pending_files = form.cleaned_data.get('images') or []
            angle = form.cleaned_data.get('angle') or 'face'
        elif request.FILES:
            messages.error(request, 'Some files could not be uploaded. Use JPG, PNG or WEBP images.')
            return redirect('consultation:upload', public_id=public_id)

        existing = consultation.photos.filter(deleted=False).count()
        max_photos = getattr(settings, 'CONSULTATION_MAX_PHOTOS', 4)
        remaining = max(0, max_photos - existing)

        if pending_files:
            if remaining <= 0:
                messages.error(request, f'Maximum {max_photos} photos per consultation.')
            else:
                saved = 0
                for upload in pending_files[:remaining]:
                    ConsultationPhoto.objects.create(
                        consultation=consultation,
                        image=upload,
                        angle=angle,
                    )
                    saved += 1
                skipped = len(pending_files) - saved
                if skipped:
                    messages.warning(
                        request,
                        f'{saved} photo(s) uploaded. {skipped} skipped (limit {max_photos}).',
                    )
                else:
                    messages.success(request, f'{saved} photo(s) uploaded.')

        if action == 'analyze':
            if not consultation.photos.filter(deleted=False).exists():
                messages.error(request, 'Please select at least one photo, then click Upload or Analyze.')
                return redirect('consultation:upload', public_id=public_id)
            consultation.status = 'analyzing'
            consultation.save(update_fields=['status'])
            try:
                SkinAnalyzer().apply_to_consultation(consultation)
                messages.success(request, 'Your AI skin consultation is ready.')
                return redirect('consultation:results', public_id=public_id)
            except Exception as exc:
                consultation.status = 'failed'
                consultation.analysis_summary = str(exc)
                consultation.save(update_fields=['status', 'analysis_summary'])
                messages.error(request, 'Analysis failed. Please try again.')
                return redirect('consultation:upload', public_id=public_id)

        return redirect('consultation:upload', public_id=public_id)


class ConsultationResultsView(DetailView):
    model = SkinConsultation
    slug_field = 'public_id'
    slug_url_kwarg = 'public_id'
    template_name = 'consultation/results.html'
    context_object_name = 'consultation'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if _get_consultation(request, self.object.public_id) is None:
            messages.error(request, 'Consultation not found or access denied.')
            return redirect('consultation:landing')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        engine = RecommendationEngine()
        context['routines'] = engine.routines_for_profile(
            self.object.concern_codes(),
            skin_type=self.object.detected_skin_type,
        )
        context['products'] = list(
            self.object.recommended_products.filter(available=True).prefetch_related(
                'images'
            )
        )
        context['payload'] = self.object.analysis_payload or {}
        return context


class AddRecommendationsToCartView(View):
    def post(self, request, public_id):
        consultation = _get_consultation(request, public_id)
        if consultation is None:
            messages.error(request, 'Consultation not found or access denied.')
            return redirect('consultation:landing')

        cart = Cart(request)
        mode = request.POST.get('mode', 'all')
        added = 0

        if mode == 'routine':
            routine = get_object_or_404(
                RoutineBundle, id=request.POST.get('routine_id'), is_active=True
            )
            for step in routine.steps.select_related('product'):
                if step.product.available:
                    cart.add(step.product, quantity=1)
                    added += 1
        elif mode == 'product':
            product = consultation.recommended_products.filter(
                id=request.POST.get('product_id'), available=True
            ).first()
            if product:
                cart.add(product, quantity=1)
                added = 1
        else:
            for product in consultation.recommended_products.filter(available=True):
                cart.add(product, quantity=1)
                added += 1

        if added:
            messages.success(request, f'{added} product(s) added to your cart.')
            return redirect('orders:cart_detail')
        messages.error(request, 'No products were added.')
        return redirect('consultation:results', public_id=public_id)


class ConsultationHistoryView(LoginRequiredMixin, ListView):
    model = SkinConsultation
    template_name = 'consultation/history.html'
    context_object_name = 'consultations'

    def get_queryset(self):
        return SkinConsultation.objects.filter(user=self.request.user)
