@echo off
echo Activating virtual environment...
call soe_venv\Scripts\activate

echo Setting environment variables...
set SOE_CLIENT_ID=yourclientid
set SOE_CLIENT_SECRET=yourclientsecret

echo Running main.py...
python main.py

echo Deactivating virtual environment...
call deactivate
pause