import json
import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from pyfolioclient import FolioClient


@dataclass
class FolioConfig:
    """Data class for FOLIO configuration"""

    base_url: str
    tenant: str
    username: str
    password: str
    mode: str


def load_env() -> FolioConfig:
    """Load configuration from environment variables"""
    env_dir = os.path.join(os.getcwd(), ".env")
    load_dotenv(env_dir)
    return FolioConfig(
        base_url=os.environ["FOLIO_ENDPOINT"],
        tenant=os.environ["FOLIO_OKAPI_TENANT"],
        username=os.environ["FOLIO_USERNAME"],
        password=os.environ["FOLIO_PASSWORD"],
        mode=os.environ["MODE"],
    )


def load_config() -> dict:
    """Load configuration from config.json file"""
    config_path = os.path.join(os.getcwd(), "config.json")
    return load_json_file(config_path)


def load_json_file(file_path: str) -> dict:
    """Load a JSON file and return its content as a dictionary"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error("Error loading JSON file %s: %s", file_path, e)
        raise


def save_json_file(file_path: str, data: dict) -> None:
    """Save a dictionary to a JSON file"""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except (FileNotFoundError, IOError) as e:
        logging.error("Error saving JSON file %s: %s", file_path, e)
        raise


def get_last_run_timestamp(last_run_timestamp_path):
    """Läs in tidsstämpeln för senaste körning - skapa en ny fil om den inte finns (initiering)"""
    try:
        with open(last_run_timestamp_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logging.error("File not found: %s", last_run_timestamp_path)
        raise


def update_last_run_timestamp(last_run_timestamp_path, current_utc_timestamp):
    """Uppdatera tidsstämpeln för senaste körning till tidsstämpel när skripetet startades"""
    try:
        with open(last_run_timestamp_path, "w", encoding="utf-8") as f:
            f.write(current_utc_timestamp)
    except FileNotFoundError:
        logging.error("File not found: %s", last_run_timestamp_path)
        raise


def build_bidirectional_dict(
    folio: FolioClient, endpoint: str, key: str, field_name: str
) -> dict[str, str]:
    """Build a bidirectional dictionary between field values and IDs"""
    index = {}

    for entry in folio.iter_data(endpoint, key=key):
        index[entry[field_name]] = entry["id"]
        index[entry["id"]] = entry[field_name]

    return index


def build_address_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of address types"""
    return build_bidirectional_dict(
        folio, "/addresstypes", "addressTypes", "addressType"
    )


def build_callnumber_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of callnumber types"""
    return build_bidirectional_dict(
        folio, "/call-number-types", "callNumberTypes", "name"
    )


def build_contributor_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of contributor types"""
    return build_bidirectional_dict(
        folio, "/contributor-types", "contributorTypes", "name"
    )


def build_contributor_name_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of contributor name types"""
    return build_bidirectional_dict(
        folio, "/contributor-name-types", "contributorNameTypes", "name"
    )


def build_departments_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of departments"""
    return build_bidirectional_dict(folio, "/departments", "departments", "name")


def build_holdings_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of holdings types"""
    return build_bidirectional_dict(folio, "/holdings-types", "holdingsTypes", "name")


def build_identifier_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of identifier types"""
    return build_bidirectional_dict(
        folio, "/identifier-types", "identifierTypes", "name"
    )


def build_instance_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of instance types"""
    return build_bidirectional_dict(folio, "/instance-types", "instanceTypes", "name")


def build_loan_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of loan types"""
    return build_bidirectional_dict(folio, "/loan-types", "loantypes", "name")


def build_locations_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of locations"""
    return build_bidirectional_dict(folio, "/locations", "locations", "code")


def build_material_types_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of material types"""
    return build_bidirectional_dict(folio, "/material-types", "mtypes", "name")


def build_patron_groups_lookup_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of patron groups"""
    return build_bidirectional_dict(folio, "/groups", "usergroups", "group")


def build_service_points_lookup_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of service points"""
    return build_bidirectional_dict(folio, "/service-points", "servicepoints", "code")


def build_statistical_codes_lookup_dict(folio: FolioClient) -> dict[str, str]:
    """Return a bidirectional dictionary of statistical codes"""
    return build_bidirectional_dict(
        folio, "/statistical-codes", "statisticalCodes", "name"
    )

