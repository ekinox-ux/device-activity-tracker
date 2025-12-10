📦 Analytics Tracker – Installation Guide (Ubuntu 24.04 LTS / VPS / LXC)

1. System Requirements

Make sure your system is up to date:

apt update && apt upgrade -y

Install essential tools:

apt install -y curl git python3 python3-pip python3-venv

2. Install Node.js 20 LTS

Install the official NodeSource repository:

curl -fsSL https://deb.nodesource.com/setup_20.x | bash -

apt install -y nodejs


Verify installation:

node -v
npm -v


You should see Node 20+ and npm 10+.

3. Project Setup

Create the application directory:

mkdir -p /opt/analytics-tracker
cd /opt/analytics-tracker


Clone your project (or copy files manually):

# git clone 


Required files:

backend_server.py

probe_worker.ts

dashboard.html

package.json

requirements.txt

ecosystem.config.js


4. Backend Setup (Python)

Create a virtual environment:


python3 -m venv venv


Install dependencies:

./venv/bin/pip install -r requirements.txt

5. Probe Setup (Node.js)

Install Node.js dependencies:

npm install

Install PM2 globally:

npm install -g pm2

6. PM2 Configuration

Check that your ecosystem.config.js points to the virtualenv Python:

interpreter: "./venv/bin/python",


Start the services:

pm2 start ecosystem.config.js


Enable auto-start on reboot:

pm2 save
pm2 startup

# Run the command printed by pm2 startup

7. Start & Pair

View logs:

pm2 logs NODE-WORKER


Look for:

>>> QR CODE ON DASHBOARD


Open your dashboard:

http://<YOUR_SERVER_IP>:5001


Then pair your WhatsApp device:

WhatsApp → Linked Devices → Link a Device → Scan the QR Code

8. Maintenance

Check service status:

pm2 status


Real-time logs:

pm2 monit


Apply updates:

pm2 restart all

9. Firewall (Optional)

If you use UFW:

ufw allow 5001/tcp
ufw reload
