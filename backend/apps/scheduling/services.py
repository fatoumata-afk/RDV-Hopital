"""Génération et interrogation des créneaux.

Les créneaux sont matérialisés en base à la demande, à partir des horaires
récurrents du médecin, en excluant les indisponibilités. Cette matérialisation
permet de poser un verrou en base lors de la réservation et donc d'éviter
toute double réservation concurrente.
"""

from datetime import date as date_cls
from datetime import datetime, timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import DoctorSchedule, Slot, SlotStatus, TimeOff


def _iter_schedule_times(schedule):
    current = datetime.combine(date_cls.min, schedule.start_time)
    end = datetime.combine(date_cls.min, schedule.end_time)
    step = timedelta(minutes=schedule.slot_duration)
    while current + step <= end:
        yield current.time(), (current + step).time()
        current += step


def _to_aware(day, time_value):
    return timezone.make_aware(datetime.combine(day, time_value), timezone.get_current_timezone())


def _overlaps_time_off(doctor_time_off, start_dt, end_dt):
    return any(
        off.start_datetime < end_dt and start_dt < off.end_datetime for off in doctor_time_off
    )


@transaction.atomic
def generate_slots(doctor, start_date, end_date):
    """Matérialise les créneaux manquants du médecin sur la période demandée."""
    horizon = timezone.localdate() + timedelta(days=settings.SLOT_GENERATION_HORIZON_DAYS)
    end_date = min(end_date, horizon)
    if end_date < start_date:
        return []

    schedules = list(doctor.schedules.filter(is_active=True))
    if not schedules:
        return []

    time_off = list(
        TimeOff.objects.filter(
            doctor=doctor,
            end_datetime__gte=_to_aware(start_date, datetime.min.time()),
            start_datetime__lte=_to_aware(end_date, datetime.max.time()),
        )
    )
    existing = set(
        Slot.objects.filter(doctor=doctor, date__gte=start_date, date__lte=end_date).values_list(
            "date", "start_time"
        )
    )

    now = timezone.now()
    new_slots = []
    day = start_date
    while day <= end_date:
        for schedule in schedules:
            if not schedule.covers(day):
                continue
            for start_time, end_time in _iter_schedule_times(schedule):
                if (day, start_time) in existing:
                    continue
                start_dt = _to_aware(day, start_time)
                if start_dt <= now:
                    continue
                blocked = _overlaps_time_off(time_off, start_dt, _to_aware(day, end_time))
                new_slots.append(
                    Slot(
                        doctor=doctor,
                        date=day,
                        start_time=start_time,
                        end_time=end_time,
                        status=SlotStatus.BLOCKED if blocked else SlotStatus.AVAILABLE,
                        generated_from=schedule,
                    )
                )
                existing.add((day, start_time))
        day += timedelta(days=1)

    if new_slots:
        try:
            Slot.objects.bulk_create(new_slots, ignore_conflicts=True)
        except IntegrityError:  # pragma: no cover - sécurité supplémentaire
            pass
    return new_slots


def available_slots(doctor, start_date, end_date):
    """Créneaux réellement réservables, après génération à la demande."""
    generate_slots(doctor, start_date, end_date)
    now = timezone.now()
    slots = Slot.objects.filter(
        doctor=doctor,
        date__gte=start_date,
        date__lte=end_date,
        status=SlotStatus.AVAILABLE,
    ).order_by("date", "start_time")
    return [slot for slot in slots if _to_aware(slot.date, slot.start_time) > now]


def available_days(doctor, start_date, end_date):
    """Dates comportant au moins un créneau libre (pour le calendrier patient)."""
    days = {}
    for slot in available_slots(doctor, start_date, end_date):
        days[slot.date] = days.get(slot.date, 0) + 1
    return [{"date": day, "slots_count": count} for day, count in sorted(days.items())]


def apply_time_off(time_off):
    """Bloque les créneaux libres couverts par une nouvelle indisponibilité."""
    Slot.objects.filter(
        doctor=time_off.doctor,
        status=SlotStatus.AVAILABLE,
        date__gte=timezone.localtime(time_off.start_datetime).date(),
        date__lte=timezone.localtime(time_off.end_datetime).date(),
    ).update(status=SlotStatus.BLOCKED)


def release_time_off(time_off):
    """Libère les créneaux bloqués non réservés lors de la suppression d'un blocage."""
    Slot.objects.filter(
        doctor=time_off.doctor,
        status=SlotStatus.BLOCKED,
        date__gte=timezone.localtime(time_off.start_datetime).date(),
        date__lte=timezone.localtime(time_off.end_datetime).date(),
    ).update(status=SlotStatus.AVAILABLE)


__all__ = [
    "generate_slots",
    "available_slots",
    "available_days",
    "apply_time_off",
    "release_time_off",
    "DoctorSchedule",
]
