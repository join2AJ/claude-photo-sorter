# Putting the sharing app online: options and costs

Prices checked in November 2026 from public price lists and comparison sites. They change, so confirm on each provider's page before paying. ₹ figures are approximate.

## What has to be online

The sharing app needs HTTPS, so phones trust it and can use the camera, and an SMS service for the 6-digit codes. Photos are blurred where the originals are, so the app must run either on your computer (reached through a tunnel) or on a server holding the photos.

## Where the app runs

| Option | Monthly cost | Good for | Catch |
|---|---|---|---|
| **Your computer + Cloudflare Tunnel** | ₹0 (free plan, Access free up to 50 users) | A pilot: one event, family, first customers | Your computer must stay on and online; home upload speed limits photo loading |
| **DigitalOcean, Bangalore** (4 GB, 2 vCPU) | about $24 (≈ ₹2,700 with GST), backups +20% | The real service, data in India | You look after the server; photo storage costs extra |
| **AWS Lightsail, Mumbai** (4 GB) | about $24 (2 GB ≈ $12) | The same, on AWS | Less data transfer included in Mumbai than in the US |
| Hetzner (EU) | about €4.5 | Cheapest | Data outside India: ask your lawyer first |

## SMS codes

| Provider | Per code | Setup | Notes |
|---|---|---|---|
| **Firebase phone sign-in** | about $0.07 (≈ ₹6); first 10 a day free | No DLT registration, needs a billing account | Easiest to start |
| **MSG91** | about ₹0.15–0.25 + 18% GST | DLT registration in India: one-time fee around ₹5,000–5,900, 1–3 weeks | Cheapest at scale |
| Twilio Verify | about $0.13 (≈ ₹11) | Needs DLT for India | Most expensive here |

Example, 1,000 sign-ins a month: MSG91 ≈ ₹300; Firebase ≈ ₹4,000 (after the free 300); Twilio ≈ ₹11,000.

## Recommended path

1. **Pilot (≈ ₹0 a month):** Cloudflare Tunnel from your computer, plus Firebase phone sign-in (free for the first 10 codes a day). Use it at one real event.
2. **Paid service:** a 4 GB server in India (DigitalOcean Bangalore or AWS Mumbai, ≈ ₹2,000–2,700 a month), plus MSG91 once DLT registration is done, plus a domain name.
3. Before either: the lawyer review in `legal-checklist.md`.
