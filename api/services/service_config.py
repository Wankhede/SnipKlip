import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

import yaml
from django.db import transaction

from backend.models import Service


ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml"}
MAX_CONFIG_SIZE = 1024 * 1024
REQUIRED_FIELDS = {"service_name", "price", "duration_in_minutes"}


class ServiceConfigError(ValueError):
    pass


def _parse_document(filename, text):
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ServiceConfigError("Only .json, .yaml, and .yml files are allowed.")

    try:
        if extension == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except json.JSONDecodeError as exc:
        raise ServiceConfigError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}."
        ) from exc
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        detail = getattr(exc, "problem", None) or "unable to parse YAML"
        raise ServiceConfigError(f"Invalid YAML{location}: {detail}.") from exc


def _validate_service(raw_service, index):
    prefix = f"Service {index}"
    if not isinstance(raw_service, dict):
        raise ServiceConfigError(f"{prefix}: expected an object with service fields.")

    fields = set(raw_service)
    missing = REQUIRED_FIELDS - fields
    unknown = fields - REQUIRED_FIELDS
    if missing:
        raise ServiceConfigError(f"{prefix}: missing {', '.join(sorted(missing))}.")
    if unknown:
        raise ServiceConfigError(f"{prefix}: unknown field(s): {', '.join(sorted(unknown))}.")

    name = raw_service["service_name"]
    if not isinstance(name, str) or not name.strip():
        raise ServiceConfigError(f"{prefix}: service_name must be a non-empty string.")
    name = name.strip()
    if len(name) > 100:
        raise ServiceConfigError(f"{prefix}: service_name cannot exceed 100 characters.")

    price_value = raw_service["price"]
    if isinstance(price_value, bool):
        raise ServiceConfigError(f"{prefix}: price must be a non-negative number.")
    try:
        price = Decimal(str(price_value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ServiceConfigError(f"{prefix}: price must be a non-negative number.") from exc
    if (
        not price.is_finite()
        or price < 0
        or price > Decimal("9999999999.99")
        or price.as_tuple().exponent < -2
    ):
        raise ServiceConfigError(
            f"{prefix}: price must be between 0 and 9999999999.99 with at most two decimal places."
        )

    duration = raw_service["duration_in_minutes"]
    if isinstance(duration, bool) or not isinstance(duration, int) or not 1 <= duration <= 1440:
        raise ServiceConfigError(f"{prefix}: duration_in_minutes must be an integer from 1 to 1440.")

    return {
        "service_name": name,
        "price": price,
        "duration_in_minutes": duration,
    }


def parse_service_config(uploaded_file):
    if not uploaded_file:
        raise ServiceConfigError("Choose a services configuration file.")
    if uploaded_file.size > MAX_CONFIG_SIZE:
        raise ServiceConfigError("The configuration file must be 1 MB or smaller.")

    raw_content = uploaded_file.read(MAX_CONFIG_SIZE + 1)
    try:
        text = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ServiceConfigError("The configuration file must use UTF-8 text encoding.") from exc

    document = _parse_document(uploaded_file.name, text)
    if not isinstance(document, list) or not document:
        raise ServiceConfigError("The configuration must be a non-empty list of services.")

    services = [_validate_service(raw_service, index) for index, raw_service in enumerate(document, 1)]
    normalized_names = [service["service_name"].casefold() for service in services]
    if len(normalized_names) != len(set(normalized_names)):
        raise ServiceConfigError("Each service_name must be unique within the file.")
    return services


@transaction.atomic
def synchronize_services(branch, services):
    created_count = 0
    updated_count = 0

    for service_data in services:
        service = Service.objects.filter(
            branch=branch,
            name__iexact=service_data["service_name"],
        ).first()
        if service:
            service.name = service_data["service_name"]
            service.user = branch.salon
            service.price = service_data["price"]
            service.time_for_each_service = service_data["duration_in_minutes"]
            service.save(update_fields=["name", "user", "price", "time_for_each_service"])
            updated_count += 1
        else:
            Service.objects.create(
                branch=branch,
                name=service_data["service_name"],
                user=branch.salon,
                price=service_data["price"],
                time_for_each_service=service_data["duration_in_minutes"],
            )
            created_count += 1

    return {
        "created": created_count,
        "updated": updated_count,
        "total": len(services),
    }
