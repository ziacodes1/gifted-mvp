"""Uzbek + Russian translations for the demo Discovery assessment and the shared
signal taxonomy. English in `seed_demo_assessment` stays canonical; these become the
`translations` JSON of each row. Keys (signal keys, option values) are never translated.
Leading underscore: not a management command.
"""

# signal key -> (uz label, ru label)
SIGNAL_TRANSLATIONS = {
    "realistic": ("Texnologiya va qurish", "Технологии и конструирование"),
    "investigative": ("Fan va tadqiqot", "Наука и исследования"),
    "artistic": ("San’at va dizayn", "Искусство и дизайн"),
    "social": ("Odamlarga yordam berish", "Помощь людям"),
    "enterprising": ("Yetakchilik va tashkilotchilik", "Лидерство и организация"),
    "logical_reasoning": ("Sonlardagi qonuniyatlar", "Числовые закономерности"),
    "spatial_reasoning": ("Fazoviy tasavvur", "Пространственное мышление"),
    "structured_planning": ("Avval reja tuzadi", "Сначала планирует"),
    "independent_work": ("Mustaqil ishlaydi", "Работает самостоятельно"),
    "problem_solving": ("Muammolarni ijodiy hal qilish", "Креативное решение задач"),
    "user_thinking": ("Foydalanuvchini tushunish va hamdardlik", "Мышление о пользователе и эмпатия"),
    "value_originality": ("O‘ziga xos narsa yaratish", "Создавать что-то своё"),
    "value_helpfulness": ("Boshqalarga foydali bo‘lish", "Быть полезным другим"),
    "value_discovery": ("Yangi narsalarni kashf qilish", "Открывать новое"),
    "value_practical": ("Kundalik narsalarni yaxshilash", "Улучшать привычные вещи"),
    "exp_technology": ("Qurish va dasturlash", "Конструирование и программирование"),
    "exp_science": ("Ilmiy tajribalar", "Научные эксперименты"),
    "exp_design": ("San’at va dizayn", "Искусство и дизайн"),
    "exp_organizing": ("Tadbirlar tashkil qilish", "Организация мероприятий"),
    "exp_helping": ("Boshqalarni o‘rgatish va qo‘llab-quvvatlash", "Обучать и поддерживать других"),
    "design_exposure": ("Dizayn va yasash tajribasi", "Опыт в дизайне и создании вещей"),
    "prioritization": ("Ustuvorlikni belgilash va murosa", "Приоритеты и компромиссы"),
}


def signal_translations(key: str) -> dict:
    uz, ru = SIGNAL_TRANSLATIONS[key]
    return {"uz": {"label": uz}, "ru": {"label": ru}}


ASSESSMENT = {
    "uz": {
        "title": "Kashfiyot testi",
        "description": "Sizga nima yoqishi, qanday fikrlashingiz va nimalarni sinab ko‘rganingiz haqida o‘nta qisqa vaziyat.",
    },
    "ru": {
        "title": "Тест «Открой себя»",
        "description": "Десять коротких ситуаций о том, что тебе нравится, как ты мыслишь и какой у тебя уже есть опыт.",
    },
}

SECTION = {"uz": {"title": "Kashfiyot"}, "ru": {"title": "Открытие"}}

NEITHER = {"uz": "Hech bir javob boshqasidan yaxshiroq emas.", "ru": "Ни один ответ не лучше другого."}

