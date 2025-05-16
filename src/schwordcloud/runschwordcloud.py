import argparse
import logging

from schwordcloud import SCHWordCloud


def run_schwordcloud():

    LOG_TS_FORMAT = "%d/%m/%Y %H:%M:%S"

    parser = argparse.ArgumentParser(description="Handle arguments for SCHWordCloud.")
    parser.add_argument(
        "-C",
        "--config_file",
        type=str,
        default=None,
        help="Path to the configuration file. If not provided, the default config will be used.",
    )
    parser.add_argument(
        "-V", "--verbose", action="store_true", help="Increase output verbosity."
    )
    args = parser.parse_args()

    logger = logging.getLogger(__name__)

    # Configure logging based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_handlers = []

    # Always log to file
    file_handler = logging.FileHandler("schwordcloud.log")
    file_handler.setLevel(logging.INFO)
    log_handlers.append(file_handler)

    # Add console handler if verbose is True
    if args.verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        log_handlers.append(console_handler)

    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s|%(name)s|%(message)s",
        datefmt=LOG_TS_FORMAT,
        handlers=log_handlers,
    )

    logger.info("SCHWordCloud started.")
    logger.debug(f"Configuration file: {args.config_file}")

    schwc = SCHWordCloud()
    schwc.generate_wordcloud()

    logger.info("SCHWordCloud finished.")

if __name__ == "__main__":
    run_schwordcloud()
