# Pitch deck: real-time payment scam prevention on IBM LinuxONE

IBM Z Datathon 2026 · Team Databaes

Anything in [brackets] is a placeholder to fill in before presenting.

---

## 1. Problem

**Payment scams trick people into sending the money themselves.**

[Project name]: real-time payment scam prevention on IBM LinuxONE

- **[£___m]** lost to authorised push payment (APP) scams in the UK in [year]
- **[___k]** APP scam cases reported in [year], each one approved by the victim
- **Seconds** is all an instant payment takes to leave, and it rarely comes back

**Speaker notes**

Open with a 10-second story, not a statistic: “Imagine getting a call from your bank’s fraud team. They say your account is compromised and you need to move your savings to a safe account, now.” [Replace with a real, cited case if you have one.]

Then name the problem: this is an authorised push payment, or APP, scam. The bank’s security works perfectly. The customer logs in, passes every check and sends the money themselves, because someone has convinced them to.

Fill the two figures from a cited source (UK Finance’s annual fraud report is the usual one) and say the source out loud. The third point is the key one for this project: instant payments settle in seconds, so prevention has to happen before the money moves, not after.

Judging angle: community value and theme fit. Under 40 seconds.

---

## 2. Who it hurts

**The cost lands on people who can least absorb it**

- **Older and isolated customers:** targeted by callers posing as the bank, the police or a family member.
- **People under financial stress:** lured by fake investments, loans and romance scams that promise a way out.
- **Small businesses:** lose whole invoices when a supplier’s bank details are quietly swapped.
- **Banks and communities:** carry reimbursement costs, call-centre load and lost trust in digital payments.

**Speaker notes**

Scams are not a victimless back-office problem. They concentrate on people who are trusting, stressed or busy. Walk the four cards quickly, one line each. If you have a real anonymised quote or story, use it on one card.

The banks card matters for the business case: in the UK, payment providers have had to reimburse most APP scam victims since October 2024 [check the current rules and limit before presenting]. Every scam stopped saves the bank money as well as saving a person from harm, which is why a bank would actually deploy this.

Judging angle: community value. About 30 seconds.

---

## 3. Solution

**Score every payment before the money moves**

- **Low risk → Send:** the payment goes straight through and the customer sees “Sent”.
- **High risk → Pause and explain:** the app stops and shows why in plain English, such as a new payee and an unusually large amount.
- **Customer decides → Confirm or cancel:** the customer stays in control of their own money, with a moment to think.

Every score, reason and decision goes into an audit log, so analysts can see exactly what happened.

**Speaker notes**

One sentence pitch: [Project name] scores every outgoing payment in real time, in the moment between the customer pressing Send and the money leaving, and pauses only the risky ones.

Why pause instead of block: blocking annoys genuine customers, and scam victims are often coached to push through. A pause with specific reasons, like “you’ve never paid this person before and this is far more than you usually send,” is the moment that breaks the scammer’s spell. The customer still decides, so we add a speed bump, not a wall.

The audit log matters for banks and regulators: every score, every reason shown and every confirm or cancel is recorded, so decisions can be reviewed and the data can later improve the model.

Judging angle: novelty. Prevention before the payment leaves, with explainable friction and a human in the loop, not after-the-fact fraud detection. About 40 seconds.

---

## 4. Demo

**Three payments, one audit trail**

| Payment | What the model sees | Outcome |
|---|---|---|
| £650 rent to the usual landlord | Known payee, normal amount | “Sent” in [__] ms |
| £4,800 to a new “safe account” | New payee, amount far above usual | Paused with reasons, customer cancels |
| £[___] to a new tradesperson | New payee, [moderate] amount | Paused, customer confirms |

Then open the audit log view · Backup recording: [link or QR code]

**Speaker notes**

Run the live demo here, about 90 seconds, using the payment screen against POST /score.

1. “Here’s Sam paying rent to the same landlord as every month.” Leave New payee off and send. It shows “Sent”. Point out the speed: [__] ms.
2. “Now Sam gets a call from ‘the bank’ telling them to move £4,800 to a safe account.” Turn New payee on and send. The pause screen appears with the risk score and plain-English reasons. Read one reason out loud, then press Cancel.
3. “Not every new payee is a scam.” Pay a new tradesperson. If it pauses, press Confirm and it goes through. Pick an amount you’ve tested and know gives the outcome you want.
4. Open the audit log view: all three payments are there with score, decision, reasons and the customer’s choice.

Rehearse with the real model loaded so the outcomes match the table. Have the backup recording ready in case the VM or Wi-Fi fails.

Judging angle: execution.

---

## 5. Architecture

**Scoring that sits inside the payment path**

