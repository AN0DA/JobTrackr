import json
import logging
import time
from typing import Dict, Any, Optional, List
import pydgraph
from contextlib import contextmanager

from src.api.config import settings

logger = logging.getLogger(__name__)


class DgraphClientPool:
    """Connection pool for DGraph clients"""

    def __init__(self, size: int = settings.dgraph_pool_size):
        """Initialize a pool of DGraph clients."""
        self.host = settings.dgraph_alpha_host
        self.port = settings.dgraph_alpha_port
        self.size = size
        self.pool: List[pydgraph.DgraphClient] = []
        self.initialize_pool()

    def initialize_pool(self) -> None:
        """Create client connections in the pool."""
        for _ in range(self.size):
            try:
                client_stub = pydgraph.DgraphClientStub(f'{self.host}:{self.port}')
                client = pydgraph.DgraphClient(client_stub)
                self.pool.append(client)
            except Exception as e:
                logger.error(f"Failed to create DGraph client: {e}")

        if not self.pool:
            raise RuntimeError("Failed to initialize any DGraph clients")

        logger.info(f"Initialized DGraph client pool with {len(self.pool)} connections")

    @contextmanager
    def get_client(self):
        """Get a client from the pool."""
        if not self.pool:
            self.initialize_pool()

        if not self.pool:
            raise RuntimeError("No DGraph clients available in the pool")

        client = self.pool.pop(0)
        try:
            yield client
        finally:
            # Return client to the pool
            self.pool.append(client)


class DgraphClient:
    """DGraph client for querying and mutating data"""

    def __init__(self):
        """Initialize the DGraph client with a connection pool."""
        self.pool = DgraphClientPool()

    def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a query on DGraph."""
        with self.pool.get_client() as client:
            # Create a new readonly transaction
            txn = client.txn(read_only=True)
            try:
                # Process variables if provided
                if variables:
                    processed_vars = self._process_variables(variables)
                    res = txn.query(query, variables=processed_vars)
                else:
                    res = txn.query(query)

                return json.loads(res.json)
            except Exception as e:
                logger.error(f"DGraph query error: {e}")
                raise
            finally:
                txn.discard()

    def mutate(self, mutations: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mutation on DGraph."""
        with self.pool.get_client() as client:
            # Create a new transaction
            txn = client.txn()
            try:
                mu = pydgraph.Mutation(set_json=json.dumps(mutations).encode('utf-8'))
                response = txn.mutate(mutation=mu)
                txn.commit()

                # Extract UIDs from response
                uids = {}
                if hasattr(response, 'uids'):
                    for k, v in response.uids.items():
                        uids[k] = v

                return {"uids": uids}
            except Exception as e:
                logger.error(f"DGraph mutation error: {e}")
                txn.discard()
                raise
            finally:
                # Ensure the transaction is discarded even if an error occurs
                if txn._state != 2:  # Not committed
                    txn.discard()

    def _process_variables(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """Process variables to ensure they're in the correct format for DGraph."""
        processed_vars = {}
        for key, value in variables.items():
            # Remove the $ prefix if present
            if key.startswith('$'):
                key = key[1:]

            # Convert value to string
            if value is None:
                processed_vars[key] = ""
            elif isinstance(value, bool):
                processed_vars[key] = "true" if value else "false"
            elif isinstance(value, (int, float)):
                processed_vars[key] = str(value)
            else:
                processed_vars[key] = str(value)

        return processed_vars

    def wait_for_dgraph(self, timeout: int = settings.dgraph_connection_timeout) -> bool:
        """Wait for Dgraph to be ready."""
        logger.info(f"Waiting for Dgraph at {self.pool.host}:{self.pool.port}...")

        for attempt in range(timeout):
            try:
                with self.pool.get_client() as client:
                    # Simple health check query
                    txn = client.txn(read_only=True)
                    txn.query("{health(func: uid(0x1)) {uid}}")
                    txn.discard()
                    logger.info("Successfully connected to Dgraph")
                    return True
            except Exception as e:
                logger.debug(f"Waiting for Dgraph to be ready (attempt {attempt + 1}/{timeout}): {e}")
                time.sleep(1)

        logger.error(
            f"Could not connect to Dgraph after {timeout} seconds. Check Dgraph logs and network configuration.")
        logger.error(f"- Verify that Dgraph is running and accessible at {self.pool.host}:{self.pool.port}")
        logger.error(f"- Ensure the whitelist includes the API container's IP address")
        return False
