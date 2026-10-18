# Pitch deck: Payment Shield, real-time payment scam prevention on IBM LinuxONE

IBM Z Datathon 2026 · Team Databaes · Event code SSF2026

The slide text and speaker notes for our 8-slide pitch, plus one backup slide. All model metrics come from `results.json` and were measured on **synthetic data**.

---

## 1. Problem

**Payment scams trick people into sending the money themselves.**

Payment Shield: real-time payment scam prevention on IBM LinuxONE

- **£576.4m** lost to authorised push payment (APP) scams in the UK in 2025
- **248,070** APP scam cases in 2025, each one approved by the victim
- **17% → 28%:** scams that start with a call or text are 17% of cases but 28% of losses

Source: UK Finance, Annual Fraud Report 2026

**Speaker notes**

Open with a 10-second story, not a statistic: “Imagine getting a call from your bank’s fraud team. They say your account is compromised and you need to move your savings to a safe account, now.”

Then name the problem: this is an authorised push payment, or APP, scam. The bank’s security works perfectly. The customer logs in, passes every check and sends the money themselves, because someone has convinced them to.

Read the numbers and say the source out loud: in 2025, people in the UK lost £576.4 million to APP scams across 248,070 cases, according to UK Finance’s Annual Fraud Report 2026. The third figure is the link to our design: phone-led scams are only 17% of cases but 28% of the money lost. That is why Payment Shield looks at how someone is paying, such as being on a call, not just how much.

Judging angle: community value and theme fit. Under 40 seconds.

---

## 2. Who it hurts

**The cost lands on people who can least absorb it**

- **Older and isolated customers:** targeted by callers posing as the bank, the police or a family member.
- **People under financial stress:** lured by fake investments, loans and romance scams that promise a way out.
- **Small businesses:** lose whole invoices when a supplier’s bank details are quietly swapped.
- **Banks and communities:** carry reimbursement costs, call-centre load and lost trust in digital payments.

**Speaker notes**

Scams are not a victimless back-office problem. They concentrate on people who are trusting, stressed or busy. Walk the four groups quickly, one line each.

The banks point matters for the business case: in the UK, payment providers have had to reimburse most APP scam victims since October 2024. Every scam stopped saves the bank money as well as saving a person from harm, which is why a bank would actually deploy this.

Judging angle: community value. About 30 seconds.

---

## 3. Solution

**Score every payment before the money moves**

- **Low risk → Approve:** the payment goes straight through and the customer sees “Payment approved”.
- **High risk → Pause and explain:** the app stops and shows a risk score and why, such as a new payee while someone is on the phone.
- **Customer decides → Confirm or cancel:** the customer stays in control of their own money, with a moment to think.

Every score, reason and decision goes into an audit log, so analysts can see exactly what happened.

**Speaker notes**

One sentence pitch: Payment Shield scores every outgoing payment in real time, in the moment between the customer pressing pay and the money leaving, and pauses only the risky ones.

It combines a machine-learning model with transparent safety rules. It looks beyond the amount, at how the person is paying: are they on a call, did they paste the payee details, is this a payee added minutes ago, have they switched device?

Why pause instead of block: blocking annoys genuine customers, and scam victims are often coached to push through. A pause with specific reasons is the moment that breaks the scammer’s spell. The customer still decides, so we add a speed bump, not a wall.

The audit log matters for banks and regulators: every score, every reason shown and every confirm or cancel is recorded, so decisions can be reviewed and the data can later improve the model.

If the judges push on what is new: banks already show generic scam warnings that customers click through. We score behavioural signals - being on a call, pasted payee details, hesitation, a payee added minutes ago - inside the payment path, in under a millisecond per decision (median 0.46 ms, measured on our LinuxONE server), so the check happens before the money moves. We pause and explain rather than block, the customer decides, and the audit log records everything. That is a targeted intervention at the moment the scam is happening, not another warning banner. All results are on synthetic data.

Judging angle: novelty. About 40 seconds.

---

## 4. Demo

**Three payments, one audit trail**

