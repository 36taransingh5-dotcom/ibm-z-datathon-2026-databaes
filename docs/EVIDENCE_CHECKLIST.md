# LinuxONE evidence checklist

Judges score "technical design and use of LinuxONE" partly on screenshots, so evidence is points. Tick items off as you go. Event code: SSF2026.

> **Screenshot rules**
> - Blur IPs, usernames, emails, keys, tokens and serial numbers.
> - Use a large terminal font (16pt or more) so it reads in a 1080p video.
> - Save as `evidence/NN_name.png` so the deck and video people can find them.
> - Take them as you go. Don't leave them until 08:30.

Shortcut: `./scripts/collect_evidence.sh` (from the repo root, on the VM) writes redacted text versions of items 2–6, 11, 14, 20 and 22 into `evidence/`. You still need screenshots for the deck and video.

## Platform proof

- [ ] **01 SSH session.** Terminal logged into the VM with the LinuxONE banner and prompt visible. Blur the IP and username. Save as `evidence/01_ssh_session.png`. Used in: deck slide 6, video beat 4.
- [ ] **02 Architecture.** `uname -a && uname -m` showing `s390x`. Save as `evidence/02_uname.png`. Used in: deck slide 6, video beat 4.
- [ ] **03 CPU.** `lscpu` showing architecture s390x and 3 CPUs. Save as `evidence/03_lscpu.png`. Used in: deck slide 6.
- [ ] **04 IBM machine type.** `grep -E "^(Type|Model|Manufacturer)" /proc/sysinfo`. Never screenshot the full file: it holds serial and sequence codes. Save as `evidence/04_sysinfo.png`. Used in: deck slide 6.
- [ ] **05 OS and Python.** `cat /etc/os-release && python3 --version`. Save as `evidence/05_os_python.png`. Used in: README.
- [ ] **06 Resources.** `free -h && nproc && df -h /`. Save as `evidence/06_resources.png`. Used in: deck slide 6.
- [ ] **07 Community Cloud dashboard.** The VM listed in the LinuxONE Community Cloud portal; blur account details. Save as `evidence/07_dashboard.png`. Used in: video beat 4.
- [ ] **08 Jupyter Lab.** Jupyter Lab open on the VM; URL bar visible, IP blurred. Save as `evidence/08_jupyter.png`. Used in: video beat 4.

## ML proof

- [ ] **09 Dataset.** `python3 -c "import pandas as p; d=p.read_csv('data/payments.csv'); print(len(d)); print(d.label.value_counts(normalize=True))"` showing 50,000 rows and about 3% scams; show `"synthetic": true` in `results.json` alongside. Save as `evidence/09_dataset.png`. Used in: deck slide 7, README.
- [ ] **10 Training.** `python3 generate_and_train.py` output on the VM (terminal or Jupyter cell). Save as `evidence/10_training.png`. Used in: deck slide 7, video beat 4.
- [ ] **11 Metrics.** `cat results.json`: precision, recall, macro-F1, ms per decision. Save as `evidence/11_results.png`. Used in: deck slide 7, video beat 4.
- [ ] **12 Plots.** Confusion matrix or feature-importance plot, if produced. Save as `evidence/12_plot.png`. Used in: deck slide 7.
- [ ] **13 IBM labs.** Final cell outputs of both mandatory labs (Predictive AI Hybrid; Predictive AI + Generative AI). Save as `evidence/13a_lab_hybrid.png` and `evidence/13b_lab_genai.png`. Used in: submission.

## App proof

- [ ] **14 Server running.** `uvicorn app:app --host 0.0.0.0 --port 8000` running, plus `ss -tlnp | grep 8000`. Save as `evidence/14_uvicorn.png`. Used in: deck slide 5, video beat 4.
- [ ] **15 API docs.** `http://SERVER_ADDRESS:8000/docs` (FastAPI's built-in page). Save as `evidence/15_api_docs.png`. Used in: deck slide 5.
- [ ] **16 Legit payment.** Normal payment → "PAYMENT APPROVED". Save as `evidence/16_approved.png`. Used in: deck slide 4, video beat 3.
- [ ] **17 Scam payment.** New payee, pasted details, on call, large amount → "PAYMENT PAUSED" with reasons. Save as `evidence/17_paused.png`. Used in: deck slide 4, video beat 3.
- [ ] **18 Confirm and Cancel.** Both buttons tested on paused payments. Save as `evidence/18a_confirmed.png` and `evidence/18b_cancelled.png`. Used in: deck slide 4.
- [ ] **19 Audit log.** `/audit` page showing approved, confirmed and cancelled entries. Save as `evidence/19_audit.png`. Used in: deck slide 4, video beat 3.
- [ ] **20 Request timing.** The `curl` timings for `POST /assess` from `evidence/05_api.txt`. Save as `evidence/20_timing.png`. Used in: deck slide 7.

## Resource and security

- [ ] **21 CPU in use.** `top` or `htop` while `generate_and_train.py` runs. Save as `evidence/21_top.png`. Used in: deck slide 6, video beat 4.
- [ ] **22 Containers.** `podman ps` / `docker ps` only if a container is used; otherwise note "no containers used" and skip.
- [ ] **23 Security hygiene.** `.gitignore` excludes `.venv/` and `data/audit.db`; no credentials in the repo; SSH key auth (`ls ~/.ssh`, names only, never contents). Save as `evidence/23_security.png`. Used in: README.

## Repo and submission

- [ ] **24 GitHub.** Repo page with README and commit history during event hours. Save as `evidence/24_github.png`. Used in: submission.
- [ ] **25 Diagram.** `docs/architecture.mmd` exported as PNG (paste into https://mermaid.live, export PNG, on a laptop not the VM). Save as `evidence/25_architecture.png`. Used in: deck slide 5, video beat 2.

## Hand-off

| Evidence | Person 5 (deck) | Person 6 (video) |
|---|---|---|
| 16, 17, 18, 19 | Slide 4 Demo | Beat 3, live demo |
| 14, 15, 25 | Slide 5 Architecture | Beat 2, solution |
| 01, 02, 03, 04, 06, 21 | Slide 6 IBM Z usage | Beat 4, LinuxONE and metrics (2:05–2:35) |
| 09, 10, 11, 12, 20 | Slide 7 Results | Beat 4, LinuxONE and metrics (2:05–2:35) |
| 07, 08 | Backup slide | Beat 4, LinuxONE and metrics |
