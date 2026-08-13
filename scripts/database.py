#!/usr/bin/env python3
"""Provide reusable PostgreSQL connectivity with optional SSH tunnelling.

The module contains:

- ``PostgresConnectionConfig`` for managing connection settings.
- ``PostgresConnection`` for managing a PostgreSQL connection and an
  optional SSH tunnel.
- ``add_connection_arguments()`` for adding connection options to an
  ``ArgumentParser``.

Basic usage:

    from database import (
        PostgresConnectionConfig,
        PostgresConnection,
    )

    config = PostgresConnectionConfig()
    config.update_from_ini("connection.ini")

    with PostgresConnection(config) as database:
        connection = database.connection

        if connection is None:
            raise RuntimeError("PostgreSQL connection is not available.")

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user")
            result = cursor.fetchone()

        print(result)
"""

from __future__ import annotations

import argparse
import configparser
import logging
import socket
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from types import TracebackType
from typing import ClassVar, Self

import psycopg
from psycopg.rows import dict_row


class PostgresConnectionConfig:
    """Manage PostgreSQL and optional SSH tunnel configuration.

    The class stores all values required to connect directly to a PostgreSQL
    database or indirectly through an SSH tunnel. A new instance starts with
    default values, although any configuration property may be supplied to the
    constructor as a keyword argument.

    Configuration values may subsequently be updated individually through
    public properties, collectively through ``update()``, from a
    ``ConfigParser`` object, or from an INI file. Every individual assignment
    is validated before its value is stored.

    Property setters validate values independently. Relationships between
    several properties, such as requiring an SSH user when an SSH host is
    configured, are checked by ``validate()``. This permits the object to be
    populated progressively without rejecting temporarily incomplete but
    individually valid configurations.

    The class does not open SSH tunnels or PostgreSQL connections. Those
    operations belong to ``PostgresConnection``.

    Attributes:
        database_host:
            PostgreSQL server host as seen from the local machine when
            connecting directly, or from the SSH server when a tunnel is used.
            The default value is ``"localhost"``.
        database_port:
            PostgreSQL server TCP port. The default value is ``5432``.
        database_name:
            Name of the PostgreSQL database. The default value is
            ``"postgres"``.
        database_user:
            PostgreSQL user name. The default value is ``"postgres"``.
        database_password:
            PostgreSQL password. The default value is an empty string. This
            value must never be written to logs.
        ssh_host:
            SSH server used to reach PostgreSQL. When ``None``, the database
            connection is established directly. The default value is ``None``.
        ssh_port:
            SSH server TCP port. The default value is ``22``.
        ssh_user:
            SSH user name. It is required when ``ssh_host`` is configured. The
            default value is ``None``.
        ssh_local_port:
            Local TCP port assigned to the SSH tunnel. The default value is
            ``5433``.
        ssh_identity_file:
            Optional path to the private SSH identity file. When omitted, the
            SSH client uses its standard authentication mechanisms. The
            default value is ``None``.
        logger:
            Logger used to report configuration loading, saving,
            normalisation, and other non-fatal operations. When omitted, the
            module logger is used.
    """

    __slots__ = (  # noqa: RUF023
        "_database_host",
        "_database_port",
        "_database_name",
        "_database_user",
        "_database_password",
        "_ssh_host",
        "_ssh_port",
        "_ssh_user",
        "_ssh_local_port",
        "_ssh_identity_file",
        "_logger",
    )

    _DATABASE_SECTION: ClassVar[str] = "Database"
    _SSH_SECTION: ClassVar[str] = "SSH"

    _DEFAULTS: ClassVar[dict[str, object]] = {
        "database_host": "localhost",
        "database_port": 5432,
        "database_name": "postgres",
        "database_user": "postgres",
        "database_password": "",
        "ssh_host": None,
        "ssh_port": 22,
        "ssh_user": None,
        "ssh_local_port": 5433,
        "ssh_identity_file": None,
    }

    _CONFIGURATION_FIELDS: ClassVar[frozenset[str]] = frozenset(_DEFAULTS)

    def __init__(
        self,
        logger: logging.Logger | None = None,
        **values: object,
    ) -> None:
        """Initialise the configuration with defaults and optional values.

        The logger is assigned first so that it is available during subsequent
        configuration operations. All connection properties are then populated
        with their default values through their corresponding setters.

        Finally, the values supplied as keyword arguments are applied through
        ``update()``, ensuring that constructor values receive the same validation
        as later programmatic assignments.

        The complete configuration is not validated here because it may be built
        progressively. Cross-property requirements are checked by ``validate()``
        before opening a PostgreSQL connection or SSH tunnel.

        Args:
            logger:
                Logger associated with the configuration. When ``None``, the
                module logger is used.
            **values:
                Initial PostgreSQL or SSH configuration values. Every key must
                identify one of the supported public configuration properties.

        Raises:
            TypeError:
                If the logger is invalid, an unknown configuration property is
                supplied, or a value has an invalid type.
            ValueError:
                If a supplied value is empty when required or outside its
                permitted range.
            FileNotFoundError:
                If a supplied SSH identity file does not exist.
            IsADirectoryError:
                If a supplied SSH identity path identifies a directory.
            OSError:
                If an SSH identity path cannot be expanded or resolved.
        """
        self.logger = (
            logger if logger is not None else logging.getLogger(__name__)
        )

        for property_name, default_value in self._DEFAULTS.items():
            setattr(self, property_name, default_value)

        self.update(**values)

    @property
    def database_host(self) -> str:
        """Return the configured PostgreSQL server host."""
        return self._database_host

    @database_host.setter
    def database_host(self, value: str) -> None:
        """Set the PostgreSQL server host.

        Surrounding whitespace is removed before the value is stored.

        Args:
            value:
                PostgreSQL host name or IP address.

        Raises:
            TypeError:
                If ``value`` is not a string.
            ValueError:
                If ``value`` is empty after removing surrounding whitespace.
        """
        self._database_host = self._normalise_required_string(
            "database host",
            value,
        )

    @property
    def database_port(self) -> int:
        """Return the configured PostgreSQL server port."""
        return self._database_port

    @database_port.setter
    def database_port(self, value: int) -> None:
        """Set the PostgreSQL server port.

        Args:
            value:
                PostgreSQL TCP port.

        Raises:
            TypeError:
                If ``value`` is not an integer. Boolean values are rejected
                even though ``bool`` is a subclass of ``int``.
            ValueError:
                If ``value`` is outside the range from 1 to 65535.
        """
        self._database_port = self._validate_port(
            "database port",
            value,
        )

    @property
    def database_name(self) -> str:
        """Return the configured PostgreSQL database name."""
        return self._database_name

    @database_name.setter
    def database_name(self, value: str) -> None:
        """Set the PostgreSQL database name.

        Surrounding whitespace is removed before the value is stored.

        Args:
            value:
                Name of the PostgreSQL database.

        Raises:
            TypeError:
                If ``value`` is not a string.
            ValueError:
                If ``value`` is empty after removing surrounding whitespace.
        """
        self._database_name = self._normalise_required_string(
            "database name",
            value,
        )

    @property
    def database_user(self) -> str:
        """Return the configured PostgreSQL user name."""
        return self._database_user

    @database_user.setter
    def database_user(self, value: str) -> None:
        """Set the PostgreSQL user name.

        Surrounding whitespace is removed before the value is stored.

        Args:
            value:
                PostgreSQL user name.

        Raises:
            TypeError:
                If ``value`` is not a string.
            ValueError:
                If ``value`` is empty after removing surrounding whitespace.
        """
        self._database_user = self._normalise_required_string(
            "database user",
            value,
        )

    @property
    def database_password(self) -> str:
        """Return the configured PostgreSQL password."""
        return self._database_password

    @database_password.setter
    def database_password(self, value: str) -> None:
        """Set the PostgreSQL password.

        The password is stored exactly as supplied because leading or trailing
        whitespace may form part of a valid password.

        Args:
            value:
                PostgreSQL password. An empty string is permitted.

        Raises:
            TypeError:
                If ``value`` is not a string.
        """
        self._database_password = self._validate_password(value)

    @property
    def ssh_host(self) -> str | None:
        """Return the configured SSH server host."""
        return self._ssh_host

    @ssh_host.setter
    def ssh_host(self, value: str | None) -> None:
        """Set the optional SSH server host.

        Surrounding whitespace is removed. ``None`` and empty strings disable
        SSH tunnelling and are stored as ``None``.

        This setter validates only the host itself. The requirement for an SSH
        user when a host is configured is checked by ``validate()``.

        Args:
            value:
                SSH host name, IP address, empty string, or ``None``.

        Raises:
            TypeError:
                If ``value`` is neither a string nor ``None``.
        """
        self._ssh_host = self._normalise_optional_string(
            "SSH host",
            value,
        )

    @property
    def ssh_port(self) -> int:
        """Return the configured SSH server port."""
        return self._ssh_port

    @ssh_port.setter
    def ssh_port(self, value: int) -> None:
        """Set the SSH server port.

        Args:
            value:
                SSH server TCP port.

        Raises:
            TypeError:
                If ``value`` is not an integer. Boolean values are rejected
                even though ``bool`` is a subclass of ``int``.
            ValueError:
                If ``value`` is outside the range from 1 to 65535.
        """
        self._ssh_port = self._validate_port(
            "SSH port",
            value,
        )

    @property
    def ssh_user(self) -> str | None:
        """Return the configured SSH user name."""
        return self._ssh_user

    @ssh_user.setter
    def ssh_user(self, value: str | None) -> None:
        """Set the optional SSH user name.

        Surrounding whitespace is removed. ``None`` and empty strings are
        stored as ``None``.

        This setter validates only the user name itself. The requirement for
        an SSH host when a user is configured is checked by ``validate()``.

        Args:
            value:
                SSH user name, empty string, or ``None``.

        Raises:
            TypeError:
                If ``value`` is neither a string nor ``None``.
        """
        self._ssh_user = self._normalise_optional_string(
            "SSH user",
            value,
        )

    @property
    def ssh_local_port(self) -> int:
        """Return the local port assigned to the SSH tunnel."""
        return self._ssh_local_port

    @ssh_local_port.setter
    def ssh_local_port(self, value: int) -> None:
        """Set the local port assigned to the SSH tunnel.

        Args:
            value:
                Local TCP port on which the SSH tunnel will listen.

        Raises:
            TypeError:
                If ``value`` is not an integer. Boolean values are rejected
                even though ``bool`` is a subclass of ``int``.
            ValueError:
                If ``value`` is outside the range from 1 to 65535.
        """
        self._ssh_local_port = self._validate_port(
            "SSH local port",
            value,
        )

    @property
    def ssh_identity_file(self) -> str | None:
        """Return the configured SSH identity-file path."""
        return self._ssh_identity_file

    @ssh_identity_file.setter
    def ssh_identity_file(
        self,
        value: str | Path | None,
    ) -> None:
        """Set the optional SSH identity-file path.

        User-home markers are expanded and a configured file is converted to
        an absolute path. ``None`` and empty strings are stored as ``None``.

        Args:
            value:
                Path to a private SSH identity file, empty string, or ``None``.

        Raises:
            TypeError:
                If ``value`` is neither a string, ``Path``, nor ``None``.
            FileNotFoundError:
                If a non-empty path does not identify an existing file.
            IsADirectoryError:
                If the supplied path identifies a directory.
            OSError:
                If the path cannot be expanded or resolved.
        """
        self._ssh_identity_file = self._normalise_identity_file(value)

    @property
    def logger(self) -> logging.Logger:
        """Return the logger associated with the configuration."""
        return self._logger

    @logger.setter
    def logger(self, value: logging.Logger) -> None:
        """Associate a logger with the configuration.

        Args:
            value:
                Logger that will receive configuration-related messages.

        Raises:
            TypeError:
                If ``value`` is not a ``logging.Logger`` instance.
        """
        self._logger = self._validate_logger(value)

    def update(self, **values: object) -> None:
        """Update one or more configuration properties through code.

        Every supplied key must identify a public configuration property.
        Values are processed through the corresponding property setters so
        that programmatic updates receive the same validation as individual
        assignments and values loaded from external configuration sources.

        The update is atomic: when any supplied value is invalid, all properties
        are restored to the values they had before the operation began.

        This method validates individual values but does not require the entire
        configuration to be immediately coherent. Cross-property requirements
        are checked by ``validate()``.

        Args:
            **values:
                PostgreSQL or SSH properties to update.

        Raises:
            TypeError:
                If an unknown property is supplied or a value has an invalid
                type.
            ValueError:
                If a supplied value is empty when required or outside its
                permitted range.
            FileNotFoundError:
                If a supplied SSH identity file does not exist.
            IsADirectoryError:
                If a supplied SSH identity path identifies a directory.
            OSError:
                If an SSH identity path cannot be resolved.
        """
        self._validate_update_names(values)

        if not values:
            return

        previous_values = {
            property_name: getattr(self, property_name)
            for property_name in values
        }

        try:
            for property_name, value in values.items():
                setattr(self, property_name, value)

        except BaseException:
            for property_name, previous_value in previous_values.items():
                object.__setattr__(
                    self,
                    f"_{property_name}",
                    previous_value,
                )

            raise

    def update_from_configparser(
        self,
        configuration: configparser.ConfigParser,
    ) -> None:
        """Update the configuration from a ``ConfigParser`` object.

        Values are read from the ``[Database]`` and ``[SSH]`` sections. Only
        options actually present in the parser are applied; missing sections
        and options leave the corresponding current properties unchanged.

        Empty optional SSH values are converted to ``None``. Numeric values
        are converted to integers before they are passed to ``update()``.

        The update is atomic: malformed or invalid configuration data does not
        leave the object partially modified.

        Args:
            configuration:
                Parser containing PostgreSQL and SSH configuration sections.

        Raises:
            TypeError:
                If ``configuration`` is not a ``ConfigParser`` instance or a
                configured value has an invalid type.
            ValueError:
                If a numeric option cannot be converted or a configuration
                value is invalid.
            FileNotFoundError:
                If the configured SSH identity file does not exist.
            IsADirectoryError:
                If the configured SSH identity path identifies a directory.
            configparser.Error:
                If a configuration option cannot be read.
        """
        values = self._read_configparser_values(configuration)

        if not values:
            self.logger.debug(
                "No PostgreSQL or SSH configuration values were found."
            )
            return

        self.update(**values)

        self.logger.debug(
            "PostgreSQL and SSH configuration updated from ConfigParser."
        )

    def update_from_ini(
        self,
        file_path: str | Path,
    ) -> None:
        """Update the configuration from an INI file.

        The file is read using UTF-8 encoding into a ``ConfigParser`` object.
        Interpretation and application of the ``[Database]`` and ``[SSH]``
        sections are delegated to ``update_from_configparser()``.

        Only options present in the file are applied. Properties whose options
        are absent retain their current values.

        Args:
            file_path:
                Path of the INI file to read.

        Raises:
            TypeError:
                If ``file_path`` has an invalid type.
            FileNotFoundError:
                If the INI file or configured SSH identity file does not exist.
            IsADirectoryError:
                If the supplied path refers to a directory.
            OSError:
                If the file cannot be opened or read.
            ValueError:
                If a configured value cannot be converted or is invalid.
            configparser.Error:
                If the INI file is malformed.
        """
        if not isinstance(file_path, (str, Path)):
            raise TypeError("INI file path must be a string or Path.")

        config_path = Path(file_path).expanduser()

        if not config_path.exists():
            raise FileNotFoundError(
                f"INI configuration file not found: {config_path}"
            )

        if not config_path.is_file():
            raise IsADirectoryError(
                f"INI configuration path is not a file: {config_path}"
            )

        config_path = config_path.resolve()

        self.logger.debug(
            "Reading PostgreSQL and SSH configuration from: %s",
            config_path,
        )

        configuration = configparser.ConfigParser(
            interpolation=None,
        )

        with config_path.open(
            mode="r",
            encoding="utf-8",
        ) as configuration_file:
            configuration.read_file(configuration_file)

        self.update_from_configparser(configuration)

        self.logger.info(
            "PostgreSQL and SSH configuration loaded from: %s",
            config_path,
        )

    def update_configparser(
        self,
        configuration: configparser.ConfigParser,
        *,
        include_password: bool = False,
    ) -> configparser.ConfigParser:
        """Add or update connection sections in a configuration parser.

        The current values are written to the ``[Database]`` and ``[SSH]``
        sections. Unrelated sections and options are left unchanged.

        By default, the PostgreSQL password is not written. Enabling
        ``include_password`` stores it as plain text and should therefore be
        used only when the destination configuration is appropriately
        protected.

        Args:
            configuration:
                Parser to update.
            include_password:
                Whether to include the PostgreSQL password in the
                ``[Database]`` section.

        Returns:
            The same ``ConfigParser`` instance after it has been updated.

        Raises:
            TypeError:
                If ``configuration`` is not a ``ConfigParser`` instance or
                ``include_password`` is not Boolean.
            ValueError:
                If the complete configuration is not coherent.
            FileNotFoundError:
                If the configured SSH identity file no longer exists.
        """
        if not isinstance(configuration, configparser.ConfigParser):
            raise TypeError("Configuration must be a ConfigParser instance.")

        if not isinstance(include_password, bool):
            raise TypeError("Include password must be Boolean.")

        self.validate()

        if not configuration.has_section(self._DATABASE_SECTION):
            configuration.add_section(self._DATABASE_SECTION)

        configuration.set(
            self._DATABASE_SECTION,
            "host",
            self._configuration_value(self.database_host),
        )
        configuration.set(
            self._DATABASE_SECTION,
            "port",
            self._configuration_value(self.database_port),
        )
        configuration.set(
            self._DATABASE_SECTION,
            "name",
            self._configuration_value(self.database_name),
        )
        configuration.set(
            self._DATABASE_SECTION,
            "user",
            self._configuration_value(self.database_user),
        )

        if include_password:
            configuration.set(
                self._DATABASE_SECTION,
                "password",
                self._configuration_value(self.database_password),
            )

            self.logger.warning(
                "The PostgreSQL password has been added to the configuration "
                "in plain text."
            )
        else:
            configuration.remove_option(
                self._DATABASE_SECTION,
                "password",
            )

        if not configuration.has_section(self._SSH_SECTION):
            configuration.add_section(self._SSH_SECTION)

        configuration.set(
            self._SSH_SECTION,
            "host",
            self._configuration_value(self.ssh_host),
        )
        configuration.set(
            self._SSH_SECTION,
            "port",
            self._configuration_value(self.ssh_port),
        )
        configuration.set(
            self._SSH_SECTION,
            "user",
            self._configuration_value(self.ssh_user),
        )
        configuration.set(
            self._SSH_SECTION,
            "local_port",
            self._configuration_value(self.ssh_local_port),
        )
        configuration.set(
            self._SSH_SECTION,
            "identity_file",
            self._configuration_value(self.ssh_identity_file),
        )

        self.logger.debug(
            "PostgreSQL and SSH configuration added to ConfigParser."
        )

        return configuration

    def save_to_ini(
        self,
        file_path: str | Path,
        *,
        include_password: bool = False,
    ) -> Path:
        """Save the connection configuration to an INI file.

        When the destination already exists, it is read first so that sections
        unrelated to PostgreSQL and SSH are retained. The current connection
        values are then applied through ``update_configparser()`` and the
        complete parser is written using UTF-8 encoding.

        By default, the PostgreSQL password is not stored. Enabling
        ``include_password`` writes it as plain text and should therefore be
        used only when the destination file is adequately protected.

        Args:
            file_path:
                Destination INI path.
            include_password:
                Whether to store the PostgreSQL password in the file.

        Returns:
            The absolute path of the INI file written.

        Raises:
            TypeError:
                If ``file_path`` has an invalid type or ``include_password`` is
                not Boolean.
            FileNotFoundError:
                If the destination directory or configured SSH identity file
                does not exist.
            IsADirectoryError:
                If the destination path refers to a directory.
            OSError:
                If an existing file cannot be read or the resulting file
                cannot be written.
            ValueError:
                If the complete configuration is not coherent.
            configparser.Error:
                If an existing INI file is malformed.
        """
        if not isinstance(file_path, (str, Path)):
            raise TypeError("INI file path must be a string or Path.")

        if not isinstance(include_password, bool):
            raise TypeError("Include password must be Boolean.")

        config_path = Path(file_path).expanduser()

        if config_path.exists() and not config_path.is_file():
            raise IsADirectoryError(
                f"INI configuration path is not a file: {config_path}"
            )

        if not config_path.parent.is_dir():
            raise FileNotFoundError(
                f"INI configuration directory not found: {config_path.parent}"
            )

        config_path = config_path.resolve()

        configuration = configparser.ConfigParser(
            interpolation=None,
        )

        if config_path.is_file():
            self.logger.debug(
                "Reading existing INI configuration from: %s",
                config_path,
            )

            with config_path.open(
                mode="r",
                encoding="utf-8",
            ) as configuration_file:
                configuration.read_file(configuration_file)

        self.update_configparser(
            configuration,
            include_password=include_password,
        )

        self.logger.debug(
            "Writing PostgreSQL and SSH configuration to: %s",
            config_path,
        )

        with config_path.open(
            mode="w",
            encoding="utf-8",
        ) as configuration_file:
            configuration.write(configuration_file)

        self.logger.info(
            "PostgreSQL and SSH configuration saved to: %s",
            config_path,
        )

        return config_path

    def validate(self) -> None:
        """Validate the complete PostgreSQL and SSH configuration.

        In addition to the validation performed by individual property
        setters, this method checks relationships between configuration
        properties.

        A direct PostgreSQL configuration is valid when neither an SSH host nor
        an SSH user is supplied. When SSH tunnelling is configured, both
        ``ssh_host`` and ``ssh_user`` must be present. The configured identity
        file, when present, must still identify an existing regular file.

        ``PostgresConnection`` should call this method immediately before
        opening an SSH tunnel or PostgreSQL connection.

        Raises:
            TypeError:
                If any property has an invalid type.
            ValueError:
                If a required value is absent, a port is outside its permitted
                range, or the SSH properties are inconsistent.
            FileNotFoundError:
                If the configured SSH identity file does not exist.
            IsADirectoryError:
                If the configured SSH identity path identifies a directory.
        """
        self._normalise_required_string(
            "database host",
            self.database_host,
        )
        self._validate_port(
            "database port",
            self.database_port,
        )
        self._normalise_required_string(
            "database name",
            self.database_name,
        )
        self._normalise_required_string(
            "database user",
            self.database_user,
        )
        self._validate_password(self.database_password)

        self._normalise_optional_string(
            "SSH host",
            self.ssh_host,
        )
        self._validate_port(
            "SSH port",
            self.ssh_port,
        )
        self._normalise_optional_string(
            "SSH user",
            self.ssh_user,
        )
        self._validate_port(
            "SSH local port",
            self.ssh_local_port,
        )
        self._normalise_identity_file(self.ssh_identity_file)
        self._validate_logger(self.logger)

        if self.ssh_host is not None and self.ssh_user is None:
            raise ValueError(
                "SSH user is required when an SSH host is configured."
            )

        if self.ssh_user is not None and self.ssh_host is None:
            raise ValueError(
                "SSH host is required when an SSH user is configured."
            )

        self.logger.debug(
            "PostgreSQL and SSH configuration validated successfully."
        )

    @classmethod
    def _validate_update_names(
        cls,
        values: Mapping[str, object],
    ) -> None:
        """Validate the property names supplied to an update operation.

        Args:
            values:
                Mapping whose keys identify properties to update.

        Raises:
            TypeError:
                If ``values`` is not a mapping, a key is not a string, or one
                or more keys do not identify supported configuration
                properties.
        """
        if not isinstance(values, Mapping):
            raise TypeError(
                "Configuration values must be supplied as a mapping."
            )

        invalid_keys = [key for key in values if not isinstance(key, str)]

        if invalid_keys:
            formatted_keys = ", ".join(repr(key) for key in invalid_keys)

            raise TypeError(
                "Configuration property names must be strings. "
                f"Invalid {'name' if len(invalid_keys) == 1 else 'names'}: "
                f"{formatted_keys}."
            )

        unexpected_names = sorted(
            property_name
            for property_name in values
            if property_name not in cls._CONFIGURATION_FIELDS
        )

        if unexpected_names:
            formatted_names = ", ".join(
                repr(property_name) for property_name in unexpected_names
            )

            raise TypeError(
                "Unexpected configuration "
                f"{'property' if len(unexpected_names) == 1 else 'properties'}: "
                f"{formatted_names}."
            )

    @classmethod
    def _read_configparser_values(
        cls,
        configuration: configparser.ConfigParser,
    ) -> dict[str, object]:
        """Extract explicitly configured values from a parser.

        Only options present in the ``[Database]`` and ``[SSH]`` sections are
        returned. Missing options are omitted so that applying the result does
        not overwrite existing object values.

        Text values are returned as strings or ``None`` as appropriate.
        PostgreSQL, SSH, and local tunnel ports are converted to integers.

        Args:
            configuration:
                Parser containing the connection sections.

        Returns:
            Dictionary suitable for passing to ``update()``.

        Raises:
            TypeError:
                If ``configuration`` is not a ``ConfigParser`` instance.
            ValueError:
                If a numeric option cannot be converted to an integer.
            configparser.Error:
                If a configured option cannot be read.
        """
        if not isinstance(configuration, configparser.ConfigParser):
            raise TypeError("Configuration must be a ConfigParser instance.")

        values: dict[str, object] = {}

        database_options = {
            "host": "database_host",
            "name": "database_name",
            "password": "database_password",
            "port": "database_port",
            "user": "database_user",
        }

        if configuration.has_section(cls._DATABASE_SECTION):
            for option_name, property_name in database_options.items():
                if not configuration.has_option(
                    cls._DATABASE_SECTION,
                    option_name,
                ):
                    continue

                if option_name == "port":
                    option_value = configuration.getint(
                        cls._DATABASE_SECTION,
                        option_name,
                        raw=True,
                    )
                else:
                    option_value = configuration.get(
                        cls._DATABASE_SECTION,
                        option_name,
                        raw=True,
                    )

                values[property_name] = option_value

        ssh_options = {
            "host": "ssh_host",
            "identity_file": "ssh_identity_file",
            "local_port": "ssh_local_port",
            "port": "ssh_port",
            "user": "ssh_user",
        }

        if configuration.has_section(cls._SSH_SECTION):
            for option_name, property_name in ssh_options.items():
                if not configuration.has_option(
                    cls._SSH_SECTION,
                    option_name,
                ):
                    continue

                if option_name in {"port", "local_port"}:
                    option_value = configuration.getint(
                        cls._SSH_SECTION,
                        option_name,
                        raw=True,
                    )
                else:
                    option_value = cls._optional_configuration_value(
                        configuration,
                        cls._SSH_SECTION,
                        option_name,
                    )

                values[property_name] = option_value

        return values

    @staticmethod
    def _normalise_required_string(
        field_name: str,
        value: str,
    ) -> str:
        """Normalise and validate a required string.

        Surrounding whitespace is removed before the value is returned.

        Args:
            field_name:
                Human-readable name used in validation messages.
            value:
                String to normalise.

        Returns:
            The stripped, non-empty string.

        Raises:
            TypeError:
                If ``field_name`` or ``value`` is not a string.
            ValueError:
                If ``field_name`` or ``value`` is empty after removing
                surrounding whitespace.
        """
        if not isinstance(field_name, str):
            raise TypeError("Field name must be a string.")

        field_name = field_name.strip()

        if not field_name:
            raise ValueError("Field name must not be empty.")

        if not isinstance(value, str):
            raise TypeError(f"{field_name.capitalize()} must be a string.")

        value = value.strip()

        if not value:
            raise ValueError(f"{field_name.capitalize()} must not be empty.")

        return value

    @staticmethod
    def _normalise_optional_string(
        field_name: str,
        value: str | None,
    ) -> str | None:
        """Normalise an optional string.

        Surrounding whitespace is removed. ``None`` and empty strings are
        represented as ``None``.

        Args:
            field_name:
                Human-readable name used in validation messages.
            value:
                Optional string to normalise.

        Returns:
            The stripped string or ``None`` when no value is present.

        Raises:
            TypeError:
                If ``field_name`` is not a string or ``value`` is neither a
                string nor ``None``.
            ValueError:
                If ``field_name`` is empty.
        """
        if not isinstance(field_name, str):
            raise TypeError("Field name must be a string.")

        field_name = field_name.strip()

        if not field_name:
            raise ValueError("Field name must not be empty.")

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name.capitalize()} must be a string or None."
            )

        value = value.strip()

        return value or None

    @staticmethod
    def _validate_password(value: str) -> str:
        """Validate a PostgreSQL password.

        The value is returned unchanged because whitespace may form part of a
        valid password.

        Args:
            value:
                Password to validate.

        Returns:
            The original password.

        Raises:
            TypeError:
                If ``value`` is not a string.
        """
        if not isinstance(value, str):
            raise TypeError("Database password must be a string.")

        return value

    @staticmethod
    def _validate_port(
        field_name: str,
        value: int,
    ) -> int:
        """Validate a TCP port number.

        Boolean values are rejected even though ``bool`` is a subclass of
        ``int`` in Python.

        Args:
            field_name:
                Human-readable name used in validation messages.
            value:
                Port number to validate.

        Returns:
            The validated integer port.

        Raises:
            TypeError:
                If ``field_name`` is not a string or ``value`` is not an
                integer.
            ValueError:
                If ``field_name`` is empty or ``value`` is outside the range
                from 1 to 65535.
        """
        if not isinstance(field_name, str):
            raise TypeError("Field name must be a string.")

        field_name = field_name.strip()

        if not field_name:
            raise ValueError("Field name must not be empty.")

        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{field_name.capitalize()} must be an integer.")

        if value < 1 or value > 65535:
            raise ValueError(
                f"{field_name.capitalize()} must be between 1 and 65535."
            )

        return value

    @staticmethod
    def _normalise_identity_file(
        value: str | Path | None,
    ) -> str | None:
        """Normalise and validate an optional SSH identity-file path.

        User-home markers are expanded and a configured file is converted to
        an absolute path. An absent or empty value is represented as ``None``.

        Args:
            value:
                Optional path to a private SSH identity file.

        Returns:
            Absolute file path represented as a string, or ``None`` when no
            identity file is configured.

        Raises:
            TypeError:
                If ``value`` is neither a string, ``Path``, nor ``None``.
            FileNotFoundError:
                If a non-empty path does not exist.
            IsADirectoryError:
                If the path identifies a directory.
            OSError:
                If the path cannot be expanded or resolved.
        """
        if value is None:
            return None

        if not isinstance(value, (str, Path)):
            raise TypeError(
                "SSH identity file must be a string, Path or None."
            )

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        identity_path = Path(value).expanduser()

        if not identity_path.exists():
            raise FileNotFoundError(
                f"SSH identity file not found: {identity_path}"
            )

        if not identity_path.is_file():
            raise IsADirectoryError(
                f"SSH identity path is not a file: {identity_path}"
            )

        return str(identity_path.resolve())

    @staticmethod
    def _validate_logger(
        value: logging.Logger,
    ) -> logging.Logger:
        """Validate a logger.

        Args:
            value:
                Logger to validate.

        Returns:
            The validated logger.

        Raises:
            TypeError:
                If ``value`` is not a ``logging.Logger`` instance.
        """
        if not isinstance(value, logging.Logger):
            raise TypeError("Logger must be a logging.Logger instance.")

        return value

    @staticmethod
    def _optional_configuration_value(
        configuration: configparser.ConfigParser,
        section: str,
        option: str,
    ) -> str | None:
        """Read an optional text value from a configuration parser.

        Missing sections, missing options, and empty values are represented as
        ``None``.

        Args:
            configuration:
                Parser from which to read the value.
            section:
                INI section name.
            option:
                Option name within the section.

        Returns:
            The stripped value or ``None`` when absent or empty.

        Raises:
            TypeError:
                If the parser, section, or option has an invalid type.
            ValueError:
                If ``section`` or ``option`` is empty.
            configparser.Error:
                If the configured value cannot be read.
        """
        if not isinstance(configuration, configparser.ConfigParser):
            raise TypeError("Configuration must be a ConfigParser instance.")

        if not isinstance(section, str):
            raise TypeError("Configuration section name must be a string.")

        section = section.strip()

        if not section:
            raise ValueError("Configuration section name must not be empty.")

        if not isinstance(option, str):
            raise TypeError("Configuration option name must be a string.")

        option = option.strip()

        if not option:
            raise ValueError("Configuration option name must not be empty.")

        if not configuration.has_section(section):
            return None

        if not configuration.has_option(section, option):
            return None

        value = configuration.get(
            section,
            option,
            raw=True,
        ).strip()

        return value or None

    @staticmethod
    def _configuration_value(value: object | None) -> str:
        """Convert a value into text suitable for an INI option.

        ``None`` is represented as an empty string. Other values are converted
        through their standard string representation.

        Args:
            value:
                Configuration value to convert.

        Returns:
            Text suitable for assignment to a ``ConfigParser`` option.
        """
        if value is None:
            return ""

        return str(value)


