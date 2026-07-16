#!/usr/bin/env python3
"""Provide the application's main entry point."""

import argparse
import configparser
import csv
import logging
import socket
import subprocess
import time
import uuid
from datetime import date, datetime
from numbers import Integral
from pathlib import Path

import pandas
import psycopg
from psycopg.rows import dict_row


class StudentRow:
    """Represent a student imported from a spreadsheet row."""

    _DATE_FORMAT = "%Y-%m-%d"
    _LIKE_ESCAPE_CHARACTER = "!"

    _OPTIONAL_PROPERTIES = (
        "vat",
        "email",
        "phone",
        "mobile",
        "last_seen",
        "student_id",
        "match_index",
    )

    _DATAFRAME_PROPERTIES = (
        ("Source Row", "row_index"),
        ("Matched Student ID", "student_id"),
        ("Matched Name", "name"),
        ("Matched VAT", "vat"),
        ("Matched Email", "email"),
        ("Matched Phone", "phone"),
        ("Matched Mobile", "mobile"),
        ("Matched Last seen", "last_seen"),
        ("Match Nº", "match_index"),
    )

    def __init__(self, row_index, name, **values):
        """Initialise a student row.

        Args:
            row_index: One-based index of the spreadsheet row.
            name: Student's name.
            **values: Optional property values used to populate the row.

        Raises:
            TypeError: If a value has an invalid type or an unexpected
                property is supplied.
            ValueError: If a value is outside its permitted range.
        """
        self._row_index = None
        self._student_id = None
        self._match_index = None
        self._name = None
        self._vat = None
        self._email = None
        self._phone = None
        self._mobile = None
        self._last_seen = None

        self._row_index = self._validate_int(
            "row index",
            row_index,
            minimum=1,
        )

        self.name = name

        for property_name in self._OPTIONAL_PROPERTIES:
            if property_name not in values:
                continue

            property_value = values.pop(property_name)
            setattr(self, property_name, property_value)

        if values:
            unexpected_arguments = ", ".join(
                sorted(str(key) for key in values)
            )

            raise TypeError(
                "Unexpected StudentRow argument"
                f"{'s' if len(values) != 1 else ''}: "
                f"{unexpected_arguments}."
            )

    @property
    def student_id(self):
        """Return the matched database student identifier."""
        return self._student_id or 0

    @student_id.setter
    def student_id(self, value):
        """Set the matched database student identifier."""
        if value is None:
            self._student_id = None
            return

        self._student_id = self._validate_int(
            "student id",
            value,
            minimum=1,
        )

    @property
    def match_index(self):
        """Return the position of the database match."""
        return self._match_index or 0

    @match_index.setter
    def match_index(self, value):
        """Set the position of the database match."""
        if value is None:
            self._match_index = None
            return

        self._match_index = self._validate_int(
            "match index",
            value,
            minimum=1,
        )

    @property
    def row_index(self):
        """Return the one-based spreadsheet row index."""
        return self._row_index or 0

    @property
    def name(self):
        """Return the student's name."""
        return self._name or ""

    @name.setter
    def name(self, value):
        """Set and validate the student's name."""
        self._name = self._validate_string(
            "name",
            value,
            allow_none=False,
        )

    @property
    def vat(self):
        """Return the student's VAT identification number."""
        return self._vat or ""

    @vat.setter
    def vat(self, value):
        """Set and validate the student's VAT identification number."""
        self._vat = self._validate_string(
            "vat",
            value,
            allow_none=True,
        )

    @property
    def email(self):
        """Return the student's email address."""
        return self._email or ""

    @email.setter
    def email(self, value):
        """Set and validate the student's email address."""
        self._email = self._validate_string(
            "email",
            value,
            allow_none=True,
        )

    @property
    def phone(self):
        """Return the student's telephone number."""
        return self._phone or ""

    @phone.setter
    def phone(self, value):
        """Set and validate the student's telephone number."""
        self._phone = self._validate_string(
            "phone",
            value,
            allow_none=True,
        )

    @property
    def mobile(self):
        """Return the student's mobile telephone number."""
        return self._mobile or ""

    @mobile.setter
    def mobile(self, value):
        """Set and validate the student's mobile telephone number."""
        self._mobile = self._validate_string(
            "mobile",
            value,
            allow_none=True,
        )

    @property
    def last_seen(self):
        """Return the last-seen date as an ISO-formatted string."""
        if self._last_seen is not None:
            return self._last_seen.strftime(self._DATE_FORMAT)

        return ""

    @last_seen.setter
    def last_seen(self, value):
        """Set the last-seen date.

        Args:
            value: Date, date and time, ISO-formatted string or ``None``.

        Raises:
            TypeError: If the supplied value has an invalid type.
            ValueError: If the supplied string is not a valid date.
        """
        if value is None:
            self._last_seen = None
            return

        # datetime must be checked first because it is a date subclass.
        if isinstance(value, datetime):
            self._last_seen = value.date()
            return

        if isinstance(value, date):
            self._last_seen = value
            return

        if isinstance(value, str):
            value = value.strip()

            if not value:
                self._last_seen = None
                return

            try:
                parsed_value = datetime.strptime(
                    value,
                    self._DATE_FORMAT,
                )
            except ValueError as error:
                raise ValueError(
                    "Last-seen date must use the YYYY-MM-DD format."
                ) from error

            self._last_seen = parsed_value.date()
            return

        raise TypeError(
            "Last-seen value must be a date, datetime, string or None."
        )

    def sql_values(self, vat_mask_character=None):
        """Return the values used by the bulk matching query.

        The name is always converted into a partial ``ILIKE`` pattern. The
        VAT value is also converted into a partial pattern when available.
        Masked VAT positions become SQL single-character wildcards.

        Args:
            vat_mask_character: Character used to mask VAT positions. If
                omitted, every VAT character is treated literally.

        Returns:
            A tuple containing the spreadsheet row index, VAT pattern and
            name pattern.

        Raises:
            TypeError: If the mask character is not a string.
            ValueError: If the mask does not contain exactly one character.
        """
        vat_mask_character = self._validate_mask_character(vat_mask_character)

        name_pattern = self._build_like_pattern(self.name)
        vat_pattern = None

        if self.vat:
            vat_pattern = self._build_like_pattern(
                self.vat,
                mask_character=vat_mask_character,
            )
            vat_pattern = f"%{vat_pattern}%"

        return (
            self.row_index,
            vat_pattern,
            f"%{name_pattern}%",
        )

    @classmethod
    def _build_like_pattern(cls, value, mask_character=None):
        """Build a safe pattern for a parameterised SQL LIKE expression.

        Args:
            value: Original value from which to build the pattern.
            mask_character: Character representing a masked position.

        Returns:
            A safely escaped SQL LIKE pattern.
        """
        if mask_character is None:
            return cls._escape_like_value(value)

        parts = value.split(mask_character)
        escaped_parts = [cls._escape_like_value(part) for part in parts]

        return "_".join(escaped_parts)

    @classmethod
    def _escape_like_value(cls, value):
        """Escape characters with a special meaning in a LIKE pattern.

        Args:
            value: Literal value to escape.

        Returns:
            The escaped value.
        """
        escape_character = cls._LIKE_ESCAPE_CHARACTER

        return (
            value.replace(
                escape_character,
                escape_character * 2,
            )
            .replace(
                "%",
                escape_character + "%",
            )
            .replace(
                "_",
                escape_character + "_",
            )
        )

    @staticmethod
    def _validate_mask_character(value):
        """Validate a VAT mask character.

        Args:
            value: Mask character to validate or ``None``.

        Returns:
            The validated character or ``None``.

        Raises:
            TypeError: If the value is not a string.
            ValueError: If the value does not contain exactly one character.
        """
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError("VAT mask character must be a string.")

        if len(value) != 1:
            raise ValueError(
                "VAT mask character must contain exactly one character."
            )

        return value

    @staticmethod
    def _validate_int(field_name, value, minimum=None, maximum=None):
        """Validate an integer value.

        Args:
            field_name: Name used to identify the value in error messages.
            value: Value to validate.
            minimum: Minimum permitted value, if any.
            maximum: Maximum permitted value, if any.

        Returns:
            The validated integer.

        Raises:
            TypeError: If the value is not an integer.
            ValueError: If the value is outside the permitted range.
        """
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(f"{field_name.capitalize()} must be an integer.")

        if minimum is not None and value < minimum:
            raise ValueError(
                f"{field_name.capitalize()} must be at least {minimum}."
            )

        if maximum is not None and value > maximum:
            raise ValueError(
                f"{field_name.capitalize()} must not exceed {maximum}."
            )

        return int(value)

    @staticmethod
    def _validate_string(field_name, value, allow_none):
        """Validate and normalise a string value.

        Args:
            field_name: Name used to identify the value in error messages.
            value: Value to validate.
            allow_none: Whether an absent or empty value is accepted.

        Returns:
            The stripped string or ``None`` when an empty value is allowed.

        Raises:
            TypeError: If the value is not a string.
            ValueError: If the value is absent when it is required.
        """
        if value is None:
            if allow_none:
                return None

            raise ValueError(f"{field_name.capitalize()} is required.")

        if not isinstance(value, str):
            raise TypeError(f"{field_name.capitalize()} must be a string.")

        value = value.strip()

        if not value:
            if allow_none:
                return None

            raise ValueError(f"{field_name.capitalize()} is required.")

        return value

    def __str__(self):
        """Return a readable representation of the student row."""
        return (
            f"row_index: {self.row_index}, "
            f"name: {self.name}, "
            f"vat: {self.vat}, "
            f"email: {self.email}, "
            f"phone: {self.phone}, "
            f"mobile: {self.mobile}, "
            f"last_seen: {self.last_seen}"
        )

    @classmethod
    def from_database_match(cls, result):
        """Create a student row from a database query result.

        Args:
            result: Mapping containing the database match values.

        Returns:
            A student row populated with the database values.
        """
        return cls(
            row_index=result["row_index"],
            name=result["name"],
            vat=result["vat"],
            email=result["email"],
            phone=result["phone"],
            mobile=result["mobile"],
            last_seen=result["last_seen"],
            student_id=result["student_id"],
            match_index=result["match_index"],
        )

    def apply_database_match(self, result):
        """Update the student row from a database query result.

        Args:
            result: Mapping containing the database match values.
        """
        for property_name in self._OPTIONAL_PROPERTIES:
            if property_name in result:
                setattr(
                    self,
                    property_name,
                    result[property_name],
                )

        if "name" in result:
            self.name = result["name"]

    @classmethod
    def dataframe_columns(cls):
        """Return the columns added to the result data frame.

        Returns:
            A list containing the result column names in output order.
        """
        return [column_name for column_name, _ in cls._DATAFRAME_PROPERTIES]

    def to_dataframe_values(self):
        """Return values to append to a source data frame row.

        Returns:
            A dictionary containing the matching result values.
        """
        return {
            column_name: getattr(self, property_name)
            for column_name, property_name in self._DATAFRAME_PROPERTIES
        }

    @classmethod
    def empty_dataframe_values(cls, row_index):
        """Return empty matching values for an unprocessed source row.

        Args:
            row_index: One-based spreadsheet row index.

        Returns:
            A dictionary containing empty result values. Numeric identifiers
            use zero so that they remain easy to locate and retain an integer
            data type.
        """
        row_index = cls._validate_int(
            "row index",
            row_index,
            minimum=1,
        )

        return {
            "Source Row": row_index,
            "Matched Student ID": 0,
            "Matched Name": "",
            "Matched VAT": "",
            "Matched Email": "",
            "Matched Phone": "",
            "Matched Mobile": "",
            "Matched Last seen": "",
            "Match Nº": 0,
        }


