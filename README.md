# MQE-Flask-App
This project implements a demo pipeline that accepts users' uploaded file and perform data analysis on it. This programme designs its backend with Flask and frontend uses JinJa and Bootstrap.

## How to run
To run this project with development mode, firstly, initialise python venv
```
python3 -m venv venv
```
the install requirements
```
# activate venv
source venv/bin/activate
# install requirements
pip install -r requirements.txt
```
Then run Flask server in debug mode
```
flask run --debug
```

## Note
- This programme only accepts Excel file with extension of ".xlsx" and ".xls"
- Web page will wait for a while if Excel file has many rows
