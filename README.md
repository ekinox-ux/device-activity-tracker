🕵️ ANALYTICS TRACKER (PoC)

Behavioral Analysis Tool via WhatsApp (Side-Channel Timing Attack)

⚠️ DISCLAIMER: This project is a Proof of Concept (PoC) intended solely for cybersecurity research and education. Monitoring individuals without consent is illegal.

🤝 Credits & Origins

This project is an instrumented and improved version of the original PoC by Gommzy Studio.

Original Project: Device Activity Tracker

Author: Gommzy Studio

Academic Research: Based on the paper "Careless Whisper" (Gegenhuber et al., 2024).

🔬 Scientific Concept

This project demonstrates how to extract activity metadata (Online, Idle, Offline) from a WhatsApp user without triggering a notification, by exploiting technical Delivery Receipts.

The RTT (Round Trip Time) Vulnerability

The protocol forces the target phone to acknowledge receipt of packets. The response time varies according to the device's physical state:

< 1000ms: Phone active (CPU awake, App in foreground).

1000ms - 5000ms: Phone in standby (CPU in power-saving mode).

> 5000ms: Phone off or out of network coverage.

To remain invisible, we use "Ghost Pings": reactions to non-existent messages, which are silently rejected by the target application but acknowledged by the network.

🛠 Technical Architecture

The system uses a decoupled architecture for robustness:

1. The Probe (Node.js + Baileys)

Role: Sends probes and measures raw response time.

High Precision Mode: The system sends pings at a fixed frequency of 400ms. This allows for very fine temporal resolution to capture micro-activities, at the cost of increased detection risk by servers.

2. The Brain (Python + Flask + SQLite)

Role: Receives raw data and applies advanced mathematics.

Statistical Engine (Median): Analysis relies on real-time median calculation. This stabilizes ONLINE and IDLE states by naturally filtering out network noise (one-off lags do not skew the status).

Z-Score Analysis: Statistically detects when the user unlocks their screen. If latency drops below the usual variation margin (Standard Deviation), the UNLOCKED event is triggered (experimental).

Sleep Detection: Identifies sleep cycles (inactivity > 1h).

3. The Dashboard (HTML5 + Chart.js)

Real-time visualization of smoothed curves.

Status indicators: ONLINE, IDLE, OFFLINE, UNLOCKED.

See INSTALLATION.md for the detailed guide on Ubuntu LXC.

🛡️ Limitations

This PoC uses a fixed polling frequency (400ms). This maximizes data precision but creates a detectable robotic traffic pattern, potentially leading to temporary bans of the probing number by WhatsApp.

⚠️ WARNING ! THIS POC IS LARGELY CODED WITH AI. I'M ONLY A SYSTEM AND NETWORK ADMINISTRATOR, NOT A DEVELOPER, SO FEEL FREE TO IMPROVE OR CORRECT THE CODE.
