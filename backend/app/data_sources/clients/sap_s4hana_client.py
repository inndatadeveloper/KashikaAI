from app.data_sources.clients.base import DataSourceClient
from app.ai.prompt_formatters import Table, TableColumn, TableFormatter
import pandas as pd
import requests
from typing import List, Optional


class SapS4hanaClient(DataSourceClient):
    def __init__(self, host: str, client_id: str, username: str, password: str, port: int = 443, use_ssl: bool = True):
        self.host = host
        self.client_id = client_id
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl

    @property
    def base_url(self):
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}:{self.port}/sap/opu/odata/sap"

    def _get_session(self):
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.headers.update({
            "Accept": "application/json",
            "sap-client": self.client_id,
        })
        return session

    def test_connection(self):
        try:
            session = self._get_session()
            url = f"{self.base_url}/API_COMPANYCODE_SRV/A_CompanyCode?$top=1&$format=json"
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return {"success": True, "message": f"Successfully connected to SAP S/4HANA at {self.host}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def execute_query(self, sql: str) -> pd.DataFrame:
        raise NotImplementedError("SAP S/4HANA uses OData APIs, not SQL. Use the OData endpoints directly.")

    def get_schemas(self) -> List[Table]:
        return [
            Table(name="A_CompanyCode", description="Company Code master data",
                  columns=[
                      TableColumn(name="CompanyCode", dtype="string"),
                      TableColumn(name="CompanyCodeName", dtype="string"),
                      TableColumn(name="CityName", dtype="string"),
                      TableColumn(name="Country", dtype="string"),
                      TableColumn(name="Currency", dtype="string"),
                  ], pks=["CompanyCode"], fks=[]),
            Table(name="A_CustomerSalesArea", description="Customer Sales Area data",
                  columns=[
                      TableColumn(name="Customer", dtype="string"),
                      TableColumn(name="SalesOrganization", dtype="string"),
                      TableColumn(name="DistributionChannel", dtype="string"),
                      TableColumn(name="Division", dtype="string"),
                  ], pks=["Customer", "SalesOrganization"], fks=[]),
            Table(name="A_SalesOrder", description="Sales Orders",
                  columns=[
                      TableColumn(name="SalesOrder", dtype="string"),
                      TableColumn(name="SalesOrderType", dtype="string"),
                      TableColumn(name="SalesOrganization", dtype="string"),
                      TableColumn(name="TotalNetAmount", dtype="number"),
                      TableColumn(name="TransactionCurrency", dtype="string"),
                      TableColumn(name="CreationDate", dtype="date"),
                  ], pks=["SalesOrder"], fks=[]),
            Table(name="A_PurchaseOrder", description="Purchase Orders",
                  columns=[
                      TableColumn(name="PurchaseOrder", dtype="string"),
                      TableColumn(name="PurchaseOrderType", dtype="string"),
                      TableColumn(name="Supplier", dtype="string"),
                      TableColumn(name="NetPaymentAmount", dtype="number"),
                      TableColumn(name="DocumentCurrency", dtype="string"),
                      TableColumn(name="CreationDate", dtype="date"),
                  ], pks=["PurchaseOrder"], fks=[]),
        ]

    def prompt_schema(self) -> str:
        return TableFormatter(self.get_schemas()).table_str

    @property
    def description(self) -> str:
        return f"SAP S/4HANA OData client for host '{self.host}', client '{self.client_id}'"
