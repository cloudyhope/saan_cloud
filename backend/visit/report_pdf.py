"""Deterministic Persian PDF for a captured client-facing visit report."""
from io import BytesIO
from pathlib import Path
import hashlib
import json

import arabic_reshaper
from bidi.algorithm import get_display
from django.conf import settings
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from visit.client_visit_detail import scoped_client_visit
from visit.models import Visit


FONT_NAME = 'SaanPersianReport'
FONT_PATH = Path(settings.BASE_DIR) / 'visit' / 'fonts' / 'IRANYekanRegularFaNum.ttf'


def _font():
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))
    return FONT_NAME


def _visual(value):
    return get_display(arabic_reshaper.reshape(str(value)), base_dir='R')


def _wrapped(value, width, font, size):
    text = str(value or '').replace('\r', '')
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split()
        if not words:
            lines.append('')
            continue
        current = ''
        for word in words:
            if pdfmetrics.stringWidth(_visual(word), font, size) > width:
                if current:
                    lines.append(current)
                    current = ''
                fragment = ''
                for char in word:
                    candidate = fragment + char
                    if fragment and pdfmetrics.stringWidth(_visual(candidate), font, size) > width:
                        lines.append(fragment)
                        fragment = char
                    else:
                        fragment = candidate
                current = fragment
                continue
            candidate = (current + ' ' + word).strip()
            if current and pdfmetrics.stringWidth(_visual(candidate), font, size) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def _answer_text(answer):
    values = [answer.get('dropdown'), answer.get('radio'),
              *(answer.get('multichoice') or []), answer.get('text'), answer.get('description')]
    if answer.get('number') is not None:
        values.append(str(answer['number']))
    if answer.get('score') is not None:
        values.append(f"{answer['score']} از 5")
    if answer.get('price') is not None:
        values.append(f"{answer['price']:,} ریال")
    if answer.get('bool') is True:
        values.append('بله')
    elif answer.get('bool') is False:
        values.append('خیر')
    return '، '.join(str(value) for value in values if value is not None and str(value).strip()) or 'پاسخی ثبت نشده'


