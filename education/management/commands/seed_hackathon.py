from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from education.models import Course, Lesson, Question, Test

PACKS = [
    {
        "subject": "math",
        "title": "Nusgalyk: Matematika",
        "group": "8-nji synp",
        "lesson": "Kwadrat funksiýa",
        "objective": "y = ax² + bx + c grafiginiň görnüşini parametrler arkaly düşündirmek.",
        "interactive": "math_graph",
        "text": "Kwadrat funksiýanyň grafigi parabola. a > 0 bolsa şahalar ýokary, a < 0 bolsa aşak seredýär. Degişme nokady werşinadyr.",
        "questions": [
            ("choice", "a > 0 bolanda parabola nähili seredýär?", ["Ýokary", "Aşak", "Göni", "Nokat"], "Ýokary"),
            ("choice", "Werşina nämäni aňladýar?", ["Iň ýokary ýa-da iň pes nokat", "Diňe kök", "Asimptota", "Merkez"], "Iň ýokary ýa-da iň pes nokat"),
            ("short", "Grafigiň ady näme?", [], "parabola", "parabol"),
            ("number", "y = x² funksiýada x = 3 bolanda y näçe?", [], "", None, 9, "", 0),
            ("number", "y = 2x bolanda x = 4, y näçe?", [], "", None, 8, "", 0),
            ("match", "Adalgalary gabat getir", [], "", [["a > 0", "Şahalar ýokary"], ["a < 0", "Şahalar aşak"], ["c", "Oý kesişmesi"]]),
            ("order", "Deňlemäni çözmegiň tertibi", [], "", None, None, None, None, ["Deňlemäni ýaz", "Koeffisiýentleri tap", "Diskriminanty hasapla", "Kökleri ýaz"]),
            ("open", "a = -1 bolanda grafigi söz bilen düşündiriň.", [], "", None, None, None, None, None, "Şahalaryň aşak seretmegi we iň ýokary nokadyň bolmagy görkezilmeli."),
            ("multi", "Haýsylary parabola?", ["y = x²", "y = 2x + 1", "y = -x² + 3", "y = 5"], "y = x²|y = -x² + 3"),
            ("practical", "Grafigiň suratyny ýa-da sanawyny tabşyryň: a=1, b=0, c=-1.", [], "", None, None, None, None, None, "Werşina we Oý bilen kesişme görkezilmeli."),
        ],
    },
    {
        "subject": "physics",
        "title": "Nusgalyk: Fizika",
        "group": "8-nji synp",
        "lesson": "Om kanuny",
        "objective": "U, I we R arasyndaky baglanyşygy ölçeg arkaly görmek.",
        "interactive": "physics_circuit",
        "text": "Om kanuny: I = U / R. Naprýaženiýe wolt, garşylyk om, tok amperde ölçelýär.",
        "questions": [
            ("choice", "Tokyň formulasy?", ["I = U / R", "I = U · R", "I = R / U", "I = U + R"], "I = U / R"),
            ("choice", "Garşylygyň birligi?", ["Om", "Amper", "Joul", "Metr"], "Om"),
            ("short", "Tokyň birligi?", [], "amper", "A"),
            ("number", "U = 12 V, R = 4 Om. I näçe?", [], "", None, 3, "A", 0.05),
            ("number", "U = 9 V, R = 3 Om. I näçe?", [], "", None, 3, "A", 0.05),
            ("match", "Birlikleri gabat getir", [], "", [["Tok", "Amper"], ["Naprýaženiýe", "Wolt"], ["Garşylyk", "Om"]]),
            ("order", "Zynjyrda ölçeg tertibi", [], "", None, None, None, None, ["Çeşmäni birikdir", "Garşylygy saýla", "Toky hasapla", "Netijäni ýaz"]),
            ("open", "Garşylyk artsa, tok nämä öwrülýär? Düşündiriň.", [], "", None, None, None, None, None, "Tok kemelýär, sebäbi I = U / R."),
            ("multi", "Om kanunyna degişli ululyklar?", ["U", "I", "R", "massa"], "U|I|R"),
            ("practical", "U we R üçin öz ölçegiňizi ýazyp, I-ni hasaplaň we faýl hökmünde tabşyryň.", [], "", None, None, None, None, None, "Hasap we birlik bolmaly."),
        ],
    },
    {
        "subject": "chemistry",
        "title": "Nusgalyk: Himiýa",
        "group": "8-nji synp",
        "lesson": "Reaksiýany deňlemek",
        "objective": "H₂ + O₂ → H₂O reaksiýasynda atomlaryň sanyny deňlemek.",
        "interactive": "chemistry_balance",
        "text": "Deňlenen görnüş: 2H₂ + O₂ → 2H₂O. Çepde we sagda H atomlary 4, O atomlary 2.",
        "questions": [
            ("choice", "Suwuň formulasy?", ["H₂O", "HO₂", "H₂O₂", "OH"], "H₂O"),
            ("choice", "2H₂ + O₂ → 2H₂O deňlenenmi?", ["Hawa", "Ýok", "Diňe wodorod", "Diňe kislorod"], "Hawa"),
            ("short", "Kislorodyň formulasy?", [], "O₂", "O2"),
            ("number", "2H₂O-da wodorod atomlarynyň sany?", [], "", None, 4, "", 0),
            ("number", "O₂ molekulasında O atomy näçe?", [], "", None, 2, "", 0),
            ("match", "Maddany we formulany gabat getir", [], "", [["Wodorod", "H₂"], ["Kislorod", "O₂"], ["Suw", "H₂O"]]),
            ("order", "Deňlemegiň ädimleri", [], "", None, None, None, None, ["Formulalary ýaz", "Atomlary sana", "Koeffisiýent goý", "Iki tarapy deňeşdir"]),
            ("open", "Näme üçin koeffisiýent gerek?", [], "", None, None, None, None, None, "Massanyň saklanma kanunyny görkezmeli."),
            ("multi", "Deňlenen reaksiýada bar bolanlar?", ["H₂", "O₂", "H₂O", "NaCl"], "H₂|O₂|H₂O"),
            ("practical", "Öz saýlan reaksiýaňyzy deňläň we kagyz ýa-da faýl tabşyryň.", [], "", None, None, None, None, None, "Iki tarapdaky atom sany deň bolmaly."),
        ],
    },
    {
        "subject": "biology",
        "title": "Nusgalyk: Biologiýa",
        "group": "8-nji synp",
        "lesson": "Öýjügiň gurluşy",
        "objective": "Öýjük böleklerini tanamak we wezipesini düşündirmek.",
        "interactive": "biology_cell",
        "text": "Ýadro nesil maglumatyny saklaýar. Mitohondriýa energiýa öndürýär. Membrana çägi dolandyrýar. Sitoplazma gurşawdyr.",
        "questions": [
            ("choice", "Nesil maglumaty nirede?", ["Ýadro", "Membrana", "Sitoplazma", "Diwar"], "Ýadro"),
            ("choice", "Energiýany esasan kim öndürýär?", ["Mitohondriýa", "Ýadro", "Wakuol", "Ribo soma"], "Mitohondriýa"),
            ("short", "Öýjügiň daşky çägine näme diýilýär?", [], "membrana"),
            ("number", "Sanawda näçe esasy bölek görkezildi: ýadro, membrana, sitoplazma, mitohondriýa?", [], "", None, 4, "", 0),
            ("number", "Ýadro bir öýjükde adatça näçe (adaty ösümlik däl, sorag sany)?", [], "", None, 1, "", 0),
            ("match", "Bölegi we wezipesini gabat getir", [], "", [["Ýadro", "Maglumat"], ["Mitohondriýa", "Energiýa"], ["Membrana", "Çäk"]]),
            ("order", "Öýjügi öwrenmegiň tertibi", [], "", None, None, None, None, ["Bölegi saýla", "Adyny aýt", "Wezipesini ýaz", "Beýlekiler bilen deňeşdir"]),
            ("open", "Membrananyň wezipesini düşündiriň.", [], "", None, None, None, None, None, "Maddalaryň saýlap geçmegi bolmaly."),
            ("multi", "Öýjüge degişli bölekler?", ["Ýadro", "Mitohondriýa", "Şina", "Sitoplazma"], "Ýadro|Mitohondriýa|Sitoplazma"),
            ("practical", "Öýjük şekilini belläp, azyndan 3 bölegi atlandyryň.", [], "", None, None, None, None, None, "Ady we wezipesi bolmaly."),
        ],
    },
    {
        "subject": "informatics",
        "title": "Nusgalyk: Informatika",
        "group": "8-nji synp",
        "lesson": "Jemleme algoritmi",
        "objective": "1-den n-e çenli jemi ädimme-ädim hasaplamak.",
        "interactive": "informatics_algo",
        "text": "Algoritm: jem = 0; her i üçin jem = jem + i. n = 4 bolanda netije 10.",
        "questions": [
            ("choice", "Algoritm näme?", ["Ädimleriň yzygiderliligi", "Diňe surat", "Kompýuteriň korpusy", "Kabel"], "Ädimleriň yzygiderliligi"),
            ("choice", "n = 4 bolanda 1+2+3+4 näçe?", ["10", "8", "16", "4"], "10"),
            ("short", "Maglumaty işläp taýýarlaýan enjam?", [], "prosessor", "CPU"),
            ("number", "1-den 3-e çenli jem?", [], "", None, 6, "", 0),
            ("number", "n = 5 bolanda jem näçe?", [], "", None, 15, "", 0),
            ("match", "Bölegi we wezipesini gabat getir", [], "", [["Prosesor", "Hasaplaýar"], ["Ýat", "Saklaýar"], ["Monitor", "Görkezýär"]]),
            ("order", "Jemi hasaplamagyň ädimleri", [], "", None, None, None, None, ["jem = 0", "i = 1", "jem = jem + i", "i-ni artdyr"]),
            ("open", "Siklli algoritmi öz sözüňiz bilen düşündiriň.", [], "", None, None, None, None, None, "Gaýtalanýan ädim bolmaly."),
            ("multi", "Kompýuteriň bölekleri?", ["Prosesor", "Ýat", "Bulut ýagyşy", "Monitor"], "Prosesor|Ýat|Monitor"),
            ("practical", "Öz n sanyňyz üçin ädimleri ýazyp tabşyryň.", [], "", None, None, None, None, None, "Soňky jem dogry bolmaly."),
        ],
    },
]


