# Plani i Projektit: Online Retail Analytics Platform

**Klienti:** [Emri i klientit]
**Dataset bazë:** Online Retail II — UCI Machine Learning Repository ([link](https://archive.ics.uci.edu/dataset/502/online+retail+ii))
**Referencë ekzistuese (bazë e thjeshtë, jo e mjaftueshme):** [Online-Retail-II-EDA (GitHub)](https://github.com/blinasopjani/Online-Retail-II-Exploratory-Data-Analysis)
**Data e hartimit:** Korrik 2026

---

## 1. Përmbledhje Ekzekutive

Projekti synon të ndërtojë një **platformë analitike të kompletuar** për të dhëna të shitjeve retail, e cila:

1. Analizon në thellësi datasetin historik "Online Retail II" (shitje, produkte, fitim/humbje, sjellje klientësh, sezonalitet).
2. Prodhon vizualizime profesionale dhe një raport me gjetje e rekomandime konkrete biznesi.
3. Shndërrohet në një **aplikacion web interaktiv në Streamlit**, ku klienti mund të ngarkojë (upload) çdo muaj një dataset të ri CSV me të njëjtin format, dhe të marrë automatikisht analiza, vizualizime dhe rekomandime.
4. Mundëson eksportimin e raporteve dhe simulimin e ndikimit të rekomandimeve në fitim.

Ky nuk është thjesht një EDA (Exploratory Data Analysis) statike si në repon referencë, por një **sistem i vazhdueshëm (recurring analytics tool)** i përdorshëm nga vetë klienti pa nevojën e ndërhyrjes tonë çdo herë.

---

## 2. Objektivat e Projektit

| # | Objektivi | Rezultati i pritur |
|---|-----------|---------------------|
| 1 | Analizë e thellë e të dhënave historike | Raport + notebook me gjetje statistikore të vlefshme |
| 2 | Identifikimi i produkteve/klientëve/rajoneve fitimprurëse dhe jofitimprurëse | Lista e prioriteteve për veprim |
| 3 | Ndërtimi i një plani konkret rritjeje fitimi | Dokument strategjik me hapa të matshëm |
| 4 | Zhvillimi i aplikacionit Streamlit "self-service" | Web app funksional, i lehtë për t'u përdorur nga klienti |
| 5 | Simulim/parashikim i ndikimit të rekomandimeve në fitim | Modul "what-if" brenda aplikacionit |

---

## 3. Fushëveprimi (Scope)

### Përfshihet:
- Pastrimi dhe përgatitja e të dhënave (data cleaning, handling missing values, refunds, outliers).
- Analizë me **pandas** dhe **numpy**: shitjet sipas kohës, produkteve, vendeve, klientëve.
- Analiza e fitimit/humbjes (të ardhurat bruto, kthimet/refunds si humbje, marzhi kur ka të dhëna kosto).
- Segmentim klientësh (p.sh. **RFM Analysis** – Recency, Frequency, Monetary).
- Vizualizime (matplotlib/seaborn/plotly): trendet mujore, top produkte, harta gjeografike e shitjeve, kohorta klientësh.
- Aplikacion Streamlit me:
  - Upload të CSV të ri mujor.
  - Validim automatik i formatit.
  - Dashboard interaktiv me grafikë dinamikë.
  - Seksion rekomandimesh të gjeneruara automatikisht (rule-based + statistikore).
  - Projeksion i rritjes së fitimit nëse zbatohen rekomandimet.
- Dokumentim teknik dhe udhëzues përdorimi (user guide) për klientin.

### Nuk përfshihet (përveç nëse kërkohet shtesë):
- Integrim direkt me sisteme POS/ERP të klientit (mund të jetë fazë e ardhshme).
- Modele machine learning të avancuara për parashikim (forecasting me ML) — mund të propozohet si Faza 2.
- Autentikim multi-user me role të ndryshme (mund të shtohet më vonë nëse nevojitet).

---

## 4. Arkitektura e Zgjidhjes

```
┌─────────────────────┐
│   Klienti (Browser) │
└──────────┬───────────┘
           │ upload CSV / shikon dashboard
           ▼
┌─────────────────────────────┐
│      Streamlit App          │
│  - Validim & parsim CSV     │
│  - Pandas/Numpy processing  │
│  - Vizualizime (Plotly)     │
│  - Motori i rekomandimeve   │
└─────────────────────────────┘
```

**Stack teknik i propozuar:**
- **Python 3.11+**
- **pandas, numpy** – përpunimi i të dhënave
- **matplotlib / seaborn / plotly** – vizualizime (plotly preferohet për interaktivitet në Streamlit)
- **Streamlit** – interface web
- **scikit-learn** (opsionale, për segmentim/klasifikim klientësh)
- **Docker** (opsionale, për deployment të thjeshtë)

---

## 5. Fazat e Projektit dhe Afatet

| Faza | Përshkrimi | Kohëzgjatja (orientuese) |
|------|-----------|----------------------------|
| **Faza 0 – Kickoff** | Mbledhje kërkesash, konfirmimi i formatit të CSV-ve mujore, marrja e qasjes në dataset/MongoDB | 2-3 ditë |
| **Faza 1 – Pastrim & Përgatitje e të Dhënave** | Ngarkimi i datasetit UCI, pastrimi (duplicates, cancellations, missing CustomerID), standardizim kolonash | 3-4 ditë |
| **Faza 2 – Analiza e Thellë (EDA)** | Analiza e shitjeve, produkteve, klientëve, fitimit/humbjes, sezonalitetit, RFM segmentim | 5-7 ditë |
| **Faza 3 – Vizualizim & Raport Fillestar** | Grafikë profesionalë + raport me gjetje kryesore për klientin | 3-4 ditë |
| **Faza 4 – Plani Strategjik i Rritjes së Fitimit** | Rekomandime konkrete (çmimi, produkte për promovim, klientë për retention, etj.) | 3-4 ditë |
| **Faza 5 – Zhvillimi i Aplikacionit Streamlit** | Upload CSV, validim, dashboard, motor rekomandimesh | 8-10 ditë |
| **Faza 6 – Moduli "What-if" / Projeksion Fitimi** | Simulim i ndikimit financiar nëse zbatohen rekomandimet | 4-5 ditë |
| **Faza 7 – Testim & Rregullim** | Testim me dataset real dhe me CSV muaj-provë, rregullim gabimesh | 3-4 ditë |
| **Faza 8 – Dorëzimi & Trajnimi i Klientit** | Dokumentacion, video/udhëzues përdorimi, sesion trajnimi | 2 ditë |

**Kohëzgjatja totale e vlerësuar: ~6-8 javë** (varet nga disponueshmëria e klientit dhe të dhënave shtesë si kostot e produkteve).

---

## 6. Detajet e Analizës së të Dhënave

### 6.1 Pastrimi i të Dhënave
- Heqja e transaksioneve me `Quantity` negative pa `InvoiceNo` që fillon me "C" (ose trajtimi i tyre si kthime/refunds).
- Trajtimi i vlerave mungesë në `CustomerID` (klientë "guest").
- Heqja/analiza e `UnitPrice` <= 0.
- Standardizimi i datave, konvertimi i `InvoiceDate` në format kohor.
- Krijimi i kolonës `Revenue = Quantity * UnitPrice`.

### 6.2 Analiza Kryesore
- **Shitjet:** trend mujor/javor, ditët/orët me shitje më të larta, sezonalitet.
- **Produktet:** top 10 produkte më të shitura (sipas sasisë dhe të ardhurave), produkte me shitje të ulëta (kandidatë për heqje nga stoku ose promovim).
- **Fitimi/Humbja:** të ardhurat totale, humbjet nga kthimet (cancellations), marzhi (nëse ka të dhëna kosto shtesë nga klienti).
- **Klientët:** segmentim RFM (Recency, Frequency, Monetary), identifikimi i klientëve VIP dhe atyre në rrezik humbjeje (churn risk).
- **Gjeografia:** performanca sipas vendit (`Country`), tregje me potencial rritjeje.

### 6.3 Vizualizimet
- Grafik linear i të ardhurave mujore.
- Bar chart i top produkteve.
- Heatmap e shitjeve sipas ditës/orës.
- Pie/bar chart i shpërndarjes gjeografike.
- Scatter/segment plot i klientëve (RFM).

---

## 7. Plani i Rritjes së Fitimit (Shembuj Rekomandimesh)

Motori i rekomandimeve në aplikacion do të gjenerojë automatikisht sugjerime të bazuara në rregulla dhe statistika, si p.sh.:

- **Cross-selling/Bundling:** produkte që blihen shpesh së bashku → sugjerim paketash.
- **Retention i klientëve VIP:** ofertave të personalizuara për klientët me `Monetary` të lartë por `Recency` në rritje (rrezik humbjeje).
- **Optimizim çmimi:** produkte me volum të lartë shitjesh por marzh të ulët → rishikim çmimi.
- **Reduktim humbjesh:** identifikimi i produkteve/klientëve me normë të lartë kthimesh (returns) dhe hetim i shkaqeve.
- **Sezonalitet:** planifikim stoku dhe fushata marketingu para periodave me kërkesë të lartë historike.
- **Tregje të reja:** vende me rritje shitjesh por ende me volum të ulët → potencial ekspansioni.

Në aplikacion, çdo rekomandim do të shoqërohet me një **vlerësim të ndikimit të mundshëm në fitim** (p.sh. "nëse rrisni retention e klientëve VIP me 10%, fitimi mujor mund të rritet me ~X%"), bazuar në të dhënat historike të ngarkuara.

---

## 8. Aplikacioni Streamlit — Funksionalitetet

1. **Faqja Kryesore / Dashboard**
   - Përmbledhje e KPI-ve kryesore (të ardhura totale, numri i porosive, klientë aktivë, marzhi).
2. **Upload i të Dhënave**
   - Buton për upload CSV mujor.
   - Validim automatik i strukturës/kolonave (krahasim me formatin origjinal të datasetit).
   - Mesazhe qarta gabimi nëse formati nuk përputhet.
3. **Analiza & Vizualizime Automatike**
   - Menjëherë pas upload-it, gjenerohen grafikët dhe tabelat përkatëse.
4. **Seksioni i Rekomandimeve**
   - Lista e sugjerimeve të gjeneruara automatikisht, të renditura sipas ndikimit të mundshëm.
5. **Simulimi "What-if"**
   - Klienti fut supozime (p.sh. "rrit retention me X%") dhe sheh projeksionin e fitimit.
6. **Eksportim**
   - Mundësi për të shkarkuar raportin (PDF/Excel) të analizës.

---

## 9. Kriteret e Suksesit (Deliverables Finale)

- [ ] Notebook/skript i plotë i analizës (pandas/numpy) me komente të qarta.
- [ ] Raport me gjetjet kryesore dhe planin strategjik të rritjes së fitimit.
- [ ] Aplikacion Streamlit funksional, i testuar me dataset të ri CSV.
- [ ] Dokumentacion teknik + udhëzues përdorimi për klientin.
- [ ] Sesion trajnimi/demonstrimi me klientin.

---

## 10. Rreziqet dhe Zbutja e Tyre

| Rreziku | Ndikimi | Zbutja |
|---------|---------|--------|
| Formate të ndryshme CSV nga klienti muaj pas muaji | Analiza mund të dështojë | Validim strikt + template CSV i dhënë klientit |
| Mungesa e të dhënave për kosto/marzh real | Analiza e "fitimit" bazohet vetëm në të ardhura | Kërkohet nga klienti të dhëna shtesë kosto nëse mundësohet |
| Volum i madh të dhënash (performancë) | Ngadalësim i aplikacionit | Caching në Streamlit dhe optimizim i përpunimit në Pandas |
| Siguria e të dhënave të klientit | Konfidencialitet | Autentikim bazik |

---

## 11. Hapat e Ardhshëm

1. Konfirmimi i planit nga klienti.
2. Sigurimi i qasjes në të dhënat burimore.
3. Fillimi i Fazës 0 (kickoff) dhe Fazës 1 (pastrimi i datasetit UCI si bazë fillestare).

---

*Ky dokument shërben si plan pune i hapur për diskutim; afatet dhe fazat mund të rregullohen sipas prioriteteve dhe disponueshmërisë së klientit.*
