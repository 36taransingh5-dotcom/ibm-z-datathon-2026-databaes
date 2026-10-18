# Demo Video Script: Real-Time Payment Scam Prevention

IBM Z Datathon 2026 · event code SSF2026 · Team Databaes

## Overview

The video runs 2:50, leaving a 10-second buffer under the 3:00 limit. It follows one person, Priya, through a normal payment and then a scam payment, so judges see both outcomes in one story.

| Beat | Time | Length | Goal |
| --- | --- | --- | --- |
| 1. Problem | 0:00–0:25 | 25s | Make judges feel the harm of payment scams |
| 2. Solution | 0:25–0:43 | 18s | Explain what the system does in one breath |
| 3. Live demo | 0:43–2:05 | 82s | Legit payment goes through, scam payment is paused, audit log |
| 4. LinuxONE and metrics | 2:05–2:33 | 28s | Prove it runs on IBM Z and show the numbers |
| 5. Impact | 2:33–2:50 | 17s | Close on who this protects |

Narration is paced at about 150 words per minute. Read it aloud with a stopwatch before recording; if a beat runs long, cut words rather than speeding up.

**Before recording:** the metrics below (recall 97.0%, precision 92.4%, macro-F1 0.972) come from `results.json`. Re-run training on the LinuxONE VM and update them if they change.

**Rule for every metrics shot:** the words "Synthetic data" must be visible on screen whenever any metric is shown.

## Script

### Beat 1: Problem (0:00–0:25)

**Narration:** "In 2025, people in the UK lost £576.4 million to authorised push payment scams across 248,070 cases. The scammer doesn't hack the bank. They phone you, pretending to be your bank or the police, and talk you into sending the money yourself. Scams that start with a call or text are 17% of cases, but 28% of the money lost."

**On screen:** "£576.4m" in large text with "across 248,070 cases in 2025" underneath and the source: UK Finance, Annual Fraud Report 2026. Then a phone showing an incoming call labelled "Bank Fraud Team", with "17% of cases · 28% of losses" beside it.

### Beat 2: Solution (0:25–0:43)

**Narration:** "Payment Shield checks every payment before the money leaves. It looks beyond the amount, at how you're paying. Are you on a call? Did you paste the payee details? Normal payments go straight through. Risky ones pause, with a plain-English reason and a choice."

**On screen:** A simple animated flow: Payment → Risk score → Approved, or Paused → Confirm or Cancel. Team name and project title in the corner.

### Beat 3: Live demo (0:43–2:05)

**Scene A, legit payment (0:43–1:05)**

**Narration:** "This is Priya paying her landlord £650 rent, like every month. Known payee, usual amount, nothing unusual. Low risk, so it goes straight through. No friction for real payments."

**On screen:** Payment form filled with £650 and a saved payee. Click Review payment. The "Payment approved" screen appears.

**Scene B, scam payment (1:05–1:50)**

**Narration:** "Now Priya gets a call from someone claiming to be her bank's fraud team. They say her account is compromised and she must move £2,400 to a safe account. It's a new payee, she pastes the details they read out, she's still on the call, and it's nearly four times her usual payment. Instead of a generic warning she'd click past, she sees exactly why we've paused it. Real banks never ask you to move money to a safe account. Priya cancels. Her money stays put."

**On screen:** Form with £2,400, new recipient on, recipient details pasted, on-call on. Click Review payment. The paused screen appears; hold on it so the reasons are readable. Click Cancel and show the cancelled confirmation.

**Scene C, audit log (1:50–2:05)**

**Narration:** "Every decision is logged with its risk score and reasons, so a bank can review cases and keep improving the model."

**On screen:** Audit log page showing both payments with time, score, decision and reasons.

### Beat 4: LinuxONE and metrics (2:05–2:33)

**Narration:** "Everything you've just seen runs on IBM LinuxONE. We trained a gradient boosting model on 50,000 synthetic payments. On a 10,000-payment test set, it caught 97% of scams with 92% precision, fast enough to sit inside a real payment flow."

**On screen:** Terminal with the SSH session to the LinuxONE VM, then `uname -m` showing s390x and the app running. Then results.json with recall, precision and macro-F1 highlighted and a "Synthetic data" label visible the whole time the numbers are on screen.

### Beat 5: Impact (2:33–2:50)

**Narration:** "Scams don't just take money. They take people's confidence. Payment Shield steps in at the one moment a scam can still be stopped, without slowing down the payments that are real. Databaes, IBM Z Datathon 2026."

**On screen:** "Scams don't just take money. They take confidence." Then the end card: project name, team name, team members, GitHub link, event code SSF2026, "All payment data is synthetic".

