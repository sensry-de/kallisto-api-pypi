# Kallisto API & Demo Suite

This repository contains the **Kallisto Python API**, example test scripts for **Kallisto devices**.

The folders are organized at folloing:
* **\kallistoapi** > Kallisto python library to access the sensor nodes
* **\tests** > short python Kallisto tests, please refer to the specific [Documentation](tests/README.md)

---

## Installation

Install the API as a package using `setup.py`:

```bash
python -m pip install .
```

The requirements for the [/tests](tests) can be installed using the [requirements.txt](requirements.txt):

```bash
pip install -r requirements.txt
```

## Test

To test the Kallisto Python API, please install the Library as described and checkout the **\test** folder. The MAC
addresses of the devices under test must be added/changed in [\tests\test_settings.py](tests/test_settings.py).
