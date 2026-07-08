# Plani Hap-pas-Hapi i Ekzekutimit — Ndarja e Punës për 4 Zhvillues

**Projekti:** Online Retail Analytics Platform
**Ekipi:** 4 zhvillues (Dev A, Dev B, Dev C, Dev D)
**Qëllimi i këtij dokumenti:** Të tregojë me radhë **çfarë bëhet, kush e bën, dhe si lidhet me hapin pasardhës**, duke organizuar punën nëpërmjet **branch-eve Git** dhe ndarjes së qartë të skedarëve.

---

## 0. Ndarja e Roleve (fikse gjatë gjithë projektit)

| Rol | Përgjegjësia kryesore | Branch kryesor |
|-----|-----------------------|----------------|
| **Dev A — Data Engineer** | Pastrimi i të dhënave, pipeline i përpunimit (pandas/numpy), funksionet e analizës bazë | `feature/data-pipeline` |
| **Dev B — Data Analyst / BI** | EDA e thelluar, RFM, KPI, motori i rekomandimeve, logjika e "what-if" | `feature/analytics-engine` |
| **Dev C — Frontend/Streamlit Developer** | Ndërtimi i aplikacionit Streamlit, dashboard, UI, integrimi i grafikëve dhe modulit të eksportimit | `feature/streamlit-app` |
| **Dev D — QA & DevOps / Dokumentacion** | Testimi i njësive (unit tests), konfigurimi i mjedisit, deployment, dokumentacioni teknik | `feature/testing-and-docs` |

> Këto role nuk janë të izoluara — çdo person varet nga output-i i personit para vetes. Prandaj radhitja e hapave më poshtë është **kritike**.

---

## Strategjia e Branch-eve Git

```
main
 └── develop                        ← branch integrimi kryesor
      ├── feature/data-pipeline      ← Dev A
      ├── feature/analytics-engine   ← Dev B
      ├── feature/streamlit-app      ← Dev C
      └── feature/testing-and-docs   ← Dev D
```

**Rregullat:**
1. Askush nuk commit-on drejtpërdrejt në `main` ose `develop`.
2. Çdo feature branch bashkohet në `develop` vetëm me **Pull Request** + aprovim nga një dev tjetër.
3. `main` merr merge vetëm kur `develop` është testuar plotësisht (pas Fazës 5).
4. Commit-et duhet të jenë të vogla dhe të shpeshta me mesazhe përshkruese, p.sh.: `feat(data): add clean_data() function with refund handling`.

---

## FAZA 1 — Themeli i të Dhënave (bazë për gjithçka tjetër)

### Hapi 1.0 — Setup fillestar i repozitorit
**Kush:** Dev D  
**Branch:** `develop` (direkt, vetëm një herë)  
**Skedarë:**
- `README.md` — struktura e projektit
- `requirements.txt` — të gjitha varësitë Python
- `.gitignore` — përjashton `data/raw/`, `venv/`, `__pycache__/`, etj.
- `data/` — struktura e dosjeve (raw, processed)

**Output:** Repositori i gatshëm për t'u klonuar nga të gjithë.  
**Lidhet me hapin tjetër:** Pa këtë, askush tjetër nuk mund të fillojë punën.

---

### Hapi 1.1 — Eksplorimi fillestar i datasetit
**Kush:** Dev A  
**Branch:** `feature/data-pipeline`  
**Skedarë:**
- `notebooks/01_data_exploration.ipynb`

**Çfarë bën:**
- Shkarkon "Online Retail II" nga UCI dhe e hap me pandas.
- Shikon strukturën, tipet e kolonave, vlerat mungesë, duplicates.
- Dokumenton problemet e gjetura (`CustomerID` bosh, `Quantity` negative, `InvoiceNo` me "C").

**Output:** Notebook `01_data_exploration.ipynb` + listë problemesh të dokumentuara si komente.  
**Lidhet me hapin tjetër:** Lista e problemeve është input direkt për 1.2.

---

### Hapi 1.2 — Pastrimi dhe standardizimi i të dhënave
**Kush:** Dev A  
**Branch:** `feature/data-pipeline`  
**Skedarë:**
- `src/data_cleaning.py` ← **skedari kryesor i dorëzimit**
- `data/cleaned_retail_data.csv` ← dataset i pastruar