# Parallel to seed_demo_assessment.QUESTIONS (by position).
# Per language: prompt, helper_text, optional content overrides; options by value: (label, description).
QUESTIONS = [
    {
        "uz": {
            "prompt": "Maktab sizga yangi narsani sinab ko‘rish uchun bir kunlik bo‘sh vaqt berdi. Birinchi navbatda nimani tanlaysiz?",
            "helper_text": "Birinchi fikringizga ishoning.",
        },
        "ru": {
            "prompt": "Школа дарит тебе свободное время после уроков, чтобы попробовать что-то новое. Что выберешь первым делом?",
            "helper_text": "Доверься первому впечатлению.",
        },
        "options": {
            "build-robot": {"uz": ("Kichik robot yasab, uni sinab ko‘rish",), "ru": ("Собрать и испытать небольшого робота",)},
            "microscope": {"uz": ("Ko‘lmak suvini mikroskopda ko‘rish",), "ru": ("Рассмотреть воду из пруда под микроскопом",)},
            "paint-canvas": {"uz": ("Katta kanvasga hech qanday qoidasiz rasm chizish",), "ru": ("Расписать большой холст без всяких правил",)},
            "help-learn": {"uz": ("Kichikroq o‘quvchiga qiyin mavzuni tushunishda yordam berish",), "ru": ("Помочь младшему школьнику разобраться в трудной теме",)},
        },
    },
    {
        "uz": {
            "prompt": "Sinfingiz maktab yarmarkasi uchun stend tayyorlayapti, lekin hech kim nimadan boshlashni bilmaydi. Siz odatda birinchi bo‘lib nima qilasiz?",
            "helper_text": "Eng chiroyli eshitiladigan javobni emas, haqiqatan qiladigan ishingizni tanlang.",
        },
        "ru": {
            "prompt": "Ваш класс готовит стенд для школьной ярмарки, и никто не знает, с чего начать. Что ты обычно делаешь первым?",
            "helper_text": "Выбери то, как ты поступишь на самом деле, а не то, что звучит лучше всего.",
        },
        "options": {
            "sketch": {"uz": ("Stend qanday ko‘rinishi mumkinligi haqida bir nechta eskiz chizaman",), "ru": ("Набросаю несколько идей, как он может выглядеть",)},
            "how-built": {"uz": ("Uni amalda qanday yasash mumkinligini o‘ylab chiqaman",), "ru": ("Продумаю, как его на самом деле построить",)},
            "ask-visitors": {"uz": ("Bir nechta mehmondan nimani ko‘rishni xohlashlarini so‘rayman",), "ru": ("Спрошу у нескольких посетителей, что бы они хотели увидеть",)},
            "split-jobs": {"uz": ("Vazifalarni taqsimlab, reja tuzaman",), "ru": ("Распределю задачи и составлю план",)},
        },
    },
    {
        "uz": {"prompt": "Keyingi son qaysi?", "helper_text": "Sonlar orasidagi farq qanday o‘zgarayotganiga e’tibor bering."},
        "ru": {"prompt": "Какое число следующее?", "helper_text": "Посмотри, как меняется разница между числами."},
        "options": {},
    },
    {
        "uz": {
            "prompt": "Qaysi loyiha ustida bir oy davomida zavq bilan ishlagan bo‘lardingiz?",
            "helper_text": "Tasavvur qiling: vaqtingiz, asboblaringiz va yordamchilaringiz bor.",
        },
        "ru": {
            "prompt": "Какой из этих проектов тебе было бы интересно делать целый месяц?",
            "helper_text": "Представь, что у тебя есть время, инструменты и помощь.",
        },
        "options": {
            "redesign-backpack": {"uz": ("Ryukzakni ko‘tarish osonroq bo‘ladigan qilib qayta loyihalash",), "ru": ("Переделать рюкзак, чтобы его было легче носить",)},
            "survey-patterns": {"uz": ("Maktab so‘rovnomasi natijalaridan qonuniyatlar topish",), "ru": ("Найти закономерности в результатах школьного опроса",)},
            "school-garden": {"uz": ("Maktab tomorqasida sabzavot yetishtirish va unga qarash",), "ru": ("Вырастить школьный огород и ухаживать за ним",)},
            "pitch-council": {"uz": ("Maktab kengashiga g‘oya taqdim etib, qo‘llab-quvvatlash olish",), "ru": ("Представить идею школьному совету и заручиться поддержкой",)},
        },
    },
    {
        "uz": {
            "prompt": "Siz ko‘proq nima qilgan bo‘lardingiz?",
            "helper_text": "",
            "content": {"scenario": "Guruh loyihasini topshirishga ikki kun qoldi. Jamoadoshlaringizdan biri o‘z qismini bajarmagan va xabarlarga javob bermayapti."},
        },
        "ru": {
            "prompt": "Как ты, скорее всего, поступишь?",
            "helper_text": "",
            "content": {"scenario": "До сдачи группового проекта осталось два дня. Один участник команды не сделал свою часть и не отвечает на сообщения."},
        },
        "options": {
            "check-in": {"uz": ("Unga alohida yozib, hammasi joyidami, so‘rab ko‘raman",), "ru": ("Напишу ему лично и узнаю, всё ли в порядке",)},
            "re-plan": {"uz": ("Guruh baribir ulgurishi uchun ishni qayta rejalashtiraman",), "ru": ("Перераспределю работу, чтобы группа всё равно успела",)},
            "do-it-myself": {"uz": ("Uning qismini jimgina o‘zim bajaraman",), "ru": ("Молча возьму его часть на себя",)},
            "tell-teacher": {"uz": ("Kutilmagan holat bo‘lmasligi uchun o‘qituvchini oldindan ogohlantiraman",), "ru": ("Заранее предупрежу учителя, чтобы не было сюрпризов",)},
        },
    },
    {
        "uz": {
            "prompt": "Agar keyingi loyihangiz uchun faqat bitta natijani tanlay olsangiz, qaysi biri siz uchun muhimroq bo‘lardi?",
            "helper_text": NEITHER["uz"],
        },
        "ru": {
            "prompt": "Если бы для следующего проекта можно было выбрать только один результат, какой был бы для тебя важнее?",
            "helper_text": NEITHER["ru"],
        },
        "options": {
            "original": {
                "uz": ("Butunlay yangi, o‘ziga xos narsa yaratish", "Hali hech kim yaratmagan narsa."),
                "ru": ("Создать что-то совершенно оригинальное", "То, чего ещё никто не делал."),
            },
            "useful": {
                "uz": ("Ko‘pchilik uchun foydali narsa yaratish", "Ko‘p odamlar haqiqatan foydalanadigan narsa."),
                "ru": ("Создать что-то полезное для многих людей", "То, чем действительно будут пользоваться многие."),
            },
        },
    },
    {
        "uz": {
            "prompt": "Bulardan qaysilarini oldin haqiqatan sinab ko‘rgansiz?",
            "helper_text": "Mos keladiganlarning hammasini tanlang — bu mahorat haqida emas, tajriba haqida.",
        },
        "ru": {
            "prompt": "Что из этого тебе уже доводилось делать?",
            "helper_text": "Выбери всё подходящее — речь об опыте, а не о мастерстве.",
        },
        "options": {
            "built": {"uz": ("Asboblar bilan biror narsa yasaganman yoki tuzatganman",), "ru": ("Мастерить или чинить что-то с инструментами",)},
            "coded": {"uz": ("Kod yozish yoki dasturlashni sinab ko‘rganman",), "ru": ("Писать код или программировать",)},
            "science-kit": {"uz": ("Mikroskop yoki ilmiy to‘plamdan foydalanganman",), "ru": ("Работать с микроскопом или научным набором",)},
            "digital-art": {"uz": ("Raqamli rasm yoki dizayn yaratganman",), "ru": ("Создавать цифровой рисунок или дизайн",)},
            "organized": {"uz": ("Tadbir tashkil qilishda yordam berganman",), "ru": ("Помогать организовать мероприятие",)},
            "taught": {"uz": ("Kimgadir nimanidir o‘rgatganman yoki uni qo‘llab-quvvatlaganman",), "ru": ("Учить кого-то или поддерживать",)},
            "none": {"uz": ("Hali bulardan hech biri",), "ru": ("Пока ничего из этого",)},
        },
    },
    {
        "uz": {"prompt": "Qaysi shakl aynan shu shaklning o‘zi — faqat burilgan?", "helper_text": "Shakllarni burish mumkin, lekin ag‘darib bo‘lmaydi."},
        "ru": {"prompt": "Какая фигура — это та же самая, только повёрнутая?", "helper_text": "Фигуры можно поворачивать, но не переворачивать зеркально."},
        "options": {},
    },
    {
        "uz": {
            "prompt": "Shaharda dam olish kunlari bepul master-klasslar bo‘lyapti. Qaysi biriga yozilasiz?",
            "helper_text": "",
        },
        "ru": {
            "prompt": "В городе на выходных проходят бесплатные мастер-классы. На какой ты запишешься?",
            "helper_text": "",
        },
        "options": {
            "repair-electronics": {"uz": ("Meykerlar yarmarkasida eski elektronikani tuzatish",), "ru": ("Чинить старую электронику на мейкер-ярмарке",)},
            "museum-lab": {"uz": ("Fan muzeyida amaliy laboratoriya kuni",), "ru": ("Практический лабораторный день в научном музее",)},
            "run-desk": {"uz": ("Yoshlar festivalida mehmonlarni kutib olish jamoasini boshqarish",), "ru": ("Руководить командой встречи гостей на молодёжном фестивале",)},
            "homework-buddy": {"uz": ("Kutubxonada ko‘ngilli bo‘lib, uy vazifasida yordam berish",), "ru": ("Помогать с домашними заданиями в библиотеке как волонтёр",)},
        },
    },
    {
        "uz": {"prompt": "Qaysi turdagi vazifa sizga qiziqroq tuyuladi?", "helper_text": NEITHER["uz"]},
        "ru": {"prompt": "Какая задача звучит интереснее?", "helper_text": NEITHER["ru"]},
        "options": {
            "unsolved": {
                "uz": ("Hali hech kim hal qilmagan narsani aniqlash", "Kashf qilish zavqi."),
                "ru": ("Разгадать то, что ещё никто не решил", "Азарт открытия."),
            },
            "improve": {
                "uz": ("Odamlar allaqachon foydalanadigan narsani yaxshiroq ishlaydigan qilish", "Tuzatishdan olinadigan qoniqish."),
                "ru": ("Сделать так, чтобы привычная вещь работала лучше", "Радость от того, что получилось улучшить."),
            },
        },
    },
]


def question_translations(index: int) -> dict:
    spec = QUESTIONS[index]
    return {lang: dict(spec[lang]) for lang in ("uz", "ru")}


def option_translations(index: int, value: str) -> dict:
    entry = QUESTIONS[index]["options"].get(value)
    if not entry:
        return {}
    out = {}
    for lang in ("uz", "ru"):
        label, *rest = entry[lang]
        out[lang] = {"label": label, **({"description": rest[0]} if rest else {})}
    return out
