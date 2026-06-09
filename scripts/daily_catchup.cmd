@echo off
cd /d C:\Project\newsNblog
rem Use the py launcher (resolves to a real installed Python, never the Hermes venv)
rem so the pipeline keeps working even after Hermes is removed.
py -3 C:\Project\newsNblog\scripts\daily_catchup.py >> C:\Project\newsNblog\data\daily_catchup.log 2>&1
