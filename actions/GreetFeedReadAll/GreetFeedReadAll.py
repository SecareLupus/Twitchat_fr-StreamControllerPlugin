from __future__ import annotations

import os

from loguru import logger

from src.backend.PluginManager.ActionBase import ActionBase


class GreetFeedReadAllAction(ActionBase):
    """Marks all Twitchat greet feed messages as read via the public API."""

    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "info.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        success = self.plugin_base.broadcast("GREET_FEED_READ_ALL")
        if not success:
            logger.warning("Twitchat greet feed read-all command failed; see plugin logs for details")

    def on_key_up(self) -> None:
        pass
