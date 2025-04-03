@echo off

echo Creating virtual environment...
python -m venv soe_venv

echo Activating virtual environment...
call soe_venv\Scripts\activate

echo Updating pip...
python -m pip install --upgrade pip

echo Installing required Python packages...
pip install --upgrade -r requirements.txt

echo Installation complete!
pip freeze

echo Deactivating virtual environment...
call soe_venv\Scripts\deactivate

pause