# LiU-Folio-Scripts

En delmängd av de skript som körs vid Linköpings universitet kopplade till Folio. Delvis anpassade och sajtspecifika detaljer kring loggning har tagits bort. 

## Installation

1. Klona projektet
2. `cd LiU-Folio-Scripts`
3. `python3 -m venv venv`
4. `source venv/bin/activate`
5. `pip3 install .`
6. `touch .env`

Följande variabler måste vara med med korrekta värden i .env-filen:

```
# mode
MODE="prod"

# folio
FOLIO_OKAPI_TENANT="tenant"
FOLIO_USERNAME="username"
FOLIO_ENDPOINT="https://path.to.folio/okapi"
FOLIO_PASSWORD="password"
```

Fler variabler kan behövas för enskilda skript. Se README-filer för respektive skript.