# Allmänt

Skript för att hämta ändrade poster i Libris från en given tidsstämpel fram till när skriptet körs. Om allt går väl uppdateras tiddstämpeln som ligger i en fil och nästa gång blir intervallet från då skriptet kördes senast. Skulle något inte funka så uppdateras inte tiddstämpel och tidsfönstret blir gradvis större tills det gått att köra skriptet. 

Då Libris ibland levererar data väldigt långsamt är timeout värdet generöst tilltaget.

Importen använder en äldre metod för dataimport till Folio och delar upp den nedladdade MARC-filen i mindre delar (chunks). Nu ska Folio klara import av större datamängder, men skriptet är inte tillpassat för detta. 

## Förutsättningar

Förutsätter att en fil `.env` finns i roten av projektet innehåller följande variabler med värden (justera för att passa aktuell miljö):

```
LIBRIS_BASE_FOLDER="/home/username/LiU-Folio-Scripts/data/libris_files/"
LIBRIS_CHUNKS_FOLDER="chunks/"
LIBRIS_JOBPROFILE="uuid-för-rätt-jobbprofil-i-folio"
LIBRIS_API_URL="https://libris.kb.se/api/marc_export"
LIBRIS_API_KEY="libris-api-nyckel"
```

Skriptet förutsätter även en fil export.properties med rätt värden i mappen `$LIBRIS_BASE_FOLDER`. Anpassa medföljande exempel.