| Payment | What the system sees | Outcome |
|---|---|---|
| £650 rent to the usual landlord | Known payee, usual amount, daytime | Payment approved |
| £2,400 to a new “safe account” | New payee, pasted details, on a call, nearly 4× usual | Paused with reasons, customer cancels |
| £600 to a long-standing payee | Six times the usual amount, while on a call | Paused, customer confirms |

Then open the audit log · Backup: the recorded demo video

**Speaker notes**

Run the live demo, about 90 seconds. It follows the same story as the video.

1. “This is Priya paying her landlord £650 rent, like every month.” Known payee, usual amount. Press Review payment: “Payment approved”.
2. “Now Priya gets a call from someone claiming to be her bank’s fraud team, telling her to move £2,400 to a safe account.” Tick New recipient, Recipient details pasted and Someone is on the phone. The pause screen shows the risk score and the reasons. Read one out loud, then press Cancel this payment.
3. “Not every pause is a scam.” Pay £600 to a long-standing payee with a usual payment of £100, while on a call. It pauses, because a large payment during a call is a classic coercion pattern. Press Confirm and send anyway.
4. Open the audit log: all three payments are there with score, decision, reason and the customer’s final choice.

Have the recorded video ready in case the VM or Wi-Fi fails.

Judging angle: execution.

---

## 5. Architecture

**Scoring that sits inside the payment path**

Payment in → Features → Rules + ML → Explanation → Human confirm

- **Payment in:** payment form posts to `POST /assess` on FastAPI, port 8000
- **Features:** amount vs usual, new payee and its age, hour, device change, hesitation, pasted payee, on call
- **Rules + ML:** gradient boosting model and red-flag rules, blended into a 0–100 score
- **Explanation:** top 3 reasons, ranked by feature importance, in plain English
- **Human confirm:** under 55 approved; 55 and over paused for Confirm or Cancel

Every score, reason and choice is written to a SQLite audit log, shown at `/audit` · all running on a LinuxONE VM

**Speaker notes**

Walk left to right, following one payment. This matches the diagram in `docs/ARCHITECTURE.md`.

1. The payment form, served by our FastAPI app on port 8000, posts the payment to `POST /assess`.
2. We turn the payment into ten signals, including the amount compared with the customer’s usual payment, whether the payee is new and how long ago it was added, the hour, a device change, hesitation time, pasted payee details and whether they’re on a call.
3. A scikit-learn gradient boosting model gives a scam probability, and transparent rules add points for known red flags. They are blended 70% model, 30% rules, and a large payment made during a call always scores at least 70.
4. The rules that fired, ranked by the model’s feature importance, become up to three plain-English reasons.
5. A score under 55 is approved; 55 or more pauses the payment and the customer confirms or cancels.

Every assessment and the customer’s final choice are stored in SQLite and shown on the audit page.

Judging angle: technical design with LinuxONE and AI. About 45 seconds.

---

## 6. IBM Z usage

**Why this belongs on LinuxONE**

- **Built and run on LinuxONE:** model trained and the FastAPI app served on our IBM LinuxONE server (s390x), with Python, scikit-learn and SQLite.
- **Scoring inside the payment:** each model decision takes 0.46 ms (median) on our LinuxONE server, so scoring fits inside the payment.
- **Data stays on the platform:** training data, model and audit log never leave the LinuxONE server.
- **Where payments already run:** many banks run core payments on IBM Z, so scoring next to the transaction data is the realistic path.

**Speaker notes**

Lead with proof: everything was built and run on our LinuxONE server. Point to the evidence: the SSH session, `uname -m` showing s390x, the training output and `results.json`, the app running on port 8000. The latency was measured on the server itself: 2,000 single-payment model calls, median 0.46 ms, p99 0.61 ms.

Then why it fits: scam prevention has to happen inside the payment, so the scoring has to sit next to the payment system, and many banks already process core payments on IBM Z.

Be precise: we ran the model on the server’s CPUs. The on-chip AI accelerator, Secure Execution and crypto cards are next steps for production, not things we used today.

