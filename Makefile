do:
	export PYTHONDONTWRITEBYTECODE=1
	export PYTHONUNBUFFERED=1
	pip install -r requirements.txt
	cd quipubase && python setup.py build_ext --inplace
	uvicorn main:app --host 0.0.0.0 --port 5000 --reload



