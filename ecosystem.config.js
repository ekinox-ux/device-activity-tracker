module.exports = {
  apps : [
    {
      name: "PYTHON-API",
      script: "backend_server.py",
      
      // CHEMIN ABSOLU VERS TON PYTHON DANS LE VENV 'wha'
      interpreter: "/home/activity/gommzy-tracker/wha/bin/python", 

      env: {
        PYTHONUNBUFFERED: "1", // Force l'affichage des logs en temps réel
        PORT: 5001
      }
    },
    {
      name: "NODE-WORKER",
      script: "npm",
      args: "start",
      env: {
        NODE_ENV: "production"
      }
    }
  ]
}