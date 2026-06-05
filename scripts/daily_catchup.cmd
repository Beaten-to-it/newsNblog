@echo off
cd /d C:\Project\newsNblog
python C:\Project\newsNblog\scripts\daily_catchup.py >> C:\Project\newsNblog\data\daily_catchup.log 2>&1
