from app.data_sources.clients.base import DataSourceClient
from app.ai.prompt_formatters import Table, TableColumn, TableFormatter
import pandas as pd
import requests
from typing import List, Optional


class ZohoBooksClient(DataSourceClient):
    def __init__(self, organization_id: str, access_token: str, region: str = "com"):
        self.organization_id = organization_id
        self.access_token = access_token
        self.region = region

    @property
    def base_url(self):
        return f"https://www.zohoapis.{self.region}/books/v3"

    def _get_headers(self):
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json",
        }

    def _get(self, endpoint: str, params: dict = None) -> dict:
        params = params or {}
        params["organization_id"] = self.organization_id
        response = requests.get(
            f"{self.base_url}/{endpoint}",
            headers=self._get_headers(),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def test_connection(self):
        try:
            data = self._get("organizations")
            return {"success": True, "message": f"Successfully connected to Zoho Books (org: {self.organization_id})"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def execute_query(self, sql: str) -> pd.DataFrame:
        raise NotImplementedError("Zoho Books uses REST APIs, not SQL.")

    def get_schemas(self) -> List[Table]:
        return [
            Table(name="invoices", description="Sales invoices",
                  columns=[
                      TableColumn(name="invoice_id", dtype="string"),
                      TableColumn(name="invoice_number", dtype="string"),
                      TableColumn(name="customer_name", dtype="string"),
                      TableColumn(name="date", dtype="date"),
                      TableColumn(name="due_date", dtype="date"),
                      TableColumn(name="total", dtype="number"),
                      TableColumn(name="balance", dtype="number"),
                      TableColumn(name="status", dtype="string"),
                      TableColumn(name="currency_code", dtype="string"),
                  ], pks=["invoice_id"], fks=[]),
            Table(name="contacts", description="Customers and vendors",
                  columns=[
                      TableColumn(name="contact_id", dtype="string"),
                      TableColumn(name="contact_name", dtype="string"),
                      TableColumn(name="contact_type", dtype="string"),
                      TableColumn(name="email", dtype="string"),
                      TableColumn(name="phone", dtype="string"),
                      TableColumn(name="currency_code", dtype="string"),
                      TableColumn(name="outstanding_receivable_amount", dtype="number"),
                  ], pks=["contact_id"], fks=[]),
            Table(name="bills", description="Purchase bills",
                  columns=[
                      TableColumn(name="bill_id", dtype="string"),
                      TableColumn(name="bill_number", dtype="string"),
                      TableColumn(name="vendor_name", dtype="string"),
                      TableColumn(name="date", dtype="date"),
                      TableColumn(name="due_date", dtype="date"),
                      TableColumn(name="total", dtype="number"),
                      TableColumn(name="balance", dtype="number"),
                      TableColumn(name="status", dtype="string"),
                  ], pks=["bill_id"], fks=[]),
            Table(name="accounts", description="Chart of accounts",
                  columns=[
                      TableColumn(name="account_id", dtype="string"),
                      TableColumn(name="account_name", dtype="string"),
                      TableColumn(name="account_type", dtype="string"),
                      TableColumn(name="current_balance", dtype="number"),
                      TableColumn(name="currency_code", dtype="string"),
                  ], pks=["account_id"], fks=[]),
        ]

    def prompt_schema(self) -> str:
        return TableFormatter(self.get_schemas()).table_str

    @property
    def description(self) -> str:
        return f"Zoho Books REST API client for organization '{self.organization_id}'"
