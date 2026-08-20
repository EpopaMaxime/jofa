"""
AI skin analysis backends.

- Google Gemini vision when GEMINI_API_KEY is configured
- Deterministic heuristic fallback so the feature always works offline
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from recommendations.engine import RecommendationEngine
from recommendations.models import SkinConcern


class SkinAnalyzer:
    def analyze(self, consultation) -> dict:
        if getattr(settings, 'GEMINI_API_KEY', ''):
            try:
                return self._analyze_gemini(consultation)
            except Exception as exc:
                result = self._analyze_heuristic(consultation)
                result['fallback_reason'] = str(exc)
                result['backend'] = 'heuristic_fallback'
                return result
        return self._analyze_heuristic(consultation)

    def apply_to_consultation(self, consultation) -> None:
        result = self.analyze(consultation)
        consultation.status = 'ready'
        consultation.detected_skin_type = (
            result.get('skin_type', '') or consultation.declared_skin_type
        )
        consultation.analysis_summary = result.get('summary', '')
        consultation.analysis_payload = result
        raw_confidence = float(result.get('confidence', 0.7))
        consultation.confidence_score = (
            raw_confidence * 100 if raw_confidence <= 1 else raw_confidence
        )
        consultation.analyzer_backend = result.get('backend', 'heuristic')
        consultation.analyzed_at = timezone.now()
        consultation.save()

        codes = result.get('concern_codes', [])
        concerns = SkinConcern.objects.filter(code__in=codes, is_active=True)
        consultation.concerns.set(concerns)

        engine = RecommendationEngine()
        payload = engine.build_payload(codes, skin_type=consultation.detected_skin_type)
        consultation.recommended_products.set(payload['products'])

        if not consultation.consent_image_retention:
            self._purge_photos(consultation)

    def _purge_photos(self, consultation) -> None:
        for photo in consultation.photos.filter(deleted=False):
            if photo.image:
                photo.image.delete(save=False)
            photo.deleted = True
            photo.save(update_fields=['deleted'])

    def _prompt_text(self, consultation) -> str:
        concern_catalog = list(
            SkinConcern.objects.filter(is_active=True).values(
                'code', 'name', 'description'
            )
        )
        return (
            'You are a cosmetic dermatology assistant for JOFA skincare. '
            'Analyze the skin photo(s) and questionnaire. '
            'Respond ONLY with valid JSON matching this schema:\n'
            '{'
            '"skin_type":"dry|oily|sensitive|combination|all",'
            '"concern_codes":["code",...],'
            '"confidence":0.0-1.0,'
            '"summary":"2-4 sentences for the customer",'
            '"concerns_detail":[{"code":"","label":"","severity":"low|medium|high","notes":""}]'
            '}\n'
            f'Allowed concern codes: {json.dumps(concern_catalog)}\n'
            f'Declared skin type: {consultation.declared_skin_type or "unknown"}\n'
            f'Age range: {consultation.age_range or "unknown"}\n'
            f'Goals: {consultation.primary_goals or "none"}\n'
            f'Sensitivity 1-5: {consultation.sensitivity_level}\n'
            'Do not diagnose medical conditions. Keep advice general skincare.'
        )

    # ------------------------------------------------------------------ gemini
    def _analyze_gemini(self, consultation) -> dict:
        import google.generativeai as genai
        from PIL import Image

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        model = genai.GenerativeModel(model_name)

        parts: list = [self._prompt_text(consultation)]
        for photo in consultation.photos.filter(deleted=False)[:3]:
            if not photo.image:
                continue
            path = Path(photo.image.path)
            if not path.exists():
                continue
            parts.append(Image.open(path))

        generation_config = {
            'temperature': 0.2,
            'max_output_tokens': 1024,
            'response_mime_type': 'application/json',
        }
        response = model.generate_content(parts, generation_config=generation_config)
        text = (getattr(response, 'text', None) or '').strip() or '{}'
        data = self._extract_json(text)
        data['backend'] = 'gemini'
        data['model'] = model_name
        data.setdefault('concern_codes', [])
        data.setdefault('confidence', 0.75)
        data.setdefault('summary', 'Analysis complete.')
        return data

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

    # -------------------------------------------------------------- heuristic
    def _analyze_heuristic(self, consultation) -> dict:
        text_blob = ' '.join(
            [
                consultation.primary_goals or '',
                consultation.declared_skin_type or '',
                consultation.age_range or '',
            ]
        ).lower()

        concerns = list(SkinConcern.objects.filter(is_active=True))
        scored = []
        for concern in concerns:
            score = 0
            for kw in concern.keyword_list():
                if kw and kw in text_blob:
                    score += 2 + concern.severity_weight
            if consultation.sensitivity_level >= 4 and concern.code in {
                'sensitivity',
                'redness',
                'barrier',
            }:
                score += 3
            if score:
                scored.append((score, concern))

        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            defaults = {
                'dry': ['dehydration', 'dullness'],
                'oily': ['acne', 'excess-oil'],
                'sensitive': ['sensitivity', 'redness'],
                'combination': ['uneven-tone', 'dehydration'],
                'all': ['dullness', 'dehydration'],
                '': ['dullness', 'dehydration'],
            }
            codes = defaults.get(consultation.declared_skin_type, ['dullness'])
            selected = list(
                SkinConcern.objects.filter(code__in=codes, is_active=True)[:3]
            )
        else:
            selected = [c for _, c in scored[:3]]

        skin_type = consultation.declared_skin_type or 'all'
        if consultation.sensitivity_level >= 4:
            skin_type = 'sensitive'

        has_photos = consultation.photos.filter(deleted=False).exists()
        confidence = 0.82 if has_photos and scored else 0.68 if scored else 0.55

        labels = ', '.join(c.name for c in selected) or 'general glow support'
        summary = (
            f'Based on your questionnaire{" and uploaded photos" if has_photos else ""}, '
            f'we identified a focus on {labels}. '
            f'Your profile leans toward {skin_type or "balanced"} skin. '
            'Below is a personalized JOFA routine built from products in our catalog. '
            'This is cosmetic guidance only — not a medical diagnosis.'
        )

        return {
            'backend': 'heuristic',
            'skin_type': skin_type or 'all',
            'concern_codes': [c.code for c in selected],
            'confidence': confidence,
            'summary': summary,
            'concerns_detail': [
                {
                    'code': c.code,
                    'label': c.name,
                    'severity': 'medium',
                    'notes': c.description[:180],
                }
                for c in selected
            ],
        }
