"""API client for interacting with the Job Tracker API."""

import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime


class APIClient:
    """Client for interacting with the Job Tracker API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.graphql_url = f"{base_url}/graphql"

    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                json={"query": query, "variables": variables or {}}
            )
            response.raise_for_status()
            return response.json()

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        query = """
        query {
          getDashboardStats {
            totalApplications
            applicationsByStatus {
              status
              count
            }
            recentApplications {
              id
              jobTitle
              position
              status
              appliedDate
              company {
                name
              }
            }
            upcomingReminders {
              id
              title
              date
              completed
            }
          }
        }
        """
        result = await self.execute_query(query)
        return result["data"]["getDashboardStats"]

    async def get_applications(self, status: Optional[str] = None, offset: int = 0, limit: int = 20) -> List[
        Dict[str, Any]]:
        """Get applications with optional filtering."""
        query = """
        query GetApplications(\$status: ApplicationStatus, \$offset: Int!, \$limit: Int!) {
          getApplications(status: \$status, offset: \$offset, limit: \$limit) {
            id
            jobTitle
            position
            location
            status
            appliedDate
            company {
              id
              name
            }
          }
        }
        """
        variables = {"offset": offset, "limit": limit}
        if status:
            variables["status"] = status

        result = await self.execute_query(query, variables)
        return result["data"]["getApplications"]

    async def get_application(self, id: str) -> Dict[str, Any]:
        """Get a single application by ID."""
        query = """
        query GetApplication(\$id: ID!) {
          getApplication(id: \$id) {
            id
            jobTitle
            company {
              id
              name
            }
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
          }
        }
        """
        result = await self.execute_query(query, {"id": id})
        return result["data"]["getApplication"]

    async def create_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new application."""
        mutation = """
        mutation CreateApplication(\$input: ApplicationInput!) {
          createApplication(input: \$input) {
            id
            jobTitle
            status
          }
        }
        """
        result = await self.execute_query(mutation, {"input": application_data})
        return result["data"]["createApplication"]

    async def get_companies(self) -> List[Dict[str, Any]]:
        """Get all companies."""
        query = """
        query {
          companies {
            id
            name
          }
        }
        """
        result = await self.execute_query(query)
        return result["data"]["companies"]

    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company."""
        mutation = """
        mutation CreateCompany(\$input: CompanyInput!) {
          createCompany(input: \$input) {
            id
            name
          }
        }
        """
        result = await self.execute_query(mutation, {"input": company_data})
        return result["data"]["createCompany"]
