📦 Installation Guide: Analytics Tracker

Target Environment: Linux Container (LXC/LXD) or VPS
Recommended OS: Ubuntu 24.04 LTS

1. System Requirements

Ensure you are logged in as root or a user with sudo privileges.

Update System

apt update && apt upgrade -y


Install Essential Tools

apt install -y curl git python3 python3-pip python3-venv


2. Install Node.js (v20 LTS)

The project requires a modern Node.js version for the WhatsApp Multi-Device protocol.

# Add NodeSource repository
curl -fsSL [https://deb.nodesource.com/setup_20.x](https://deb.nodesource.com/setup_20.x) | bash -

# Install Node.js
apt install -y nodejs

# Verify installation (Should be v20+)
node -v
npm -v


3. Project Setup

Create a dedicated directory for the application to keep things organized.

# Create directory
mkdir -p /opt/analytics-tracker
cd /opt/analytics-tracker

# Clone your repository (or copy files manually)
# git clone https://github.com/ekinox-ux/Whatsapp-Tracker.git


Ensure the following files are present:

backend_server.py

probe_worker.ts

dashboard.html

package.json

requirements.txt

ecosystem.config.js

4. Backend Setup (Python)

We use a virtual environment (venv) to isolate Python dependencies.

# 1. Create virtual environment
python3 -m venv venv

# 2. Install dependencies
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt


5. Probe Setup (Node.js)

Install the required Node.js packages and the Process Manager (PM2).

# 1. Install project dependencies
npm install

# 2. Install PM2 globaly
npm install -g pm2


6. PM2 Configuration

PM2 acts as the orchestrator. It ensures both the Python backend and the Node.js probe run simultaneously and restart automatically if they crash.

Check your ecosystem.config.js. It must point to the virtual environment Python interpreter:

// Inside ecosystem.config.js
interpreter: "./venv/bin/python",


7. Start & Pair

Start the Services

pm2 start ecosystem.config.js


Enable Startup on Boot

To ensure the tracker restarts after a server reboot:

pm2 save
pm2 startup
# Run the command displayed by the output of 'pm2 startup'


Link WhatsApp Account

Monitor the logs to see the pairing code:

pm2 logs NODE-WORKER


You will see a message: >>> QR CODE ON DASHBOARD.

Open the Dashboard in your browser:

URL: http://<YOUR_SERVER_IP>:5001

Open WhatsApp on your phone → Linked Devices → Link a Device.

Scan the QR Code displayed on the dashboard.

8. Maintenance

View Status

Check if services are online:

pm2 status


View Real-time Logs

See ping operations and detections live:

pm2 monit


Update Application

If you modify the code, apply changes with:

pm2 restart all


🛡️ Firewall Configuration (UFW)

If you are using a firewall (UFW), allow traffic on port 5001:

ufw allow 5001/tcp
ufw reload
