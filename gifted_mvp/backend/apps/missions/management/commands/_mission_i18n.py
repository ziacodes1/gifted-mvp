"""Uzbek + Russian translations for "Design a Better School Bag". English in
`seed_demo_mission` stays canonical. Option/field lists are matched by `key`, other
lists by position (see common.i18n.tr). Evidence rules are never translated.
Leading underscore: not a management command.
"""

MISSION = {
    "uz": {
        "title": "Yaxshiroq maktab sumkasini loyihalang",
        "short_description": (
            "O‘quvchilar sumkalari og‘ir, noqulay va ichida tartib saqlash qiyin ekanini aytishmoqda. "
            "Muammoni o‘rganing, cheklangan byudjet doirasida ishlang va dizayn yo‘nalishini tanlang."
        ),
        "context": "Haqiqiy foydalanuvchilar, cheklangan resurslar va murosalar haqida qisqa dizayn vazifasi.",
        "metadata": {
            "time_label": "5–8 daqiqa",
            "activity_label": "Dizayn vazifasi",
            "focus_areas": ["Muammolarni ijodiy hal qilish", "Ustuvorlikni belgilash", "Foydalanuvchini tushunish", "Dizayn tajribasi"],
            "intro_steps": [
                {"title": "Foydalanuvchilar bilan tanishing", "text": "O‘quvchilar sumkalari haqida nima deyishini o‘qing."},
                {"title": "Nimani o‘rganishni tanlang", "text": "Birinchi navbatda o‘rganadigan muammolarni tanlang."},
                {"title": "Cheklangan byudjetni sarflang", "text": "10 ball — hammasini tuzatib bo‘lmaydi."},
                {"title": "Yo‘nalishni tanlang", "text": "Eng yaxshi muvozanatni topadigan dizaynni tanlang."},
                {"title": "Fikr yuriting", "text": "Fikringizni bir necha jumlada tushuntiring."},
            ],
        },
    },
    "ru": {
        "title": "Придумай школьный рюкзак получше",
        "short_description": (
            "Школьники жалуются, что рюкзаки тяжёлые, неудобные и в них трудно навести порядок. "
            "Изучи проблему, уложись в бюджет и выбери направление дизайна."
        ),
        "context": "Короткое дизайн-задание о реальных пользователях, ограниченных ресурсах и компромиссах.",
        "metadata": {
            "time_label": "5–8 мин",
            "activity_label": "Дизайн-задание",
            "focus_areas": ["Креативное решение задач", "Расстановка приоритетов", "Мышление о пользователе", "Опыт в дизайне"],
            "intro_steps": [
                {"title": "Познакомься с пользователями", "text": "Прочитай, что школьники говорят о своих рюкзаках."},
                {"title": "Выбери, что исследовать", "text": "Отметь проблемы, которые изучишь в первую очередь."},
                {"title": "Распредели ограниченный бюджет", "text": "10 баллов — всё исправить не получится."},
                {"title": "Выбери направление", "text": "Найди дизайн с лучшим балансом."},
                {"title": "Поразмышляй", "text": "Объясни свою логику в нескольких предложениях."},
            ],
        },
    },
}

