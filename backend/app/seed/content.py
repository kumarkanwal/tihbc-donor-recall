"""Exact bilingual content-series definitions from the demo specification."""

from dataclasses import dataclass

from app.models.enums import MessageCategory, SeriesKind


@dataclass(frozen=True)
class StepSeed:
    """One exact bilingual series step."""

    delay_days: int
    category: MessageCategory
    english: str
    urdu: str
    video: bool = False


@dataclass(frozen=True)
class SeriesSeed:
    """One complete active content-series definition."""

    name: str
    description: str
    kind: SeriesKind
    tags: tuple[str, ...]
    steps: tuple[StepSeed, ...]


RECALL_BUTTONS: list[dict[str, object]] = [
    {
        "id": "btn_confirm",
        "intent": "confirm",
        "labels": {"en": "Confirm", "ur": "تصدیق کریں"},
    },
    {
        "id": "btn_reschedule",
        "intent": "reschedule",
        "labels": {"en": "Reschedule", "ur": "دوسرا وقت"},
    },
    {
        "id": "btn_decline",
        "intent": "decline",
        "labels": {"en": "Not now", "ur": "ابھی نہیں"},
    },
]

REGULAR_DONOR_RECALL = SeriesSeed(
    name="Regular Donor Recall",
    description="Recall sequence for regular donors who are eligible to donate again.",
    kind=SeriesKind.PRIMARY,
    tags=("regular", "recall"),
    steps=(
        StepSeed(
            0,
            MessageCategory.UTILITY,
            "Assalam-o-Alaikum {{donor_name}}, thank you for being a regular blood donor "
            "with Team Indus Health & Blood Center. Your last donation helped patients who "
            "needed it most. You are now eligible to donate again. Would you like to visit "
            "us at {{center_name}} on {{appointment_date}}?",
            "السلام علیکم {{donor_name}}، ٹیم انڈس ہیلتھ اینڈ بلڈ سینٹر کے باقاعدہ خون عطیہ "
            "کنندہ ہونے کا شکریہ۔ آپ کے پچھلے عطیے سے ضرورت مند مریضوں کی مدد ہوئی۔ اب آپ "
            "دوبارہ خون عطیہ کر سکتے ہیں۔ کیا آپ {{appointment_date}} کو {{center_name}} "
            "تشریف لا سکتے ہیں؟",
            video=True,
        ),
        StepSeed(
            3,
            MessageCategory.UTILITY,
            "Hi {{donor_name}}, a quick reminder: patients at our center depend on regular "
            "donors like you. Your visit on {{appointment_date}} takes about 45 minutes. "
            "Please let us know if this time works for you.",
            "{{donor_name}}، ایک یاددہانی: ہمارے مریض آپ جیسے باقاعدہ عطیہ کنندگان پر انحصار "
            "کرتے ہیں۔ {{appointment_date}} کو آپ کی آمد میں تقریباً ۴۵ منٹ لگیں گے۔ براہِ "
            "کرم بتائیں کہ کیا یہ وقت آپ کے لیے مناسب ہے۔",
        ),
        StepSeed(
            7,
            MessageCategory.UTILITY,
            "{{donor_name}}, one donation can help up to three patients. If "
            "{{appointment_date}} does not suit you, tap Reschedule and choose a time that "
            "works better.",
            "{{donor_name}}، ایک عطیہ تین مریضوں تک کی مدد کر سکتا ہے۔ اگر "
            '{{appointment_date}} آپ کے لیے مناسب نہیں تو "دوسرا وقت" دبائیں اور اپنی '
            "سہولت کا وقت منتخب کریں۔",
        ),
    ),
)

