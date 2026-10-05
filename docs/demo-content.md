# Demo Content

Content used by the seed script (`backend/app/seed/`). Text must be used exactly as written.
Variables: `{{donor_name}}`, `{{center_name}}`, `{{appointment_date}}`. No emojis.

Business display name: **Team Indus Health & Blood Center**.

---

## 1. Shared Assets

| Asset | Location in repo | Notes |
|---|---|---|
| Recall video | `backend/app/seed/assets/donor-recall.mp4` | MP4 (H.264 + AAC), under 16 MB, about 24 seconds. Seed copies it to `MEDIA_STORAGE_DIR` |
| Video thumbnail | `backend/app/seed/assets/donor-recall-thumb.jpg` | First frame or end card, 16:9 |
| Logo | `frontend/public/images/IHHN-Logo-02-150x150.webp` | Simulator profile picture |

## 2. Quick-Reply Buttons (used on every recall step)

| Button id | Intent | English | Urdu |
|---|---|---|---|
| `btn_confirm` | confirm | Confirm | تصدیق کریں |
| `btn_reschedule` | reschedule | Reschedule | دوسرا وقت |
| `btn_decline` | decline | Not now | ابھی نہیں |

## 3. Primary Series

### 3.1 Regular Donor Recall
Kind: `primary` · Tags: `regular`, `recall` · Languages: en, ur · Response window: 48 hours

**Step 1 · Day 0 · Utility · Video**
- EN: Assalam-o-Alaikum {{donor_name}}, thank you for being a regular blood donor with Team Indus Health & Blood Center. Your last donation helped patients who needed it most. You are now eligible to donate again. Would you like to visit us at {{center_name}} on {{appointment_date}}?
- UR: السلام علیکم {{donor_name}}، ٹیم انڈس ہیلتھ اینڈ بلڈ سینٹر کے باقاعدہ خون عطیہ کنندہ ہونے کا شکریہ۔ آپ کے پچھلے عطیے سے ضرورت مند مریضوں کی مدد ہوئی۔ اب آپ دوبارہ خون عطیہ کر سکتے ہیں۔ کیا آپ {{appointment_date}} کو {{center_name}} تشریف لا سکتے ہیں؟

**Step 2 · Day 3 · Utility · Text**
- EN: Hi {{donor_name}}, a quick reminder: patients at our center depend on regular donors like you. Your visit on {{appointment_date}} takes about 45 minutes. Please let us know if this time works for you.
- UR: {{donor_name}}، ایک یاددہانی: ہمارے مریض آپ جیسے باقاعدہ عطیہ کنندگان پر انحصار کرتے ہیں۔ {{appointment_date}} کو آپ کی آمد میں تقریباً ۴۵ منٹ لگیں گے۔ براہِ کرم بتائیں کہ کیا یہ وقت آپ کے لیے مناسب ہے۔

**Step 3 · Day 7 · Utility · Text**
- EN: {{donor_name}}, one donation can help up to three patients. If {{appointment_date}} does not suit you, tap Reschedule and choose a time that works better.
- UR: {{donor_name}}، ایک عطیہ تین مریضوں تک کی مدد کر سکتا ہے۔ اگر {{appointment_date}} آپ کے لیے مناسب نہیں تو "دوسرا وقت" دبائیں اور اپنی سہولت کا وقت منتخب کریں۔

### 3.2 Lapsed Donor Win-back
Kind: `primary` · Tags: `lapsed`, `win-back` · Languages: en, ur · Response window: 48 hours

**Step 1 · Day 0 · Marketing · Video**
- EN: Assalam-o-Alaikum {{donor_name}}, we have missed you at Team Indus Health & Blood Center. It has been a while since your last donation, and patients still need donors like you. Would you like to donate again at {{center_name}} on {{appointment_date}}?
- UR: السلام علیکم {{donor_name}}، ٹیم انڈس ہیلتھ اینڈ بلڈ سینٹر میں ہمیں آپ کی کمی محسوس ہوئی۔ آپ کے پچھلے عطیے کو کافی وقت گزر چکا ہے اور مریضوں کو آج بھی آپ جیسے عطیہ کنندگان کی ضرورت ہے۔ کیا آپ {{appointment_date}} کو {{center_name}} پر دوبارہ خون عطیہ کرنا چاہیں گے؟