Judging angle: technical design with LinuxONE and AI. About 40 seconds.

---

## 7. Results

**What the prototype achieved** (synthetic data)

- **97%** of scam payments caught (recall 0.97): 291 of 300
- **92.4%** of flagged payments were real scams (precision 0.9238)
- **24** false alarms out of 9,700 genuine payments
- **0.61 ms** p99 time per model decision on LinuxONE (median 0.46 ms)

Rules alone caught **72.3%** of scams. The model catches **97%** on the same test set.

Synthetic data: 50,000 payments, 3% scams · 10,000 held-out test payments · scikit-learn gradient boosting · from `results.json`

| Approach (synthetic test set) | Precision | Recall | F1 (scam class) |
|---|---:|---:|---:|
| Gradient boosting model | 0.9238 | 0.9700 | 0.9463 |
| Rules-only baseline | 0.9819 | 0.7233 | 0.8330 |

**Speaker notes**

Lead with the comparison, then the detail. Every number comes from `results.json`, measured on synthetic data.

- Recall, 97%: of the 300 scam payments in the held-out synthetic test set, the model caught 291 and missed 9.
- Precision, 92.4%: of the payments it flagged, 92 in every 100 were real scams.
- 24 false alarms: out of 9,700 genuine test payments, only 24 were wrongly flagged, about 1 in 400.
- 0.61 ms: the p99 time for a single model decision, measured over 2,000 calls on our LinuxONE server. The median was 0.46 ms.

The baseline: on the same test set, our transparent rules alone caught 72.3% of scams. The rules were slightly more precise (98.2%) but missed over a quarter of scams, which is why we combine them: the model finds the combinations, and the rules keep it explainable.

Say the honest part out loud: the data is synthetic and the scam patterns are our assumptions, so these numbers prove the system works end to end, not how it would perform on a real bank’s payments.

Judging angle: execution. About 40 seconds.

---

## 8. Impact and next steps

**Fewer victims, and a clear path to a pilot**

Impact
- 97 in every 100 scam payments paused in our synthetic test
- Only 24 of 9,700 genuine test payments paused, so real customers rarely wait
- Warnings that teach customers to spot the next scam

Next steps
- Test on real, anonymised payment data with a bank or fintech partner
- Retrain on confirm and cancel choices from the audit log
- Run inference on IBM Z’s on-chip AI accelerator at production volume

Thank you · Payment Shield by Team Databaes
github.com/36taransingh5-dotcom/ibm-z-datathon-2026-databaes · SSF2026

**Speaker notes**

Close on people, then on what happens next. In our synthetic test of 10,000 payments, the model caught 291 of the 300 scams and paused only 24 of the 9,700 genuine payments, about 1 in 400. Rules alone would have let 83 of those scams through. Say clearly that this is synthetic data.

Next steps, in order: validate on real anonymised data with a partner; use every confirm and cancel in the audit log as a training label; move inference onto IBM Z’s on-chip AI accelerator for production volume.

End with: “Payment Shield stops the payment before the scammer gets the money. Thank you.” Then open for questions.

Judging angle: community value, plus execution and pitch. About 30 seconds.

---

## 9. Backup: how the model decides

**How the model decides** (synthetic data)

![Confusion matrix on the synthetic test set](../evidence/confusion_matrix.png)

![Gradient boosting feature importance on synthetic data](../evidence/feature_importance.png)

Both plots from `generate_and_train.py` on the 10,000-payment synthetic test set.

**Speaker notes**

Show this only if judges ask how the model works or how it fails.

The confusion matrix: 9,676 genuine payments correctly approved, 24 genuine payments wrongly flagged, 291 scams caught and 9 missed.

Feature importance: the model leans most on how recently the payee was added, whether the customer is on a phone call, how long they hesitated while typing, and how the amount compares with their usual payment. That matches how real APP scams work: a scammer on the phone talking someone into paying a brand-new payee. Raw amount on its own barely matters, which is why a big but normal payment doesn’t get paused.

These come from synthetic data, so they reflect the patterns we built in, not a real bank’s data.

