from app.data_sources.clients.base import DataSourceClient
from app.ai.prompt_formatters import Table, TableColumn, TableFormatter
import pandas as pd
import requests
from typing import List, Optional


class TallyClient(DataSourceClient):
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.host = host
        self.port = port

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

    def _post_xml(self, xml_body: str) -> str:
        response = requests.post(
            self.base_url,
            data=xml_body.encode("utf-8"),
            headers={"Content-Type": "text/xml"},
            timeout=30,
        )
        response.raise_for_status()
        return response.text

    def test_connection(self):
        try:
            xml = """<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>List of Companies</ID></HEADER><BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES></DESC></BODY></ENVELOPE>"""
            self._post_xml(xml)
            return {"success": True, "message": "Successfully connected to Tally"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def execute_query(self, sql: str) -> pd.DataFrame:
        raise NotImplementedError("Tally uses XML-based TDL queries, not SQL.")

    def get_schemas(self) -> List[Table]:
        return [
            Table(name="Ledger", description="Chart of accounts",
                  columns=[
                      TableColumn(name="Name", dtype="string"),
                      TableColumn(name="Parent", dtype="string"),
                      TableColumn(name="OpeningBalance", dtype="number"),
                      TableColumn(name="ClosingBalance", dtype="number"),
                  ], pks=[], fks=[]),
            Table(name="Voucher", description="Financial transactions",
                  columns=[
                      TableColumn(name="Date", dtype="date"),
                      TableColumn(name="VoucherType", dtype="string"),
                      TableColumn(name="VoucherNumber", dtype="string"),
                      TableColumn(name="Amount", dtype="number"),
                      TableColumn(name="Narration", dtype="string"),
                  ], pks=[], fks=[]),
            Table(name="StockItem", description="Inventory items",
                  columns=[
                      TableColumn(name="Name", dtype="string"),
                      TableColumn(name="BaseUnits", dtype="string"),
                      TableColumn(name="OpeningBalance", dtype="number"),
                      TableColumn(name="ClosingBalance", dtype="number"),
                  ], pks=[], fks=[]),
        ]

    def prompt_schema(self) -> str:
        return TableFormatter(self.get_schemas()).table_str

    @property
    def description(self) -> str:
        return f"Tally ERP client at {self.host}:{self.port}"
