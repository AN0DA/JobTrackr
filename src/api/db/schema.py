"""Dgraph schema management module."""

import logging
import time

import pydgraph
from typing import Optional

from src.api.db.client import DgraphClient

logger = logging.getLogger(__name__)

SCHEMA = """
# Define predicates first
jobTitle: string @index(exact) .
position: string @index(exact) .
location: string .
salary: string .
status: string @index(exact) .
appliedDate: datetime @index(hour) .
link: string .
description: string .
notes: string .
tags: [string] @index(exact) .
createdAt: datetime @index(hour) .
updatedAt: datetime @index(hour) .
name: string @index(exact) .
website: string .
industry: string @index(exact) .
size: string .
logo: string .
title: string .
email: string @index(exact) .
phone: string .
type: string @index(exact) .
date: datetime @index(hour) .
url: string .
content: string .
completed: bool @index(bool) .

# Define connections between entities
company: uid @reverse .
application: uid @reverse .
contacts: [uid] @reverse .
applications: [uid] @reverse .
interactions: [uid] @reverse .
documents: [uid] @reverse .
reminders: [uid] @reverse .

# Define types
type Application {
  jobTitle
  position
  location
  salary
  status
  appliedDate
  link
  description
  notes
  tags
  createdAt
  updatedAt
  company
  contacts
  interactions
  documents
  reminders
}

type Company {
  name
  website
  industry
  size
  logo
  notes
  applications
  contacts
}

type Contact {
  name
  title
  email
  phone
  company
  applications
  notes
}

type Interaction {
  type
  date
  notes
  application
  contacts
  documents
}

type Document {
  name
  type
  url
  content
  applications
  interactions
  createdAt
}

type Reminder {
  title
  description
  date
  completed
  application
}

# Add schema version tracking
type SchemaVersion {
  schema_version
  version
}
schema_version: bool @index(bool) .
version: string .
"""

SCHEMA_VERSION = "1.0"


# Add this function
def check_schema_version(client: DgraphClient) -> bool:
    """Check if the current schema version matches the stored version."""
    query = """
    {
      schema_version(func: has(schema_version)) {
        version
      }
    }
    """

    try:
        result = client.query(query)
        if not result.get("schema_version"):
            logger.info("No schema version found, will initialize schema")
            return False

        stored_version = result["schema_version"][0].get("version")
        if stored_version != SCHEMA_VERSION:
            logger.info(f"Schema version mismatch: stored={stored_version}, current={SCHEMA_VERSION}")
            return False

        logger.info(f"Schema version matches: {SCHEMA_VERSION}")
        return True
    except Exception as e:
        logger.warning(f"Error checking schema version: {e}")
        return False


def save_schema_version(client: DgraphClient) -> bool:
    """Save the current schema version to Dgraph."""
    version_data = {
        "uid": "_:schema_version",
        "dgraph.type": "SchemaVersion",
        "schema_version": "true",
        "version": SCHEMA_VERSION
    }

    try:
        client.mutate(version_data)
        return True
    except Exception as e:
        logger.error(f"Failed to save schema version: {e}")
        return False


# Update initialize_schema function to use versioning
def initialize_schema(client: Optional[DgraphClient] = None, max_retries: int = 5) -> bool:
    """Initialize the Dgraph schema with retry logic."""
    if not client:
        client = DgraphClient()

    # First wait for Dgraph to be available
    if not client.wait_for_dgraph():
        logger.error("Failed to connect to Dgraph")
        return False

    # Check if schema needs to be updated
    if check_schema_version(client):
        logger.info("Schema is up to date, skipping initialization")
        return True

    for attempt in range(max_retries):
        try:
            # Use the client pool to get a client
            with client.pool.get_client() as dgraph_client:
                operation = pydgraph.Operation(schema=SCHEMA)
                dgraph_client.alter(operation)

            # Save schema version
            if save_schema_version(client):
                logger.info(f"Schema successfully initialized with version {SCHEMA_VERSION}")
                return True
            else:
                logger.warning("Schema initialized but version tracking failed")
                return True
        except Exception as e:
            logger.warning(f"Schema initialization attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to initialize schema after {max_retries} attempts: {e}")
                return False
