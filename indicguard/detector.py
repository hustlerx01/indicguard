"""IndicGuard: lexicon + co-occurrence prompt-injection detector for Hindi, Hinglish, Marathi and English.
A text is flagged when a *pair* of signals co-occur (e.g. override-verb + instruction-noun). Single
trigger words ("ignore", "password", "system") alone never flag, which is what keeps hard benigns down."""
import re, unicodedata

def normalize(t: str) -> str:
    t = unicodedata.normalize("NFC", t).replace("\u093c", "")  # drop nukta: ज़ -> ज
    t = re.sub("[\u200b-\u200f\u2060\ufeff]", "", t)
    return t.lower()

L = lambda *xs: re.compile("|".join(xs))
OVERRIDE_VERB = L(r"\bignore", r"disregard", r"\bforget", r"bh[uo]+l", r"cancel", r"avhelna", r"side me rakh",
                  r"अनदेखा", r"नजरअंदाज", r"भूल", r"रद्द", r"दुर्लक्ष", r"विसर", r"\bvisar")
INSTR_NOUN = L(r"instruction", r"\brules?\b", r"nirdesh", r"\bprompt", r"\bsuchana", r"\baadesh",
               r"निर्देश", r"नियम", r"सूचना", r"आदेश", r"प्रॉम्प्ट", r"बताया गया", r"सांगितल")
SCOPE = L(r"previous", r"above", r"pichl", r"pehle", r"upar", r"purane", r"\bsab\b", r"saare", r"sabhi", r"\ball\b", r"aadhi",
          r"पिछल", r"ऊपर", r"पहले", r"जो भी", r"मागील", r"वरचे", r"आधी", r"सगळ", r"सर्व")
LEAK_OBJ = L(r"system (prompt|message)", r"hidden (prompt|instruction)", r"your (instructions|prompt)",
             r"सिस्टम (प्रॉम्प्ट|संदेश)", r"छुपे", r"लपवलेल्या", r"गुप्त (सूचना|निर्देश)")
LEAK_VERB = L(r"reveal", r"print", r"show", r"repeat", r"dikha", r"bata", r"copy", r"verbatim", r"word by word",
              r"दिखा", r"बता", r"दोहरा", r"दाखव", r"सांग", r"लिही", r"उघड")
ROLE = L(r"\bdan\b", r"developer mode", r"no restrictions?", r"koi restriction nahi", r"bina rules", r"jailbreak",
         r"डेवलपर मोड", r"डेव्हलपर मोड", r"पाबंदी", r"कोई नियम नहीं", r"बंधन नसलेला", r"नियम नाहीत", r"सुरक्षा नियम बंद")
SECRET = L(r"password", r"api key", r"\bsecret\b", r"token", r"पासवर्ड", r"गुप्त जानकारी")
SEND = L(r"bhej", r"de do", r"send", r"\bsang\b", r"batao", r"भेज", r"पाठव", r"सांग", r"बताओ", r"दीजिए")
RESET_CTX = L(r"reset", r"kaise", r"कैसे", r"कसा", r"how do i", r"बदल", r"तरीका")


def detect(text: str) -> dict:
    t = normalize(text)
    hits = []
    if OVERRIDE_VERB.search(t) and (INSTR_NOUN.search(t) or (SCOPE.search(t) and re.search(r"sab kuch|सगळं|सब कुछ|जो भी", t))):
        hits.append("override")
    if LEAK_OBJ.search(t) and LEAK_VERB.search(t):
        hits.append("leak")
    if ROLE.search(t):
        hits.append("roleplay")
    if SECRET.search(t) and SEND.search(t) and not RESET_CTX.search(t):
        hits.append("exfil")
    return {"injection": bool(hits), "signals": hits}


EN_BASELINE = re.compile(r"ignore (all )?(previous|prior|above) instructions|disregard (the )?(rules|instructions)|"
                         r"system prompt|you are now|developer mode|\bdan\b|reveal your|jailbreak", re.I)

def english_baseline(text: str) -> dict:
    """Typical English-only regex filter (the kind most guardrail starter kits ship)."""
    return {"injection": bool(EN_BASELINE.search(text)), "signals": []}