class PostgresConnection:
    """Manage a PostgreSQL connection with optional SSH tunnelling.

    The class coordinates the complete lifecycle of a single PostgreSQL
    connection. When the supplied configuration contains an SSH host, it first
    opens a local SSH tunnel and then connects PostgreSQL through that tunnel.
    Otherwise, it connects directly to the configured database server.

    The configuration object is stored by reference rather than copied.
    Consequently, changes made to it before calling ``open()`` are taken into
    account. The complete configuration is validated immediately before any
    external resource is opened.

    The class manages at most one PostgreSQL connection and one SSH process.
    It does not implement connection pooling and is intended for scripts that
    perform a bounded operation and then terminate.

    Instances may be used explicitly through ``open()`` and ``close()``, or as
    context managers. Context-manager usage guarantees that the PostgreSQL
    connection and SSH tunnel are closed even when an exception occurs.

    Example:
        ::

            config = PostgresConnectionConfig(
                database_name="odoo",
                database_user="readonly",
            )

            with PostgresConnection(config) as database:
                with database.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()

    Attributes:
        config:
            Mutable ``PostgresConnectionConfig`` object used when opening the
            SSH tunnel and PostgreSQL connection.
        logger:
            Logger used to report connection, tunnelling, testing, and cleanup
            operations. When no logger is supplied to the constructor, the
            logger associated with ``config`` is used.
        connection:
            Active Psycopg connection, or ``None`` when PostgreSQL is not
            connected.
        ssh_process:
            Active SSH subprocess, or ``None`` when no tunnel is open.
        is_connected:
            Whether an active PostgreSQL connection is currently available.
        is_tunnel_open:
            Whether an SSH tunnel process is currently running.
    """

    __slots__ = (
        "_config",
        "_connection",
        "_logger",
        "_ssh_process",
    )

    def __init__(
        self,
        config: PostgresConnectionConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise the PostgreSQL connection manager.

        No SSH tunnel or PostgreSQL connection is opened during
        initialisation. External resources are opened only by ``open()`` or
        when entering a context-manager block.

        The supplied configuration object is retained by reference. When
        ``logger`` is omitted, the logger associated with the configuration is
        used.

        Args:
            config:
                PostgreSQL and SSH configuration used to establish the
                connection.
            logger:
                Optional logger that overrides ``config.logger`` for
                connection-related messages.

        Raises:
            TypeError:
                If ``config`` is not a ``PostgresConnectionConfig`` instance
                or ``logger`` is neither a ``logging.Logger`` nor ``None``.
        """
        self._connection = None
        self._ssh_process = None

        self.config = config
        self.logger = logger if logger is not None else self.config.logger

    @property
    def config(self) -> PostgresConnectionConfig:
        """Return the PostgreSQL and SSH connection configuration."""
        return self._config

    @config.setter
    def config(
        self,
        value: PostgresConnectionConfig,
    ) -> None:
        """Set the PostgreSQL and SSH connection configuration.

        The configuration may only be replaced while no PostgreSQL connection
        or SSH tunnel is active.

        Args:
            value:
                Configuration object to associate with the manager.

        Raises:
            TypeError:
                If ``value`` is not a ``PostgresConnectionConfig`` instance.
            RuntimeError:
                If a PostgreSQL connection or SSH tunnel is currently active.
        """
        if not isinstance(value, PostgresConnectionConfig):
            raise TypeError(
                "Config must be a PostgresConnectionConfig instance."
            )

        if self.is_connected:
            raise RuntimeError(
                "Configuration cannot be replaced while the PostgreSQL "
                "connection is active."
            )

        if self.is_tunnel_open:
            raise RuntimeError(
                "Configuration cannot be replaced while the SSH tunnel is active."
            )

        self._config = value

    @property
    def logger(self) -> logging.Logger:
        """Return the logger associated with the connection manager."""
        return self._logger

    @logger.setter
    def logger(self, value: logging.Logger) -> None:
        """Associate a logger with the connection manager.

        Args:
            value:
                Logger that will receive connection-related messages.

        Raises:
            TypeError:
                If ``value`` is not a ``logging.Logger`` instance.
        """
        self._logger = self._validate_logger(value)

    @property
    def connection(self) -> psycopg.Connection | None:
        """Return the active PostgreSQL connection, if any."""
        return self._connection

    @property
    def ssh_process(self) -> subprocess.Popen | None:
        """Return the active SSH tunnel process, if any."""
        return self._ssh_process

    @property
    def is_connected(self) -> bool:
        """Return whether a PostgreSQL connection is currently active."""
        return self._connection is not None and not self._connection.closed

    @property
    def is_tunnel_open(self) -> bool:
        """Return whether an SSH tunnel process is currently running."""
        return (
            self._ssh_process is not None and self._ssh_process.poll() is None
        )

    def open(self) -> psycopg.Connection:
        """Open the optional SSH tunnel and PostgreSQL connection.

        The complete configuration is validated before any external resource
        is opened. When SSH tunnelling is configured, the tunnel is started
        first and the method waits until the configured local port accepts
        connections. PostgreSQL is then connected through that local endpoint.

        When no SSH host is configured, PostgreSQL is connected directly to
        ``config.database_host`` and ``config.database_port``.

        If PostgreSQL cannot be connected after an SSH tunnel has been opened,
        the tunnel is closed before the exception is propagated.

        Returns:
            The active Psycopg connection.

        Raises:
            RuntimeError:
                If the manager already has an active PostgreSQL connection or
                SSH tunnel, the SSH executable is unavailable, the tunnel
                terminates prematurely, or its local port does not become
                available.
            TypeError:
                If a configuration value has an invalid type.
            ValueError:
                If the complete configuration is invalid or inconsistent.
            FileNotFoundError:
                If the configured SSH identity file no longer exists.
            IsADirectoryError:
                If the configured SSH identity path identifies a directory.
            OSError:
                If the SSH process cannot be created or a network resource
                cannot be accessed.
            psycopg.Error:
                If the PostgreSQL connection cannot be established.
        """
        if self.is_connected:
            raise RuntimeError("The PostgreSQL connection is already active.")

        if self.is_tunnel_open:
            raise RuntimeError("The SSH tunnel is already active.")

        self.config.validate()

        # Discard references to resources that have already terminated or closed.
        if self._connection is not None and self._connection.closed:
            self._connection = None

        if (
            self._ssh_process is not None
            and self._ssh_process.poll() is not None
        ):
            self._ssh_process = None

        try:
            self._open_ssh_tunnel()
            return self._connect_database()

        except BaseException:
            try:
                self._close_database()
            except Exception:
                self.logger.exception(
                    "An error occurred while cleaning up the PostgreSQL "
                    "connection after a failed open operation."
                )

            try:
                self._close_ssh_tunnel()
            except Exception:
                self.logger.exception(
                    "An error occurred while cleaning up the SSH tunnel "
                    "after a failed open operation."
                )

            raise

    def close(self) -> None:
        """Close the PostgreSQL connection and optional SSH tunnel.

        PostgreSQL is closed before the SSH tunnel because the database
        connection may depend on that tunnel. The method is idempotent and may
        safely be called when one or both resources are already closed.

        Cleanup failures do not prevent the method from attempting to close the
        remaining resource.

        Raises:
            OSError:
                If the SSH process cannot be terminated or inspected.
            psycopg.Error:
                If the PostgreSQL connection cannot be closed cleanly.
        """
        first_error: Exception | None = None

        try:
            self._close_database()
        except Exception as error:
            first_error = error

            self.logger.debug(
                "PostgreSQL cleanup failed.",
                exc_info=True,
            )

        try:
            self._close_ssh_tunnel()
        except Exception as error:
            if first_error is None:
                first_error = error
            else:
                self.logger.error(
                    "The SSH tunnel could not be closed after PostgreSQL "
                    "cleanup had also failed: %s",
                    error,
                )

            self.logger.debug(
                "SSH tunnel cleanup failed.",
                exc_info=True,
            )

        if first_error is not None:
            raise first_error

    def test_connection(self) -> dict[str, object]:
        """Test the active PostgreSQL connection.

        The method executes a lightweight diagnostic query and returns
        information identifying the reached PostgreSQL database, user, and
        server version. It does not open or close the connection itself.

        Returns:
            A dictionary containing the diagnostic values returned by
            PostgreSQL.

        Raises:
            RuntimeError:
                If no active PostgreSQL connection is available or the
                diagnostic query produces no result.
            psycopg.Error:
                If the diagnostic query cannot be executed.
        """
        if not self.is_connected:
            raise RuntimeError(
                "A PostgreSQL connection must be active before it can be tested."
            )

        connection = self._connection

        if connection is None:
            raise RuntimeError("The PostgreSQL connection is not available.")

        query = """
            SELECT
                current_database() AS database_name,
                current_user AS database_user,
                inet_server_addr()::text AS server_address,
                inet_server_port() AS server_port,
                version() AS server_version
        """

        self.logger.debug("Testing the PostgreSQL connection.")

        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                "The PostgreSQL connection test produced no result."
            )

        test_result = dict(result)

        self.logger.info(
            "PostgreSQL connection test completed successfully for database "
            "'%s' as user '%s'.",
            test_result["database_name"],
            test_result["database_user"],
        )

        return test_result

    def __enter__(self) -> Self:
        """Open the resources and return this connection manager.

        Returns:
            This instance after its PostgreSQL connection has been opened.

        Raises:
            RuntimeError:
                If the manager already has active resources or the SSH tunnel
                cannot be established.
            TypeError:
                If a configuration value has an invalid type.
            ValueError:
                If the complete configuration is invalid or inconsistent.
            OSError:
                If an SSH or network operation fails.
            psycopg.Error:
                If PostgreSQL cannot be connected.
        """
        self.open()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close all resources when leaving a context-manager block.

        The original exception, when present, is not suppressed. When cleanup
        also fails while another exception is already active, the cleanup error
        is recorded in the logger so that it does not replace the original
        exception.

        Args:
            exception_type:
                Type of the exception raised inside the context, or ``None``.
            exception_value:
                Exception raised inside the context, or ``None``.
            traceback:
                Traceback associated with the exception, or ``None``.
        """
        if exception_type is None:
            self.close()
            return

        try:
            self.close()
        except Exception:
            self.logger.exception(
                "An error occurred while closing PostgreSQL and SSH resources "
                "after another exception."
            )

    def _open_ssh_tunnel(self) -> subprocess.Popen | None:
        """Open the configured SSH tunnel.

        When no SSH host is configured, the method performs no external
        operation and returns ``None``.

        The tunnel binds only to the local loopback interface and forwards the
        configured local port to the PostgreSQL host and port as seen from the
        SSH server. The method waits until the local endpoint accepts
        connections before returning.

        Returns:
            The active SSH process, or ``None`` when tunnelling is disabled.

        Raises:
            RuntimeError:
                If a tunnel is already active, the SSH executable is not
                available, the tunnel terminates prematurely, or the local
                forwarded port does not become available.
            OSError:
                If the SSH process cannot be created.
        """
        if self.config.ssh_host is None:
            self.logger.debug("SSH tunnelling is not configured.")
            return None

        if self.is_tunnel_open:
            raise RuntimeError("The SSH tunnel is already active.")

        # Discard a reference to a process that has already terminated.
        if self._ssh_process is not None:
            self._ssh_process = None

        self._ensure_local_port_available(
            "127.0.0.1",
            self.config.ssh_local_port,
        )

        command = self._build_ssh_command()

        self.logger.info(
            "Opening SSH tunnel through %s:%d.",
            self.config.ssh_host,
            self.config.ssh_port,
        )

        self.logger.debug(
            "Forwarding 127.0.0.1:%d to %s:%d through SSH.",
            self.config.ssh_local_port,
            self.config.database_host,
            self.config.database_port,
        )

        try:
            self._ssh_process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                "The SSH executable was not found. Ensure that OpenSSH "
                "is installed and available in PATH."
            ) from error

        try:
            tunnel_available = self._wait_for_local_port(
                "127.0.0.1",
                self.config.ssh_local_port,
            )
        except BaseException:
            try:
                self._close_ssh_tunnel()
            except Exception:
                self.logger.debug(
                    "SSH tunnel cleanup failed after an error while waiting "
                    "for the local port.",
                    exc_info=True,
                )

            raise

        if not tunnel_available:
            return_code = self._ssh_process.poll()

            try:
                self._close_ssh_tunnel()
            except Exception:
                self.logger.debug(
                    "SSH tunnel cleanup failed after the tunnel could not "
                    "be established.",
                    exc_info=True,
                )

            if return_code is not None:
                raise RuntimeError(
                    "The SSH tunnel process terminated with exit status "
                    f"{return_code}."
                )

            raise RuntimeError(
                "The SSH tunnel could not be established before the timeout "
                "expired."
            )

        self.logger.info(
            "SSH tunnel established on 127.0.0.1:%d.",
            self.config.ssh_local_port,
        )

        return self._ssh_process

    def _build_ssh_command(self) -> list[str]:
        """Build the command used to create the SSH tunnel.

        The command uses local port forwarding, disables remote command
        execution, requests failure when port forwarding cannot be
        established, and configures connection-liveness checks. The optional
        SSH identity file is included when configured.

        Returns:
            Command and arguments suitable for ``subprocess.Popen``.

        Raises:
            ValueError:
                If SSH tunnelling is not completely configured.
        """
        if self.config.ssh_host is None:
            raise ValueError(
                "SSH host is required to build an SSH tunnel command."
            )

        if self.config.ssh_user is None:
            raise ValueError(
                "SSH user is required to build an SSH tunnel command."
            )

        local_forwarding = (
            f"127.0.0.1:{self.config.ssh_local_port}:"
            f"{self.config.database_host}:{self.config.database_port}"
        )

        destination = f"{self.config.ssh_user}@{self.config.ssh_host}"

        command = [
            "ssh",
            "-N",
            "-T",
            "-p",
            str(self.config.ssh_port),
            "-L",
            local_forwarding,
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ServerAliveInterval=30",
            "-o",
            "ServerAliveCountMax=3",
        ]

        if self.config.ssh_identity_file is not None:
            command.extend(
                [
                    "-i",
                    self.config.ssh_identity_file,
                ]
            )

        command.append(destination)

        return command

    @staticmethod
    def _ensure_local_port_available(
        host: str,
        port: int,
    ) -> None:
        """Ensure that a local TCP port is available for SSH forwarding.

        Args:
            host:
                Local interface on which the SSH tunnel will listen.
            port:
                Local TCP port to reserve for the tunnel.

        Raises:
            TypeError:
                If ``host`` or ``port`` has an invalid type.
            ValueError:
                If ``host`` is empty or ``port`` is outside the valid TCP
                range.
            RuntimeError:
                If another process is already using the requested endpoint.
        """
        if not isinstance(host, str):
            raise TypeError("Host must be a string.")

        host = host.strip()

        if not host:
            raise ValueError("Host must not be empty.")

        if isinstance(port, bool) or not isinstance(port, int):
            raise TypeError("Port must be an integer.")

        if port < 1 or port > 65535:
            raise ValueError("Port must be between 1 and 65535.")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as local_socket:
            try:
                local_socket.bind((host, port))
            except OSError as error:
                raise RuntimeError(
                    "Local SSH tunnel endpoint is already in use: "
                    f"{host}:{port}."
                ) from error

    def _wait_for_local_port(
        self,
        host: str,
        port: int,
        timeout: float = 15.0,
    ) -> bool:
        """Wait until a local TCP port accepts connections.

        The SSH process is inspected while waiting. The method returns
        immediately with ``False`` if that process terminates before the local
        endpoint becomes available.

        Args:
            host:
                Local interface on which the forwarded port should listen.
            port:
                Local TCP port to test.
            timeout:
                Maximum number of seconds to wait.

        Returns:
            ``True`` when the endpoint becomes available within the timeout;
            otherwise, ``False``.

        Raises:
            TypeError:
                If ``host``, ``port``, or ``timeout`` has an invalid type.
            ValueError:
                If ``host`` is empty, ``port`` is outside the valid TCP range,
                or ``timeout`` is not positive.
            OSError:
                If the SSH process cannot be inspected.
        """
        if not isinstance(host, str):
            raise TypeError("Host must be a string.")

        host = host.strip()

        if not host:
            raise ValueError("Host must not be empty.")

        if isinstance(port, bool) or not isinstance(port, int):
            raise TypeError("Port must be an integer.")

        if port < 1 or port > 65535:
            raise ValueError("Port must be between 1 and 65535.")

        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("Timeout must be a number.")

        timeout = float(timeout)

        if timeout <= 0:
            raise ValueError("Timeout must be greater than zero.")

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if (
                self._ssh_process is not None
                and self._ssh_process.poll() is not None
            ):
                return False

            try:
                with socket.create_connection(
                    (host, port),
                    timeout=min(0.5, timeout),
                ):
                    return True
            except OSError:
                time.sleep(0.2)

        return False

    def _resolve_database_endpoint(self) -> tuple[str, int]:
        """Return the endpoint Psycopg must use.

        When SSH tunnelling is enabled, the returned endpoint is the local
        loopback address and configured SSH local port. Otherwise, it is the
        PostgreSQL host and port configured for direct access.

        Returns:
            A tuple containing the connection host and TCP port.
        """
        if self.config.ssh_host is not None:
            return (
                "127.0.0.1",
                self.config.ssh_local_port,
            )

        return (
            self.config.database_host,
            self.config.database_port,
        )

    def _connect_database(self) -> psycopg.Connection:
        """Connect to the configured PostgreSQL database.

        The connection endpoint is obtained from
        ``_resolve_database_endpoint()`` so that the same operation supports
        both direct and SSH-tunnelled access.

        The resulting connection is stored by the manager and returned to the
        caller.

        Returns:
            The active Psycopg connection.

        Raises:
            RuntimeError:
                If a PostgreSQL connection is already active or SSH tunnelling
                is configured but its tunnel has not been opened.
            psycopg.Error:
                If PostgreSQL cannot be connected.
        """
        if self.is_connected:
            raise RuntimeError("The PostgreSQL connection is already active.")

        if self.config.ssh_host is not None and not self.is_tunnel_open:
            raise RuntimeError(
                "The SSH tunnel must be open before connecting to PostgreSQL."
            )

        # Discard a reference to a connection that is already closed.
        if self._connection is not None and self._connection.closed:
            self._connection = None

        connection_host, connection_port = self._resolve_database_endpoint()

        self.logger.info(
            "Connecting to PostgreSQL database '%s' on %s:%d.",
            self.config.database_name,
            connection_host,
            connection_port,
        )

        self._connection = psycopg.connect(
            host=connection_host,
            port=connection_port,
            dbname=self.config.database_name,
            user=self.config.database_user,
            password=self.config.database_password,
            autocommit=True,
        )

        self.logger.info("PostgreSQL connection established.")

        return self._connection

    def _close_database(self) -> None:
        """Close the active PostgreSQL connection.

        The method is idempotent. After the connection is closed, the internal
        reference is reset to ``None``.

        Raises:
            psycopg.Error:
                If the connection cannot be closed cleanly.
        """
        connection = self._connection

        if connection is None:
            return

        if connection.closed:
            self._connection = None
            return

        self.logger.debug("Closing the PostgreSQL connection.")

        try:
            connection.close()
        finally:
            if connection.closed:
                self._connection = None

        self.logger.info("PostgreSQL connection closed.")

    def _close_ssh_tunnel(self) -> None:
        """Close the active SSH tunnel.

        The method first requests orderly process termination. If the process
        does not finish within the permitted interval, it is forcibly killed.
        The method is idempotent and resets the internal process reference to
        ``None`` after cleanup.

        Raises:
            OSError:
                If the SSH process cannot be inspected, terminated, or killed.
            subprocess.TimeoutExpired:
                If the process does not terminate within the configured
                waiting periods.
        """
        ssh_process = self._ssh_process

        if ssh_process is None:
            return

        self.logger.debug("Closing the SSH tunnel.")

        if ssh_process.poll() is None:
            ssh_process.terminate()

            try:
                ssh_process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.logger.warning(
                    "The SSH tunnel did not terminate normally; "
                    "forcing process termination."
                )

                ssh_process.kill()
                ssh_process.wait(timeout=5.0)

        self._ssh_process = None
        self.logger.info("SSH tunnel closed.")

    @staticmethod
    def _validate_logger(
        value: logging.Logger,
    ) -> logging.Logger:
        """Validate a logger.

        Args:
            value:
                Logger to validate.

        Returns:
            The validated logger.

        Raises:
            TypeError:
                If ``value`` is not a ``logging.Logger`` instance.
        """
        if not isinstance(value, logging.Logger):
            raise TypeError("Logger must be a logging.Logger instance.")

        return value


