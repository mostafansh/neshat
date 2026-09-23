# Leak-tracing watermarks and Cloudflare: what the evidence says (checked 2026-09-23)

## A. Watermarks that identify who leaked an image

**Short answer:** your idea is sound, but a watermark does not stop anyone copying an image. It does two things:
- **Deterrence:** readers who know every image is traceable to them are less likely to leak.
- **Evidence:** it links a leaked copy to one person.

A signed agreement is what turns that evidence into consequences. The agreement and the access log do most of the work, and the mark connects a leaked copy to a row in the log.

The best-known precedent is the 2004 Oscar screeners. Watermarked copies leaked online and were traced to Academy member Carmine Caridi. He was expelled and ordered to pay Warner Bros. $300,000, even though someone else (Russell Sprague) did the uploading ([Wikipedia](https://en.wikipedia.org/wiki/Carmine_Caridi), accessed 2026-09-23). The lesson for your agreement: make each reader responsible for safeguarding their copies and login, not only for leaking personally.

### Three kinds of tracing
- **Visible stamp** (a faint code drawn on or next to the image).
  - Azure Virtual Desktop tiles faint QR codes that hold only a random connection ID. Admins look that ID up in their logs to find the user, so the code itself reveals no name ([Microsoft](https://learn.microsoft.com/en-us/azure/virtual-desktop/watermarking), updated 2025-06-21).
  - Citrix stamps the user's identity and calls the feature "not a security feature", offering only deterrence and traceability ([Citrix](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/graphics/introduction/session-watermark-introduction.html), accessed 2026-09-23).
  - Microsoft's stamp is drawn by its own app, and it disappears when users connect with a different program. For your website, this means the stamp must be burned into the image pixels on your server. A stamp drawn by browser code can simply be deleted by the viewer.
- **Invisible ("forensic") watermark** (hidden pixel changes that software can read later).
  - Simple "fragile" marks are useless for tracing leaks. These change the least-significant bit (LSB) of each pixel, the last bit of its grey value. In a 2025 test, the mark's match score fell from 0.82 to 0.01 as JPEG compression got stronger ([arXiv 2511.10245](https://arxiv.org/html/2511.10245), 2025-11-13).
  - Robust marks spread a weak signal across the whole image. The classic design survives compression, filtering, and printing then rescanning. It detects the mark by comparing against the original image, which your server keeps ([Cox et al., IEEE TIP](https://www.ee.columbia.edu/~ywang/MSS/HW2/CoxSpectrumWatermarking.pdf), 1997).
- **"Who had what" (canary trap):** give different people slightly different material and see which version leaks. MI5 and Tesla have used this ([Wikipedia](https://en.wikipedia.org/wiki/Canary_trap), accessed 2026-09-23).

### What survives what

| How the image leaks | Access log + file fingerprint | Visible code in a margin strip | Invisible mark (free libraries) | Which cases leaked* |
|---|---|---|---|---|
| File saved and forwarded unchanged | Traces exactly | Traces | Traces | Narrows suspects |
| Screenshot | No (the file's bytes change) | Traces unless cropped | Claimed by TrustMark; untested on radiographs | Narrows |
| Phone photo of the monitor | No | Traces if the code is in frame | Unknown | Narrows |
| Margin cropped off | No | No | Maybe (TrustMark claims about 20% crop) | Narrows |
| 2–3 readers combine their copies | No | No | Only with a special code spread over many images; unproven | Narrows to a group |
| Skilled attacker using AI removal tools | No | No | Removable | Still works |

*This column only helps when readers read different cases. In a design where everyone reads every case (as planned for the workshop), it tells you nothing.

What the evidence behind the table says:
- **Phone photos.** Invisible marks have survived phone photos only with methods trained specifically for screen capture, and only in lab conditions.
  - PIMoG needs the photo straightened and the image filling at least a quarter of the screen ([GitHub](https://github.com/FangHanNUS/PIMoG-An-Effective-Screen-shooting-Noise-Layer-Simulation-for-Deep-Learning-Based-Watermarking-Netw), 2022). Its GPL licence also imposes conditions if you build it into your software.
  - A 2025 method reports over 95% accuracy ([Sci Rep](https://www.nature.com/articles/s41598-025-00912-8), May 2025).
  - The gap between lab simulation and real phone photos is still an open problem ([arXiv 2504.18906](https://arxiv.org/abs/2504.18906), AAAI 2026).
- **Collusion** (several readers combine copies, for example by averaging them, to wash out their personal marks).
  - In theory, enough colluders can defeat any watermark ([Ergun, Kilian, Kumar](https://link.springer.com/chapter/10.1007/3-540-48910-X_10), 1999).
  - The defence is a "fingerprinting code" that still points to at least one colluder. For 2–3 colluders among 12 readers it needs roughly 370–830 bits, and that estimate is approximate at such small numbers ([Škorić et al.](https://eprint.iacr.org/2007/041), 2008). That is more than one image can carry, so the code has to be spread across the many images each reader receives.
  - Video streaming already works this way. Each segment is prepared in two marked versions, A and B, and each viewer gets a unique A/B sequence ([Irdeto](https://irdeto.com/blog/modern-forensic-watermarking-at-scale), accessed 2026-09-23). This is standardised as ETSI TS 104 002, Aug 2023 ([Fora Soft](https://www.forasoft.com/learn/video-streaming/articles-streaming/forensic-watermarking-ab-streaming), 2026-09-19).
- **Skilled attackers.**
  - "Regeneration" attacks add noise and then let an AI image model redraw the picture. They provably remove pixel-level invisible marks while the image looks unchanged ([NeurIPS 2024](https://arxiv.org/abs/2306.01953), revised 2024-10-31).
  - In a May 2026 study, TrustMark and VideoSeal marks were removed with smaller image changes than a classic method needed ([arXiv 2605.27135](https://arxiv.org/abs/2605.27135), 2026-05-26).
  - Marks can also be **forged**: WmForger fakes or removes marks using only one watermarked image ([arXiv 2510.20468](https://arxiv.org/abs/2510.20468), 2025).
  - So treat a detected mark as grounds for an investigation, not as proof. Stamp secret random codes that your server maps to a person, never names.

### Free libraries
None of these handles 12/16-bit medical data; all take 8-bit colour images.
- **Meta VideoSeal / PixelSeal** (MIT licence, 256 bits, Dec 2025) ([GitHub](https://github.com/facebookresearch/videoseal)). It hides its data in the brightness channel only ([WAM README](https://github.com/facebookresearch/watermark-anything)), so it should survive conversion to grayscale. It is the best fit for you. It makes no claims about surviving screenshots or phone photos.
- **Adobe TrustMark** (MIT licence, 100 bits). The "P" version changes the image very little: its PSNR, a similarity score where higher means closer to the original, is above 50 dB. Its FAQ claims it survives screenshots and printing ([FAQ](https://github.com/adobe/trustmark/blob/main/FAQ.md), accessed 2026-09-23). However, it has no secret key by design: anyone can read or remove it with the official code. The FAQ also says it is not meant for marking images secretly without consent. It only deters non-technical leakers. It downloads model files on first use, so download them in advance in case they are blocked.
- **Avoid:**
  - invisible-watermark (last updated 2023-09-23). Its README lists poor results on screenshots and on images with large uniform backgrounds, which describes a radiograph's black borders ([GitHub](https://github.com/ShieldMnt/invisible-watermark)).
  - Watermark Anything (archived 2026-08-01).
  - Stable Signature and SynthID. Stable Signature only marks AI-generated images, and SynthID is not open ([arXiv 2510.09263](https://arxiv.org/abs/2510.09263), 2025-10-10).
- **Commercial:** Imatag (price on request) and Steg.AI (from $10/month) claim their marks survive screenshots, and Steg.AI also claims phone photos. Neither mentions medical or grayscale images, and these are marketing claims ([Steg.AI](https://steg.ai/pricing/), [Imatag](https://www.imatag.com/api/forensic-watermarking-api), accessed 2026-09-23).

### Keeping images diagnostic
- **Window/level** (the brightness/contrast setting).
  - CT windows range from brain W80 to lung W1500 ([Radiopaedia](https://radiopaedia.org/articles/windowing-ct), 2025-01-07). By my arithmetic, 1 HU spans about 3 screen grey levels in a brain window but only about 0.17 in a lung window.
  - So a mark embedded in the raw CT numbers would look exaggerated in narrow windows and vanish in wide ones. A mark behaves predictably only on the final 8-bit picture you send.
  - Render a few preset windows on the server. Do not send raw data and let the browser do the windowing.
- **Perceptibility.**
  - A 2023 review treats PSNR above 40 dB as acceptable for medical images ([PMC10161187](https://pmc.ncbi.nlm.nih.gov/articles/PMC10161187/), 2023). That is a convention, not a clinical test.
  - In a 2026 study, 3 radiologists picked out the watermarked images only 51.3% of the time (chance), and their diagnostic confidence did not change ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2590005626002213), May 2026; I only saw excerpts).
  - An older study found radiologists' diagnoses unchanged ([Zain et al.](https://pubmed.ncbi.nlm.nih.gov/17946306/), 2006).
- **Medical watermarking research** mostly targets integrity checks and hiding patient data, not tracing leakers ([example](https://www.sciencedirect.com/science/article/pii/S2773186326000617), 2026). I found no DICOM watermark standard ([Sup 142](https://www.dicomstandard.org/News-dir/ftsup/docs/sups/sup142.pdf), 2011).
- **Server time.** A simple method takes about 40–50 ms per 512×512 slice, so about 12–15 s for a 300-slice CT per reader. Your 3-slice window would take only about 0.15 s per request (estimate scaled from the [imwatermark README](https://github.com/ShieldMnt/invisible-watermark)).

### Ethics and reporting
- Your readers are research participants, so announce the marking. EchoMark (a vendor) recommends telling people, because knowing a copy is traceable deters leaks ([EchoMark](https://www.echomark.com/post/using-invisible-forensic-watermarks-to-prevent-insider-information-leaks), 2024-07-16). Secret marking counts as withholding information. Typical ethics-board rules then require a justification and a debrief afterwards ([UNC SOP](https://research.unc.edu/human-research-ethics/standard-operating-procedures-sops/research-involving-deception-or-withholding-of-information/), 2025-04-16).
- Any stamp must stay outside the anatomy, look identical in the unaided and AI-aided reads, and be described in your methods section. STARD item 10a asks for enough detail to replicate the test ([STARD 2015](https://www.equator-network.org/wp-content/uploads/2015/03/STARD-2015-checklist.pdf)). Also check STARD-AI ([Nat Med](https://www.nature.com/articles/s41591-025-03953-8), Oct 2025).

### Cheap "who had what" tracing (no watermark science needed)
- **File fingerprint (my design suggestion).** Log a hash of every file you serve (a short code computed from the file's exact bytes). Also make each reader's files unique at the byte level, for example with a random code in the file's metadata, which leaves the pixels untouched. A file that is saved and forwarded unchanged then matches exactly one row in your log.
- **Different cases for different readers.**
  - In a fully crossed design every reader reads every case, so a leaked case points to no one.
  - In a split-plot design, groups of readers read different case sets. It reaches similar statistical power but needs more cases with verified diagnoses ([Chen et al.](https://pubmed.ncbi.nlm.nih.gov/29795776/), 2018). A leaked case then narrows suspects to one group.
  - Mathematically, this is the same problem as tracing traitors ([Meerwald & Furon](https://ieeexplore.ieee.org/document/5947280/), ICASSP 2011).

**About using Cloudflare for the stamps:** Cloudflare can draw a per-reader stamp on each image as it passes through ([docs](https://developers.cloudflare.com/images/transform-images/draw-overlays), 2026-09-02). It is free for 5,000 unique images a month, then $0.50 per 1,000 ([pricing](https://developers.cloudflare.com/images/pricing/), 2026-07-08). It offers nothing for invisible marks. Your Django server can draw the same stamp itself, and section B explains why Cloudflare fits Iran poorly.

### Unknowns (A)
- Whether any free library survives phone photos of grayscale radiographs on real monitors. You would have to test this yourself.
- How fast TrustMark and PixelSeal run on an ordinary processor; this is unpublished.
- How well per-reader marks hold up when only 2–3 readers combine their copies.
- Whether a stamp or mark changes reader accuracy or reliance on AI. No radiology study was found, and that is exactly what your studies measure.
- The full text of the 2026 study on whether radiologists can spot watermarks.
- Whether PSNR/SSIM scores miss diagnostically relevant detail; this is claimed but unsourced.
- Iranian ethics-committee disclosure rules, how enforceable the agreements are in Iran, whether Iranian courts would accept watermark evidence, and the privacy rules for logging reader identity.
- Whether the commercial vendors can serve Iranian institutions under sanctions.
- Whether the vendors' robustness claims hold up in independent tests.

### Recommendation (A)
Build in this order.
- **Workshop (Nov 2026):**
  1. A data-use agreement plus matching wording in the consent form and ethics protocol. It should say that images are individually marked, all access is logged, readers must safeguard their copies and login, and redistribution has named consequences.
  2. The access log plus a fingerprint of every file served.
  3. Server-rendered preset windows.
  4. A visible random code (a QR code or short code) burned into a thin margin strip outside the anatomy.

  Do not use invisible marks: this is 12 known people in a supervised room, and it would add an untested change to the pixels of a diagnostic study.
- **Online pilot:** everything above, plus:
  - per-account viewing limits in your app;
  - separate case sets per reader group, if the study design allows it;
  - in-house testing of VideoSeal/PixelSeal on your own radiographs: screenshots, re-saves, rescaling, crops, phone photos of typical monitors, and averaging two readers' copies;
  - a blinded "spot the marked image" test with radiologists, reporting PSNR/SSIM.

  Do not rely on invisible marks yet.
- **Later:** switch on invisible marks only if the testing passes, and spread a collusion-resistant code across each reader's images. Consider a commercial vendor only if sanctions and data-transfer rules allow it. Treat any detection as grounds for an investigation, not as proof.

## B. Cloudflare vs ArvanCloud vs no proxy

Some terms first:
- A **proxy/CDN** sits between readers and your server. Readers connect to it, it decrypts ("unlocks") the traffic, filters attacks, and passes requests on to your server.
- A **data centre** here means one of the proxy's server sites.

### Sanctions and account risk (Cloudflare)
- **Cloudflare's terms.** They bar sanctioned parties and do not name Iran. They also forbid using the service to export to countries where that is restricted, and they allow Cloudflare to close any account "for any reason or no reason" ([terms](https://www.cloudflare.com/terms/), 2025-09-12).
- **Cloudflare's stated policy.**
  - It told the US SEC that from early 2018 it limited new Iranian customers to its free services ([SEC filing](https://www.sec.gov/Archives/edgar/data/1477333/000095012319006180/filename1.htm), 2019-06-28).
  - Its 2022 blog says US licences allow some services in Iran "except for government parties" ([blog](https://blog.cloudflare.com/the-challenges-of-sanctioning-the-internet/), 2022-12-12).
- **US rules.**
  - The rules allow communication services and cloud services that support them. They exclude web hosting for commercial entities located in Iran and do not mention CDNs ([Baker McKenzie](https://sanctionsnews.bakermckenzie.com/ofac-amends-the-iranian-transactions-and-sanctions-regulations/), 2024-06-13; [OFAC FAQ 1110](https://ofac.treasury.gov/faqs/1110), 2024-05-16).
  - "Government of Iran" includes anything the state owns or controls "directly or indirectly" ([31 CFR 560.304](https://www.law.cornell.edu/cfr/text/31/560.304), accessed 2026-09-23). A public university site may fall under this. That question needs a US sanctions lawyer.
- **Cloudflare's own history.** Cloudflare reported its own past sanctions violations to OFAC in 2019 ([Lowenstein](https://www.lowenstein.com/news-insights/publications/articles/internet-businesses-are-targeted-by-ofac-for-sanctions-violations-how-to-reduce-risk-edelman-baker-contardo), 2020-09-15), so it has reason to be cautious.

### Reachability from Iran
- **No data centre in Iran.** Cloudflare has none; the nearest are in Iraq and the Gulf ([network](https://www.cloudflare.com/network/), accessed 2026-09-23). Its CEO said sanctions prevent it putting equipment in Iran ([CNN via KVIA](https://kvia.com/news/2023/01/19/cloudflare-says-white-house-asked-tech-firm-to-bypass-iran-censorship-but-us-sanctions-got-in-the-way/), 2023-01-19). An Iranian hosting guide warns that Cloudflare can slow down Iran-hosted sites for Iranian visitors ([Mihanwp](https://mihanwp.com/cloudflare/), 2026-08-09).
- **Past blocking.** Iran has blocked Cloudflare addresses before. On TCI this started 2023-01-15 and spread to other providers, making many Cloudflare-fronted sites unreachable ([net4people #214](https://github.com/net4people/bbs/issues/214), 2023-02-26).
- **Shutdown pattern: domestic stays up, foreign goes down, in both directions.** In June 2025, local sites kept working inside Iran, but Iran-hosted services were unreachable from abroad ([ISOC](https://pulse.internetsociety.org/en/blog/2026/08/when-networks-stay-up-but-services-disappear/), 2026-08-04).
- **Shutdowns in 2026.**
  - From 2026-01-08, traffic effectively dropped to zero ([Cloudflare](https://blog.cloudflare.com/iran-protests-internet-shutdown/), 2026-01-13). At first even the domestic network was cut. Partial restoration from about Jan 26 used whitelists and reached about 25% of normal traffic ([arXiv 2603.28753](https://arxiv.org/html/2603.28753v1), 2026-03-30).
  - A second shutdown ran 2026-02-28 to 2026-05-26: 87 days, with traffic well under 1% of normal ([Cloudflare](https://blog.cloudflare.com/iran-internet-partially-restored-may-2026/), 2026-05-27).
  - In April, routes from some Iranian data centres to Cloudflare were opened only briefly ([Jamaran](https://www.jamaran.news/%D8%A8%D8%AE%D8%B4-%D8%A8%D8%A7%D8%B2%D9%86%D8%B4%D8%B1-59/1706243-%D8%A8%D8%A7%D8%B2-%D8%B4%D8%AF%D9%86-%DA%A9%D9%84%D8%A7%D8%AF%D9%81%D9%84%D8%B1-%D9%85%D9%88%D9%82%D8%AA%DB%8C-%D8%A8%D9%88%D8%AF-%DA%AF%D8%B4%D8%A7%DB%8C%D8%B4%DB%8C-%D8%AF%D8%B1-%D8%A7%DB%8C%D9%86%D8%AA%D8%B1%D9%86%D8%AA-%D8%A7%DB%8C%D8%AC%D8%A7%D8%AF-%D9%86%D8%B4%D8%AF), 2026-04-22).
  - Since late May: HTTP/3 and IPv6 are blocked, UDP is disrupted, and many foreign addresses sit in a restricted "grey" state ([Al Jazeera](https://www.aljazeera.com/news/2026/5/31/iran-reinstates-some-internet-access-but-restrictions-remain-for-most), 2026-05-31).
  - Taken together, a Cloudflare-fronted site would likely have been unreachable to most Iranian readers for more than 100 days this year.
- **Universities were favoured.**
  - Academic networks made up 66.6% of the visible Iranian servers during the March partial recovery ([arXiv 2605.00187](https://arxiv.org/html/2605.00187v1), 2026-04-30).
  - Professors were among the first groups promised international access ([Iran International](https://www.iranintl.com/en/202604193717), 2026-04-19).
- **A trap for domestic hosting.** After 53 days of shutdown, dozens of Iran-hosted government sites broke because their free (Let's Encrypt) HTTPS certificates could not renew without international access ([Zoomit](https://www.zoomit.ir/tech-iran/458960-government-websites-error/), 2026-04-21).
- **Pending law.** A "Cyberspace Regulation Plan" was presented to MPs on 2026-08-26 ([RFE/RL](https://www.rferl.org/a/iran-internet-bill-restriction-access/33845516.html), 2026-09-03).

### Data residency
- **Where decryption happens.** Cloudflare decrypts traffic at its own data centre ([docs](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/), 2026-04-16). With no data centre in Iran, every image an Iranian reader views would be decrypted outside the country.
- **No Iran option.** Cloudflare's paid option to keep decryption inside one region lists Turkey, UAE and Saudi Arabia, but not Iran ([region support](https://developers.cloudflare.com/data-localization/region-support/), 2026-07-01).
- **Iranian law.**
  - A 2023 review found no specific personal-data law in Iran. The 2016 data-localization act it mentions concerns foreign messaging platforms ([Mohiqi](https://ccsenet.org/journal/index.php/jpl/article/download/0/0/48880/52677), 2023-06-06).
  - A data-protection bill was approved by the cabinet in July 2024 ([Peivast](https://peivast.com/p/202493)), and a competing parliamentary draft was registered 2024-10-21 ([Peivast](https://peivast.com/p/212052)).

### What Cloudflare does and does not protect
- **Flood attacks** (DDoS, many machines swamping your site): unlimited protection, free ([docs](https://developers.cloudflare.com/ddos-protection/about/), 2026-04-15).
- **Common hacking attempts** (a WAF, or web application firewall): the free plan has only a small rule set; full rules need Pro ([docs](https://developers.cloudflare.com/waf/managed-rules/), 2026-09-08). Pro costs about $20–25/month ([third-party](https://costbench.com/software/cdn-edge/cloudflare/), 2026).
- **Rate limits:**
  - The free plan allows one rule, counted per internet address, over a 10-second window ([docs](https://developers.cloudflare.com/waf/rate-limiting-rules/), 2026-08-25).
  - Counting per logged-in account needs the Enterprise plan.
- **Your main risk is not covered.** Cloudflare sees a logged-in reader saving or screenshotting images at human speed as normal traffic (my analysis). Only your app's limits, logs and watermarks catch that.
- **Caching adds little.** Per-reader images must be marked "private/no-store", so they are never cached ([docs](https://developers.cloudflare.com/cache/concepts/default-cache-behavior/), 2026-09-14). Only the viewer's code files would benefit.

### ArvanCloud
ArvanCloud is an Iranian CDN and cloud provider with data centres in Tehran, Isfahan, Mashhad, Tabriz and Shiraz ([CDN Planet](https://www.cdnplanet.com/cdns/arvancloud/), accessed 2026-09-23).
- **For it:** its network stayed about 99.7% visible during the March 2026 shutdown. The study calls it the only network fully exempted across both 2026 shutdowns ([arXiv 2605.00187](https://arxiv.org/html/2605.00187v1), 2026-04-30).
- **Against it:**
  - The US sanctioned it for helping build Iran's national network and agreeing to "provide interception for the government" ([Treasury](https://home.treasury.gov/news/press-releases/jy1518), 2023-06-02). Any US collaborator or funder is barred from dealing with it.
  - The EU listed it in 2022 and removed it on 2024-04-04 ([RFE/RL](https://www.rferl.org/a/iran-eu-sanctions-arvancloud-internet-censorship/32897604.html), 2024-04-05).
  - Its government cloud contract includes "lawful interception" clauses ([Radio Zamaneh](https://en.radiozamaneh.com/31799/), 2021-08-29).
  - Like Cloudflare, it would decrypt your traffic, in this case under a company named for interception.

### Unknowns (B)
- Whether Cloudflare would open or keep an account for an Iran-based person or university today, and whether paying from Iran is possible.
- Whether a TUMS/ADIR site counts as "Government of Iran" under US rules.
- Whether Cloudflare-fronted sites are reachable from ordinary Iranian connections now.
- Whether the data-protection bill has been enacted.
- Whether any Ministry of Health or ethics rule covers sending de-identified images abroad.
- Whether a site behind ArvanCloud stays reachable from abroad during shutdowns.
- ArvanCloud's prices and features; its site would not load.
- Whether Cloudflare Access is really free for up to 50 users; only third-party sites say so.
- Whether the Cloudflare account suspension reported in a [community thread](https://community.cloudflare.com/t/request-for-account-review-critical-internet-access-in-iran/884455) was reversed.
- Whether there will be a shutdown during 3–6 Nov.

### Recommendation (B)
- **Workshop (Nov 2026):** use no proxy and depend on no internet connection.
  - Run a local server on the room's own network: a laptop or mini-server plus a router.
  - Keep an offline copy of the cases and a paper fallback.
  - Install the HTTPS certificate beforehand, so nothing has to renew online during the event.
- **Online pilot:** use no foreign proxy.
  - Host inside Iran, preferably in TUMS/ADIR's own data centre, since academic networks were favoured during the 2026 shutdowns. Otherwise use a domestic hosting company.
  - Handle security yourself: HTTPS, logins, per-account limits, a server firewall, backups, and the access log plus watermarks.
  - Renew certificates early and watch their expiry dates.
  - Add a domestic CDN only if you are actually attacked. Weigh ArvanCloud's sanctions and interception issues first; Asiatech and Derak Cloud were not researched.
  - Get written ethics-committee approval for where the data is hosted and how it flows.
- **Later (international readers):** a server in Iran is not reliably reachable from abroad during shutdowns.
  - Plan a separate copy outside Iran, run by a non-Iranian partner, with its own cases and its own ethics and data-transfer approvals.
  - Cloudflare's free tier (flood protection, Turnstile, a free alternative to CAPTCHA) is reasonable for that foreign copy only.
  - Avoid ArvanCloud if any US person is involved.
  - Get a sanctions lawyer's opinion before opening any Cloudflare account tied to TUMS.