**Çfarë bën:**
- Trajton `CustomerID` mungesë (shënon si "Guest" ose izolon).
- Vendos rregull për `Quantity` negative → klasifikon si kthime/refunds.
- Filtron `UnitPrice <= 0`.
- Konverton `InvoiceDate` në format datetime.
- Krijon kolonën `Revenue = Quantity * UnitPrice`.
- E kthen gjithë procesin në **funksion të ripërdorshëm**: `clean_data(df) -> df_clean`.

**Output:** `src/data_cleaning.py` funksional + `data/cleaned_retail_data.csv`.  
**PR:** `feature/data-pipeline` → `develop` (pas aprovimit hapen branch-et e tjerë).

> ⚠️ **Pikë kritike:** Ky PR duhet të bashkohet në `develop` **para se Dev B dhe Dev C të fillojnë** punën e tyre, sepse të dy varen nga `clean_data()`.

---

## FAZA 2 — Analiza (varet nga Faza 1)

### Hapi 2.1 — EDA e thelluar dhe funksionet e analizës
**Kush:** Dev B  
**Branch:** `feature/analytics-engine`  
**Skedarë:**
- `notebooks/02_eda_analysis.ipynb`
- `src/analysis.py` ← funksionet e analizës si module

**Çfarë bën:**
- Analizë e shitjeve sipas kohës (mujore/javore/orare).
- Top produkte sipas sasisë dhe të ardhurave; produkte me shitje të ulëta.
- Analiza e fitimit/humbjes: të ardhura totale, humbje nga kthimet.
- Analiza gjeografike sipas `Country`.
- Shkruan funksione të veçuara si `get_monthly_revenue(df)`, `get_top_products(df)`, `get_kpis(df)` — jo vetëm kod "inline" në notebook.

**Output:** `src/analysis.py` me funksione të thirrshme + notebook dokumentues.  
**Lidhet me hapin tjetër:** Këto funksione thirren nga Dev C brenda Streamlit-it.

---

### Hapi 2.2 — Segmentimi RFM dhe motori i rekomandimeve
**Kush:** Dev B  
**Branch:** `feature/analytics-engine`  
**Skedarë:**
- `notebooks/03_rfm_recommendations.ipynb`
- `src/recommendation_engine.py` ← **skedari kryesor i dorëzimit**

**Çfarë bën:**
- Llogarit Recency, Frequency, Monetary për çdo klient.
- Ndan klientët në segmente (VIP, në rrezik, të rinj, etj.).
- Shkruan rregullat e rekomandimeve (rule-based): p.sh. nëse marzhi i produktit X është i ulët por volumi i lartë → sugjero rishikim çmimi.
- Për çdo rekomandim, llogarit një **vlerësim numerik të mundshëm të ndikimit në fitim**.
- Shkruan funksionin kryesor `generate_recommendations(df) -> list[dict]`.

**Output:** `src/recommendation_engine.py` funksional.  
**Lidhet me hapin tjetër:** Ky funksion është "truri" i seksionit të rekomandimeve dhe modulit "what-if" në Streamlit.

---

### Hapi 2.3 — Vizualizimet dhe raporti fillestar
**Kush:** Dev B  
**Branch:** `feature/analytics-engine`  
**Skedarë:**
- `notebooks/04_visualisations.ipynb`
- `src/visualisations.py` ← funksionet Plotly si module

**Çfarë bën:**
- Krijon grafikët kryesorë me plotly (trend mujor, top produkte, heatmap, RFM scatter, hartë gjeografike).
- Çdo grafik është funksion i ripërdorshëm: `plot_monthly_revenue(df)`, `plot_rfm_segments(df)`, etj.
- Përgatit një raport (Excel/PDF) me gjetjet kryesore.

**Output:** `src/visualisations.py` + notebook demonstrues.  
**PR:** `feature/analytics-engine` → `develop`.

> Preferohet plotly **që nga fillimi** për të shmangur rishkrimin kur grafikët integrohen në Streamlit.

---

## FAZA 3 — Aplikacioni Streamlit (varet nga Faza 1 + Faza 2)