def add_connection_arguments(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Add PostgreSQL and SSH connection arguments to a parser.

    The function adds the ``Database`` and ``SSH tunnel`` argument groups.
    Argument defaults are suppressed so that omitted command-line options do
    not overwrite values already present in a ``PostgresConnectionConfig``
    object, including values loaded from an INI file.

    The resulting namespace contains only the connection options explicitly
    supplied by the user. Its values may therefore be applied directly through
    ``PostgresConnectionConfig.update()``.

    Args:
        parser:
            Argument parser to which the connection arguments will be added.

    Returns:
        The same ``ArgumentParser`` instance after the argument groups have
        been added.

    Raises:
        TypeError:
            If ``parser`` is not an ``argparse.ArgumentParser`` instance.
    """
    if not isinstance(parser, argparse.ArgumentParser):
        raise TypeError("Parser must be an argparse.ArgumentParser instance.")

    database_group = parser.add_argument_group(
        title="Database",
        description="PostgreSQL database connection configuration.",
    )

    database_group.add_argument(
        "-dh",
        "--database-host",
        default=argparse.SUPPRESS,
        metavar="HOST",
        help=(
            "PostgreSQL server host. When an SSH tunnel is used, this is "
            "the database host as seen from the SSH server. "
            "Default: localhost."
        ),
    )

    database_group.add_argument(
        "-dp",
        "--database-port",
        default=argparse.SUPPRESS,
        type=int,
        metavar="PORT",
        help="PostgreSQL server port. Default: 5432.",
    )

    database_group.add_argument(
        "-dn",
        "--database-name",
        default=argparse.SUPPRESS,
        metavar="NAME",
        help="PostgreSQL database name. Default: postgres.",
    )

    database_group.add_argument(
        "-du",
        "--database-user",
        default=argparse.SUPPRESS,
        metavar="USER",
        help="PostgreSQL user name. Default: postgres.",
    )

    database_group.add_argument(
        "-dw",
        "--database-password",
        default=argparse.SUPPRESS,
        metavar="PASSWORD",
        help=(
            "PostgreSQL password. Supplying passwords on the command line "
            "may expose them to other users or process-monitoring tools."
        ),
    )

    ssh_group = parser.add_argument_group(
        title="SSH tunnel",
        description="Optional SSH tunnel configuration.",
    )

    ssh_group.add_argument(
        "-sh",
        "--ssh-host",
        default=argparse.SUPPRESS,
        metavar="HOST",
        help=(
            "SSH server used to reach PostgreSQL. When omitted, PostgreSQL "
            "is accessed directly."
        ),
    )

    ssh_group.add_argument(
        "-sp",
        "--ssh-port",
        default=argparse.SUPPRESS,
        type=int,
        metavar="PORT",
        help="SSH server port. Default: 22.",
    )

    ssh_group.add_argument(
        "-su",
        "--ssh-user",
        default=argparse.SUPPRESS,
        metavar="USER",
        help="SSH user name.",
    )

    ssh_group.add_argument(
        "-slp",
        "--ssh-local-port",
        default=argparse.SUPPRESS,
        type=int,
        metavar="PORT",
        help="Local port assigned to the SSH tunnel. Default: 5433.",
    )

    ssh_group.add_argument(
        "-si",
        "--ssh-identity-file",
        default=argparse.SUPPRESS,
        metavar="FILE_PATH",
        help="Path to the private SSH identity file.",
    )

    return parser


def main(arguments: list[str] | None = None) -> int:
    """Test a direct or SSH-tunnelled PostgreSQL connection.

    The function creates a default ``PostgresConnectionConfig`` object,
    optionally updates it from an INI file, and finally applies PostgreSQL and
    SSH values explicitly supplied on the command line. Command-line values
    therefore take precedence over INI values, while omitted options preserve
    the existing configuration.

    After resolving and validating the configuration, the function opens the
    optional SSH tunnel and PostgreSQL connection, executes the diagnostic
    query provided by ``PostgresConnection.test_connection()``, displays the
    result, and closes all resources.

    Args:
        arguments:
            Command-line arguments to process. When ``None``, the arguments
            received by the Python process are used.

    Returns:
        Zero when the connection test succeeds; otherwise, one.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Test a PostgreSQL connection directly or through an SSH tunnel."
        ),
    )

    parser.add_argument(
        "-c",
        "--config-file",
        default=None,
        metavar="FILE_PATH",
        help=(
            "Optional INI file containing [Database] and [SSH] sections. "
            "Explicit command-line options take precedence over its values."
        ),
    )

    verbosity_group = parser.add_mutually_exclusive_group()

    verbosity_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display informational messages.",
    )

    verbosity_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Display only errors.",
    )

    add_connection_arguments(parser)

    namespace = parser.parse_args(arguments)

    log_level = logging.WARNING

    if namespace.verbose:
        log_level = logging.INFO
    elif namespace.quiet:
        log_level = logging.ERROR

    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    logger = logging.getLogger(__name__)

    try:
        config = PostgresConnectionConfig(
            logger=logger,
        )

        if namespace.config_file is not None:
            config.update_from_ini(namespace.config_file)

        connection_values = {
            property_name: value
            for property_name, value in vars(namespace).items()
            if property_name in PostgresConnectionConfig._CONFIGURATION_FIELDS
        }

        config.update(**connection_values)

        with PostgresConnection(
            config,
            logger=logger,
        ) as database:
            result = database.test_connection()

        print("PostgreSQL connection successful.")
        print(f"Database: {result['database_name']}")
        print(f"User: {result['database_user']}")
        print(
            "Server: "
            f"{result['server_address'] or '<local or unavailable>'}"
            f":{result['server_port'] or '<unavailable>'}"
        )
        print(f"Version: {result['server_version']}")

    except (
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
        configparser.Error,
        psycopg.Error,
    ) as error:
        logger.error("%s", error)
        logger.debug(
            "PostgreSQL connection test failed.",
            exc_info=True,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