Payment in → Features → ML scoring → Explanation → Human confirm

- **Payment in:** payment screen sends amount and payee to POST /score (FastAPI)
- **Features:** amount, new-payee flag and [other features] built from the request
- **ML scoring:** trained model (model.pkl) gives a risk score and decision
- **Explanation:** top risk factors turned into plain-English reasons
- **Human confirm:** low risk is sent; high risk waits for Confirm or Cancel

Every score, reason and choice is written to a SQLite audit log, served by GET /audit · all running on a LinuxONE VM

**Speaker notes**

Walk left to right, following one payment. This slide should match the Mermaid diagram in the architecture write-up exactly.

1. Payment in: the single-page payment screen (plain HTML and JavaScript) posts the payment as JSON to POST /score on the FastAPI backend.
2. Features: [list the real features].
3. ML scoring: the trained model, loaded from model.pkl, returns a risk score and a decision. Before the model existed we used a rule-based placeholder scorer, which also serves as our baseline on the results slide. Say which model type you trained and why.
4. Explanation: the biggest risk factors become sentences a customer understands.
5. Human confirm: low-risk payments show “Sent”; high-risk ones show the pause screen and the customer confirms or cancels.

Every request, score, reason and decision is stored in SQLite and visible through GET /audit and the audit log view. Everything runs on our LinuxONE VM.

Judging angle: technical design with LinuxONE and AI. About 45 seconds.

---

## 6. IBM Z usage

**Why this belongs on LinuxONE**

- **Built and run on LinuxONE:** model trained and the FastAPI app served on our LinuxONE VM (s390x), with Python, [scikit-learn] and SQLite.
- **AI inference in the transaction path:** scoring happens inside the payment request. In production it can use the on-chip Integrated Accelerator for AI.
- **Payment data stays put:** banks can score payments where the data already lives, under IBM Z’s pervasive encryption.
- **Built for transaction volume:** the platform banks already run high-volume, always-on payment workloads on.

**Speaker notes**

Lead with proof, then the production argument.

Proof first: everything was built and run on our LinuxONE VM. Point to the evidence screenshots: the SSH session, uname -a showing s390x, model training output, evaluation metrics, the app running and its resource use.

Then the production story: scam prevention has to happen inside the payment, before the money leaves. LinuxONE’s Telum processors include an on-chip AI accelerator designed for in-transaction inference. Be honest that in the datathon we ran the model on [CPU on the VM], and that the accelerator is the path to production scale.

Judging angle: technical design with LinuxONE and AI. About 40 seconds.

---

## 7. Results

**What the prototype achieved**

- **[__] ms** p99 scoring time per payment
- **[__]%** of scam payments caught (recall)
- **[__]%** of genuine payments flagged (false positives)
- **[__] MB** memory used by the running app on LinuxONE

Against our rule-based placeholder scorer: **[__]% more scams caught** at the same false-positive rate.

Tested on [dataset name] · [__] transactions, [__]% labelled as scams · LinuxONE VM [cores / memory]

**Speaker notes**

Lead with the number you’re proudest of, then give context.

- Latency: the customer is waiting on the Send button. Quote p99, not the average. Time a batch of requests to POST /score on the VM.
- Recall: share of scam payments caught on the held-out test set.
- False positives: share of genuine payments that were paused. Banks care most about this one.
- Memory: from the resource-use screenshot on the VM.

Every number should match a screenshot in the evidence checklist. For the baseline, run the same test set through the rule-based placeholder scorer and compare. If the data is synthetic, say so and explain how scams were labelled.

Judging angle: execution. About 40 seconds.

---

## 8. Impact and next steps

**Fewer victims, and a clear path to a pilot**

Impact
- [__] scams stopped per [100,000] payments in our test
- An estimated [£__] in losses prevented at a mid-sized bank’s volume
- Warnings that teach customers to spot the next scam

Next steps
- Test on real, anonymised payment data with a [bank or fintech partner]
- Retrain on confirm and cancel choices from the audit log
- Run on the Integrated Accelerator for AI at production volume

Thank you · Databaes · [repo link]

**Speaker notes**

Turn your results into one human number, for example “at our recall, a bank processing [__] payments a day would stop about [__] scams a day.” Don’t inflate it.

Next steps, in order of how soon they could happen: validate on real anonymised data with a partner; close the loop by using every confirm and cancel in the audit log as a training label; benchmark on LinuxONE’s AI accelerator at production volume.

End with: “[Project name] stops the payment before the scammer gets the money. Thank you.” Then open for questions.

Total talk: roughly 5 to 6 minutes including the demo; trim to the datathon’s time limit [check the submission rules].