### Hapi 3.1 — Skeleti i aplikacionit dhe upload CSV
**Kush:** Dev C  
**Branch:** `feature/streamlit-app`  
**Skedarë:**
- `app/app.py` ← skedari kryesor i aplikacionit

**Çfarë bën:**
- Krijon strukturën bazë të Streamlit-it (navigimi, seksionet/faqet).
- Ndërton komponentin e upload-it të CSV.
- Thërret `clean_data()` (nga `src/data_cleaning.py`) automatikisht pas upload-it.
- Validim: krahason kolonat e CSV-së së re me formatin origjinal; shfaq mesazh gabimi nëse nuk përputhet.

**Output:** `app/app.py` funksional që pranon CSV, e pastron dhe tregon konfirmim.  
**Lidhet me hapin tjetër:** Pa këtë, asnjë analizë/grafik s'ka nga vjen.

---

### Hapi 3.2 — Dashboard dhe integrimi i analizave
**Kush:** Dev C  
**Branch:** `feature/streamlit-app`  
**Skedarë:**
- `app/app.py` (vazhdim)

**Çfarë bën:**
- Shfaq KPI kryesore duke thirrur `get_kpis()` nga `src/analysis.py`.
- Integron grafikët plotly duke thirrur funksionet nga `src/visualisations.py`.
- Ndërton seksionin e rekomandimeve duke thirrur `generate_recommendations()` nga `src/recommendation_engine.py`.
- Shton seksionin "Customer Analysis" (RFM segments, churn risk).
- Shton seksionin "Geographic Performance" (hartë interaktive).

**Output:** Dashboard interaktiv i plotë brenda `app/app.py`.

---

### Hapi 3.3 — Moduli "What-if" dhe eksportimi
**Kush:** Dev C (UI) + Dev B (logjika, nëse duhet zgjerim)  
**Branch:** `feature/streamlit-app`  
**Skedarë:**
- `app/app.py` (vazhdim)
- `src/export_utils.py` ← funksioni i gjenerimit të raportit Excel

**Çfarë bën:**
- Dev C ndërton inputet (slider/input fusha) në Streamlit për skenaret "what-if".
- Integron projeksionin e fitimit bazuar në formulat nga `src/recommendation_engine.py`.
- Buton "Shkarko Raportin" që gjeneron Excel me KPI, grafikë dhe rekomandime.

**Output:** Seksioni "What-if" + butoni i eksportimit funksionalë.  
**PR:** `feature/streamlit-app` → `develop`.

---

## FAZA 4 — Testimi dhe Sigurimi i Cilësisë (paralel me Fazën 3)

### Hapi 4.1 — Konfigurimi i mjedisit të testimit
**Kush:** Dev D  
**Branch:** `feature/testing-and-docs`  
**Skedarë:**
- `tests/__init__.py`
- `tests/test_data_cleaning.py`
- `tests/test_analysis.py`
- `tests/test_recommendation_engine.py`

**Çfarë bën:**
- Shkruan teste njësi (unit tests) me `pytest` për:
  - `clean_data()`: teston trajtimin e refunds, vlerave mungesë, tipeve të kolonave.
  - Funksionet e `analysis.py`: teston saktësinë e KPI-ve dhe agregimeve.
  - `generate_recommendations()`: teston outputin e saktë format dhe kushtet e rregullave.
- Shkruan dataset-e të vogla "fixture" si input testimi.

**Output:** Suite testesh të ekzekutueshme me `pytest`.  
**Shënim paralelizmi:** Dev D mund ta fillojë këtë **njëkohësisht** me Fazën 3, pa pritur mbarimin e Streamlit-it.

---

### Hapi 4.2 — Testimi i integruar dhe rregullimi
**Kush:** Dev A, B, C, D (secili teston pjesën e vet + testim i kryqëzuar)  
**Branch:** `feature/testing-and-docs`  
**Çfarë bëhet:**
- Dev A teston `clean_data()` me 2-3 CSV muaj-provë me probleme të ndryshme.
- Dev B verifikon saktësinë e rekomandimeve dhe projeksioneve.
- Dev C teston rrjedhën e plotë (upload → dashboard → rekomandime → what-if → export).
- Dev D ekzekuton të gjitha testet dhe dokumenton gabimet.

