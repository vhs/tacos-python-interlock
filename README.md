# tacos-python-interlock
TACOS Python Interlock

## Usage

```
python3 -m venv .
```

On Windows:
```
Scripts\activate.bat
```

On Linux:
```
. bin/activate
```

To install dependencies:
```
pip install -U -r requirements -r requirements-mock.txt -r requirements-pi.txt
```

Copy `config.sample.yml` to `config.yml` and edit

Start with `TACOS_ENV=mock` for mock development.