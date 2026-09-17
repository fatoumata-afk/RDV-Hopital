# HospiRDV — Gestion des rendez-vous et de l'accueil hospitalier

Application web hospitalière couvrant le parcours complet du patient : réservation en ligne,
QR code sécurisé, scan à l'accueil, validation de l'arrivée et orientation vers le bon service.

- **Backend** : Django 5 + Django REST Framework (JWT, SQLite en développement, PostgreSQL en production)
- **Frontend** : Vue 3 + Vite + Tailwind CSS 4 + Pinia + Vue Router

## Démarrage rapide

### Backend

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements/dev.txt
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo      # données de démonstration (optionnel)
.venv/bin/python manage.py runserver
```

API : `http://127.0.0.1:8000/api/v1/` — documentation interactive : `http://127.0.0.1:8000/api/docs/`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface : `http://localhost:5173` (les appels `/api` sont relayés vers Django par Vite).

## Comptes de démonstration

Créés par `python manage.py seed_demo`, mot de passe commun `Demo2026!hopital` :

| Rôle | Identifiant |
| --- | --- |
| Administrateur | `admin@demo.test` |
| Agent d'accueil | `accueil@demo.test` |
| Médecin | `dr.diallo@demo.test` |
| Patiente | `awa.traore@demo.test` |

`seed_demo --reset` réinitialise les données de démonstration. Ces données sont strictement
séparées de la logique applicative : toutes les fonctionnalités reposent sur la base et l'API.

## Parcours fonctionnel

1. Le patient s'inscrit, choisit une spécialité, un médecin, une date puis un créneau.
2. La réservation est validée côté serveur dans une transaction avec verrouillage du créneau,
   ce qui rend la double réservation impossible.
3. Un token opaque signé (HMAC-SHA256) est émis et rendu sous forme de QR code
   (`HMS:<uuid>.<signature>`), sans aucune donnée personnelle ni médicale.
4. À l'arrivée, l'agent scanne le code (caméra) ou le saisit manuellement.
   Le backend vérifie la signature, l'existence, l'expiration, la révocation, le statut du
   rendez-vous, la fenêtre horaire et l'absence d'arrivée déjà enregistrée.
5. L'agent valide l'arrivée et obtient l'orientation : spécialité — service — salle.

## Rôles et cloisonnement

| Rôle | Périmètre |
| --- | --- |
| Patient | Ses propres rendez-vous, son QR code, son profil |
| Médecin | Son agenda, ses patients attendus, ses horaires et indisponibilités |
| Agent d'accueil | Vérification des QR codes et informations d'orientation uniquement |
| Administrateur | Utilisateurs, organisation, rendez-vous, statistiques |

Les permissions sont appliquées côté API (filtrage des querysets + classes de permission) :
modifier un identifiant dans une URL ne donne pas accès aux données d'un autre utilisateur.
Les gardes du routeur Vue ne sont qu'un confort d'interface.

## Règles métier configurables

Variables d'environnement lues par `config/settings/base.py` :

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `APPOINTMENT_CANCELLATION_DEADLINE_HOURS` | `24` | Délai minimal d'annulation par le patient |
| `CHECKIN_WINDOW_BEFORE_MINUTES` | `120` | Ouverture de la fenêtre de scan avant l'heure du RDV |
| `CHECKIN_WINDOW_AFTER_MINUTES` | `60` | Fermeture de la fenêtre après l'heure du RDV |
| `DEFAULT_SLOT_DURATION_MINUTES` | `30` | Durée par défaut d'un créneau |
| `SLOT_GENERATION_HORIZON_DAYS` | `60` | Horizon de génération des créneaux |

## Tests

```bash
cd backend && .venv/bin/python -m pytest      # tests API et règles métier
cd backend && .venv/bin/python -m ruff check .
cd frontend && npm test                        # tests unitaires Vitest
cd frontend && npm run lint
```

Les tests backend couvrent l'inscription, la connexion, les permissions par rôle, la réservation,
la double réservation, l'annulation, les transitions de statut, la génération du QR code,
les codes invalides, expirés, hors fenêtre et déjà utilisés, l'enregistrement de l'arrivée et
l'isolation des données entre utilisateurs.

## Déploiement PostgreSQL

Le backend utilise `dj-database-url` : aucune modification de code n'est nécessaire.

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
export DATABASE_URL=postgres://utilisateur:motdepasse@hote:5432/hospirdv
export DJANGO_SECRET_KEY=...
export DJANGO_ALLOWED_HOSTS=exemple.org
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

Le frontend se construit avec `npm run build` ; définissez `VITE_API_BASE_URL` si l'API n'est pas
servie sur la même origine.