**Step 2 · Day 3 · Marketing · Text**
- EN: Hi {{donor_name}}, every day, patients with thalassemia and patients in surgery need blood. Your support makes a real difference. Reply with a day that suits you, or tap a button below.
- UR: {{donor_name}}، تھیلیسیمیا کے مریضوں اور آپریشن کے مریضوں کو روزانہ خون کی ضرورت ہوتی ہے۔ آپ کا تعاون واقعی فرق ڈالتا ہے۔ اپنی سہولت کا دن لکھ کر بھیجیں یا نیچے دیا گیا بٹن دبائیں۔

**Step 3 · Day 7 · Marketing · Text**
- EN: {{donor_name}}, we would be glad to welcome you back. Donating is safe and takes less than an hour. Shall we book your visit?
- UR: {{donor_name}}، ہمیں آپ کو دوبارہ خوش آمدید کہہ کر خوشی ہوگی۔ خون کا عطیہ محفوظ ہے اور اس میں ایک گھنٹے سے کم وقت لگتا ہے۔ کیا ہم آپ کی آمد کا وقت طے کر دیں؟

### 3.3 First-Time Donor Return
Kind: `primary` · Tags: `first-time`, `retention` · Languages: en, ur · Response window: 48 hours

**Step 1 · Day 0 · Utility · Video**
- EN: Assalam-o-Alaikum {{donor_name}}, thank you for your first blood donation with Team Indus Health & Blood Center. Your gift has already helped a patient in need. You are now eligible to donate again. Would you like to visit {{center_name}} on {{appointment_date}}?
- UR: السلام علیکم {{donor_name}}، ٹیم انڈس ہیلتھ اینڈ بلڈ سینٹر میں پہلی بار خون عطیہ کرنے کا شکریہ۔ آپ کے عطیے سے ایک ضرورت مند مریض کی مدد ہو چکی ہے۔ اب آپ دوبارہ خون عطیہ کر سکتے ہیں۔ کیا آپ {{appointment_date}} کو {{center_name}} تشریف لانا چاہیں گے؟

**Step 2 · Day 4 · Utility · Text**
- EN: Hi {{donor_name}}, donors who return are the backbone of our blood supply. Let us know if {{appointment_date}} works for you, or choose another time.
- UR: {{donor_name}}، دوبارہ آنے والے عطیہ کنندگان ہی ہمارے بلڈ بینک کی بنیاد ہیں۔ بتائیں کہ کیا {{appointment_date}} آپ کے لیے مناسب ہے، یا کوئی اور وقت منتخب کریں۔

## 4. Secondary Series

### 4.1 Final Follow-up
Kind: `secondary` · Tags: `follow-up` · Languages: en, ur · Response window: 48 hours

**Step 1 · Day 0 · Utility · Text**
- EN: Hi {{donor_name}}, we have not heard from you yet. If you are available to donate this month, please tap Confirm or choose another time.
- UR: {{donor_name}}، ہمیں ابھی تک آپ کا جواب نہیں ملا۔ اگر آپ اس مہینے خون عطیہ کر سکتے ہیں تو "تصدیق کریں" دبائیں یا کوئی اور وقت منتخب کریں۔

**Step 2 · Day 3 · Utility · Text**
- EN: {{donor_name}}, this is our last reminder for now. A member of our team may call you to help find a suitable time. Thank you for supporting our patients.
- UR: {{donor_name}}، یہ فی الحال ہماری آخری یاددہانی ہے۔ ہماری ٹیم کا کوئی رکن مناسب وقت طے کرنے کے لیے آپ کو کال کر سکتا ہے۔ ہمارے مریضوں کا ساتھ دینے کا شکریہ۔

## 5. Automatic Bot Replies (`backend/app/services/replies/`)

