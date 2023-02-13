from typing import Optional

from pydantic import BaseModel, Field
from tenacity import wait, stop, retry_unless_exception_type

from opal_common.fetcher.fetch_provider import BaseFetchProvider
from opal_common.fetcher.events import FetcherConfig, FetchEvent
from opal_common.logger import logger
from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.exceptions import CosmosHttpResponseError


class CosmosConnectionParams(BaseModel):
    database_name: Optional[str] = Field(None, description="the database name")
    container_name: Optional[str] = Field(None, description="the container name")
    key: Optional[str] = Field(None, description="key used for authentication")


class CosmosFetcherConfig(FetcherConfig):
    """
    Config for CosmosFetchProvider, inherits from `FetcherConfig`.
    * In your own class, you must set the value of the `fetcher` key to be your custom provider class name.
    """

    fetcher: str = "CosmosFetchProvider"
    connection_params: Optional[CosmosConnectionParams] = Field(
        None,
        description="these params can override or complement parts of the dsn (connection string)",
    )
    query: str = Field(
        ..., description="the query to run against cosmos in order to fetch the data"
    )


class CosmosFetchEvent(FetchEvent):
    """
    When writing a custom provider, you must create a custom FetchEvent subclass, just like this class.
    In your own class, you must:
    * set the value of the `fetcher` key to be your custom provider class name.
    * set the type of the `config` key to be your custom config class (the one just above).
    """

    fetcher: str = "CosmosFetchProvider"
    config: CosmosFetcherConfig = None


class CosmosFetchProvider(BaseFetchProvider):
    """
    The fetch-provider logic, must inherit from `BaseFetchProvider`.
    """

    RETRY_CONFIG = {
        "wait": wait.wait_random_exponential(),
        "stop": stop.stop_after_attempt(10),
        "retry": retry_unless_exception_type(
            CosmosHttpResponseError
        ),  # query error (i.e: invalid table, etc)
        "reraise": True,
    }

    def __init__(self, event: CosmosFetchEvent) -> None:
        logger.warning("init")
        if event.config is None:
            event.config = CosmosFetcherConfig()
        super().__init__(event)
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._container: Optional[ContainerProxy] = None

    def parse_event(self, event: FetchEvent) -> CosmosFetchEvent:
        c = CosmosFetchEvent(**event.dict(exclude={"config"}), config=event.config)
        return c

    async def __aenter__(self):
        self._event: CosmosFetchEvent  # type casting
        dsn: str = self._event.url
        connection_params: dict = (
            {}
            if self._event.config.connection_params is None
            else self._event.config.connection_params.dict(exclude_none=True)
        )

        self._client = CosmosClient(url=dsn, credential=connection_params["key"])
        self._database = self._client.get_database_client(
            database=connection_params["database_name"]
        )
        self._container = self._database.get_container_client(
            container=connection_params["container_name"]
        )

        return self

    async def __aexit__(self, exc_type=None, exc_val=None, tb=None):
        if self._client is not None:
            await self._client.close()

    async def _fetch_(self):
        self._event: CosmosFetchEvent  # type casting
        if self._event.config is None:
            logger.warning("incomplete fetcher config: event config is empty")
            return

        logger.info(f"{self.__class__.__name__} fetching from {self._url}")

        return self._container.query_items(query=self._event.config.query)

    async def _process_(self, results: dict[str, any]):
        self._event: CosmosFetchEvent  # type casting
        items = [item async for item in results]
        return items
