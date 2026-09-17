"""Utilisateurs et profils métier (patient, médecin, agent d'accueil)."""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class UserRole(models.TextChoices):
    PATIENT = "PATIENT", "Patient"
    DOCTOR = "DOCTOR", "Médecin"
    AGENT = "AGENT", "Agent d'accueil"
    ADMIN = "ADMIN", "Administrateur"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("role", UserRole.PATIENT)
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("role", UserRole.ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True or extra.get("is_superuser") is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff et is_superuser à True.")
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Compte unique de l'application, identifié par l'e-mail et porteur d'un rôle."""

    email = models.EmailField("adresse e-mail", unique=True)
    first_name = models.CharField("prénom", max_length=80)
    last_name = models.CharField("nom", max_length=80)
    phone = models.CharField("téléphone", max_length=30, blank=True)
    role = models.CharField("rôle", max_length=10, choices=UserRole.choices)
    is_active = models.BooleanField("actif", default=True)
    is_staff = models.BooleanField("accès à l'admin Django", default=False)
    must_change_password = models.BooleanField("doit changer son mot de passe", default=False)
    date_joined = models.DateTimeField("inscrit le", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_patient(self):
        return self.role == UserRole.PATIENT

    @property
    def is_doctor(self):
        return self.role == UserRole.DOCTOR

    @property
    def is_agent(self):
        return self.role == UserRole.AGENT

    @property
    def is_admin_role(self):
        return self.role == UserRole.ADMIN


class Gender(models.TextChoices):
    FEMALE = "F", "Féminin"
    MALE = "M", "Masculin"
    OTHER = "O", "Autre"


class PatientProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    medical_record_number = models.CharField("numéro de dossier", max_length=20, unique=True)
    birth_date = models.DateField("date de naissance", null=True, blank=True)
    gender = models.CharField("genre", max_length=1, choices=Gender.choices, blank=True)
    national_id = models.CharField(
        "pièce d'identité", max_length=40, blank=True, null=True, unique=True
    )
    address = models.CharField("adresse", max_length=255, blank=True)
    emergency_contact = models.CharField("contact d'urgence", max_length=120, blank=True)

    class Meta:
        verbose_name = "profil patient"
        verbose_name_plural = "profils patients"

    def __str__(self):
        return f"{self.user.full_name} ({self.medical_record_number})"


class DoctorProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    license_number = models.CharField("numéro d'ordre", max_length=40, unique=True)
    specialty = models.ForeignKey(
        "organization.Specialty",
        on_delete=models.PROTECT,
        related_name="doctors",
        verbose_name="spécialité",
    )
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.PROTECT,
        related_name="doctors",
        verbose_name="service",
    )
    room = models.ForeignKey(
        "organization.Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors",
        verbose_name="salle",
    )
    bio = models.TextField("présentation", blank=True)
    default_slot_duration = models.PositiveSmallIntegerField(
        "durée de consultation (min)", default=30
    )
    is_accepting_appointments = models.BooleanField("accepte les rendez-vous", default=True)

    class Meta:
        verbose_name = "profil médecin"
        verbose_name_plural = "profils médecins"
        ordering = ["user__last_name"]

    def __str__(self):
        return f"Dr {self.user.full_name}"

    @property
    def display_name(self):
        return f"Dr {self.user.full_name}"


class AgentProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="agent_profile")
    badge_number = models.CharField("numéro de badge", max_length=30, unique=True)
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        verbose_name="service d'affectation",
    )

    class Meta:
        verbose_name = "profil agent d'accueil"
        verbose_name_plural = "profils agents d'accueil"

    def __str__(self):
        return f"{self.user.full_name} ({self.badge_number})"