def _add(test, spec):
    qtype = spec[0]
    text = spec[1]
    options = spec[2] if len(spec) > 2 else []
    correct = spec[3] if len(spec) > 3 else ""
    extra = spec[4] if len(spec) > 4 else None
    number = spec[5] if len(spec) > 5 else None
    unit = spec[6] if len(spec) > 6 else ""
    tol = spec[7] if len(spec) > 7 else 0
    seq = spec[8] if len(spec) > 8 else None
    rubric = spec[9] if len(spec) > 9 else ""
    opts = (options + ["", "", "", ""])[:4]
    question = Question(
        test=test,
        text=text,
        qtype=qtype,
        points=2 if qtype in ("open", "practical") else 1,
        option_a=opts[0],
        option_b=opts[1],
        option_c=opts[2],
        option_d=opts[3],
        correct_answer=correct or "",
        rubric=rubric or "",
        explanation=rubric or "",
    )
    if qtype == "short":
        question.accepted_answers = extra or ""
    if qtype == "number":
        question.number_value = number
        question.number_unit = unit or ""
        question.number_tolerance = tol or 0
    if qtype == "match":
        question.match_pairs = extra or []
    if qtype == "order":
        question.order_items = seq or []
    question.save()


class Command(BaseCommand):
    help = "Bäş ders üçin nusgalyk sapak, 10 sorag we interaktiw döredýär."

    def handle(self, *args, **options):
        User = get_user_model()
        teacher = User.objects.filter(role="TH").first()
        if teacher is None:
            teacher = User.objects.create_user(
                username="mugallym",
                password="bilim123",
                role="TH",
                is_staff=True,
            )
            self.stdout.write("Mugallym döredildi: mugallym / bilim123")
        elif not teacher.is_staff:
            teacher.is_staff = True
            teacher.save(update_fields=["is_staff"])
        for pack in PACKS:
            course, _ = Course.objects.get_or_create(
                title=pack["title"],
                defaults={
                    "description": pack["text"],
                    "subject": pack["subject"],
                    "group_name": pack["group"],
                    "author": teacher,
                },
            )
            course.subject = pack["subject"]
            course.group_name = pack["group"]
            course.save()
            lesson = course.lessons.filter(title=pack["lesson"]).first()
            if lesson and lesson.test and lesson.test.questions.exists():
                self.stdout.write(f"Bar: {pack['title']}")
                continue
            test = Test.objects.create(
                title=f"Synag: {pack['lesson']}",
                author=teacher,
                duration_minutes=20,
                allow_retry=True,
            )
            for spec in pack["questions"]:
                _add(test, spec)
            if lesson is None:
                lesson = Lesson(course=course, title=pack["lesson"])
            lesson.objective = pack["objective"]
            lesson.content_text = pack["text"]
            lesson.interactive = pack["interactive"]
            lesson.test = test
            lesson.save()
            self.stdout.write(self.style.SUCCESS(pack["title"]))
