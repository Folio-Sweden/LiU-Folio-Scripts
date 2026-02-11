# -*- coding: utf-8 -*-

"""
Skript för att exportera data från Libris och importera till Folio
"""

import datetime
import logging
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from httpx import Client, ConnectError, HTTPStatusError, TimeoutException
from pyfolioclient import BadRequestError, FolioClient, ItemNotFoundError
from pymarc import MARCReader, MARCWriter

from utils import utils

CURRENT_UTC_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
CHUNK_SIZE = 200


def get_last_run_timestamp(last_run_timestamp_path):
    """Läs in tidsstämpeln för senaste körning - skapa en ny fil om den inte finns (initiering)"""
    if not os.path.exists(last_run_timestamp_path):
        with open(last_run_timestamp_path, "w", encoding="utf-8") as f:
            f.write(CURRENT_UTC_TIMESTAMP)

    with open(last_run_timestamp_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def update_last_run_timestamp(last_run_timestamp_path):
    """Uppdatera tidsstämpeln för senaste körning till tidsstämpel när skripetet startades"""
    with open(last_run_timestamp_path, "w", encoding="utf-8") as f:
        f.write(CURRENT_UTC_TIMESTAMP)


def get_libris_data(last_run_timestamp, libris_export_properties_path):
    """Håmta MARC-data från Libris"""
    libris_api_url = os.getenv("LIBRIS_API_URL")
    libris_client = Client()
    params = {
        "from": last_run_timestamp,
        "until": CURRENT_UTC_TIMESTAMP,
        "deleted": "ignore",
        "virtualDelete": "false",
    }

    # Eftersom inte Libris klarar att ":"" URL-kodas behvövs denna lösning
    url = f"{libris_api_url}/?{urllib.parse.urlencode(params, safe=':')}"
    logging.info("Hämtar data från Libris: %s", url)
    try:
        with open(libris_export_properties_path, "rb") as prop_file:
            response = libris_client.post(url, data=prop_file, timeout=60 * 60)  # type: ignore
            response.raise_for_status()
            return response.content
    except ConnectError as connection_err:
        raise ConnectionError("Kan inte ansluta till Libris") from connection_err
    except TimeoutException as timeout_err:
        raise TimeoutError("Timeout mot Libris") from timeout_err
    except HTTPStatusError as http_err:
        raise RuntimeError(f"HTTP fel från Libris: {http_err}") from http_err
    finally:
        libris_client.close()


def save_marc(data, libris_base_folder):
    """Spara MARC-data till fil"""
    filename = os.path.join(libris_base_folder, f"export_{CURRENT_UTC_TIMESTAMP}.mrc")
    with open(filename, "wb") as f:
        f.write(data)


def ensure_output_dir(output_dir):
    """Kolla att output-mappen finns, skapa den om den inte gör det"""
    output_dir.mkdir(parents=True, exist_ok=True)


def get_mrc_files(input_dir):
    """Skapa lista över MARC-filer i en given mapp"""
    return list(input_dir.glob("*.mrc"))


def read_marc_records(file_path):
    """Läs MARC-poster från fil"""
    with open(file_path, "rb") as fh:
        yield from MARCReader(fh)


def write_marc_chunk(records, output_path):
    """Skriv MARC-poster till fil"""
    with open(output_path, "wb") as fh:
        writer = MARCWriter(fh)
        for record in records:
            writer.write(record)
        writer.close()


def write_chunk(records, output_dir, chunk_index):
    """Skriv chunk till fil"""
    output_file = output_dir / f"export_{CURRENT_UTC_TIMESTAMP}_{chunk_index:03}.mrc"
    write_marc_chunk(records, output_file)
    logging.info("Skrev %s poster till %s", len(records), output_file)


def get_libris_id(record):
    """Hämta Libris-ID från MARC-poster"""
    return record["001"].value()


def custom_transform(record):
    """Anpassad transformation av MARC-poster"""

    # Ta bort hela fält 035
    record.remove_fields("035")

    # Ta bort delfält 9 i fält 830
    rec_830s = record.get_fields("830")
    for rec_830 in rec_830s:
        for _ in rec_830.get_subfields("9"):
            rec_830.delete_subfield("9")

    return record


def process_mrc_files(input_dir, output_dir, chunk_size):
    """Bearbeta MARC-filer - dela upp dem i mindre delar"""
    ensure_output_dir(output_dir)

    accumulated_records = []
    unique_records = set()
    chunk_index = 1

    for mrc_file in get_mrc_files(input_dir):
        for record in read_marc_records(mrc_file):
            libris_id = get_libris_id(record)
            if libris_id in unique_records:
                continue
            unique_records.add(libris_id)
            record = custom_transform(record)
            accumulated_records.append(record)
            if len(accumulated_records) == chunk_size:
                write_chunk(accumulated_records, output_dir, chunk_index)
                accumulated_records = []
                chunk_index += 1

    # Skriv de poster som återstår
    if accumulated_records:
        write_chunk(accumulated_records, output_dir, chunk_index)


def import_marc_files_to_folio(folio, chunks_folder, libris_jobprofile):
    """Importera MARC-filer till Folio"""
    chunks_path = Path(chunks_folder)
    marc_files = list(chunks_path.glob("*.mrc"))
    marc_files_dict = {file.name: file for file in marc_files}

    if not marc_files:
        return

    # Steg 1 - skapa upload definition
    upload_definition = create_upload_definition(folio, marc_files)
    upload_definition_id = upload_definition.get("id")

    # Steg 2 - ladda upp filinnehåll för varje file definition
    for file_definition in upload_definition.get("fileDefinitions"):
        file_definition_id = file_definition["id"]
        file_name = file_definition["name"]
        file_path = marc_files_dict.get(file_name)
        upload_file(folio, upload_definition_id, file_definition_id, file_path)

    # Steg 3 - initiera import
    initiate_import(folio, upload_definition_id, libris_jobprofile)


def create_upload_definition(folio, files):
    """Skapa en upload definition för att ladda upp MARC-filer"""
    payload = {
        "fileDefinitions": [
            {
                "name": file_path.name,
            }
            for file_path in files
        ]
    }
    try:
        return folio.post_data("/data-import/uploadDefinitions", payload=payload)
    except (
        ConnectionError,
        TimeoutException,
        BadRequestError,
        ItemNotFoundError,
        RuntimeError,
    ) as e:
        logging.error("Fel vid skapande av upload definition: %s", e)
        raise RuntimeError(f"Fel vid skapande av upload definition: {e}") from e


def upload_file(folio, upload_definition_id, file_definition_id, file_path):
    """Ladda upp filinnehåll för en given file definition"""
    with open(file_path, "rb") as file:
        try:
            return folio.post_data(
                f"/data-import/uploadDefinitions/{upload_definition_id}/files/{file_definition_id}",
                content=file,
            )
        except (
            ConnectionError,
            TimeoutException,
            BadRequestError,
            ItemNotFoundError,
            RuntimeError,
        ) as e:
            logging.error(
                "Fel vid uppladdning av fil %s (id %s) till upload definition %s: %s",
                file_path,
                file_definition_id,
                upload_definition_id,
                e,
            )
            raise RuntimeError(f"Fel vid uppladdning av fil: {e}") from e


def initiate_import(folio, upload_definition_id, job_profile_id):
    """Initiera import av MARC-filer / processning av det som laddats upp"""
    try:
        upload_definition = folio.get_data(
            f"/data-import/uploadDefinitions/{upload_definition_id}", limit=0
        )
        payload = {
            "uploadDefinition": upload_definition,
            "jobProfileInfo": {
                "id": job_profile_id,
                "name": "Libris",
                "dataType": "MARC",
            },
        }
        return folio.post_data(
            f"/data-import/uploadDefinitions/{upload_definition_id}/processFiles",
            payload=payload,
        )
    except (
        ConnectionError,
        TimeoutException,
        BadRequestError,
        ItemNotFoundError,
        RuntimeError,
    ) as e:
        logging.error(
            "Fel vid initiering av import för upload definition %s: %s",
            upload_definition_id,
            e,
        )
        raise RuntimeError(f"Fel vid intiering av import: {e}") from e


def clean_up_folders(folders):
    """Remove .mrc files from specified folders."""
    for folder in folders:
        for file_path in folder.glob("*.mrc"):
            try:
                file_path.unlink()
                logging.info("Removed %s", file_path)
            except OSError as err:
                logging.error("Error removing %s: %s", file_path, err)


def main():
    """Exportera MARC-data från Libris och importera till Folio:
    0. Radera nedladdade filer och temporära filer
    1. Läs in tidsstämpeln för senaste körning
    2. Hämta MARC-data från Libris (avbryt om det inte finns några nya poster)
    3. Spara MARC-data till fil
    4. Dela upp MARC-data i mindre delar
    5. Importera MARC-data till Folio
    6. Radera nedladdade filer och temporära filer
    7. Uppdatera tidsstämpeln för senaste körning om allt gått bra
    OBS! I steg 4 tas dubletter bort och posten modifieras enligt custom_transform
    """
    completed_with_errors = False
    folio_config = utils.load_env()
    mode = folio_config.mode

    # Kör bara i prod-miljö normalt för att inte belasta Libris i onödan
    if mode != "prod":
        logging.info("Skriptet körs bara i produktionsmiljöer")
        return

    libris_base_folder = Path(os.environ["LIBRIS_BASE_FOLDER"])
    chunks_folder = Path(
        os.path.join(libris_base_folder, os.environ["LIBRIS_CHUNKS_FOLDER"])
    )
    libris_jobprofile = os.environ["LIBRIS_JOBPROFILE"]
    last_run_timestamp_path = os.path.join(libris_base_folder, "lastRun.timestamp")
    libris_export_properties_path = os.path.join(
        libris_base_folder, "export.properties"
    )

    # Rensa upp gamla chunk-filer ifall de mot förmodan inte raderats tidigare
    clean_up_folders([chunks_folder])

    try:
        with FolioClient(
            folio_config.base_url,
            folio_config.tenant,
            folio_config.username,
            folio_config.password,
        ) as folio:
            last_run_timestamp = get_last_run_timestamp(last_run_timestamp_path)

            try:
                marc_data = get_libris_data(
                    last_run_timestamp, libris_export_properties_path
                )
            except (ConnectionError, TimeoutError, RuntimeError) as e:
                logging.error("Fel vid hämtning av data från Libris: %s", e)
                return

            if not marc_data:
                logging.info("Inga nya MARC-poster att hämta")
                return

            save_marc(marc_data, libris_base_folder)

            process_mrc_files(
                input_dir=libris_base_folder,
                output_dir=chunks_folder,
                chunk_size=CHUNK_SIZE,
            )

            try:
                import_marc_files_to_folio(folio, chunks_folder, libris_jobprofile)
            except RuntimeError:
                completed_with_errors = True

            clean_up_folders([libris_base_folder, chunks_folder])

            # Uppdatera tidsstämpeln för senaste körning om allt gått bra
            if not completed_with_errors:
                update_last_run_timestamp(last_run_timestamp_path)
    except (
        ConnectionError,
        TimeoutError,
    ) as e:
        logging.error("Misslyckades att ansluta fill Folio: %s", e)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    main()
