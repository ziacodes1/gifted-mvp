"""Rewards catalog + a few demo peers so the weekly leaderboard isn't empty (idempotent).

Demo peers are STUDENT accounts that cannot log in (unusable password) and carry only a
first name + surname for the "Aziza Y." display. Their activity is keyed by week, so
re-running in the same week changes nothing and a new week gets fresh demo activity.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Role, User
from apps.engagement.models import Reward
from apps.engagement.rules import EventType, RewardType
from apps.engagement.services import _create_event, local_day, week_start

REWARDS = [
    {
        "key": "sticker-pack", "points_required": 50, "reward_type": RewardType.PHYSICAL, "image_key": "sticker_pack", "order": 1,
        "title": "Gifted Sticker Pack", "description": "A set of Gifted stickers for your notebook, laptop or water bottle.",
        "translations": {
            "uz": {"title": "Gifted stikerlar to‘plami", "description": "Daftaringiz, noutbukingiz yoki suv idishingiz uchun Gifted stikerlari to‘plami."},
            "ru": {"title": "Набор стикеров Gifted", "description": "Набор стикеров Gifted для тетради, ноутбука или бутылки."},
        },
    },
    {
        "key": "notebook", "points_required": 150, "reward_type": RewardType.PHYSICAL, "image_key": "notebook", "order": 2,
        "title": "Gifted Notebook", "description": "A forest-green notebook for ideas, sketches and plans.",
        "translations": {
            "uz": {"title": "Gifted daftari", "description": "G‘oyalar, chizmalar va rejalar uchun yashil daftar."},
            "ru": {"title": "Блокнот Gifted", "description": "Тёмно-зелёный блокнот для идей, набросков и планов."},
        },
    },
    {
        "key": "water-bottle", "points_required": 200, "reward_type": RewardType.PHYSICAL, "image_key": "water_bottle", "order": 3,
        "title": "Gifted Water Bottle", "description": "A reusable bottle to keep you going through busy days.",
        "translations": {
            "uz": {"title": "Gifted suv idishi", "description": "Band kunlarda hamrohingiz bo‘ladigan qayta ishlatiladigan idish."},
            "ru": {"title": "Бутылка Gifted", "description": "Многоразовая бутылка для насыщенных дней."},
        },
    },
    {
        "key": "expert-course", "points_required": 300, "reward_type": RewardType.COURSE, "image_key": "expert_course", "order": 4,
        "title": "Free Expert Course", "description": "Access to a short online course from a Gifted expert in an area you're exploring.",
        "translations": {
            "uz": {"title": "Bepul ekspert kursi", "description": "Siz o‘rganayotgan soha bo‘yicha Gifted ekspertining qisqa onlayn kursiga kirish."},
            "ru": {"title": "Бесплатный курс эксперта", "description": "Доступ к короткому онлайн-курсу эксперта Gifted в направлении, которое ты исследуешь."},
        },
    },
    {
        "key": "event-pass", "points_required": 500, "reward_type": RewardType.EVENT, "image_key": "event_pass", "order": 5,
        "title": "Pro Event Pass", "description": "A pass to a Gifted Live event with talks and hands-on workshops.",
        "translations": {
            "uz": {"title": "Pro tadbir chiptasi", "description": "Ma’ruzalar va amaliy mashg‘ulotlar bo‘ladigan Gifted Live tadbiriga chipta."},
            "ru": {"title": "Pro-пропуск на событие", "description": "Пропуск на Gifted Live с выступлениями и практическими мастер-классами."},
        },
    },
    {
        "key": "community-access", "points_required": 500, "reward_type": RewardType.COMMUNITY, "image_key": "community_access", "order": 6,
        "title": "Exclusive Community Access", "description": "Early access to a moderated Gifted learner community when it opens.",
        "translations": {
            "uz": {"title": "Maxsus hamjamiyatga kirish", "description": "Gifted o‘quvchilar hamjamiyati ochilganda unga birinchilardan bo‘lib kirish."},
            "ru": {"title": "Доступ к закрытому сообществу", "description": "Ранний доступ к модерируемому сообществу учеников Gifted, когда оно откроется."},
        },
    },
    {
        "key": "mentor-session", "points_required": 750, "reward_type": RewardType.MENTOR, "image_key": "mentor_session", "order": 7, "stock": 10,
        "title": "1:1 Mentor Session", "description": "A 30-minute online conversation with a Gifted mentor about what you're exploring.",
        "translations": {
            "uz": {"title": "Mentor bilan 1:1 uchrashuv", "description": "Gifted mentori bilan siz o‘rganayotgan narsalar haqida 30 daqiqalik onlayn suhbat."},
            "ru": {"title": "Встреча 1:1 с ментором", "description": "30-минутный онлайн-разговор с ментором Gifted о том, что ты исследуешь."},
        },
    },
]

# (full name, [(event type, days ago within this week)])
PEERS = [
    ("Aziza Yusupova", [(EventType.MISSION_COMPLETED, 3), (EventType.ASSESSMENT_COMPLETED, 4)] + [(EventType.DIARY_ENTRY_CREATED, d) for d in (0, 1, 2)]),
    ("Rohan Karimov", [(EventType.MISSION_COMPLETED, 1), (EventType.ASSESSMENT_COMPLETED, 2), (EventType.DIARY_ENTRY_CREATED, 0)]),
    ("Meera Patel", [(EventType.ASSESSMENT_COMPLETED, 2)] + [(EventType.DIARY_ENTRY_CREATED, d) for d in (0, 1, 3)]),
    ("Timur Aliev", [(EventType.MISSION_COMPLETED, 1)]),
    ("Diyora Saidova", [(EventType.ASSESSMENT_COMPLETED, 0), (EventType.DIARY_ENTRY_CREATED, 1)]),
    ("Sofia Ivanova", [(EventType.DIARY_ENTRY_CREATED, d) for d in (0, 2)]),
]


class Command(BaseCommand):
    help = "Seed the rewards catalog and demo leaderboard peers (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        for spec in REWARDS:
            spec = dict(spec)
            Reward.objects.update_or_create(key=spec.pop("key"), defaults={"active": True, "stock": spec.pop("stock", None), **spec})

        today = local_day()
        monday = week_start(today)
        for i, (name, activity) in enumerate(PEERS, start=1):
            user, created = User.objects.get_or_create(
                email=f"peer{i}@peers.gifted.demo", defaults={"full_name": name, "role": Role.STUDENT}
            )
            if created or user.has_usable_password():
                user.set_unusable_password()  # demo peers never sign in
            user.full_name, user.role = name, Role.STUDENT
            user.save()
            for n, (event_type, days_ago) in enumerate(activity):
                day = max(today - timedelta(days=days_ago), monday)
                key = f"demo:{monday.isoformat()}:{n}"
                if event_type == EventType.ASSESSMENT_COMPLETED:
                    key = f"assessment:demo-{monday.isoformat()}:session:1"
                _create_event(user, event_type, key, day)
        self.stdout.write(f"Seeded {len(REWARDS)} rewards and {len(PEERS)} demo leaderboard peers.")
