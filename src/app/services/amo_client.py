import httpx
from typing import Dict, Any
from datetime import datetime, timedelta

from src.app.config import settings
from src.app.services.token_store import TokenStore


class AmoClient:
    def __init__(self, token_store: TokenStore):
        self.token_store = token_store
        self.base_url = f"https://{settings.AMO_DOMAIN}"
        # локальный кеш токенов (может быть пустым на старте)
        self._tokens: Dict[str, Any] = self.token_store.get_tokens() or {}

    def get_auth_url(self) -> str:
        return (
            f"{settings.AMO_AUTH_BASE_URL}/oauth"
            f"?client_id={settings.AMO_CLIENT_ID}"
            f"&redirect_uri={settings.AMO_REDIRECT_URI}"
            f"&mode=post_message"
        )

    def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Первый обмен кода авторизации на access/refresh токены.
        Вызывается один раз после того, как amoCRM вернул code.
        """
        url = f"{self.base_url}/oauth2/access_token"
        payload = {
            "client_id": settings.AMO_CLIENT_ID,
            "client_secret": settings.AMO_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": str(settings.AMO_REDIRECT_URI),
        }
        r = httpx.post(url, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        self._save_tokens_from_response(data)
        return data

    def _save_tokens_from_response(self, data: Dict[str, Any]) -> None:
        """
        Amo обычно возвращает expires_in (в секундах).
        Сохраняем expires_at, чтобы удобно проверять валидность.
        """
        expires_in = data.get("expires_in", 900)
        data["expires_at"] = (
            datetime.utcnow() + timedelta(seconds=expires_in)
        ).isoformat()

        self._tokens = data
        self.token_store.save_tokens(data)

    def _load_tokens_from_store(self) -> None:
        """
        Подгрузить токены из хранилища (файла), если локально пусто.
        """
        if not self._tokens:
            self._tokens = self.token_store.get_tokens() or {}

    def _ensure_token_valid(self) -> None:
        """
        Гарантирует, что у нас есть актуальные токены.
        Если локально пусто — пробуем подгрузить из файла.
        Если нет refresh_token — просим заново авторизоваться.
        """
        # лениво подгружаем из файла
        self._load_tokens_from_store()

        if not self._tokens:
            raise RuntimeError("No tokens. Complete authorization first.")

        expires_at_str = self._tokens.get("expires_at")
        if not expires_at_str:
            # если почему-то нет expires_at — пробуем рефреш
            self.refresh_tokens()
            return

        expires_at = datetime.fromisoformat(expires_at_str)

        # обновляем чуть заранее, за 60 секунд до истечения
        if datetime.utcnow() > expires_at - timedelta(seconds=60):
            self.refresh_tokens()

    def refresh_tokens(self) -> None:
        """
        Обновление токенов по refresh_token.
        """
        # если локально пусто — пробуем достать из файла
        if not self._tokens:
            self._tokens = self.token_store.get_tokens() or {}

        if not self._tokens or "refresh_token" not in self._tokens:
            raise RuntimeError("No refresh token. Complete authorization first.")

        url = f"{self.base_url}/oauth2/access_token"
        payload = {
            "client_id": settings.AMO_CLIENT_ID,
            "client_secret": settings.AMO_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": self._tokens["refresh_token"],
            "redirect_uri": str(settings.AMO_REDIRECT_URI),
        }
        r = httpx.post(url, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        self._save_tokens_from_response(data)

    def api_call(self, method: str, path: str, **kwargs) -> httpx.Response:
        """
        Базовый метод для всех запросов к amoCRM.
        """
        self._ensure_token_valid()

        headers = kwargs.pop("headers", {}) or {}
        headers["Authorization"] = f"Bearer {self._tokens['access_token']}"
        url = f"{self.base_url}{path}"

        return httpx.request(method, url, headers=headers, timeout=10, **kwargs)

    def add_note_to_lead(self, lead_id: int, text: str) -> Dict[str, Any]:
        """
        Добавить комментарий (note_type=common) к сделке.
        """
        path = f"/api/v4/leads/{lead_id}/notes"
        payload = [
            {
                "note_type": "common",
                "params": {
                    "text": text,
                },
            }
        ]
        resp = self.api_call("POST", path, json=payload)
        resp.raise_for_status()
        return resp.json()
