A simple Rasa 3.0 assistant that plays rock, paper scissors. Code from the Rasa 3.0 launch event livecoding. You can view the livecoding video here: https://www.youtube.com/watch?v=PfYBXidENlg

To run: 

* Install Rasa 3.0+
* Clone repository
* Run the action server: `rasa run actions`
* Talk to the assistant in the shell: `rasa shell`

Note that the markers *will not* work unless you set up a tracker store other than the default in-memory one, they are provided as a syntax example only.


---------------------------------------------

# Núcleo Software 2022-07-28

# /bin/bash /home/ubuntu/crons/edy_bot_cron.sh
# edy_bot_reload
# pm2 flush edy_bot

# Stop the services
pm2 delete edy_bot
pm2 delete edy_bot_actions

# Search for other rasa-python processes if any
ps -fA | grep python
sudo kill <id>

# pidof /usr/bin/python3 /usr/local/bin/rasa
# sudo kill -9 $(pidof /usr/bin/python3 /usr/local/bin/rasa)

# Get latest source code or edy_bot
git pull origin master

# Start RASA server //  --watch
pm2 start "sudo rasa run --enable-api --port 5005 --cors '*'" --name edy_bot

# Start RASA actions server //  --watch
pm2 start "rasa run actions --port 5055" --name edy_bot_actions

# See the log
pm2 log

# See a list of the processes
pm2 list