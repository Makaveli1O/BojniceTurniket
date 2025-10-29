PYTHON = python3
APP = qr_gate_control.py
API = test_api.py
REQ = requirements.txt

.PHONY: run api testrun clean deps

deps:
	$(PYTHON) -m pip install -r $(REQ)

api: deps
	$(PYTHON) $(API)

run:
	sudo -E python qr_gate_control.py

testrun: deps
	$(PYTHON) $(API) & \
	sleep 1 && \
	$(PYTHON) $(APP)

clean:
	@echo "Stopping test API..."
	@pkill -f $(API) || true
