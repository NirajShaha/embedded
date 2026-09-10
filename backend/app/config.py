from pathlib import Path
from typing import Literal

from pydantic import (
    Field,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


ENV_FILE = (
    Path(__file__).resolve().parent.parent
    / ".env"
)


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Security-sensitive values must be supplied through environment
    variables or the backend .env file.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    database_url: str = Field(
        min_length=1,
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
        ]
    )

    jwt_secret_key: str = Field(
        min_length=32,
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = Field(
        default=60,
        gt=0,
        le=1440,
    )

    seed_default_users: bool = True

    initial_admin_username: str = Field(
        default="admin",
        min_length=1,
        max_length=255,
    )

    initial_admin_password: str = Field(
        min_length=12,
    )

    initial_user_username: str = Field(
        default="user",
        min_length=1,
        max_length=255,
    )

    initial_user_password: str = Field(
        min_length=12,
    )

    @field_validator(
        "database_url",
    )
    @classmethod
    def validate_database_url(
        cls,
        value: str,
    ):
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "DATABASE_URL is required"
            )

        if not normalized_value.startswith(
            "mysql://"
        ):
            raise ValueError(
                "DATABASE_URL must use the "
                "mysql:// Prisma connection format"
            )

        return normalized_value

    @field_validator(
        "cors_origins",
        mode="before",
    )
    @classmethod
    def parse_cors_origins(
        cls,
        value,
    ):
        """
        Accept either a JSON array from .env or a comma-separated string.
        """

        if isinstance(value, str):
            stripped_value = value.strip()

            if (
                stripped_value.startswith("[")
                and stripped_value.endswith("]")
            ):
                return value

            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return value

    @field_validator(
        "cors_origins",
    )
    @classmethod
    def normalize_cors_origins(
        cls,
        values: list[str],
    ):
        normalized_origins = sorted(
            {
                origin.strip().rstrip("/")
                for origin in values
                if origin.strip()
            }
        )

        if not normalized_origins:
            raise ValueError(
                "At least one CORS origin is required"
            )

        if "*" in normalized_origins:
            raise ValueError(
                "Wildcard CORS origins are not allowed "
                "when credentials are enabled"
            )

        return normalized_origins

    @field_validator(
        "jwt_secret_key",
    )
    @classmethod
    def validate_jwt_secret(
        cls,
        value: str,
    ):
        normalized_value = value.strip()

        weak_values = {
            "change-this-development-secret-before-deployment",
            "replace-this-with-a-long-random-secret",
            "replace-with-a-long-random-secret",
            "replace-with-a-random-secret-of-at-least-32-characters",
            "replace_with_a_random_secret_of_at_least_32_characters",
            "replace_with_a_random_secret_of_at_least_32_characters_here",
            "paste_a_real_random_secret_here",
            "secret",
            "password",
        }

        if (
            normalized_value.lower()
            in weak_values
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be replaced "
                "with a strong random secret"
            )

        return normalized_value

    @field_validator(
        "jwt_algorithm",
    )
    @classmethod
    def validate_jwt_algorithm(
        cls,
        value: str,
    ):
        normalized_value = (
            value.strip().upper()
        )

        allowed_algorithms = {
            "HS256",
            "HS384",
            "HS512",
        }

        if (
            normalized_value
            not in allowed_algorithms
        ):
            raise ValueError(
                "JWT_ALGORITHM must be one of: "
                "HS256, HS384, or HS512"
            )

        return normalized_value

    @field_validator(
        "initial_admin_username",
        "initial_user_username",
    )
    @classmethod
    def normalize_username(
        cls,
        value: str,
    ):
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "Initial usernames cannot be blank"
            )

        return normalized_value

    @field_validator(
        "initial_admin_password",
        "initial_user_password",
    )
    @classmethod
    def validate_initial_password(
        cls,
        value: str,
    ):
        if value != value.strip():
            raise ValueError(
                "Initial passwords cannot start "
                "or end with spaces"
            )

        return value

    @model_validator(
        mode="after",
    )
    def validate_environment_security(
        self,
    ):
        if (
            self.initial_admin_username
            == self.initial_user_username
        ):
            raise ValueError(
                "The initial admin and user "
                "usernames must be different"
            )

        if (
            self.initial_admin_password
            == self.initial_user_password
        ):
            raise ValueError(
                "The initial admin and user "
                "passwords must be different"
            )

        if (
            self.initial_admin_password
            == self.initial_admin_username
        ):
            raise ValueError(
                "The initial admin password cannot "
                "match the admin username"
            )

        if (
            self.initial_user_password
            == self.initial_user_username
        ):
            raise ValueError(
                "The initial user password cannot "
                "match the user username"
            )

        if (
            self.environment
            == "production"
        ):
            if self.seed_default_users:
                raise ValueError(
                    "SEED_DEFAULT_USERS must be false "
                    "in production"
                )

            local_origins = {
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            }

            if any(
                origin in local_origins
                for origin
                in self.cors_origins
            ):
                raise ValueError(
                    "Production CORS_ORIGINS cannot "
                    "contain localhost addresses"
                )

        return self


settings = Settings()