# Reading list: how AI suggestions change radiologists' decisions

_Compiled 2026-09-23. Five search lanes plus a completeness pass; each paper was checked against PubMed, its DOI page, PMC, arXiv or NBER by a separate verifier. Companion to Dratsch et al., Radiology 2023 (`Automation Bias in Mammography.pdf`, in this folder)._

## 1. How to use this list

Read the five must-reads in order. Together they take you from Dratsch's design to the choices your platform has to make: the unaided baseline, workflow order, who benefits, and deception with debriefing. After that, use section 3 as a reference by theme and section 4 to place your own study. Every paper was checked on PubMed, a DOI or journal page, PMC, arXiv or NBER. "(abstract only)" means only the abstract or landing page could be read, so its design details are thinner. A missing detail means the checked source did not state it.

## 2. Start here: the 5 must-reads

### 1. Rezazade Mehrizi 2023: the sister study to Dratsch, with Iranian readers
Rezazade Mehrizi MH, Mol F, Peter M, et al. The impact of AI suggestions on radiologists' decisions: a pilot study of explainability and attitudinal priming interventions in mammography examination. *Scientific Reports* 2023;13:9230. DOI: https://doi.org/10.1038/s41598-023-36435-3 · Open access: https://pmc.ncbi.nlm.nih.gov/articles/PMC10247804/

- **What they did.**
  - **Readers and cases.** 92 radiologists (66% from Iran, 34% from Europe; 71% with no prior CAD/AI experience) scored BI-RADS 1-5 per breast side on 15 mammograms. That gave 30 decisions per reader, and readers could not go back. The study ran on a custom online platform.
  - **AI.** The AI was purported. The researchers made the suggestions, a senior radiologist drew "artificial" heat maps, and readers were told the AI was real.
  - **Planted errors.** 8 of 30 suggestions (27%) were wrong: 6 one-point and 2 two-point errors, 4 over-calls and 4 under-calls.
  - **Baseline and display.** There was no unaided baseline. The suggestion stayed hidden until the reader clicked "Show AI suggestion". The heat map sat behind a toggle, and a case-attribute chart appeared on hover.
  - **Arms.** Study 1 randomized which explanation inputs readers got. Study 2 randomized priming videos (positive, negative, ambivalent about AI, or none).
- **Key number.** Accuracy was 78% when the AI was correct vs 28% when it was incorrect. Readers opened the AI in 84% of tasks. Neither explanations nor priming meaningfully reduced the pull of wrong suggestions.
- **What to borrow for our platform.**
  - **Telemetry.** Log time to AI reveal, heat-map toggles and dwell, time to first answer and each revision.
  - **Error mix.** Balance planted errors explicitly: minor vs major, over-call vs under-call.
  - **Recruitment.** Its Iranian-plus-European recruitment is the direct precedent for your network. Co-authors include Fatehi M (National Brain Mapping Laboratory, Tehran) and Dratsch T.
  - **Gap to fill.** It had no committed unaided read, which is the gap your platform can close.

### 2. Gaube 2021: scale, per-reader susceptibility and the "AI" label
Gaube S, Suresh H, Raue M, et al. Do as AI say: susceptibility in deployment of clinical decision-aids. *npj Digital Medicine* 2021;4:31. DOI: https://doi.org/10.1038/s41746-021-00385-9 · Open access: https://pmc.ncbi.nlm.nih.gov/articles/PMC7896064/

- **What they did.**
  - **Readers and cases.** 138 radiologists and 127 internal or emergency medicine (IM/EM) physicians from the US and Canada read the same 8 MIMIC-CXR chest X-rays, each with a short vignette. Images opened in an external web DICOM viewer, and the survey ran in Qualtrics.
  - **Advice and label.** Human experts wrote all the advice (findings plus a primary diagnosis). Between subjects, it was labelled either "CHEST-AI" (a deep-learning model) or "Dr. S. Johnson", an experienced radiologist.
  - **Planted errors.** 2 of 8 cases (25%, randomized per participant) carried inaccurate but plausible advice.
  - **Baseline.** None: the advice came with every case. Readers accepted, modified or rejected it and rated their confidence from 1 to 7.
- **Key number.**
  - **Susceptibility.** 27.54% of radiologists and 41.73% of IM/EM physicians were "susceptible": they always gave the wrong diagnosis when the advice was wrong.
  - **Resistance.** 28.26% of radiologists and 17.32% of IM/EM physicians rejected all wrong advice.
  - **Label effect.** Radiologists rated AI-labelled advice as lower quality, but they followed it just as much.
- **What to borrow for our platform.**
  - **Per-reader profiles.** Report the share of wrong-AI cases each reader followed (always, sometimes, never), not only pooled means.
  - **Source label.** Keep the AI-vs-colleague label between-subject.
  - **Say and do.** Collect both what readers say (quality and trust ratings) and what they do (whether they switch), because the label changed one and not the other.

### 3. Bernstein 2023: unaided baseline, two cheap mitigations, and a debrief
Bernstein MH, Atalay MK, Dibble EH, et al. Can incorrect artificial intelligence (AI) results impact radiologists, and if so, what can we do about it? A multi-reader pilot study of lung cancer detection with chest radiography. *European Radiology* 2023;33(11):8263-8269. DOI: https://doi.org/10.1007/s00330-023-09747-1 · Open access: https://pmc.ncbi.nlm.nih.gov/articles/PMC10235827/

- **What they did.**
  - **Readers and cases.** 6 radiologists with 1-14 years' experience took part; 5 were analysed, because one did not believe the cover story. They read the same 90 frontal chest X-rays (CXRs; 50% biopsy-proven lung cancer) in 4 sessions at least a month apart (mean 113.8 days). For each they answered "follow-up CT yes/no" and gave a confidence rating.
  - **AI.** The AI was a sham: a thoracic radiologist chose the outputs. Readers were told they were evaluating several AI programs, each with ROC-AUC >0.85. "Abnormal" or "Normal" appeared in the image corner and was also read aloud. Reading used a research PACS in a clinical reading room.
  - **Planted errors.** 12 of 90 outputs were wrong: 8 false positives (FP) and 4 false negatives (FN).
  - **Baseline and sessions.** The unaided baseline was within-subject: the No-AI session always came first. The Keep-AI and Delete-AI sessions (readers were told the AI result would or would not be saved in the record) were counterbalanced. The session with a box around the region came last.
- **Key number.** False negatives on the manipulated cases were 2.7% without AI, 33.0% with wrong AI (Keep, no box), 26.7% (Delete) and 20.7% (Keep, with box). False positives were 51.4% vs 86.0%, 80.5% and 80.5%.
- **What to borrow for our platform.**
  - **Suspicion probe and debrief.** End with a suspicion probe, then a formal debrief screen.
  - **Exclusion rule.** Pre-specify what happens to readers who saw through the setup.
  - **Cheap factors.** Accountability framing (keep vs delete) and region boxes are cheap factors to randomize.
  - **Debrief precedent.** This is the only must-read that reports debriefing.