STEPS = {
    "brief": {
        "uz": {
            "title": "Topshiriq",
            "prompt": (
                "Maktabingiz o‘quvchilari sumkalari og‘ir, noqulay va ichida tartib saqlash qiyin ekanini aytishmoqda. "
                "O‘quvchilar kengashi kichik dizayn jamoasidan — ya’ni sizdan — yaxshiroq maktab sumkasini taklif qilishni so‘radi."
            ),
            "content": {
                "voices": [
                    {"quote": "Oxirgi darsga kelib yelkalarim qattiq og‘riydi.", "who": "8-sinf o‘quvchisi"},
                    {"quote": "Kalkulyatorimni hech topa olmayman — hamma narsa sumka tagiga tushib ketadi.", "who": "9-sinf o‘quvchisi"},
                    {"quote": "O‘tgan chorakda planshetimning ekrani sumka ichida yorilib ketdi.", "who": "7-sinf o‘quvchisi"},
                ],
                "goal": "Vazifangiz: haqiqiy cheklovlar doirasida avval nimani tuzatishni hal qiling.",
            },
        },
        "ru": {
            "title": "Задание",
            "prompt": (
                "Ученики твоей школы жалуются, что рюкзаки тяжёлые, неудобные и в них трудно навести порядок. "
                "Школьный совет попросил небольшую дизайн-команду — то есть тебя — предложить рюкзак получше."
            ),
            "content": {
                "voices": [
                    {"quote": "К последнему уроку у меня очень болят плечи.", "who": "Ученик 8 класса"},
                    {"quote": "Никогда не могу найти калькулятор — всё проваливается на дно.", "who": "Ученица 9 класса"},
                    {"quote": "В прошлой четверти у меня в рюкзаке треснул экран планшета.", "who": "Ученик 7 класса"},
                ],
                "goal": "Твоя задача — решить, что исправить в первую очередь, с учётом реальных ограничений.",
            },
        },
    },
    "understand": {
        "uz": {
            "title": "Foydalanuvchini tushuning",
            "prompt": "Qaysi muammolarni birinchi bo‘lib o‘rganardingiz? Ko‘pi bilan ikkitasini tanlang — haqiqiy jamoa ham hammasini birdaniga o‘rgana olmaydi.",
            "content": {
                "options": [
                    {"key": "too_heavy", "label": "Juda og‘ir", "description": "Kun oxiriga kelib sumka juda og‘irlashadi."},
                    {"key": "hard_to_organize", "label": "Tartib saqlash qiyin", "description": "Narsalar tagiga tushib, yo‘qolib qoladi."},
                    {"key": "uncomfortable_straps", "label": "Noqulay tasmalar", "description": "Tasmalar yelkaga botadi va sirg‘anib tushadi."},
                    {"key": "books_damaged", "label": "Kitoblar buziladi", "description": "Burchaklari bukiladi, varaqlari yirtiladi, ichimlik to‘kiladi."},
                    {"key": "device_safety", "label": "Qurilmalar uchun xavfsiz joy yo‘q", "description": "Planshet va telefonlar urilib, shikastlanadi."},
                ],
            },
        },
        "ru": {
            "title": "Пойми пользователя",
            "prompt": "Какие проблемы ты изучишь первыми? Выбери не больше двух — настоящая команда тоже не может исследовать всё сразу.",
            "content": {
                "options": [
                    {"key": "too_heavy", "label": "Слишком тяжёлый", "description": "К концу дня рюкзак весит очень много."},
                    {"key": "hard_to_organize", "label": "Трудно навести порядок", "description": "Вещи проваливаются на дно и теряются."},
                    {"key": "uncomfortable_straps", "label": "Неудобные лямки", "description": "Лямки врезаются и сползают с плеч."},
                    {"key": "books_damaged", "label": "Портятся учебники", "description": "Загнутые углы, порванные страницы, пролитые напитки."},
                    {"key": "device_safety", "label": "Негде безопасно хранить гаджеты", "description": "Планшеты и телефоны бьются обо всё подряд."},
                ],
            },
        },
    },
    "prioritize": {
        "uz": {
            "title": "Ustuvorlikni belgilang",
            "prompt": "Yaxshilanishlarga sarflash uchun 10 ballingiz bor. Hammasiga yetmaydi — eng muhimini tanlang.",
            "content": {
                "options": [
                    {"key": "lightweight_material", "label": "Mustahkamroq va yengilroq material", "description": "Mustahkamlikni yo‘qotmasdan og‘irlikni kamaytiradi."},
                    {"key": "ergonomic_straps", "label": "Ergonomik tasmalar", "description": "Yumshoq, sozlanadigan, og‘irlikni teng taqsimlaydi."},
                    {"key": "modular_compartments", "label": "Modulli bo‘limlar", "description": "Har bir narsaning o‘z joyi bor, joyini o‘zgartirish mumkin."},
                    {"key": "waterproof_layer", "label": "Suv o‘tkazmaydigan qatlam", "description": "Yomg‘irda va suyuqlik to‘kilganda kitoblarni quruq saqlaydi."},
                    {"key": "device_protection", "label": "Qurilmalar uchun yumshoq g‘ilof", "description": "Planshet va noutbuklarni zarbalardan himoya qiladi."},
                ],
            },
        },
        "ru": {
            "title": "Расставь приоритеты",
            "prompt": "У тебя есть 10 баллов на улучшения. На всё не хватит — выбери самое важное.",
            "content": {
                "options": [
                    {"key": "lightweight_material", "label": "Более прочный и лёгкий материал", "description": "Снижает вес без потери прочности."},
                    {"key": "ergonomic_straps", "label": "Эргономичные лямки", "description": "Мягкие, регулируемые, распределяют нагрузку."},
                    {"key": "modular_compartments", "label": "Модульные отделения", "description": "У каждой вещи своё место, всё можно переставить."},
                    {"key": "waterproof_layer", "label": "Водонепроницаемый слой", "description": "Защищает учебники от дождя и пролитой воды."},
                    {"key": "device_protection", "label": "Мягкий чехол для гаджетов", "description": "Защищает планшеты и ноутбуки от ударов."},
                ],
            },
        },
    },
    "direction": {
        "uz": {
            "title": "Dizayn yo‘nalishini tanlang",
            "prompt": "Qaysi yo‘nalish foydalanuvchilar ehtiyoji va byudjet imkoniyatlari o‘rtasida eng yaxshi muvozanatni topadi?",
            "content": {
                "options": [
                    {"key": "featherweight", "label": "Pat kabi yengil", "description": "Iloji boricha yengil — kun bo‘yi ko‘tarish oson.", "tradeoff": "Bo‘limlar kamroq"},
                    {"key": "organizer", "label": "Tartib ustasi", "description": "Ichi modulli, har bir narsaning o‘z joyi bor.", "tradeoff": "Biroz og‘irroq"},
                    {"key": "comfort_fit", "label": "Qulay moslashuv", "description": "Tanaga moslashgan: yumshoq orqa qism, sozlanadigan tasmalar.", "tradeoff": "Kattaroq ko‘rinadi"},
                    {"key": "statement", "label": "Ko‘zga tashlanadigan sumka", "description": "O‘quvchilar faxrlanadigan ko‘rinish, almashtiriladigan panellar bilan.", "tradeoff": "Uslub byudjetni sarflaydi"},
                ],
            },
        },
        "ru": {
            "title": "Выбери направление дизайна",
            "prompt": "Какое направление лучше всего сочетает то, что нужно пользователям, с тем, что позволяет бюджет?",
            "content": {
                "options": [
                    {"key": "featherweight", "label": "Пёрышко", "description": "Максимально лёгкий — удобно носить весь день.", "tradeoff": "Меньше отделений"},
                    {"key": "organizer", "label": "Органайзер", "description": "Модульный внутри: у каждой вещи своё место.", "tradeoff": "Чуть тяжелее"},
                    {"key": "comfort_fit", "label": "Комфорт", "description": "Создан под тело: мягкая спинка, регулируемые лямки.", "tradeoff": "Выглядит громоздче"},
                    {"key": "statement", "label": "Стильный акцент", "description": "Внешний вид, которым гордятся, со сменными панелями.", "tradeoff": "Стиль съедает бюджет"},
                ],
            },
        },
    },
    "reflect": {
        "uz": {
            "title": "Fikr yuriting",
            "prompt": "Bu yerda to‘g‘ri javob yo‘q — bizni qanday o‘ylaganingiz qiziqtiradi.",
            "content": {
                "fields": [
                    {"key": "why", "label": "Nega aynan shu yaxshilanishlarni tanladingiz?", "placeholder": "Men … ga e’tibor qaratdim, chunki …"},
                    {"key": "test_first", "label": "Agar prototip yasay olsangiz, birinchi navbatda nimani sinab ko‘rardingiz?", "placeholder": "Avval … ni … orqali sinab ko‘rardim"},
                ],
            },
        },
        "ru": {
            "title": "Поразмышляй",
            "prompt": "Здесь нет правильного ответа — нам интересен ход твоих мыслей.",
            "content": {
                "fields": [
                    {"key": "why", "label": "Почему именно эти улучшения?", "placeholder": "Главным для меня было… потому что…"},
                    {"key": "test_first", "label": "Если бы у тебя был прототип, что стоило бы проверить в первую очередь?", "placeholder": "Сначала проверить… с помощью…"},
                ],
            },
        },
    },
}
