"""Small JSON API for the packaging rule engine."""

import json
import math
import csv
import os
from dataclasses import asdict, replace
from functools import lru_cache
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from src.database.connection import DB_PATH
from src.rule_engine.engine import RuleEngine
from src.rule_engine.food import create_food_profile_from_dict, load_food_profiles_from_db, load_food_profiles_from_sources
from src.rule_engine.materials import create_material_from_dict, load_materials_from_db, load_materials_from_csv
from src.rule_engine.models import PackagingContext

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _load_foods():
    food_csv = ROOT / "data" / "raw" / "food_ctegory" / "index.csv"
    requirement_csv = ROOT / "data" / "raw" / "packaging_materials" / "food_requirements.csv"
    if food_csv.exists() and requirement_csv.exists():
        return load_food_profiles_from_sources(str(food_csv), str(requirement_csv))
    if DB_PATH.exists():
        return load_food_profiles_from_db(str(DB_PATH))
    return None


@lru_cache(maxsize=1)
def _load_categories():
    path = ROOT / "data" / "raw" / "packaging_materials" / "food_requirements.csv"
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    def optional_number(value):
        try:
            return float(value) if value not in (None, "") else None
        except ValueError:
            return None
    return [
        {
            "name": row.get("Food_Category"),
            "min_otr": optional_number(row.get("Min_OTR")),
            "max_otr": optional_number(row.get("Max_OTR")),
            "min_wvtr": optional_number(row.get("Min_WVTR")),
            "max_wvtr": optional_number(row.get("Max_WVTR")),
            "description": row.get("Description") or "",
        }
        for row in rows if row.get("Food_Category")
    ]


def _json_value(value: Any):
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, default=_json_value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def _foods(self):
        return _load_foods()

    def _categories(self):
        return _load_categories()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/api", "/api/", "/api/health"):
            return self._send(200, {"ok": True, "service": "packaging-rule-engine", "database_exists": DB_PATH.exists()})
        if parsed.path == "/api/foods":
            foods = self._foods()
            if foods is None:
                return self._send(503, {"error": "Food data unavailable. Prepare processed CSV or seed the database."})
            query = parse_qs(parsed.query)
            term = query.get("q", [""])[0].strip().casefold()
            try:
                limit = max(1, min(int(query.get("limit", ["50"])[0]), 200))
                offset = int(query.get("offset", ["0"])[0])
            except ValueError:
                return self._send(400, {"error": "limit and offset must be integers"})
            if offset < 0:
                return self._send(400, {"error": "offset must be non-negative"})
            filtered = [
                f for f in foods
                if not term or term in f.name.casefold() or term in f.code.casefold()
                or term in str(f.raw_attributes.get("grup") or "").casefold()
            ]
            return self._send(200, {"count": len(filtered), "foods": filtered[offset:offset + limit]})
        if parsed.path == "/api/categories":
            categories = self._categories()
            if categories is None:
                return self._send(503, {"error": "Food requirement categories are unavailable."})
            return self._send(200, {"count": len(categories), "categories": categories})
        return self._send(404, {"error": "Not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/recommend":
            return self._send(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 64_000:
                return self._send(413, {"error": "Request body too large"})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                return self._send(400, {"error": "Request body must be a JSON object"})
            foods = self._foods()
            if foods is None:
                return self._send(503, {"error": "Food data unavailable. Prepare processed CSV or seed the database."})
            food_code = str(payload.get("food_code", "")).strip()
            if food_code:
                food = next((item for item in foods if item.code == food_code), None)
                if food is None:
                    return self._send(404, {"error": f"Unknown food_code: {food_code}"})
                if not food.food_category or not any((food.min_otr, food.max_otr, food.min_wvtr, food.max_wvtr)):
                    return self._send(400, {"error": "This food has no mapped barrier range. Choose a category in manual entry before checking materials."})
            else:
                manual = payload.get("manual_food")
                if not isinstance(manual, dict):
                    return self._send(400, {"error": "food_code or manual_food is required"})
                category_name = str(manual.get("food_category", "")).strip()
                category = next((item for item in self._categories() or [] if item["name"] == category_name), None)
                if category is None:
                    return self._send(400, {"error": "Choose a valid packaging category for the unlisted food."})
                food = create_food_profile_from_dict({
                    "code": "MANUAL",
                    "name": str(manual.get("name") or "Unlisted food").strip()[:120],
                    "packaging_category": category["name"],
                    "water": manual.get("water_pct"),
                    "fatce": manual.get("fat_pct"),
                    "Min_OTR": category["min_otr"],
                    "Max_OTR": category["max_otr"],
                    "Min_WVTR": category["min_wvtr"],
                    "Max_WVTR": category["max_wvtr"],
                    "Description": category["description"],
                })
            barrier_limits = payload.get("barrier_limits", {})
            if not isinstance(barrier_limits, dict):
                return self._send(400, {"error": "barrier_limits must be a JSON object"})
            limits = {}
            for metric, attr in (("otr", "otr"), ("wvtr", "wvtr")):
                key = f"max_{metric}"
                if key not in barrier_limits:
                    continue
                target = barrier_limits[key]
                if isinstance(target, bool) or not isinstance(target, (int, float)) or not math.isfinite(target):
                    return self._send(400, {"error": f"{key} must be a finite number"})
                minimum = getattr(food, f"min_{attr}")
                maximum = getattr(food, f"max_{attr}")
                if maximum is None or target < (minimum or 0) or target > maximum:
                    return self._send(400, {"error": f"{key} must stay within this food's recorded range"})
                limits[f"max_{attr}"] = float(target)
            if limits:
                food = replace(food, **limits)
            if payload.get("materials"):
                materials = [create_material_from_dict(row) for row in payload["materials"]]
            elif DB_PATH.exists():
                materials = load_materials_from_db(str(DB_PATH))
            else:
                csv_path = ROOT / "data" / "raw" / "packaging_materials" / "materials_permeability.csv"
                if not csv_path.exists():
                    return self._send(503, {"error": "Material data unavailable; provide materials or seed the database."})
                materials = load_materials_from_csv(str(csv_path))
            if payload.get("materials") is not None and not isinstance(payload.get("materials"), list):
                return self._send(400, {"error": "materials must be a JSON array"})
            if not all(isinstance(row, dict) for row in payload.get("materials", [])):
                return self._send(400, {"error": "Each supplied material must be a JSON object"})
            context_data = payload.get("context") or {}
            if not isinstance(context_data, dict):
                return self._send(400, {"error": "context must be a JSON object"})
            allowed = PackagingContext.__dataclass_fields__.keys()
            context = PackagingContext(**{key: val for key, val in context_data.items() if key in allowed})
            top_k = payload.get("top_k", 10)
            if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 0:
                return self._send(400, {"error": "top_k must be a non-negative integer"})
            use_clustering = payload.get("use_clustering", True)
            if not isinstance(use_clustering, bool):
                return self._send(400, {"error": "use_clustering must be a boolean"})
            result = RuleEngine.from_config().recommend(food, materials, context, top_k=top_k, use_clustering=use_clustering)
            return self._send(200, {"result": result})
        except json.JSONDecodeError:
            return self._send(400, {"error": "Request body must be valid JSON"})
        except (TypeError, ValueError) as exc:
            return self._send(400, {"error": str(exc)})
        except Exception as exc:
            return self._send(500, {"error": str(exc)})


app = handler


if __name__ == "__main__":
    from http.server import HTTPServer
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), handler).serve_forever()
