# Demo Video Script: Real-Time Payment Scam Prevention

IBM Z Datathon 2026 · event code SSF2026

## Overview

The video runs 2:52, leaving an 8-second buffer under the 3:00 limit. It follows one person, Priya, through a normal payment and then a scam payment, so judges see both outcomes in one story.

| Beat | Time | Length | Goal |
| --- | --- | --- | --- |
| 1. Problem | 0:00–0:20 | 20s | Make judges feel the harm of payment scams |
| 2. Solution | 0:20–0:40 | 20s | Explain what the system does in one breath |
| 3. Live demo | 0:40–2:05 | 85s | Legit payment goes through, scam payment is paused, audit log |
| 4. LinuxONE and metrics | 2:05–2:35 | 30s | Prove it runs on IBM Z and show the numbers |
| 5. Impact | 2:35–2:52 | 17s | Close on who this protects |

Narration is paced at about 150 words per minute. Read it aloud with a stopwatch before recording; if a beat runs long, cut words rather than speeding up.

**Placeholders to fill before recording:**

- [TEAM NAME]
- [PRECISION], [RECALL], [MACRO-F1] and [MS PER DECISION] from results.json, measured on the LinuxONE VM

## Script

### Beat 1: Problem (0:00–0:20)

**Narration:** "In 2025, people in the UK lost £576.4 million to authorised push payment scams, across 248,070 cases. The scammer doesn't hack the bank. They phone you, pretending to be your bank or the police, and talk you into sending the money yourself. Scams that start with a call or text are 17% of cases, but 28% of the money lost."

**On screen:** Black background, "£576.4m" in large text with "248,070 cases in 2025" underneath and the source: UK Finance, Annual Fraud Report 2026. Then a phone showing an incoming call labelled "Bank Fraud Team", with "17% of cases · 28% of losses" beside it.

### Beat 2: Solution (0:20–0:40)

**Narration:** "We built a system that checks every payment in milliseconds, before the money leaves. It looks beyond the amount, at how you're paying. Are you on a call? Did you paste the payee details? Normal payments go straight through. Risky ones pause, with a plain-English reason and a choice."

**On screen:** A simple animated flow: Payment → Risk score → Sent, or Pause → Confirm or Cancel. Team name and project title in the corner.

### Beat 3: Live demo (0:40–2:05)

**Scene A, legit payment (0:40–1:05)**

**Narration:** "This is Priya paying her landlord £650 rent, like every month. Known payee, usual amount, nothing unusual. Low risk, so it goes straight through. No friction for real payments."

**On screen:** Payment form filled with £650 and a saved payee. Click Review payment. The "Payment approved" screen appears.

**Scene B, scam payment (1:05–1:50)**

**Narration:** "Now Priya gets a call from someone claiming to be her bank's fraud team. They say her account is compromised and she must move £2,400 to a safe account. It's a new payee, she pastes the details they read out, she's still on the call, and it's nearly four times her usual payment. Instead of a generic warning she'd click past, she sees exactly why we've paused it. Real banks never ask you to move money to a safe account. Priya cancels. Her money stays put."

**On screen:** Form with £2,400, new payee toggle on, pasted payee, on-call flag on. Click Send. The pause screen appears; zoom in on the reasons. Click Cancel and show the "Payment cancelled" confirmation.

**Scene C, audit log (1:50–2:05)**

**Narration:** "Every decision is logged with its risk score and reasons, so a bank can review cases and keep improving the model."

**On screen:** Audit log page showing both payments with time, score, decision and reasons.

### Beat 4: LinuxONE and metrics (2:05–2:35)

**Narration:** "Everything you've just seen runs on IBM LinuxONE. We trained a gradient boosting model on 50,000 synthetic payments. It catches [RECALL] of scams with [PRECISION] precision, and scores each payment in [MS PER DECISION] milliseconds, fast enough to sit inside a real payment flow."

**On screen:** Terminal with the SSH session to the LinuxONE VM, then `uname -m` showing s390x, the app running, training output, then results.json with the metrics highlighted. Small caption: "Synthetic dataset, clearly labelled."

### Beat 5: Impact (2:35–2:52)

**Narration:** "Scams don't just take money. They take people's confidence. Our system steps in at the one moment a scam can still be stopped, without slowing down the payments that are real. [TEAM NAME], IBM Z Datathon 2026."

**On screen:** Priya's "Payment cancelled" screen fades to the end card: project name, team name, team members, GitHub link, event code SSF2026.

## Shot list

| # | Time | Shot | Must be on screen | Source |
| --- | --- | --- | --- | --- |
| 1 | 0:00–0:12 | Stat card | £576.4m, 248,070 cases, source: UK Finance Annual Fraud Report 2026 | Slide or title card |
| 2 | 0:12–0:20 | Incoming call | Phone screen, caller "Bank Fraud Team", "17% of cases · 28% of losses" | Mock-up or real phone |
| 3 | 0:20–0:40 | Solution flow | Payment → score → Sent or Pause → Confirm/Cancel | Person 4's diagram, simplified |
| 4 | 0:40–0:52 | Legit payment form | £650, saved payee, Send button | Frontend screen recording |
| 5 | 0:52–1:05 | Approved screen | "Payment approved" confirmation | Frontend screen recording |
| 6 | 1:05–1:25 | Scam payment form | £2,400, new payee on, pasted payee, on-call on | Frontend screen recording |
| 7 | 1:25–1:42 | Pause screen | Risk reasons readable (zoomed), Confirm and Cancel | Frontend screen recording |
| 8 | 1:42–1:50 | Cancelled | "Payment cancelled" confirmation | Frontend screen recording |
| 9 | 1:50–2:05 | Audit log | Both payments, score, decision, reasons | Frontend screen recording |
| 10 | 2:05–2:13 | SSH session | Prompt showing the LinuxONE VM, `uname -m` = s390x | Terminal recording on VM |
| 11 | 2:13–2:21 | App running | FastAPI server running on port 8000 on the VM | Terminal recording on VM |
| 12 | 2:21–2:35 | Metrics | results.json: precision, recall, macro-F1, ms per decision; "synthetic data" caption | Terminal recording on VM |
| 13 | 2:35–2:52 | End card | Project name, team, members, GitHub link, SSF2026 | Slide or title card |

## Recording checklist

Record the screen shots and the narration separately, then line them up in an editor; it is far easier than getting both right in one take.

- [ ] Fill in every placeholder with real numbers from results.json on the VM
- [ ] Rehearse the narration with a stopwatch; each beat within its time
- [ ] Record the screen at 1080p (OBS Studio is free) with browser zoom at 125% so text is readable
- [ ] Clear browser tabs, bookmarks bar and notifications before recording
- [ ] Pre-type the payee details so form filling is quick; speed up typing in editing if needed
- [ ] Run the scam scenario a few times first to confirm the reasons it shows match the narration
- [ ] Use a terminal font size of at least 18 for the VM shots
- [ ] Record narration in a quiet room with a headset mic, not the laptop mic
- [ ] Add captions for the narration; judges may watch without sound
- [ ] Show "synthetic dataset" on screen whenever the data or metrics appear
- [ ] Export and check the final length is under 3:00 before submitting
