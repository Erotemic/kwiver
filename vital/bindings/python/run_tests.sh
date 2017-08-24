#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "0" == "1" ]; then
    nosetests \
      --cover-erase --with-coverage --cover-package=vital \
      "$@" ${SCRIPT_DIR}/vital/tests/
else
    py.test -cov=vital "$@" ${SCRIPT_DIR}/vital/tests/
fi