| Key | English | Urdu |
|---|---|---|
| `confirm_thanks` | Thank you, {{donor_name}}. Your visit is confirmed for {{appointment_date}} at {{center_name}}. Please eat well and drink plenty of water before donating. | شکریہ {{donor_name}}۔ آپ کی آمد {{appointment_date}} کو {{center_name}} پر کنفرم ہو گئی ہے۔ عطیہ سے پہلے اچھی طرح کھانا کھائیں اور زیادہ پانی پئیں۔ |
| `reschedule_offer` | No problem. Here are the next available times. Please choose one, or type a day that suits you. | کوئی مسئلہ نہیں۔ یہ اگلے دستیاب اوقات ہیں۔ ان میں سے ایک منتخب کریں، یا اپنی سہولت کا دن لکھ کر بھیجیں۔ |
| `reschedule_confirmed` | Done. Your new visit is booked for {{appointment_date}} at {{center_name}}. Thank you, {{donor_name}}. | ہو گیا۔ آپ کی نئی آمد {{appointment_date}} کو {{center_name}} پر طے ہو گئی ہے۔ شکریہ {{donor_name}}۔ |
| `decline_ask_reason` | We understand, {{donor_name}}. May we know the reason? This helps us contact you at a better time. | ہم سمجھتے ہیں {{donor_name}}۔ کیا ہم وجہ جان سکتے ہیں؟ اس سے ہمیں بہتر وقت پر آپ سے رابطہ کرنے میں مدد ملے گی۔ |
| `decline_closing` | Thank you for letting us know. We will reach out again later. Take care. | بتانے کا شکریہ۔ ہم بعد میں دوبارہ رابطہ کریں گے۔ اپنا خیال رکھیں۔ |
| `needs_call` | Thank you. A coordinator from Team Indus will contact you shortly. | شکریہ۔ ٹیم انڈس کا ایک کوآرڈینیٹر جلد آپ سے رابطہ کرے گا۔ |
| `no_slots` | Our coordinator will call you to find a suitable time. | ہمارا کوآرڈینیٹر مناسب وقت طے کرنے کے لیے آپ کو کال کرے گا۔ |

Decline reason buttons (with `decline_ask_reason`):

| Button id | Reason | English | Urdu |
|---|---|---|---|
| `btn_reason_travelling` | travelling | Travelling | سفر میں ہوں |
| `btn_reason_health` | health | Health reason | صحت کی وجہ |
| `btn_reason_other` | other | Other | کوئی اور وجہ |

Slot buttons label format: EN `Sat 10 Oct, 11:00 AM` · UR `ہفتہ ۱۰ اکتوبر، صبح ۱۱ بجے`.

## 6. Seed Data Settings

- **Centers (placeholders, editable):** `Korangi Campus Blood Center`, `North Nazimabad Donor Center`.
- **Slots:** each center, every day for the next 21 demo days, 9:00 AM to 4:00 PM hourly, capacity 4.
  Some slots pre-filled so availability looks realistic.
- **Default appointment date** for `{{appointment_date}}`: campaign start + 2 days, 10:00 AM, at the donor's
  nearest center (by city; default Korangi). For an already-running campaign, use the later of the
  campaign start and the current demo-clock time before adding two days. If that slot is unavailable,
  search forward through 14 days at the same center, then at either center. If no slot exists, leave the
  appointment unbooked and render `at your earliest convenience` (EN) or
  `اپنی جلد از جلد سہولت کے مطابق` (UR) for `{{appointment_date}}`.
- **Donors:** about 200, segments roughly 50% regular, 30% lapsed, 20% first-time; languages about 60% Urdu,
  40% English; about 5% unreachable (`sim_reachable=false`), about 25% without read receipts.
- **Sample upload file:** `backend/app/seed/assets/sample-donors.xlsx` with 40 rows, including 5 invalid
  rows (bad phone, unknown segment, missing name, duplicate phone, future donation date).
- **Campaigns:** two running ("October Regular Recall" and "Lapsed Donor Win-back"), with a realistic mix of
  statuses; one draft campaign ready for the live demo using the sample upload.