LAPSED_DONOR_WIN_BACK = SeriesSeed(
    name="Lapsed Donor Win-back",
    description="Re-engagement sequence for donors who have not donated recently.",
    kind=SeriesKind.PRIMARY,
    tags=("lapsed", "win-back"),
    steps=(
        StepSeed(
            0,
            MessageCategory.MARKETING,
            "Assalam-o-Alaikum {{donor_name}}, we have missed you at Team Indus Health & "
            "Blood Center. It has been a while since your last donation, and patients still "
            "need donors like you. Would you like to donate again at {{center_name}} on "
            "{{appointment_date}}?",
            "السلام علیکم {{donor_name}}، ٹیم انڈس ہیلتھ اینڈ بلڈ سینٹر میں ہمیں آپ کی کمی "
            "محسوس ہوئی۔ آپ کے پچھلے عطیے کو کافی وقت گزر چکا ہے اور مریضوں کو آج بھی آپ "
            "جیسے عطیہ کنندگان کی ضرورت ہے۔ کیا آپ {{appointment_date}} کو {{center_name}} "
            "پر دوبارہ خون عطیہ کرنا چاہیں گے؟",
            video=True,
        ),
        StepSeed(
            3,
            MessageCategory.MARKETING,
            "Hi {{donor_name}}, every day, patients with thalassemia and patients in surgery "
            "need blood. Your support makes a real difference. Reply with a day that suits "
            "you, or tap a button below.",
            "{{donor_name}}، تھیلیسیمیا کے مریضوں اور آپریشن کے مریضوں کو روزانہ خون کی ضرورت "
            "ہوتی ہے۔ آپ کا تعاون واقعی فرق ڈالتا ہے۔ اپنی سہولت کا دن لکھ کر بھیجیں یا نیچے "
            "دیا گیا بٹن دبائیں۔",
        ),
        StepSeed(
            7,
            MessageCategory.MARKETING,
            "{{donor_name}}, we would be glad to welcome you back. Donating is safe and takes "
            "less than an hour. Shall we book your visit?",
            "{{donor_name}}، ہمیں آپ کو دوبارہ خوش آمدید کہہ کر خوشی ہوگی۔ خون کا عطیہ محفوظ "
            "ہے اور اس میں ایک گھنٹے سے کم وقت لگتا ہے۔ کیا ہم آپ کی آمد کا وقت طے کر دیں؟",
        ),
    ),
)

FIRST_TIME_DONOR_RETURN = SeriesSeed(
    name="First-Time Donor Return",
    description="Return sequence for donors after their first donation.",
    kind=SeriesKind.PRIMARY,
    tags=("first-time", "retention"),
    steps=(
        StepSeed(
            0,
            MessageCategory.UTILITY,
            "Assalam-o-Alaikum {{donor_name}}, thank you for your first blood donation with "
            "Team Indus Health & Blood Center. Your gift has already helped a patient in need. "
            "You are now eligible to donate again. Would you like to visit {{center_name}} on "
            "{{appointment_date}}?",
            "السلام علیکم {{donor_name}}، ٹیم انڈس ہیلتھ اینڈ بلڈ سینٹر میں پہلی بار خون عطیہ "
            "کرنے کا شکریہ۔ آپ کے عطیے سے ایک ضرورت مند مریض کی مدد ہو چکی ہے۔ اب آپ دوبارہ "
            "خون عطیہ کر سکتے ہیں۔ کیا آپ {{appointment_date}} کو {{center_name}} تشریف لانا "
            "چاہیں گے؟",
            video=True,
        ),
        StepSeed(
            4,
            MessageCategory.UTILITY,
            "Hi {{donor_name}}, donors who return are the backbone of our blood supply. Let us "
            "know if {{appointment_date}} works for you, or choose another time.",
            "{{donor_name}}، دوبارہ آنے والے عطیہ کنندگان ہی ہمارے بلڈ بینک کی بنیاد ہیں۔ "
            "بتائیں کہ کیا {{appointment_date}} آپ کے لیے مناسب ہے، یا کوئی اور وقت منتخب کریں۔",
        ),
    ),
)

FINAL_FOLLOW_UP = SeriesSeed(
    name="Final Follow-up",
    description="Final automated outreach before coordinator escalation.",
    kind=SeriesKind.SECONDARY,
    tags=("follow-up",),
    steps=(
        StepSeed(
            0,
            MessageCategory.UTILITY,
            "Hi {{donor_name}}, we have not heard from you yet. If you are available to donate "
            "this month, please tap Confirm or choose another time.",
            "{{donor_name}}، ہمیں ابھی تک آپ کا جواب نہیں ملا۔ اگر آپ اس مہینے خون عطیہ کر "
            'سکتے ہیں تو "تصدیق کریں" دبائیں یا کوئی اور وقت منتخب کریں۔',
        ),
        StepSeed(
            3,
            MessageCategory.UTILITY,
            "{{donor_name}}, this is our last reminder for now. A member of our team may call "
            "you to help find a suitable time. Thank you for supporting our patients.",
            "{{donor_name}}، یہ فی الحال ہماری آخری یاددہانی ہے۔ ہماری ٹیم کا کوئی رکن مناسب "
            "وقت طے کرنے کے لیے آپ کو کال کر سکتا ہے۔ ہمارے مریضوں کا ساتھ دینے کا شکریہ۔",
        ),
    ),
)

SERIES_SEEDS = (
    REGULAR_DONOR_RECALL,
    LAPSED_DONOR_WIN_BACK,
    FIRST_TIME_DONOR_RETURN,
    FINAL_FOLLOW_UP,
)
