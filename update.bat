@echo off

echo Activating virtual environment...
call soe_venv\Scripts\activate

echo Updating pip...
python -m pip install --upgrade pip

echo Updating Python packages...
pip install --upgrade -r requirements.txt

echo Update complete!
pip freeze

echo Deactivating virtual environment...
call deactivate

pause