def render_report_pdf(snapshot):
    payload = snapshot.payload
    expected = hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                         sort_keys=True).encode('utf-8')).hexdigest()
    if expected != snapshot.checksum or payload.get('visit_id') != snapshot.visit_id:
        raise ValueError('Report snapshot checksum mismatch')
    font = _font()
    output = BytesIO()
    page = canvas.Canvas(output, pagesize=A4, invariant=1, pageCompression=1)
    page.setTitle(f'Saan service report {snapshot.visit_id} v{snapshot.version}')
    page.setAuthor('Saan App')
    width, height = A4
    margin, right = 42, width - 42
    page_number = 0

    def start_page():
        nonlocal page_number
        if page_number:
            page.showPage()
        page_number += 1
        page.setFillColor(colors.HexColor('#143d59'))
        page.rect(0, height - 108, width, 108, stroke=0, fill=1)
        page.setFont(font, 20)
        page.setFillColor(colors.white)
        page.drawRightString(right, height - 53, _visual('گزارش خدمت سان اپ'))
        page.setFont(font, 9)
        page.setFillColor(colors.HexColor('#d9eef5'))
        page.drawRightString(right, height - 78, _visual('نسخه ثابت پاسخ‌های ثبت‌شده'))
        page.setStrokeColor(colors.HexColor('#dbe8ef'))
        page.line(margin, 52, right, 52)
        page.setFillColor(colors.HexColor('#567486'))
        page.setFont(font, 8)
        page.drawRightString(right, 36, _visual(f'صفحه {page_number}'))
        page.drawString(margin, 36, f'SHA-256 {snapshot.checksum[:16]}')
        return height - 135

    y = start_page()
    page.setFillColor(colors.HexColor('#f1f7f9'))
    page.roundRect(margin, y - 78, width - 2 * margin, 78, 12, stroke=0, fill=1)
    page.setFont(font, 10)
    page.setFillColor(colors.HexColor('#19465e'))
    page.drawRightString(right - 15, y - 25, _visual(f'کد خدمت: {snapshot.visit_id}'))
    page.drawRightString(right - 15, y - 48, _visual(f'نسخه گزارش: {snapshot.version}'))
    captured = str(payload.get('captured_at') or snapshot.created_at.isoformat())[:19].replace('T', ' ')
    page.drawRightString(right - 15, y - 69, _visual(f'زمان ثبت: {captured}'))
    y -= 109
    answers = payload.get('answers') or []
    if not answers:
        answers = [{'question': 'نتیجه خدمت', 'text': 'پاسخی برای این گزارش ثبت نشده است.'}]
    for index, answer in enumerate(answers, 1):
        question = f'{index}. {answer.get("question") or "سؤال بدون عنوان"}'
        question_lines = _wrapped(question, width - 2 * margin - 28, font, 10)
        value_lines = _wrapped(_answer_text(answer), width - 2 * margin - 28, font, 9)
        remaining = [(line, 10, 18, '#173e57') for line in question_lines]
        remaining += [(line, 9, 17, '#416476') for line in value_lines]
        continuation = False
        while remaining:
            heading = [('ادامه پاسخ ' + str(index), 9, 17, '#2d7187')] if continuation else []
            full_height = 24 + sum(row[2] for row in heading + remaining)
            if y - full_height < 72 and full_height <= height - 135 - 72:
                y = start_page()
            if y < 150:
                y = start_page()
            selected = list(heading)
            while remaining and 24 + sum(row[2] for row in selected) + remaining[0][2] <= y - 72:
                selected.append(remaining.pop(0))
            if not selected or selected == heading:
                y = start_page()
                continue
            card_height = 24 + sum(row[2] for row in selected)
            page.setFillColor(colors.white)
            page.setStrokeColor(colors.HexColor('#dce8ee'))
            page.roundRect(margin, y - card_height, width - 2 * margin, card_height, 10, stroke=1, fill=1)
            line_y = y - 19
            for line, size, leading, color in selected:
                page.setFont(font, size)
                page.setFillColor(colors.HexColor(color))
                page.drawRightString(right - 14, line_y, _visual(line))
                line_y -= leading
            y -= card_height + 11
            continuation = True
    def text_block(heading, text, continuation_label):
        nonlocal y
        title_lines = _wrapped(heading, width - 2 * margin - 28, font, 10)
        value_lines = _wrapped(text, width - 2 * margin - 28, font, 9)
        remaining = [(line, 10, 18, '#173e57') for line in title_lines]
        remaining += [(line, 9, 17, '#416476') for line in value_lines]
        continuation = False
        while remaining:
            header_items = [(continuation_label, 9, 17, '#2d7187')] if continuation else []
            full_height = 24 + sum(row[2] for row in header_items + remaining)
            if y - full_height < 72 and full_height <= height - 135 - 72:
                y = start_page()
            if y < 150:
                y = start_page()
            selected = list(header_items)
            while remaining and 24 + sum(row[2] for row in selected) + remaining[0][2] <= y - 72:
                selected.append(remaining.pop(0))
            if not selected or selected == header_items:
                y = start_page()
                continue
            card_height = 24 + sum(row[2] for row in selected)
            page.setFillColor(colors.white)
            page.setStrokeColor(colors.HexColor('#dce8ee'))
            page.roundRect(margin, y - card_height, width - 2 * margin, card_height, 10, stroke=1, fill=1)
            line_y = y - 19
            for line, size, leading, color in selected:
                page.setFont(font, size)
                page.setFillColor(colors.HexColor(color))
                page.drawRightString(right - 14, line_y, _visual(line))
                line_y -= leading
            y -= card_height + 11
            continuation = True

    parts = payload.get('parts') or []
    if parts:
        labels = [f'{i}. {p.get("name") or "قطعه"}: {p.get("amount")} {p.get("unit") or "عدد"}'
                  for i, p in enumerate(parts, 1)]
        text_block(f'قطعات تأمین‌شده برای این خدمت ({len(parts)} مورد)', '\n'.join(labels), 'ادامه قطعات')
    wage = payload.get('wage')
    if wage:
        text_block('اجرت خدمت', f'{int(wage):,} ریال', 'ادامه اجرت')
    photos = payload.get('photos') or []
    if photos:
        photo_labels = [f'{i}. {p.get("type_name") or "تصویر خدمت"}' for i, p in enumerate(photos, 1)]
        text_block(f'مدارک تصویری ثبت‌شده خدمت ({len(photos)} مورد)', '  ·  '.join(photo_labels),
                   'ادامه مدارک تصویری')
    page.save()
    output.seek(0)
    return output


class ClientVisitReportPDFAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        visit = scoped_client_visit(request, self, id)
        if visit is None:
            return Response({'detail': 'دسترسی به گزارش مجاز نیست.'}, status=403)
        if visit.status not in (Visit.COMPLETED, Visit.APPROVED):
            return Response({'detail': 'گزارش هنوز آماده نیست.'}, status=409)
        snapshot = visit.report_snapshots.order_by('-version').first()
        if snapshot is None:
            return Response({'detail': 'این گزارش قدیمی نسخه ثابت برای دریافت ندارد.'}, status=409)
        try:
            output = render_report_pdf(snapshot)
        except ValueError:
            return Response({'detail': 'نسخه ثابت گزارش معتبر نیست.'}, status=409)
        response = FileResponse(output, as_attachment=True,
                                filename=f'saan-visit-{visit.pk}-v{snapshot.version}.pdf',
                                content_type='application/pdf')
        response['Cache-Control'] = 'private, no-store'
        return response