## Shot list

| # | Time | Shot | Must be on screen | Source |
| --- | --- | --- | --- | --- |
| 1 | 0:00–0:14 | Stat card | £576.4m, 248,070 cases, source: UK Finance Annual Fraud Report 2026 | Title card |
| 2 | 0:14–0:25 | Incoming call | Phone screen, caller "Bank Fraud Team", "17% of cases · 28% of losses" | Title card |
| 3 | 0:25–0:43 | Solution flow | Payment → score → Approved or Paused → Confirm/Cancel | Animated card |
| 4 | 0:43–0:58 | Legit payment form | £650, saved payee, Review payment button | App screen recording |
| 5 | 0:58–1:05 | Approved screen | "Payment approved" confirmation | App screen recording |
| 6 | 1:05–1:25 | Scam payment form | £2,400, new recipient, details pasted, on-call on | App screen recording |
| 7 | 1:25–1:42 | Paused screen | Risk reasons readable, Cancel and Confirm buttons | App screen recording |
| 8 | 1:42–1:50 | Cancelled | Cancelled confirmation | App screen recording |
| 9 | 1:50–2:05 | Audit log | Both payments, score, decision, reasons | App screen recording |
| 10 | 2:05–2:13 | SSH session | Prompt showing the LinuxONE VM, `uname -m` = s390x | Terminal recording on VM |
| 11 | 2:13–2:20 | App running | Server running on port 8000 on the VM | Terminal recording on VM |
| 12 | 2:20–2:33 | Metrics | Recall, precision, macro-F1 from results.json + "Synthetic data" label | Terminal recording on VM or metrics card |
| 13 | 2:33–2:50 | Impact and end card | Closing line, then project, team, GitHub link, SSF2026, "All payment data is synthetic" | Title card |

## Recording checklist

Record the screen shots and the narration separately, then line them up in an editor; it is far easier than getting both right in one take.

- [ ] Re-run training on the VM and confirm the metrics match the script
- [ ] Rehearse the narration with a stopwatch; each beat within its time
- [ ] Record the screen at 1080p (OBS Studio is free) with browser zoom at 125% so text is readable
- [ ] Clear browser tabs, bookmarks bar and notifications before recording
- [ ] Run the scam scenario a few times first to confirm the reasons it shows match the narration
- [ ] Use a terminal font size of at least 18 for the VM shots
- [ ] Record narration in a quiet room with a headset mic, not the laptop mic
- [ ] Add captions for the narration; judges may watch without sound
- [ ] "Synthetic data" visible on screen whenever any metric appears
- [ ] Export and check the final length is under 3:00 before submitting

## Voiceover (clean read)

| Time | Scene | Voiceover |
| --- | --- | --- |
| 0:00–0:25 | Problem | In 2025, people in the UK lost £576.4 million to authorised push payment scams across 248,070 cases. The scammer doesn't hack the bank. They phone you, pretending to be your bank or the police, and talk you into sending the money yourself. Scams that start with a call or text are 17% of cases, but 28% of the money lost. |
| 0:25–0:43 | Solution | Payment Shield checks every payment before the money leaves. It looks beyond the amount, at how you're paying. Are you on a call? Did you paste the payee details? Normal payments go straight through. Risky ones pause, with a plain-English reason and a choice. |
| 0:43–1:05 | Demo: everyday payment | This is Priya paying her landlord £650 rent, like every month. Known payee, usual amount, nothing unusual. Low risk, so it goes straight through. No friction for real payments. |
| 1:05–1:50 | Demo: scam payment | Now Priya gets a call from someone claiming to be her bank's fraud team. They say her account is compromised and she must move £2,400 to a safe account. It's a new payee, she pastes the details they read out, she's still on the call, and it's nearly four times her usual payment. Instead of a generic warning she'd click past, she sees exactly why we've paused it. Real banks never ask you to move money to a safe account. Priya cancels. Her money stays put. |
| 1:50–2:05 | Demo: audit log | Every decision is logged with its risk score and reasons, so a bank can review cases and keep improving the model. |
| 2:05–2:33 | LinuxONE and metrics | Everything you've just seen runs on IBM LinuxONE. We trained a gradient boosting model on 50,000 synthetic payments. On a 10,000-payment test set, it caught 97% of scams with 92% precision, fast enough to sit inside a real payment flow. |
| 2:33–2:50 | Impact | Scams don't just take money. They take people's confidence. Payment Shield steps in at the one moment a scam can still be stopped, without slowing down the payments that are real. Databaes, IBM Z Datathon 2026. |
