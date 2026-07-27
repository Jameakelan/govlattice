from urllib.parse import urlsplit


class PolicyReference:
    __slots__ = ("title", "url")

    def __init__(self, title: str, url: str) -> None:
        self.title = self._validate_title(title)
        self.url = self._validate_url(url)

    @staticmethod
    def _validate_title(title: str) -> str:
        if not isinstance(title, str):
            raise TypeError("reference title must be a string")
        title = title.strip()
        if not title:
            raise ValueError("reference title must not be empty")
        return title

    @staticmethod
    def _validate_url(url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("reference URL must be a string")
        url = url.strip()
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "reference URL must use http or https"
            )
        return url
