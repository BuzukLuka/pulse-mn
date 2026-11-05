# UML загвар ба шаардлага

| Файл | Агуулга |
|---|---|
| `pulse.mn.v2.feap` | Enterprise Architect загвар. `01–03` — анхны (v1) UC, Activity, Sequence; `04–08` — хэрэгжсэн платформ |
| `spec.py` | Шаардлага, use case, activity, класс, байршуулалтын **нэг эх өгөгдөл** |
| `pulse_model.json` | `spec.py`-ийн гаралт (EA скрипт уншина) |
| `build_ea.ps1` | `.feap`-д `04–08` багцуудыг (дахин) үүсгэнэ |
| `../requirements.csv` | Шаардлагын хүснэгт (Excel, UTF-8) — хэрэгжилтийн төлөвтэй |

## Багцууд (`04–08`)
- **04 Use Case (v2)** — 9 оролцогч (сэтгүүлч, редакц, редакцын редактор, Pulse.mn редактор, иргэн, админ, AI, төлбөр, мэдээний эх сурвалж), 24 use case; use case бүр шаардлагатайгаа `Realisation`-оор холбогдсон.
- **05 Activity (v2)** — UC-04 шалгалтын чиглүүлэлт, UC-05 мэдээ лицензлэх (ДЕМО төлбөр), UC-06 дэлхийн мэдээний AI шүүлт.
- **06 Class** — Django-ийн домэйн модель (User, Content, Membership, Purchase, Rating, Correction …).
- **07 Deployment** — Vercel (API, platform, admin), Neon, Blob, Cron, Gemini, RSS, GitHub.
- **08 Requirements** — 53 шаардлага (Functional / Non-functional / Legal), Status, Priority-тэй.

## Шинэчлэх
```bash
python docs/model/spec.py
```
```powershell
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -File docs\model\build_ea.ps1 -feap docs\model\pulse.mn.v2.feap -json docs\model\pulse_model.json
```
EA 32 бит тул 32 битийн PowerShell хэрэгтэй. Скрипт `04–08` багцыг устгаад дахин үүсгэдэг; `01–03` хөндөгдөхгүй.
