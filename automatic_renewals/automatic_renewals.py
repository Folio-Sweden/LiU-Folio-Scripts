# -*- coding: utf-8 -*-

"""
Skript som automatiskt förlänger lån.
"""

import datetime
import logging

from pyfolioclient import FolioClient, UnprocessableContentError

from utils import utils

DAYS_LOOK_AHEAD = 3


def main():
    """Huvudfunktion för att förnya lån."""
    folio_config = utils.load_env()
    renewed_loans = 0

    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=DAYS_LOOK_AHEAD)
    end_date_str = str(end_date)

    try:
        with FolioClient(
            folio_config.base_url,
            folio_config.tenant,
            folio_config.username,
            folio_config.password,
        ) as folio:
            print(folio)
            for loan in folio.iter_open_loans_by_due_date_bl(end_date_str):
                load_id = loan.get("id")

                if "borrower" in loan and loan["borrower"].get("barcode"):
                    user_barcode = loan["borrower"]["barcode"]
                else:
                    logging.error("Lån %s saknar streckkod för användare", load_id)
                    continue

                if "item" in loan and loan["item"].get("barcode"):
                    item_barcode = loan["item"]["barcode"]
                else:
                    logging.error("Lån %s saknar streckkod för verk", load_id)
                    continue

                try:
                    folio.renew_loan_by_barcode(
                        item_barcode=item_barcode, user_barcode=user_barcode
                    )
                    renewed_loans += 1
                except UnprocessableContentError:
                    # If a loan cannot be renewed, just continue
                    continue
                except RuntimeError as e:
                    logging.error(
                        "Kunde inte förnya lån för %s och användare %s: %s",
                        item_barcode,
                        user_barcode,
                        e,
                    )

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        logging.error("Misslyckades att ansluta fill Folio: %s", e)


if __name__ == "__main__":
    main()
