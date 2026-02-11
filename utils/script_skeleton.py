# -*- coding: utf-8 -*-

"""
Skelett för skript.
"""

import logging

from pyfolioclient import FolioClient

from utils import utils


def main():
    """Huvudfunktion"""
    folio_config = utils.load_env()
    mode = folio_config.mode

    # För skript som bara får köras i produktionsläge
    if mode != "prod":
        logging.info("Skriptet körs inte i produktionsläge.")
        return

    try:
        with FolioClient(
            folio_config.base_url,
            folio_config.tenant,
            folio_config.username,
            folio_config.password,
        ) as folio:
            print(folio)
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        logging.error("Misslyckades att ansluta fill Folio: %s", e)


if __name__ == "__main__":
    main()
