from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

from .services import OBSConnectionConfig


@dataclass
class TwitchatSettings:
    """Serializable settings for the Twitchat integration plugin."""

    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""
    use_ssl: bool = False
    namespace: str = "twitchat"
    request_timeout: float = 5.0

    @classmethod
    def from_dict(cls, raw: Dict[str, Any] | None) -> "TwitchatSettings":
        raw = raw or {}
        return cls(
            host=str(raw.get("host", cls.host)).strip() or cls.host,
            port=int(raw.get("port", cls.port)),
            password=str(raw.get("password", cls.password)),
            use_ssl=bool(raw.get("use_ssl", cls.use_ssl)),
            namespace=str(raw.get("namespace", cls.namespace)).strip() or cls.namespace,
            request_timeout=float(raw.get("request_timeout", cls.request_timeout)),
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    def to_obs_config(self) -> OBSConnectionConfig:
        return OBSConnectionConfig(
            host=self.host,
            port=int(self.port),
            password=self.password,
            use_ssl=self.use_ssl,
            request_timeout=float(self.request_timeout),
        )

    def update(self, **kwargs: Any) -> "TwitchatSettings":
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)


__all__ = ["TwitchatSettings"]
