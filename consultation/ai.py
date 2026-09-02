"""
AI skin analysis — Google Gemini vision only.

Images are required. There is no questionnaire-only or heuristic fallback:
if Gemini is missing, blocked, or errors, the consultation fails and the
raw error is logged.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from recommendations.engine import RecommendationEngine
from recommendations.models import ConcernProductMap, SkinConcern

logger = logging.getLogger('consultation.ai')

USER_UNAVAILABLE = (
    'The AI consultant is currently unavailable. Please try again in a few minutes.'
)


class SkinAnalysisUnavailable(Exception):
    def __init__(self, user_message=USER_UNAVAILABLE, *, details=None):
        super().__init__(user_message)
        self.user_message = user_message
        self.details = details or {}


class SkinAnalyzer:
    def analyze(self, consultation) -> dict:
        api_key = (getattr(settings, 'GEMINI_API_KEY', '') or '').strip()
        if not api_key:
            logger.error('GEMINI_API_KEY is not configured; cannot analyze photos.')
            raise SkinAnalysisUnavailable(
                USER_UNAVAILABLE,
                details={'reason': 'missing_api_key'},
            )
        return self._analyze_gemini(consultation)

    def apply_to_consultation(self, consultation) -> None:
        result = self.analyze(consultation)
        allowed = set(
            SkinConcern.objects.filter(is_active=True).values_list('code', flat=True)
        )
        codes = [
            code
            for code in result.get('concern_codes') or []
            if isinstance(code, str) and code in allowed
        ]
        if not codes:
            logger.error(
                'Gemini returned no valid concern codes. payload=%s',
                result,
            )
            raise SkinAnalysisUnavailable(
                USER_UNAVAILABLE,
                details={
                    'reason': 'invalid_concerns',
                    'raw_concern_codes': result.get('concern_codes'),
                    'gemini_payload': result,
                },
            )

        skin_type = result.get('skin_type') or consultation.declared_skin_type or 'all'
        if skin_type not in {'dry', 'oily', 'sensitive', 'combination', 'all'}:
            skin_type = consultation.declared_skin_type or 'all'

        engine = RecommendationEngine()
        mapped_products = engine.products_for_concerns(codes, skin_type=skin_type)
        products = self._intersect_ai_products(
            mapped_products, result.get('product_ids') or []
        )

        consultation.status = 'ready'
        consultation.detected_skin_type = skin_type
        consultation.analysis_summary = result.get('summary') or (
            'We analysed your photos and matched JOFA products to the concerns we found.'
        )
        consultation.analysis_payload = result
        raw_confidence = float(result.get('confidence') or 0)
        consultation.confidence_score = (
            raw_confidence * 100 if raw_confidence <= 1 else raw_confidence
        )
        consultation.analyzer_backend = result.get('backend', 'gemini')
        consultation.analyzed_at = timezone.now()
        consultation.save()

        consultation.concerns.set(
            SkinConcern.objects.filter(code__in=codes, is_active=True)
        )
        consultation.recommended_products.set(products)

        if not consultation.consent_image_retention:
            self._purge_photos(consultation)

    def _intersect_ai_products(self, mapped_products, ai_product_ids):
        mapped_by_id = {p.id: p for p in mapped_products}
        ordered = []
        seen = set()
        for raw in ai_product_ids:
            try:
                pid = int(raw)
            except (TypeError, ValueError):
                continue
            product = mapped_by_id.get(pid)
            if product and pid not in seen:
                ordered.append(product)
                seen.add(pid)
        if ordered:
            return ordered
        return mapped_products

    def _purge_photos(self, consultation) -> None:
        for photo in consultation.photos.filter(deleted=False):
            if photo.image:
                photo.image.delete(save=False)
            photo.deleted = True
            photo.save(update_fields=['deleted'])

    def _catalog_for_prompt(self):
        maps = (
            ConcernProductMap.objects.filter(is_active=True, product__available=True)
            .select_related('product', 'concern', 'product__category')
            .order_by('priority', 'id')
        )
        by_product = {}
        for mapping in maps:
            entry = by_product.setdefault(
                mapping.product_id,
                {
                    'id': mapping.product_id,
                    'name': mapping.product.name,
                    'skin_type': mapping.product.skin_type,
                    'category': mapping.product.category.name
                    if mapping.product.category_id
                    else '',
                    'concerns': [],
                },
            )
            if mapping.concern.code not in entry['concerns']:
                entry['concerns'].append(mapping.concern.code)
        return list(by_product.values())

    def _prompt_text(self, consultation) -> str:
        concern_catalog = list(
            SkinConcern.objects.filter(is_active=True).values(
                'code', 'name', 'description'
            )
        )
        product_catalog = self._catalog_for_prompt()
        return (
            'You are a cosmetic dermatology assistant for JOFA skincare. '
            'You MUST visually inspect every attached skin photo before answering. '
            'Do not invent findings that are not visible. '
            'Do not recommend products that do not match the visible concerns. '
            'Questionnaire context is secondary to the photos.\n'
            'Respond ONLY with valid JSON:\n'
            '{'
            '"skin_type":"dry|oily|sensitive|combination|all",'
            '"concern_codes":["code",...],'
            '"product_ids":[1,2],'
            '"confidence":0.0-1.0,'
            '"summary":"2-4 sentences for the customer about what you saw on the photos",'
            '"concerns_detail":[{"code":"","label":"","severity":"low|medium|high","notes":""}],'
            '"photo_quality":"good|fair|poor"'
            '}\n'
            'Rules:\n'
            '- concern_codes: only from the allowed list, only what the photos support.\n'
            '- product_ids: only ids from the catalog below, and only products whose '
            '"concerns" overlap concern_codes. Maximum 6 products. Never pad with unrelated items.\n'
            '- If photos are too blurry or not of skin, set photo_quality to poor, '
            'confidence below 0.4, and an empty product_ids list.\n'
            f'Allowed concerns: {json.dumps(concern_catalog)}\n'
            f'Catalog: {json.dumps(product_catalog)}\n'
            f'Declared skin type (secondary): {consultation.declared_skin_type or "unknown"}\n'
            f'Age range: {consultation.age_range or "unknown"}\n'
            f'Goals (secondary): {consultation.primary_goals or "none"}\n'
            f'Sensitivity 1-5: {consultation.sensitivity_level}\n'
            'Do not diagnose medical conditions.'
        )

    def _load_photo_images(self, consultation):
        from PIL import Image

        images = []
        errors = []
        for photo in consultation.photos.filter(deleted=False)[:4]:
            if not photo.image:
                continue
            path = Path(photo.image.path)
            if not path.exists():
                errors.append(f'missing file {path}')
                continue
            try:
                img = Image.open(path)
                img = img.convert('RGB')
                images.append(img)
            except Exception as exc:
                errors.append(f'{path}: {exc}')
        return images, errors

    def _gemini_response_dump(self, response) -> dict:
        dump = {}
        try:
            dump['text'] = getattr(response, 'text', None)
        except Exception as exc:
            dump['text_error'] = str(exc)
        prompt_feedback = getattr(response, 'prompt_feedback', None)
        if prompt_feedback is not None:
            dump['prompt_feedback'] = str(prompt_feedback)
        candidates = getattr(response, 'candidates', None)
        if candidates:
            dump['candidates'] = [str(c) for c in candidates[:3]]
        return dump

    def _analyze_gemini(self, consultation) -> dict:
        import google.generativeai as genai

        images, load_errors = self._load_photo_images(consultation)
        if load_errors:
            logger.warning('Some consultation photos could not be opened: %s', load_errors)
        if not images:
            logger.error(
                'No readable photos for consultation %s. errors=%s',
                consultation.public_id,
                load_errors,
            )
            raise SkinAnalysisUnavailable(
                'We could not read the uploaded photos. Please upload a clear face photo and try again.',
                details={'reason': 'no_readable_photos', 'errors': load_errors},
            )

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        model = genai.GenerativeModel(model_name)
        parts = [self._prompt_text(consultation), *images]
        generation_config = {
            'temperature': 0.1,
            'max_output_tokens': 2048,
            'response_mime_type': 'application/json',
        }
        try:
            response = model.generate_content(parts, generation_config=generation_config)
        except Exception as exc:
            logger.exception(
                'Gemini request failed for consultation %s: %s',
                consultation.public_id,
                exc,
            )
            details = {'reason': 'gemini_request_error', 'error': str(exc)}
            api_response = getattr(exc, 'message', None) or getattr(exc, 'args', None)
            if api_response:
                details['gemini_error_message'] = str(api_response)[:4000]
            raw = getattr(exc, 'response', None)
            if raw is not None:
                details['gemini_http_response'] = str(
                    getattr(raw, 'text', None) or raw
                )[:4000]
            raise SkinAnalysisUnavailable(
                USER_UNAVAILABLE,
                details=details,
            ) from exc
        finally:
            for img in images:
                try:
                    img.close()
                except Exception:
                    pass

        dump = self._gemini_response_dump(response)
        text = (dump.get('text') or '').strip()
        if not text:
            logger.error(
                'Empty Gemini response for consultation %s: %s',
                consultation.public_id,
                dump,
            )
            raise SkinAnalysisUnavailable(
                USER_UNAVAILABLE,
                details={'reason': 'empty_gemini_response', 'gemini_response': dump},
            )

        try:
            data = self._extract_json(text)
        except Exception as exc:
            logger.error(
                'Invalid Gemini JSON for consultation %s: %s raw=%s dump=%s',
                consultation.public_id,
                exc,
                text[:4000],
                dump,
            )
            raise SkinAnalysisUnavailable(
                USER_UNAVAILABLE,
                details={
                    'reason': 'invalid_gemini_json',
                    'error': str(exc),
                    'raw_text': text[:4000],
                    'gemini_response': dump,
                },
            ) from exc

        if (data.get('photo_quality') or '').lower() == 'poor':
            logger.warning(
                'Gemini reported poor photo quality for %s: %s',
                consultation.public_id,
                data,
            )
            raise SkinAnalysisUnavailable(
                'The photos are not clear enough for a reliable skin analysis. '
                'Please upload a well-lit, in-focus photo of your face and try again.',
                details={'reason': 'poor_photo_quality', 'gemini_payload': data},
            )

        data['backend'] = 'gemini'
        data['model'] = model_name
        data.setdefault('concern_codes', [])
        data.setdefault('product_ids', [])
        data.setdefault('confidence', 0.0)
        logger.info(
            'Gemini analysis ok consultation=%s skin_type=%s concerns=%s product_ids=%s',
            consultation.public_id,
            data.get('skin_type'),
            data.get('concern_codes'),
            data.get('product_ids'),
        )
        return data

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                raise
            parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise ValueError('Gemini JSON was not an object')
        return parsed
