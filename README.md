# cs6440 Individual Project

# Setup environment

Run the following steps on an ubuntu 18 VM, such as the one provided for Lab 3.

```
sudo apt install python3.7-minimal python3.7-venv python3.7-dev python3-wheel build-essential gcc libssl-dev libffi-dev -y
sudo snap install heroku --classic
python3.7 -m venv venv
pip install -r requirements.txt
# pip install wheel # if bdist_wheel errors
```

# Local dev

Run with heroku cli

```
heroku login
heroku local
# heroku local will parse your .env file for any config vars
```