class Application:
    """Manage the configuration and execution of the application."""

    _CONF_SUFIX = "ini"
    _LOG_SUFIX = "log"

    def __init__(self):
        """Initialise the application state."""

        self.arguments = None
        self.logger = None
        self.dataframe = None
        self.result_dataframe = None
        self.result_path = None
        self.source_csv_separator = None
        self.source_sheet_name = None
        self.student_rows = []
        self.additional_student_rows = []
        self.connection = None
        self.ssh_process = None
        self.configuration_loaded = False
        self.configuration_path = self._configuration_path(self._CONF_SUFIX)

    def parse_arguments(self, arguments=None):
        """Process configuration values and command-line arguments.

        Values read from the INI file are used as parser defaults. Values
        supplied explicitly on the command line take precedence over them.

        Args:
            arguments: Arguments to process. If omitted, the arguments
                received by the script are used.

        Returns:
            A namespace containing the processed arguments.
        """
        parser = argparse.ArgumentParser(
            description=("Find competitive exam candidates in the database.")
        )

        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help=(
                "Path of the spreadsheet file to process. It may be omitted "
                "when it is present in the saved configuration."
            ),
        )

        self._add_spreadsheet_arguments(parser)
        self._add_csv_arguments(parser)
        self._add_database_arguments(parser)
        self._add_ssh_arguments(parser)
        self._add_miscellaneous_arguments(parser)

        try:
            configuration_defaults = self._load_configuration()
        except (OSError, ValueError, configparser.Error) as error:
            parser.error(
                "The saved configuration could not be loaded: " f"{error}"
            )

        parser.set_defaults(**configuration_defaults)

        return parser.parse_args(arguments)

    def _add_spreadsheet_arguments(self, parser):
        """Add the spreadsheet-related arguments.

        Args:
            parser: Argument parser to which the arguments are added.
        """
        group = parser.add_argument_group(
            title="Spreadsheet",
            description="Spreadsheet and field configuration.",
        )

        group.add_argument(
            "-sn",
            "--sheet-name",
            default="",
            help=(
                "Name of the sheet to process. By default, the first sheet "
                "is used."
            ),
        )

        group.add_argument(
            "-fn",
            "--field-name",
            default="name",
            help="Name of the field containing the person's name.",
        )

        group.add_argument(
            "-fv",
            "--field-vat",
            default=None,
            help=(
                "Name of the field containing the VAT number. "
                "If omitted, VAT numbers are not read."
            ),
        )

        group.add_argument(
            "-o",
            "--output-file",
            default=None,
            metavar="FILE_PATH",
            help=(
                "Optional result file name or path. Relative paths are "
                "resolved beside the source file. If omitted, a unique "
                "file name is generated automatically."
            ),
        )

    def _add_csv_arguments(self, parser):
        """Add the CSV file processing arguments.

        Args:
            parser: Argument parser to which the arguments are added.
        """
        group = parser.add_argument_group(
            title="CSV",
            description="CSV file format configuration.",
        )

        group.add_argument(
            "-ce",
            "--csv-encoding",
            default="utf-8-sig",
            help=(
                "Character encoding used by the CSV file. "
                "Default: utf-8-sig."
            ),
        )

        group.add_argument(
            "-cs",
            "--csv-separator",
            default=None,
            help=(
                "Field separator used by the CSV file. If omitted, the "
                "separator is detected automatically."
            ),
        )

        group.add_argument(
            "-cq",
            "--csv-quote-character",
            default='"',
            help=(
                "Character used to quote CSV fields. "
                'Default: double quotation mark (").'
            ),
        )

    def _add_database_arguments(self, parser):
        """Add the PostgreSQL database connection arguments.

        Args:
            parser: Argument parser to which the arguments are added.
        """
        group = parser.add_argument_group(
            title="Database",
            description="PostgreSQL database connection configuration.",
        )

        group.add_argument(
            "-dh",
            "--database-host",
            default="localhost",
            help="Database server host. Default: localhost.",
        )

        group.add_argument(
            "-dp",
            "--database-port",
            default=5432,
            type=int,
            help="Database server port. Default: 5432.",
        )

        group.add_argument(
            "-dn",
            "--database-name",
            default="postgres",
            help="Database name. Default: postgres.",
        )

        group.add_argument(
            "-du",
            "--database-user",
            default="postgres",
            help="Database user. Default: postgres.",
        )

        group.add_argument(
            "-dw",
            "--database-password",
            default="",
            help="Database password. Empty by default.",
        )

    def _add_ssh_arguments(self, parser):
        """Add the SSH tunnel arguments.

        Args:
            parser: Argument parser to which the arguments are added.
        """
        group = parser.add_argument_group(
            title="SSH tunnel",
            description="Optional SSH tunnel configuration.",
        )

        group.add_argument(
            "-sh",
            "--ssh-host",
            default=None,
            help=(
                "SSH server used to reach the database. If omitted, no SSH "
                "tunnel is created."
            ),
        )

        group.add_argument(
            "-sp",
            "--ssh-port",
            default=22,
            type=int,
            help="SSH server port. Default: 22.",
        )

        group.add_argument(
            "-su",
            "--ssh-user",
            default=None,
            help="SSH user name.",
        )

        group.add_argument(
            "-slp",
            "--ssh-local-port",
            default=5433,
            type=int,
            help="Local port assigned to the SSH tunnel. Default: 5433.",
        )

        group.add_argument(
            "-si",
            "--ssh-identity-file",
            default=None,
            help="Path of the private SSH identity file.",
        )

    def _add_miscellaneous_arguments(self, parser):
        """Add miscellaneous application arguments.

        Args:
            parser: Argument parser to which the arguments are added.
        """
        group = parser.add_argument_group(
            title="Miscellaneous",
            description="General application options.",
        )

        group.add_argument(
            "-vm",
            "--vat-mask-character",
            default=None,
            help=(
                "Character used to mask positions in VAT identifiers. "
                "If omitted, every VAT character is treated literally."
            ),
        )

        group.add_argument(
            "-sc",
            "--save-config",
            action="store_true",
            help=(
                "Save the complete application configuration to an INI "
                "file in the user's home folder and exit."
            ),
        )

        group.add_argument(
            "-sq",
            "--show-sql",
            action="store_true",
            help=(
                "Display the final SQL queries with their parameter values "
                "included and exit without connecting to the database."
            ),
        )

        verbosity_group = group.add_mutually_exclusive_group()

        verbosity_group.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            default=False,
            help="Display informational messages in the console.",
        )

        verbosity_group.add_argument(
            "--no-verbose",
            dest="verbose",
            action="store_false",
            help=(
                "Do not display informational messages in the console, "
                "even if verbose mode is enabled in the configuration."
            ),
        )

    def _configure_logger(self):
        """Configure file and console logging.

        All messages, including debugging messages, are written to a log file
        with the same base name as the script. The console displays warnings
        and errors by default, or informational messages when verbose mode is
        enabled.

        Returns:
            The configured application logger.
        """
        logger = logging.getLogger("candidate_finder")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

        log_path = self._configuration_path(self._LOG_SUFIX)

        file_formatter = logging.Formatter(
            fmt=("%(asctime)s | %(levelname)-8s | " "%(name)s | %(message)s"),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")

        file_handler = logging.FileHandler(
            log_path,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            logging.INFO if self.arguments.verbose else logging.WARNING
        )
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _validate_arguments(self):
        """Validate the application arguments.

        Raises:
            FileNotFoundError: If the SSH identity file does not exist.
            TypeError: If an argument has an invalid type.
            ValueError: If an argument has an invalid value.
        """
        if not self.arguments.file_path:
            raise ValueError(
                "Spreadsheet file path is required either on the command "
                "line or in the saved configuration."
            )

        port_arguments = {
            "database port": self.arguments.database_port,
            "SSH port": self.arguments.ssh_port,
            "SSH local port": self.arguments.ssh_local_port,
        }

        for argument_name, port in port_arguments.items():
            if port < 1 or port > 65535:
                raise ValueError(
                    f"{argument_name.capitalize()} must be between "
                    "1 and 65535."
                )

        quote_character = self.arguments.csv_quote_character

        if not isinstance(quote_character, str):
            raise TypeError("CSV quote character must be a string.")

        if len(quote_character) != 1:
            raise ValueError(
                "CSV quote character must contain exactly one character."
            )

        separator = self.arguments.csv_separator

        if separator is not None:
            if not isinstance(separator, str):
                raise TypeError("CSV separator must be a string.")

            if separator not in {"tab", r"\t"} and len(separator) != 1:
                raise ValueError(
                    "CSV separator must contain exactly one character."
                )

        mask_character = self.arguments.vat_mask_character

        if mask_character is not None:
            StudentRow._validate_mask_character(mask_character)

        if self.arguments.ssh_host and not self.arguments.ssh_user:
            raise ValueError(
                "SSH user is required when an SSH host is configured."
            )

        if self.arguments.ssh_user and not self.arguments.ssh_host:
            raise ValueError(
                "SSH host is required when an SSH user is configured."
            )

        identity_file = self.arguments.ssh_identity_file

        if identity_file is not None:
            identity_path = Path(identity_file).expanduser()

            if not identity_path.is_file():
                raise FileNotFoundError(
                    f"SSH identity file not found: {identity_path}"
                )

            self.arguments.ssh_identity_file = str(identity_path.resolve())

    def _log_configuration(self):
        """Record the application configuration in the log."""
        self.logger.debug(
            "Configuration file: %s",
            self.configuration_path,
        )
        self.logger.debug(
            "Saved configuration loaded: %s",
            self.configuration_loaded,
        )
        self.logger.debug(
            "Spreadsheet file: %s",
            self.arguments.file_path,
        )
        self.logger.debug(
            "Output file: %s",
            self.arguments.output_file or "<automatic>",
        )
        self.logger.debug(
            "Sheet name: %s",
            self.arguments.sheet_name or "<first sheet>",
        )
        self.logger.debug(
            "Name field: %s",
            self.arguments.field_name,
        )
        self.logger.debug(
            "VAT field: %s",
            self.arguments.field_vat or "<not configured>",
        )
        self.logger.debug(
            "VAT mask character configured: %s",
            self.arguments.vat_mask_character is not None,
        )
        self.logger.debug(
            "CSV encoding: %s",
            self.arguments.csv_encoding,
        )
        self.logger.debug(
            "CSV separator: %s",
            self.arguments.csv_separator or "<automatic>",
        )
        self.logger.debug(
            "Database host: %s",
            self.arguments.database_host,
        )
        self.logger.debug(
            "Database port: %s",
            self.arguments.database_port,
        )
        self.logger.debug(
            "Database name: %s",
            self.arguments.database_name,
        )
        self.logger.debug(
            "Database user: %s",
            self.arguments.database_user,
        )
        self.logger.debug(
            "SSH host: %s",
            self.arguments.ssh_host or "<not configured>",
        )
        self.logger.debug(
            "Show SQL mode: %s",
            self.arguments.show_sql,
        )
        self.logger.debug(
            "Verbose mode: %s",
            self.arguments.verbose,
        )

    def _read_spreadsheet(self):
        """Read the spreadsheet specified in the application arguments.

        CSV files are read using the configured encoding, separator and quote
        character. Excel files are read from the configured sheet or, when no
        sheet name is supplied, from the first sheet.

        Returns:
            A data frame containing the spreadsheet data.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            IsADirectoryError: If the specified path refers to a directory.
            ValueError: If the file format is not supported.
        """
        file_path = Path(self.arguments.file_path).expanduser()

        if not file_path.exists():
            raise FileNotFoundError(f"Spreadsheet file not found: {file_path}")

        if not file_path.is_file():
            raise IsADirectoryError(
                f"The spreadsheet path is not a file: {file_path}"
            )

        file_extension = file_path.suffix.lower()

        self.logger.info(
            "Reading spreadsheet: %s",
            file_path,
        )
        self.logger.debug(
            "Spreadsheet format: %s",
            file_extension,
        )

        if file_extension == ".csv":
            separator = self.arguments.csv_separator

            if separator in {"tab", r"\t"}:
                separator = "\t"

            if separator is None:
                separator = self._detect_csv_separator(file_path)

            self.source_csv_separator = separator

            dataframe = pandas.read_csv(
                file_path,
                sep=separator,
                engine="c",
                encoding=self.arguments.csv_encoding,
                quotechar=self.arguments.csv_quote_character,
                dtype=str,
            )

        elif file_extension in {
            ".xls",
            ".xlsx",
            ".xlsm",
            ".xlsb",
            ".ods",
        }:
            with pandas.ExcelFile(file_path) as workbook:
                if self.arguments.sheet_name:
                    sheet_name = self.arguments.sheet_name
                else:
                    sheet_name = workbook.sheet_names[0]

                self.source_sheet_name = sheet_name

                dataframe = pandas.read_excel(
                    workbook,
                    sheet_name=sheet_name,
                    dtype=str,
                )

        else:
            raise ValueError(
                "Unsupported spreadsheet format: "
                f"{file_extension or '<no extension>'}"
            )

        self.logger.info(
            "Spreadsheet read successfully: %d rows and %d columns.",
            len(dataframe.index),
            len(dataframe.columns),
        )

        self.logger.debug(
            "Spreadsheet columns: %s",
            ", ".join(str(column) for column in dataframe.columns),
        )

        return dataframe

    def _detect_csv_separator(self, file_path):
        """Detect the separator used by a CSV file.

        Args:
            file_path: Path of the CSV file to inspect.

        Returns:
            The detected single-character field separator.

        Raises:
            ValueError: If the separator cannot be detected.
        """
        with file_path.open(
            mode="r",
            encoding=self.arguments.csv_encoding,
            newline="",
        ) as csv_file:
            sample = csv_file.read(8192)

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error as error:
            raise ValueError(
                "The CSV separator could not be detected. Use "
                "--csv-separator to specify it explicitly."
            ) from error

        separator = dialect.delimiter

        if not isinstance(separator, str) or len(separator) != 1:
            raise ValueError("The detected CSV separator is not valid.")

        self.logger.debug(
            "Detected CSV separator: %r",
            separator,
        )

        return separator

    def _find_column(
        self,
        dataframe,
        column_name,
        raise_if_not_found=True,
    ):
        """Find a column in a data frame by name.

        An exact match is attempted first. If no exact match is found, column
        names are compared after removing surrounding whitespace and ignoring
        letter case.

        Args:
            dataframe: Data frame whose columns will be searched.
            column_name: Name of the column to find.
            raise_if_not_found: Whether to raise an exception when the column
                cannot be found.

        Returns:
            The actual column label found in the data frame, or ``None`` when
            the column is not found and ``raise_if_not_found`` is ``False``.

        Raises:
            TypeError: If the column name is neither a string nor ``None``.
            ValueError: If the column name is empty or matches several columns.
            KeyError: If the column is not found and ``raise_if_not_found`` is
                ``True``.
        """
        if column_name is None:
            if raise_if_not_found:
                raise ValueError("Column name cannot be None.")

            return None

        if not isinstance(column_name, str):
            raise TypeError("Column name must be a string or None.")

        column_name = column_name.strip()

        if not column_name:
            if raise_if_not_found:
                raise ValueError("Column name cannot be empty.")

            return None

        if column_name in dataframe.columns:
            self.logger.debug(
                "Column found by exact name: %s",
                column_name,
            )
            return column_name

        normalised_name = column_name.casefold()

        matching_columns = [
            column
            for column in dataframe.columns
            if str(column).strip().casefold() == normalised_name
        ]

        if len(matching_columns) == 1:
            actual_column = matching_columns[0]

            self.logger.debug(
                "Column '%s' found as '%s'.",
                column_name,
                actual_column,
            )

            return actual_column

        if len(matching_columns) > 1:
            matching_names = ", ".join(
                repr(column) for column in matching_columns
            )

            raise ValueError(
                f"Column name '{column_name}' is ambiguous. "
                f"Matching columns: {matching_names}."
            )

        if raise_if_not_found:
            available_columns = ", ".join(
                repr(column) for column in dataframe.columns
            )

            raise KeyError(
                f"Column '{column_name}' was not found. "
                f"Available columns: "
                f"{available_columns or '<none>'}."
            )

        self.logger.debug(
            "Optional column not found: %s",
            column_name,
        )

        return None

    def _load_student_rows(self):
        """Load student rows from the configured spreadsheet.

        The method reads the spreadsheet, locates the configured columns and
        creates one ``StudentRow`` object for each valid data row. Rows without
        a valid name are skipped and recorded as warnings.

        Returns:
            A list containing the student rows loaded from the spreadsheet.

        Raises:
            KeyError: If a configured column cannot be found.
            TypeError: If a configured column name has an invalid type.
            ValueError: If a configured column name is empty or ambiguous.
        """
        self.dataframe = self._read_spreadsheet()

        name_column = self._find_column(
            self.dataframe,
            self.arguments.field_name,
        )

        vat_column = None

        if self.arguments.field_vat is not None:
            vat_column = self._find_column(
                self.dataframe,
                self.arguments.field_vat,
            )

        self.logger.debug(
            "Student name column: %s",
            name_column,
        )
        self.logger.debug(
            "Student VAT column: %s",
            vat_column or "<not configured>",
        )

        self.student_rows = []

        for row_index, (_, row) in enumerate(
            self.dataframe.iterrows(),
            start=2,
        ):
            name = self._normalise_cell_value(row[name_column])

            vat = None

            if vat_column is not None:
                vat = self._normalise_cell_value(row[vat_column])

            try:
                student_row = StudentRow(
                    row_index=row_index,
                    name=name,
                    vat=vat,
                )
            except (TypeError, ValueError) as error:
                self.logger.warning(
                    "Spreadsheet row %d was skipped: %s",
                    row_index,
                    error,
                )
                self.logger.debug(
                    "Spreadsheet row %d failed validation.",
                    row_index,
                )
                continue

            self.student_rows.append(student_row)

            self.logger.debug(
                "Student loaded from spreadsheet row %d.",
                row_index,
            )

        self.logger.info(
            "%d student rows loaded from the spreadsheet.",
            len(self.student_rows),
        )

        return self.student_rows

    @staticmethod
    def _normalise_cell_value(value):
        """Normalise a value read from a spreadsheet cell.

        Missing pandas values and empty strings are converted to ``None``.
        Other values are converted to stripped strings.

        Args:
            value: Value read from a spreadsheet cell.

        Returns:
            The normalised string or ``None`` when the cell is empty.
        """
        if pandas.isna(value):
            return None

        value = str(value).strip()

        return value or None

    def _open_ssh_tunnel(self):
        """Open the configured SSH tunnel.

        The database host and port identify the PostgreSQL server as seen from
        the SSH server. The local end of the tunnel is bound exclusively to the
        loopback interface.

        Raises:
            RuntimeError: If SSH is unavailable or the tunnel cannot be
                established.
        """
        if self.arguments.ssh_host is None:
            self.logger.debug("SSH tunnel is not configured.")
            return

        local_address = (
            f"127.0.0.1:{self.arguments.ssh_local_port}:"
            f"{self.arguments.database_host}:"
            f"{self.arguments.database_port}"
        )

        destination = (
            f"{self.arguments.ssh_user}@" f"{self.arguments.ssh_host}"
        )

        command = [
            "ssh",
            "-N",
            "-T",
            "-p",
            str(self.arguments.ssh_port),
            "-L",
            local_address,
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ServerAliveInterval=30",
            "-o",
            "ServerAliveCountMax=3",
        ]

        if self.arguments.ssh_identity_file:
            command.extend(
                [
                    "-i",
                    self.arguments.ssh_identity_file,
                ]
            )

        command.append(destination)

        self.logger.info(
            "Opening SSH tunnel through %s:%d.",
            self.arguments.ssh_host,
            self.arguments.ssh_port,
        )

        try:
            self.ssh_process = subprocess.Popen(command)
        except FileNotFoundError as error:
            raise RuntimeError(
                "The SSH executable was not found. Ensure that OpenSSH "
                "is installed and available in PATH."
            ) from error

        if not self._wait_for_local_port(
            "127.0.0.1",
            self.arguments.ssh_local_port,
        ):
            self._close_ssh_tunnel()

            raise RuntimeError("The SSH tunnel could not be established.")

        self.logger.info(
            "SSH tunnel established on 127.0.0.1:%d.",
            self.arguments.ssh_local_port,
        )

    def _wait_for_local_port(self, host, port, timeout=15):
        """Wait until a local TCP port accepts connections.

        Args:
            host: Local host on which the tunnel listens.
            port: Local TCP port on which the tunnel listens.
            timeout: Maximum number of seconds to wait.

        Returns:
            ``True`` if the port becomes available; otherwise, ``False``.
        """
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if (
                self.ssh_process is not None
                and self.ssh_process.poll() is not None
            ):
                return False

            try:
                with socket.create_connection(
                    (host, port),
                    timeout=0.5,
                ):
                    return True
            except OSError:
                time.sleep(0.2)

        return False

    def _connect_database(self):
        """Connect to the configured PostgreSQL database.

        Returns:
            An open PostgreSQL database connection.

        Raises:
            psycopg.Error: If the connection cannot be established.
        """
        if self.arguments.ssh_host is not None:
            connection_host = "127.0.0.1"
            connection_port = self.arguments.ssh_local_port
        else:
            connection_host = self.arguments.database_host
            connection_port = self.arguments.database_port

        self.logger.info(
            "Connecting to PostgreSQL database '%s' on %s:%s.",
            self.arguments.database_name,
            connection_host,
            connection_port,
        )

        self.connection = psycopg.connect(
            host=connection_host,
            port=connection_port,
            dbname=self.arguments.database_name,
            user=self.arguments.database_user,
            password=self.arguments.database_password,
            row_factory=dict_row,
            autocommit=True,
        )

        self.logger.info("Database connection established.")

        return self.connection

    def _build_partner_query(self):
        """Build one query for all loaded student rows.

        Returns:
            A tuple containing the parameterised query and its values.

        Raises:
            ValueError: If no student rows have been loaded.
        """
        if not self.student_rows:
            raise ValueError(
                "There are no student rows from which to build the query."
            )

        value_placeholder = "(%s::integer, %s::text, %s::text)"
        values_clause = ",\n        ".join(
            value_placeholder for _ in self.student_rows
        )

        parameters = []

        for student_row in self.student_rows:
            parameters.extend(
                student_row.sql_values(
                    vat_mask_character=(self.arguments.vat_mask_character),
                )
            )

        query = f"""
WITH vals (
    row_index,
    vat_pattern,
    name_pattern
) AS (
    VALUES
        {values_clause}
)
SELECT
    std.id AS student_id,
    rp.name,
    rp.vat,
    rp.email,
    rp.phone,
    rp.mobile,
    COALESCE(
        enrol.deregister,
        enrol.register
    )::date AS last_seen,
    vals.row_index,
    ROW_NUMBER() OVER (
        PARTITION BY vals.row_index
        ORDER BY std.id
    )::integer AS match_index
FROM vals
INNER JOIN res_partner AS rp
    ON unaccent(rp.name)
        ILIKE unaccent(vals.name_pattern) ESCAPE '!'
    AND (
        vals.vat_pattern IS NULL
        OR rp.vat ILIKE vals.vat_pattern ESCAPE '!'
    )
INNER JOIN academy_student AS std
    ON std.res_partner_id = rp.id
LEFT JOIN (
    SELECT DISTINCT ON (student_id)
        student_id,
        register,
        deregister
    FROM academy_training_action_enrolment
    ORDER BY
        student_id,
        deregister DESC NULLS FIRST,
        register DESC
) AS enrol
    ON enrol.student_id = std.id
ORDER BY
    vals.row_index,
    match_index
"""

        return query.strip(), tuple(parameters)

    @staticmethod
    def _quote_sql_value(value):
        """Convert a parameter value into a PostgreSQL SQL literal.

        This conversion is used exclusively to display diagnostic SQL.
        Database queries must continue to use separate parameters.

        Args:
            value: Parameter value to represent as SQL text.

        Returns:
            A PostgreSQL-compatible SQL literal.
        """
        if value is None:
            return "NULL"

        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, datetime):
            value = value.isoformat(sep=" ")
        elif isinstance(value, date):
            value = value.isoformat()
        else:
            value = str(value)

        value = value.replace("\\", "\\\\").replace("'", "''")

        return f"E'{value}'"

    @classmethod
    def _render_sql(cls, query, parameters):
        """Render a parameterised query for diagnostic display.

        The resulting text is intended for inspection and copying only.
        It is not used to execute the database query.

        Args:
            query: SQL query containing positional ``%s`` placeholders.
            parameters: Values associated with the placeholders.

        Returns:
            The SQL query with its parameter values represented as literals.

        Raises:
            ValueError: If the number of placeholders and values differs.
        """
        query_parts = query.split("%s")
        placeholder_count = len(query_parts) - 1

        if placeholder_count != len(parameters):
            raise ValueError(
                "SQL placeholder count does not match parameter count."
            )

        rendered_parts = [query_parts[0]]

        for parameter, query_part in zip(
            parameters,
            query_parts[1:],
        ):
            rendered_parts.append(cls._quote_sql_value(parameter))
            rendered_parts.append(query_part)

        return "".join(rendered_parts)

    def _show_sql_query(self):
        """Display the final bulk SQL query and exit.

        The query is displayed with its parameters represented as SQL
        literals. No SSH tunnel or database connection is opened.
        """
        query, parameters = self._build_partner_query()
        rendered_query = self._render_sql(
            query,
            parameters,
        )

        print(f"{rendered_query};")

        self.logger.info(
            "Bulk SQL query displayed for %d student rows.",
            len(self.student_rows),
        )

    def _apply_partner_matches(self, results):
        """Apply database matches to the loaded student rows.

        A result whose ``match_index`` is one updates the existing object
        created from the spreadsheet. Every later result creates a new
        ``StudentRow`` with the same source row index and is stored in the
        separate ``additional_student_rows`` collection.

        Args:
            results: Database rows returned by the bulk matching query.

        Returns:
            The collection of additional student rows created.

        Raises:
            KeyError: If a result refers to an unknown spreadsheet row.
            TypeError: If a result value has an invalid type.
            ValueError: If a result value is invalid.
        """
        students_by_row = {
            student_row.row_index: student_row
            for student_row in self.student_rows
        }

        self.additional_student_rows = []

        for result in results:
            row_index = result["row_index"]
            match_index = result["match_index"]

            if row_index not in students_by_row:
                raise KeyError(
                    "Database result refers to unknown spreadsheet row "
                    f"{row_index}."
                )

            if match_index == 1:
                students_by_row[row_index].apply_database_match(result)
                continue

            additional_student = StudentRow.from_database_match(result)
            self.additional_student_rows.append(additional_student)

        updated_rows = sum(
            1
            for student_row in self.student_rows
            if student_row.match_index == 1
        )
        unmatched_rows = sum(
            1
            for student_row in self.student_rows
            if student_row.match_index == 0
        )

        self.logger.info(
            "%d original student rows updated, %d additional matches "
            "created and %d rows left unmatched.",
            updated_rows,
            len(self.additional_student_rows),
            unmatched_rows,
        )

        return self.additional_student_rows

    def _build_result_dataframe(self):
        """Build the enriched result data frame.

        Original spreadsheet columns remain on the left. Matching values are
        appended on the right. Additional database matches duplicate their
        corresponding source row and preserve its spreadsheet row index.

        Returns:
            A data frame containing the original and matching data.

        Raises:
            RuntimeError: If the source data frame has not been loaded.
            ValueError: If a result column already exists in the source.
        """
        if self.dataframe is None:
            raise RuntimeError("The source data frame has not been loaded.")

        original_columns = list(self.dataframe.columns)
        result_columns = StudentRow.dataframe_columns()
        duplicate_columns = sorted(
            set(original_columns).intersection(result_columns)
        )

        if duplicate_columns:
            duplicates = ", ".join(
                repr(column) for column in duplicate_columns
            )
            raise ValueError(
                "Result columns already exist in the source data frame: "
                f"{duplicates}."
            )

        students_by_row = {
            student_row.row_index: student_row
            for student_row in self.student_rows
        }
        additional_by_row = {}

        for student_row in self.additional_student_rows:
            additional_by_row.setdefault(
                student_row.row_index,
                [],
            ).append(student_row)

        output_rows = []

        for dataframe_position in range(len(self.dataframe.index)):
            row_index = dataframe_position + 2
            source_values = self.dataframe.iloc[dataframe_position].to_dict()
            student_row = students_by_row.get(row_index)

            if student_row is None:
                result_values = StudentRow.empty_dataframe_values(row_index)
                output_rows.append({**source_values, **result_values})
                continue

            matches = [student_row]
            matches.extend(additional_by_row.get(row_index, []))
            matches.sort(key=lambda match: match.match_index)

            for match in matches:
                result_values = match.to_dataframe_values()
                output_rows.append({**source_values, **result_values})

        self.result_dataframe = pandas.DataFrame(
            output_rows,
            columns=original_columns + result_columns,
        )

        return self.result_dataframe

    def _build_result_path(self):
        """Build the output path for the result spreadsheet.

        When an output file is configured, relative paths are resolved
        beside the source spreadsheet. If the configured name has no
        extension, the source extension is appended. Otherwise, a unique
        file name is generated beside the source spreadsheet.

        Returns:
            The configured or automatically generated result path.

        Raises:
            FileNotFoundError: If the configured output folder does not
                exist.
            RuntimeError: If a unique automatic path cannot be generated.
            ValueError: If the configured path would overwrite the source
                or uses a different file extension.
        """
        source_path = Path(self.arguments.file_path).expanduser().resolve()

        if self.arguments.output_file:
            result_path = Path(self.arguments.output_file).expanduser()

            if not result_path.is_absolute():
                result_path = source_path.parent / result_path

            if not result_path.suffix:
                result_path = result_path.with_suffix(source_path.suffix)

            result_path = result_path.resolve()

            if result_path.suffix.lower() != source_path.suffix.lower():
                raise ValueError(
                    "The output file must use the same extension as "
                    "the source spreadsheet."
                )

            if result_path == source_path:
                raise ValueError(
                    "The output file must be different from the source "
                    "spreadsheet."
                )

            if not result_path.parent.is_dir():
                raise FileNotFoundError(
                    "Output folder not found: " f"{result_path.parent}"
                )

            return result_path

        for _ in range(100):
            identifier = uuid.uuid4().hex[:8]
            result_name = (
                f"{source_path.stem}_{identifier}" f"{source_path.suffix}"
            )
            result_path = source_path.with_name(result_name)

            if not result_path.exists():
                return result_path

        raise RuntimeError("A unique result file name could not be generated.")

    def _save_result_dataframe(self):
        """Save the enriched data frame beside the source spreadsheet.

        The result uses the configured output path or an automatically
        generated path beside the source spreadsheet. It retains the source
        extension. CSV output also reuses the configured encoding, quote
        character and detected or configured separator.

        Returns:
            The path of the result file created.

        Raises:
            RuntimeError: If the result data frame has not been built.
            ValueError: If writing the source format is not supported.
        """
        if self.result_dataframe is None:
            raise RuntimeError("The result data frame has not been built.")

        result_path = self._build_result_path()
        file_extension = result_path.suffix.lower()

        if file_extension == ".csv":
            separator = self.source_csv_separator

            if separator is None:
                separator = self.arguments.csv_separator or ","

            if separator in {"tab", r"\t"}:
                separator = "\t"

            self.result_dataframe.to_csv(
                result_path,
                index=False,
                encoding=self.arguments.csv_encoding,
                sep=separator,
                quotechar=self.arguments.csv_quote_character,
                quoting=csv.QUOTE_NONNUMERIC,
                lineterminator="\n",
            )

        elif file_extension in {".xlsx", ".xlsm"}:
            sheet_name = self.source_sheet_name or "Results"

            self.result_dataframe.to_excel(
                result_path,
                index=False,
                sheet_name=sheet_name,
                engine="openpyxl",
            )

            if file_extension == ".xlsm":
                self.logger.warning(
                    "The result keeps the XLSM extension, but VBA macros "
                    "from the source workbook are not copied."
                )

        elif file_extension == ".ods":
            sheet_name = self.source_sheet_name or "Results"

            self.result_dataframe.to_excel(
                result_path,
                index=False,
                sheet_name=sheet_name,
                engine="odf",
            )

        elif file_extension in {".xls", ".xlsb"}:
            raise ValueError(
                f"Writing {file_extension} files is not supported. "
                "Convert the source file to XLSX before processing it."
            )

        else:
            raise ValueError(
                "Unsupported result spreadsheet format: "
                f"{file_extension or '<no extension>'}"
            )

        self.result_path = result_path

        self.logger.info(
            "Result spreadsheet saved to: %s",
            result_path,
        )

        return result_path

    def _find_all_partner_matches(self):
        """Find and apply matches for all loaded student rows.

        Returns:
            The complete list of database query results.

        Raises:
            RuntimeError: If no database connection is available.
        """
        if self.connection is None:
            raise RuntimeError("Database connection has not been established.")

        query, parameters = self._build_partner_query()

        self.logger.debug(
            "Executing bulk partner search for %d student rows.",
            len(self.student_rows),
        )
        self.logger.debug(
            "SQL parameter count: %d",
            len(parameters),
        )

        with self.connection.cursor() as cursor:
            cursor.execute(query, parameters)
            results = cursor.fetchall()

        self._apply_partner_matches(results)

        self.logger.info(
            "%d total database matches found.",
            len(results),
        )

        return results

    def _close_database(self):
        """Close the PostgreSQL database connection."""
        if self.connection is None:
            return

        self.connection.close()
        self.connection = None

        if self.logger is not None:
            self.logger.info("Database connection closed.")

    def _close_ssh_tunnel(self):
        """Close the SSH tunnel."""
        if self.ssh_process is None:
            return

        if self.ssh_process.poll() is None:
            self.ssh_process.terminate()

            try:
                self.ssh_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ssh_process.kill()
                self.ssh_process.wait()

        self.ssh_process = None

        if self.logger is not None:
            self.logger.info("SSH tunnel closed.")

    @staticmethod
    def _configuration_path(file_extension):
        """Return the path of the user's INI configuration file.

        Returns:
            The configuration path in the user's home folder.
        """
        this_path = Path(__file__).resolve()
        sufix = f".{file_extension}"

        config_name = this_path.with_suffix(sufix).name

        return Path.home() / config_name

    def _load_configuration(self):
        """Load saved configuration values from the user's INI file.

        Empty optional values are converted to ``None``. Numeric and Boolean
        values are converted to their corresponding Python types so that they
        can be used directly as ``argparse`` defaults.

        Returns:
            A dictionary containing defaults read from the configuration file.

        Raises:
            OSError: If the configuration file cannot be read.
            ValueError: If a numeric or Boolean value is invalid.
            configparser.Error: If the INI file is malformed.
        """
        config_path = self._configuration_path(self._CONF_SUFIX)
        self.configuration_path = config_path
        self.configuration_loaded = False

        if not config_path.is_file():
            return {}

        configuration = configparser.ConfigParser(
            interpolation=None,
        )

        with config_path.open(
            mode="r",
            encoding="utf-8",
        ) as config_file:
            configuration.read_file(config_file)

        defaults = {
            "file_path": self._optional_configuration_value(
                configuration,
                "Application",
                "file_path",
            ),
            "output_file": self._optional_configuration_value(
                configuration,
                "Application",
                "output_file",
            ),
            "sheet_name": configuration.get(
                "Spreadsheet",
                "sheet_name",
                fallback="",
            ),
            "field_name": configuration.get(
                "Spreadsheet",
                "field_name",
                fallback="name",
            ),
            "field_vat": self._optional_configuration_value(
                configuration,
                "Spreadsheet",
                "field_vat",
            ),
            "csv_encoding": configuration.get(
                "CSV",
                "encoding",
                fallback="utf-8-sig",
            ),
            "csv_separator": self._optional_configuration_value(
                configuration,
                "CSV",
                "separator",
            ),
            "csv_quote_character": configuration.get(
                "CSV",
                "quote_character",
                fallback='"',
            ),
            "database_host": configuration.get(
                "Database",
                "host",
                fallback="localhost",
            ),
            "database_port": configuration.getint(
                "Database",
                "port",
                fallback=5432,
            ),
            "database_name": configuration.get(
                "Database",
                "name",
                fallback="postgres",
            ),
            "database_user": configuration.get(
                "Database",
                "user",
                fallback="postgres",
            ),
            "database_password": configuration.get(
                "Database",
                "password",
                fallback="",
            ),
            "ssh_host": self._optional_configuration_value(
                configuration,
                "SSH",
                "host",
            ),
            "ssh_port": configuration.getint(
                "SSH",
                "port",
                fallback=22,
            ),
            "ssh_user": self._optional_configuration_value(
                configuration,
                "SSH",
                "user",
            ),
            "ssh_local_port": configuration.getint(
                "SSH",
                "local_port",
                fallback=5433,
            ),
            "ssh_identity_file": self._optional_configuration_value(
                configuration,
                "SSH",
                "identity_file",
            ),
            "vat_mask_character": self._optional_configuration_value(
                configuration,
                "Miscellaneous",
                "vat_mask_character",
            ),
            "verbose": configuration.getboolean(
                "Miscellaneous",
                "verbose",
                fallback=False,
            ),
        }

        self.configuration_loaded = True

        return defaults

    @staticmethod
    def _optional_configuration_value(
        configuration,
        section,
        option,
    ):
        """Read an optional text value from an INI configuration.

        Args:
            configuration: Configuration parser containing the value.
            section: Name of the INI section.
            option: Name of the option within the section.

        Returns:
            The stripped value or ``None`` when absent or empty.
        """
        value = configuration.get(
            section,
            option,
            fallback=None,
        )

        if value is None:
            return None

        value = value.strip()

        return value or None

    def _save_configuration(self):
        """Save the application configuration to the user's home folder.

        The INI file uses the same base name as the script. The configuration
        includes the spreadsheet, CSV, database, SSH and miscellaneous
        options. The ``save_config`` flag itself is omitted.

        Returns:
            The path of the configuration file created.

        Raises:
            OSError: If the configuration file cannot be written.
        """
        config_path = self._configuration_path(self._CONF_SUFIX)
        self.configuration_path = config_path

        configuration = configparser.ConfigParser(
            interpolation=None,
        )

        configuration["Application"] = {
            "file_path": self._configuration_value(self.arguments.file_path),
            "output_file": self._configuration_value(
                self.arguments.output_file
            ),
        }

        configuration["Spreadsheet"] = {
            "sheet_name": self._configuration_value(self.arguments.sheet_name),
            "field_name": self._configuration_value(self.arguments.field_name),
            "field_vat": self._configuration_value(self.arguments.field_vat),
        }

        configuration["CSV"] = {
            "encoding": self._configuration_value(self.arguments.csv_encoding),
            "separator": self._configuration_value(
                self.arguments.csv_separator
            ),
            "quote_character": self._configuration_value(
                self.arguments.csv_quote_character
            ),
        }

        configuration["Database"] = {
            "host": self._configuration_value(self.arguments.database_host),
            "port": self._configuration_value(self.arguments.database_port),
            "name": self._configuration_value(self.arguments.database_name),
            "user": self._configuration_value(self.arguments.database_user),
            "password": self._configuration_value(
                self.arguments.database_password
            ),
        }

        configuration["SSH"] = {
            "host": self._configuration_value(self.arguments.ssh_host),
            "port": self._configuration_value(self.arguments.ssh_port),
            "user": self._configuration_value(self.arguments.ssh_user),
            "local_port": self._configuration_value(
                self.arguments.ssh_local_port
            ),
            "identity_file": self._configuration_value(
                self.arguments.ssh_identity_file
            ),
        }

        configuration["Miscellaneous"] = {
            "vat_mask_character": self._configuration_value(
                self.arguments.vat_mask_character
            ),
            "verbose": self._configuration_value(self.arguments.verbose),
        }

        with config_path.open(
            mode="w",
            encoding="utf-8",
        ) as config_file:
            configuration.write(config_file)

        self.logger.info(
            "Configuration saved to: %s",
            config_path,
        )

        return config_path

    @staticmethod
    def _configuration_value(value):
        """Convert a configuration value into INI-compatible text.

        Args:
            value: Value to convert.

        Returns:
            A string representation suitable for an INI file.
        """
        if value is None:
            return ""

        if isinstance(value, bool):
            return "true" if value else "false"

        return str(value)

    def run(self, arguments=None):
        """Run the main application workflow.

        Args:
            arguments: Arguments to process. If omitted, the arguments
                received by the script are used.

        Returns:
            The application's exit status.
        """
        self.arguments = self.parse_arguments(arguments)
        self.logger = self._configure_logger()

        self.logger.debug("Application started.")

        try:
            self._validate_arguments()
            self._log_configuration()

            if self.arguments.save_config:
                self._save_configuration()
                return 0

            self._load_student_rows()

            if not self.student_rows:
                self.logger.warning("No valid student rows were found.")
                return 0

            if self.arguments.show_sql:
                self._show_sql_query()
                return 0

            self._open_ssh_tunnel()
            self._connect_database()

            self._find_all_partner_matches()
            self._build_result_dataframe()
            self._save_result_dataframe()

            self.logger.info("Processing completed successfully.")

        except psycopg.Error as error:
            self.logger.error(
                "A database error occurred: %s",
                error,
            )
            self.logger.debug(
                "Database exception details.",
                exc_info=True,
            )
            return 1

        except Exception as error:
            self.logger.error(
                "An unexpected error occurred: %s",
                error,
            )
            self.logger.debug(
                "Unexpected exception details.",
                exc_info=True,
            )
            return 1

        finally:
            self._close_database()
            self._close_ssh_tunnel()

            if self.logger is not None:
                self.logger.debug("Application finished.")

        return 0


def main():
    """Create and run the main application object.

    Returns:
        The application's exit status.
    """
    application = Application()
    return application.run()


if __name__ == "__main__":
    raise SystemExit(main())
