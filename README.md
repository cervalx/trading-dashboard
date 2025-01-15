# tradingedge.club-scraper

### Prerequisites

#### Using Poetry

```sh
python -m venv .venv
# then you need to activate the virtual environment for your shell
pip install poetry
poetry install # switched to poetry for dependency management
```

#### Using pip

```sh
python -m venv .venv
pip install -r requirements.txt
```

````sh

### Run app with

`streamlit run streamlit_app.py`

### Run scraper with

```sh
poetry run python -m modules.tradingedge_scraper.scraper
````

### Run telegram bot for the very first time

```sh
rm .local/scraper.db # if you have the default sqlite db path
poetry run python -m modules.tradingedge_scraper.scraper
# add required chat_id and telegram_token to ./local/settings.json
# you should receive messages for BTC because BTC is hardcoded in the watched list
# and the full ticker list. TODO this needs to take in the full ticker list and the watched list
# needs to be changed from the settings in streamlit before this PR gets merged
poetry run python -m modules.tradingedge_scraper.telegram_bot.bot_alerts
```

```sh

### Community

[Discord](https://discord.gg/DWBMfFQg)
```