**Output:** Raport gabimesh (bug list) + korrigjime të bëra.

---

## FAZA 5 — Dokumentimi dhe Dorëzimi

### Hapi 5.1 — Dokumentacioni teknik dhe udhëzuesi i përdorimit
**Kush:** Dev D (koordinon), me kontribut nga të gjithë  
**Branch:** `feature/testing-and-docs`  
**Skedarë:**
- `README.md` — përditësohet me udhëzime të plota setup dhe usage
- `docs/user_guide.md` — si bëhet upload, si lexohen rekomandimet, si përdoret what-if
- `docs/technical_docs.md` — arkitektura, skedarët, si mirëmbahet/zgjerohet aplikacioni

**Output:** Dokumentacion final i gatshëm për klientin.  
**PR final:** `feature/testing-and-docs` → `develop` → `main`.

---

## Tabela Përmbledhëse e Varësive (Dependency Map)

| Hapi | Kush | Skedarët kryesorë | Varet nga | Kush pret këtë output |
|------|------|-------------------|-----------|------------------------|
| 1.0 Setup repozitori | Dev D | `README`, `requirements.txt`, `.gitignore` | — | Të gjithë |
| 1.1 Eksplorim | Dev A | `notebooks/01_data_exploration.ipynb` | 1.0 | 1.2 |
| 1.2 Pastrim (`clean_data()`) | Dev A | `src/data_cleaning.py` | 1.1 | 2.1, 3.1 |
| 2.1 EDA (funksione analize) | Dev B | `src/analysis.py` | 1.2 | 3.2 |
| 2.2 RFM + Rekomandime | Dev B | `src/recommendation_engine.py` | 1.2, 2.1 | 3.2, 3.3 |
| 2.3 Vizualizime | Dev B | `src/visualisations.py` | 2.1 | 3.2 |
| 3.1 Upload CSV (Streamlit) | Dev C | `app/app.py` | 1.2 | 3.2 |
| 3.2 Dashboard | Dev C | `app/app.py` | 2.1, 2.2, 2.3, 3.1 | 3.3 |
| 3.3 What-if + Export | Dev C + Dev B | `app/app.py`, `src/export_utils.py` | 2.2, 3.2 | 4.2 |
| 4.1 Unit Tests | Dev D | `tests/*.py` | 1.2, 2.1, 2.2 | 4.2 |
| 4.2 Testim i integruar | Të gjithë | — | 3.3, 4.1 | 5.1 |
| 5.1 Dokumentim/Dorëzim | Dev D | `docs/`, `README.md` | 4.2 | — |

---

## Sekuenca e Pull Requests

```
PR #1  feature/data-pipeline      → develop   (pas Hapit 1.2) ← bllokuese, të gjithë presin
PR #2  feature/analytics-engine   → develop   (pas Hapit 2.3)
PR #3  feature/streamlit-app      → develop   (pas Hapit 3.3)
PR #4  feature/testing-and-docs   → develop   (pas Hapit 4.2)
PR #5  develop                    → main      (release final)
```

> Çdo PR duhet të ketë të paktën **1 aprovim** nga një zhvillues tjetër përpara merge-it.

---

## Rregulli i Artë i Koordinimit

1. **Dev A punon i pari** dhe jep `clean_data()` sa më shpejt — çdo vonesë këtu vonon të gjithë ekipin.
2. **Dev D mund të fillojë paralelisht** me setup-in e repozitorit dhe strukturën e testeve që në ditën e parë.
3. **Dev B dhe Dev C punojnë në "handoff" të vazhdueshëm**: çdo funksion analize që shkruan Dev B duhet menjëherë t'i kalohet Dev C si funksion i thirrshëm (jo si notebook i veçantë), përndryshe Dev C mbetet i bllokuar.
4. **Stand-up i shkurtër çdo ditë** (10-15 min) mes 4 zhvilluesve: "çfarë përfundova, çfarë po pres, a jam i bllokuar".

---

*Ky plan mund të përshtatet nëse ekipi vendos të punojë me sprint-e (p.sh. Scrum 1-javor) — struktura e varësive mbetet e njëjtë, ndryshon vetëm ritmi i dorëzimit.*
