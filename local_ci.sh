#!/bin/bash
#
# watchmedo is cool
# rebuild the doc whenever an rst file changes
# should do this whenever code changes too...
#watchmedo shell-command -p '*.py' -c 'pytest --integration' -R -D .
watchmedo shell-command -p '*.py' -c 'pytest' -R -D .
