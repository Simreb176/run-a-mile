# Run A Mile — small helpers.
#
# Most of the time you don't need any of these: pushing to `main` is the whole
# deploy for the website itself (GitHub Actions rebuilds it). The editing page
# is the one thing that runs on this machine, hence `deploy`.

SERVICE := runamile-editor
UNIT    := deploy/$(SERVICE).service

.PHONY: help build preview edit deploy undeploy status logs

help:  ## show this list
	@grep -E '^[a-z]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  make %-10s %s\n", $$1, $$2}'

build:  ## rebuild docs/ from data/ + templates/
	.venv/bin/python generate.py

preview:  ## serve the dev preview on http://simon-dev.rebecchi.uk:8080
	.venv/bin/python serve.py

edit:  ## run the editing page in the foreground (http://simon-dev.rebecchi.uk:9001)
	.venv/bin/python editor.py

deploy:  ## install/refresh the always-on editing page service and start it
	sudo cp $(UNIT) /etc/systemd/system/$(SERVICE).service
	sudo systemctl daemon-reload
	sudo systemctl enable --now $(SERVICE)
	sudo systemctl restart $(SERVICE)
	@sudo systemctl --no-pager --lines=0 status $(SERVICE) | head -6

undeploy:  ## stop the editing page and remove the service
	-sudo systemctl disable --now $(SERVICE)
	sudo rm -f /etc/systemd/system/$(SERVICE).service
	sudo systemctl daemon-reload

status:  ## is the editing page running?
	@sudo systemctl --no-pager --lines=0 status $(SERVICE) | head -6

logs:  ## follow the editing page's log
	sudo journalctl -u $(SERVICE) -f