### 4. Fogliato 2022: your read-then-reveal design is itself an intervention
Fogliato R, Chappidi S, Lungren M, et al. Who Goes First? Influences of Human-AI Workflow on Decision Making in Clinical Imaging. *Proceedings of the 2022 ACM Conference on Fairness, Accountability, and Transparency (FAccT '22)*. DOI: https://doi.org/10.1145/3531146.3533193 · Open access: https://arxiv.org/pdf/2205.09696

- **What they did.**
  - **Readers and cases.** 19 veterinary radiologists (Mars) assessed 33 possible findings on each of 40 canine radiographs. For each finding they gave a likelihood slider, a present/absent call and a second-opinion flag.
  - **AI.** A real ensemble model gave a confidence for each finding and a flag at ≥60%. Its errors were natural; none were planted.
  - **Workflow arms (between subjects).** One-step: AI shown with the image (11 readers). Two-step: provisional answer first, then a click to reveal the AI and revise (8 readers). The two-step arm therefore gives a within-case unaided read.
- **Key number.** Two-step readers changed their answer on only 70 of 10,560 findings, which is 5% of the findings where they first disagreed with the AI. They agreed with the AI less whether or not it was right. They rated it useful for 17% of images vs 36% in the one-step arm, and they did not take longer.
- **What to borrow for our platform.**
  - **Expect a smaller effect.** Commit-first reading will understate how much AI moves readers compared with concurrent display in deployment. Say so in write-ups, or add a concurrent arm.
  - **Reference implementation.** Look at their open-source experiment platform (http://aka.ms/Exp-HAIC).

### 5. Yu 2024: who benefits, who is harmed, and how not to fool yourself
Yu F, Moehring A, Banerjee O, Salz T, Agarwal N, Rajpurkar P. Heterogeneity and predictors of the effects of AI assistance on radiologists. *Nature Medicine* 2024;30(3):837-849. DOI: https://doi.org/10.1038/s41591-024-02850-w · Open access: https://pmc.ncbi.nlm.nih.gov/articles/PMC10957478/

- **What they did.**
  - **Readers and cases.** 140 radiologists each read 60 of 324 retrospective Stanford chest radiographs, giving probabilities for 15 pathology labels.
  - **AI.** A real CheXpert-trained model was shown as probabilities only, with no localization or explanation. Onboarding showed example predictions. Errors were natural and were analysed by size and direction.
  - **Baseline.** Within-reader. 107 radiologists read 30 cases unaided and 30 assisted. 33 read every case in all four AI x clinical-history conditions, across sessions with washout.
- **Key number.**
  - **Spread.** Effects per radiologist ranged from −1.295 to 1.440 (IQR 0.797).
  - **Predictors.** Experience, thoracic subspecialty and prior AI use did not predict benefit. Once split sampling was used, lower unaided skill did not reliably predict it either.
  - **AI error size.** The effect was 0.679 when the AI's absolute error was under 20 and −16.845 when it was above 80. Over-estimating AI hurt more than under-estimating AI by the same amount.
- **What to borrow for our platform.**
  - **Split sampling.** Measure each reader's skill on a separate block of cases before asking who benefits. Otherwise regression to the mean produces a false "weaker readers gain more" result.
  - **Error logging.** Log each suggestion's error size and direction so harm can be broken down by AI error.

**Before you write a protocol,** add three methods pieces from section 3.5:
- the FDA CADe guidance, on the bias of sequential designs and how to check for it;
- Schemmer 2023, for switch metrics normalized by opportunity;
- Miller 2005, for authorized-deception consent.

## 3. Core list

### 3.1 Deliberately wrong AI and automation bias

**Alberdi 2004.** Alberdi E, Povyakalo A, Strigini L, Ayton P. Effects of incorrect computer-aided detection (CAD) output on human decision-making in mammography. *Academic Radiology* 2004;11(8):909-918. DOI: [10.1016/j.acra.2004.05.012](https://doi.org/10.1016/j.acra.2004.05.012) · OA: [City Research Online](https://openaccess.city.ac.uk/id/eprint/1589/)
- **Design.** 20 UK film readers (12 radiologists, 7 radiographers, 1 breast clinician) read 60 four-view cases (30 cancers) with real R2 ImageChecker prompts on a paper copy.
  - **Enrichment.** The set was enriched so that 20 of 30 cancers had incorrect CAD output: 11 prompted only away from the cancer and 9 unmarked.
  - **Baseline.** The unaided comparison was a different group of 19 readers.
- **Finding.** Mean sensitivity was 52% with CAD vs 68% without (F=17.17, p<0.001). 7 unmarked cancers were not recalled by 18 or more of the 20 readers. Questionnaires suggested some readers had not noticed that CAD was missing far more cancers than usual.
- **Borrow.** Use a within-reader baseline. After the session, ask readers what share of AI outputs they think were wrong.

**Tsai 2003** (abstract only). Tsai TL, Fridsma DB, Gatti G. Computer decision support as a source of interpretation error: the case of electrocardiograms. *J Am Med Inform Assoc* 2003;10(5):478-483. DOI: [10.1197/jamia.m1279](https://doi.org/10.1197/jamia.m1279) · OA: [PMC212785](https://pmc.ncbi.nlm.nih.gov/articles/PMC212785/)
- **Design.** Internal medicine residents read 12-lead EKGs with or without a real computer interpretation (CI) shown alongside. This was a randomized two-period crossover in a lab setting. Whether the incorrect CIs were chosen deliberately was not verified.
- **Finding.** Accuracy rose from 48.9% to 55.4% with CI. Residents agreed with an incorrect CI 67.7% of the time when it was shown, vs 34.6% when they read the same EKG without it (p<0.0001).
- **Borrow.** Compare agreement with a wrong AI answer against the rate at which readers reach that same answer unaided. Your pre-reveal commit gives this for each case.

**Southern 2009** (abstract only). Southern WN, Arnsten JH. The effect of erroneous computer interpretation of ECGs on resident decision making. *Med Decis Making* 2009;29(3):372-376. DOI: [10.1177/0272989X09333125](https://doi.org/10.1177/0272989X09333125) · OA: [PMC2806088](https://pmc.ncbi.nlm.nih.gov/articles/PMC2806088/)
- **Design.** 105 internal and emergency medicine residents read one ECG. Handouts from a concealed stack either carried an erroneous computer interpretation citing acute ischemia or none (quasi-randomized, between-subject).
- **Finding.** Interpretation did not change (P=0.62), but management did: 30% recommended revascularization with the erroneous interpretation vs 10% without (P=0.01).
- **Borrow.** Capture a downstream action (recall, biopsy, follow-up) next to the diagnostic label.

**Jabbour 2023.** Jabbour S, Fouhey D, Shepard S, et al. Measuring the Impact of AI in the Diagnosis of Hospitalized Patients: A Randomized Clinical Vignette Survey Study. *JAMA* 2023;330(23):2275-2284. DOI: [10.1001/jama.2023.22295](https://doi.org/10.1001/jama.2023.22295) · OA: [PMC10731487](https://pmc.ncbi.nlm.nih.gov/articles/PMC10731487/)
- **Design.** 457 hospitalist physicians, nurse practitioners and physician assistants from 13 US states took part; no radiologists.
  - **Vignettes.** Each saw 9 vignettes of acute respiratory failure: 2 without AI, 6 with AI (3 standard, 3 systematically biased), and a final one with a colleague consult.
  - **AI display.** Scores from 0 to 100 were shown at the same time as the vignette.
  - **Explanation arm.** Participants were randomized to also see Grad-CAM heat maps. The biased models used rules such as age ≥80 → pneumonia, and their heat maps highlighted irrelevant regions.
- **Finding.** Baseline accuracy was 73.0%. Standard AI added 2.9 pp (4.4 with explanations). Biased AI subtracted 11.3 pp (9.1 with explanations). The 2.3-point difference explanations made was not significant.
- **Borrow.**
  - **Systematic errors.** Make errors tied to a detectable feature a condition separate from random errors.
  - **Revealing explanations.** Include wrong-AI cases whose explanation gives the error away.
  - **Registration.** Register before data collection; this study registered retrospectively.

**Pesapane 2026** (abstract and declarations only). Pesapane F, Latronico A, Abbate F, et al. Evaluating cognitive biases in AI-assisted mammography interpretation: a simulation reader study of explainable AI across radiologist experience levels. *European Radiology* 2026;36(10):7639-7650. DOI: [10.1007/s00330-026-12666-6](https://doi.org/10.1007/s00330-026-12666-6)
- **Design.** 6 breast radiologists, stratified by experience, read 200 mammograms in a fixed order: unassisted, then AI-assisted, then AI plus saliency heat maps. In 30% of exams the real AI output was shifted by one BI-RADS category.
- **Finding.** On manipulated cases, automation bias fell from 36.1% (65/180) to 17.8% with heat maps, and anchoring bias from 33.9% to 17.2%. The adjusted odds ratio (aOR) for automation bias was 0.56 (0.44-0.71). On unmanipulated exams, accuracy rose from 86.2% unaided to 90.1% with AI plus heat maps.
- **Borrow.** Make wrong suggestions plausible near misses by shifting a real output one category. Report automation bias and anchoring/revision bias as separate metrics. Counterbalance condition order, because the heat-map condition always came last here.

**Kim 2025.** Kim SH, Schramm S, Riedel EO, et al. Automation bias in AI-assisted detection of cerebral aneurysms on time-of-flight MR angiography. *La Radiologia Medica* 2025;130(4):555-566. DOI: [10.1007/s11547-025-01964-6](https://doi.org/10.1007/s11547-025-01964-6) · OA: [PMC12008054](https://pmc.ncbi.nlm.nih.gov/articles/PMC12008054/)
- **Design.** 9 readers (3 residents, 3 radiologists, 3 neuroradiologists) read 20 TOF-MRA studies with and without real mdbrain AI, in a crossover with at least 4 weeks' washout (mean 45 days).
  - **AI.** Output appeared in the clinical PACS, and readers were told to look at the AI annotations first.
  - **Case selection.** 10 of 20 cases had at least one false-positive AI finding.
  - **Warm-up.** Before session 1, readers saw 5 true-positive AI cases, intended "to cultivate trust" in the tool.
- **Finding.** False-positive AI findings raised suspicion (p=0.01), and inexperienced readers escalated follow-up (p=0.005). Inexperienced readers took 164.1 s with AI vs 228.2 s without.
- **Borrow.** Make any warm-up block an explicit, logged or randomized variable. The combined presence-and-certainty scale is worth reusing.

**Taib 2026** (abstract only). Taib AG, Partridge GJW, Phillips P, et al. Automation Bias in Action: Eye Tracking of Humans Reading Screening Mammograms with and without AI Prompts. *Radiology* 2026;320(1):e252590. DOI: [10.1148/radiol.252590](https://doi.org/10.1148/radiol.252590)
- **Design.** 10 NHS screening readers read 60 cases enriched for AI errors: 26 true positive, 14 false negative, 14 false positive, 6 true negative. They read without AI first, then with commercial AI prompts 6 weeks later, under eye tracking.
- **Finding.** On cases the AI missed, sensitivity was 39% with AI vs 71% unassisted (P=.002), and readers fixated less on those cancers.
- **Borrow.** Plant AI false negatives, not only false positives. Log zoom, pan and dwell as a cheap proxy for eye tracking.

**Drew 2012** (abstract only). Drew T, Cunningham C, Wolfe JM. When and why might a computer-aided detection (CAD) system interfere with visual search? An eye-tracking study. *Acad Radiol* 2012;19(10):1260-1267. DOI: [10.1016/j.acra.2012.05.013](https://doi.org/10.1016/j.acra.2012.05.013) · OA: [PMC3438519](https://pmc.ncbi.nlm.nih.gov/articles/PMC3438519/)
- **Design.** 47 naive observers searched noise images for targets with a simulated CAD that marked 75% of targets and 10% of distractors, under eye tracking.
- **Finding.** CAD raised sensitivity, but targets it failed to mark were missed more often (t(22)=7.02, P<.001), and observers searched less of the image.
- **Borrow.** Include cases where the AI is silent on a real finding, and log viewer interaction. Caveat: the observers were not radiologists.

**Wang 2023.** Wang DY, Ding J, Sun AL, et al. Artificial intelligence suppression as a strategy to mitigate artificial intelligence automation bias. *Journal of the American Medical Informatics Association* 2023;30(10):1684-1692. DOI: [10.1093/jamia/ocad118](https://doi.org/10.1093/jamia/ocad118) · OA: [PMC10531198](https://pmc.ncbi.nlm.nih.gov/articles/PMC10531198/)
- **Design.** 40 clinicians from 20 hospitals read 200 knee MRIs for ACL status, with and without a real model. This was a randomized crossover with a 14-day washout, giving 8,000 interactions.
  - **AI display.** The model showed a diagnosis, a confidence band and a colour indicator.
  - **Disclosure.** Clinicians were told in advance that the AI can be wrong.
- **Finding.** Accuracy rose from 87.2% to 96.4%. There were 833 correcting and 132 misleading events, and automation bias caused 45.5% of mistakes in the assisted round. All interviewed clinicians denied being misled. Hiding AI output in the confidence zone most likely to mislead was estimated, by simulation only, to cut automation bias by 41.7%.
- **Borrow.** Correcting vs misleading events equal your rescued vs talked-out. Store AI confidence per case so misleading confidence zones can be modelled.

**Shi 2025** (abstract only). Shi Z, Hu B, Lu M, et al. Development and Validation of a Sham-AI Model for Intracranial Aneurysm Detection at CT Angiography. *Radiology: Artificial Intelligence* 2025;7(3):e240140. DOI: [10.1148/ryai.240140](https://doi.org/10.1148/ryai.240140) · OA: [journal](https://doi.org/10.1148/ryai.240140)
- **Design.** 28 radiologists from 7 hospitals read 300 CTA patients (50 with aneurysms). Half the cases came with standard AI output and half with a sham "placebo" model (0.0% sensitivity, similar specificity), crossed over after washout.
- **Finding.** Sham-assisted reads were non-inferior to reading alone (−2.6% sensitivity). After sham suggestions, 5.3% (44/823) of readers' true positives changed.
- **Borrow.** Add a placebo-AI arm to separate the effect of what the AI says from the effect of an AI box simply being on screen.

**Jacobs 2021.** Jacobs M, Pradier MF, McCoy TH, Perlis RH, Doshi-Velez F, Gajos KZ. How machine-learning recommendations influence clinician treatment selections: the example of the antidepressant selection. *Transl Psychiatry* 2021;11(1):108. DOI: [10.1038/s41398-021-01224-x](https://doi.org/10.1038/s41398-021-01224-x) · OA: [PMC7862671](https://pmc.ncbi.nlm.nih.gov/articles/PMC7862671/)
- **Design.** 220 clinicians worked 17 antidepressant-selection vignettes: 5 without a recommendation, 12 with simulated ML recommendations.
  - **Error rate.** One recommendation in three was incorrect (the option experts scored lowest).
  - **Explanations.** There were 4 explanation types.
  - **Labelling.** Each recommendation was labelled as coming from a different model.
- **Finding.** Accuracy was 0.357 at baseline, 0.384 with a correct recommendation and 0.299 with an incorrect one. An incorrect recommendation with a feature-based explanation gave 0.262 (d=0.28 vs baseline).
- **Borrow.** Labelling each suggestion as coming from a different model stops readers learning the AI's overall error rate. Pair that with a debrief, which this study did not describe.

### 3.2 Who benefits and who is harmed

**Povyakalo 2013** (abstract and repository record). Povyakalo AA, Alberdi E, Strigini L, Ayton P. How to discriminate between computer-aided and computer-hindered decisions: a case study in mammography. *Medical Decision Making* 2013;33(1):98-107. DOI: [10.1177/0272989X12465490](https://doi.org/10.1177/0272989X12465490) · OA: [White Rose PDF](https://eprints.whiterose.ac.uk/id/eprint/165906/1/Povyakalo_etal_MDM_120731CLEAN.pdf)
- **Design.** A reanalysis of a UK trial: 50 readers, 180 mammograms read with and without real CAD, with the AI effect modelled by case difficulty and reader skill.
- **Finding.** The trial showed no average effect. Underneath it, sensitivity rose by 0.016 for the 44 least-discriminating readers on 45 easy cancers and fell by 0.145 for the 6 most-discriminating readers on 15 difficult cancers.
- **Borrow.** Pre-plan a difficulty x skill analysis from the unaided reads. A null average can hide harm.

**Kiani 2020.** Kiani A, Uyumazturk B, Rajpurkar P, Wang A, Gao R, Jones E, Yu Y, Langlotz CP, et al.; Ng AY, Shen J. Impact of a deep learning assistant on the histopathologic classification of liver cancer. *NPJ Digit Med* 2020;3:23. DOI: [10.1038/s41746-020-0232-8](https://doi.org/10.1038/s41746-020-0232-8) · OA: [PMC7044422](https://pmc.ncbi.nlm.nih.gov/articles/PMC7044422/)
- **Design.** 11 pathologists classified 80 whole-slide images (HCC vs CC), with a real model shown alongside as probabilities plus activation heat maps. Randomized crossover, at least 2 weeks apart.
- **Finding.** There was no average change (OR 1.281, p=0.184). When the model was right the OR was 4.289; when it was wrong, 0.253, at every experience level.
- **Borrow.** Stratify every analysis and dashboard by whether the AI was correct.

**Tschandl 2020.** Tschandl P, Rinner C, Apalla Z, et al. Human-computer collaboration for skin cancer recognition. *Nature Medicine* 2020;26(8):1229-1234. DOI: [10.1038/s41591-020-0942-0](https://doi.org/10.1038/s41591-020-0942-0)
- **Design.** 302 raters on the dermachallenge.com web platform (56.0% board-certified dermatologists) diagnosed ISIC 2018 dermoscopic images. Each gave an unaided diagnosis, then saw support and could change it.
  - **Formats compared.** AI multiclass probabilities, AI malignancy probability, similar-image retrieval, or crowd probabilities.
  - **Faulty-AI experiment.** A "misleading probabilities" experiment involved 155 raters. How the outputs were manipulated was not verified.
- **Finding.** Good AI support beat both humans and AI alone, and the least experienced gained most. Faulty AI misled clinicians at every level, experts included. When raters switched, the average AI malignancy cutoff they acted on was below 25%, not 50%.
- **Borrow.** This is the closest large-scale web-platform precedent: research consent at registration with the right to withdraw. Log the AI confidence at which each reader switches.

**Agarwal 2023 (NBER).** Agarwal N, Moehring A, Rajpurkar P, Salz T. Combining Human Expertise with Artificial Intelligence: Experimental Evidence from Radiology. *NBER Working Paper 31422* (July 2023, revised August 2026). DOI: [10.3386/w31422](https://doi.org/10.3386/w31422) · OA: [NBER PDF](https://www.nber.org/system/files/working_papers/w31422/w31422.pdf)
- **Design.** 227 radiologists, mostly recruited via teleradiology companies plus VinMec staff, read cases from a pool of 324 Stanford chest X-rays. They gave probabilities for each pathology and a treatment decision.
  - **Factors.** AI (the real CheXpert model) x clinical history, in 3 designs. Design 3 read the same cases first without, then with AI.
  - **Pre-registration.** AEARCTR-0009620.
- **Finding.** The AI was more accurate than 78% of the radiologists, yet it did not improve their accuracy on average. Clinical history did help (4.0% less deviation from the standard). Radiologists under-weighted the AI ("automation neglect"). AI helped when it was confident and hurt when it was uncertain.
- **Borrow.**
  - **Response format.** Collect a probability slider plus a separate binary action.
  - **Incentives.** Score accuracy payments with a proper scoring rule.
  - **Second-look control.** Add a same-case re-read without AI to separate the AI effect from the effect of simply looking again.

**Moehring 2025 (Collab-CXR dataset).** Moehring A, Kutwal M, Huang R, Banerjee O, et al.; Agarwal N, Rajpurkar P, Salz T. A Dataset for Understanding Radiologist-Artificial Intelligence Collaboration. *Scientific Data* 2025;12(1):739. DOI: [10.1038/s41597-025-05054-0](https://doi.org/10.1038/s41597-025-05054-0) · OA: [PMC12049457](https://pmc.ncbi.nlm.nih.gov/articles/PMC12049457/)
- **Design.** The public release of the Agarwal experiment: 227 radiologists, 324 cases, 104 thoracic pathologies, probabilistic reports, AI predictions, timing and clickstream.
- **Borrow.** Use their layout as your schema: one row per radiologist, session, patient and pathology, plus a separate event log. Test your analysis pipeline on it before your own data arrive.

**Martin 2026 (preprint).** Martin D. Revisiting the ABCs of Working with AI: A Replication with Radiologists. *arXiv preprint 2606.12585*. OA: [arXiv](https://arxiv.org/abs/2606.12585)
- **Design.** Secondary analysis of 68 Collab-CXR radiologists (11,420 paired observations). Ability was measured on unaided skill-block cases, and calibration as confidence minus correctness.
- **Finding.** Fitted AI effects were 5.10, 1.38, 2.20 and −1.53 pp for low-ability/well-calibrated, low-ability/poorly calibrated, high-ability/well-calibrated and high-ability/poorly calibrated readers. This conflicts with Yu 2024. The metrics differ, and this is a single-author preprint.
- **Borrow.** Add an unaided skill block with confidence ratings, so each reader has a calibration score before AI appears.

**Song 2026** (abstract only). Song J, Jeong WG, Han DH, et al. Determinants of Reader-LLM Interaction in Thoracic Radiology: Impact of Model Confidence and Reader Expertise. *Radiology* 2026;320(2):e253397. DOI: [10.1148/radiol.253397](https://doi.org/10.1148/radiol.253397)
- **Design.** 10 readers worked 100 chest cases (radiography, CT, MRI, PET). Session 1 was unaided. In session 2 an LLM gave ranked diagnoses with rationales; the model was GPT-5 (76% correct) or GPT-4o (27% correct), randomized per reader-case.
- **Finding.** Model confidence (OR 3.82) and reader expertise (OR 2.06) predicted adequate interaction. Better-written rationales raised acceptance of incorrect suggestions (OR 1.71).
- **Borrow.** Make "adequate interaction" (accept correct, reject incorrect) an endpoint. Randomizing between real models of different accuracy is an ethically softer alternative to scripted wrong AI.

**Sim 2020** (abstract only). Sim Y, Chung MJ, Kotter E, et al.; Choi BW. Deep Convolutional Neural Network-based Software Improves Radiologist Detection of Malignant Lung Nodules on Chest Radiographs. *Radiology* 2020;294(1):199-209. DOI: [10.1148/radiol.2019182465](https://doi.org/10.1148/radiol.2019182465)
- **Design.** 12 radiologists from 4 centres marked nodules on 800 CXRs (600 cancers) unaided, then re-reviewed them with real commercial software.
- **Finding.** 104 of 2,400 reads changed for the better and 56 for the worse. Sensitivity went from 65.1% to 70.3%.
- **Borrow.** Report rescued and talked-out counts per reader next to the net change.

**Lindsey 2018.** Lindsey R, Daluiski A, Chopra S, et al.; Potter H. Deep neural network improves fracture detection by clinicians. *Proc Natl Acad Sci U S A* 2018;115(45):11591-11596. DOI: [10.1073/pnas.1806905115](https://doi.org/10.1073/pnas.1806905115) · OA: [PMC6233134](https://pmc.ncbi.nlm.nih.gov/articles/PMC6233134/)
- **Design.** 40 emergency medicine clinicians (24 MDs, 16 physician assistants; 1 excluded) read 300 wrist radiographs (266 analysed). Each answered unaided, then saw a real model's overlay and text and answered again. The order was never reversed.
- **Finding.** Sensitivity went from 80.8% to 91.5% and specificity from 87.5% to 93.9%. The misinterpretation rate fell by 47.0%. Harm was not examined case by case.
- **Borrow.** Add a re-read-without-AI control. Record first-read time as a measure of difficulty.

**Rajpurkar 2020 (CheXaid).** Rajpurkar P, O'Connell C, Schechter A, et al.; Lungren MP. CheXaid: deep learning assistance for physician diagnosis of tuberculosis using chest x-rays in patients with HIV. *npj Digital Medicine* 2020;3:115. DOI: [10.1038/s41746-020-00322-2](https://doi.org/10.1038/s41746-020-00322-2) · OA: [PMC7481246](https://pmc.ncbi.nlm.nih.gov/articles/PMC7481246/)
- **Design.** 13 non-radiologist physicians in South Africa read 114 test cases, half unaided and half assisted (different cases). The AI showed a verbal likelihood category plus a visual explanation.
- **Finding.** Accuracy went from 0.60 to 0.65 (p=0.002), well below the AI alone at 0.79. Clinicians under-used the AI.
- **Borrow.** Always report reader alone, reader plus AI and AI alone on the same cases. Reader plus AI falling below AI alone is under-reliance, the opposite failure to automation bias.

**Friedman 1999** (abstract only). Friedman CP, Elstein AS, Wolf FM, Murphy GC, Franz TM, Heckerling PS, Fine PL, Miller TM, Abraham V. Enhancement of clinicians' diagnostic reasoning by computer-based consultation: a multisite study of 2 systems. *JAMA* 1999;282(19):1851-1856. DOI: [10.1001/jama.282.19.1851](https://doi.org/10.1001/jama.282.19.1851)
- **Design.** 216 faculty, residents and students each worked 9 hard internal medicine cases. They listed diagnoses, consulted ILIAD or QMR hands-on, then revised.
- **Finding.** The correct diagnosis appeared on the list in 39.5% of cases before consultation and 45.4% after (d=0.32). Gains were larger for students. The systems differed: ILIAD d=0.20 vs QMR d=0.45.
- **Borrow.** The original commit, consult, revise design. Treat the AI system itself as a factor.

**Typical MRMC-with-AI benchmarks (mostly correct AI, natural errors; abstract only):**
- **Kim HE 2020.** Kim HE, Kim HH, Han BK, et al.; Kim EK. Changes in cancer detection and false-positive recall in mammography using artificial intelligence: a retrospective, multireader study. *Lancet Digital Health* 2020;2(3):e138-e148. DOI: [10.1016/S2589-7500(20)30003-0](https://doi.org/10.1016/S2589-7500(20)30003-0) (OA).
  - **Design.** 14 radiologists read 320 mammograms first without, then with AI. The study was funded by the AI vendor (Lunit).
  - **Finding.** AUROC rose from 0.810 to 0.881; AI alone scored 0.940.
  - **Borrow.** Collect a likelihood, a location and a recall decision per case.
- **Seah 2021.** Seah JCY, Tang CHM, Buchlak QD, et al.; Jones CM. Effect of a comprehensive deep-learning model on the accuracy of chest x-ray interpretation by radiologists: a retrospective, multireader multicase study. *Lancet Digital Health* 2021;3(8):e496-e506. DOI: [10.1016/S2589-7500(21)00106-0](https://doi.org/10.1016/S2589-7500(21)00106-0) (OA).
  - **Design.** 20 radiologists read 2,568 CXRs for 127 findings, with a 3-month washout. 15 of 17 authors were employed by or seconded to the vendor.
  - **Finding.** Macro AUC rose from 0.713 to 0.808, with no finding getting worse.
  - **Caution.** Per-finding AUC hides harm at the level of cases and readers.
- **Duron 2021.** Duron L, Ducarouge A, Gillibert A, et al.; Feydy A. Assessment of an AI Aid in Detection of Adult Appendicular Skeletal Fractures by Emergency Physicians and Radiologists: A Multicenter Cross-sectional Diagnostic Study. *Radiology* 2021;300(1):120-129. DOI: [10.1148/radiol.2021203886](https://doi.org/10.1148/radiol.2021203886).
  - **Design.** 6 radiologists and 6 emergency physicians read 600 patients; each case was read either with the aid or without it.
  - **Finding.** Sensitivity +8.7%, specificity +4.1%, reading time −15.0%.
- **Guermazi 2022.** Guermazi A, Tannoury C, Kompel AJ, et al.; Hayashi D. Improving Radiographic Fracture Recognition Performance and Efficiency Using Artificial Intelligence. *Radiology* 2022;302(3):627-636. DOI: [10.1148/radiol.210937](https://doi.org/10.1148/radiol.210937) (OA).
  - **Design.** 24 readers from 6 specialties read 480 exams in a crossover with at least 1 month's washout.
  - **Finding.** Sensitivity rose from 64.8% to 75.2% and specificity from 90.6% to 95.6%.
- **Tam 2021.** Tam MDBS, Dyer T, Dissez G, et al.; Rasalingham S. Augmenting lung cancer diagnosis on chest radiographs: positioning artificial intelligence to improve radiologist performance. *Clinical Radiology* 2021;76(8):607-614. DOI: [10.1016/j.crad.2021.03.021](https://doi.org/10.1016/j.crad.2021.03.021).
  - **Design.** 3 radiologists never saw the AI; their labels were combined with the AI's afterwards.
  - **Finding.** "average reduction of missed cancers of 60%".
  - **Caution.** A counterpoint, not a reader study. Use such simulated combinations only as a ceiling.

### 3.3 How presentation and timing change influence

**Timing and order**

**Zheng 2004** (abstract only). Zheng B, Swensson RG, Golla S, et al. Detection and classification performance levels of mammographic masses under different computer-aided detection cueing environments. *Academic Radiology* 2004;11(4):398-406. DOI: [10.1016/s1076-6332(03)00677-9](https://doi.org/10.1016/s1076-6332(03)00677-9)
- **Design.** 8 radiologists read 110 subtle cases (45 masses) 6 times each. The investigators controlled the cues (80% sensitivity; 1.2 or 0.5 false-positive cues per image), shown either after an initial read or at the same time as the image.
- **Finding.** Cues shown after the initial read had little effect. Concurrent cues at the highest false-positive rate reduced performance (P<.05), and readers found fewer abnormalities outside cued regions.
- **Borrow.** Score findings outside the AI-marked region separately. Treat the AI false-positive rate as a design parameter.

**Halligan 2011** (abstract only). Halligan S, Mallett S, Altman DG, et al. Incremental benefit of computer-aided detection when used as a second and concurrent reader of CT colonographic data: multiobserver study. *Radiology* 2011;258(2):469-76. DOI: [10.1148/radiol.10100354](https://doi.org/10.1148/radiol.10100354)
- **Design.** 16 radiologists read 112 CT colonography patients three ways: unaided, CAD as second reader, and concurrent CAD. Order was randomized and reads were at least a month apart.
- **Finding.** Per-patient sensitivity gain was +7.0% with CAD as second reader vs +4.5% concurrent.
- **Borrow.** The template for studying timing as a factor: a three-arm within-reader crossover.

**Beyer 2007** (abstract only). Beyer F, Zierott L, Fallenberg EM, Juergens KU, Stoeckel J, Heindel W, Wormanns D. Comparison of sensitivity and reading time for the use of computer-aided detection (CAD) of pulmonary nodules at MDCT as concurrent or second reader. *Eur Radiol* 2007;17(11):2941-2947. DOI: [10.1007/s00330-007-0667-1](https://doi.org/10.1007/s00330-007-0667-1)
- **Design.** 4 radiologists read 50 chest CTs with concurrent CAD, then with CAD as a second reader a median of 14 weeks later.
- **Finding.** For nodules >4 mm, sensitivity was 68% without CAD, 68% with concurrent CAD and 75% with CAD as second reader. Time was 294 s, 274 s and 337 s.
- **Borrow.** Timestamp the unaided and post-reveal phases separately.

**Lee 2022.** Lee SE, Han K, Youk JH, Lee JE, Hwang JY, Rho M, Yoon J, Kim EK, Yoon JH. Differing benefits of artificial intelligence-based computer-aided diagnosis for breast US according to workflow and experience level. *Ultrasonography* 2022;41(4):718-727. DOI: [10.14366/usg.22014](https://doi.org/10.14366/usg.22014) · OA: [PMC9532201](https://pmc.ncbi.nlm.nih.gov/articles/PMC9532201/)
- **Design.** 6 radiologists (3 inexperienced, 3 experienced) read 492 breast lesions with real S-Detect output. They read sequentially first, then simultaneously 4 weeks later; the order was not counterbalanced.
- **Finding.** Readers changed their final assessment in 40.8% of simultaneous reads vs 16.8% of sequential reads. Changes crossing the BI-RADS 3 / 4a line were 15.8% vs 6.2%. Inexperienced readers changed more (46.2% vs 35.4% when reading simultaneously).
- **Borrow.** Score flips that cross an action threshold separately from any category change.

**Cabitza 2023 (AIIM)** (abstract only). Cabitza F, Campagner A, Ronzio L, et al. Rams, hounds and white boxes: Investigating human-AI collaboration protocols in medical diagnosis. *Artificial Intelligence in Medicine* 2023;138:102506. DOI: [10.1016/j.artmed.2023.102506](https://doi.org/10.1016/j.artmed.2023.102506)
- **Design.** 12 radiologists read 240 knee MRIs and 44 readers read 20 ECGs, under human-first vs AI-first protocols, with and without explanations (XAI).
- **Finding.** AI-first protocols gave higher accuracy. Explanations showed a "white-box paradox": no effect or a harmful one.
- **Borrow.** The counterweight to Fogliato. Frame commit-first results as measuring AI used as a second opinion.

**Buçinca 2021.** Buçinca Z, Malaya MB, Gajos KZ. To Trust or to Think: Cognitive Forcing Functions Can Reduce Overreliance on AI in AI-assisted Decision-making. *Proceedings of the ACM on Human-Computer Interaction* 5(CSCW1), Article 188, 2021. DOI: [10.1145/3449287](https://doi.org/10.1145/3449287) · OA: [arXiv](https://arxiv.org/pdf/2102.09692)
- **Design.** 199 crowd workers did a nutrition task. The AI was simulated at 75% accuracy, with 6 of 26 suggestions wrong. Conditions included AI on demand, "update" (decide first, then see the AI) and a 30-second wait.
- **Finding.** Overreliance on wrong AI was 0.48 with cognitive forcing vs 0.64 with simple explanations (p=.003). Participants liked the most effective designs least.
- **Borrow.** Commit-first is a cognitive forcing function. Measure reader satisfaction alongside reliance.

**Explanations and confidence display**

**Gaube 2023.** Gaube S, Suresh H, Raue M, et al. Non-task expert physicians benefit from correct explainable AI advice when reviewing X-rays. *Scientific Reports* 2023;13(1):1383. DOI: [10.1038/s41598-023-28633-w](https://doi.org/10.1038/s41598-023-28633-w) · OA: [PMC9876883](https://pmc.ncbi.nlm.nih.gov/articles/PMC9876883/)
- **Design.** 106 radiologists and 117 IM/EM physicians read chest X-rays in a 2x2 design. Arrow annotations were varied within subject and the AI-vs-human label between subjects. All advice was correct and written by humans.
- **Finding.** Annotations gave OR 2.30 and the AI label OR 2.10. IM/EM physicians gained 5.66% (p=0.042); radiologists gained 3.41% (not significant).
- **Borrow.** Cross explanation display with AI correctness, to answer their untested question: do annotations also raise acceptance of wrong advice?

**Prinster 2024.** Prinster D, Mahmood A, Saria S, et al. Care to Explain? AI Explanation Types Differentially Impact Chest Radiograph Diagnostic Performance and Physician Trust in AI. *Radiology* 2024;313(2):e233261. DOI: [10.1148/radiol.233261](https://doi.org/10.1148/radiol.233261) · OA: [PMC11605106](https://pmc.ncbi.nlm.nih.gov/articles/PMC11605106/)
- **Design.** 220 physicians were analysed (132 radiologists, 88 IM/EM). Each saw 8 cases, 2 with incorrect advice from a purported tool called "ChestAId".
  - **Workflow.** Readers viewed the image first, but entered their diagnosis only after the advice appeared.
  - **Factors.** Explanation type (local boxes vs a global prototype image) was between subjects. The displayed confidence (65-94%) was randomized independently of correctness.
- **Finding.** With correct AI, accuracy was 92.8% (local) vs 85.3% (global). With incorrect AI it was 23.6% vs 26.1%. Local explanations made physicians align with the AI faster even when it was wrong, which they did not notice.
- **Borrow.** Record "simple trust": the latency from AI reveal to the final answer. Make AI-stated confidence a within-reader factor, independent of correctness.

**Sayres 2019** (abstract only). Sayres R, Taly A, Rahimy E, et al.; Webster DR. Using a deep learning algorithm and integrated gradients explanation to assist grading for diabetic retinopathy. *Ophthalmology* 2019;126(4):552-564. DOI: [10.1016/j.ophtha.2018.11.016](https://doi.org/10.1016/j.ophtha.2018.11.016)
- **Design.** 10 ophthalmologists graded 1,796 fundus images unassisted, with model grades only, or with grades plus a heat map.
- **Finding.** Heat maps improved accuracy for images with diabetic retinopathy (DR) (P<0.001) but reduced it for images without DR (P=0.006).
- **Borrow.** Analyse heat-map effects separately for normal and abnormal cases.

**Reverberi 2022.** Reverberi C, Rigon T, Solari A, Hassan C, Cherubini P; GI Genius CADx Study Group; Cherubini A. Experimental evidence of effective human-AI collaboration in medical decision-making. *Sci Rep* 2022;12(1):14952. DOI: [10.1038/s41598-022-18751-2](https://doi.org/10.1038/s41598-022-18751-2) · OA: [PMC9440124](https://pmc.ncbi.nlm.nih.gov/articles/PMC9440124/)
- **Design.** 21 endoscopists from 5 countries classified 504 lesion videos. Session 1 was unaided. Session 2, at least 2 weeks later, showed a real CADx label. Readers reported their own confidence and what they took the AI's diagnosis and confidence to be.
- **Finding.** Accuracy went from 0.768 to 0.802 (AI alone 0.849), with an AI influence OR of 3.05. Readers followed the AI more when it was correct, weighing their own confidence against how reliable it seemed.
- **Borrow.** After the reveal, ask how confident the AI seemed, so switching can be modelled as own confidence vs perceived AI confidence.

**Ewals 2024.** Ewals LJS, Heesterbeek LJJ, Yu B, et al. The Impact of Expectation Management and Model Transparency on Radiologists' Trust and Utilization of AI Recommendations for Lung Nodule Assessment on Computed Tomography: Simulated Use Study. *JMIR AI* 2024;3:e52211. DOI: [10.2196/52211](https://doi.org/10.2196/52211) · OA: [PMC11041414](https://pmc.ncbi.nlm.nih.gov/articles/PMC11041414/)
- **Design.** 20 radiologists from 7 Dutch centres each read 7 CTs for incidental nodules, first without AI and then with it.
  - **Factors.** A 2x2 design crossed onboarding style (informative vs reflective) with output (black box vs explainable).
  - **AI.** Detection came from a real model; the explanations were simulated by radiologists.
- **Finding.** Of 12 follow-up changes: 7 went wrong→correct, 3 wrong→better, 1 wrong→worse and 1 correct→wrong. Correct follow-up rose from 94/140 to 100/140. Trust fell over the task in the explainable group.
- **Borrow.** Their transition table is ready-made rescued/harmed accounting on an ordinal scale. Standardize or randomize onboarding.

**McGuirl and Sarter 2006** (abstract only). McGuirl JM, Sarter NB. Supporting trust calibration and the effective use of decision aids by presenting dynamic system confidence information. *Human Factors* 2006;48(4):656-65. DOI: [10.1518/001872006779166334](https://doi.org/10.1518/001872006779166334)
- **Design.** 30 instructor pilots flew 28 approaches each in an icing simulator. One group was told only the aid's overall reliability; the other saw continuously updated case-level confidence.
- **Finding.** Pilots who saw updated confidence had fewer stalls, reversed failing responses more often and judged the aid's accuracy better.
- **Borrow.** Decide deliberately whether displayed confidence is calibrated or decoupled from correctness, and record which.

**Zhang 2020.** Zhang Y, Liao QV, Bellamy RKE. Effect of Confidence and Explanation on Accuracy and Trust Calibration in AI-Assisted Decision Making. *Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency (FAT* '20)*. DOI: [10.1145/3351095.3372852](https://doi.org/10.1145/3351095.3372852) · OA: [arXiv](https://arxiv.org/pdf/2001.02114)
- **Design.** Crowd workers (72 in experiment 1) predicted income. On each trial they predicted first, then saw the AI, then answered again. Confidence display and explanations were varied.
- **Finding.** Confidence scores increased reliance when the AI was confident but did not improve joint accuracy. Local explanations did not help readers tell right AI answers from wrong ones.
- **Borrow.** Use "switch percentage" (switches only among disagreement trials) as the main reliance measure.

**Instructions and framing**

**Kunar 2023.** Kunar MA, Watson DG. Framing the fallibility of Computer-Aided Detection aids cancer detection. *Cognitive Research: Principles and Implications* 2023;8(1):30. DOI: [10.1186/s41235-023-00485-y](https://doi.org/10.1186/s41235-023-00485-y) · OA: [PMC10209366](https://pmc.ncbi.nlm.nih.gov/articles/PMC10209366/)
- **Design.** Untrained student volunteers (about 40 per experiment) searched simulated mammograms with simulated CAD boxes. On target-present trials, 20% of cues were incorrect. The framing text before the task was varied, up to an instruction to "IGNORE the CAD cues".
- **Finding.** Mild framing did nothing. A strong warning reduced misses and false alarms on incorrect-CAD trials (Experiment 2: t(38)=2.19, p=0.04; t(38)=2.29, p=0.03) without hurting correct-CAD trials. Over-reliance persisted.
- **Borrow.** Version and log the exact instructions each reader saw. Randomize disclosure text if the ethics committee allows it.

Rezazade Mehrizi 2023 (priming videos) and Bernstein 2023 (accountability framing, box) also belong here; see section 2.

### 3.4 Real-world evidence

**CAD-era warnings**

**Fenton 2007** (abstract only). Fenton JJ, Taplin SH, Carney PA, et al. Influence of computer-aided detection on performance of screening mammography. *N Engl J Med* 2007;356(14):1399-409. DOI: [10.1056/NEJMoa066099](https://doi.org/10.1056/NEJMoa066099) · OA: [PMC3182841](https://pmc.ncbi.nlm.nih.gov/articles/PMC3182841/)
- **Design.** 429,345 screening mammograms at 43 US facilities. 7 facilities were compared before and after adopting CAD.
- **Finding.** After CAD, specificity fell from 90.2% to 87.2% and PPV from 4.1% to 3.2%, and biopsies rose 19.7%. The sensitivity gain was not significant (80.4% to 84.0%, P=0.32).
- **Borrow.** Harm often appears as lost specificity. Include many normal cases carrying false-positive AI marks.

**Lehman 2015** (abstract only). Lehman CD, Wellman RD, Buist DS, et al.; Breast Cancer Surveillance Consortium. Diagnostic Accuracy of Digital Screening Mammography With and Without Computer-Aided Detection. *JAMA Intern Med* 2015;175(11):1828-37. DOI: [10.1001/jamainternmed.2015.5231](https://doi.org/10.1001/jamainternmed.2015.5231) · OA: [PMC4836172](https://pmc.ncbi.nlm.nih.gov/articles/PMC4836172/)
- **Design.** 271 radiologists and about 625,000 screens. 107 radiologists read both with and without CAD.
- **Finding.** CAD improved no measure. Within the same radiologist, sensitivity was lower with CAD (OR 0.53, 0.29-0.97).
- **Borrow.** Within-reader comparisons with a random effect per radiologist are the most sensitive way to detect harm.

**AI screening trials and deployments**

**Lång 2023 (MASAI safety)** (abstract only). Lång K, Josefsson V, Larsson AM, et al. Artificial intelligence-supported screen reading versus standard double reading in the Mammography Screening with Artificial Intelligence trial (MASAI): a clinical safety analysis of a randomised, controlled, non-inferiority, single-blinded, screening accuracy study. *Lancet Oncol* 2023;24(8):936-944. DOI: [10.1016/S1470-2045(23)00298-X](https://doi.org/10.1016/S1470-2045(23)00298-X)
- **Design.** 80,033 women were randomised. The AI's risk score triaged exams to single or double reading. Readers saw the score on every exam, CAD marks on high scores, and were not masked to allocation.
- **Finding.** Cancer detection was 6.1 vs 5.1 per 1000, and screen-reading workload fell 44.3%.
- **Borrow.** "AI output" can be two separate signals. Make the reveal configurable (score, marks, both) and log exactly what each reader saw.

**Hernström 2025 (MASAI full cohort)** (abstract only). Hernström V, Josefsson V, Sartor H, et al. Screening performance and characteristics of breast cancer detected in the Mammography Screening with Artificial Intelligence trial (MASAI): a randomised, controlled, parallel-group, non-inferiority, single-blinded, screening accuracy study. *Lancet Digit Health* 2025;7(3):e175-e183. DOI: [10.1016/S2589-7500(24)00267-X](https://doi.org/10.1016/S2589-7500(24)00267-X) · OA: [journal](https://www.thelancet.com/journals/landig/article/PIIS2589-7500(24)00267-X/fulltext)
- **Finding.** Cancer detection was 6.4 vs 5.0 per 1000 (ratio 1.29) with no significant rise in false positives (ratio 1.01), and 44.2% fewer screen readings.
- **Borrow.** Store ground-truth metadata for each case (lesion type, size, grade, density) so rescue and harm rates can be broken down by case type.

**Gommers 2026 (MASAI interval cancers)** (abstract only). Gommers J, Hernström V, Josefsson V, et al. Interval cancer, sensitivity, and specificity comparing AI-supported mammography screening with standard double reading without AI in the MASAI study: a randomised, controlled, non-inferiority, single-blinded, population-based, screening-accuracy trial. *Lancet* 2026;407(10527):505-514. DOI: [10.1016/S0140-6736(25)02464-X](https://doi.org/10.1016/S0140-6736(25)02464-X)
- **Finding.** Interval cancers were 1.55 vs 1.76 per 1000 (non-inferior). Sensitivity was 80.5% vs 73.8%, and specificity 98.5% in both arms.
- **Borrow.** Lab studies with many wrong suggestions show large harm, while real practice shows a modest net benefit. Record each study's AI error rate so results can be re-weighted to a realistic rate.

**Dembrower 2023 (ScreenTrustCAD)** (abstract only). Dembrower K, Crippa A, Colón E, et al.; ScreenTrustCAD Trial Consortium. Artificial intelligence for breast cancer detection in screening mammography in Sweden: a prospective, population-based, paired-reader, non-inferiority study. *Lancet Digit Health* 2023;5(10):e703-e711. DOI: [10.1016/S2589-7500(23)00153-X](https://doi.org/10.1016/S2589-7500(23)00153-X) · OA: [journal](https://www.thelancet.com/journals/landig/article/PIIS2589-7500(23)00153-X/fulltext)
- **Design.** 55,581 women. Every exam was read independently, without AI, by two radiologists and separately by the AI. Any positive flag went to a consensus discussion.
- **Finding.** One radiologist plus AI was non-inferior to two radiologists (261 vs 250 cancers).
- **Borrow.** A real-world analogue of your locked first read. Enforce the lock on the server, not only in the interface.

**Dembrower 2025** (abstract only). Dembrower KE, Crippa A, Eklund M, Strand F. Human-AI Interaction in the ScreenTrustCAD Trial: Recall Proportion and Positive Predictive Value Related to Screening Mammograms Flagged by AI CAD versus a Human Reader. *Radiology* 2025;314(3):e242566. DOI: [10.1148/radiol.242566](https://doi.org/10.1148/radiol.242566)
- **Finding.** At consensus, exams flagged only by the AI were recalled less often than exams flagged only by a radiologist (4.6% vs 14.2%). Those AI-only recalls had a much higher PPV (22% vs 3.4%), which suggests a stricter bar for AI flags.
- **Borrow.** Score harmful acceptance and harmful rejection separately. Consider randomizing the "AI" vs "colleague" label.

**Eisemann 2025 (PRAIM).** Eisemann N, Bunk S, Mukama T, et al. Nationwide real-world implementation of AI for cancer detection in population-based mammography screening. *Nat Med* 2025;31(3):917-924. DOI: [10.1038/s41591-024-03408-6](https://doi.org/10.1038/s41591-024-03408-6) · OA: [PMC11922743](https://pmc.ncbi.nlm.nih.gov/articles/PMC11922743/)
- **Design.** 461,818 women and 119 radiologists at 12 German sites. Use of the AI was voluntary for each exam. The AI worked in two ways:
  - **"Normal" tag.** Exams the AI judged highly unsuspicious were tagged normal in the worklist, visible before the case was opened.
  - **Safety net.** A forced accept/reject alert appeared after an unaided "unsuspicious" read of an exam the AI judged highly suspicious.
- **Finding.** Detection was 17.6% higher with no rise in recalls. The safety net led to 204 cancers. Normal-tagged exams were read in a median 16 s vs 30 s. The visible tag changed which viewer readers chose ("reading behavior bias"), which forced a change to the analysis plan.
- **Borrow.** Never show any AI-derived information (tags, sort order, priority) before the unaided read. Copy the forced accept/reject step. The study was funded by the vendor, Vara.

**Chang 2025 (AI-STREAM).** Chang YW, Ryu JK, An JK, et al. Artificial intelligence for breast cancer screening in mammography (AI-STREAM): preliminary analysis of a prospective multicenter cohort study. *Nat Commun* 2025;16(1):2248. DOI: [10.1038/s41467-025-57469-3](https://doi.org/10.1038/s41467-025-57469-3) · OA: [PMC11885569](https://pmc.ncbi.nlm.nih.gov/articles/PMC11885569/)
- **Design.** 24,543 Korean women were screened by breast radiologists at 6 hospitals.
  - **Locked reads.** An unaided read was recorded and locked, the AI was then shown automatically, and a second locked read followed.
  - **AI display.** Score and mark shown at a per-breast score of 10 or higher.
- **Finding.** Cancer detection was 5.70‰ with AI vs 5.01‰ without, with recall unchanged (4.53% vs 4.48%). In an exploratory simulation, general radiologists gained more (+26.4%) but also recalled more.
- **Borrow.** The closest real-world match to your study mode. Store both reads as immutable, timestamped records, and size studies with McNemar paired analysis (discordant pairs = rescued vs talked out).

**Lauritzen 2024** (abstract only). Lauritzen AD, Lillholm M, Lynge E, et al. Early Indicators of the Impact of Using AI in Mammography Screening for Breast Cancer. *Radiology* 2024;311(3):e232479. DOI: [10.1148/radiol.232479](https://doi.org/10.1148/radiol.232479) · OA: [journal](https://pubs.rsna.org/doi/10.1148/radiol.232479)
- **Finding.** In Denmark, after AI deployment recall fell from 3.09% to 2.46% and detection rose from 0.70% to 0.82%, with 33.5% less reading. The AI threshold was changed partway through.
- **Borrow.** Version the AI configuration (model, threshold, display) on every case shown.

**McCabe 2026** (abstract only). McCabe MP, Wakelin EA, Louis LD, et al. Closing the Performance Gap between Generalists and Breast Imaging Specialists Using a Nationally Deployed AI Workflow for Screening Mammography. *Radiology* 2026;320(1):e252005. DOI: [10.1148/radiol.252005](https://doi.org/10.1148/radiol.252005)
- **Finding.** Among 95 radiologists, generalists' detection rose from 3.76 to 4.99 per 1000, but their recall also rose (9.06% to 10.40%). Specialists showed no significant change. The design bundles concurrent CAD with an expert second review, so their effects cannot be separated.
- **Borrow.** Collect a structured reader profile at sign-up and keep AI components separable.

**Other settings**

**Nam 2023** (abstract only). Nam JG, Hwang EJ, Kim J, et al. AI Improves Nodule Detection on Chest Radiographs in a Health Screening Population: A Randomized Controlled Trial. *Radiology* 2023;307(2):e221894. DOI: [10.1148/radiol.221894](https://doi.org/10.1148/radiol.221894)
- **Finding.** 10,476 people were randomised at patient level. Actionable nodules were detected in 0.59% vs 0.25% (OR 2.4). A companion emergency-department RCT found no gain.
- **Borrow.** Offer case-level randomisation (each case with or without AI) as an alternative mode that avoids the second-look confound.

**Shin 2023.** Shin HJ, Han K, Ryu L, Kim EK. The impact of artificial intelligence on the reading times of radiologists for chest radiographs. *NPJ Digit Med* 2023;6(1):82. DOI: [10.1038/s41746-023-00829-4](https://doi.org/10.1038/s41746-023-00829-4) · OA: [PMC10148851](https://pmc.ncbi.nlm.nih.gov/articles/PMC10148851/)
- **Finding.** 11 radiologists read 18,680 CXRs, with the AI visible in some months and hidden in others. Reads were faster with AI (13.3 s vs 14.8 s), mainly when the AI found nothing (10.8 s vs 13.1 s).
- **Borrow.** Short post-reveal times on AI-negative cases are a free behavioural marker of over-reliance.

**Budzyń 2025** (abstract only). Budzyń K, Romańczyk M, Kitala D, et al. Endoscopist deskilling risk after exposure to artificial intelligence in colonoscopy: a multicentre, observational study. *Lancet Gastroenterol Hepatol* 2025;10(10):896-903. DOI: [10.1016/S2468-1253(25)00133-5](https://doi.org/10.1016/S2468-1253(25)00133-5)
- **Finding.** Adenoma detection in colonoscopies done without AI fell from 28.4% to 22.4% after endoscopists had been using AI (retrospective, observational).
- **Borrow.** Deskilling is visible only if unaided performance is measured again. Build in periodic AI-free probe sessions.

### 3.5 Methods, guidelines and ethics

**Study design and statistics**
- **FDA 2022 CADe guidance.** US Food and Drug Administration, CDRH. Clinical Performance Assessment: Considerations for Computer-Assisted Detection Devices Applied to Radiology Images and Radiology Device Data in Premarket Notification (510(k)) Submissions. FDA Guidance (Docket FDA-2009-D-0503); final, Sept 28, 2022. [Landing page](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-performance-assessment-considerations-computer-assisted-detection-devices-applied-radiology) · [PDF](https://www.fda.gov/media/77642/download)
  - **Point.** Your read, commit, reveal flow is FDA's "sequential design". The guidance warns that readers may undercall the unaided read, which inflates the aided effect. Its fix is to randomize a fraction of cases to be read unaided only, revealing that only after the commit. Sessions that repeat cases should be at least four weeks apart. It also recommends training on non-test cases and justifying any rules for changing the initial read.
  - **Borrow.** Build in a hidden no-reveal subset per reader.
- **Obuchowski and Bullen 2022** (abstract only). Obuchowski NA, Bullen J. Multireader Diagnostic Accuracy Imaging Studies: Fundamentals of Design and Analysis. *Radiology* 2022;303(1):26-34. DOI: [10.1148/radiol.211593](https://doi.org/10.1148/radiol.211593)
  - **Point.** A tutorial on multi-reader multi-case (MRMC) design and analysis, including correcting for multiple endpoints and location bias.
  - **Borrow.** Treat readers and cases as random effects. Pre-specify one primary endpoint.
- **Park 2023** (abstract only). Park SH, Han K, Jang HY, et al. Methods for Clinical Evaluation of Artificial Intelligence Algorithms for Medical Diagnosis. *Radiology* 2023;306(1):20-31. DOI: [10.1148/radiol.220182](https://doi.org/10.1148/radiol.220182)
  - **Point.** A primer on paired and parallel designs and which reporting guideline fits each.
- **Gallas 2012** (abstract only). Gallas BD, Chan HP, D'Orsi CJ, et al. Evaluating imaging and computer-aided detection and diagnosis devices at the FDA. *Academic Radiology* 2012;19(4):463-77. DOI: [10.1016/j.acra.2011.12.016](https://doi.org/10.1016/j.acra.2011.12.016) · OA: [PMC5557046](https://pmc.ncbi.nlm.nih.gov/articles/PMC5557046/)
  - **Point.** The regulatory-science background from the FDA-MIPS workshop.
- **Beiden 2002** (abstract only). Beiden SV, Wagner RF, Doi K, et al. Independent versus sequential reading in ROC studies of computer-assist modalities: analysis of components of variance. *Academic Radiology* 2002;9(9):1036-43. DOI: [10.1016/s1076-6332(03)80479-8](https://doi.org/10.1016/s1076-6332(03)80479-8)
  - **Point.** Sequential reading may be the more sensitive probe of the aided-unaided difference, provided the mean effect is not perturbed.
- **Obuchowski 2010** (abstract only). Obuchowski NA, Meziane M, Dachman AH, Lieber ML, Mazzone PJ. What's the control in studies measuring the effect of computer-aided detection (CAD) on observer performance? *Academic Radiology* 2010;17(6):761-7. DOI: [10.1016/j.acra.2010.01.018](https://doi.org/10.1016/j.acra.2010.01.018)
  - **Point.** Sequential and crossover designs gave similar CAD-effect estimates; the sequential design had narrower CIs.
  - **Borrow.** Make sequential the default mode, with an optional crossover arm.
- **Obuchowski 2012** (abstract only). Obuchowski NA, Gallas BD, Hillis SL. Multi-reader ROC studies with split-plot designs: a comparison of statistical methods. *Academic Radiology* 2012;19(12):1508-17. DOI: [10.1016/j.acra.2012.09.012](https://doi.org/10.1016/j.acra.2012.09.012) · OA: [PMC3522484](https://pmc.ncbi.nlm.nih.gov/articles/PMC3522484/)
  - **Borrow.** Volunteers will not read every case. Assign case blocks to reader groups by design (split-plot).
- **Dorfman, Berbaum and Metz 1992.** Dorfman DD, Berbaum KS, Metz CE. Receiver operating characteristic rating analysis. Generalization to the population of readers and patients with the jackknife method. *Investigative Radiology* 1992;27(9):723-31. DOI: [10.1097/00004424-199209000-00015](https://doi.org/10.1097/00004424-199209000-00015)
  - **Point.** The original DBM method (no PubMed abstract; described via later papers).
  - **Borrow.** Export long-format data (reader, case, condition, rating, truth) for existing MRMC software.
- **Gallas 2006** (abstract only). Gallas BD. One-shot estimate of MRMC variance: AUC. *Academic Radiology* 2006;13(3):353-62. DOI: [10.1016/j.acra.2005.11.030](https://doi.org/10.1016/j.acra.2005.11.030)
  - **Point.** The basis of the free FDA iMRMC software (https://github.com/DIDSR/iMRMC).
  - **Borrow.** Add an iMRMC export and a sample-size step to study setup.
- **Gallas 2019** (abstract only). Gallas BD, Chen W, Cole E, et al. Impact of prevalence and case distribution in lab-based diagnostic imaging studies. *Journal of Medical Imaging (Bellingham)* 2019;6(1):015501. DOI: [10.1117/1.JMI.6.1.015501](https://doi.org/10.1117/1.JMI.6.1.015501) · OA: [PMC6340399](https://pmc.ncbi.nlm.nih.gov/articles/PMC6340399/)
  - **Point.** AUC was robust to prevalence (largest difference 0.02), but readers recalled more aggressively as prevalence rose.
  - **Borrow.** Fix and report both disease prevalence and the planted-error rate.
- **Gur 2008** (abstract only). Gur D, Bandos AI, Cohen CS, et al. The "laboratory" effect: comparing radiologists' performance and variability during prospective clinical and laboratory mammography interpretations. *Radiology* 2008;249(1):47-53. DOI: [10.1148/radiol.2491072025](https://doi.org/10.1148/radiol.2491072025) · OA: [PMC2607194](https://pmc.ncbi.nlm.nih.gov/articles/PMC2607194/)
  - **Point.** Radiologists performed better and more consistently in the clinic than in the lab.
  - **Borrow.** Label platform results as laboratory findings.

**Measuring reliance and theory**
- **Schemmer 2023.** Schemmer M, Kühl N, Benz C, Bartos A, Satzger G. Appropriate Reliance on AI Advice: Conceptualization and the Effect of Explanations. *Proceedings of the 28th International Conference on Intelligent User Interfaces (IUI '23)*, ACM, pp. 410-422. DOI: [10.1145/3581641.3584066](https://doi.org/10.1145/3581641.3584066) · OA: [arXiv](https://arxiv.org/abs/2302.02187)
  - **Design.** 199 crowd participants classified hotel reviews. They made an initial decision with confidence, saw the advice of a real SVM (86% accurate), then revised. Cases were chosen so the advice was wrong on 8 of 16.
  - **Point.** Defines relative AI reliance (RAIR, your "rescued" rate) and relative self-reliance (RSR, 1 − RSR = "talked out of a correct read"). Each is normalized by opportunity.
  - **Borrow.** Use these as core metrics, with advice sampled evenly across the four correct/incorrect x positive/negative cells.
- **Cabitza 2023 (CHI).** Cabitza F, Campagner A, Angius R, Natali C, Reverberi C. AI Shall Have No Dominion: on How to Measure Technology Dominance in AI-supported Human decision-making. *Proceedings of the 2023 CHI Conference on Human Factors in Computing Systems (CHI '23)*, pp. 1-20. DOI: [10.1145/3544548.3581095](https://doi.org/10.1145/3544548.3581095) · OA: [ACM PDF](https://dl.acm.org/doi/pdf/10.1145/3544548.3581095)
  - **Point.** Statistics and plots that separate harmful dominance (automation bias) from beneficial dominance (algorithm appreciation).
- **Parasuraman and Manzey 2010** (abstract only). Parasuraman R, Manzey DH. Complacency and bias in human use of automation: an attentional integration. *Human Factors* 2010;52(3):381-410. DOI: [10.1177/0018720810376055](https://doi.org/10.1177/0018720810376055)
  - **Point.** Automation bias produces both omission and commission errors, affects experts, and cannot be prevented by training or instructions.
  - **Borrow.** Balance omission and commission plants and analyse them separately.
- **Goddard 2012** (abstract only). Goddard K, Roudsari A, Wyatt JC. Automation bias: a systematic review of frequency, effect mediators, and mitigators. *Journal of the American Medical Informatics Association* 2012;19(1):121-7. DOI: [10.1136/amiajnl-2011-000089](https://doi.org/10.1136/amiajnl-2011-000089) · OA: [PMC3240751](https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751/)
  - **Point.** 74 studies. Mitigators: training, accountability, advice position, updated confidence, and information rather than a recommendation.
  - **Borrow.** Make each mitigator a configurable factor.
- **Lyell and Coiera 2017** (abstract only). Lyell D, Coiera E. Automation bias and verification complexity: a systematic review. *Journal of the American Medical Informatics Association* 2017;24(2):423-431. DOI: [10.1093/jamia/ocw105](https://doi.org/10.1093/jamia/ocw105) · OA: [PMC7651899](https://pmc.ncbi.nlm.nih.gov/articles/PMC7651899/)
  - **Point.** Automation bias appears in single diagnostic tasks with high verification complexity, and few studies used a control condition.

**Evidence syntheses**
- **Vasey 2021** (abstract only). Vasey B, Ursprung S, Beddoe B, et al. Association of Clinician Diagnostic Performance With Machine Learning-Based Decision Support Systems: A Systematic Review. *JAMA Network Open* 2021;4(3):e211276. DOI: [10.1001/jamanetworkopen.2021.1276](https://doi.org/10.1001/jamanetworkopen.2021.1276) · OA: [PMC7953308](https://pmc.ncbi.nlm.nih.gov/articles/PMC7953308/)
  - **Point.** 37 studies with a median of 4 clinicians each. 50% of results improved and 4% worsened; there was no benefit in representative clinical settings.
- **Zhao 2025.** Zhao D, Packer T, Jie X, et al. Diagnostic accuracy of artificial intelligence-assisted radiology assessment of cancer: a systematic review. *BJR|Artificial Intelligence* 2025;2(1):ubaf016. DOI: [10.1093/bjrai/ubaf016](https://doi.org/10.1093/bjrai/ubaf016) · OA: [journal](https://academic.oup.com/bjrai/article/2/1/ubaf016/8322749)
  - **Point.** Median 5.5 readers per dataset. Pooled sensitivity 0.67 unaided vs 0.79 with AI; specificity 0.82 vs 0.87. Half the studies had bias concerns on QUADAS-C, a risk-of-bias tool for comparative accuracy studies.
- **Lu 2026** (abstract only). Lu J, Xu X, Zhang Y, et al. Diagnostic Performance of AI-Assisted Radiologists in Breast Cancer Detection Using Digital Mammography: A Systematic Review and Meta-Analysis. *Clinical Breast Cancer* 2026;26(2):121-135. DOI: [10.1016/j.clbc.2025.08.013](https://doi.org/10.1016/j.clbc.2025.08.013)
  - **Point.** Effects differ by reading scenario. With concurrent AI, sensitivity was 0.84 vs 0.78.
- **Vaccaro 2024.** Vaccaro M, Almaatouq A, Malone T. When combinations of humans and AI are useful: A systematic review and meta-analysis. *Nature Human Behaviour* 2024;8(12):2293-2303. DOI: [10.1038/s41562-024-02024-1](https://doi.org/10.1038/s41562-024-02024-1) · OA: [PMC11659167](https://pmc.ncbi.nlm.nih.gov/articles/PMC11659167/)
  - **Point.** 106 studies. Human-AI teams were worse than the better of human or AI alone (g = −0.23) but better than humans alone (g = 0.64). Losses were concentrated in decision tasks.
  - **Borrow.** Report AI-alone accuracy on your exact case set.

**Reporting guidelines**
- **DECIDE-AI 2022.** Vasey B, Nagendran M, Campbell B, et al.; DECIDE-AI expert group. Reporting guideline for the early-stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI. *Nature Medicine* 2022;28(5):924-933 (also BMJ 2022;377:e070904). DOI: [10.1038/s41591-022-01772-9](https://doi.org/10.1038/s41591-022-01772-9) · OA: [PMC9116198](https://pmc.ncbi.nlm.nih.gov/articles/PMC9116198/)
  - **Point.** Item 12 (human-computer agreement, including users changing their mind) is essentially your switch analysis. Item 14b covers learning curves.
  - **Borrow.** Generate a DECIDE-AI-style export automatically.
- **CONSORT-AI 2020** (abstract only). Liu X, Cruz Rivera S, Moher D, Calvert MJ, Denniston AK; SPIRIT-AI and CONSORT-AI Working Group. Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension. *Nature Medicine* 2020;26(9):1364-1374. DOI: [10.1038/s41591-020-1034-x](https://doi.org/10.1038/s41591-020-1034-x) · OA: [PMC7598943](https://pmc.ncbi.nlm.nih.gov/articles/PMC7598943/)
  - **Point.** 14 AI-specific items, including human-AI interaction and an analysis of error cases.
- **CLAIM 2024** (abstract only). Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH, Kahn CE Jr; CLAIM 2024 Update Panel. Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 Update. *Radiology: Artificial Intelligence* 2024;6(4):e240300. DOI: [10.1148/ryai.240300](https://doi.org/10.1148/ryai.240300) · OA: [PMC11304031](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031/)
  - **Point.** Prefers "reference standard" to "ground truth". Whether it has a reader-study item was not verified.

**Ethics of deception**
- **Miller, Wendler and Swartzman 2005.** Miller FG, Wendler D, Swartzman LC. Deception in Research on the Placebo Effect. *PLoS Medicine* 2005;2(9):e262. DOI: [10.1371/journal.pmed.0020262](https://doi.org/10.1371/journal.pmed.0020262) · OA: [PMC1198039](https://pmc.ncbi.nlm.nih.gov/articles/PMC1198039/)
  - **Point.** Proposes "authorized deception": participants are told up front that some procedures are misdescribed and will be explained at the end. The paper provides model wording and notes that forewarning may raise suspicion.
- **Wendler and Miller 2004** (preview only). Wendler D, Miller FG. Deception in the pursuit of science. *Archives of Internal Medicine* 2004;164(6):597-600. DOI: [10.1001/archinte.164.6.597](https://doi.org/10.1001/archinte.164.6.597)
  - **Point.** Deception is justified when accurate information would bias the very response being measured.
- **Verbeke 2023** (abstract only). Verbeke K, Krawczyk T, Baeyens D, Piasecki J, Borry P. Informed Consent and Debriefing When Deceiving Participants: A Systematic Review of Research Ethics Guidelines. *Journal of Empirical Research on Human Research Ethics* 2023;18(3):118-133. DOI: [10.1177/15562646231173477](https://doi.org/10.1177/15562646231173477) · OA: [repository](https://ruj.uj.edu.pl/xmlui/handle/item/312378)
  - **Point.** Guidelines agree on principles but vary widely on implementation.
  - **Borrow.** Make consent and debrief configurable per study, with auditable logs.
- **Murphy and Greene 2023** (abstract only). Murphy G, Greene CM. Conducting ethical misinformation research: Deception, dialogue, and debriefing. *Current Opinion in Psychology* 2023;54:101713. DOI: [10.1016/j.copsyc.2023.101713](https://doi.org/10.1016/j.copsyc.2023.101713) · OA: [journal](https://doi.org/10.1016/j.copsyc.2023.101713)
  - **Point.** "Three D's": deception balanced by consent, dialogue with participants, and debriefing, which the authors describe as perhaps the most important of the three.
  - **Borrow.** Show each planted case with its correct answer in the debrief.

## 4. Design-space map

"Concurrent" = AI shown with the image. "Sequential" = unaided answer committed, then AI revealed on the same case. "Sessions" = unaided and aided reads in separate sessions.

| Study | Task | Readers | Real / purported AI | Wrong AI planted? | Unaided baseline? | Sequential or concurrent | What varied | Main effect |
|---|---|---|---|---|---|---|---|---|
| Dratsch 2023 (already read) | Mammography BI-RADS | 27 radiologists | Purported (pre-drawn heat maps) | Yes, 12 of 40 | No | No committed first read | AI correctness; experience | 79.7-82.3% accuracy with correct AI vs 19.8-45.5% with incorrect |
| Gaube 2021 | CXR + vignette | 138 rad + 127 IM/EM | Human-written, labelled AI or human | Yes, 2 of 8 | No | Concurrent | Source label | 27.54% of radiologists always followed wrong advice |
| Rezazade Mehrizi 2023 | Mammography BI-RADS | 92 (66% Iran) | Purported | Yes, 8 of 30 | No | AI on demand (click to reveal) | Explainability; priming | 78% vs 28%; no intervention helped |
| Bernstein 2023 | CXR, CT yes/no | 5 analysed | Sham | Yes, 12 of 90 | Yes (first session) | Sessions, AI concurrent | Accountability; box | FN 2.7% → 33.0%; box 20.7% |
| Prinster 2024 | CXR diagnosis | 220 (132 rad) | Simulated | Yes, 2 of 8 | No committed read | Image, then AI, then answer | Explanation type; stated confidence | Wrong AI: 23.6-26.1% accuracy; local explanations speed alignment |
| Jabbour 2023 | Respiratory failure vignettes | 457 hospital clinicians | Real + investigator-built biased models | Yes, 3 of 6 AI vignettes | Yes (different vignettes) | Concurrent | Heat maps; biased vs standard | Biased AI −11.3 pp; explanations did not offset |
| Pesapane 2026 | Mammography | 6 | Real, 30% shifted one category | Yes, 30% | Yes | Fixed-order conditions | Saliency XAI | Automation bias 36.1% → 17.8% |
| Kim 2025 | TOF-MRA aneurysm | 9 | Real, case selection | Yes, 10 of 20 with false-positive AI | Yes (crossover) | AI first | Experience | False-positive AI raised suspicion and follow-up |
| Taib 2026 | Screening mammography | 10 | Real, enriched | Yes, 14 FN + 14 FP of 60 | Yes (round 1) | Sessions | AI error type; eye tracking | Sensitivity on AI-missed cancers 71% → 39% |
| Shi 2025 | CTA aneurysm | 28 | Real vs sham model | Yes (sham, 0% sensitivity) | Yes | Not stated in abstract | Standard vs sham AI | Sham non-inferior to alone; 5.3% of true positives flipped |
| Wang 2023 | Knee MRI ACL | 40 | Real | No | Yes (crossover) | Concurrent | Expertise; AI confidence | Automation bias = 45.5% of assisted-round errors |
| Tschandl 2020 | Dermoscopy | 302 | Real + misleading arm | Yes | Yes | Sequential | Support format; faulty AI | Faulty AI misled experts too |
| Kiani 2020 | Liver pathology | 11 | Real | No | Yes (crossover) | Concurrent | AI correctness | OR 4.29 (AI right) vs 0.25 (AI wrong); null average |
| Yu 2024 | CXR, 15 labels | 140 | Real | No | Yes | Concurrent in assisted reads | Reader traits; AI error size | Wide heterogeneity; large AI error → large harm |
| Agarwal 2023 | CXR probabilities | 227 | Real | No | Yes | Both (design 3 sequential) | AI x clinical history | No average AI gain; automation neglect |
| Sim 2020 | CXR nodules | 12 | Real | No | Yes | Sequential | — | 104 better vs 56 worse of 2,400 |
| Fogliato 2022 | Veterinary radiographs | 19 | Real | No | Yes (two-step arm) | One-step vs two-step | Workflow order | Commit-first → less AI influence |
| Zheng 2004 | Mammography masses | 8 | Controlled cues | Yes (set FP cue rates) | Yes | Both | Timing; FP cue rate | Concurrent high-FP cues hurt |
| Halligan 2011 | CT colonography | 16 | Real CAD | No | Yes | Second-read vs concurrent | Timing | +7.0% vs +4.5% sensitivity |
| Lee 2022 | Breast US | 6 | Real | No | Yes | Sequential vs simultaneous | Workflow; experience | 16.8% vs 40.8% of reads changed |
| Ewals 2024 | CT lung nodules | 20 | Real + simulated explanations | No | Yes | Sequential | Onboarding; explainability | 10 improved vs 2 worse follow-up changes |
| Kunar 2023 | Simulated mammography | Students | Simulated CAD | Yes | Yes (different trials) | Concurrent | Fallibility framing | Strong warning reduced errors from wrong CAD |
| Song 2026 | Thoracic imaging, LLM | 10 | Real LLMs of different accuracy | Indirect (weak model) | Yes (session 1) | Sessions | Model confidence; expertise | Good rationales raised acceptance of wrong advice |
| Chang 2025 | Screening mammography, practice | Breast radiologists, 6 hospitals | Real | No | Yes (locked) | Sequential, locked | — | Detection 5.01‰ → 5.70‰, recall unchanged |
| Schemmer 2023 | Fake reviews (non-medical) | 199 crowd | Real SVM, case selection | Yes, 8 of 16 | Yes | Sequential | Explanations | Defines RAIR/RSR metrics |

**Patterns.**
- **Well studied: the wrong-AI effect.** Whenever the AI is wrong, accuracy collapses, usually to about a quarter to a third (Dratsch, Rezazade Mehrizi, Prinster, Gaube). Heat maps and explanations mostly fail to protect readers (Rezazade Mehrizi, Jabbour, Prinster), with one small exception where saliency halved the bias (Pesapane).
- **Well studied: timing.** It has been studied in both the CAD era and recently (Zheng, Halligan, Beyer, Lee, Fogliato, Cabitza). Committing first consistently lowers AI influence in both directions, so your design measures AI used as a second opinion.
- **Thin: planted errors plus a same-case baseline.** Studies that plant errors rarely also record a committed unaided answer on the same case. Bernstein, Kim 2025, Taib and Pesapane use separate sessions. The clean within-case versions are outside radiology (Tschandl, Schemmer, Zhang). Mammography and chest X-ray dominate; planted errors in CT, MRI or ultrasound appear only through case selection or a sham model (Kim 2025, Shi 2025).
- **Thin or absent: other factors.**
  - **AI confidence.** Only Prinster varied displayed confidence with planted errors, and it was decoupled from correctness.
  - **Reader calibration.** Only one preprint uses it as a moderator (Martin).
  - **Repeated exposure.** Trust drift or deskilling from repeated exposure has not been measured in radiology (Ewals looked within one session; Budzyń is endoscopy).
  - **Disclosure wording.** It has been tested only in students (Kunar).
  - **Language of the AI output.** No paper in this list studied it.

## 5. Gaps = research opportunities

1. **Sequential study with planted wrong AI in a modality Dratsch did not cover (e.g., head or chest CT).**
   - **Design.** Readers commit an answer and confidence, the AI is revealed (about 25-30% wrong, balanced over- and under-calls), and readers may revise. A hidden random subset of cases gets no reveal at all.
   - **Metrics.** Report RAIR/RSR per reader.
   - **Why it's open.**
     - Dratsch, Gaube 2021, Rezazade Mehrizi and Prinster had no committed unaided read.
     - Bernstein, Kim 2025 and Taib used separate sessions instead of a same-case baseline.
     - Planted errors in CT or MRI exist only through case selection or a sham model (Kim 2025, Shi 2025).
   - **Method sources.** The FDA guidance supplies the no-reveal check against undercalling; Beiden 2002 and Obuchowski 2010 support the sequential design's efficiency; Schemmer 2023 supplies the metrics.

2. **Show the AI's confidence or not: none vs calibrated vs decoupled, crossed with planted errors.**
   - **Add-on.** A prospective test of Wang 2023's rule for hiding the AI in its misleading zone, which was only simulated.
   - **Why it's open.**
     - Prinster used only decoupled random confidence.
     - Wang, Song and Reverberi studied natural confidence.
     - McGuirl & Sarter (pilots) and Zhang 2020 (crowd) were outside medicine.
     - Goddard 2012 lists updated confidence as a mitigator that has not been tested in radiology reader studies.

3. **Experience and calibration gradient across Iranian training levels, from first-year resident to subspecialist.**
   - **Design.** Start with an unaided skill block with confidence ratings (split sample). Pre-register experience, skill and calibration as moderators.
   - **Why it's open.** Yu 2024 and Martin 2026 disagree on whether unaided skill predicts benefit. Dratsch's experience gradient had no baseline. Povyakalo 2013, Pesapane, Lee 2022 and Kim 2025 used small reader groups. McCabe 2026 shows generalist vs specialist differences only at the level of whole practices.

4. **Persian vs English AI rationale.**
   - **Design.** Randomize the language of the AI's written explanation, crossed with correctness. Test whether a fluent native-language rationale increases acceptance of wrong advice.
   - **Why it's open.**
     - Song 2026 found better-written rationales raised acceptance of wrong suggestions (OR 1.71).
     - Jacobs 2021 found simple explanations made wrong recommendations more harmful.
     - Rezazade Mehrizi recruited mostly Iranian readers but varied explainability and priming, not language.
     - No paper in this list tested language.

5. **Repeated exposure: trust drift and deskilling.**
   - **Design.** A reader panel over several months with the AI error rate held fixed, periodic AI-free probe sessions, and per-reader RAIR/RSR tracked across sessions.
   - **Why it's open.**
     - Budzyń 2025 showed deskilling in endoscopy, not radiology.
     - Ewals 2024 saw trust fall within a single session.
     - Alberdi 2004 suggests readers do not notice an unusual error rate.
     - Kim 2025's warm-up shows early exposure is used to shape trust.
     - Shin 2023 shows AI changes reading effort.
     - DECIDE-AI item 14b asks for learning curves.

6. **Disclosure wording as a randomized factor.**
   - **Arms.** Standard ("AI assistant"), authorized-deception consent ("some aspects are not fully described; AI suggestions may not be accurate; you will be debriefed"), and a strong warning.
   - **Two answers at once.** Whether forewarning reduces reliance, and whether it breaks the study, which is Miller 2005's concern. Useful evidence for Iranian ethics committees.
   - **Why it's open.**
     - Kunar 2023 tested framing only in students.
     - Wang 2023 told readers the AI errs and still saw substantial automation bias.
     - Parasuraman & Manzey (2010) state that instructions do not prevent automation bias.
     - Bernstein had to exclude a reader who suspected the cover story.
     - Verbeke 2023 shows guidelines disagree on implementation.

7. **Omission vs commission errors, with a downstream action.**
   - **Design.** Plant AI false negatives (silent on a real finding) and false positives in equal numbers. Record the label and the action (recall, biopsy, follow-up), and score flips that cross an action threshold. Log zoom, pan and dwell as a search proxy.
   - **Why it's open.**
     - Taib 2026 and Drew 2012 found missed findings the most harmful but had few or no radiologist readers analysed by error type.
     - Zheng 2004 found less search outside cues.
     - Southern 2009 showed actions shift even when the read does not.
     - Lee 2022 and Fenton 2007 point to threshold and specificity harms.

8. **Source label and placebo AI.**
   - **Design.** Randomize the suggestion's label (AI vs senior colleague) and add a sham AI box with no real signal.
   - **Why it's open.** Gaube 2021/2023 varied the label only with concurrent advice and no baseline. Dembrower 2025 shows radiologists treat AI flags and human flags differently in real consensus. Shi 2025 is the only sham-model precedent, and its reading order is not described.

## 6. Ethics and consent notes (only what the papers state)

**What readers were told about the AI**
- **Told it can be wrong, or shown errors.**
  - Wang 2023: shown correct and incorrect examples and told not to rely on the AI completely, especially at low confidence.
  - Ewals 2024: onboarding showed false-positive and false-negative examples.
  - Alberdi 2004: the parent trial showed readers examples of inappropriate prompts.
  - Kunar 2023: the strong-warning condition told participants to ignore CAD.
  - Agarwal 2023: readers got training materials on the model and its performance and had to pass comprehension questions.
- **Given a cover story, or told the AI was real.**
  - Bernstein 2023: several "AI programs" with AUC >0.85, plus a false claim that performance would be compared with colleagues'.
  - Rezazade Mehrizi 2023: explicitly told the AI was real, "to avoid suspicion".
  - Prinster 2024: radiologist-written advice presented as "ChestAId".
  - Gaube 2021 and 2023: human-written advice labelled as AI for half the participants.
  - Ewals 2024: participants were unaware the explanations were simulated.
  - Jacobs 2021: each recommendation was attributed to a different model.
  - Kim 2025: readers were blinded to the design and warmed up with true-positive cases "to cultivate trust".
  - Alberdi 2004: Study 1 was designed to mask the lower CAD sensitivity.
- **No deception described.** Fogliato 2022, Agarwal 2023, Yu 2024, Rajpurkar 2020, Halligan 2011.
- **Not stated in the pages checked.** Jabbour 2023 (66.7% of its participants said they were unaware AI could be systematically biased), Pesapane 2026, Shi 2025, Taib 2026, Tsai 2003, Southern 2009, Reverberi 2022, Kiani 2020, Buçinca 2021 (whether participants were told the AI was simulated).

**Debriefing**
- Only Bernstein 2023 explicitly reports debriefing, with all deception explained. It also excluded one reader who did not believe the cover story.
- Debriefing is not reported, or not found in the text checked, for Gaube 2021, Rezazade Mehrizi 2023, Alberdi 2004, Prinster 2024, Jabbour 2023, Jacobs 2021, Buçinca 2021, Pesapane 2026 and the misleading-AI arm of Tschandl 2020.

**Consent, approval, incentives, registration**
- **Informed consent obtained.**
  - Gaube 2021: MIT review declared it exempt; consent obtained; raffle entry.
  - Gaube 2023: consent checkbox; raffle.
  - Prinster 2024: written consent; $10 gift card; Johns Hopkins IRB.
  - Jabbour 2023: exempt; consent before randomization; $50 gift card.
  - Rezazade Mehrizi 2023: informed consent and opt-in; departmental ethics committee.
  - Kunar 2023: written consent; paid.
  - Reverberi 2022: written consent.
  - Jacobs 2021: online consent; $20 gift card; Harvard IRB.
  - Lindsey 2018: IRB exemption; consent obtained.
  - Rajpurkar 2020: Stanford IRB and University of Cape Town ethics review; consent obtained.
  - Shin 2023: radiologists consented specifically to having reading times collected.
  - Fogliato 2022: Mars IRB; consent form.
  - Buçinca 2021: consent form; paid.
  - Tschandl 2020: research consent at platform registration, withdrawable at any time.
- **Consent waived for readers.** Wang 2023 ("laboratory study"), Kim 2025, Lee 2022 (retrospective).
- **Data-collection transparency.** In Agarwal 2023, participants were not explicitly told that active time and clickstream were recorded.
- **Accuracy incentives.** A random subset in Agarwal 2023 got a $120 bonus scored with a proper scoring rule. Schemmer 2023 paid a bonus per correct decision.
- **Registration.** Pre-registered: Gaube 2021 (OSF), Prinster 2024 (OSF), Agarwal 2023 (AEARCTR-0009620). Jabbour 2023 registered only after completion. Kunar 2023 was not pre-registered.

**What the ethics and methods papers add**
- **Miller 2005.** Offers authorized-deception consent wording and warns that forewarning may raise suspicion.
- **Wendler and Miller 2004.** Justifies deception when disclosure would bias the measured response.
- **Verbeke 2023.** Finds guidelines disagree on how to implement consent and debriefing.
- **Murphy and Greene 2023.** Call effective debriefing perhaps the most important safeguard and ask authors to report their ethical practices.
- **FDA 2022.** Notes that retrospective reading may change reader behaviour because readers know patient management is unaffected.

**Where the papers are silent**
- No radiology study in this list reports using authorized-deception consent.
- None reports checking whether the debrief corrected a wrong lesson learned from a planted case, although Murphy and Greene raise this risk for misinformation studies.
- None reports readers' reactions or distress after learning they were talked out of a correct read.
- None addresses how per-reader performance data are protected from employers or training programmes.
- The one study with mostly Iranian readers (Rezazade Mehrizi 2023) reports only a departmental ethics approval and says nothing about Iranian ethics requirements.