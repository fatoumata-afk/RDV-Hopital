"""Jeu de données de démonstration.

Cette commande est volontairement isolée du code applicatif : elle n'utilise que
les services métier publics et n'est importée nulle part ailleurs. L'application
fonctionne intégralement sans elle.

    python manage.py seed_demo [--reset]
"""

from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import DoctorProfile, User, UserRole
from apps.accounts.services import create_staff_user, register_patient
from apps.appointments.services import book_appointment
from apps.organization.models import Department, Room, Specialty
from apps.scheduling.models import DoctorSchedule
from apps.scheduling.services import available_slots

DEMO_PASSWORD = "Demo2026!hopital"

SPECIALTIES = [
    ("Cardiologie", "Maladies du cœur et des vaisseaux."),
    ("Neurologie", "Système nerveux central et périphérique."),
    ("Pédiatrie", "Suivi médical des enfants."),
    ("Dermatologie", "Maladies de la peau."),
    ("Ophtalmologie", "Santé de la vision."),
    ("Médecine générale", "Consultations générales et orientation."),
]

DEPARTMENTS = [
    ("Cardiologie", "CARD", "Bâtiment B", "2e étage"),
    ("Neurologie", "NEUR", "Bâtiment C", "1er étage"),
    ("Pédiatrie", "PEDI", "Bâtiment A", "Rez-de-chaussée"),
    ("Dermatologie", "DERM", "Bâtiment A", "1er étage"),
    ("Consultations externes", "CONS", "Bâtiment A", "Rez-de-chaussée"),
]

ROOMS = [
    ("Cardiologie", ["B-201", "B-204", "B-210"]),
    ("Neurologie", ["C-105", "C-108"]),
    ("Pédiatrie", ["A-012", "A-015"]),
    ("Dermatologie", ["A-110"]),
    ("Consultations externes", ["A-001", "A-002"]),
]

DOCTORS = [
    ("Amadou", "Diallo", "Cardiologie", "Cardiologie", "B-204"),
    ("Fatoumata", "Bah", "Neurologie", "Neurologie", "C-105"),
    ("Mariama", "Sow", "Pédiatrie", "Pédiatrie", "A-012"),
    ("Ibrahima", "Camara", "Dermatologie", "Dermatologie", "A-110"),
    ("Aissatou", "Barry", "Médecine générale", "Consultations externes", "A-001"),
    ("Ousmane", "Keita", "Cardiologie", "Cardiologie", "B-201"),
]

PATIENTS = [
    ("Awa", "Traoré", "awa.traore@demo.test"),
    ("Moussa", "Konaté", "moussa.konate@demo.test"),
    ("Kadiatou", "Diop", "kadiatou.diop@demo.test"),
]


class Command(BaseCommand):
    help = "Crée un jeu de données de démonstration (comptes, services, rendez-vous)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime les comptes de démonstration existants avant de recréer.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            User.objects.filter(email__endswith="@demo.test").delete()
            self.stdout.write("Comptes de démonstration supprimés.")

        specialties = {
            name: Specialty.objects.get_or_create(name=name, defaults={"description": description})[
                0
            ]
            for name, description in SPECIALTIES
        }
        departments = {}
        for name, code, building, floor in DEPARTMENTS:
            departments[name] = Department.objects.get_or_create(
                code=code,
                defaults={"name": name, "building": building, "floor": floor},
            )[0]
        rooms = {}
        for department_name, codes in ROOMS:
            for code in codes:
                rooms[code] = Room.objects.get_or_create(
                    department=departments[department_name], code=code
                )[0]

        admin = self._get_or_create_user(
            role=UserRole.ADMIN,
            email="admin@demo.test",
            first_name="Awa",
            last_name="Administratrice",
        )
        self._get_or_create_user(
            role=UserRole.AGENT,
            email="accueil@demo.test",
            first_name="Salif",
            last_name="Accueil",
            badge_number="AG-001",
            department_id=departments["Consultations externes"].id,
        )

        doctors = []
        for index, (first, last, specialty, department, room) in enumerate(DOCTORS, start=1):
            email = f"dr.{last.lower()}@demo.test"
            user = self._get_or_create_user(
                role=UserRole.DOCTOR,
                email=email,
                first_name=first,
                last_name=last,
                license_number=f"ORD-{1000 + index}",
                specialty_id=specialties[specialty].id,
                department_id=departments[department].id,
                room_id=rooms[room].id,
            )
            doctors.append(user.doctor_profile)

        today = timezone.localdate()
        for doctor in doctors:
            for weekday in range(0, 5):
                DoctorSchedule.objects.get_or_create(
                    doctor=doctor,
                    weekday=weekday,
                    start_time=time(9, 0),
                    defaults={
                        "end_time": time(13, 0),
                        "slot_duration": doctor.default_slot_duration,
                        "valid_from": today - timedelta(days=1),
                    },
                )
                DoctorSchedule.objects.get_or_create(
                    doctor=doctor,
                    weekday=weekday,
                    start_time=time(14, 30),
                    defaults={
                        "end_time": time(17, 30),
                        "slot_duration": doctor.default_slot_duration,
                        "valid_from": today - timedelta(days=1),
                    },
                )

        patients = []
        for first, last, email in PATIENTS:
            user = User.objects.filter(email=email).first()
            if user is None:
                user = register_patient(
                    email=email,
                    password=DEMO_PASSWORD,
                    first_name=first,
                    last_name=last,
                    phone="+224 600 00 00 00",
                    birth_date=date(1990, 5, 12),
                )
            patients.append(user.patient_profile)

        created = 0
        for patient, doctor in zip(patients, doctors, strict=False):
            if patient.appointments.exists():
                continue
            slots = available_slots(doctor, today, today + timedelta(days=7))
            if slots:
                book_appointment(
                    patient=patient,
                    slot_id=slots[0].id,
                    reason="Consultation de contrôle (démonstration)",
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Données de démonstration prêtes.\n"
                f"  Administrateur : admin@demo.test / {DEMO_PASSWORD}\n"
                f"  Agent d'accueil : accueil@demo.test / {DEMO_PASSWORD}\n"
                f"  Médecin        : dr.diallo@demo.test / {DEMO_PASSWORD}\n"
                f"  Patient        : awa.traore@demo.test / {DEMO_PASSWORD}\n"
                f"  Médecins : {DoctorProfile.objects.count()} · "
                f"Rendez-vous créés : {created} · Admin : {admin.email}"
            )
        )

    def _get_or_create_user(self, *, role, email, first_name, last_name, **profile_fields):
        user = User.objects.filter(email=email).first()
        if user:
            return user
        return create_staff_user(
            role=role,
            email=email,
            password=DEMO_PASSWORD,
            first_name=first_name,
            last_name=last_name,
            phone="+224 600 00 00 00",
            **profile_fields,
        )
