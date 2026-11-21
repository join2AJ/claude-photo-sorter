# Before going public: questions for a privacy lawyer

The app recognises faces, links them to mobile numbers, and shares photos with blurring. That is biometric and personal data in every market. Take this list and `dashboard/share-privacy.html` (the draft notice) to a lawyer before anyone outside your own family uses it.

## What the app does today (facts for the lawyer)

- Face codes (128-number SFace embeddings) are made for **every face** in the owner's photos, to group them into people. Most of those people never signed up.
- A person signs up with a mobile number (one-time code by SMS) and a live selfie with random head turns. They tick: consent to face matching (notice version recorded) and "18+ or a guardian agrees".
- Their selfie's face code is compared with the album. New people are confirmed by the owner; a face registered to another number is blocked and the owner is alerted.
- Each viewer sees only photos they're in. Other faces are blurred on the server unless that person agreed (with optional show-to / hide-from lists). Unregistered people are always blurred.
- Optional age, gender and emotion **estimates** (can be switched off: then they are never computed).
- Retention: one-time codes ~1 hour, sign-ins 30 days, live selfies 30 days, face codes of rejected sign-ups 30 days. A person can ask to be deleted; the owner deletes their face codes, face pictures, number and sign-ups in one click. Every consent and deletion is logged with the date.
- Data is stored on the owner's computer (prototype). Going online means a server and an SMS provider (processors).

## Questions

1. **Role:** is the album owner the data controller / data fiduciary (India DPDP Act 2023), and the app maker a processor? What contract do we need with owners who pay for the app?
2. **Faces of people who never signed up:** may we make face codes for everyone in a photo to group them, without their consent? Is "household / personal use" an exemption for a family album, and does it end once the app is a paid service?
3. **Consent wording:** is the tick-box text and the notice enough for explicit consent to biometric processing (DPDP, GDPR Art. 9, Illinois BIPA if any US users)? Do we need a separate, written consent for BIPA?
4. **Children:** DPDP needs verifiable parental consent for under-18s. Is a tick box ("my parent or guardian agrees") enough, or do we need verification? Should children's faces always stay blurred?
5. **Age, gender and emotion estimates:** are they allowed? (EU AI Act bans emotion recognition at workplaces and in education; corporate events may count.) Should they be off by default, or removed from the paid product?
6. **Retention:** are 30 days for selfies and "until deleted" for face codes acceptable? What must we keep, and for how long, to prove consent?
7. **Breach:** what must we do and in how many hours if face codes or numbers leak (DPDP Board notice, GDPR 72 hours)?
8. **Where data lives:** any rule on storing Indian users' data outside India? Which server region should we choose?
9. **Grievance officer / contact:** do we need a named grievance officer and a response time?
10. **Terms of use** for album owners: they must have the right to upload the photos and to invite people; who is liable if they upload someone else's photos?
11. **Impersonation alerts:** may we tell the real person that someone tried to use their face (it reveals that their face is in the album)?
12. **Selling the product:** anything to add before charging money (consumer law, GST invoices, refund policy)?

## Already built to help

- Consent recorded per person with notice version and time (Library → Privacy → Consent record, CSV download).
- One-click deletion of a person's face data (Library → People → person → Delete their face data, or from a deletion request).
- Estimates switch (Library → Privacy).
- Automatic clean-up of codes, sign-ins and selfies.
