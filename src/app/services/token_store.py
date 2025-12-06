from abc import ABC, abstractmethod
from typing import Optional, Dict
import json
from pathlib import Path
from datetime import datetime


class TokenStore(ABC):
    @abstractmethod
    def get_tokens(self) -> Optional[Dict]:
        ...

    @abstractmethod
    def save_tokens(self, data: Dict) -> None:
        ...


class FileTokenStore(TokenStore):
    def __init__(self, path: str):
        self.path = Path(path)

    def get_tokens(self) -> Optional[Dict]:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_tokens(self, data: Dict) -> None:
        # добавляем время последнего обновления
        data["updated_at"] = datetime.utcnow().isoformat()
        # на всякий случай создаём директорию, если её нет
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
